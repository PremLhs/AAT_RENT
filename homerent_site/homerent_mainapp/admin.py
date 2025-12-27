from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Tenant, RentRecord

class RentRecordInline(admin.TabularInline):
    model = RentRecord
    extra = 0

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_no', 'mobile1', 'base_rent', 'unit_rate', 'owner']
    list_filter = ['owner', 'joining_date']
    inlines = [RentRecordInline]
    search_fields = ['name', 'room_no', 'mobile1']

@admin.register(RentRecord)
class RentRecordAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'month', 'year', 'total_amount', 'status', 'rent_date']
    list_filter = ['status', 'rent_date', 'tenant__owner']
    search_fields = ['tenant__name', 'tenant__room_no']

class TenantInline(admin.TabularInline):
    model = Tenant
    fk_name = 'owner'
    extra = 0

class CustomUserAdmin(UserAdmin):
    inlines = [TenantInline]

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
