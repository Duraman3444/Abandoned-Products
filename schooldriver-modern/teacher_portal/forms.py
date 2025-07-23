from django import forms
from django.forms import modelformset_factory
from academics.models import Assignment, AssignmentCategory, Grade, Enrollment


class AssignmentForm(forms.ModelForm):
    """Form for creating and editing assignments"""
    
    class Meta:
        model = Assignment
        fields = [
            'name', 'description', 'category', 'assigned_date', 
            'due_date', 'max_points', 'weight', 'is_published'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Assignment name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Assignment description (optional)'
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
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = AssignmentCategory.objects.filter(is_active=True)


class AssignmentCategoryForm(forms.ModelForm):
    """Form for creating assignment categories"""
    
    class Meta:
        model = AssignmentCategory
        fields = ['name', 'description', 'default_weight']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name (e.g., Tests, Quizzes, Homework)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Category description (optional)'
            }),
            'default_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'value': '1.0'
            }),
        }


class GradeForm(forms.ModelForm):
    """Form for entering individual grades"""
    
    class Meta:
        model = Grade
        fields = ['points_earned', 'letter_grade', 'is_excused', 'is_late', 'comments']
        widgets = {
            'points_earned': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0',
                'step': '0.01',
                'placeholder': '--'
            }),
            'letter_grade': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'maxlength': '2',
                'placeholder': '--'
            }),
            'is_excused': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_late': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Comments (optional)'
            }),
        }


class BulkGradeForm(forms.Form):
    """Form for bulk grade operations"""
    
    BULK_ACTIONS = [
        ('', 'Select Action'),
        ('set_all', 'Set All Grades'),
        ('add_points', 'Add Points to All'),
        ('multiply', 'Multiply All by Factor'),
        ('excuse_all', 'Excuse All'),
    ]
    
    action = forms.ChoiceField(
        choices=BULK_ACTIONS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    value = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Value'
        })
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Reason for bulk change (optional)'
        })
    )


class GradebookFilterForm(forms.Form):
    """Form for filtering gradebook view"""
    
    category = forms.ModelChoiceField(
        queryset=AssignmentCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    published_only = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    show_comments = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


# Formset for bulk grade entry
GradeFormSet = modelformset_factory(
    Grade,
    form=GradeForm,
    fields=['points_earned', 'letter_grade', 'is_excused', 'is_late', 'comments'],
    extra=0,
    can_delete=False
)


class QuickGradeForm(forms.Form):
    """Quick form for individual grade entry via AJAX"""
    
    grade_id = forms.IntegerField(widget=forms.HiddenInput())
    points_earned = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm grade-input',
            'min': '0',
            'step': '0.01'
        })
    )
    
    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment', None)
        super().__init__(*args, **kwargs)
        
        if assignment:
            self.fields['points_earned'].widget.attrs['max'] = str(assignment.max_points)
            self.fields['points_earned'].widget.attrs['placeholder'] = f'/{assignment.max_points}'


class ProgressReportForm(forms.Form):
    """Form for generating progress reports"""
    
    REPORT_TYPES = [
        ('individual', 'Individual Student Report'),
        ('class', 'Class Summary Report'),
        ('category', 'By Category Report'),
        ('missing', 'Missing Assignments Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    students = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    include_comments = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    date_range_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_range_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def __init__(self, *args, **kwargs):
        section = kwargs.pop('section', None)
        super().__init__(*args, **kwargs)
        
        if section:
            self.fields['students'].queryset = section.enrollments.filter(
                is_active=True
            ).values_list('student', flat=True)
