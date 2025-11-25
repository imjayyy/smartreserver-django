from django.contrib import admin
from .models import Business, BusinessUser, BusinessSettings, RegisteredUser


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone_number', 'email')
    search_fields = ('name', 'address', 'phone_number', 'email')
    ordering = ('name',)
    list_filter = ('name',) 

@admin.register(BusinessUser)
class BusinessUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'business', 'role')
    search_fields = ('user__username', 'business__name', 'role')
    ordering = ('business__name', 'user__username')
    list_filter = ('role',)
    
@admin.register(BusinessSettings)
class BusinessSettingsAdmin(admin.ModelAdmin):  
    list_display = ('business', 'timezone', 'currency', 'language')
    search_fields = ('business__name', 'timezone', 'currency', 'language')
    ordering = ('business__name',)
    list_filter = ('timezone', 'currency', 'language')

@admin.register(RegisteredUser)
class RegisteredUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'business', 'registration_date')
    search_fields = ('user__username', 'business__name')
    ordering = ('business__name', 'user__username', 'registration_date')
    list_filter = ('business',)

# Register your models here.
