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
        
        
        

from django import forms
from django.forms import inlineformset_factory
from .models import (
    Requisition, RequisitionItem, RequisitionAttachment,
    Budget, BudgetCategory, ItemCategory, Item
)


class RequisitionForm(forms.ModelForm):
    """Form for creating/editing requisitions"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter budgets for user's department if available
        if self.user and hasattr(self.user, 'department') and self.user.department:
            self.fields['budget'].queryset = Budget.objects.filter(
                department=self.user.department,
                is_active=True
            )
    
    class Meta:
        model = Requisition
        fields = [
            'title',
            'budget',
            'priority',
            'required_date',
            'justification',
            'is_emergency',
            'emergency_justification',
            'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a clear, descriptive title for this requisition'
            }),
            'budget': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'required_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'justification': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide detailed justification for this purchase requisition'
            }),
            'is_emergency': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'emergency_justification': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explain why this is an emergency requisition'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional notes or special instructions'
            }),
        }
        labels = {
            'title': 'Requisition Title',
            'budget': 'Budget Allocation',
            'priority': 'Priority Level',
            'required_date': 'Required By Date',
            'justification': 'Justification',
            'is_emergency': 'Emergency Requisition?',
            'emergency_justification': 'Emergency Justification',
            'notes': 'Additional Notes',
        }
        help_texts = {
            'title': 'Brief but descriptive title of what you are requesting',
            'budget': 'Select the budget line this will be charged to',
            'required_date': 'Date by which you need these items',
            'justification': 'Explain why this purchase is necessary',
            'is_emergency': 'Check if this is an urgent/emergency purchase',
        }


class RequisitionItemForm(forms.ModelForm):
    """Form for individual requisition items"""
    
    class Meta:
        model = RequisitionItem
        fields = [
            'item',
            'item_description',
            'specifications',
            'quantity',
            'unit_of_measure',
            'estimated_unit_price',
            'notes',
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-control item-select',
                'placeholder': 'Select from catalog (optional)'
            }),
            'item_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Describe the item you need'
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detailed technical specifications, requirements, or standards'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'min': '0.01',
                'step': '0.01',
                'placeholder': 'Qty'
            }),
            'unit_of_measure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Pieces, Boxes, Liters'
            }),
            'estimated_unit_price': forms.NumberInput(attrs={
                'class': 'form-control price-input',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Unit Price'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any special requirements or notes for this item'
            }),
        }
        labels = {
            'item': 'Catalog Item (Optional)',
            'item_description': 'Item Description',
            'specifications': 'Specifications',
            'quantity': 'Quantity',
            'unit_of_measure': 'Unit of Measure',
            'estimated_unit_price': 'Estimated Unit Price (KES)',
            'notes': 'Notes',
        }


# Formset for handling multiple requisition items
RequisitionItemFormSet = inlineformset_factory(
    Requisition,
    RequisitionItem,
    form=RequisitionItemForm,
    extra=3,  # Show 3 empty forms initially
    can_delete=True,
    min_num=1,  # At least one item required
    validate_min=True,
)


class RequisitionAttachmentForm(forms.ModelForm):
    """Form for requisition attachments"""
    
    class Meta:
        model = RequisitionAttachment
        fields = [
            'attachment_type',
            'file_name',
            'file',
            'description',
        ]
        widgets = {
            'attachment_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'file_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document name'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Brief description of this document'
            }),
        }
        labels = {
            'attachment_type': 'Document Type',
            'file_name': 'Document Name',
            'file': 'Upload File',
            'description': 'Description',
        }


# Formset for handling multiple attachments
RequisitionAttachmentFormSet = inlineformset_factory(
    Requisition,
    RequisitionAttachment,
    form=RequisitionAttachmentForm,
    extra=2,  # Show 2 empty forms initially
    can_delete=True,
    min_num=0,  # Attachments are optional
    validate_min=False,
)


class RequisitionFilterForm(forms.Form):
    """Form for filtering requisitions"""
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('HOD_APPROVED', 'HOD Approved'),
        ('FACULTY_APPROVED', 'Faculty Approved'),
        ('BUDGET_APPROVED', 'Budget Approved'),
        ('PROCUREMENT_APPROVED', 'Procurement Approved'),
        ('APPROVED', 'Fully Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('', 'All Priorities'),
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by requisition number, title...'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='From Date'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='To Date'
    )


class QuickRequisitionForm(forms.Form):
    """Simplified form for quick requisition creation"""
    
    title = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'What do you need?'
        })
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe your requirement...'
        })
    )
    
    priority = forms.ChoiceField(
        choices=Requisition.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    required_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    

"""
Finance Forms
Forms for finance officer functionality
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    Payment, Budget, BudgetReallocation, Invoice,
    BudgetYear, Department, BudgetCategory
)


