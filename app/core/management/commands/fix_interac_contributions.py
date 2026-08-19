from django.core.management.base import BaseCommand
from contributor.models import Contribution, TransactionType
from organization.models import LocalChurch


class Command(BaseCommand):
    help = 'Copy contributions for Regina church from OFFERINGS_CAN to INTEREC_E_TRANSFER'

    def handle(self, *args, **kwargs):
        count = self.create_data()
        self.stdout.write(self.style.SUCCESS(f"{count} Interac contributions created successfully."))

    @staticmethod
    def create_data():
        """Copy contributions marked as OFFERINGS_CAN and recreate them as INTEREC_E_TRANSFER for Regina"""
        try:
            local_church = LocalChurch.objects.get(local_church_name__title="Regina")
        except LocalChurch.DoesNotExist:
            raise ValueError("LocalChurch with name 'Regina' not found.")

        original_contributions = Contribution.objects.filter(
            local_church=local_church,
            payment_type=TransactionType.OFFERINGS_CAN.value
        )

        if original_contributions.count() != 236:
            raise ValueError(f"Expected 270 contributions, found {original_contributions.count()}")

        new_contributions = []

        for item in original_contributions:
            new_contributions.append(Contribution(
                contributor=item.contributor,
                amount=item.amount,
                deposited_date=item.deposited_date,
                payment_type=TransactionType.INTEREC_E_TRANSFER.value,
                special_contribution=item.special_contribution,
                month=item.month,
                local_church=item.local_church,
                account_type=item.account_type,
                can_edit=item.can_edit,
            ))

        Contribution.objects.bulk_create(new_contributions)
        return len(new_contributions)
