from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Account, Transaction
from .utils import import_dat_files
import os
import logging
from django.db import transaction
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    
    def get_queryset(self):
        queryset = Account.objects.all()
        account_type = self.request.query_params.get('account_type', None)
        if account_type:
            queryset = queryset.filter(account_type=account_type)
        return queryset

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    
    def get_queryset(self):
        queryset = Transaction.objects.all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        
        # Filter by account types
        account_types = self.request.query_params.get('account_types', None)
        if account_types:
            account_types = account_types.split(',')
            queryset = queryset.filter(account__account_type__in=account_types)
        
        return queryset.select_related('account')

    @action(detail=False, methods=['post'])
    def import_dat(self, request):
        masters_file = request.FILES.get('masters')
        transactions_file = request.FILES.get('transactions')
        
        if not masters_file or not transactions_file:
            return Response(
                {'error': 'Both masters.DAT and transactions.DAT files are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save files temporarily
        masters_path = os.path.join('/tmp', 'masters.DAT')
        transactions_path = os.path.join('/tmp', 'transactions.DAT')
        
        with open(masters_path, 'wb+') as destination:
            for chunk in masters_file.chunks():
                destination.write(chunk)
        
        with open(transactions_path, 'wb+') as destination:
            for chunk in transactions_file.chunks():
                destination.write(chunk)
        
        try:
            import_dat_files(masters_path, transactions_path)
            return Response({'message': 'Data imported successfully'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Clean up temporary files
            os.remove(masters_path)
            os.remove(transactions_path)

    @action(detail=False, methods=['get'])
    def profit_loss(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        account_types = request.query_params.get('account_types', '').split(',')
        
        queryset = self.get_queryset()
        
        # Calculate totals
        income = queryset.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
        expenses = queryset.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'total_income': income,
            'total_expenses': expenses,
            'net_profit': income - expenses,
            'transactions': self.get_serializer(queryset, many=True).data
        })

class DashboardViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def summary(self, request):
        try:
            # Get date range for the last 4 months
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=120)
            
            logger.info(f"Fetching dashboard summary from {start_date} to {end_date}")
            
            # Get transactions for the period
            transactions = Transaction.objects.filter(
                date__range=[start_date, end_date]
            ).select_related('account')
            
            logger.debug(f"Found {transactions.count()} transactions")
            
            # Calculate Profit & Loss data
            profit_loss_data = []
            current_date = start_date
            
            while current_date <= end_date:
                month_end = current_date.replace(day=28) + timedelta(days=4)
                month_end = month_end - timedelta(days=month_end.day)
                
                month_transactions = transactions.filter(
                    date__range=[current_date, month_end]
                )
                
                income = month_transactions.filter(type='income').aggregate(
                    total=Sum('amount')
                )['total'] or 0
                
                expense = month_transactions.filter(type='expense').aggregate(
                    total=Sum('amount')
                )['total'] or 0
                
                profit_loss_data.append({
                    'date': current_date.strftime('%Y-%m'),
                    'income': float(income),
                    'expense': float(expense),
                })
                
                current_date = (month_end + timedelta(days=1))
            
            logger.debug(f"Generated profit/loss data for {len(profit_loss_data)} months")
            
            # Calculate GST Summary
            gst_transactions = transactions.filter(
                Q(account__account_type='creditor') | Q(account__account_type='debtor')
            )
            
            gst_payable = gst_transactions.filter(
                account__account_type='creditor'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            input_credit = gst_transactions.filter(
                account__account_type='debtor'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            logger.debug(f"GST Summary - Payable: {gst_payable}, Input Credit: {input_credit}")
            
            # Calculate Total Assets and Liabilities
            total_assets = Account.objects.filter(
                account_type__in=['bank', 'cash']
            ).aggregate(total=Sum('balance'))['total'] or 0
            
            total_liabilities = Account.objects.filter(
                account_type='creditor'
            ).aggregate(total=Sum('balance'))['total'] or 0
            
            logger.debug(f"Assets: {total_assets}, Liabilities: {total_liabilities}")
            
            response_data = {
                'profitLoss': profit_loss_data,
                'gstSummary': {
                    'payable': float(gst_payable),
                    'inputCredit': float(input_credit),
                },
                'totalAssets': float(total_assets),
                'totalLiabilities': float(total_liabilities),
                'netTaxPayable': float(gst_payable - input_credit),
            }
            
            logger.info("Successfully generated dashboard summary")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error generating dashboard summary: {str(e)}", exc_info=True)
            raise APIException(
                detail={
                    'message': 'An error occurred while generating the dashboard summary',
                    'error': str(e)
                }
            ) 