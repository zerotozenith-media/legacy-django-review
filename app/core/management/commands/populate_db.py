from django.core.management.base import BaseCommand
from django.db import transaction
from attendance.models import ChurchServices
from authentication.models import User
from expenses.models import Category, SubCategory
from income.models import Source

from organization.models import LocalChurch, Region, LocalChurchName, BankAccount


class Command(BaseCommand):
    help = "Populate default database data"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with transaction.atomic():
            self.add_local_churches()
            self.add_categories()
            self.add_church_services()
            self.add_back_account()
            self.add_default_source()
            self.stdout.write(self.style.SUCCESS("Database default data added successfully."))

    def add_local_churches(self):
        churches_data = {
            "NOVA_SCOTIA": [
                "Sydney",
                "Truro",
                "Halifax",
                "Antigonish"
            ],
            "NEWFOUNDLAND_AND_LABRADOR": [
                "St. John's"
            ],
            "FREDERICTON": [
                "Fredericton"
            ],

            "SAINT_JOHN": [
                "Saint John"
            ],

            "MONCTON": [
                "Moncton"
            ],

            "PRINCE_EDWARD_ISLAND": [
                "Charlottetown"
            ],
            "OTTAWA": [
                "Ottawa"
            ],
            "QUEBEC": [
                "Montreal",
                "Quebec City"
            ],
            "KITCHENER": [
                "Kitchener",
                "London Ontario",
                "Guelph",
                "Hamilton"
            ],
            "BRAMPTON": [
                "Brampton"
            ],
            "TORONTO_1": [
                "Oakdale",
                "Vaughan"
            ],
            "SCARBOROUGH": [
                "Scarborough"
            ],
            "OSHAWA": [
                "Oshawa",
                "Ajax"
            ],
            "WINDSOR": [
                "Windsor"
            ],
            "THUNDER_BAY": [
                "Thunder Bay"
            ],
            "MANITOBA": [
                "Winnipeg",
                "Brandon",
                "Osborne",
                "Campus",
                "Selkirk"
            ],
            "SASKATOON": [
                "Saskatoon East",
                "Saskatoon West",
                "Saskatoon South",
                "Prince Albert"
            ],
            "REGINA": [
                "Regina"
            ],
            "FORT_MCMURRAY": [
                "Fort-McMurray"
            ],
            "CALGARY": [
                "Calgary South",
                "Calgary North",
                "Calgary Midtown"
            ],
            "EDMONTON": [
                "Edmonton NE",
                "Edmonton NW",
                "Edmonton South"
            ],
            "BRITISH_COLUMBIA": [
                "Surrey",
                "Prince George",
                "Nanaimo",
                "Kelowna",
                "Burns Lake"
            ],
            "BARRIE": [
                "Barrie",
                "Sudbury"
            ],
            "CAMROSE": [
                "Camrose"
            ]
        }

        for region, church_list in churches_data.items():
            region_name = region.replace("_", " ")
            region_object = Region.objects.create(name=region_name.replace("_", " "))

            for church in church_list:
                local_church_name = LocalChurchName.objects.create(title=church)
                LocalChurch.objects.create(local_church_name=local_church_name, region=region_object)
            self.stdout.write(
                self.style.SUCCESS("Successfully created local churches and region"))

    def add_categories(self):
        """Populate Category and Subcategories"""
        categories_data = {
            "RECURRENT": {
                "Advertising & Promotion": [
                    "Advertisement",
                    "Promotion / Retreat Expenses",
                    "Special Programs -M&WF",
                    "Outreach Activities",
                    "Tracts, Books and other printed Materials",
                ],
                "Travel/Vehicle Expenses": [
                    "Vehicle Registration and Insurance",
                    "Vehicle Repairs / Maintenance",
                    "Gas / Fueling" "Flights - local, national and international",
                    "Ground Transport - buses, taxis, airport taxi, etc"
                    "Car Hire, Rental Expenses",
                    "Other Transportation Expenses - Rail, Sea, etc",
                ],
                "Interest/Bank Charges": [
                    "Mortgage Interest",
                    "Interests Paid on Loans",
                    "Bank Charges",
                ],
                "Licences, Memberships & Dues": [
                    "Professional Licence Fees",
                    "Membership Fees / Dues",
                    "Contributions to external bodies",
                ],
                "Office Supplies & Expenses": [
                    "Stationeries",
                    "Printing",
                    "Photocopy",
                    "Internet",
                    "Mobile Phones",
                    "Office Phone & Fax",
                    "Small Consumable Items",
                    "Postage/Shipping",
                    "Entertainment",
                    "Equipment Rentals",
                ],
                "Occupancy Costs": [
                    "Rent",
                    "Other Charges",
                    "City Utilities: Water,Gas,Hydro",
                    "Property Taxes",
                    "Property Insurance",
                    "Building Repairs / Maintenance",
                    "Snow Removal / Sanitation",
                    "Garbage Removal",
                    "Hotel Accommodation",
                    "Other Occupancy Costs",
                ],
                "Professional & Consulting": [
                    "Professional Fees",
                    "Consulting Fees",
                    "Honorarium",
                    "Pastoral Care",
                ],
                "Education & Training": [
                    "Campus",
                    "Youth",
                    "Children",
                    "Sunday School / Choir",
                    "Home Fellowships",
                    "Support to other sections",
                    "Other Training/Education activities",
                ],
                "Grants/Scholarships/Charity": [
                    "Research Grants",
                    "Scholarships",
                    "Support to Needy Students and others",
                    "Other Charity Activities",
                ],
            },
            "CAPITAL": {
                "Purchase Supplies & Assets": [
                    "Land & Buildings",
                    "Furniture/Furnishing (Office, Church and Mission)",
                    "Electronics",
                    "Audio/Video Mixer, Microphone, Speaker",
                    "Musical Instruments (ALL) - Saz, Keyboard, etc",
                    "Small Equipments - Cabinets, Electrical, etc",
                    "Cash & Bank, etc",
                ],
                "Finance": [
                    "Loan Repayments",
                    "Contribution to National Church",
                    "Account Receivable (if any)",
                    "Contributions made for DLICC in CAD",
                ],
            },
        }

        category_mapping = {
            "RECURRENT": Category.RECURRENT,
            "CAPITAL": Category.CAPITAL,
        }

        subcategory_objs = []
        for cat_type, categories in categories_data.items():
            for name in categories.keys():
                category, created = Category.objects.get_or_create(
                    name=name, category_type=category_mapping.get(cat_type)
                )
                if created:
                    subcategories = categories_data[cat_type][name]
                    for c in subcategories:
                        subcategory_objs.append(SubCategory(parent=category, name=c))

        SubCategory.objects.bulk_create(subcategory_objs)
        self.stdout.write(
            self.style.SUCCESS("Successfully created categories and subcategories")
        )

    def add_church_services(self):
        ChurchServices.objects.bulk_create([
            ChurchServices(name='Sunday Worship Service', short_name='SWS', local_church_id=None),
            ChurchServices(name='Bible Study', short_name='BS', local_church_id=None),
            ChurchServices(name='Weekly Prayer Meeting - Wednesday/Thursday/Friday', short_name='WPM',
                           local_church_id=None),
            ChurchServices(name='Workers Meeting', short_name='WM', local_church_id=None),
            ChurchServices(name='Special Program/Monthly National Program', short_name='SP', local_church_id=None),
        ])
        self.stdout.write(
            self.style.SUCCESS("Successfully created Church Services")
        )

    def add_back_account(self):
        bank_accounts_numbers = {
            "HQ(Tithe and Offerings)": "5202022",
            "HQ(Non - tax)": "5256601",
            "HQ(DLICC / GCK)": "5256423",
            "HQ(GCK Canada)": "5252622",
            "NOVA_SCOTIA": "5015001",
            "PRINCE_EDWARD_ISLAND": "5250171",
            "OTTAWA": "7947-5228797",
            "QUEBEC": "5216962",
            "KITCHENER": "5259262",
            "BRAMPTON": "5273321",
            "TORONTO_1": "5362948",
            "SCARBOROUGH": "5253566",
            "OSHAWA": "5020762",
            "WINDSOR": "5238424",
            "THUNDER_BAY": "5218512",
            "MANITOBA": "6546-5203225",
            "SASKATOON": "5226339",
            "REGINA": "5243229",
            "FORT_MCMURRAY": "0829-5233802",
            "CALGARY": "8063-5211516",
            "EDMONTON": "0879-5205179",
            "BRITISH_COLUMBIA": "0926-5207640",
        }

        for region_name, bank_accounts_number in bank_accounts_numbers.items():
            region = Region.objects.filter(name=region_name.replace("_", " ")).first()
            if region:
                BankAccount.objects.get_or_create(
                    region=region,
                    account_name=f"{region.name.title()}",
                    account_number=f"[{bank_accounts_number}]",
                    balance=0.00
                )

                self.stdout.write(
                    self.style.SUCCESS("Successfully created default bank accounts"))
            else:
                if region_name[:2] == "HQ":
                    BankAccount.objects.get_or_create(
                        account_name=f"{region_name}",
                        account_number=f"[{bank_accounts_number}]",
                        balance=0.00
                    )

                    self.stdout.write(
                        self.style.SUCCESS("Successfully created HQ default bank accounts"))
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Region not found - {region_name}{region_name[:2]}"))

    def add_default_source(self):
        user = User.objects.filter(is_superuser=True, is_staff=True, is_active=True).first()
        source = [
            {
                'name': "Sales",
                "type": "Income",
                "description": "Women Mirror, STS, Manna, Magazines",
                "entry_by": user
            },
            {
                'name': "Charity Donations",
                "type": "Income",
                "description": "Donation from the Charity Events",
                "entry_by": user
            },
            {
                'name': "Other Donations",
                "type": "Income",
                "description": "Donations from unknown sources ",
                "entry_by": user
            },
            {
                'name': "Material Sales",
                "type": "Income",
                "description": "Fair Market Value of all Donated Goods Used in Charitable Activities",
                "entry_by": user
            }
        ]
        Source.objects.bulk_create(Source(**data) for data in source)
        self.stdout.write(
            self.style.SUCCESS("Successfully created default Sources")
        )
