from rest_framework import serializers
from django.contrib.auth import get_user_model
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
    GSTR3B,
    AccountType,
    EntryType
)

class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = '__all__'

class EntryTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryType
        fields = '__all__'

class AccountGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountGroup
        fields = '__all__'

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class VoucherItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoucherItem
        fields = '__all__'

class VoucherSerializer(serializers.ModelSerializer):
    items = VoucherItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Voucher
        fields = '__all__'

class AccountEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountEntry
        fields = '__all__'

class AuditTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditTrail
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'department')
        read_only_fields = ('id',)

class TrialBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrialBalance
        fields = '__all__'

class ProfitLossSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfitLoss
        fields = '__all__'

class GSTR1Serializer(serializers.ModelSerializer):
    class Meta:
        model = GSTR1
        fields = '__all__'

class GSTR2Serializer(serializers.ModelSerializer):
    class Meta:
        model = GSTR2
        fields = '__all__'

class GSTR3BSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSTR3B
        fields = '__all__' 