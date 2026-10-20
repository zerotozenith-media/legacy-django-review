"""
Query helpers for the income app.

Kept apart from the views so the same rule is applied in every place rather
than repeated inline, and so it can be tested on its own.
"""

from django.db.models import Q

from .models import Source

# A source whose name contains any of these holds contribution money, which is
# recorded on the Contributions screens and summed from there by the financial
# report. Used to flag such a source automatically when one is created from the
# Add Income form, so a user typing "Tithes" cannot reintroduce double counting.
#
# Migration income/0011 carries its own copy of this list on purpose.
# Migrations must not import application code, because that code changes while
# the migration has to keep behaving as it did when it was written.
CONTRIBUTION_SOURCE_TERMS = ("tithe", "offering", "special contribution")


def looks_like_contribution_source(name):
    """True when a source name indicates tithe, offering or special
    contribution money. Deliberately broad: a false positive is visible in the
    admin and can be unticked, while a false negative silently double counts
    money in a tax report."""
    lowered = (name or "").strip().lower()
    return any(term in lowered for term in CONTRIBUTION_SOURCE_TERMS)


def selectable_sources(current_source_id=None):
    """
    The income sources a user may choose on the Add or Edit Income form.

    Sources flagged counted_via_contributions are excluded. Money for those is
    recorded on the Contributions screens, and the financial report sums it
    from there, so an Income row against one of them would be counted twice.

    current_source_id keeps an already-saved source in the list even when it is
    flagged. Without this, opening an old income record that points at a
    flagged source and pressing save would silently change or clear its
    source, because the saved value would not be among the valid choices.
    A change to what is selectable going forward must not rewrite history.
    """
    if current_source_id:
        return Source.objects.filter(
            Q(counted_via_contributions=False) | Q(pk=current_source_id)
        ).order_by("name")

    return Source.objects.exclude(counted_via_contributions=True).order_by("name")
