"""
Set counted_via_contributions on any existing income Source whose name
indicates it holds tithe, offering or special contribution money.

Why this is needed
------------------
The financial report previously avoided double counting by comparing a
source's lowercased name against a hardcoded set:

    "tithe & offering cad"
    "tithe & offering usd"
    "special contribution cad"

The seed command creates a source named "Tithe and Offerings". That string is
not in the set, so the guard never matched it. Users can also create sources
with any name they type, directly from the Add Income form, so any number of
unmatched spellings may exist.

This migration flags the ones already present so the new flag is correct from
the moment it ships, rather than relying on someone remembering to tick boxes.

On the production database at the time of writing, four sources exist (Charity
Donations, Material Sales, Other Donations, Sales) and none match, so this
migration flags nothing there. It matters for any other environment, and for
databases seeded with the older seed command.
"""

from django.db import migrations

# A source whose name contains any of these is contribution money.
# Deliberately broad: a false positive is visible and reversible, while a false
# negative silently double counts money in a tax report.
SUSPECT_TERMS = ("tithe", "offering", "special contribution")


def flag_sources(apps, schema_editor):
    Source = apps.get_model("income", "Source")
    for source in Source.objects.all():
        name = (source.name or "").strip().lower()
        if any(term in name for term in SUSPECT_TERMS):
            source.counted_via_contributions = True
            source.save(update_fields=["counted_via_contributions"])


def unflag_sources(apps, schema_editor):
    # Reversing clears every flag rather than guessing which were set by this
    # migration and which an administrator ticked afterwards. The field is
    # removed by the reverse of 0010 anyway.
    Source = apps.get_model("income", "Source")
    Source.objects.filter(counted_via_contributions=True).update(
        counted_via_contributions=False
    )


class Migration(migrations.Migration):

    dependencies = [
        ("income", "0010_source_counted_via_contributions"),
    ]

    operations = [
        migrations.RunPython(flag_sources, unflag_sources),
    ]
