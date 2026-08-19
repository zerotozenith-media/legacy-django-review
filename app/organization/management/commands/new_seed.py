import traceback

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from faker import Faker

from attendance.models import ChurchServices, Attendance
from authentication.models import User
from authentication.utils import account_activation_token
from church_properties.models import ChurchProperties
from contributor.models import MiscellaneousUser, Contribution, MiscellaneousContribution, AnonymousContribution
from expenses.models import Category, SubCategory, Expense
from income.models import Source, Income
from organization.models import LocalChurch, Region, BankAccount, LocalChurchName
from authentication.middleware import Role
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import random
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = "Database seed"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with transaction.atomic():
            self.add_users()
            self.add_local_churches()
            self.add_categories()
            self.add_default_source()
            # self.add_back_account()
            self.add_church_services()
            self.add_attendance()
            self.add_church_properties()
            self.add_contributions()
            self.add_income_and_expense()
            self.stdout.write(self.style.SUCCESS("Database seeding completed."))

    def send_activation_email(self, user, password):
        # current_site = get_current_site(request)
        domain = "127.0.0.1:8000"
        email_body = {
            "user": user,
            "domain": domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
        }

        link = reverse(
            "activate", kwargs={"uidb64": email_body["uid"], "token": email_body["token"]}
        )
        activate_url = "http://" + domain + link

        email_subject = "Activate your account"

        try:
            email_body_html = render_to_string('authentication/seed_user_email.html', {
                'user': user,
                'password': password,
                'activate_url': activate_url,
            })
            email_message = EmailMessage(
                email_subject,
                body=email_body_html,
                from_email="dclmcafinance@gmail.com",
                to=[user.email],
                bcc=["ugurunedu@gmail.com"],
            )
            email_message.content_subtype = 'html'
            email_message.send()
        except Exception as e:
            print(str(e))
            traceback.print_exc()

    def add_users(self):
        # Create the admin user
        admin_email = "admin@local.com"
        admin_password = "password123"
        if not User.objects.filter(email=admin_email).exists():
            admin_user = User.objects.create_superuser(
                email=admin_email,
                password=admin_password,
                first_name="Admin",
                last_name="User"
            )
            self.stdout.write(self.style.SUCCESS(f"Admin user created with email: {admin_email}"))
        else:
            self.stdout.write(self.style.WARNING(f"Admin user with email {admin_email} already exists."))
        if not User.objects.filter(email='national_overseer@dclmca.com').exists():
            admin_user = User.objects.create_superuser(
                email='national_overseer@dclmca.com',
                password=admin_password,
                first_name="National",
                last_name="Overseer",
                role = Role.national_overseer.value
            )
            self.stdout.write(self.style.SUCCESS(f"National overseer user created with email: national_overseer@dclmca.com"))
        else:
            self.stdout.write(self.style.WARNING(f"Admin user with email national_overseer@dclmca.com already exists."))

        # Generate 10 simple users with fake data
        fake = Faker()
        success = 0
        fail = 0
        for _ in range(10):
            email = fake.email()
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    role= Role.member.value,
                    email=email,
                    password="123456",
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                )
                success += 1
            else:
                fail += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully created {success} simple users and {fail} failed"))


    def add_local_churches(self):
        """
        Populate DB with branches
        """
        # TO DO: determine if we can set branch type on seeding
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
            print(region_name, church_list)
            print(region.lower())
            # create region overseer user
            user_overseer = {
                "email": f"region_overseer@{region.lower()}.ca",
                "password": "12345",
                "first_name": region_name,
                "last_name": "Region Overseer",
            }
            role = Role.region_overseer.value
            region_overseer = User.objects.create_user(**user_overseer, role=role)
            # self.send_activation_email(region_overseer, user_overseer.get("password"))
            # creating region object
            region_object = Region(
                name=region_name.replace("_", " "),
                region_overseer=region_overseer
            )
            region_object.save()
            for church in church_list:
                # create local church pastor user for church
                user_pastor = {
                    "email": f"local_church_pastor@{church.replace(' ', '').lower()}.ca",
                    "password": "12345",
                    "first_name": church,
                    "last_name": "Pastor",
                }
                role = Role.local_church_pastor.value
                local_church_pastor = User.objects.create_user(**user_pastor, role=role)
                # self.send_activation_email(local_church_pastor, user_pastor.get("password"))
                # create local church
                local_church_name = LocalChurchName.objects.create(title=church)
                local_church_object = LocalChurch.objects.create(
                    local_church_name=local_church_name,
                    local_church_pastor=local_church_pastor,
                    region=region_object
                )
                print(local_church_name, "save successfully")
            self.stdout.write(
                self.style.SUCCESS("Successfully created local churches and region overseers and local church pastors"))

    def add_categories(self):
        "Populate Category and Subcategories"

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
                    "Small Consummable Items",
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
                    "Small Equipments - cabinets, electricals, etc",
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

        regions = Region.objects.all()
        for region in regions:
            bank_ac = BankAccount.objects.create(
                region=region,
                account_name=f"{region.name.title()}",
                account_description="This is a regional branch",
                balance=random.randint(9999999, 10000000)
            )
            try:
                account_number = bank_accounts_numbers.get(region.name)
                if account_number:
                    bank_ac.account_number = str(account_number)
                else:
                    bank_ac.account_number = '000-000000'
            except Exception as e:
                print(e)
                bank_ac.account_number = '000-000000'
            bank_ac.save()
        self.stdout.write(
            self.style.SUCCESS("Successfully created default bank accounts")
        )

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
                "description": "Donations from unknow sources ",
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

    def add_attendance(self):
        today = datetime.today()
        current_year = today.year
        local_churches = LocalChurch.objects.all()
        church_services = ChurchServices.objects.all()
        if not local_churches:
            print('No local churches found in the database.')
            return

        for church in local_churches:
            for month in range(1, today.month + 1):
                for _ in range(6):  # Create 6 records per month
                    day = random.randint(1, 28)  # Avoid issues with different month lengths
                    date = datetime(current_year, month, day).date()
                    Attendance.objects.create(
                        church_service=random.choice(church_services),  # Replace with appropriate data if necessary
                        adult_male=random.randint(0, 100),
                        adult_female=random.randint(0, 100),
                        youth_male=random.randint(0, 100),
                        youth_female=random.randint(0, 100),
                        children_male=random.randint(0, 100),
                        children_female=random.randint(0, 100),
                        campus_male=random.randint(0, 100),
                        campus_female=random.randint(0, 100),
                        cau=random.randint(0, 100),
                        visitor=random.randint(0, 100),
                        conv=random.randint(0, 100),
                        ypf_male=random.randint(0, 100),
                        ypf_female=random.randint(0, 100),
                        zoom=random.randint(0, 100),
                        youtube=random.randint(0, 100),
                        date=date,
                        comment='This is a fake attendance record.',
                        local_church=church
                    )

        self.stdout.write(
            self.style.SUCCESS("Successfully created Attendance Record")
        )

    def add_church_properties(self):
        local_churches = LocalChurch.objects.all()

        if not local_churches:
            print('No local churches found in the database.')
            return

        for church in local_churches:
            for _ in range(10):  # Create 10 records per church
                ChurchProperties.objects.create(
                    local_church=church,
                    name=f'Property {random.randint(1, 1000)}',
                    purchase_date=datetime.today().date() - timedelta(days=random.randint(0, 365)),
                    description='This is a fake property description.',
                    serial_no=f'SN{random.randint(1000, 9999)}{church.id}{_}',
                    amount_paid=round(random.uniform(1000, 50000), 2),
                    disposal_date=None,  # or some date if needed
                    mode_of_disposal='N/A',
                    amount_sold=None  # or some amount if needed
                )

        self.stdout.write(
            self.style.SUCCESS("Successfully created Church Properties Record")
        )

    def add_contributions(self):
        today = datetime.today()
        local_churches = LocalChurch.objects.all()
        users = User.objects.all()
        miscellaneous_users = MiscellaneousUser.objects.all()

        if not local_churches:
            print('No local churches found in the database.')
            return
        if not users:
            print('No users found in the database.')
            return
        if not miscellaneous_users:
            print('No miscellaneous users found in the database. Creating new 10 users')
            n = 20
            fake = Faker()
            for _ in range(n):
                print(_)
                # Generate fake data
                first_name = fake.first_name()
                middle_name = fake.first_name()
                last_name = fake.last_name()
                full_name = f"{first_name} {middle_name} {last_name}"
                email = fake.unique.email()
                address = fake.address()

                # Create a MiscellaneousUser instance
                miscellaneous_user = MiscellaneousUser.objects.create(
                    full_name=full_name,
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                    email=email,
                    address=address,
                )

                # Create a corresponding User instance with the same details
                user = User.objects.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=fake.password()
                )

                # Link the created User to the MiscellaneousUser
                miscellaneous_user.registered_miscellaneous = user
                miscellaneous_user.save()

            print('New user created')
        miscellaneous_users = MiscellaneousUser.objects.all()

        for church in local_churches:
            print(church)
            for _ in range(10):  # Create 10 records per church
                amount = round(random.uniform(10, 500), 2)
                date = today - timedelta(days=random.randint(0, 365))
                user = random.choice(users)
                Contribution.objects.create(
                    contributor=user,
                    amount=amount,
                    deposited_date=date,
                    payment_type=random.choice([
                        'offerings_can',
                        'offerings_usd',
                        'interec_e_transfer',
                        'direct',
                        'online_deposited'
                    ]),
                    special_contribution=random.choice([True, False]),
                    month=date.strftime('%B'),
                    local_church=church
                )

            for _ in range(10):  # Create 10 records per church
                amount = round(random.uniform(10, 500), 2)
                date = today - timedelta(days=random.randint(0, 365))
                misc_user = random.choice(miscellaneous_users)
                MiscellaneousContribution.objects.create(
                    contributor=misc_user,
                    deposited_date=date,
                    amount=amount,
                    payment_type=random.choice([
                        'offerings_can',
                        'offerings_usd',
                        'interec_e_transfer',
                        'direct',
                        'online_deposited'
                    ]),
                    special_contribution=random.choice([True, False]),
                    month=date.strftime('%B'),
                    local_church=church
                )

            for _ in range(10):  # Create 10 records per church
                amount = round(random.uniform(10, 500), 2)
                date = today - timedelta(days=random.randint(0, 365))
                AnonymousContribution.objects.create(
                    deposited_date=date,
                    amount=amount,
                    payment_type=random.choice([
                        'offerings_can',
                        'offerings_usd',
                        'interec_e_transfer',
                        'direct',
                        'online_deposited'
                    ]),
                    special_contribution=random.choice([True, False]),
                    month=date.strftime('%B'),
                    local_church=church
                )

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully seeded fake data for Contribution, MiscellaneousContribution, and AnonymousContribution models.')
        )

    def add_income_and_expense(self):
        today = datetime.today()
        local_churches = LocalChurch.objects.all()
        categories = Category.objects.all()
        sub_categories = SubCategory.objects.all()
        sources = Source.objects.all()
        bank_accounts = BankAccount.objects.all()

        if not local_churches:
            print('No local churches found in the database.')
            return
        if not categories:
            print('No categories found in the database.')
            return
        if not sub_categories:
            print('No subcategories found in the database.')
            return
        if not sources:
            print('No sources found in the database.')
            return
        if not bank_accounts:
            print('No bank accounts found in the database.')
            return


        for church in local_churches:
            for _ in range(10):  # Create 10 records per church
                amount = round(random.uniform(100, 5000), 2)
                tax_amount = round(amount * random.uniform(0.05, 0.15), 2)
                date = today - timedelta(days=random.randint(0, 365))
                category = random.choice(categories)
                sub_category = random.choice(sub_categories) if random.choice([True, False]) else None
                Expense.objects.create(
                    local_church=church,
                    amount=amount,
                    tax_amount=tax_amount,
                    description='This is a fake expense description.',
                    date=date,
                    category=category,
                    sub_category=sub_category,
                    tax_category=random.choice([choice[0] for choice in Expense.TAX_CATEGORY_CHOICES])
                )

            for _ in range(10):  # Create 10 records per church
                amount = round(random.uniform(100, 5000), 2)
                date = today - timedelta(days=random.randint(0, 365))
                source = random.choice(sources)
                account = random.choice(bank_accounts)
                Income.objects.create(
                    local_church=church,
                    amount=amount,
                    description='This is a fake income description.',
                    date=date,
                    source=source,
                    account=account
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded fake data for Expense and Income models.'))
