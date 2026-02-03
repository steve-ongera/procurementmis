from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from decimal import Decimal
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import  *


# ============================================================================
# 1. USER & ROLE MANAGEMENT
# ============================================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'get_full_name', 'role', 'department', 'employee_id', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'department', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('University Information', {
            'fields': ('role', 'employee_id', 'phone_number', 'department', 'profile_picture')
        }),
        ('Status', {
            'fields': ('is_active_user',)
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('University Information', {
            'fields': ('role', 'employee_id', 'phone_number', 'department', 'email')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Full Name'


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'module', 'created_at']
    list_filter = ['module', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['module', 'name']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['role', 'permission__name']
    ordering = ['role', 'permission']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'ip_address', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'object_repr', 'ip_address']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent', 'timestamp']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================================
# 2. ORGANIZATIONAL STRUCTURE
# ============================================================================

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'dean', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'dean__username']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'faculty', 'department_type', 'hod', 'is_active', 'created_at']
    list_filter = ['faculty', 'department_type', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'faculty__name']
    ordering = ['faculty', 'name']
    readonly_fields = ['created_at', 'updated_at']


# ============================================================================
# 3. BUDGET MANAGEMENT
# ============================================================================

@admin.register(BudgetYear)
class BudgetYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active', 'created_at']
    list_filter = ['is_active', 'start_date']
    search_fields = ['name']
    ordering = ['-start_date']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['code']
    readonly_fields = ['created_at']



from decimal import Decimal
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import SafeString

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):

    list_display = (
        'department',
        'category',
        'budget_year',
        'budget_type',
        'formatted_allocated_amount',
        'formatted_committed_amount',
        'formatted_actual_spent',
        'formatted_available_balance',
        'is_active',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Budget Information', {
            'fields': (
                'budget_year',
                'department',
                'category',
                'budget_type',
                'reference_number',
            )
        }),
        ('Financial Details', {
            'fields': (
                'allocated_amount',
                'committed_amount',
                'actual_spent',
            )
        }),
        ('Additional Information', {
            'fields': (
                'description',
                'is_active',
                'created_by',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    # ========= LIST VIEW FORMATTERS =========

    @admin.display(description='Allocated Amount')
    def formatted_allocated_amount(self, obj):
        return self._format_money(obj.allocated_amount)

    @admin.display(description='Committed Amount')
    def formatted_committed_amount(self, obj):
        return self._format_money(obj.committed_amount)

    @admin.display(description='Actual Spent')
    def formatted_actual_spent(self, obj):
        return self._format_money(obj.actual_spent)

    @admin.display(description='Available Balance')
    def formatted_available_balance(self, obj):
        balance = obj.available_balance
        color = 'green' if balance > 0 else 'red'
        return self._format_money(balance, color=color)

    # ========= SAFE FORMATTER =========

    def _format_money(self, value, color=None):
        if isinstance(value, SafeString):
            return value
        
        try:
            # Ensure we have a Decimal
            if value is None:
                value = Decimal('0')
            elif not isinstance(value, Decimal):
                value = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            value = Decimal('0')
        
        # Format as string first, then pass to format_html
        formatted_value = format(value, ',.2f')
        
        if color:
            return format_html(
                '<span style="color:{}; font-weight:600;">{}</span>',
                color,
                formatted_value
            )
        
        return format_html('{}', formatted_value)



@admin.register(BudgetReallocation)
class BudgetReallocationAdmin(admin.ModelAdmin):
    list_display = ['from_budget', 'to_budget', 'amount', 'status', 'requested_by', 'approved_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['from_budget__department__name', 'to_budget__department__name', 'justification']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


# ============================================================================
# 4. ITEM CATALOG
# ============================================================================

@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category_type', 'parent', 'is_active', 'created_at']
    list_filter = ['category_type', 'is_active', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['code']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'unit_of_measure', 'standard_price', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['code']
    readonly_fields = ['created_at', 'updated_at']


# ============================================================================
# 5. SUPPLIER MANAGEMENT
# ============================================================================

class SupplierDocumentInline(admin.TabularInline):
    model = SupplierDocument
    extra = 0
    readonly_fields = ['uploaded_at']


class SupplierPerformanceInline(admin.TabularInline):
    model = SupplierPerformance
    extra = 0
    readonly_fields = ['overall_rating', 'reviewed_at']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['supplier_number', 'user', 'name', 'email', 'phone_number', 'status', 'rating', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'supplier_number', 'email', 'registration_number']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SupplierDocumentInline, SupplierPerformanceInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user','supplier_number', 'name', 'registration_number', 'tax_id')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'physical_address', 'postal_address', 'website',
                      'contact_person', 'contact_person_phone', 'contact_person_email')
        }),
        ('Banking Details', {
            'fields': ('bank_name', 'bank_branch', 'account_number', 'account_name', 'swift_code')
        }),
        ('Categories & Status', {
            'fields': ('categories', 'status', 'rating')
        }),
        ('Compliance', {
            'fields': ('tax_compliance_expiry', 'registration_expiry')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['categories']


@admin.register(SupplierDocument)
class SupplierDocumentAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'document_type', 'document_name', 'is_verified', 'expiry_date', 'uploaded_at']
    list_filter = ['document_type', 'is_verified', 'uploaded_at']
    search_fields = ['supplier__name', 'document_name']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at', 'verified_at']


@admin.register(SupplierPerformance)
class SupplierPerformanceAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'purchase_order', 'quality_rating', 'delivery_rating', 'service_rating', 'overall_rating', 'reviewed_at']
    list_filter = ['reviewed_at']
    search_fields = ['supplier__name', 'purchase_order__po_number']
    ordering = ['-reviewed_at']
    readonly_fields = ['overall_rating', 'reviewed_at']


# ============================================================================
# 6. REQUISITION MANAGEMENT
# ============================================================================

class RequisitionItemInline(admin.TabularInline):
    model = RequisitionItem
    extra = 1
    readonly_fields = ['estimated_total']


class RequisitionAttachmentInline(admin.TabularInline):
    model = RequisitionAttachment
    extra = 0
    readonly_fields = ['uploaded_at']


# ============================================================================
# UPDATE REQUISITION ADMIN (Modify existing RequisitionAdmin)
# ============================================================================

# Replace the existing RequisitionAdmin fieldsets with this updated version:
@admin.register(Requisition)
class RequisitionAdmin(admin.ModelAdmin):
    list_display = [
        'requisition_number', 'title', 'department', 'requested_by',
        'status', 'priority', 'estimated_amount', 'required_date',
        'is_planned', 'is_emergency', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'is_emergency', 'is_planned',
        'department', 'created_at', 'hod_emergency_approval'
    ]
    search_fields = [
        'requisition_number', 'title', 'requested_by__username',
        'justification', 'emergency_justification'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'requisition_number', 'created_at', 'updated_at',
        'submitted_at', 'plan_deviation_approved_at'
    ]
    inlines = [RequisitionItemInline, RequisitionAttachmentInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Requisition Information', {
            'fields': (
                'requisition_number', 'title', 'department',
                'budget', 'requested_by'
            )
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Details', {
            'fields': (
                'justification', 'estimated_amount', 'required_date'
            )
        }),
        ('Procurement Plan', {
            'fields': (
                'is_planned', 'procurement_plan_item',
                'requires_plan_amendment', 'plan_amendment'
            )
        }),
        ('Emergency/Unplanned Procurement', {
            'fields': (
                'is_emergency', 'emergency_type', 'emergency_justification',
                'hod_emergency_approval', 'plan_deviation_approved_by',
                'plan_deviation_approved_at'
            ),
            'classes': ('collapse',)
        }),
        ('Notes & Rejection', {
            'fields': ('notes', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_requisitions', 'reject_requisitions', 'approve_emergency']
    
    def approve_requisitions(self, request, queryset):
        updated = queryset.update(status='APPROVED')
        self.message_user(request, f'{updated} requisition(s) approved successfully.')
    approve_requisitions.short_description = 'Approve selected requisitions'
    
    def reject_requisitions(self, request, queryset):
        updated = queryset.update(status='REJECTED')
        self.message_user(request, f'{updated} requisition(s) rejected.')
    reject_requisitions.short_description = 'Reject selected requisitions'
    
    def approve_emergency(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_emergency=True).update(
            hod_emergency_approval=True,
            plan_deviation_approved_by=request.user,
            plan_deviation_approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} emergency requisition(s) approved.')
    approve_emergency.short_description = 'Approve emergency procurement'
    
    
@admin.register(RequisitionItem)
class RequisitionItemAdmin(admin.ModelAdmin):
    list_display = ['requisition', 'item_description', 'quantity', 'unit_of_measure', 'estimated_unit_price', 'estimated_total']
    list_filter = ['created_at']
    search_fields = ['requisition__requisition_number', 'item_description']
    ordering = ['-created_at']
    readonly_fields = ['estimated_total', 'created_at']


@admin.register(RequisitionAttachment)
class RequisitionAttachmentAdmin(admin.ModelAdmin):
    list_display = ['requisition', 'attachment_type', 'file_name', 'uploaded_by', 'uploaded_at']
    list_filter = ['attachment_type', 'uploaded_at']
    search_fields = ['requisition__requisition_number', 'file_name']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at']


# ============================================================================
# 7. APPROVAL WORKFLOW
# ============================================================================

@admin.register(ApprovalThreshold)
class ApprovalThresholdAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_amount', 'max_amount', 'requires_hod_approval', 'requires_faculty_approval', 
                   'requires_procurement_approval', 'requires_finance_approval', 'requires_tender', 'is_active']
    list_filter = ['is_active', 'requires_tender']
    search_fields = ['name']
    ordering = ['min_amount']


@admin.register(RequisitionApproval)
class RequisitionApprovalAdmin(admin.ModelAdmin):
    list_display = ['requisition', 'approval_stage', 'approver', 'status', 'approval_date', 'sequence']
    list_filter = ['approval_stage', 'status', 'approval_date']
    search_fields = ['requisition__requisition_number', 'approver__username']
    ordering = ['requisition', 'sequence']
    readonly_fields = ['created_at']


# ============================================================================
# 8. TENDERING & QUOTATIONS
# ============================================================================

class TenderDocumentInline(admin.TabularInline):
    model = TenderDocument
    extra = 0
    readonly_fields = ['uploaded_at']


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    readonly_fields = ['bid_number', 'submitted_at']
    fields = ['supplier', 'bid_amount', 'status', 'rank']


@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = [
        'tender_number', 'title', 'tender_type',
        'procurement_method', 'status', 'closing_date',
        'estimated_budget',
        'technical_evaluation_complete',
        'financial_evaluation_complete',
        'created_at'
    ]
    list_filter = [
        'tender_type', 'procurement_method', 'status',
        'requires_technical_evaluation',
        'technical_evaluation_complete',
        'financial_evaluation_complete',
        'created_at'
    ]
    search_fields = [
        'tender_number', 'title', 'requisition__requisition_number'
    ]
    ordering = ['-created_at']
    readonly_fields = ['tender_number', 'created_at', 'updated_at']
    inlines = [TenderDocumentInline, BidInline]
    filter_horizontal = ['invited_suppliers']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Tender Information', {
            'fields': (
                'tender_number', 'requisition', 'title',
                'tender_type', 'procurement_method'
            )
        }),
        ('Description & Dates', {
            'fields': (
                'description', 'publish_date', 'closing_date',
                'bid_opening_date'
            )
        }),
        ('Budget & Status', {
            'fields': ('estimated_budget', 'status')
        }),
        ('Evaluation Settings', {
            'fields': (
                'requires_technical_evaluation', 'technical_pass_mark',
                'evaluation_start_date', 'evaluation_end_date'
            )
        }),
        ('Evaluation Status', {
            'fields': (
                'preliminary_evaluation_complete',
                'technical_evaluation_complete',
                'financial_evaluation_complete'
            )
        }),
        ('Award Information', {
            'fields': (
                'award_recommendation_date', 'award_approved_date'
            ),
            'classes': ('collapse',)
        }),
        ('Suppliers', {
            'fields': ('invited_suppliers',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BidDocument)
class BidDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'bid', 'document_type', 'document_name',
        'uploaded_at'
    ]
    list_filter = ['document_type', 'uploaded_at']
    search_fields = [
        'bid__bid_number', 'document_name', 'description'
    ]
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('bid', 'document_type', 'document_name')
        }),
        ('File & Description', {
            'fields': ('file', 'description')
        }),
        ('Metadata', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(TenderDocument)
class TenderDocumentAdmin(admin.ModelAdmin):
    list_display = ['tender', 'document_name', 'is_mandatory', 'uploaded_at']
    list_filter = ['is_mandatory', 'uploaded_at']
    search_fields = ['tender__tender_number', 'document_name']
    ordering = ['-uploaded_at']


class BidItemInline(admin.TabularInline):
    model = BidItem
    extra = 0
    readonly_fields = ['quoted_total']


class BidDocumentInline(admin.TabularInline):
    model = BidDocument
    extra = 0
    readonly_fields = ['uploaded_at']


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = [
        'bid_number', 'tender', 'supplier', 'bid_amount',
        'status', 'evaluation_score', 'rank',
        'technical_evaluation_status', 'financial_evaluation_status',
        'is_lowest_evaluated', 'submitted_at'
    ]
    list_filter = [
        'status', 'preliminary_evaluation_status',
        'technical_evaluation_status', 'financial_evaluation_status',
        'is_lowest_evaluated', 'submitted_at', 'opened_at'
    ]
    search_fields = [
        'bid_number', 'tender__tender_number', 'supplier__name'
    ]
    ordering = ['tender', 'rank']
    readonly_fields = [
        'bid_number', 'submitted_at', 'opened_at'
    ]
    inlines = [BidItemInline, BidDocumentInline]
    
    fieldsets = (
        ('Bid Information', {
            'fields': ('bid_number', 'tender', 'supplier')
        }),
        ('Bid Details', {
            'fields': (
                'bid_amount', 'bid_bond_amount',
                'validity_period_days', 'delivery_period_days'
            )
        }),
        ('Preliminary Evaluation', {
            'fields': (
                'preliminary_evaluation_status',
                'preliminary_evaluation_notes'
            )
        }),
        ('Technical Evaluation', {
            'fields': (
                'technical_evaluation_status', 'technical_score'
            )
        }),
        ('Financial Evaluation', {
            'fields': (
                'financial_evaluation_status', 'financial_score',
                'is_lowest_evaluated', 'price_variance_percentage'
            )
        }),
        ('Overall Evaluation', {
            'fields': ('status', 'evaluation_score', 'rank')
        }),
        ('Disqualification', {
            'fields': ('disqualification_reason',),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'opened_at', 'opened_by'),
            'classes': ('collapse',)
        }),
    )




