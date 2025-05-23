import rest_framework_simplejwt
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, BookListCreateView, BookUpdateDeleteView,
    OrderCreateView, OrderListView, OrderAcceptView, OrderReturnView, OrderRateView
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Library API",
        default_version='v1',
        description="API for Library Management",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=(rest_framework_simplejwt.authentication.JWTAuthentication,),
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('books/', BookListCreateView.as_view(), name='book_list_create'),
    path('books/<int:book_id>/', BookUpdateDeleteView.as_view(), name='book_update_delete'),
    path('orders/', OrderCreateView.as_view(), name='order_create'),
    path('orders/list/', OrderListView.as_view(), name='order_list'),
    path('orders/<int:order_id>/accept/', OrderAcceptView.as_view(), name='order_accept'),
    path('orders/<int:order_id>/return/', OrderReturnView.as_view(), name='order_return'),
    path('orders/<int:order_id>/rate/', OrderRateView.as_view(), name='order_rate'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]