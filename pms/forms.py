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
    
    

# forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import *


# ============================================================================
# SUPPLIER PROFILE FORMS
# ============================================================================

class SupplierProfileForm(forms.ModelForm):
    """Form for editing supplier company profile"""
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'registration_number', 'tax_id',
            'email', 'phone_number', 
            'physical_address', 'postal_address', 'website',
            'contact_person', 'contact_person_phone', 'contact_person_email',
            'bank_name', 'bank_branch', 'account_number', 
            'account_name', 'swift_code',
            'categories'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company Name'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Registration Number'
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tax ID/PIN'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'company@example.com'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254...'
            }),
            'physical_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Physical Address'
            }),
            'postal_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'P.O. Box...'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact Person Name'
            }),
            'contact_person_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact Phone'
            }),
            'contact_person_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@example.com'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank Name'
            }),
            'bank_branch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Branch Name'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account Number'
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account Name'
            }),
            'swift_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SWIFT Code (if applicable)'
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
        }


class SupplierDocumentForm(forms.ModelForm):
    """Form for uploading supplier documents"""
    
    class Meta:
        model = SupplierDocument
        fields = [
            'document_type', 'document_name', 'file',
            'issue_date', 'expiry_date'
        ]
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'document_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document Name'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


# ============================================================================
# BID FORMS
# ============================================================================

class BidForm(forms.ModelForm):
    """Form for submitting a bid"""
    
    class Meta:
        model = Bid
        fields = [
            'bid_amount', 'bid_bond_amount', 'validity_period_days',
            'delivery_period_days', 'notes'
        ]
        widgets = {
            'bid_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'bid_bond_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'validity_period_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '90',
                'min': '1'
            }),
            'delivery_period_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of days',
                'min': '1'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional notes or comments...'
            }),
        }


class BidItemForm(forms.ModelForm):
    """Form for individual bid items"""
    
    class Meta:
        model = BidItem
        fields = [
            'requisition_item', 'quoted_unit_price', 'brand', 'model',
            'specifications', 'delivery_period_days', 
            'warranty_period_months', 'notes'
        ]
        widgets = {
            'requisition_item': forms.HiddenInput(),
            'quoted_unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brand'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Model'
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Technical specifications...'
            }),
            'delivery_period_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Days',
                'min': '1'
            }),
            'warranty_period_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Months',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes...'
            }),
        }


# Create formset for bid items
BidItemFormSet = inlineformset_factory(
    Bid,
    BidItem,
    form=BidItemForm,
    extra=0,
    can_delete=False,
    min_num=1,
    validate_min=True
)


class BidDocumentForm(forms.ModelForm):
    """Form for uploading bid documents"""
    
    class Meta:
        model = BidDocument
        fields = ['document_type', 'document_name', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'document_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document Name'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Brief description...'
            }),
        }


# ============================================================================
# INVOICE FORMS
# ============================================================================

class InvoiceForm(forms.ModelForm):
    """Form for submitting invoices"""
    
    def __init__(self, *args, **kwargs):
        supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)
        
        if supplier:
            # Filter purchase orders for this supplier
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
                supplier=supplier,
                status__in=['ACKNOWLEDGED', 'PARTIAL_DELIVERY', 'DELIVERED']
            )
    
    class Meta:
        model = Invoice
        fields = [
            'purchase_order', 'supplier_invoice_number', 
            'invoice_date', 'due_date', 'grn',
            'other_charges', 'notes'
        ]
        widgets = {
            'purchase_order': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'supplier_invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Invoice Number',
                'required': True
            }),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'grn': forms.Select(attrs={
                'class': 'form-control'
            }),
            'other_charges': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
        }


class InvoiceItemForm(forms.ModelForm):
    """Form for individual invoice items"""
    
    class Meta:
        model = InvoiceItem
        fields = [
            'po_item', 'description', 'quantity', 
            'unit_price', 'tax_rate'
        ]
        widgets = {
            'po_item': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Item description...',
                'required': True
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'required': True
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '16',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
        }


# Create formset for invoice items
InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class InvoiceDocumentForm(forms.ModelForm):
    """Form for uploading invoice documents"""
    
    class Meta:
        model = InvoiceDocument
        fields = ['document_name', 'file', 'description']
        widgets = {
            'document_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document Name'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Brief description...'
            }),
        }