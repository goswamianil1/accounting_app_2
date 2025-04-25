from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from .views import (
    AccountGroupViewSet,
    AccountViewSet,
    ItemViewSet,
    VoucherViewSet,
    VoucherItemViewSet,
    AccountEntryViewSet,
    AuditTrailViewSet,
    CustomTokenObtainPairView,
    logout_view,
    register_view,
    user_profile,
    index,
    get_account_types,
    get_transaction_types,
    chatbot
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'account-groups', AccountGroupViewSet)
router.register(r'accounts', AccountViewSet)
router.register(r'items', ItemViewSet)
router.register(r'vouchers', VoucherViewSet)
router.register(r'voucher-items', VoucherItemViewSet)
router.register(r'account-entries', AccountEntryViewSet)
router.register(r'audit-trails', AuditTrailViewSet)

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Accounting API",
        default_version='v1',
        description="API for accounting application",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/chatbot/', chatbot, name='chatbot'),
    
    # Authentication endpoints
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', register_view, name='register'),
    path('api/auth/profile/', user_profile, name='profile'),
    
    # Type endpoints
    path('api/account-types/', get_account_types, name='account-types'),
    path('api/transaction-types/', get_transaction_types, name='transaction-types'),
    
    # Swagger documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Serve React Frontend - this should be last to catch all other URLs
    re_path(r'^.*$', index, name='index'),
] 