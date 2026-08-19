from django.db import models
from core.models import BaseModel
from enum import Enum


class TransactionType(Enum):
    OFFERINGS_CAN = 'offerings_can'
    OFFERINGS_USD = 'offerings_usd'
    INTEREC_E_TRANSFER = 'interec_e_transfer'
    DIRECT = 'direct_transfer'
    ONLINE_DEPOSIT = 'cheque_deposit'


ACCOUNT_TYPE_CHOICES = [
    ('credit_account', 'Credit Account'),
    ('savings_account', 'Savings Account'),
]


class Contribution(BaseModel):
    contributor = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, default=None, related_name='contributor')
    amount = models.DecimalField(max_digits=10, decimal_places=6)
    deposited_date = models.DateField(null=True)
    payment_type = models.CharField(null=False, blank=False, max_length=20,default=TransactionType.OFFERINGS_CAN.value)
    special_contribution = models.BooleanField(default=False)
    month = models.CharField(max_length=20, default='N/A')
    local_church = models.ForeignKey('organization.LocalChurch',on_delete=models.CASCADE, null=True, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, null=True, blank=True)
    can_edit = models.BooleanField(default=True, help_text="If the contribution is from bank statement, then False")

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        contributor_name = self.contributor.full_name if self.contributor else "Anonymous"  # noqa
        church_name = self.local_church.local_church_name.title if self.local_church else "No Church"  # noqa
        return f"{contributor_name} - {self.amount:.2f} on {self.deposited_date} " \
               f"(Local Church - {church_name})"

    @property
    def type(self):
        return "Contribution"


class TaxReceipt(BaseModel):
    receipt_receiver = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, default=None,
                                         related_name='receipt_receiver')
    pdf_file = models.FileField(null=True)


class MiscellaneousUser(BaseModel):
    full_name = models.CharField(max_length=512, blank=True, null=True)
    first_name = models.CharField(max_length=256, blank=True, null=True)
    middle_name = models.CharField(max_length=256, blank=True, null=True)
    last_name = models.CharField(max_length=256, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    address = models.CharField(max_length=512, blank=True, null=True)
    can_edit_full_name = models.BooleanField(default=True, help_text="If the full name was added "
                                                                     "from the bank statement no need to edit it.")
    registered_miscellaneous = models.ForeignKey('authentication.User',  on_delete=models.SET_NULL, null=True, blank=True, default=None, related_name='registered_miscellaneous')

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return self.full_name


class MiscellaneousContribution(BaseModel):
    contributor = models.ForeignKey(MiscellaneousUser,  on_delete=models.SET_NULL, null=True, blank=True, default=None, related_name='contributor_miscellaneous')
    deposited_date = models.DateField(null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=6)
    payment_type = models.CharField(null=False, blank=False, max_length=20, default=TransactionType.OFFERINGS_CAN.value)
    special_contribution = models.BooleanField(default=False)
    month = models.CharField(max_length=20, default='N/A')
    local_church = models.ForeignKey('organization.LocalChurch',on_delete=models.CASCADE, null=True, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, null=True, blank=True)
    can_edit = models.BooleanField(default=True, help_text="If the contribution is from bank statement, then False")

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return str(self.amount) +' deposit on' +str(self.deposited_date)

    @property
    def type(self):
        return "Miscellaneous"


class AnonymousContribution(BaseModel):
    deposited_date = models.DateField(null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=6)
    payment_type = models.CharField(null=False, blank=False, max_length=20, default=TransactionType.OFFERINGS_CAN.value)
    special_contribution = models.BooleanField(default=False)
    month = models.CharField(max_length=20, default='N/A')
    local_church = models.ForeignKey('organization.LocalChurch',on_delete=models.CASCADE, null=True, blank=True)
    can_edit = models.BooleanField(default=True, help_text="If the contribution is from bank statement, then False")

    def __str__(self):
        return str(self.amount) + ' deposited on' + str(self.deposited_date)

    class Meta:
        db_table = 'anonymous_contribution'
        ordering = ['-created_date']

    @property
    def type(self):
        return "Anonymous"


class EmailQueue(models.Model):
    contributor_id = models.IntegerField()
    report_year = models.IntegerField()
    email = models.EmailField()
    report_type = models.CharField(max_length=20)  # 'interac' or 'offerings'
    created_at = models.DateTimeField(auto_now_add=True)
