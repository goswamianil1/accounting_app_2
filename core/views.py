from django.shortcuts import render
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F, Q
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import datetime, timedelta
import openai
from django.conf import settings
import json
import re
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import logging
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.fields.related import (
    ForeignKey,
    OneToOneField,
    ManyToManyField,
    ManyToOneRel,
    OneToOneRel,
    ManyToManyRel
)

from .models import (
    AccountGroup,
    Account,
    AccountType,
    EntryType,
    AccountEntry,
    Item,
    Voucher,
    VoucherItem,
    AuditTrail,
    CustomUser,
    TrialBalance,
    ProfitLoss,
    GSTR1,
    GSTR2,
    GSTR3B
)

from .serializers import (
    AccountGroupSerializer,
    AccountSerializer,
    ItemSerializer,
    VoucherSerializer,
    VoucherItemSerializer,
    AccountEntrySerializer,
    AuditTrailSerializer,
    UserSerializer,
    TrialBalanceSerializer,
    ProfitLossSerializer,
    GSTR1Serializer,
    GSTR2Serializer,
    GSTR3BSerializer
)

# Initialize OpenAI client
openai.api_key = settings.OPENAI_API_KEY

logger = logging.getLogger(__name__)

def extract_date(text):
    # Add date extraction logic here
    # This is a simple example - you might want to use a more robust date parsing library
    date_patterns = [
        r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]+)',
        r'([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                if len(match.groups()) == 2:
                    day, month = match.groups()
                    # Convert month name to number
                    month_num = datetime.strptime(month, '%B').month
                    return datetime.now().replace(day=int(day), month=month_num)
            except:
                continue
    return None

def extract_amount(text):
    # Extract amount from text
    amount_pattern = r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)'
    match = re.search(amount_pattern, text)
    if match:
        return float(match.group(1).replace(',', ''))
    return None

class AccountGroupViewSet(viewsets.ModelViewSet):
    queryset = AccountGroup.objects.all()
    serializer_class = AccountGroupSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    permission_classes = [permissions.IsAuthenticated]

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account_type', 'is_active', 'group']
    search_fields = ['name', 'code', 'gst_number', 'pan_number']
    ordering_fields = ['name', 'code', 'created_at']
    permission_classes = [permissions.IsAuthenticated]

