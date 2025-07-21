from django.contrib import admin
from .models import UserProfile, SecurityEvent


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model"""
    list_display = ['user', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'avatar')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Admin interface for SecurityEvent model"""
    list_display = ['event_type', 'user_or_username', 'ip_address', 'timestamp']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['username', 'user__username', 'ip_address', 'user_agent']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (None, {
            'fields': ('event_type', 'user', 'username')
        }),
        ('Request Info', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Details', {
            'fields': ('details',)
        }),
        ('Metadata', {
            'fields': ('id', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
    
    def user_or_username(self, obj):
        """Display user or username for list view"""
        return obj.user.username if obj.user else obj.username
    user_or_username.short_description = 'User'
    user_or_username.admin_order_field = 'user__username'
    
    def has_add_permission(self, request):
        """Prevent manual creation of security events"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification of security events"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of security events (audit trail)"""
        return False
