from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    KBQueryView,
    AdminUsageSummaryView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('kb/query/', KBQueryView.as_view(), name='kb-query'),
    path('admin/usage-summary/', AdminUsageSummaryView.as_view(), name='admin-usage-summary'),
]
