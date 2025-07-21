from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    FeederSchool, AdmissionLevel, AdmissionCheck, ApplicationDecision,
    Applicant, ContactLog, OpenHouse, ApplicantDocument
)


@admin.register(FeederSchool)
class FeederSchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'school_type', 'city', 'state', 'is_active']
    list_filter = ['school_type', 'is_active', 'state']
    search_fields = ['name', 'city']
    list_editable = ['is_active']


class AdmissionCheckInline(admin.TabularInline):
    model = AdmissionCheck
    extra = 1
    fields = ['name', 'is_required', 'description', 'is_active']


@admin.register(AdmissionLevel)
class AdmissionLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'get_check_count', 'is_active']
    list_editable = ['order', 'is_active']
    ordering = ['order']
    inlines = [AdmissionCheckInline]
    
    def get_check_count(self, obj):
        count = obj.checks.filter(is_active=True).count()
        required_count = obj.checks.filter(is_required=True, is_active=True).count()
        return f"{count} checks ({required_count} required)"
    get_check_count.short_description = 'Requirements'


@admin.register(AdmissionCheck)
class AdmissionCheckAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'is_required', 'is_active']
    list_filter = ['level', 'is_required', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_required', 'is_active']


@admin.register(ApplicationDecision)
class ApplicationDecisionAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_positive', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_positive', 'is_active']
    ordering = ['order']


class ApplicantDocumentInline(admin.TabularInline):
    model = ApplicantDocument
    extra = 1
    readonly_fields = ['document_preview', 'file_info', 'uploaded_at']
    fields = [
        'document_type', 'title', 'file', 'document_preview', 'file_info',
        'is_verified', 'uploaded_by', 'notes', 'uploaded_at'
    ]
    classes = ['collapse']
    
    def document_preview(self, obj):
        if not obj.file:
            return "No file uploaded"
        
        if obj.is_image():
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; border: 1px solid #ddd; border-radius: 4px;">',
                obj.file.url
            )
        elif obj.is_pdf():
            return format_html(
                '<a href="{}" target="_blank" style="color: #007cba; text-decoration: none;">'
                '📄 View PDF</a>',
                obj.file.url
            )
        else:
            return format_html(
                '<a href="{}" target="_blank" style="color: #007cba; text-decoration: none;">'
                '📎 Download File</a>',
                obj.file.url
            )
    document_preview.short_description = 'Preview'
    
    def file_info(self, obj):
        if obj.file:
            return format_html(
                '<small>{}<br>{} MB</small>',
                obj.file_extension().upper(),
                obj.file_size_mb()
            )
        return "No file"
    file_info.short_description = 'File Info'


