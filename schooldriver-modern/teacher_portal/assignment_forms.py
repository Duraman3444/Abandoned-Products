from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from datetime import date, time
from academics.models import (
    Assignment, AssignmentCategory, AssignmentTemplate, AssignmentAttachment,
    CurriculumStandard, LessonPlan, StudentSubmission
)


class EnhancedAssignmentForm(forms.ModelForm):
    """Enhanced form for creating and editing assignments with all features"""
    
    class Meta:
        model = Assignment
        fields = [
            'name', 'description', 'instructions', 'category', 
            'assigned_date', 'due_date', 'due_time', 'max_points', 'weight', 
            'allow_late_submission', 'late_penalty', 'estimated_duration',
            'standards', 'lesson_plan', 'is_published'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Assignment name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the assignment'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed instructions for students'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'assigned_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'max_points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'value': '1.0'
            }),
            'allow_late_submission': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'late_penalty': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.1',
                'placeholder': 'Penalty % per day'
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Minutes'
            }),
            'standards': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'lesson_plan': forms.Select(attrs={
                'class': 'form-select',
                'empty_label': 'Select lesson plan (optional)'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        section = kwargs.pop('section', None)
        super().__init__(*args, **kwargs)
        
        self.fields['category'].queryset = AssignmentCategory.objects.filter(is_active=True)
        self.fields['standards'].queryset = CurriculumStandard.objects.filter(is_active=True)
        
        if section:
            self.fields['lesson_plan'].queryset = section.lesson_plans.all()
        else:
            self.fields['lesson_plan'].queryset = LessonPlan.objects.none()
        
        # Set default assigned date to today
        if not self.instance.pk:
            self.fields['assigned_date'].initial = date.today()


class AssignmentTemplateForm(forms.ModelForm):
    """Form for creating and editing assignment templates"""
    
    class Meta:
        model = AssignmentTemplate
        fields = [
            'name', 'description', 'category', 'max_points', 'weight',
            'instructions', 'estimated_duration', 'is_public'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Template name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Template description'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'max_points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'value': '100'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'value': '1.0'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Standard instructions for this type of assignment'
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Minutes'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = AssignmentCategory.objects.filter(is_active=True)


class AssignmentFromTemplateForm(forms.Form):
    """Form for creating assignments from templates"""
    
    template = forms.ModelChoiceField(
        queryset=AssignmentTemplate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Choose a template..."
    )
    
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Assignment name'
        })
    )
    
    assigned_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    due_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    
    modify_instructions = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    custom_instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Custom instructions (optional)'
        })
    )


class AssignmentAttachmentForm(forms.ModelForm):
    """Form for uploading assignment attachments"""
    
    class Meta:
        model = AssignmentAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.gif'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'File description (optional)'
            }),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 10MB')
            
            # Check file type
            allowed_types = [
                'application/pdf', 'application/msword', 
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-powerpoint',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/plain', 'image/jpeg', 'image/png', 'image/gif'
            ]
            
            if file.content_type not in allowed_types:
                raise forms.ValidationError('File type not allowed')
        
        return file


class CurriculumStandardForm(forms.ModelForm):
    """Form for creating and editing curriculum standards"""
    
    class Meta:
        model = CurriculumStandard
        fields = ['code', 'title', 'description', 'subject_area', 'grade_level']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CCSS.MATH.5.NBT.1'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Standard title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed description of the standard'
            }),
            'subject_area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Mathematics, English Language Arts'
            }),
            'grade_level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Grade 5, K-2, 9-12'
            }),
        }


class LessonPlanForm(forms.ModelForm):
    """Form for creating and editing lesson plans"""
    
    class Meta:
        model = LessonPlan
        fields = [
            'title', 'lesson_type', 'date', 'duration', 
            'objectives', 'content', 'materials'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lesson title'
            }),
            'lesson_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Duration in minutes'
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Learning objectives for this lesson'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Lesson content and activities'
            }),
            'materials': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Required materials and resources'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = date.today()


class AssignmentAnalyticsFilterForm(forms.Form):
    """Form for filtering assignment analytics"""
    
    category = forms.ModelChoiceField(
        queryset=AssignmentCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    completion_threshold = forms.DecimalField(
        initial=75.0,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum completion %'
        })
    )
    
    include_unpublished = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date range to current semester
        today = date.today()
        # Rough semester start (adjust as needed)
        semester_start = today.replace(month=8 if today.month >= 8 else 1, day=1)
        self.fields['date_start'].initial = semester_start
        self.fields['date_end'].initial = today


class BulkAssignmentActionForm(forms.Form):
    """Form for bulk actions on assignments"""
    
    BULK_ACTIONS = [
        ('', 'Select Action'),
        ('publish', 'Publish Selected'),
        ('unpublish', 'Unpublish Selected'),
        ('duplicate', 'Duplicate Selected'),
        ('delete', 'Delete Selected'),
        ('export', 'Export to Template'),
    ]
    
    action = forms.ChoiceField(
        choices=BULK_ACTIONS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    assignments = forms.ModelMultipleChoiceField(
        queryset=Assignment.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        section = kwargs.pop('section', None)
        super().__init__(*args, **kwargs)
        
        if section:
            self.fields['assignments'].queryset = section.assignments.all()


# Formsets for multiple file uploads
AssignmentAttachmentFormSet = inlineformset_factory(
    Assignment,
    AssignmentAttachment,
    form=AssignmentAttachmentForm,
    fields=['file', 'description'],
    extra=3,
    can_delete=True
)
