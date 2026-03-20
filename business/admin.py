from django.contrib import admin
from .models import Business, BusinessUser, Service, SpecialOffer, Staff

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone_number', 'timezone')
    search_fields = ('name', 'email')
    list_filter = ('timezone',)

@admin.register(BusinessUser)
class BusinessUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'business', 'role')
    list_filter = ('role', 'business')
    search_fields = ('user__email', 'business__name')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'business', 'price', 'duration')
    list_filter = ('business',)
    search_fields = ('name', 'business__name')

@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'business', 'discount_percentage', 'start_date', 'end_date')
    list_filter = ('business', 'start_date', 'end_date')
    search_fields = ('title', 'business__name')

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'business', 'position', 'email', 'is_active')
    list_filter = ('business', 'is_active', 'position')
    search_fields = ('name', 'email', 'business__name')