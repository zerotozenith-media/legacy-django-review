import io
import logging
import re
import json
from datetime import datetime, date
from decimal import Decimal

import fitz
from django.contrib.auth import get_user_model
from django.db import transaction
from openpyxl.reader.excel import load_workbook

from authentication.models import User
from contributor.models import TransactionType, MiscellaneousContribution, Contribution, MiscellaneousUser
import pymupdf

from organization.models import LocalChurch, LocalChurchName, Region


def validate_date(value):
    if isinstance(value, (datetime, date)):
        return True
    if isinstance(value, str):
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
    return False

def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None

def validate_date_offerings(date):
    try:
        if isinstance(date, str):
            # Assuming date format is '17-Dec-23'
            datetime.strptime(date, '%Y-%m-%d').date()
            return True
        else:
            date = date.date()
            return True
    except ValueError:
        return False


def validate_amount(amount_string):
    # Allow an optional decimal point with up to 6 digits after it
    if isinstance(amount_string, float) or isinstance(amount_string, int):
        return True
    pattern = re.compile(r'\$\d+(\.\d{1,6})?$')
    return bool(pattern.match(amount_string))


def check_amount(amount_string):
    if isinstance(amount_string, float) or isinstance(amount_string, int):
        return True
    pattern = re.compile(r'^[-+]?[0-9]*\.?[0-9]+$')
    return bool(pattern.match(amount_string))


def parse_amount(amount_string):
    if isinstance(amount_string, (int, float)):
        return Decimal(str(amount_string))

    pattern = re.compile(r'^\$?(\d+(\.\d{1,6})?)$')
    match = pattern.match(str(amount_string))

    if match:
        return Decimal(match.group(1))
    else:
        return 0


def validate_headers(worksheet):
    headers = [cell.value.strip() if cell.value else None for cell in worksheet[1]]
    return headers == ["Date Deposited", "Received From", "Amount"]


def handle_uploaded_file(file, local_church_id):
    try:
        workbook = load_workbook(file, read_only=True)
        worksheet = workbook.active

        # Validate Headers
        if not validate_headers(worksheet):
            return {'error': 'Invalid headers'}

        for row in worksheet.iter_rows(min_row=2, values_only=True):
            print(row)
            if row == ():
                break

            date_deposited, received_from, amount = row[0], row[1], row[2]

            # Validate Date Deposited
            if not validate_date_offerings(date_deposited):
                return {'error': f'Invalid date format: {date_deposited}'}

            # Validate Amount
            if not validate_amount(amount):
                return {'error': f'Invalid amount format: {amount}'}

        process_and_save_data(worksheet, local_church_id)

        return None

    except Exception as e:
        return {'error': f'Error processing the file: {str(e)}'}


def extract_pdf_text(file):
    doc = pymupdf.open(stream=file.file, filetype="pdf")

    # Extract text from each page
    extracted_text = ""
    for page_num in range(doc.page_count):
        page = doc[page_num]
        extracted_text += page.get_text("text") + "\n"  # "text" mode preserves formatting
    print(f"***ORIGINAL TEXT from {file}")
    print(extracted_text)
    doc.close()
    return extracted_text


def adapt_transaction_data_format(tx, local_church_id):
    return {
        "contributor_name": tx['name'],
        "local_church_id": local_church_id,
        "type": TransactionType.INTEREC_E_TRANSFER.value,
        "deposit_date": str(datetime.strptime(tx['date'], "%b %d, %Y").strftime("%Y-%m-%d")),
        "amount": parse_amount(tx['amount'].replace("$", "").replace(",", "")),
        "special_contribution": False
    }


def parse_pdf(document_text):
    from contributor.llm_pdf_parsing import doc_intelligence

    output = doc_intelligence(document_text)
    output = output.replace('```python', '').replace('```json', '').replace('```', '').replace('\n', '')
    # print(json.loads(output))
    return json.loads(output)


def create_user_with_ful_name_and_region(full_name, region_id):
    """When adding contribution from bank statement we create a user if the user is not
    already created.
    """
    name_parts = full_name.split()
    first_name = name_parts[0] if len(name_parts) > 0 else None
    middle_name = name_parts[1] if len(name_parts) > 2 else None
    last_name = name_parts[-1] if len(name_parts) > 1 else None

    region = Region.objects.filter(id=region_id).first()

    # Generate email based on available name information
    if first_name and last_name:
        email = f"{first_name.lower()}.{last_name.lower()}@{region.name.lower()}.example.com"
    else:
        email = f"user{region}@{region.name.lower()}.example.com"

    # Ensure email uniqueness
    counter = 1
    original_email = email
    while User.objects.filter(email=email).exists():
        email = f"{original_email.split('@')[0]}{counter}@{region.name.lower()}.example.com"
        counter += 1

    # Get or create a placeholder local church for the region
    local_church_name, created = LocalChurchName.objects.get_or_create(title="Unassigned")
    placeholder_church, created = LocalChurch.objects.get_or_create(
        local_church_name=local_church_name,
        region=region,
        defaults={
            "local_church_pastor": None
        }
    )

    # Create the user
    user = User.objects.create(
        full_name=full_name,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        email=email,
        role=User.MEMBER,  # Default role
        local_church=placeholder_church  # Assign placeholder local church
    )
    return user


