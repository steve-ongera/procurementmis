from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


# ============================================================================
# 1. USER & ROLE MANAGEMENT
# ============================================================================

class User(AbstractUser):
    """Extended User model with university-specific fields"""
    ROLE_CHOICES = [
        ('STAFF', 'Requesting Staff'),
        ('HOD', 'Head of Department'),
        ('PROCUREMENT', 'Procurement Officer'),
        ('FINANCE', 'Finance Officer'),
        ('STORES', 'Stores Officer'),
        ('SUPPLIER', 'Supplier/Vendor'),
        ('AUDITOR', 'Internal Auditor'),
        ('ADMIN', 'System Administrator'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    is_active_user = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"


class Permission(models.Model):
    """Granular permissions for role-based access control"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'permissions'
        ordering = ['module', 'name']

    def __str__(self):
        return f"{self.module} - {self.name}"


class RolePermission(models.Model):
    """Maps permissions to user roles"""
    role = models.CharField(max_length=20)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'role_permissions'
        unique_together = ['role', 'permission']

    def __str__(self):
        return f"{self.role} - {self.permission.name}"


class AuditLog(models.Model):
    """System-wide audit trail"""
    ACTION_TYPES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('APPROVE', 'Approved'),
        ('REJECT', 'Rejected'),
        ('SUBMIT', 'Submitted'),
        ('CANCEL', 'Cancelled'),
        ('LOGIN', 'Logged In'),
        ('LOGOUT', 'Logged Out'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=255)
    object_repr = models.CharField(max_length=500)
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} at {self.timestamp}"


# ============================================================================
# 2. ORGANIZATIONAL STRUCTURE
# ============================================================================

class Faculty(models.Model):
    """University Faculties/Schools"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    dean = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dean_of')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'faculties'
        verbose_name_plural = 'Faculties'
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(models.Model):
    """Academic and Administrative Departments"""
    DEPARTMENT_TYPE = [
        ('ACADEMIC', 'Academic'),
        ('ADMINISTRATIVE', 'Administrative'),
        ('SUPPORT', 'Support Services'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    department_type = models.CharField(max_length=20, choices=DEPARTMENT_TYPE)
    hod = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='head_of')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departments'
        unique_together = ['faculty', 'name']
        ordering = ['faculty', 'name']

    def __str__(self):
        return f"{self.faculty.code} - {self.name}"


# ============================================================================
# 3. BUDGET MANAGEMENT
# ============================================================================

class BudgetYear(models.Model):
    """Financial/Budget Years"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budget_years'
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class BudgetCategory(models.Model):
    """Budget line items/categories"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'budget_categories'
        verbose_name_plural = 'Budget Categories'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Budget(models.Model):
    """Budget allocations"""
    BUDGET_TYPE = [
        ('DEPARTMENTAL', 'Departmental Budget'),
        ('PROJECT', 'Project Budget'),
        ('GRANT', 'Grant/Donor Funded'),
        ('CAPITAL', 'Capital Expenditure'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget_year = models.ForeignKey(BudgetYear, on_delete=models.CASCADE, related_name='budgets')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE, related_name='budgets')
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE)
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2)
    committed_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    actual_spent = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    reference_number = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='budgets_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budgets'
        unique_together = ['budget_year', 'department', 'category', 'reference_number']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.department.code} - {self.category.code} ({self.budget_year.name})"

    @property
    def available_balance(self):
        allocated = self.allocated_amount or Decimal('0.00')
        committed = self.committed_amount or Decimal('0.00')
        spent = self.actual_spent or Decimal('0.00')
        return allocated - committed - spent


class BudgetReallocation(models.Model):
    """Track budget reallocations/virements"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='reallocations_from')
    to_budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='reallocations_to')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    justification = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reallocations_requested')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reallocations_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'budget_reallocations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Reallocation: {self.amount} from {self.from_budget} to {self.to_budget}"


# ============================================================================
# 4. ITEM CATALOG
# ============================================================================

class ItemCategory(models.Model):
    """Categories for procurement items"""
    CATEGORY_TYPE = [
        ('GOODS', 'Goods'),
        ('SERVICES', 'Services'),
        ('WORKS', 'Works'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    description = models.TextField(blank=True)
    requires_specifications = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'item_categories'
        verbose_name_plural = 'Item Categories'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Item(models.Model):
    """Master catalog of items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(ItemCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=300)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    unit_of_measure = models.CharField(max_length=50)
    standard_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    specifications = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'items'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ProcurementPlan(models.Model):
    """Annual Procurement Plan"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('AMENDED', 'Amended'),
        ('CLOSED', 'Closed'),
    ]
    
    QUARTER_CHOICES = [
        ('Q1', 'Quarter 1 (Jul-Sep)'),
        ('Q2', 'Quarter 2 (Oct-Dec)'),
        ('Q3', 'Quarter 3 (Jan-Mar)'),
        ('Q4', 'Quarter 4 (Apr-Jun)'),
    ]
    
    PROCUREMENT_METHOD_CHOICES = [
        ('OPEN_TENDER', 'Open Tender'),
        ('RESTRICTED_TENDER', 'Restricted Tender'),
        ('RFQ', 'Request for Quotation'),
        ('DIRECT_PROCUREMENT', 'Direct Procurement'),
        ('FRAMEWORK', 'Framework Agreement'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_number = models.CharField(max_length=50, unique=True, editable=False)
    
    budget_year = models.ForeignKey(
        BudgetYear, 
        on_delete=models.CASCADE, 
        related_name='procurement_plans'
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='procurement_plans'
    )
    
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Approval tracking
    submitted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='plans_submitted'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='plans_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Amendment tracking
    is_amended = models.BooleanField(default=False)
    amendment_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_plans'
        unique_together = ['budget_year', 'department']
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.plan_number:
            year = self.budget_year.name.replace('/', '-')
            last_plan = ProcurementPlan.objects.filter(
                plan_number__startswith=f'PP-{year}'
            ).order_by('-plan_number').first()
            
            if last_plan:
                last_number = int(last_plan.plan_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.plan_number = f'PP-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.plan_number} - {self.department.code} ({self.budget_year.name})"


class ProcurementPlanItem(models.Model):
    """Individual items in procurement plan"""
    ITEM_TYPE_CHOICES = [
        ('GOODS', 'Goods'),
        ('SERVICES', 'Services'),
        ('WORKS', 'Works'),
    ]
    
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('CARRIED_FORWARD', 'Carried Forward'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    procurement_plan = models.ForeignKey(
        ProcurementPlan, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    
    # Link to item catalog (optional)
    item = models.ForeignKey(
        Item, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='plan_items'
    )
    
    # Item details
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    description = models.TextField()
    specifications = models.TextField(blank=True)
    
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)]
    )
    unit_of_measure = models.CharField(max_length=50)
    
    # Budget allocation
    estimated_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    budget = models.ForeignKey(
        Budget, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='plan_items'
    )
    
    # Procurement details
    procurement_method = models.CharField(
        max_length=30, 
        choices=ProcurementPlan.PROCUREMENT_METHOD_CHOICES
    )
    planned_quarter = models.CharField(
        max_length=2, 
        choices=ProcurementPlan.QUARTER_CHOICES
    )
    
    # Source of funds
    source_of_funds = models.CharField(
        max_length=100,
        help_text="e.g., Government Budget, Donor Funds, IGR"
    )
    
    # Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    
    # Usage tracking
    quantity_requisitioned = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    amount_committed = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0
    )
    
    sequence = models.IntegerField(default=1)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_plan_items'
        ordering = ['procurement_plan', 'sequence']

    def __str__(self):
        return f"{self.procurement_plan.plan_number} - {self.description[:50]}"
    
    @property
    def remaining_quantity(self):
        return self.quantity - self.quantity_requisitioned
    
    @property
    def remaining_budget(self):
        return self.estimated_cost - self.amount_committed


class ProcurementPlanAmendment(models.Model):
    """Track amendments to procurement plans"""
    AMENDMENT_TYPE_CHOICES = [
        ('ADD_ITEM', 'Add New Item'),
        ('REMOVE_ITEM', 'Remove Item'),
        ('MODIFY_ITEM', 'Modify Existing Item'),
        ('BUDGET_CHANGE', 'Budget Change'),
        ('QUARTER_CHANGE', 'Quarter Change'),
        ('METHOD_CHANGE', 'Procurement Method Change'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amendment_number = models.CharField(max_length=50, unique=True, editable=False)
    
    procurement_plan = models.ForeignKey(
        ProcurementPlan, 
        on_delete=models.CASCADE, 
        related_name='amendments'
    )
    
    amendment_type = models.CharField(max_length=20, choices=AMENDMENT_TYPE_CHOICES)
    
    # What's being changed
    plan_item = models.ForeignKey(
        ProcurementPlanItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='amendments'
    )
    
    justification = models.TextField(
        help_text="Detailed reason for amendment"
    )
    
    # Changes (stored as JSON for flexibility)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    # Supporting documents
    supporting_document = models.FileField(
        upload_to='plan_amendments/',
        null=True,
        blank=True
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Approval workflow
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='plan_amendments_requested'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plan_amendments_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'procurement_plan_amendments'
        ordering = ['-requested_at']

    def save(self, *args, **kwargs):
        if not self.amendment_number:
            plan_number = self.procurement_plan.plan_number
            count = self.procurement_plan.amendments.count() + 1
            self.amendment_number = f"{plan_number}-AMD-{count:03d}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.amendment_number} - {self.get_amendment_type_display()}"


# ============================================================================
# 5. SUPPLIER/VENDOR MANAGEMENT
# ============================================================================

class Supplier(models.Model):
    """Vendor/Supplier registry"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('SUSPENDED', 'Suspended'),
        ('BLACKLISTED', 'Blacklisted'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='supplier_profile',
        help_text="User account linked to this supplier"
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=300)
    registration_number = models.CharField(max_length=100, unique=True)
    tax_id = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    physical_address = models.TextField()
    postal_address = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    contact_person = models.CharField(max_length=200)
    contact_person_phone = models.CharField(max_length=20)
    contact_person_email = models.EmailField()
    
    bank_name = models.CharField(max_length=200)
    bank_branch = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=200)
    swift_code = models.CharField(max_length=20, blank=True)
    
    categories = models.ManyToManyField(ItemCategory, related_name='suppliers')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    
    tax_compliance_expiry = models.DateField(null=True, blank=True)
    registration_expiry = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='suppliers_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'suppliers'
        ordering = ['name']

    def __str__(self):
        return f"{self.supplier_number} - {self.name}"


