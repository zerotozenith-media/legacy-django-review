import traceback

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse

from authentication.models import User
from authentication.utils import account_activation_token
from expenses.models import Category, SubCategory
from income.models import Source
from organization.models import Branch, Region, BankAccount
from authentication.middleware import Role
from django.core.mail import EmailMessage
from django.contrib import messages
from django.template.loader import render_to_string
class Command(BaseCommand):
    help = "Database seed"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with transaction.atomic():
            # self.add_users()
            self.add_branches()
            self.add_categories()
            self.add_default_source()
            self.add_back_account()
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
        users = {
            "branch_manager": [{
                "email": "branch_manager_15@yopmail.com",
                "password": "12345",
                "first_name": "branch",
                "last_name": "manager 1",
            },
            {
                "email": "branch_manager_25@yopmail.com",
                "password": "12345",
                "first_name": "branch",
                "last_name": "manager 2",
            }],
            "head_officer": [{
                "email": "head_officer15@yopmail.com",
                "password": "12345",
                "first_name": "head",
                "last_name": "officer 1",
            },
            {
                "email": "head_officer25@yopmail.com",
                "password": "12345",
                "first_name": "head",
                "last_name": "officer 2",
            }],
            "region_manager": [{
                "email": "region_manager_15@yopmail.com",
                "password": "12345",
                "first_name": "region",
                "last_name": "manager 1"
            },
            {
                "email": "region_manager_25@yopmail.com",
                "password": "12345",
                "first_name": "region",
                "last_name": "manager 2",
            }]
        }
        user_objects = []
        success = 0
        fail = 0
        for role_name, users_data in users.items():
            if role_name == "branch_manager":
                role = Role.branch_leader.value
            elif role_name == "head_officer":
                role = Role.head_officer.value
            elif role_name == "region_manager":
                role = Role.region_manager.value
            for user_data in users_data:
                if user_data.get("email") and not User.objects.filter(email=user_data.get("email")).exists():
                    user = User.objects.create_user(**user_data, role=role)
                    self.send_activation_email(user, user_data.get("password"))
                    success += 1
                else:
                    fail += 1
        self.stdout.write(self.style.SUCCESS("Successfully created {} users and {} failed".format(success, fail)))
    def add_branches(self):
        """
        Populate DB with branches
        """
        # TO DO: determine if we can set branch type on seeding
        branches_data = {
            "NOVA_SCOTIA": [
                "NFL"
            ],
            "NEW_BRUNSWICK": [
                "St John",
                "Moncton",
                "Fredericton"
            ],
            "PRINCE_EDWARD_ISLAND": [
                "Prince Edward Island"
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
                "Osborne Campus"
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
                "Edmonton S"
            ],
            "BRITISH_COLUMBIA": [
                "Surrey",
                "Prince George",
                "Nanaimo",
                "Kelowna"
            ],
            "BARRIE": [
                "Barrie",
                "Sudbury"
            ],
            "CAMROSE": [
                "Camrose"
            ]
        }

        location_mapping = {
            "ALBERTA": Branch.ALBERTA,
            "BRITISH_COLUMBIA": Branch.BRITISH_COLUMBIA,
            "SASKATCHEWAN": Branch.SASKATCHEWAN,
            "MANITOBA": Branch.MANITOBA,
            "ONTARIO": Branch.ONTARIO,
            "OTTAWA": Branch.OTTAWA,
            "QUEBEC": Branch.QUEBEC,
            "NEWFOUNDLAND_AND_LABRADOR": Branch.NEWFOUNDLAND_AND_LABRADOR,
            "NOVA_SCOTIA": Branch.NOVA_SCOTIA,
            "NEW_BRUNSWICK": Branch.NEW_BRUNSWICK,
            "PRINCE_EDWARD_ISLAND": Branch.PRINCE_EDWARD_ISLAND,
        }
        # give region managers email
        region_manager = {
            "ALBERTA": "region_manager_15@yopmail.com",
            "BRITISH_COLUMBIA": "region_manager_15@yopmail.com",
            "SASKATCHEWAN": "region_manager_15@yopmail.com",
            "MANITOBA": "region_manager_15@yopmail.com",
            "ONTARIO": "region_manager_15@yopmail.com",
            "OTTAWA": "region_manager_15@yopmail.com",
            "QUEBEC": "region_manager_15@yopmail.com",
            "NEWFOUNDLAND_AND_LABRADOR": "region_manager_15@yopmail.com",
            "NOVA_SCOTIA": "region_manager_15@yopmail.com",
            "NEW_BRUNSWICK": "region_manager_15@yopmail.com",
            "PRINCE_EDWARD_ISLAND": "region_manager_15@yopmail.com"
        }
        branch_leaders = {'Prince_George': 'branch_manager_15@yopmail.com',
                          'Burns_Lake': 'branch_manager_15@yopmail.com',
                          'Nanaimo': 'branch_manager_15@yopmail.com',
                          'Kelowna': 'branch_manager_15@yopmail.com',
                          'Surrey': 'branch_manager_15@yopmail.com',
                          'Fort-McMurray': 'branch_manager_15@yopmail.com',
                          'Edmont_E': 'branch_manager_15@yopmail.com',
                          'Edmonton_W': 'branch_manager_15@yopmail.com',
                          'Edmont_S': 'branch_manager_15@yopmail.com',
                          'Camrose': 'branch_manager_15@yopmail.com',
                          'Calgary_N': 'branch_manager_15@yopmail.com',
                          'Calgary_Mid-town': 'branch_manager_15@yopmail.com',
                          'Calgary_S': 'branch_manager_15@yopmail.com',
                          'Saskatoon_East': 'branch_manager_15@yopmail.com',
                          'Saskatoon_West': 'branch_manager_15@yopmail.com',
                          'Prinec_Albert': 'branch_manager_15@yopmail.com',
                          'Regina': 'branch_manager_15@yopmail.com',
                          'St_Mary_Rd_MB': 'branch_manager_15@yopmail.com',
                          'Osborne_MB': 'branch_manager_15@yopmail.com',
                          'Brandon_MB': 'branch_manager_15@yopmail.com',
                          'Go-Ye': 'branch_manager_15@yopmail.com',
                          'Windsor_ON': 'branch_manager_15@yopmail.com',
                          'Thunder_Bay': 'branch_manager_15@yopmail.com',
                          'Kitchener': 'branch_manager_15@yopmail.com',
                          'Online_Church': 'branch_manager_15@yopmail.com',
                          'Brampton': 'branch_manager_15@yopmail.com',
                          'Hamilton': 'branch_manager_15@yopmail.com',
                          'Barrie': 'branch_manager_15@yopmail.com',
                          'Vaughan_ON': 'branch_manager_15@yopmail.com',
                          'Oakdale': 'branch_manager_15@yopmail.com',
                          'London_Ontario': 'branch_manager_15@yopmail.com',
                          'Scarborough': 'branch_manager_15@yopmail.com',
                          'Sudbury': 'branch_manager_15@yopmail.com',
                          'Oshawa': 'branch_manager_15@yopmail.com',
                          'Ottawa': 'branch_manager_15@yopmail.com',
                          'Montreal': 'branch_manager_15@yopmail.com',
                          'Quebec': 'branch_manager_15@yopmail.com',
                          "St_John's_NFL": 'branch_manager_15@yopmail.com',
                          'Cope_Breton': 'branch_manager_15@yopmail.com',
                          'Truro': 'branch_manager_15@yopmail.com',
                          'Halifax_NS': 'branch_manager_15@yopmail.com',
                          'Antigonish_NS': 'branch_manager_15@yopmail.com',
                          'Federiction_NB': 'branch_manager_15@yopmail.com',
                          'Moncton_NB': 'branch_manager_15@yopmail.com',
                          'St_John_NB': 'branch_manager_15@yopmail.com',
                          'Charlottetown_PEI': 'branch_manager_15@yopmail.com'
                          }


        default_manager = User.objects.first()
        branch_objects = []
        for branch_location, branch_names in branches_data.items():
            print("branch location", branch_location, " branch names", branch_names)
            words = branch_location.split('_')
            print("words", words)
            region_object = Region(
                name=' '.join(words),
                manager=User.objects.filter(email=region_manager[branch_location]).first()
            )
            region_object.save()
            for branch_name in branch_names:
                branch = Branch(
                    branch_location=location_mapping.get(branch_location),
                    branch_name=branch_name,
                    manager=User.objects.filter(email=branch_leaders['_'.join(branch_name.split(' '))]).first(),
                    region=region_object
                )
                branch_objects.append(branch)
        Branch.objects.bulk_create(branch_objects)
        self.stdout.write(self.style.SUCCESS("Successfully created branches"))

    def add_categories(self):
        "Populate Category and Subcategories"

        categories_data = {
            "RECURRENT": {
                "Advertising and Promotion": [
                    "Advertisement",
                    "Promotion / Retreat Expenses",
                    "Special Programs -M&WF",
                    "Outreach Activities",
                    "Tracts, Books and other printed Materials",
                ],
                "Travel and Vehicle Expenses": [
                    "Vehicle Registration and Insurance",
                    "Vehicle Repairs / Maintenance",
                    "Gas / Fueling" "Flights - local, national and international",
                    "Ground Transport - buses, taxis, airport taxi, etc"
                    "Car Hire, Rental Expenses",
                    "Other Transportation Expenses - Rail, Sea, etc",
                ],
                "Interest and Bank Charges": [
                    "Mortgage Interest",
                    "Interests Paid on Loans",
                    "Bank Charges",
                ],
                "Licences, Memberships and Dues": [
                    "Professional Licence Fees",
                    "Membership Fees / Dues",
                    "Contributions to external bodies",
                ],
                "Office Supplies and Expenses": [
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
                "Professional and Consulting Fees": [
                    "Professional Fees",
                    "Consulting Fees",
                    "Honorarium",
                    "Pastoral Care",
                ],
                "Education and Training For Staff and Volunteers": [
                    "Campus",
                    "Youth",
                    "Children",
                    "Sunday School / Choir",
                    "Home Fellowships",
                    "Support to other sections",
                    "Other Training/Education activities",
                ],
                "Research Grants and Scholarships/Charitable Activities": [
                    "Research Grants",
                    "Scholarships",
                    "Support to Needy Students and others",
                    "Other Charity Activities",
                ],
                "All Other Expenditues not included": [
                    "Amounts Above (excluding gifts to qualified donnees)",
                    "Refunded fund mistakenly paid to church",
                ],
            },
            "CAPITAL": {
                "Purchase Supplies and Assets": [
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
        bank_accounts = [
            {
                "branch_name": "Prince George",
                "account_name": "Tithe and offerings",
                "account_number": "5202022",
                "account_description": "",
                "balance": 12345.123456,
            },
            {
                "branch_name": "Burns Lake",
                "account_name": "DLICC",
                "account_number": "5256423",
                "account_description": "DLICC or projects outside Canada",
                "balance": 456.6,
            },
            {
                "branch_name": "Nanaimo",
                "account_name": "Non-tax account",
                "account_number": "5256601",
                "account_description": "Money that has nothing to do with tax receipt. E.g. Buying book or balance of money not spent - overpaid money",
                "balance": 459.09,
            }
        ]
        for bank_account in bank_accounts:
            tagged_branch = Branch.objects.filter(branch_name__exact=bank_account.get("branch_name")).first()
            bank_ac = BankAccount.objects.create(
                branch=tagged_branch,
                account_name=bank_account.get("account_name"),
                account_number=bank_account.get("account_number"),
                account_description=bank_account.get("account_description", ""),
                balance=bank_account.get("balance", 0)
            )
        self.stdout.write(
            self.style.SUCCESS("Successfully created default bank accounts")
        )




    def add_default_source(self):
        user = User.objects.filter(is_superuser=True, is_staff=True, is_active=True).first()
        source = [
            {
                'name': "Tithe and Offerings",
                "type": "Income",
                "description": "Tithe and Offerings",
                "entry_by": user
            },
            {
                'name': "DLICC or Projects Outside Canada",
                "type": "Income",
                "description": "DLICC or Projects Outside Canada",
                "entry_by": user
            },
            {
                'name': "Non-Taxable",
                "type": "Income",
                "description": "Non-Taxable",
                "entry_by": user
            }
        ]
        Source.objects.bulk_create(Source(**data) for data in source)
        self.stdout.write(
            self.style.SUCCESS("Successfully created default Sources")
        )
