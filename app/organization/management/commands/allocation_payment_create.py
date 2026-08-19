import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db.models import Sum
from organization.models import PaymentAllocation, Region
from income.models import Income
from contributor.models import Contribution, MiscellaneousContribution, AnonymousContribution


class Command(BaseCommand):
    help = 'Create monthly payment allocations for each region if not already present'

    def handle(self, *args, **options):
        today = datetime.date.today()
        current_month = today.month
        current_year = today.year
        first = today.replace(day=1)
        last_month = first - datetime.timedelta(days=1)

        regions = Region.objects.all()
        allocation_choices = dict(PaymentAllocation.ALLOCATION_CHOICES)

        for region in regions:
            for allocation_choice in allocation_choices.keys():
                if not PaymentAllocation.objects.filter(
                        region=region,
                        date__year=last_month.year,
                        date__month=last_month.month,
                        name=allocation_choice
                ).exists():
                    if allocation_choice == 'gck_canada':
                        PaymentAllocation.objects.create(
                            region=region,
                            date=last_month,
                            total_amount=region.gck_canada_payment,
                            paid_amount=0,
                            note='',
                            name=allocation_choice
                        )
                    elif allocation_choice == 'dclm':
                        total_income ,total_amount = self.calculate_total_amount(region, current_year, current_month, 30)
                        PaymentAllocation.objects.create(
                            region=region,
                            date=last_month,
                            total_amount=total_amount,
                            income = total_income,
                            paid_amount=0,
                            note='',
                            name=allocation_choice
                        )
                        print(f'Created allocation for {region.name} ({allocation_choice}) with total_amount {total_amount}')
                    else:
                        total_income ,total_amount = self.calculate_total_amount(region, current_year, current_month,10)
                        PaymentAllocation.objects.create(
                            region=region,
                            date=last_month,
                            total_amount=total_amount,
                            income = total_income,
                            paid_amount=0,
                            note='',
                            name=allocation_choice
                        )
                        print(f'Created allocation for {region.name} ({allocation_choice}) with total_amount {total_amount}')
                else:
                    print(f'Allocation already exists for {region.name} ({allocation_choice})')

        print('Monthly allocations creation process completed')


    def calculate_total_amount(self, region, current_year, current_month, percentage):
        if current_month == 1:
            previous_month = 12
            previous_year = current_year - 1
        else:
            previous_month = current_month - 1
            previous_year = current_year

        income_object_query = Income.objects.filter(
            local_church__region_id=region.id,
            date__year=previous_year,
            date__month=previous_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)

        contrib_object_query = Contribution.objects.filter(
            local_church__region_id=region.id,
            deposited_date__year=previous_year,
            deposited_date__month=previous_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)

        misc_contrib_object_query = MiscellaneousContribution.objects.filter(
            local_church__region_id=region.id,
            deposited_date__year=previous_year,
            deposited_date__month=previous_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)

        anon_contrib_object_query = AnonymousContribution.objects.filter(
            local_church__region_id=region.id,
            deposited_date__year=previous_year,
            deposited_date__month=previous_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.00)


        total_income = income_object_query + contrib_object_query + misc_contrib_object_query + anon_contrib_object_query
        total_amount = total_income * Decimal(percentage/100)
        return total_income, total_amount