@admin.register(BidItem)
class BidItemAdmin(admin.ModelAdmin):
    list_display = ['bid', 'requisition_item', 'quoted_unit_price', 'quoted_total', 'brand', 'delivery_period_days']
    search_fields = ['bid__bid_number', 'brand', 'model']
    readonly_fields = ['quoted_total']


@admin.register(BidEvaluation)
class BidEvaluationAdmin(admin.ModelAdmin):
    list_display = ['bid', 'evaluator', 'technical_score', 'financial_score', 'total_score', 'evaluated_at']
    list_filter = ['evaluated_at']
    search_fields = ['bid__bid_number', 'evaluator__username']
    ordering = ['-evaluated_at']
    readonly_fields = ['total_score', 'evaluated_at']


@admin.register(EvaluationCriteria)
class EvaluationCriteriaAdmin(admin.ModelAdmin):
    list_display = ['tender', 'criterion_name', 'criterion_type', 'weight', 'max_score', 'is_mandatory', 'sequence']
    list_filter = ['criterion_type', 'is_mandatory']
    search_fields = ['tender__tender_number', 'criterion_name']
    ordering = ['tender', 'sequence']


# ============================================================================
# EVALUATION COMMITTEE MANAGEMENT (NEW SECTION)
# ============================================================================

class CommitteeMemberInline(admin.TabularInline):
    model = CommitteeMember
    extra = 1
    readonly_fields = ['appointed_at']
    fields = [
        'user', 'role', 'department', 'expertise_area',
        'has_conflict', 'conflict_details', 'is_active'
    ]