class SupplierDocument(models.Model):
    """Supplier compliance documents"""
    DOCUMENT_TYPES = [
        ('REGISTRATION', 'Business Registration Certificate'),
        ('TAX', 'Tax Compliance Certificate'),
        ('BANK', 'Bank Statement'),
        ('LICENSE', 'Professional License'),
        ('INSURANCE', 'Insurance Certificate'),
        ('OTHER', 'Other Document'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=200)
    file = models.FileField(upload_to='supplier_documents/')
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_supplier_docs')
    verified_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'supplier_documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.supplier.name} - {self.document_name}"


class SupplierPerformance(models.Model):
    """Track supplier performance per transaction"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='performances')
    purchase_order = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE, related_name='performance_reviews')
    
    quality_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    delivery_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    service_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2)
    
    comments = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'supplier_performances'
        ordering = ['-reviewed_at']

    def save(self, *args, **kwargs):
        self.overall_rating = (self.quality_rating + self.delivery_rating + self.service_rating) / 3
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.supplier.name} - {self.overall_rating}/5"


# ============================================================================
# 6. REQUISITION MANAGEMENT
# ============================================================================

class Requisition(models.Model):
    """Purchase requisitions"""
    STATUS_CHOICES = [
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
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requisition_number = models.CharField(max_length=50, unique=True, editable=False)
    title = models.CharField(max_length=300)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='requisitions')
    budget = models.ForeignKey(Budget, on_delete=models.SET_NULL, null=True, related_name='requisitions')
    
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisitions_created')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    justification = models.TextField()
    estimated_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    required_date = models.DateField()
    
    is_emergency = models.BooleanField(default=False)
    emergency_justification = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    procurement_plan_item = models.ForeignKey(
        ProcurementPlanItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisitions',
        help_text="Link to approved procurement plan item"
    )
    
    is_planned = models.BooleanField(
        default=True,
        help_text="Whether this requisition is from procurement plan"
    )
    
    # For unplanned requisitions
    is_emergency = models.BooleanField(
        default=False,
        help_text="Emergency procurement flag"
    )
    
    emergency_justification = models.TextField(
        blank=True,
        help_text="Detailed justification for unplanned/emergency procurement"
    )
    
    emergency_type = models.CharField(
        max_length=20,
        choices=[
            ('BREAKDOWN', 'Equipment Breakdown'),
            ('SAFETY', 'Safety/Health Emergency'),
            ('REGULATORY', 'Regulatory/Compliance Requirement'),
            ('DONOR', 'New Donor Funding'),
            ('ACADEMIC', 'New Academic Requirement'),
            ('OTHER', 'Other Emergency'),
        ],
        null=True,
        blank=True
    )
    
    # Plan amendment tracking
    requires_plan_amendment = models.BooleanField(
        default=False,
        help_text="Whether plan needs to be amended for this requisition"
    )
    
    plan_amendment = models.ForeignKey(
        ProcurementPlanAmendment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisitions',
        help_text="Link to plan amendment if required"
    )
    
    # Additional validation fields
    hod_emergency_approval = models.BooleanField(
        default=False,
        help_text="HOD confirmed this is genuine emergency"
    )
    
    plan_deviation_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plan_deviations_approved',
        help_text="Senior officer who approved deviation from plan"
    )
    
    plan_deviation_approved_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    

    class Meta:
        db_table = 'requisitions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['department', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.requisition_number:
            year = timezone.now().year
            last_req = Requisition.objects.filter(
                requisition_number__startswith=f'REQ-{year}'
            ).order_by('-requisition_number').first()
            
            if last_req:
                last_number = int(last_req.requisition_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.requisition_number = f'REQ-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.requisition_number} - {self.title}"


class RequisitionItem(models.Model):
    """Line items in a requisition"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisition_items')
    item_description = models.TextField()
    specifications = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_of_measure = models.CharField(max_length=50)
    estimated_unit_price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    estimated_total = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'requisition_items'
        ordering = ['requisition', 'id']

    def save(self, *args, **kwargs):
        self.estimated_total = self.quantity * self.estimated_unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.requisition.requisition_number} - {self.item_description[:50]}"