def adapt_bank_statement_transaction_data_format(tx, region_id, account_type):
    return {
        "contributor_name": tx['name'],
        "type_": TransactionType.INTEREC_E_TRANSFER.value,
        "deposit_date": str(datetime.strptime(tx['date'], "%b %d, %Y").strftime("%Y-%m-%d")),
        "amount": parse_amount(tx['amount'].replace("$", "").replace(",", "")),
        "special_contribution": False,
        "region_id": region_id,
        "account_type": account_type,
    }


def handle_bank_statement(file, region_id, account_type):
    """Handle populating contributions from bank statement"""
    try:
        transactions = extract_transactions_with_pymupdf(file)
        for tx in transactions:
            add_bank_statement_contribution(**adapt_bank_statement_transaction_data_format(tx, region_id, account_type))
    except Exception as e:
        logging.exception(str(e))
        return {'error': f'Error processing the file: {str(e)}'}

    # try:
    #     text = extract_pdf_text(file)
    #     transactions = parse_pdf(text)
    #     for tx in transactions:
    #         add_bank_statement_contribution(**adapt_bank_statement_transaction_data_format(tx,
    #         region_id, account_type))
    # except Exception as e:
    #     logging.exception(str(e))
    #     return {'error': f'Error processing the file: {str(e)}'}

def get_user(name, local_church_id):
    user_model = get_user_model()
    user = user_model.objects.filter(full_name__exact=name, local_church_id=local_church_id).first()
    return user


def create_or_get_miscellaneous_contributor(name, registered_by, **kwargs):
    email = kwargs.get('email', None)
    first_name = kwargs.get('first_name', None)
    middle_name = kwargs.get('middle_name', None)
    last_name = kwargs.get('last_name', None)
    address = kwargs.get('address', None)
    miscellaneous = MiscellaneousUser.objects
    user = miscellaneous.filter(email=email).first() if email else miscellaneous.filter(full_name=name.strip()).first()
    if not user:
        user = MiscellaneousUser.objects.create(
            full_name=name,
            email=email,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            address=address,
            registered_miscellaneous=registered_by if registered_by else None
        )
    return user


def add_contribution(local_church_id, contributor_name, type, deposit_date, amount, special_contribution,
                     registered_by=None, can_edit=False,
                     **kwargs):
    print(special_contribution)
    registered_user = get_user(contributor_name, local_church_id)
    date_object = datetime.strptime(str(deposit_date), '%Y-%m-%d')
    month_name = date_object.strftime('%B')
    if not registered_user:
        misc_user = create_or_get_miscellaneous_contributor(contributor_name, registered_by, **kwargs)
        contribution = MiscellaneousContribution.objects.create(
            local_church_id=local_church_id,
            contributor=misc_user,
            payment_type=type,
            deposited_date=deposit_date,
            amount=amount,
            special_contribution=special_contribution,
            month=month_name
        )

        return contribution
    else:
        contribution = Contribution.objects.create(
            local_church_id=local_church_id,
            contributor=registered_user,
            payment_type=type,
            deposited_date=deposit_date,
            amount=amount,
            special_contribution=special_contribution,
            month=month_name
        )
        return contribution


def create_or_get_bank_statement_miscellaneous_contributor(contributor_name, region_id):
    region = Region.objects.filter(id=region_id).first()
    miscellaneous_user = MiscellaneousUser.objects.filter(full_name__exact=contributor_name,
                                                          registered_miscellaneous=region.region_overseer
                                                          ).first()
    if not miscellaneous_user:
        miscellaneous_user = MiscellaneousUser.objects.create(full_name=contributor_name,
                                                              can_edit_full_name=False,
                                                              registered_miscellaneous=region.region_overseer)
    return miscellaneous_user


