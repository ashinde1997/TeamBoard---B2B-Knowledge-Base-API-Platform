from django.contrib import admin
from .models import Company, KBEntry, QueryLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'role', 'api_key', 'created_at')
    search_fields = ('company_name', 'user__username', 'api_key')
    list_filter = ('role', 'created_at')


@admin.register(KBEntry)
class KBEntryAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'created_at')
    search_fields = ('question', 'answer')
    list_filter = ('category', 'created_at')


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ('company', 'search_term', 'results_count', 'queried_at')
    search_fields = ('company__company_name', 'search_term')
    list_filter = ('company', 'queried_at')
