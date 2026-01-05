from django import forms
from django.core.exceptions import ValidationError
from .models import User, Department, Faculty, SystemConfiguration, ProcurementPolicy


class UserForm(forms.ModelForm):
    """Form for creating and editing users"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        required=False,
        help_text='Leave blank to keep current password when editing'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        required=False,
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'employee_id', 'phone_number', 'department',
            'is_active_user', 'profile_picture'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter employee ID'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active_user': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'is_active_user': 'Active User',
            'employee_id': 'Employee ID',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make password required only for new users
        if not self.instance.pk:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Only validate password if it's provided
        if password or confirm_password:
            if password != confirm_password:
                raise ValidationError({
                    'confirm_password': 'Passwords do not match'
                })
            
            # Password strength validation
            if password and len(password) < 8:
                raise ValidationError({
                    'password': 'Password must be at least 8 characters long'
                })

        return cleaned_data


class DepartmentForm(forms.ModelForm):
    """Form for creating and editing departments"""
    class Meta:
        model = Department
        fields = [
            'faculty', 'name', 'code', 'department_type',
            'hod', 'description', 'is_active'
        ]
        widgets = {
            'faculty': forms.Select(attrs={
                'class': 'form-control'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department code (e.g., CS, ENG)'
            }),
            'department_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'hod': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter department description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'hod': 'Head of Department',
            'is_active': 'Active',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter HOD choices to only show users with HOD role
        if 'hod' in self.fields:
            self.fields['hod'].queryset = User.objects.filter(
                role='HOD',
                is_active_user=True
            )
            self.fields['hod'].required = False


class FacultyForm(forms.ModelForm):
    """Form for creating and editing faculties"""
    class Meta:
        model = Faculty
        fields = ['name', 'code', 'dean', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter faculty/school name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter faculty code (e.g., FOS, FOE)'
            }),
            'dean': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter faculty description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_active': 'Active',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dean can be any active user, but typically admin or senior staff
        if 'dean' in self.fields:
            self.fields['dean'].queryset = User.objects.filter(
                is_active_user=True
            ).exclude(role='SUPPLIER')
            self.fields['dean'].required = False


class SystemConfigForm(forms.ModelForm):
    """Form for editing system configuration settings"""
    class Meta:
        model = SystemConfiguration
        fields = ['key', 'value', 'data_type', 'description', 'is_editable']
        widgets = {
            'key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., MAX_APPROVAL_DAYS'
            }),
            'value': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter configuration value'
            }),
            'data_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what this configuration controls'
            }),
            'is_editable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_editable': 'Editable by Users',
        }

    def clean_value(self):
        """Validate value based on data_type"""
        value = self.cleaned_data.get('value')
        data_type = self.cleaned_data.get('data_type')

        if data_type == 'INTEGER':
            try:
                int(value)
            except (ValueError, TypeError):
                raise ValidationError('Value must be a valid integer')
        
        elif data_type == 'DECIMAL':
            try:
                float(value)
            except (ValueError, TypeError):
                raise ValidationError('Value must be a valid decimal number')
        
        elif data_type == 'BOOLEAN':
            if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                raise ValidationError('Value must be a boolean (true/false, yes/no, 1/0)')
        
        elif data_type == 'JSON':
            import json
            try:
                json.loads(value)
            except (ValueError, TypeError):
                raise ValidationError('Value must be valid JSON')

        return value


class ProcurementPolicyForm(forms.ModelForm):
    """Form for creating and editing procurement policies"""
    class Meta:
        model = ProcurementPolicy
        fields = [
            'title', 'policy_number', 'description', 'content',
            'effective_date', 'expiry_date', 'is_active', 'document'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter policy title'
            }),
            'policy_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., PP-2024-001'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the policy'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter the full policy content'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
        }
        labels = {
            'is_active': 'Active Policy',
        }
        help_texts = {
            'document': 'Upload PDF or Word document (optional)',
            'expiry_date': 'Leave blank if policy has no expiry date',
        }

    def clean(self):
        cleaned_data = super().clean()
        effective_date = cleaned_data.get('effective_date')
        expiry_date = cleaned_data.get('expiry_date')

        # Validate that expiry date is after effective date
        if effective_date and expiry_date:
            if expiry_date <= effective_date:
                raise ValidationError({
                    'expiry_date': 'Expiry date must be after effective date'
                })

        return cleaned_data