class RequisitionAttachment(models.Model):
    """Supporting documents for requisitions"""
    ATTACHMENT_TYPES = [
        ('QUOTATION', 'Quotation'),
        ('TOR', 'Terms of Reference'),
        ('SPECIFICATION', 'Technical Specification'),
        ('JUSTIFICATION', 'Justification Document'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, related_name='attachments')
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='requisition_attachments/')
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'requisition_attachments'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.requisition.requisition_number} - {self.file_name}"


# ============================================================================
# 7. APPROVAL WORKFLOW
# ============================================================================

class ApprovalThreshold(models.Model):
    """Approval thresholds based on amount"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    min_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    requires_hod_approval = models.BooleanField(default=True)
    requires_faculty_approval = models.BooleanField(default=False)
    requires_procurement_approval = models.BooleanField(default=True)
    requires_finance_approval = models.BooleanField(default=True)
    requires_tender = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'approval_thresholds'
        ordering = ['min_amount']

    def __str__(self):
        return self.name


class RequisitionApproval(models.Model):
    """Approval workflow tracking"""
    APPROVAL_STAGES = [
        ('HOD', 'Head of Department'),
        ('FACULTY', 'Faculty/School Dean'),
        ('BUDGET', 'Budget/Finance Check'),
        ('PROCUREMENT', 'Procurement Officer'),
        ('FINAL', 'Final Approval'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, related_name='approvals')
    approval_stage = models.CharField(max_length=20, choices=APPROVAL_STAGES)
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approvals_made')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    comments = models.TextField(blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    sequence = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'requisition_approvals'
        ordering = ['requisition', 'sequence']
        unique_together = ['requisition', 'approval_stage']

    def __str__(self):
        return f"{self.requisition.requisition_number} - {self.get_approval_stage_display()}"


# ============================================================================
# 8. TENDERING & QUOTATIONS
# ============================================================================

class Tender(models.Model):
    """Tender/RFQ/RFP management"""
    TENDER_TYPES = [
        ('RFQ', 'Request for Quotation'),
        ('RFP', 'Request for Proposal'),
        ('ITB', 'Invitation to Bid'),
    ]
    
    METHOD_CHOICES = [
        ('OPEN', 'Open Tender'),
        ('RESTRICTED', 'Restricted Tender'),
        ('DIRECT', 'Direct Procurement'),
        ('FRAMEWORK', 'Framework Agreement'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CLOSED', 'Closed'),
        ('EVALUATING', 'Under Evaluation'),
        ('AWARDED', 'Awarded'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tender_number = models.CharField(max_length=50, unique=True, editable=False)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, related_name='tenders')
    title = models.CharField(max_length=300)
    tender_type = models.CharField(max_length=10, choices=TENDER_TYPES)
    procurement_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    
    description = models.TextField()
    publish_date = models.DateTimeField(null=True, blank=True)
    closing_date = models.DateTimeField()
    bid_opening_date = models.DateTimeField()
    
    estimated_budget = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    invited_suppliers = models.ManyToManyField(Supplier, related_name='invited_tenders', blank=True)
    
    # NEW FIELDS FOR EVALUATION
    requires_technical_evaluation = models.BooleanField(
        default=True,
        help_text="Whether technical evaluation is required"
    )
    
    technical_pass_mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum technical score to qualify"
    )
    
    evaluation_start_date = models.DateField(null=True, blank=True)
    evaluation_end_date = models.DateField(null=True, blank=True)
    
    preliminary_evaluation_complete = models.BooleanField(default=False)
    technical_evaluation_complete = models.BooleanField(default=False)
    financial_evaluation_complete = models.BooleanField(default=False)
    
    award_recommendation_date = models.DateField(null=True, blank=True)
    award_approved_date = models.DateField(null=True, blank=True)
    
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tenders_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenders'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.tender_number:
            year = timezone.now().year
            last_tender = Tender.objects.filter(
                tender_number__startswith=f'TND-{year}'
            ).order_by('-tender_number').first()
            
            if last_tender:
                last_number = int(last_tender.tender_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.tender_number = f'TND-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tender_number} - {self.title}"


class TenderDocument(models.Model):
    """Tender documents (RFQ/RFP documents)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='documents')
    document_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='tender_documents/')
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tender_documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.tender.tender_number} - {self.document_name}"


