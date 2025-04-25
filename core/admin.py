from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    AccountGroup,
    Account,
    Item,
    Voucher,
    VoucherItem,
    AccountEntry,
    AuditTrail,
    CustomUser,
    TrialBalance,
    ProfitLoss,
    GSTR1,
    GSTR2,
    GSTR3B
)

@admin.register(AccountGroup)
class AccountGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'group', 'balance', 'is_active')
    list_filter = ('account_type', 'is_active', 'group')
    search_fields = ('name', 'code', 'gst_number', 'pan_number')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'unit', 'rate', 'gst_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'hsn_code')

@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'voucher_type', 'party', 'total_amount', 'status')
    list_filter = ('voucher_type', 'status', 'date')
    search_fields = ('number', 'party__name', 'narration')
    date_hierarchy = 'date'

@admin.register(VoucherItem)
class VoucherItemAdmin(admin.ModelAdmin):
    list_display = ('voucher', 'item', 'quantity', 'rate', 'amount')
    list_filter = ('voucher__voucher_type',)
    search_fields = ('item__name', 'voucher__number')

@admin.register(AccountEntry)
class AccountEntryAdmin(admin.ModelAdmin):
    list_display = ('account', 'voucher', 'entry_type', 'amount')
    list_filter = ('entry_type', 'voucher__voucher_type')
    search_fields = ('account__name', 'narration')

@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'details')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'details', 'ip_address', 'timestamp')

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_active')
    list_filter = ('role', 'is_active', 'department')
    search_fields = ('username', 'email', 'phone_number')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'department', 'last_login_ip')}),
    )

@admin.register(TrialBalance)
class TrialBalanceAdmin(admin.ModelAdmin):
    list_display = ('account', 'debit_amount', 'credit_amount', 'balance', 'balance_type', 'date')
    list_filter = ('date', 'balance_type')
    search_fields = ('account__name',)
    date_hierarchy = 'date'

@admin.register(ProfitLoss)
class ProfitLossAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'is_income', 'date')
    list_filter = ('is_income', 'date')
    search_fields = ('category',)
    date_hierarchy = 'date'

@admin.register(GSTR1)
class GSTR1Admin(admin.ModelAdmin):
    list_display = ('invoice_number', 'invoice_date', 'customer_name', 'total_amount')
    list_filter = ('invoice_date',)
    search_fields = ('invoice_number', 'customer_name', 'gstin')
    date_hierarchy = 'invoice_date'

@admin.register(GSTR2)
class GSTR2Admin(admin.ModelAdmin):
    list_display = ('invoice_number', 'invoice_date', 'supplier_name', 'total_amount')
    list_filter = ('invoice_date',)
    search_fields = ('invoice_number', 'supplier_name', 'gstin')
    date_hierarchy = 'invoice_date'

@admin.register(GSTR3B)
class GSTR3BAdmin(admin.ModelAdmin):
    list_display = ('period', 'outward_supplies', 'inward_supplies', 'net_tax_payable')
    search_fields = ('period',)
    ordering = ('-period',)