class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['voucher_type', 'status', 'party']
    search_fields = ['number', 'party__name', 'narration']
    ordering_fields = ['date', 'number', 'created_at']
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditTrail.objects.create(
            user=self.request.user,
            action='CREATE',
            model_name='Voucher',
            object_id=str(instance.id),
            details={'number': instance.number}
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditTrail.objects.create(
            user=self.request.user,
            action='UPDATE',
            model_name='Voucher',
            object_id=str(instance.id),
            details={'number': instance.number}
        )

    def perform_destroy(self, instance):
        AuditTrail.objects.create(
            user=self.request.user,
            action='DELETE',
            model_name='Voucher',
            object_id=str(instance.id),
            details={'number': instance.number}
        )
        instance.delete()

    @action(detail=False, methods=['get'])
    def trial_balance(self, request):
        """Generate trial balance report."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', timezone.now().date())

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        # Get all accounts with their debit and credit balances
        accounts = Account.objects.filter(is_active=True)
        debit_type = EntryType.objects.get(code='debit')
        credit_type = EntryType.objects.get(code='credit')
        trial_balance_data = []

        for account in accounts:
            debit_amount = AccountEntry.objects.filter(
                account=account,
                entry_type=debit_type,
                voucher__date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0

            credit_amount = AccountEntry.objects.filter(
                account=account,
                entry_type=credit_type,
                voucher__date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0

            balance = debit_amount - credit_amount
            balance_type = debit_type if balance > 0 else credit_type

            trial_balance_data.append({
                'account_name': account.name,
                'account_code': account.code,
                'debit_amount': debit_amount,
                'credit_amount': credit_amount,
                'balance': abs(balance),
                'balance_type': balance_type.code
            })

        serializer = TrialBalanceSerializer(trial_balance_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def profit_loss(self, request):
        """Generate profit and loss statement."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', timezone.now().date())

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        # Get income accounts
        income_type = AccountType.objects.get(code='income')
        income_accounts = Account.objects.filter(
            account_type=income_type,
            is_active=True
        )
        credit_type = EntryType.objects.get(code='credit')
        income_data = []
        total_income = 0

        for account in income_accounts:
            amount = AccountEntry.objects.filter(
                account=account,
                entry_type=credit_type,
                voucher__date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            total_income += amount
            income_data.append({
                'category': account.name,
                'amount': amount,
                'is_income': True
            })

        # Get expense accounts
        expense_type = AccountType.objects.get(code='expense')
        expense_accounts = Account.objects.filter(
            account_type=expense_type,
            is_active=True
        )
        debit_type = EntryType.objects.get(code='debit')
        expense_data = []
        total_expense = 0

        for account in expense_accounts:
            amount = AccountEntry.objects.filter(
                account=account,
                entry_type=debit_type,
                voucher__date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            total_expense += amount
            expense_data.append({
                'category': account.name,
                'amount': amount,
                'is_income': False
            })

        # Add net profit/loss
        net_profit = total_income - total_expense
        profit_loss_data = income_data + expense_data + [{
            'category': 'Net Profit/Loss',
            'amount': abs(net_profit),
            'is_income': net_profit > 0
        }]

        serializer = ProfitLossSerializer(profit_loss_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def gstr1(self, request):
        """Generate GSTR-1 report."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', timezone.now().date())

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        # Get all purchase vouchers with GST
        vouchers = Voucher.objects.filter(
            date__range=[start_date, end_date],
            items__gst_rate__gt=0
        ).distinct()

        gstr1_data = []
        for voucher in vouchers:
            for item in voucher.items.all():
                if item.gst_rate > 0:
                    gstr1_data.append({
                        'gstin': voucher.party.gst_number,
                        'invoice_number': voucher.number,
                        'invoice_date': voucher.date,
                        'customer_name': voucher.party.name,
                        'taxable_value': item.amount,
                        'cgst_amount': item.gst_amount / 2,
                        'sgst_amount': item.gst_amount / 2,
                        'igst_amount': 0,
                        'total_amount': item.amount + item.gst_amount
                    })

        serializer = GSTR1Serializer(gstr1_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def gstr2(self, request):
        """Generate GSTR-2 report."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', timezone.now().date())

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        # Get all purchase vouchers with GST
        vouchers = Voucher.objects.filter(
            date__range=[start_date, end_date],
            items__gst_rate__gt=0
        ).distinct()

        gstr2_data = []
        for voucher in vouchers:
            for item in voucher.items.all():
                if item.gst_rate > 0:
                    gstr2_data.append({
                        'gstin': voucher.party.gst_number,
                        'invoice_number': voucher.number,
                        'invoice_date': voucher.date,
                        'supplier_name': voucher.party.name,
                        'taxable_value': item.amount,
                        'cgst_amount': item.gst_amount / 2,
                        'sgst_amount': item.gst_amount / 2,
                        'igst_amount': 0,
                        'total_amount': item.amount + item.gst_amount
                    })

        serializer = GSTR2Serializer(gstr2_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def gstr3b(self, request):
        """Generate GSTR-3B report."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', timezone.now().date())

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = end_date - timedelta(days=30)

        # Calculate outward supplies (sales)
        outward_supplies = AccountEntry.objects.filter(
            account__account_type='INCOME',
            entry_type='CREDIT',
            voucher__date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Calculate inward supplies (purchases)
        inward_supplies = AccountEntry.objects.filter(
            account__account_type='EXPENSE',
            entry_type='DEBIT',
            voucher__date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Calculate GST amounts
        cgst_payable = ItemEntry.objects.filter(
            voucher__date__range=[start_date, end_date],
            gst_rate__gt=0
        ).aggregate(total=Sum('gst_amount')/2)['total'] or 0

        sgst_payable = cgst_payable
        igst_payable = 0

        # Calculate input tax credit
        cgst_input = BillSundry.objects.filter(
            voucher__date__range=[start_date, end_date],
            gst_rate__gt=0
        ).aggregate(total=Sum('gst_amount')/2)['total'] or 0

        sgst_input = cgst_input
        igst_input = 0

        # Calculate net tax payable
        net_tax_payable = (cgst_payable + sgst_payable + igst_payable) - (cgst_input + sgst_input + igst_input)

        gstr3b_data = {
            'period': f"{start_date.strftime('%b %Y')}",
            'outward_supplies': outward_supplies,
            'inward_supplies': inward_supplies,
            'cgst_payable': cgst_payable,
            'sgst_payable': sgst_payable,
            'igst_payable': igst_payable,
            'cgst_input': cgst_input,
            'sgst_input': sgst_input,
            'igst_input': igst_input,
            'net_tax_payable': net_tax_payable
        }

        serializer = GSTR3BSerializer(gstr3b_data)
        return Response(serializer.data)

class VoucherItemViewSet(viewsets.ModelViewSet):
    queryset = VoucherItem.objects.all()
    serializer_class = VoucherItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['voucher', 'item']
    search_fields = ['item__name', 'voucher__number']
    ordering_fields = ['created_at']
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditTrail.objects.create(
            user=self.request.user,
            action='CREATE',
            model_name='VoucherItem',
            object_id=str(instance.id),
            details={'voucher': instance.voucher.number, 'item': instance.item.name}
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditTrail.objects.create(
            user=self.request.user,
            action='UPDATE',
            model_name='VoucherItem',
            object_id=str(instance.id),
            details={'voucher': instance.voucher.number, 'item': instance.item.name}
        )

    def perform_destroy(self, instance):
        AuditTrail.objects.create(
            user=self.request.user,
            action='DELETE',
            model_name='VoucherItem',
            object_id=str(instance.id),
            details={'voucher': instance.voucher.number, 'item': instance.item.name}
        )
        instance.delete()

class AccountEntryViewSet(viewsets.ModelViewSet):
    queryset = AccountEntry.objects.all()
    serializer_class = AccountEntrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['voucher', 'account', 'entry_type']
    search_fields = ['account__name', 'narration']
    ordering_fields = ['created_at']
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditTrail.objects.create(
            user=self.request.user,
            action='CREATE',
            model_name='AccountEntry',
            object_id=str(instance.id),
            details={'voucher': instance.voucher.number, 'account': instance.account.name}
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditTrail.objects.create(
            user=self.request.user,
            action='UPDATE',
            model_name='AccountEntry',
            object_id=str(instance.id),
            details={'voucher': instance.voucher.number, 'account': instance.account.name}
        )

    def perform_destroy(self, instance):
        AuditTrail.objects.create(
            user=self.request.user,
            action='DELETE',
            model_name='AccountEntry',
            object_id=str(instance.id),
            details={'voucher': instance.voucher.number, 'account': instance.account.name}
        )
        instance.delete()

class AuditTrailViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditTrail.objects.all()
    serializer_class = AuditTrailSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'action', 'model_name']
    search_fields = ['user__username', 'model_name', 'object_id']
    ordering_fields = ['timestamp']
    permission_classes = [permissions.IsAuthenticated]

@api_view(['POST'])
def chatbot(request):
    try:
        message = request.data.get('message', '')
        
        # Process the message using OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful accounting assistant. You can help with queries about profits, purchases, and GST reports."},
                {"role": "user", "content": message}
            ],
            max_tokens=150
        )
        
        bot_response = response.choices[0].message.content
        
        # Extract entities from the message
        date = extract_date(message)
        amount = extract_amount(message)
        
        # Handle different types of queries
        if "profit" in message.lower():
            # Query profit data
            # Add your profit calculation logic here
            pass
        elif "purchase" in message.lower() and amount:
            # Handle purchase record
            # Add your purchase record creation logic here
            pass
        elif "gst" in message.lower():
            # Handle GST report
            # Add your GST report generation logic here
            pass
        
        return Response({
            'response': bot_response,
            'entities': {
                'date': date.isoformat() if date else None,
                'amount': amount
            }
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            logger.info(f"Successful login for user: {request.data.get('username')}")
            return response
        except InvalidToken as e:
            logger.warning(f"Invalid token attempt for user: {request.data.get('username')}")
            return Response(
                {'detail': 'Invalid credentials provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except TokenError as e:
            logger.error(f"Token error for user: {request.data.get('username')}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Login error for user: {request.data.get('username')}", exc_info=True)
            return Response(
                {'detail': 'An error occurred during authentication.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Please provide both username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user:
        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    else:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'message': 'Successfully logged out'})

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    return Response(UserSerializer(request.user).data)

@api_view(['GET'])
def get_account_types(request):
    """
    Get all available account types.
    """
    account_types = AccountType.objects.all().values('id', 'name', 'code', 'description')
    return Response({
        'status': 'success',
        'data': list(account_types)
    })

@api_view(['GET'])
def get_transaction_types(request):
    """
    Get all available transaction types.
    """
    entry_types = EntryType.objects.all().values('id', 'name', 'code', 'description')
    return Response({
        'status': 'success',
        'data': list(entry_types)
    })

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'hsn_code']
    ordering_fields = ['name', 'code', 'created_at']
    permission_classes = [permissions.IsAuthenticated]

# Serve React Frontend
index = never_cache(TemplateView.as_view(template_name='index.html'))