@admin.register(EvaluationCommittee)
class EvaluationCommitteeAdmin(admin.ModelAdmin):
    list_display = [
        'committee_number', 'tender', 'committee_type',
        'chairperson', 'secretary', 'status',
        'appointment_date', 'completion_date', 'created_at'
    ]
    list_filter = [
        'committee_type', 'status', 'appointment_date',
        'completion_date', 'created_at'
    ]
    search_fields = [
        'committee_number', 'name', 'tender__tender_number',
        'chairperson__username', 'secretary__username'
    ]
    ordering = ['-created_at']
    readonly_fields = ['committee_number', 'created_at', 'updated_at']
    inlines = [CommitteeMemberInline]
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Committee Information', {
            'fields': (
                'committee_number', 'tender', 'committee_type', 'name'
            )
        }),
        ('Leadership', {
            'fields': ('chairperson', 'secretary')
        }),
        ('Dates & Status', {
            'fields': (
                'appointment_date', 'completion_date', 'status'
            )
        }),
        ('Terms of Reference', {
            'fields': ('terms_of_reference', 'evaluation_guidelines')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['complete_committees', 'suspend_committees']
    
    def complete_committees(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='ACTIVE').update(
            status='COMPLETED',
            completion_date=timezone.now().date()
        )
        self.message_user(request, f'{updated} committee(s) marked as completed.')
    complete_committees.short_description = 'Mark committees as completed'
    
    def suspend_committees(self, request, queryset):
        updated = queryset.update(status='SUSPENDED')
        self.message_user(request, f'{updated} committee(s) suspended.')
    suspend_committees.short_description = 'Suspend selected committees'


@admin.register(CommitteeMember)
class CommitteeMemberAdmin(admin.ModelAdmin):
    list_display = [
        'committee', 'user', 'role', 'department',
        'expertise_area', 'has_conflict', 'is_active', 'appointed_at'
    ]
    list_filter = [
        'role', 'has_conflict', 'is_active',
        'appointed_at', 'committee__status'
    ]
    search_fields = [
        'committee__committee_number', 'user__username',
        'user__first_name', 'user__last_name', 'expertise_area'
    ]
    ordering = ['committee', 'role', 'user']
    readonly_fields = ['appointed_at']
    
    fieldsets = (
        ('Committee Assignment', {
            'fields': ('committee', 'user', 'role')
        }),
        ('Details', {
            'fields': ('department', 'expertise_area')
        }),
        ('Conflict of Interest', {
            'fields': ('has_conflict', 'conflict_details')
        }),
        ('Status', {
            'fields': ('is_active', 'appointed_at')
        }),
    )


# ============================================================================
# TECHNICAL EVALUATION CRITERIA
# ============================================================================

class TechnicalEvaluationScoreInline(admin.TabularInline):
    model = TechnicalEvaluationScore
    extra = 0
    readonly_fields = ['weighted_score', 'evaluated_at']
    fields = [
        'bid', 'evaluator', 'score', 'weighted_score',
        'is_compliant', 'comments'
    ]


@admin.register(TechnicalEvaluationCriteria)
class TechnicalEvaluationCriteriaAdmin(admin.ModelAdmin):
    list_display = [
        'tender', 'criterion_name', 'sequence',
        'max_score', 'weight_percentage',
        'is_mandatory', 'is_pass_fail', 'response_type', 'created_at'
    ]
    list_filter = [
        'is_mandatory', 'is_pass_fail', 'response_type', 'created_at'
    ]
    search_fields = [
        'tender__tender_number', 'criterion_name',
        'description', 'minimum_specification'
    ]
    ordering = ['tender', 'sequence']
    readonly_fields = ['created_at']
    inlines = [TechnicalEvaluationScoreInline]
    
    fieldsets = (
        ('Criterion Information', {
            'fields': (
                'tender', 'criterion_name', 'description',
                'minimum_specification', 'sequence'
            )
        }),
        ('Response Type', {
            'fields': ('response_type',)
        }),
        ('Scoring', {
            'fields': (
                'max_score', 'weight_percentage',
                'scoring_guidelines'
            )
        }),
        ('Requirements', {
            'fields': ('is_mandatory', 'is_pass_fail')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(BidTechnicalResponse)
class BidTechnicalResponseAdmin(admin.ModelAdmin):
    list_display = [
        'bid', 'criterion', 'compliance_status',
        'response_value', 'has_document', 'created_at'
    ]
    list_filter = [
        'compliance_status', 'created_at', 'updated_at'
    ]
    search_fields = [
        'bid__bid_number', 'criterion__criterion_name',
        'response_text', 'response_value'
    ]
    ordering = ['bid', 'criterion__sequence']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Response Information', {
            'fields': ('bid', 'criterion')
        }),
        ('Supplier Response', {
            'fields': (
                'response_text', 'response_value',
                'supporting_document', 'supplier_remarks'
            )
        }),
        ('Evaluation', {
            'fields': ('compliance_status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_document(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.supporting_document else 'red',
            '✓' if obj.supporting_document else '✗'
        )
    has_document.short_description = 'Document'


@admin.register(TechnicalEvaluationScore)
class TechnicalEvaluationScoreAdmin(admin.ModelAdmin):
    list_display = [
        'bid', 'criterion', 'evaluator',
        'score', 'weighted_score', 'is_compliant', 'evaluated_at'
    ]
    list_filter = [
        'is_compliant', 'evaluated_at', 'evaluator'
    ]
    search_fields = [
        'bid__bid_number', 'criterion__criterion_name',
        'evaluator__username', 'comments', 'justification'
    ]
    ordering = ['bid', 'criterion__sequence', 'evaluator']
    readonly_fields = ['weighted_score', 'evaluated_at']
    
    fieldsets = (
        ('Score Information', {
            'fields': ('bid', 'criterion', 'evaluator')
        }),
        ('Scoring', {
            'fields': ('score', 'weighted_score', 'is_compliant')
        }),
        ('Evaluation Notes', {
            'fields': ('comments', 'justification')
        }),
        ('Timestamp', {
            'fields': ('evaluated_at',),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# FINANCIAL EVALUATION CRITERIA
# ============================================================================

@admin.register(FinancialEvaluationCriteria)
class FinancialEvaluationCriteriaAdmin(admin.ModelAdmin):
    list_display = [
        'tender', 'evaluation_method',
        'technical_weight', 'financial_weight',
        'acceptable_variance_percentage',
        'uses_formula', 'check_price_reasonability', 'created_at'
    ]
    list_filter = [
        'evaluation_method', 'uses_formula',
        'check_price_reasonability', 'created_at'
    ]
    search_fields = [
        'tender__tender_number', 'formula_description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Tender Reference', {
            'fields': ('tender',)
        }),
        ('Evaluation Method', {
            'fields': ('evaluation_method',)
        }),
        ('Weighting', {
            'fields': ('technical_weight', 'financial_weight')
        }),
        ('Formula', {
            'fields': ('uses_formula', 'formula_description')
        }),
        ('Price Reasonability', {
            'fields': (
                'check_price_reasonability',
                'acceptable_variance_percentage'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FinancialEvaluationScore)
class FinancialEvaluationScoreAdmin(admin.ModelAdmin):
    list_display = [
        'bid', 'evaluator', 'quoted_amount',
        'financial_score', 'weighted_financial_score',
        'is_arithmetic_correct', 'is_within_budget',
        'is_price_reasonable', 'evaluated_at'
    ]
    list_filter = [
        'is_arithmetic_correct', 'is_within_budget',
        'is_price_reasonable', 'evaluated_at', 'evaluator'
    ]
    search_fields = [
        'bid__bid_number', 'evaluator__username',
        'comments', 'arithmetic_notes'
    ]
    ordering = ['bid', 'financial_score']
    readonly_fields = ['weighted_financial_score', 'evaluated_at']
    
    fieldsets = (
        ('Evaluation Information', {
            'fields': ('bid', 'evaluator')
        }),
        ('Price Analysis', {
            'fields': (
                'quoted_amount', 'variance_from_estimate',
                'is_within_budget', 'is_price_reasonable'
            )
        }),
        ('Arithmetic Verification', {
            'fields': ('is_arithmetic_correct', 'arithmetic_notes')
        }),
        ('Scoring', {
            'fields': ('financial_score', 'weighted_financial_score')
        }),
        ('Comments', {
            'fields': ('comments',)
        }),
        ('Timestamp', {
            'fields': ('evaluated_at',),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# COMBINED EVALUATION RESULTS
# ============================================================================

@admin.register(CombinedEvaluationResult)
class CombinedEvaluationResultAdmin(admin.ModelAdmin):
    list_display = [
        'bid', 'combined_score', 'final_rank',
        'average_technical_score', 'average_financial_score',
        'is_technically_qualified', 'is_recommended',
        'is_disqualified', 'evaluation_date'
    ]
    list_filter = [
        'is_technically_qualified', 'is_recommended',
        'is_disqualified', 'evaluation_date', 'created_at'
    ]
    search_fields = [
        'bid__bid_number', 'bid__supplier__name',
        'recommendation_notes', 'disqualification_reason'
    ]
    ordering = ['bid__tender', '-combined_score']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Bid Reference', {
            'fields': ('bid', 'evaluated_by_committee')
        }),
        ('Technical Evaluation', {
            'fields': (
                'average_technical_score', 'technical_percentage',
                'is_technically_qualified', 'technical_pass_mark'
            )
        }),
        ('Financial Evaluation', {
            'fields': (
                'average_financial_score', 'financial_percentage'
            )
        }),
        ('Combined Results', {
            'fields': ('combined_score', 'final_rank')
        }),
        ('Recommendation', {
            'fields': (
                'is_recommended', 'recommendation_notes'
            )
        }),
        ('Disqualification', {
            'fields': (
                'is_disqualified', 'disqualification_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('evaluation_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['recalculate_scores']
    
    def recalculate_scores(self, request, queryset):
        count = 0
        for result in queryset:
            result.calculate_combined_score()
            count += 1
        self.message_user(
            request,
            f'Combined scores recalculated for {count} result(s).'
        )
    recalculate_scores.short_description = 'Recalculate combined scores'


# ============================================================================
# EVALUATION REPORTS
# ============================================================================

@admin.register(EvaluationReport)
class EvaluationReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_number', 'tender', 'report_type',
        'status', 'recommended_bidder',
        'submitted_by', 'submitted_at',
        'approved_by', 'approved_at', 'created_at'
    ]
    list_filter = [
        'report_type', 'status', 'submitted_at',
        'approved_at', 'created_at'
    ]
    search_fields = [
        'report_number', 'title', 'tender__tender_number',
        'executive_summary', 'findings', 'recommendations'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'report_number', 'created_at', 'updated_at',
        'submitted_at', 'approved_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': (
                'report_number', 'tender', 'committee',
                'report_type', 'title'
            )
        }),
        ('Report Content', {
            'fields': (
                'executive_summary', 'methodology',
                'findings', 'recommendations'
            )
        }),
        ('Recommendation', {
            'fields': ('recommended_bidder',)
        }),
        ('Status & Document', {
            'fields': ('status', 'report_document')
        }),
        ('Submission', {
            'fields': ('submitted_by', 'submitted_at')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reports', 'submit_reports']
    
    def submit_reports(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='DRAFT').update(
            status='SUBMITTED',
            submitted_by=request.user,
            submitted_at=timezone.now()
        )
        self.message_user(request, f'{updated} report(s) submitted successfully.')
    submit_reports.short_description = 'Submit selected reports'
    
    def approve_reports(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='SUBMITTED').update(
            status='APPROVED',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} report(s) approved successfully.')
    approve_reports.short_description = 'Approve selected reports'

# ============================================================================
# 9. PURCHASE ORDERS
# ============================================================================

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    readonly_fields = ['total_price', 'quantity_pending']


class POAmendmentInline(admin.TabularInline):
    model = POAmendment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'supplier', 'requisition', 'po_date', 'delivery_date', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'po_date', 'created_at']
    search_fields = ['po_number', 'supplier__name', 'requisition__requisition_number']
    ordering = ['-created_at']
    readonly_fields = ['po_number', 'po_date', 'created_at', 'updated_at', 'sent_at', 'acknowledged_at']
    inlines = [PurchaseOrderItemInline, POAmendmentInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('PO Information', {
            'fields': ('po_number', 'requisition', 'supplier', 'bid')
        }),
        ('Dates & Delivery', {
            'fields': ('po_date', 'delivery_date', 'delivery_address')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_amount', 'total_amount')
        }),
        ('Terms & Instructions', {
            'fields': ('payment_terms', 'warranty_terms', 'special_instructions')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
        ('Communication', {
            'fields': ('sent_at', 'acknowledged_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'item_description', 'quantity', 'unit_price', 'total_price', 'quantity_delivered', 'quantity_pending']
    search_fields = ['purchase_order__po_number', 'item_description']
    readonly_fields = ['total_price', 'quantity_pending']


@admin.register(POAmendment)
class POAmendmentAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'amendment_number', 'amendment_type', 'amount_change', 'requested_by', 'approved_by', 'created_at']
    list_filter = ['amendment_type', 'created_at']
    search_fields = ['purchase_order__po_number', 'amendment_number']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


# ============================================================================
# 10. CONTRACT MANAGEMENT
# ============================================================================

class ContractDocumentInline(admin.TabularInline):
    model = ContractDocument
    extra = 0
    readonly_fields = ['uploaded_at']


class ContractMilestoneInline(admin.TabularInline):
    model = ContractMilestone
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['contract_number', 'title', 'supplier', 'contract_type', 'contract_value', 'start_date', 'end_date', 'status', 'contract_manager']
    list_filter = ['contract_type', 'status', 'start_date', 'created_at']
    search_fields = ['contract_number', 'title', 'supplier__name']
    ordering = ['-created_at']
    readonly_fields = ['contract_number', 'created_at', 'updated_at']
    inlines = [ContractDocumentInline, ContractMilestoneInline]
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Contract Information', {
            'fields': ('contract_number', 'purchase_order', 'supplier', 'title', 'contract_type')
        }),
        ('Description & Value', {
            'fields': ('description', 'contract_value')
        }),
        ('Dates & Renewal', {
            'fields': ('start_date', 'end_date', 'renewal_option', 'renewal_period_months')
        }),
        ('Status & Management', {
            'fields': ('status', 'contract_manager')
        }),
        ('Payment & Bond', {
            'fields': ('payment_schedule', 'performance_bond_required', 'performance_bond_amount')
        }),
        ('Terms & Conditions', {
            'fields': ('special_conditions', 'termination_clause'),
            'classes': ('collapse',)
        }),
        ('Signatures', {
            'fields': ('signed_by_supplier', 'signed_by_university', 'signing_date')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContractDocument)
class ContractDocumentAdmin(admin.ModelAdmin):
    list_display = ['contract', 'document_type', 'document_name', 'version', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['contract__contract_number', 'document_name']
    ordering = ['-uploaded_at']


@admin.register(ContractMilestone)
class ContractMilestoneAdmin(admin.ModelAdmin):
    list_display = ['contract', 'milestone_name', 'due_date', 'completion_date', 'milestone_value', 'payment_percentage', 'status', 'sequence']
    list_filter = ['status', 'due_date']
    search_fields = ['contract__contract_number', 'milestone_name']
    ordering = ['contract', 'sequence']


@admin.register(ContractVariation)
class ContractVariationAdmin(admin.ModelAdmin):
    list_display = ['contract', 'variation_number', 'title', 'value_change', 'time_extension_days', 'status', 'requested_by', 'approved_by']
    list_filter = ['status', 'created_at']
    search_fields = ['contract__contract_number', 'variation_number', 'title']
    ordering = ['-created_at']


# ============================================================================
# 11. STORES & INVENTORY
# ============================================================================

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'store_type', 'department', 'store_keeper', 'is_active', 'created_at']
    list_filter = ['store_type', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'location']
    ordering = ['name']


class GRNItemInline(admin.TabularInline):
    model = GRNItem
    extra = 0


@admin.register(GoodsReceivedNote)
class GoodsReceivedNoteAdmin(admin.ModelAdmin):
    list_display = ['grn_number', 'purchase_order', 'store', 'delivery_date', 'received_date', 'status', 'received_by', 'inspected_by']
    list_filter = ['status', 'received_date', 'inspection_date']
    search_fields = ['grn_number', 'purchase_order__po_number', 'delivery_note_number']
    ordering = ['-created_at']
    readonly_fields = ['grn_number', 'created_at', 'updated_at']
    inlines = [GRNItemInline]
    date_hierarchy = 'received_date'


@admin.register(GRNItem)
class GRNItemAdmin(admin.ModelAdmin):
    list_display = ['grn', 'po_item', 'quantity_ordered', 'quantity_delivered', 'quantity_accepted', 'quantity_rejected', 'item_status']
    list_filter = ['item_status']
    search_fields = ['grn__grn_number']


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ['store', 'item', 'quantity_on_hand', 'reorder_level', 'average_unit_cost', 'total_value', 'last_restock_date', 'last_issue_date']
    list_filter = ['store', 'last_restock_date']
    search_fields = ['store__name', 'item__name']
    ordering = ['store', 'item']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['stock_item', 'movement_type', 'reference_number', 'quantity', 'balance_before', 'balance_after', 'performed_by', 'movement_date']
    list_filter = ['movement_type', 'movement_date']
    search_fields = ['stock_item__item__name', 'reference_number']
    ordering = ['-movement_date']
    readonly_fields = ['movement_date']
    date_hierarchy = 'movement_date'


class StockIssueItemInline(admin.TabularInline):
    model = StockIssueItem
    extra = 0


@admin.register(StockIssue)
class StockIssueAdmin(admin.ModelAdmin):
    list_display = ['issue_number', 'store', 'department', 'requested_by', 'issued_by', 'issue_date', 'status', 'created_at']
    list_filter = ['status', 'issue_date', 'created_at']
    search_fields = ['issue_number', 'department__name', 'requested_by__username']
    ordering = ['-created_at']
    readonly_fields = ['issue_number', 'created_at']
    inlines = [StockIssueItemInline]


@admin.register(StockIssueItem)
class StockIssueItemAdmin(admin.ModelAdmin):
    list_display = ['stock_issue', 'stock_item', 'quantity_requested', 'quantity_issued']
    search_fields = ['stock_issue__issue_number', 'stock_item__item__name']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_number', 'asset_tag', 'description', 'department', 'custodian', 'status', 'acquisition_date', 'acquisition_cost', 'current_value']
    list_filter = ['status', 'acquisition_date', 'department']
    search_fields = ['asset_number', 'asset_tag', 'description', 'serial_number']
    ordering = ['asset_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Asset Identification', {
            'fields': ('asset_number', 'asset_tag', 'grn', 'item')
        }),
        ('Description', {
            'fields': ('description', 'serial_number', 'model', 'brand')
        }),
        ('Financial Details', {
            'fields': ('acquisition_date', 'acquisition_cost', 'current_value', 'depreciation_rate', 'useful_life_years')
        }),
        ('Location & Custodian', {
            'fields': ('department', 'location', 'custodian')
        }),
        ('Status', {
            'fields': ('status', 'warranty_expiry')
        }),
        ('Disposal Information', {
            'fields': ('disposal_date', 'disposal_method', 'disposal_value'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# 12. INVOICE & PAYMENT PROCESSING
# ============================================================================

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ['total_price', 'tax_amount']


class InvoiceDocumentInline(admin.TabularInline):
    model = InvoiceDocument
    extra = 0
    readonly_fields = ['uploaded_at']


# Update the InvoiceAdmin list_display to include new payment tracking fields:
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'supplier_invoice_number', 'supplier',
        'purchase_order', 'invoice_date', 'due_date',
        'total_amount', 'amount_paid', 'balance_due',
        'status', 'is_three_way_matched', 'created_at'
    ]
    list_filter = [
        'status', 'is_three_way_matched', 'invoice_date',
        'due_date', 'created_at'
    ]
    search_fields = [
        'invoice_number', 'supplier_invoice_number',
        'supplier__name', 'purchase_order__po_number'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'created_at', 'updated_at', 'verified_at',
        'approved_at', 'amount_paid', 'balance_due'
    ]
    inlines = [InvoiceItemInline, InvoiceDocumentInline]
    date_hierarchy = 'invoice_date'
    
    fieldsets = (
        ('Invoice Information', {
            'fields': (
                'invoice_number', 'supplier_invoice_number',
                'purchase_order', 'grn', 'supplier'
            )
        }),
        ('Dates', {
            'fields': ('invoice_date', 'due_date')
        }),
        ('Financial Details', {
            'fields': (
                'subtotal', 'tax_amount', 'other_charges',
                'total_amount', 'amount_paid', 'balance_due'
            )
        }),
        ('Status & Matching', {
            'fields': ('status', 'is_three_way_matched', 'matching_notes')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Payment', {
            'fields': ('payment_reference', 'payment_date')
        }),
        ('Additional Information', {
            'fields': ('dispute_reason', 'notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('submitted_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_paid(self, obj):
        return format_html(
            '<span style="color: green; font-weight: 600;">{:,.2f}</span>',
            obj.amount_paid
        )
    amount_paid.short_description = 'Amount Paid'
    
    def balance_due(self, obj):
        color = 'red' if obj.balance_due > 0 else 'green'
        return format_html(
            '<span style="color: {}; font-weight: 600;">{:,.2f}</span>',
            color,
            obj.balance_due
        )
    balance_due.short_description = 'Balance Due'


# ============================================================================
# ADDITIONAL UTILITY METHODS
# ============================================================================

# Add this method to help with payment status updates
def update_invoice_payment_status(modeladmin, request, queryset):
    """Update payment status for selected invoices"""
    count = 0
    for invoice in queryset:
        invoice.update_payment_status()
        count += 1
    modeladmin.message_user(
        request,
        f'Payment status updated for {count} invoice(s).'
    )
update_invoice_payment_status.short_description = 'Update payment status'


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'po_item', 'description', 'quantity', 'unit_price', 'total_price', 'tax_rate', 'tax_amount']
    search_fields = ['invoice__invoice_number', 'description']
    readonly_fields = ['total_price', 'tax_amount']


@admin.register(InvoiceDocument)
class InvoiceDocumentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'document_name', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['invoice__invoice_number', 'document_name']
    ordering = ['-uploaded_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'invoice', 'payment_date', 'payment_amount', 'payment_method', 
                   'payment_reference', 'status', 'processed_by', 'approved_by']
    list_filter = ['status', 'payment_method', 'payment_date', 'created_at']
    search_fields = ['payment_number', 'invoice__invoice_number', 'payment_reference']
    ordering = ['-created_at']
    readonly_fields = ['payment_number', 'created_at', 'updated_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_number', 'invoice', 'payment_date', 'payment_amount')
        }),
        ('Payment Method', {
            'fields': ('payment_method', 'payment_reference', 'bank_name', 'cheque_number')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Approval', {
            'fields': ('processed_by', 'approved_by')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# 13. REPORTING & ANALYTICS
# ============================================================================

@admin.register(ProcurementReport)
class ProcurementReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'generated_by', 'generated_at']
    list_filter = ['report_type', 'generated_at']
    search_fields = ['title', 'description']
    ordering = ['-generated_at']
    readonly_fields = ['generated_at']
    
    def has_add_permission(self, request):
        return False


# ============================================================================
# 14. NOTIFICATIONS & COMMUNICATIONS
# ============================================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'priority', 'title', 'is_read', 'sent_via_email', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'sent_via_email', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'read_at', 'email_sent_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Recipient', {
            'fields': ('user',)
        }),
        ('Notification Details', {
            'fields': ('notification_type', 'priority', 'title', 'message', 'link_url')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'sent_via_email', 'email_sent_at')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'subject', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'sent_at', 'created_at']
    search_fields = ['recipient', 'subject']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'sent_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False


# ============================================================================
# 15. SYSTEM CONFIGURATION
# ============================================================================

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'data_type', 'is_editable', 'updated_by', 'updated_at']
    list_filter = ['data_type', 'is_editable', 'updated_at']
    search_fields = ['key', 'value', 'description']
    ordering = ['key']
    readonly_fields = ['updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj and not obj.is_editable:
            return self.readonly_fields + ('key', 'value', 'data_type')
        return self.readonly_fields


@admin.register(ProcurementPolicy)
class ProcurementPolicyAdmin(admin.ModelAdmin):
    list_display = ['policy_number', 'title', 'effective_date', 'expiry_date', 'is_active', 'created_at']
    list_filter = ['is_active', 'effective_date', 'expiry_date', 'created_at']
    search_fields = ['policy_number', 'title', 'description']
    ordering = ['-effective_date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'effective_date'
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('policy_number', 'title', 'description')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Dates', {
            'fields': ('effective_date', 'expiry_date', 'is_active')
        }),
        ('Document', {
            'fields': ('document',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# ============================================================================
# PROCUREMENT PLANNING (Add this new section after Item Catalog section)
# ============================================================================

class ProcurementPlanItemInline(admin.TabularInline):
    model = ProcurementPlanItem
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'remaining_quantity', 'remaining_budget']
    fields = [
        'item', 'item_type', 'description', 'quantity', 'unit_of_measure',
        'estimated_cost', 'budget', 'procurement_method', 'planned_quarter',
        'source_of_funds', 'status', 'sequence'
    ]
    
    def remaining_quantity(self, obj):
        if obj.pk:
            return f"{obj.remaining_quantity} {obj.unit_of_measure}"
        return "-"
    remaining_quantity.short_description = 'Remaining Qty'
    
    def remaining_budget(self, obj):
        if obj.pk:
            return format_html(
                '<span style="color: {};">{:,.2f}</span>',
                'green' if obj.remaining_budget > 0 else 'red',
                obj.remaining_budget
            )
        return "-"
    remaining_budget.short_description = 'Remaining Budget'


class ProcurementPlanAmendmentInline(admin.TabularInline):
    model = ProcurementPlanAmendment
    extra = 0
    readonly_fields = ['amendment_number', 'requested_at', 'approved_at']
    fields = [
        'amendment_number', 'amendment_type', 'status', 
        'requested_by', 'approved_by'
    ]
    can_delete = False


@admin.register(ProcurementPlan)
class ProcurementPlanAdmin(admin.ModelAdmin):
    list_display = [
        'plan_number', 'budget_year', 'department', 'title', 
        'status', 'is_amended', 'amendment_count', 
        'submitted_by', 'approved_by', 'created_at'
    ]
    list_filter = [
        'status', 'is_amended', 'budget_year', 
        'department', 'created_at', 'submitted_at'
    ]
    search_fields = [
        'plan_number', 'title', 'description',
        'department__name', 'department__code'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'plan_number', 'created_at', 'updated_at',
        'submitted_at', 'approved_at', 'amendment_count'
    ]
    inlines = [ProcurementPlanItemInline, ProcurementPlanAmendmentInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Plan Information', {
            'fields': (
                'plan_number', 'budget_year', 'department',
                'title', 'description'
            )
        }),
        ('Status', {
            'fields': ('status', 'is_amended', 'amendment_count')
        }),
        ('Submission', {
            'fields': ('submitted_by', 'submitted_at')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['submit_plans', 'approve_plans', 'activate_plans']
    
    def submit_plans(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='DRAFT').update(
            status='SUBMITTED',
            submitted_by=request.user,
            submitted_at=timezone.now()
        )
        self.message_user(request, f'{updated} plan(s) submitted successfully.')
    submit_plans.short_description = 'Submit selected plans'
    
    def approve_plans(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='SUBMITTED').update(
            status='APPROVED',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} plan(s) approved successfully.')
    approve_plans.short_description = 'Approve selected plans'
    
    def activate_plans(self, request, queryset):
        updated = queryset.filter(status='APPROVED').update(status='ACTIVE')
        self.message_user(request, f'{updated} plan(s) activated successfully.')
    activate_plans.short_description = 'Activate selected plans'


@admin.register(ProcurementPlanItem)
class ProcurementPlanItemAdmin(admin.ModelAdmin):
    list_display = [
        'procurement_plan', 'description_short', 'item_type',
        'quantity', 'unit_of_measure', 'estimated_cost',
        'procurement_method', 'planned_quarter', 'status',
        'remaining_quantity', 'remaining_budget'
    ]
    list_filter = [
        'item_type', 'procurement_method', 'planned_quarter',
        'status', 'created_at'
    ]
    search_fields = [
        'procurement_plan__plan_number', 'description',
        'specifications', 'source_of_funds'
    ]
    ordering = ['procurement_plan', 'sequence']
    readonly_fields = [
        'created_at', 'updated_at',
        'remaining_quantity', 'remaining_budget'
    ]
    
    fieldsets = (
        ('Plan Reference', {
            'fields': ('procurement_plan', 'item', 'sequence')
        }),
        ('Item Details', {
            'fields': (
                'item_type', 'description', 'specifications',
                'quantity', 'unit_of_measure'
            )
        }),
        ('Budget & Procurement', {
            'fields': (
                'estimated_cost', 'budget', 'source_of_funds',
                'procurement_method', 'planned_quarter'
            )
        }),
        ('Status & Usage', {
            'fields': (
                'status', 'quantity_requisitioned', 'amount_committed',
                'remaining_quantity', 'remaining_budget'
            )
        }),
        ('Additional Info', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def remaining_quantity(self, obj):
        return format_html(
            '<span style="font-weight: 600;">{} {}</span>',
            obj.remaining_quantity,
            obj.unit_of_measure
        )
    remaining_quantity.short_description = 'Remaining Qty'
    
    def remaining_budget(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: 600;">{:,.2f}</span>',
            'green' if obj.remaining_budget > 0 else 'red',
            obj.remaining_budget
        )
    remaining_budget.short_description = 'Remaining Budget'


@admin.register(ProcurementPlanAmendment)
class ProcurementPlanAmendmentAdmin(admin.ModelAdmin):
    list_display = [
        'amendment_number', 'procurement_plan', 'amendment_type',
        'status', 'requested_by', 'requested_at',
        'approved_by', 'approved_at'
    ]
    list_filter = [
        'amendment_type', 'status', 'requested_at', 'approved_at'
    ]
    search_fields = [
        'amendment_number', 'procurement_plan__plan_number',
        'justification', 'rejection_reason'
    ]
    ordering = ['-requested_at']
    readonly_fields = [
        'amendment_number', 'requested_at', 'approved_at'
    ]
    
    fieldsets = (
        ('Amendment Information', {
            'fields': (
                'amendment_number', 'procurement_plan',
                'amendment_type', 'plan_item'
            )
        }),
        ('Justification', {
            'fields': ('justification', 'supporting_document')
        }),
        ('Changes', {
            'fields': ('old_values', 'new_values'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Request Details', {
            'fields': ('requested_by', 'requested_at')
        }),
        ('Approval Details', {
            'fields': ('approved_by', 'approved_at')
        }),
    )
    
    actions = ['approve_amendments', 'reject_amendments']
    
    def approve_amendments(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} amendment(s) approved successfully.')
    approve_amendments.short_description = 'Approve selected amendments'
    
    def reject_amendments(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='PENDING').update(
            status='REJECTED',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} amendment(s) rejected.')
    reject_amendments.short_description = 'Reject selected amendments'


# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

admin.site.site_header = "University PMIS Administration"
admin.site.site_title = "University PMIS Admin Portal"
admin.site.index_title = "Welcome to University Procurement Management System"


# ============================================================================
# CUSTOM ADMIN ACTIONS
# ============================================================================

def export_as_csv(modeladmin, request, queryset):
    """
    Generic export as CSV action
    """
    import csv
    from django.http import HttpResponse
    from django.utils import timezone
    
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta}-{timezone.now().strftime("%Y%m%d-%H%M%S")}.csv'
    
    writer = csv.writer(response)
    writer.writerow(field_names)
    
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    
    return response

export_as_csv.short_description = "Export Selected as CSV"


# Register the action globally for all admin classes
# You can add this action to specific admin classes as needed