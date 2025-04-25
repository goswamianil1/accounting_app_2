from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class VoucherType:
    # Purchase Related
    PURCHASE = 'purchase'
    PURCHASE_RETURN = 'purchase_return'
    
    # Sale Related
    SALE = 'sale'
    SALE_RETURN = 'sale_return'
    SALE_QUOTATION = 'sale_quotation'
    
    # Payment Related
    PAYMENT = 'payment'
    RECEIPT = 'receipt'
    CONTRA = 'contra'
    
    # Other Types
    JOURNAL = 'journal'
    DEBIT_NOTE = 'debit_note'
    CREDIT_NOTE = 'credit_note'

    CHOICES = [
        (PURCHASE, 'Purchase'),
        (PURCHASE_RETURN, 'Purchase Return'),
        (SALE, 'Sale'),
        (SALE_RETURN, 'Sale Return'),
        (SALE_QUOTATION, 'Sale Quotation'),
        (PAYMENT, 'Payment'),
        (RECEIPT, 'Receipt'),
        (CONTRA, 'Contra'),
        (JOURNAL, 'Journal'),
        (DEBIT_NOTE, 'Debit Note'),
        (CREDIT_NOTE, 'Credit Note'),
    ]

class AccountType(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']

class VoucherStatus:
    DRAFT = 'draft'
    POSTED = 'posted'
    CANCELLED = 'cancelled'

    CHOICES = [
        (DRAFT, 'Draft'),
        (POSTED, 'Posted'),
        (CANCELLED, 'Cancelled'),
    ]

class EntryType(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']

class AccountGroup(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Account(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name='accounts')
    group = models.ForeignKey(AccountGroup, on_delete=models.CASCADE, related_name='accounts')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']

class Item(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=20)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    hsn_code = models.CharField(max_length=20, blank=True, null=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['name']

class Voucher(models.Model):
    number = models.CharField(max_length=20, unique=True)
    date = models.DateField()
    voucher_type = models.CharField(max_length=20, choices=VoucherType.CHOICES)
    status = models.CharField(max_length=10, choices=VoucherStatus.CHOICES, default=VoucherStatus.DRAFT)
    party = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='vouchers')
    
    # Common fields
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    narration = models.TextField(blank=True, null=True)
    
    # Additional fields for specific voucher types
    reference_number = models.CharField(max_length=100, blank=True, null=True)  # For purchase/sale reference
    due_date = models.DateField(null=True, blank=True)  # For credit purchases/sales
    shipping_address = models.TextField(blank=True, null=True)  # For sales
    shipping_gstin = models.CharField(max_length=15, blank=True, null=True)  # For sales
    return_reason = models.TextField(blank=True, null=True)  # For returns
    reference_voucher = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_vouchers')  # For returns/credit notes
    terms_conditions = models.TextField(blank=True, null=True)  # For quotations
    validity_date = models.DateField(null=True, blank=True)  # For quotations
    is_converted = models.BooleanField(default=False)  # For quotations
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.voucher_type} - {self.number} ({self.date})"

    class Meta:
        ordering = ['-date', 'number']
        indexes = [
            models.Index(fields=['voucher_type', 'date']),
            models.Index(fields=['party', 'voucher_type']),
            models.Index(fields=['status', 'voucher_type']),
        ]

class VoucherItem(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.name} - {self.quantity} x {self.rate}"

    class Meta:
        indexes = [
            models.Index(fields=['voucher', 'item']),
        ]

class AccountEntry(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='account_entries')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='entries')
    entry_type = models.ForeignKey(EntryType, on_delete=models.CASCADE, related_name='entries')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    narration = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.account.name} - {self.entry_type.name} - {self.amount}"

    class Meta:
        verbose_name_plural = "Account Entries"
        indexes = [
            models.Index(fields=['voucher', 'account']),
            models.Index(fields=['entry_type', 'account']),
        ]

class AuditTrail(models.Model):
    ACTION_TYPES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    details = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} {self.object_id} at {self.timestamp}"

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrator'),
        ('ACCOUNTANT', 'Accountant'),
        ('VIEWER', 'Viewer'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='VIEWER')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    def has_permission(self, permission):
        if self.role == 'ADMIN':
            return True
        elif self.role == 'ACCOUNTANT':
            return permission in ['view', 'add', 'change']
        elif self.role == 'VIEWER':
            return permission == 'view'
        return False

class TrialBalance(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_type = models.ForeignKey(EntryType, on_delete=models.CASCADE, related_name='trial_balances')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['account', 'date']
        ordering = ['account__name']

    def __str__(self):
        return f"{self.account.name} - {self.date}"

class ProfitLoss(models.Model):
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_income = models.BooleanField(default=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['category', 'date']
        ordering = ['-date', 'category']

    def __str__(self):
        return f"{self.category} - {self.date}"

class GSTR1(models.Model):
    gstin = models.CharField(max_length=15)
    invoice_number = models.CharField(max_length=20)
    invoice_date = models.DateField()
    customer_name = models.CharField(max_length=100)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=2)
    cgst_amount = models.DecimalField(max_digits=15, decimal_places=2)
    sgst_amount = models.DecimalField(max_digits=15, decimal_places=2)
    igst_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['gstin', 'invoice_number']
        ordering = ['-invoice_date']

    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name}"

class GSTR2(models.Model):
    gstin = models.CharField(max_length=15)
    invoice_number = models.CharField(max_length=20)
    invoice_date = models.DateField()
    supplier_name = models.CharField(max_length=100)
    taxable_value = models.DecimalField(max_digits=15, decimal_places=2)
    cgst_amount = models.DecimalField(max_digits=15, decimal_places=2)
    sgst_amount = models.DecimalField(max_digits=15, decimal_places=2)
    igst_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['gstin', 'invoice_number']
        ordering = ['-invoice_date']

    def __str__(self):
        return f"{self.invoice_number} - {self.supplier_name}"

class GSTR3B(models.Model):
    period = models.CharField(max_length=7)  # Format: MM-YYYY
    outward_supplies = models.DecimalField(max_digits=15, decimal_places=2)
    inward_supplies = models.DecimalField(max_digits=15, decimal_places=2)
    cgst_payable = models.DecimalField(max_digits=15, decimal_places=2)
    sgst_payable = models.DecimalField(max_digits=15, decimal_places=2)
    igst_payable = models.DecimalField(max_digits=15, decimal_places=2)
    cgst_input = models.DecimalField(max_digits=15, decimal_places=2)
    sgst_input = models.DecimalField(max_digits=15, decimal_places=2)
    igst_input = models.DecimalField(max_digits=15, decimal_places=2)
    net_tax_payable = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['period']
        ordering = ['-period']

    def __str__(self):
        return f"GSTR-3B - {self.period}"