class Bid(models.Model):
    """Supplier bids/quotations"""
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('OPENED', 'Opened'),
        ('EVALUATING', 'Under Evaluation'),
        ('QUALIFIED', 'Qualified'),
        ('DISQUALIFIED', 'Disqualified'),
        ('AWARDED', 'Awarded'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bid_number = models.CharField(max_length=50, unique=True, editable=False)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='bids')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='bids')
    
    bid_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    bid_bond_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    validity_period_days = models.IntegerField(default=90)
    delivery_period_days = models.IntegerField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    evaluation_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    financial_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    disqualification_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # NEW FIELDS FOR EVALUATION
    preliminary_evaluation_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('RESPONSIVE', 'Responsive'),
            ('NON_RESPONSIVE', 'Non-Responsive'),
        ],
        default='PENDING'
    )
    
    preliminary_evaluation_notes = models.TextField(blank=True)
    
    technical_evaluation_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PASSED', 'Passed'),
            ('FAILED', 'Failed'),
        ],
        default='PENDING'
    )
    
    financial_evaluation_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('EVALUATED', 'Evaluated'),
        ],
        default='PENDING'
    )
    
    is_lowest_evaluated = models.BooleanField(
        default=False,
        help_text="Is this the lowest evaluated bidder"
    )
    
    price_variance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Variance from engineer's estimate"
    )
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    opened_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bids_opened')

    class Meta:
        db_table = 'bids'
        ordering = ['tender', 'rank']
        unique_together = ['tender', 'supplier']

    def save(self, *args, **kwargs):
        if not self.bid_number:
            year = timezone.now().year
            last_bid = Bid.objects.filter(
                bid_number__startswith=f'BID-{year}'
            ).order_by('-bid_number').first()
            
            if last_bid:
                last_number = int(last_bid.bid_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.bid_number = f'BID-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bid_number} - {self.supplier.name}"


class BidItem(models.Model):
    """Line items in a bid"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='items')
    requisition_item = models.ForeignKey(RequisitionItem, on_delete=models.CASCADE, related_name='bid_items')
    
    quoted_unit_price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    quoted_total = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    brand = models.CharField(max_length=200, blank=True)
    model = models.CharField(max_length=200, blank=True)
    specifications = models.TextField(blank=True)
    delivery_period_days = models.IntegerField()
    warranty_period_months = models.IntegerField(default=0)
    
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'bid_items'
        ordering = ['bid', 'id']

    def save(self, *args, **kwargs):
        self.quoted_total = self.requisition_item.quantity * self.quoted_unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bid.bid_number} - Item {self.id}"


class BidDocument(models.Model):
    """Documents submitted with bid"""
    DOCUMENT_TYPES = [
        ('TECHNICAL', 'Technical Proposal'),
        ('FINANCIAL', 'Financial Proposal'),
        ('COMPLIANCE', 'Compliance Document'),
        ('CERTIFICATE', 'Certificate'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='bid_documents/')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bid_documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.bid.bid_number} - {self.document_name}"


class BidEvaluation(models.Model):
    """Bid evaluation records"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='evaluations')
    evaluator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    technical_compliance = models.BooleanField(default=True)
    financial_compliance = models.BooleanField(default=True)
    
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    financial_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    total_score = models.DecimalField(max_digits=5, decimal_places=2)
    
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    recommendation = models.TextField()
    
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bid_evaluations'
        ordering = ['-evaluated_at']

    def save(self, *args, **kwargs):
        # Weighted scoring: 70% technical, 30% financial
        # Convert float literals to Decimal to avoid TypeError 
        self.total_score = (self.technical_score * Decimal('0.7')) + (self.financial_score * Decimal('0.3'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Evaluation: {self.bid.bid_number} by {self.evaluator}"


class EvaluationCriteria(models.Model):
    """Evaluation criteria for tenders"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name='evaluation_criteria')
    criterion_name = models.CharField(max_length=200)
    criterion_type = models.CharField(max_length=20, choices=[
        ('TECHNICAL', 'Technical'),
        ('FINANCIAL', 'Financial'),
        ('GENERAL', 'General'),
    ])
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    is_mandatory = models.BooleanField(default=False)
    sequence = models.IntegerField(default=1)

    class Meta:
        db_table = 'evaluation_criteria'
        ordering = ['tender', 'sequence']

    def __str__(self):
        return f"{self.tender.tender_number} - {self.criterion_name}"


class EvaluationCommittee(models.Model):
    """Tender Evaluation Committee"""
    COMMITTEE_TYPES = [
        ('TECHNICAL', 'Technical Evaluation'),
        ('FINANCIAL', 'Financial Evaluation'),
        ('COMBINED', 'Combined Evaluation'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    committee_number = models.CharField(max_length=50, unique=True, editable=False)
    tender = models.ForeignKey('Tender', on_delete=models.CASCADE, related_name='evaluation_committees')
    
    committee_type = models.CharField(max_length=20, choices=COMMITTEE_TYPES)
    name = models.CharField(max_length=300)
    
    chairperson = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='committees_chaired'
    )
    
    secretary = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='committees_secretaried'
    )
    
    appointment_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    terms_of_reference = models.TextField()
    evaluation_guidelines = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'evaluation_committees'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.committee_number:
            year = timezone.now().year
            last_committee = EvaluationCommittee.objects.filter(
                committee_number__startswith=f'EC-{year}'
            ).order_by('-committee_number').first()
            
            if last_committee:
                last_number = int(last_committee.committee_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.committee_number = f'EC-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.committee_number} - {self.tender.tender_number}"
    
class CommitteeMember(models.Model):
    """Members of evaluation committee"""
    MEMBER_ROLES = [
        ('CHAIRPERSON', 'Chairperson'),
        ('SECRETARY', 'Secretary'),
        ('MEMBER', 'Member'),
        ('OBSERVER', 'Observer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    committee = models.ForeignKey(
        EvaluationCommittee, 
        on_delete=models.CASCADE, 
        related_name='members'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='committee_memberships')
    
    role = models.CharField(max_length=20, choices=MEMBER_ROLES)
    department = models.ForeignKey(
        'Department', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='committee_members'
    )
    
    expertise_area = models.CharField(max_length=200, blank=True)
    
    # Conflict of interest declaration
    has_conflict = models.BooleanField(default=False)
    conflict_details = models.TextField(blank=True)
    
    appointed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'committee_members'
        unique_together = ['committee', 'user']
        ordering = ['committee', 'role']

    def __str__(self):
        return f"{self.committee.committee_number} - {self.user.get_full_name()} ({self.role})"
    
    
class TechnicalEvaluationCriteria(models.Model):
    """Technical evaluation criteria for tenders"""
    RESPONSE_TYPES = [
        ('YES_NO', 'Yes/No'),
        ('DOCUMENT', 'Document Upload'),
        ('NUMERIC', 'Numeric Value'),
        ('TEXT', 'Text Description'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tender = models.ForeignKey(
        'Tender', 
        on_delete=models.CASCADE, 
        related_name='technical_criteria'
    )
    
    criterion_name = models.CharField(max_length=300)
    description = models.TextField()
    minimum_specification = models.TextField()
    
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPES)
    
    is_mandatory = models.BooleanField(default=True)
    is_pass_fail = models.BooleanField(
        default=False,
        help_text="If true, failing this criterion disqualifies the bid"
    )
    
    max_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Maximum points for this criterion"
    )
    
    weight_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Weight in overall technical score"
    )
    
    scoring_guidelines = models.TextField(
        blank=True,
        help_text="How to score this criterion"
    )
    
    sequence = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'technical_evaluation_criteria'
        ordering = ['tender', 'sequence']

    def __str__(self):
        return f"{self.tender.tender_number} - {self.criterion_name}"
    
    
class FinancialEvaluationCriteria(models.Model):
    """Financial evaluation criteria"""
    EVALUATION_METHODS = [
        ('LOWEST_PRICE', 'Lowest Evaluated Price'),
        ('FIXED_BUDGET', 'Fixed Budget'),
        ('QUALITY_COST', 'Quality and Cost Based'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tender = models.OneToOneField(
        'Tender',
        on_delete=models.CASCADE,
        related_name='financial_criteria'
    )
    
    evaluation_method = models.CharField(max_length=20, choices=EVALUATION_METHODS)
    
    # Technical-Financial weighting
    technical_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    financial_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Price evaluation formula
    uses_formula = models.BooleanField(default=True)
    formula_description = models.TextField(
        blank=True,
        help_text="e.g., Score = (Lowest Price / Bid Price) × 100"
    )
    
    # Price reasonability
    check_price_reasonability = models.BooleanField(default=True)
    acceptable_variance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15,
        help_text="Acceptable variance from engineer's estimate"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_evaluation_criteria'

    def __str__(self):
        return f"{self.tender.tender_number} - Financial Criteria"
    
class BidTechnicalResponse(models.Model):
    """Supplier responses to technical criteria"""
    RESPONSE_STATUS = [
        ('PENDING', 'Pending Review'),
        ('COMPLIANT', 'Compliant'),
        ('NON_COMPLIANT', 'Non-Compliant'),
        ('PARTIALLY_COMPLIANT', 'Partially Compliant'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bid = models.ForeignKey('Bid', on_delete=models.CASCADE, related_name='technical_responses')
    criterion = models.ForeignKey(
        TechnicalEvaluationCriteria,
        on_delete=models.CASCADE,
        related_name='bid_responses'
    )
    
    # Supplier's response
    response_text = models.TextField(blank=True)
    response_value = models.CharField(max_length=200, blank=True)
    
    # Supporting documents
    supporting_document = models.FileField(
        upload_to='bid_technical_documents/',
        null=True,
        blank=True
    )
    
    supplier_remarks = models.TextField(blank=True)
    
    # Evaluation
    compliance_status = models.CharField(
        max_length=30,
        choices=RESPONSE_STATUS,
        default='PENDING'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bid_technical_responses'
        unique_together = ['bid', 'criterion']
        ordering = ['bid', 'criterion__sequence']

    def __str__(self):
        return f"{self.bid.bid_number} - {self.criterion.criterion_name}"
    
    
class TechnicalEvaluationScore(models.Model):
    """Individual evaluator scores for technical criteria"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    bid = models.ForeignKey('Bid', on_delete=models.CASCADE, related_name='technical_scores')
    criterion = models.ForeignKey(
        TechnicalEvaluationCriteria,
        on_delete=models.CASCADE,
        related_name='scores'
    )
    evaluator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='technical_scores_given'
    )
    
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    weighted_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    is_compliant = models.BooleanField(default=True)
    
    comments = models.TextField(blank=True)
    justification = models.TextField(blank=True)
    
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'technical_evaluation_scores'
        unique_together = ['bid', 'criterion', 'evaluator']
        ordering = ['bid', 'criterion__sequence']

    def save(self, *args, **kwargs):
        # Calculate weighted score
        self.weighted_score = (self.score / self.criterion.max_score) * self.criterion.weight_percentage
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bid.bid_number} - {self.criterion.criterion_name} - {self.score}"
    
    
    
class FinancialEvaluationScore(models.Model):
    """Financial evaluation scores"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    bid = models.ForeignKey('Bid', on_delete=models.CASCADE, related_name='financial_scores')
    evaluator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='financial_scores_given'
    )
    
    # Price analysis
    quoted_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    is_arithmetic_correct = models.BooleanField(default=True)
    arithmetic_notes = models.TextField(blank=True)
    
    is_within_budget = models.BooleanField(default=True)
    
    # Price reasonability
    is_price_reasonable = models.BooleanField(default=True)
    variance_from_estimate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage variance"
    )
    
    # Financial score
    financial_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    weighted_financial_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    comments = models.TextField(blank=True)
    
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_evaluation_scores'
        unique_together = ['bid', 'evaluator']
        ordering = ['bid', 'financial_score']

    def __str__(self):
        return f"{self.bid.bid_number} - Financial Score: {self.financial_score}"
    
    
    
class CombinedEvaluationResult(models.Model):
    """Final combined technical + financial evaluation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    bid = models.OneToOneField(
        'Bid',
        on_delete=models.CASCADE,
        related_name='combined_evaluation'
    )
    
    # Technical Evaluation
    average_technical_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    technical_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    is_technically_qualified = models.BooleanField(default=False)
    technical_pass_mark = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Financial Evaluation
    average_financial_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    financial_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Combined Score
    combined_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    final_rank = models.IntegerField(null=True, blank=True)
    
    # Recommendation
    is_recommended = models.BooleanField(default=False)
    recommendation_notes = models.TextField(blank=True)
    
    # Disqualification
    is_disqualified = models.BooleanField(default=False)
    disqualification_reason = models.TextField(blank=True)
    
    evaluated_by_committee = models.ForeignKey(
        EvaluationCommittee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evaluation_results'
    )
    
    evaluation_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'combined_evaluation_results'
        ordering = ['bid__tender', '-combined_score']

    def calculate_combined_score(self):
        """Calculate the final combined score"""
        financial_criteria = self.bid.tender.financial_criteria
        
        self.combined_score = (
            (self.average_technical_score * financial_criteria.technical_weight / 100) +
            (self.average_financial_score * financial_criteria.financial_weight / 100)
        )
        
        self.save()

    def __str__(self):
        return f"{self.bid.bid_number} - Score: {self.combined_score}"
    
    
    
class EvaluationReport(models.Model):
    """Formal evaluation reports"""
    REPORT_TYPES = [
        ('PRELIMINARY', 'Preliminary Evaluation'),
        ('TECHNICAL', 'Technical Evaluation'),
        ('FINANCIAL', 'Financial Evaluation'),
        ('COMBINED', 'Combined Evaluation'),
        ('FINAL', 'Final Recommendation'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_number = models.CharField(max_length=50, unique=True, editable=False)
    
    tender = models.ForeignKey('Tender', on_delete=models.CASCADE, related_name='evaluation_reports')
    committee = models.ForeignKey(
        EvaluationCommittee,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=300)
    
    executive_summary = models.TextField()
    methodology = models.TextField()
    findings = models.TextField()
    recommendations = models.TextField()
    
    recommended_bidder = models.ForeignKey(
        'Bid',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommended_in_reports'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    report_document = models.FileField(
        upload_to='evaluation_reports/',
        null=True,
        blank=True
    )
    
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evaluation_reports_submitted'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluation_reports_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'evaluation_reports'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.report_number:
            year = timezone.now().year
            last_report = EvaluationReport.objects.filter(
                report_number__startswith=f'ER-{year}'
            ).order_by('-report_number').first()
            
            if last_report:
                last_number = int(last_report.report_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.report_number = f'ER-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.report_number} - {self.title}"

# ============================================================================
# 9. PURCHASE ORDERS
# ============================================================================

class PurchaseOrder(models.Model):
    """Purchase Orders"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('SENT', 'Sent to Supplier'),
        ('ACKNOWLEDGED', 'Acknowledged by Supplier'),
        ('PARTIAL_DELIVERY', 'Partially Delivered'),
        ('DELIVERED', 'Fully Delivered'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po_number = models.CharField(max_length=50, unique=True, editable=False)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_order')
    
    po_date = models.DateField(auto_now_add=True)
    delivery_date = models.DateField()
    delivery_address = models.TextField()
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    payment_terms = models.TextField()
    warranty_terms = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pos_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.po_number:
            year = timezone.now().year
            last_po = PurchaseOrder.objects.filter(
                po_number__startswith=f'PO-{year}'
            ).order_by('-po_number').first()
            
            if last_po:
                last_number = int(last_po.po_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.po_number = f'PO-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"


class PurchaseOrderItem(models.Model):
    """Line items in purchase order"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    requisition_item = models.ForeignKey(RequisitionItem, on_delete=models.CASCADE, related_name='po_items')
    
    item_description = models.TextField()
    specifications = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_of_measure = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    quantity_delivered = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_pending = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchase_order_items'
        ordering = ['purchase_order', 'id']

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        self.quantity_pending = self.quantity - self.quantity_delivered
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.item_description[:50]}"


class POAmendment(models.Model):
    """Purchase Order amendments/variations"""
    AMENDMENT_TYPES = [
        ('QUANTITY', 'Quantity Change'),
        ('PRICE', 'Price Change'),
        ('DELIVERY', 'Delivery Date Change'),
        ('TERMS', 'Terms Change'),
        ('CANCELLATION', 'Item Cancellation'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='amendments')
    amendment_number = models.CharField(max_length=50)
    amendment_type = models.CharField(max_length=20, choices=AMENDMENT_TYPES)
    
    description = models.TextField()
    justification = models.TextField()
    
    old_value = models.TextField()
    new_value = models.TextField()
    
    amount_change = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='po_amendments_requested')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='po_amendments_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'po_amendments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.purchase_order.po_number} - Amendment {self.amendment_number}"


# ============================================================================
# 10. CONTRACT MANAGEMENT
# ============================================================================

class Contract(models.Model):
    """Contract management"""
    CONTRACT_TYPES = [
        ('GOODS', 'Supply of Goods'),
        ('SERVICES', 'Provision of Services'),
        ('WORKS', 'Construction/Works'),
        ('CONSULTANCY', 'Consultancy'),
        ('MAINTENANCE', 'Maintenance Agreement'),
        ('FRAMEWORK', 'Framework Agreement'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('COMPLETED', 'Completed'),
        ('TERMINATED', 'Terminated'),
        ('EXPIRED', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract_number = models.CharField(max_length=50, unique=True, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='contracts')
    
    title = models.CharField(max_length=300)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES)
    description = models.TextField()
    
    contract_value = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    start_date = models.DateField()
    end_date = models.DateField()
    renewal_option = models.BooleanField(default=False)
    renewal_period_months = models.IntegerField(null=True, blank=True)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    
    payment_schedule = models.TextField()
    performance_bond_required = models.BooleanField(default=False)
    performance_bond_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    special_conditions = models.TextField(blank=True)
    termination_clause = models.TextField(blank=True)
    
    contract_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contracts_managed')
    
    signed_by_supplier = models.BooleanField(default=False)
    signed_by_university = models.BooleanField(default=False)
    signing_date = models.DateField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contracts_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contracts'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.contract_number:
            year = timezone.now().year
            last_contract = Contract.objects.filter(
                contract_number__startswith=f'CNT-{year}'
            ).order_by('-contract_number').first()
            
            if last_contract:
                last_number = int(last_contract.contract_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.contract_number = f'CNT-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.contract_number} - {self.title}"


class ContractDocument(models.Model):
    """Contract documents"""
    DOCUMENT_TYPES = [
        ('CONTRACT', 'Signed Contract'),
        ('ADDENDUM', 'Addendum'),
        ('PERFORMANCE_BOND', 'Performance Bond'),
        ('INSURANCE', 'Insurance Certificate'),
        ('VARIATION', 'Variation Order'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='contract_documents/')
    version = models.IntegerField(default=1)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contract_documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.contract.contract_number} - {self.document_name}"


class ContractMilestone(models.Model):
    """Contract milestones and deliverables"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('DELAYED', 'Delayed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='milestones')
    milestone_name = models.CharField(max_length=300)
    description = models.TextField()
    
    due_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    
    milestone_value = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    payment_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    deliverables = models.TextField()
    acceptance_criteria = models.TextField()
    
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='milestones_completed')
    notes = models.TextField(blank=True)
    
    sequence = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contract_milestones'
        ordering = ['contract', 'sequence']

    def __str__(self):
        return f"{self.contract.contract_number} - {self.milestone_name}"


class ContractVariation(models.Model):
    """Contract variations/amendments"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='variations')
    variation_number = models.CharField(max_length=50)
    
    title = models.CharField(max_length=300)
    description = models.TextField()
    justification = models.TextField()
    
    value_change = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    time_extension_days = models.IntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='variations_requested')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='variations_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contract_variations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract.contract_number} - Variation {self.variation_number}"


# ============================================================================
# 11. STORES & INVENTORY MANAGEMENT
# ============================================================================

class Store(models.Model):
    """Physical store/warehouse locations"""
    STORE_TYPES = [
        ('MAIN', 'Main Store'),
        ('DEPARTMENTAL', 'Departmental Store'),
        ('LABORATORY', 'Laboratory Store'),
        ('ICT', 'ICT Store'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    store_type = models.CharField(max_length=20, choices=STORE_TYPES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='stores')
    location = models.TextField()
    store_keeper = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stores_managed')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stores'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class GoodsReceivedNote(models.Model):
    """Goods Received Notes"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('INSPECTING', 'Under Inspection'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('PARTIAL', 'Partially Accepted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grn_number = models.CharField(max_length=50, unique=True, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='grns')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='grns')
    
    delivery_note_number = models.CharField(max_length=100)
    delivery_date = models.DateField()
    received_date = models.DateField(auto_now_add=True)
    
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='grns_received')
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='grns_inspected')
    inspection_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    general_condition = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'goods_received_notes'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.grn_number:
            year = timezone.now().year
            last_grn = GoodsReceivedNote.objects.filter(
                grn_number__startswith=f'GRN-{year}'
            ).order_by('-grn_number').first()
            
            if last_grn:
                last_number = int(last_grn.grn_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.grn_number = f'GRN-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.grn_number} - PO: {self.purchase_order.po_number}"


class GRNItem(models.Model):
    """Line items in GRN"""
    ITEM_STATUS = [
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('DAMAGED', 'Damaged'),
        ('INCOMPLETE', 'Incomplete'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.CASCADE, related_name='grn_items')
    
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_delivered = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity_accepted = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_rejected = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    item_status = models.CharField(max_length=20, choices=ITEM_STATUS, default='ACCEPTED')
    
    remarks = models.TextField(blank=True)

    class Meta:
        db_table = 'grn_items'
        ordering = ['grn', 'id']

    def __str__(self):
        return f"{self.grn.grn_number} - Item {self.id}"


class StockItem(models.Model):
    """Inventory stock items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stock_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='stock_items')
    
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_stock_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    average_unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    last_restock_date = models.DateField(null=True, blank=True)
    last_issue_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock_items'
        unique_together = ['store', 'item']
        ordering = ['store', 'item']

    def __str__(self):
        return f"{self.store.code} - {self.item.name} ({self.quantity_on_hand})"


class StockMovement(models.Model):
    """Track all stock movements"""
    MOVEMENT_TYPES = [
        ('RECEIPT', 'Receipt/Stock In'),
        ('ISSUE', 'Issue/Stock Out'),
        ('TRANSFER', 'Transfer Between Stores'),
        ('ADJUSTMENT', 'Stock Adjustment'),
        ('RETURN', 'Return to Store'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    
    reference_number = models.CharField(max_length=100)
    reference_type = models.CharField(max_length=50)  # e.g., "GRN", "Issue", "Transfer"
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    from_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_out')
    to_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_in')
    
    remarks = models.TextField(blank=True)
    
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    movement_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_movements'
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.movement_type} - {self.stock_item.item.name} - {self.quantity}"


class StockIssue(models.Model):
    """Stock issues to departments"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('ISSUED', 'Issued'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue_number = models.CharField(max_length=50, unique=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='issues')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='stock_issues')
    
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_issues_requested')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_issues_made')
    
    issue_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    purpose = models.TextField()
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_issues'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.issue_number:
            year = timezone.now().year
            last_issue = StockIssue.objects.filter(
                issue_number__startswith=f'ISS-{year}'
            ).order_by('-issue_number').first()
            
            if last_issue:
                last_number = int(last_issue.issue_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.issue_number = f'ISS-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.issue_number} - {self.department.name}"


class StockIssueItem(models.Model):
    """Items in a stock issue"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_issue = models.ForeignKey(StockIssue, on_delete=models.CASCADE, related_name='items')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='issue_items')
    
    quantity_requested = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    quantity_issued = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    remarks = models.TextField(blank=True)

    class Meta:
        db_table = 'stock_issue_items'
        ordering = ['stock_issue', 'id']

    def __str__(self):
        return f"{self.stock_issue.issue_number} - {self.stock_item.item.name}"


class Asset(models.Model):
    """Fixed assets register"""
    ASSET_STATUS = [
        ('ACTIVE', 'Active/In Use'),
        ('IDLE', 'Idle'),
        ('UNDER_MAINTENANCE', 'Under Maintenance'),
        ('DAMAGED', 'Damaged'),
        ('DISPOSED', 'Disposed'),
        ('LOST', 'Lost/Missing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset_number = models.CharField(max_length=50, unique=True)
    asset_tag = models.CharField(max_length=50, unique=True)
    
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='assets')
    
    description = models.TextField()
    serial_number = models.CharField(max_length=200, blank=True)
    model = models.CharField(max_length=200, blank=True)
    brand = models.CharField(max_length=200, blank=True)
    
    acquisition_date = models.DateField()
    acquisition_cost = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    current_value = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    useful_life_years = models.IntegerField(default=0)
    
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='assets')
    location = models.TextField()
    custodian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assets_custodian')
    
    status = models.CharField(max_length=30, choices=ASSET_STATUS, default='ACTIVE')
    
    warranty_expiry = models.DateField(null=True, blank=True)
    
    disposal_date = models.DateField(null=True, blank=True)
    disposal_method = models.CharField(max_length=100, blank=True)
    disposal_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assets'
        ordering = ['asset_number']

    def __str__(self):
        return f"{self.asset_number} - {self.description}"


# ============================================================================
# 12. INVOICE & PAYMENT PROCESSING
# ============================================================================

class Invoice(models.Model):
    """Supplier invoices"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('VERIFYING', 'Under Verification'),
        ('MATCHED', 'Matched'),
        ('APPROVED', 'Approved for Payment'),
        ('PAID', 'Paid'),
        ('DISPUTED', 'Disputed'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=100, unique=True)
    supplier_invoice_number = models.CharField(max_length=100)
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='invoices')
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='invoices')
    
    invoice_date = models.DateField()
    due_date = models.DateField()
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    is_three_way_matched = models.BooleanField(default=False)
    matching_notes = models.TextField(blank=True)
    
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_verified')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    
    dispute_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices_submitted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    # ADD THESE NEW FIELDS (at the end of existing fields)
    amount_paid = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Total amount paid so far"
    )
    balance_due = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Remaining balance to be paid"
    )
    
    def update_payment_status(self):
        """Update invoice payment status based on payments"""
        from django.db.models import Sum
        
        total_paid = self.payments.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('payment_amount'))['total'] or Decimal('0')
        
        self.amount_paid = total_paid
        self.balance_due = self.total_amount - total_paid
        
        # Update status
        if self.balance_due <= 0 and self.status == 'APPROVED':
            self.status = 'PAID'
            self.payment_date = timezone.now().date()
        
        self.save()
        
    # In models.py, Invoice model needs this save method:
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            year = timezone.now().year
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=f'INV-{year}'
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.invoice_number = f'INV-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.supplier.name}"


class InvoiceItem(models.Model):
    """Line items in invoice"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.CASCADE, related_name='invoice_items')
    
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        db_table = 'invoice_items'
        ordering = ['invoice', 'id']

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        self.tax_amount = self.total_price * (self.tax_rate / 100)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description[:50]}"


class InvoiceDocument(models.Model):
    """Invoice supporting documents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='documents')
    document_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='invoice_documents/')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoice_documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.document_name}"


class Payment(models.Model):
    """Payment records"""
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('EFT', 'Electronic Funds Transfer'),
        ('MOBILE_MONEY', 'Mobile Money'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_number = models.CharField(max_length=50, unique=True, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    
    payment_date = models.DateField()
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_reference = models.CharField(max_length=100)
    
    bank_name = models.CharField(max_length=200, blank=True)
    cheque_number = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payments_processed')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_approved')
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.payment_number:
            year = timezone.now().year
            last_payment = Payment.objects.filter(
                payment_number__startswith=f'PAY-{year}'
            ).order_by('-payment_number').first()
            
            if last_payment:
                last_number = int(last_payment.payment_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.payment_number = f'PAY-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.payment_number} - {self.payment_amount}"


# ============================================================================
# 13. REPORTING & ANALYTICS
# ============================================================================

class ProcurementReport(models.Model):
    """Generated reports storage"""
    REPORT_TYPES = [
        ('SPEND_ANALYSIS', 'Spend Analysis'),
        ('SUPPLIER_PERFORMANCE', 'Supplier Performance'),
        ('BUDGET_UTILIZATION', 'Budget Utilization'),
        ('COMPLIANCE', 'Compliance Report'),
        ('DEPARTMENTAL', 'Departmental Procurement'),
        ('INVENTORY', 'Inventory Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    
    parameters = models.JSONField()
    
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_reports'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.generated_at.strftime('%Y-%m-%d')}"


# ============================================================================
# 14. NOTIFICATIONS & COMMUNICATIONS
# ============================================================================

class Notification(models.Model):
    """System notifications"""
    NOTIFICATION_TYPES = [
        ('REQUISITION', 'Requisition'),
        ('APPROVAL', 'Approval'),
        ('TENDER', 'Tender'),
        ('PO', 'Purchase Order'),
        ('DELIVERY', 'Delivery'),
        ('INVOICE', 'Invoice'),
        ('PAYMENT', 'Payment'),
        ('CONTRACT', 'Contract'),
        ('ALERT', 'Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    
    title = models.CharField(max_length=300)
    message = models.TextField()
    
    link_url = models.CharField(max_length=500, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    sent_via_email = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class EmailLog(models.Model):
    """Email communication log"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.EmailField()
    subject = models.CharField(max_length=500)
    body = models.TextField()
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient} - {self.subject}"


# ============================================================================
# 15. SYSTEM CONFIGURATION
# ============================================================================

class SystemConfiguration(models.Model):
    """System-wide configuration settings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    data_type = models.CharField(max_length=20, choices=[
        ('STRING', 'String'),
        ('INTEGER', 'Integer'),
        ('DECIMAL', 'Decimal'),
        ('BOOLEAN', 'Boolean'),
        ('JSON', 'JSON'),
    ])
    description = models.TextField(blank=True)
    is_editable = models.BooleanField(default=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_configurations'
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"


class ProcurementPolicy(models.Model):
    """Procurement policies and guidelines"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    policy_number = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    content = models.TextField()
    
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    document = models.FileField(upload_to='policies/', null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_policies'
        verbose_name_plural = 'Procurement Policies'
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.policy_number} - {self.title}"