class ContactLogInline(admin.TabularInline):
    model = ContactLog
    extra = 0
    readonly_fields = ['contact_date']
    fields = ['contact_type', 'contacted_by', 'summary', 'follow_up_needed', 'follow_up_date']
    ordering = ['-contact_date']


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = [
        'applicant_id',
        'display_name',
        'applying_for_grade', 
        'get_admission_progress',
        'get_document_status',
        'current_school',
        'decision',
        'is_ready_for_enrollment',
        'created_at'
    ]
    list_filter = [
        'applying_for_grade',
        'school_year',
        'level',
        'decision',
        'is_ready_for_enrollment',
        'is_from_online_inquiry',
        'living_situation'
    ]
    search_fields = [
        'first_name',
        'last_name', 
        'preferred_name',
        'applicant_id',
        'email',
        'primary_parent_name',
        'primary_parent_email'
    ]
    readonly_fields = [
        'applicant_id',
        'primary_parent_name',
        'primary_parent_email',
        'primary_parent_phone',
        'created_at',
        'updated_at',
        'get_completion_percentage'
    ]
    
    fieldsets = (
        ('Applicant Information', {
            'fields': (
                ('first_name', 'middle_name', 'last_name'),
                'preferred_name',
                ('date_of_birth', 'gender'),
                'photo'
            )
        }),
        ('Application Details', {
            'fields': (
                'applicant_id',
                ('applying_for_grade', 'school_year'),
                ('current_school', 'current_school_name'),
                ('is_from_online_inquiry', 'follow_up_date')
            )
        }),
        ('Contact Information', {
            'fields': (
                'email',
                ('street', 'city'),
                ('state', 'zip_code')
            )
        }),
        ('Family Information', {
            'fields': (
                'living_situation',
            )
        }),
        ('Admission Process', {
            'fields': (
                ('level', 'get_completion_percentage'),
                'completed_checks',
                ('decision', 'decision_date', 'decision_by'),
                ('is_ready_for_enrollment', 'enrolled_student')
            )
        }),
        ('Additional Information', {
            'fields': ('notes', 'special_circumstances'),
            'classes': ('collapse',)
        }),
        ('Cached Parent Information', {
            'fields': (
                'primary_parent_name',
                'primary_parent_email', 
                'primary_parent_phone'
            ),
            'classes': ('collapse',),
            'description': 'Automatically updated from parent/guardian contacts.'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['completed_checks', 'parent_guardians', 'siblings']
    date_hierarchy = 'created_at'
    inlines = [ApplicantDocumentInline, ContactLogInline]
    
    actions = ['mark_ready_for_enrollment', 'advance_to_next_level']
    
    def display_name(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; margin-right: 10px; vertical-align: middle;">'
                '<span>{}</span>',
                obj.photo.url,
                obj.display_name
            )
        return obj.display_name
    display_name.short_description = 'Name'
    
    def get_admission_progress(self, obj):
        percentage = obj.get_completion_percentage()
        if obj.level:
            color = 'green' if percentage >= 80 else 'orange' if percentage >= 50 else 'red'
            return format_html(
                '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
                '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
                '{}%</div></div>'
                '<br><small>{}</small>',
                percentage, color, int(percentage), obj.level.name if obj.level else 'Not Started'
            )
        return "Not Started"
    get_admission_progress.short_description = 'Progress'
    
    def get_document_status(self, obj):
        total_docs = obj.documents.count()
        verified_docs = obj.documents.filter(is_verified=True).count()
        
        if total_docs == 0:
            return format_html('<span style="color: red;">📄 No documents</span>')
        
        if verified_docs == total_docs:
            color = 'green'
            icon = '✅'
        elif verified_docs > 0:
            color = 'orange' 
            icon = '⚠️'
        else:
            color = 'red'
            icon = '📄'
            
        return format_html(
            '<span style="color: {};">{} {}/{} verified</span>',
            color, icon, verified_docs, total_docs
        )
    get_document_status.short_description = 'Documents'
    
    def mark_ready_for_enrollment(self, request, queryset):
        updated = queryset.update(is_ready_for_enrollment=True)
        self.message_user(request, f'{updated} applicants marked as ready for enrollment.')
    mark_ready_for_enrollment.short_description = 'Mark selected applicants as ready for enrollment'
    
    def advance_to_next_level(self, request, queryset):
        count = 0
        for applicant in queryset:
            if applicant.can_advance_to_next_level():
                applicant._update_admission_level()
                applicant.save()
                count += 1
        self.message_user(request, f'{count} applicants advanced to next level.')
    advance_to_next_level.short_description = 'Advance eligible applicants to next level'


@admin.register(ContactLog)
class ContactLogAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'contact_type', 'contacted_by', 'contact_date', 'follow_up_needed']
    list_filter = ['contact_type', 'follow_up_needed', 'contact_date']
    search_fields = ['applicant__first_name', 'applicant__last_name', 'contacted_by', 'summary']
    readonly_fields = ['contact_date']
    date_hierarchy = 'contact_date'
    
    fieldsets = (
        (None, {
            'fields': (
                'applicant',
                ('contact_type', 'contacted_by'),
                'summary'
            )
        }),
        ('Follow-up', {
            'fields': (
                'follow_up_needed',
                'follow_up_date'
            )
        }),
        ('System Info', {
            'fields': ('contact_date',),
            'classes': ('collapse',)
        })
    )


@admin.register(OpenHouse)
class OpenHouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'get_attendance_info', 'is_active']
    list_filter = ['is_active', 'date']
    search_fields = ['name', 'description']
    readonly_fields = ['get_attendance_count', 'get_capacity_percentage']
    filter_horizontal = ['attendees']
    date_hierarchy = 'date'
    
    fieldsets = (
        (None, {
            'fields': (
                'name',
                ('date', 'is_active'),
                'description',
                'capacity'
            )
        }),
        ('Attendance', {
            'fields': (
                ('get_attendance_count', 'get_capacity_percentage'),
                'attendees'
            )
        }),
    )
    
    def get_attendance_info(self, obj):
        count = obj.get_attendance_count()
        if obj.capacity:
            percentage = obj.get_capacity_percentage()
            color = 'red' if percentage > 100 else 'orange' if percentage > 80 else 'green'
            return format_html(
                '<span style="color: {};">{} / {} ({}%)</span>',
                color, count, obj.capacity, int(percentage)
            )
        return f"{count} attendees"
    get_attendance_info.short_description = 'Attendance'


@admin.register(ApplicantDocument)
class ApplicantDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'get_document_preview',
        'applicant',
        'document_type',
        'title',
        'get_file_info',
        'is_verified',
        'uploaded_by',
        'uploaded_at'
    ]
    list_filter = [
        'document_type',
        'is_verified',
        'uploaded_at'
    ]
    search_fields = [
        'applicant__first_name',
        'applicant__last_name',
        'applicant__applicant_id',
        'title',
        'uploaded_by'
    ]
    readonly_fields = [
        'get_large_document_preview',
        'file_size_mb',
        'file_extension',
        'uploaded_at',
        'updated_at'
    ]
    list_editable = ['is_verified']
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Document Information', {
            'fields': (
                ('applicant', 'admission_check'),
                ('document_type', 'title'),
                'file',
                'get_large_document_preview'
            )
        }),
        ('File Details', {
            'fields': (
                ('file_extension', 'file_size_mb'),
                'notes'
            )
        }),
        ('Verification', {
            'fields': (
                ('is_verified', 'verified_by'),
                'verified_date',
                'uploaded_by'
            )
        }),
        ('System Information', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_document_preview(self, obj):
        if not obj.file:
            return "No file"
            
        if obj.is_image():
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">',
                obj.file.url
            )
        elif obj.is_pdf():
            return '📄 PDF'
        else:
            return '📎 File'
    get_document_preview.short_description = 'Preview'
    
    def get_large_document_preview(self, obj):
        if not obj.file:
            return "No file uploaded"
            
        if obj.is_image():
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 400px; max-height: 400px; border: 1px solid #ddd; border-radius: 4px;">'
                '<br><a href="{}" target="_blank">View Full Size</a></div>',
                obj.file.url, obj.file.url
            )
        elif obj.is_pdf():
            return format_html(
                '<div style="text-align: center;">'
                '<a href="{}" target="_blank" style="font-size: 48px; color: #007cba; text-decoration: none;">📄</a>'
                '<br><a href="{}" target="_blank">View PDF</a></div>',
                obj.file.url, obj.file.url
            )
        else:
            return format_html(
                '<div style="text-align: center;">'
                '<a href="{}" target="_blank" style="font-size: 48px; color: #007cba; text-decoration: none;">📎</a>'
                '<br><a href="{}" target="_blank">Download File</a></div>',
                obj.file.url, obj.file.url
            )
    get_large_document_preview.short_description = 'Document Preview'
    
    def get_file_info(self, obj):
        if obj.file:
            return format_html(
                '{}<br><small>{} MB</small>',
                obj.file_extension().upper(),
                obj.file_size_mb()
            )
        return "No file"
    get_file_info.short_description = 'File Info'