class PaymentForm(forms.ModelForm):
    """Form for processing payments"""
    
    class Meta:
        model = Payment
        fields = [
            'payment_date',
            'payment_amount',
            'payment_method',
            'payment_reference',
            'bank_name',
            'cheque_number',
            'notes'
        ]
        widgets = {
            'payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'payment_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment reference number'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bank name (if applicable)'
            }),
            'cheque_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter cheque number (if applicable)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            })
        }
    
    def clean_payment_amount(self):
        """Validate payment amount"""
        amount = self.cleaned_data.get('payment_amount')
        if amount <= 0:
            raise ValidationError('Payment amount must be greater than zero.')
        return amount
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        cheque_number = cleaned_data.get('cheque_number')
        bank_name = cleaned_data.get('bank_name')
        
        # Validate cheque details if payment method is cheque
        if payment_method == 'CHEQUE':
            if not cheque_number:
                raise ValidationError({
                    'cheque_number': 'Cheque number is required for cheque payments.'
                })
            if not bank_name:
                raise ValidationError({
                    'bank_name': 'Bank name is required for cheque payments.'
                })
        
        return cleaned_data


class BudgetForm(forms.ModelForm):
    """Form for creating/editing budgets"""
    
    class Meta:
        model = Budget
        fields = [
            'budget_year',
            'department',
            'category',
            'budget_type',
            'allocated_amount',
            'reference_number',
            'description'
        ]
        widgets = {
            'budget_year': forms.Select(attrs={
                'class': 'form-control'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'budget_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'allocated_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Enter allocated amount'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reference number (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter budget description'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active budget years
        self.fields['budget_year'].queryset = BudgetYear.objects.all().order_by('-start_date')
        # Filter active departments
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        # Filter active categories
        self.fields['category'].queryset = BudgetCategory.objects.filter(is_active=True).order_by('code')
    
    def clean_allocated_amount(self):
        """Validate allocated amount"""
        amount = self.cleaned_data.get('allocated_amount')
        if amount <= 0:
            raise ValidationError('Allocated amount must be greater than zero.')
        return amount
    
    def clean(self):
        """Validate unique constraint"""
        cleaned_data = super().clean()
        budget_year = cleaned_data.get('budget_year')
        department = cleaned_data.get('department')
        category = cleaned_data.get('category')
        reference_number = cleaned_data.get('reference_number')
        
        if budget_year and department and category:
            # Check for duplicate budget
            query = Budget.objects.filter(
                budget_year=budget_year,
                department=department,
                category=category,
                reference_number=reference_number
            )
            
            # Exclude current instance if editing
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise ValidationError(
                    'A budget already exists for this combination of year, department, category, and reference number.'
                )
        
        return cleaned_data


class BudgetReallocationForm(forms.ModelForm):
    """Form for budget reallocation/virement"""
    
    class Meta:
        model = BudgetReallocation
        fields = [
            'from_budget',
            'to_budget',
            'amount',
            'justification'
        ]
        widgets = {
            'from_budget': forms.Select(attrs={
                'class': 'form-control'
            }),
            'to_budget': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Enter reallocation amount'
            }),
            'justification': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide justification for this reallocation'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get current active budget year
        current_year = BudgetYear.objects.filter(is_active=True).first()
        if current_year:
            # Filter budgets for current year only
            active_budgets = Budget.objects.filter(
                budget_year=current_year,
                is_active=True
            ).select_related('department', 'category').order_by('department__name', 'category__name')
            
            self.fields['from_budget'].queryset = active_budgets
            self.fields['to_budget'].queryset = active_budgets
    
    def clean_amount(self):
        """Validate reallocation amount"""
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError('Reallocation amount must be greater than zero.')
        return amount
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        from_budget = cleaned_data.get('from_budget')
        to_budget = cleaned_data.get('to_budget')
        amount = cleaned_data.get('amount')
        
        if from_budget and to_budget:
            # Check if same budget
            if from_budget == to_budget:
                raise ValidationError('Cannot reallocate to the same budget.')
            
            # Check if sufficient balance
            if from_budget.available_balance < amount:
                raise ValidationError({
                    'amount': f'Insufficient available balance in source budget. Available: {from_budget.available_balance}'
                })
        
        return cleaned_data


class InvoiceFilterForm(forms.Form):
    """Form for filtering invoices"""
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Invoice.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    supplier = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='All Suppliers',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search invoice number or supplier...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Supplier
        self.fields['supplier'].queryset = Supplier.objects.filter(
            status='APPROVED'
        ).order_by('name')


class PaymentFilterForm(forms.Form):
    """Form for filtering payments"""
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Payment.PAYMENT_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_method = forms.ChoiceField(
        choices=[('', 'All Methods')] + Payment.PAYMENT_METHODS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search payment number or reference...'
        })
    )


class BudgetFilterForm(forms.Form):
    """Form for filtering budgets"""
    
    year = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='All Years',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='All Departments',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    budget_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Budget.BUDGET_TYPE,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search department, category, or reference...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].queryset = BudgetYear.objects.all().order_by('-start_date')
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['category'].queryset = BudgetCategory.objects.filter(is_active=True).order_by('code')


class ReportFilterForm(forms.Form):
    """Form for report filtering"""
    
    date_from = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='From Date'
    )
    
    date_to = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='To Date'
    )
    
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='All Departments',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    export_format = forms.ChoiceField(
        choices=[
            ('csv', 'CSV'),
            ('pdf', 'PDF'),
            ('excel', 'Excel')
        ],
        required=False,
        initial='csv',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
    
    def clean(self):
        """Validate date range"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError('From date must be before to date.')
        
        return cleaned_data
    