def add_bank_statement_contribution(contributor_name, type_, deposit_date, amount, special_contribution,
                                    region_id, account_type):
    registered_user = get_user_model().objects.filter(full_name__exact=contributor_name,
                                                      local_church__region_id=region_id).first()
    date_object = datetime.strptime(str(deposit_date), '%Y-%m-%d')
    month_name = date_object.strftime('%B')
    if not registered_user:
        misc_user = create_or_get_bank_statement_miscellaneous_contributor(contributor_name, region_id)
        contribution = MiscellaneousContribution.objects.get_or_create(
            contributor=misc_user,
            payment_type=type_,
            deposited_date=deposit_date,
            amount=amount,
            special_contribution=special_contribution,
            month=month_name,
            account_type=account_type,
            can_edit=False
        )
        return contribution
    else:
        contribution = Contribution.objects.get_or_create(
            local_church_id=registered_user.local_church_id,
            contributor=registered_user,
            payment_type=type_,
            deposited_date=deposit_date,
            amount=amount,
            special_contribution=special_contribution,
            month=month_name,
            account_type=account_type,
            can_edit=False
        )
        return contribution


def process_and_save_data(worksheet, local_church_id):
    with transaction.atomic():
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            print('process and save')
            print(row)
            if row == ():
                break
            date, name, amount = row[0], row[1], row[2]
            data = {
                "contributor_name": name,
                "local_church_id": local_church_id,
                "type": TransactionType.INTEREC_E_TRANSFER.value,
                "deposit_date": (str(date)),
                "amount": parse_amount(amount),
                "special_contribution": False
            }
            add_contribution(**data)


"""
offering file handling
"""


def validate_offering_amount(amount_input):
    if isinstance(amount_input, (int, float)):
        return True

    pattern = re.compile(r'^\$?(\d+(\.\d{1,6})?)$')
    match = pattern.match(str(amount_input))

    return bool(match)


def name_split(full_name):
    name = str(full_name).split(' ')
    if len(name) == 1:
        return name[0], '', ''
    elif len(name) == 2:
        return name[0], '', name[1]
    elif len(name) == 3:
        return name[0], name[1], name[2]
    return full_name, '', ''


def validate_offering_header(worksheet):
    headers = [cell.value.strip() if cell.value else None for cell in worksheet[1]]
    return headers == ['First Name', 'Middle Name', 'Last Name', 'Email', 'Address', 'Date Deposited', 'Amount']


def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


def handle_uploaded_for_offering(file, type, local_church_id, registered_by):
    try:
        workbook = load_workbook(file, read_only=True)
        worksheet = workbook.active

        # Validate Headers
        if not validate_offering_header(worksheet):
            return {'error': 'Invalid headers'}

        for row_number, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
            first_name, middle_name, last_name, email, address, date_deposited, amount = (
                row[0], row[1], row[2], row[3], row[4], row[5], row[6])
            if not any(row):
                break

            # Validate Date Deposited
            if not validate_date(date_deposited):
                return {'error': f'Invalid date format: {date_deposited} at row number {row_number}'}

            # Validate Amount
            if not validate_offering_amount(amount):
                return {'error': f'Invalid amount format: {amount} at row number {row_number}'}

            if not first_name or not last_name:
                return {'error': f'Required field missing in row {row_number}. Please provide name'}

            if email and not validate_email(email):
                return {'error': f'Invalid Email {email} at row {row_number}.'}

        process_and_save_offering_data(worksheet, type, local_church_id, registered_by)

        return None

    except Exception as e:
        return {'error': f'Error processing the file: {str(e)}'}


def process_and_save_offering_data(worksheet, type, local_church_id, registered_by):
    with transaction.atomic():
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            first_name, middle_name, last_name, email, address, date_deposited, amount = (
                row[0], row[1], row[2], row[3], row[4], row[5], row[6])
            if row[0] is None:
                break
            if first_name:
                first_name = first_name.strip()
            if middle_name:
                middle_name = middle_name.strip()
            if last_name:
                last_name = last_name.strip()
            if middle_name:
                full_name = " ".join([first_name, middle_name, last_name])
            else:
                full_name = " ".join([first_name, last_name])

            data = {
                "local_church_id": local_church_id,
                "contributor_name": full_name,
                "type": type,
                "deposit_date": (str(date_deposited)),
                "amount": parse_amount(amount),
                "special_contribution": False,
                "email": email,
                "address": address,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "registered_by": registered_by
            }
            add_contribution(**data)


def extract_transactions_with_pymupdf(file_path):
    transactions = []

    print(file_path)

    file_stream = io.BytesIO(file_path.read())
    doc = fitz.open(stream=file_stream, filetype="pdf")

    for page in doc:
        text = page.get_text()  # Extract text from the page
        # Regex to match the rows in the transaction table
        matches = re.findall(
            r"(\w{3} \d{2}, \d{4})\s+([\w\s.]+)\s+(\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(Email/Mobile)\s+(Autodeposited)",
            text
        )
        for match in matches:
            transactions.append({
                "date": match[0],
                "name": match[1].strip(),
                "amount": match[2],
                "method": match[3],
                "status": match[4]
            })

    doc.close()
    return transactions
