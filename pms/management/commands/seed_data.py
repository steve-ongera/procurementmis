from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta, date
import random
from pms.models import *


class Command(BaseCommand):
    help = 'Seeds the database with sample data for 1 year period'

    def __init__(self):
        super().__init__()
        self.start_date = timezone.now().date() - timedelta(days=365)
        self.end_date = timezone.now().date()
        
    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data seeding...')
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        self.stdout.write('Clearing existing data...')
        self.clear_data()
        
        # Seed in order of dependencies
        self.stdout.write('Creating users and permissions...')
        self.create_permissions()
        self.create_users()
        
        self.stdout.write('Creating organizational structure...')
        self.create_faculties_and_departments()
        
        self.stdout.write('Creating budget structure...')
        self.create_budget_data()
        
        self.stdout.write('Creating item catalog...')
        self.create_item_catalog()
        
        self.stdout.write('Creating suppliers...')
        self.create_suppliers()
        
        self.stdout.write('Creating requisitions...')
        self.create_requisitions()
        
        self.stdout.write('Creating tenders and bids...')
        self.create_tenders_and_bids()
        
        self.stdout.write('Creating purchase orders...')
        self.create_purchase_orders()
        
        self.stdout.write('Creating contracts...')
        self.create_contracts()
        
        self.stdout.write('Creating stores and inventory...')
        self.create_stores_and_inventory()
        
        self.stdout.write('Creating invoices and payments...')
        self.create_invoices_and_payments()
        
        self.stdout.write('Creating notifications...')
        self.create_notifications()
        
        self.stdout.write('Creating system configuration...')
        self.create_system_config()
        
        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))

    def clear_data(self):
        """Clear existing data - use with caution"""
        models_to_clear = [
            Payment, InvoiceItem, InvoiceDocument, Invoice,
            Asset, StockIssueItem, StockIssue, StockMovement, StockItem,
            GRNItem, GoodsReceivedNote,
            ContractVariation, ContractMilestone, ContractDocument, Contract,
            POAmendment, PurchaseOrderItem, PurchaseOrder,
            BidEvaluation, BidDocument, BidItem, Bid, EvaluationCriteria,
            TenderDocument, Tender,
            RequisitionAttachment, RequisitionItem, RequisitionApproval, Requisition,
            SupplierPerformance, SupplierDocument, Supplier,
            Item, ItemCategory,
            BudgetReallocation, Budget, BudgetCategory, BudgetYear,
            Department, Faculty,
            Notification, EmailLog, ProcurementReport,
            AuditLog, RolePermission, Permission,
            ApprovalThreshold, SystemConfiguration, ProcurementPolicy,
            Store,
        ]
        for model in models_to_clear:
            model.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

    def create_permissions(self):
        """Create system permissions"""
        permissions_data = [
            ('Create Requisition', 'create_requisition', 'Can create requisitions', 'Requisition'),
            ('Approve Requisition', 'approve_requisition', 'Can approve requisitions', 'Requisition'),
            ('Create Tender', 'create_tender', 'Can create tenders', 'Tender'),
            ('Evaluate Bids', 'evaluate_bids', 'Can evaluate bids', 'Tender'),
            ('Create PO', 'create_po', 'Can create purchase orders', 'Purchase Order'),
            ('Approve Payment', 'approve_payment', 'Can approve payments', 'Payment'),
            ('Manage Inventory', 'manage_inventory', 'Can manage inventory', 'Inventory'),
            ('View Reports', 'view_reports', 'Can view reports', 'Reports'),
        ]
        
        for name, code, desc, module in permissions_data:
            Permission.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc, 'module': module}
            )

    def create_users(self):
        """Create users with different roles"""
        self.users = {}
        
        users_data = [
            ('admin', 'admin@university.edu', 'Admin', 'User', 'ADMIN', None),
            ('john.doe', 'john.doe@university.edu', 'John', 'Doe', 'STAFF', None),
            ('jane.smith', 'jane.smith@university.edu', 'Jane', 'Smith', 'HOD', None),
            ('procurement1', 'procurement@university.edu', 'Peter', 'Procurement', 'PROCUREMENT', None),
            ('finance1', 'finance@university.edu', 'Frank', 'Finance', 'FINANCE', None),
            ('stores1', 'stores@university.edu', 'Steve', 'Stores', 'STORES', None),
            ('auditor1', 'auditor@university.edu', 'Alice', 'Auditor', 'AUDITOR', None),
        ]
        
        for username, email, first, last, role, dept in users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'role': role,
                    'employee_id': f'EMP{random.randint(1000, 9999)}',
                    'phone_number': f'+254{random.randint(700000000, 799999999)}',
                    'is_active_user': True,
                    'password': make_password('password123')
                }
            )
            self.users[role] = user

    def create_faculties_and_departments(self):
        """Create faculties and departments"""
        self.faculties = []
        self.departments = []
        
        faculties_data = [
            ('Faculty of Science', 'FSC'),
            ('Faculty of Engineering', 'FEN'),
            ('Faculty of Business', 'FBS'),
            ('Faculty of Education', 'FED'),
        ]
        
        for name, code in faculties_data:
            faculty = Faculty.objects.create(
                name=name,
                code=code,
                dean=self.users.get('HOD'),
                is_active=True
            )
            self.faculties.append(faculty)
        
        departments_data = [
            ('Computer Science', 'CS', 'ACADEMIC', 0),
            ('Mathematics', 'MATH', 'ACADEMIC', 0),
            ('Civil Engineering', 'CIV', 'ACADEMIC', 1),
            ('Electrical Engineering', 'ELE', 'ACADEMIC', 1),
            ('Accounting', 'ACC', 'ACADEMIC', 2),
            ('Management', 'MGT', 'ACADEMIC', 2),
            ('Procurement Department', 'PROC', 'ADMINISTRATIVE', 3),
            ('Finance Department', 'FIN', 'ADMINISTRATIVE', 3),
            ('ICT Services', 'ICT', 'SUPPORT', 3),
        ]
        
        for name, code, dept_type, fac_idx in departments_data:
            dept = Department.objects.create(
                faculty=self.faculties[fac_idx],
                name=name,
                code=code,
                department_type=dept_type,
                hod=self.users.get('HOD'),
                is_active=True
            )
            self.departments.append(dept)
        
        # Update users with departments
        for i, user in enumerate([self.users['STAFF'], self.users['HOD']]):
            user.department = self.departments[i % len(self.departments)]
            user.save()

    def create_budget_data(self):
        """Create budget years, categories and allocations"""
        # Budget Year
        year = timezone.now().year
        self.budget_year = BudgetYear.objects.create(
            name=f'FY {year}/{year+1}',
            start_date=date(year, 7, 1),
            end_date=date(year+1, 6, 30),
            is_active=True
        )
        
        # Budget Categories
        self.budget_categories = []
        categories_data = [
            ('Equipment & Machinery', 'EQP-001'),
            ('Office Supplies', 'SUP-001'),
            ('ICT Equipment', 'ICT-001'),
            ('Laboratory Supplies', 'LAB-001'),
            ('Furniture & Fixtures', 'FUR-001'),
            ('Professional Services', 'SRV-001'),
            ('Maintenance & Repairs', 'MNT-001'),
        ]
        
        for name, code in categories_data:
            cat = BudgetCategory.objects.create(
                name=name,
                code=code,
                is_active=True
            )
            self.budget_categories.append(cat)
        
        # Budget Allocations
        self.budgets = []
        for dept in self.departments[:5]:  # First 5 departments
            for cat in self.budget_categories:
                budget = Budget.objects.create(
                    budget_year=self.budget_year,
                    department=dept,
                    category=cat,
                    budget_type=random.choice(['DEPARTMENTAL', 'PROJECT']),
                    allocated_amount=Decimal(random.randint(100000, 500000)),
                    committed_amount=Decimal(0),
                    actual_spent=Decimal(0),
                    is_active=True,
                    created_by=self.users['ADMIN']
                )
                self.budgets.append(budget)

    def create_item_catalog(self):
        """Create item categories and items"""
        # Item Categories
        self.item_categories = []
        categories_data = [
            ('Desktop Computers', 'ICT-DESK', 'GOODS'),
            ('Laptops', 'ICT-LAP', 'GOODS'),
            ('Office Furniture', 'FUR-OFF', 'GOODS'),
            ('Laboratory Equipment', 'LAB-EQP', 'GOODS'),
            ('Stationery', 'STAT', 'GOODS'),
            ('Consulting Services', 'CONS', 'SERVICES'),
            ('Cleaning Services', 'CLN', 'SERVICES'),
        ]
        
        for name, code, cat_type in categories_data:
            cat = ItemCategory.objects.create(
                name=name,
                code=code,
                category_type=cat_type,
                is_active=True
            )
            self.item_categories.append(cat)
        
        # Items
        self.items = []
        items_data = [
            ('Dell Desktop Computer', 'DESK-001', 'Desktop computer with monitor', 'Unit', 45000, 0),
            ('HP Laptop', 'LAP-001', 'HP Laptop i5 8GB RAM', 'Unit', 65000, 1),
            ('Office Desk', 'DSK-001', 'Executive office desk', 'Unit', 15000, 2),
            ('Office Chair', 'CHR-001', 'Ergonomic office chair', 'Unit', 8000, 2),
            ('Microscope', 'MIC-001', 'Laboratory microscope', 'Unit', 120000, 3),
            ('A4 Paper', 'PPR-001', 'A4 printing paper', 'Ream', 500, 4),
            ('Pens', 'PEN-001', 'Ballpoint pens', 'Box', 300, 4),
            ('IT Consultant', 'CONS-IT', 'IT consulting services', 'Day', 15000, 5),
        ]
        
        for name, code, desc, uom, price, cat_idx in items_data:
            item = Item.objects.create(
                category=self.item_categories[cat_idx],
                name=name,
                code=code,
                description=desc,
                unit_of_measure=uom,
                standard_price=Decimal(price),
                is_active=True
            )
            self.items.append(item)

    def create_suppliers(self):
        """Create suppliers"""
        self.suppliers = []
        suppliers_data = [
            ('TechSupply Ltd', 'REG001', 'techsupply@example.com', '+254712345601', 'John Tech', [0, 1]),
            ('Office Furniture Co', 'REG002', 'furniture@example.com', '+254712345602', 'Mary Furni', [2]),
            ('Lab Equipment Inc', 'REG003', 'labequip@example.com', '+254712345603', 'Peter Lab', [3]),
            ('Stationery World', 'REG004', 'stationery@example.com', '+254712345604', 'Jane Station', [4]),
            ('IT Consultants Ltd', 'REG005', 'itconsult@example.com', '+254712345605', 'Bob Consult', [5]),
        ]
        
        for i, (name, reg, email, phone, contact, cat_indices) in enumerate(suppliers_data):
            supplier = Supplier.objects.create(
                supplier_number=f'SUP-{2024}-{i+1:06d}',
                name=name,
                registration_number=reg,
                tax_id=f'TAX{random.randint(100000, 999999)}',
                email=email,
                phone_number=phone,
                physical_address=f'{random.randint(1, 100)} Main Street, Nairobi',
                contact_person=contact,
                contact_person_phone=phone,
                contact_person_email=email,
                bank_name='Kenya Commercial Bank',
                bank_branch='Nairobi Branch',
                account_number=f'{random.randint(1000000000, 9999999999)}',
                account_name=name,
                status='APPROVED',
                rating=Decimal(random.uniform(3.5, 5.0)),
                created_by=self.users['PROCUREMENT']
            )
            
            # Add categories
            for idx in cat_indices:
                supplier.categories.add(self.item_categories[idx])
            
            self.suppliers.append(supplier)
            
            # Add supplier documents
            SupplierDocument.objects.create(
                supplier=supplier,
                document_type='REGISTRATION',
                document_name=f'{name} Registration Certificate',
                file='dummy/path/registration.pdf',
                is_verified=True,
                verified_by=self.users['PROCUREMENT'],
                verified_at=timezone.now()
            )

    def create_requisitions(self):
        """Create requisitions for the year"""
        self.requisitions = []
        
        # Create 50 requisitions spread over the year
        for i in range(50):
            days_ago = random.randint(0, 365)
            created_date = timezone.now() - timedelta(days=days_ago)
            
            dept = random.choice(self.departments[:5])
            budget = random.choice([b for b in self.budgets if b.department == dept])
            
            # Determine status based on age
            if days_ago > 300:
                status = 'APPROVED'
            elif days_ago > 200:
                status = random.choice(['APPROVED', 'PROCUREMENT_APPROVED'])
            elif days_ago > 100:
                status = random.choice(['HOD_APPROVED', 'BUDGET_APPROVED'])
            else:
                status = random.choice(['SUBMITTED', 'HOD_APPROVED', 'DRAFT'])
            
            req = Requisition.objects.create(
                title=f'Purchase Request for {random.choice(self.items).name}',
                department=dept,
                budget=budget,
                requested_by=self.users['STAFF'],
                status=status,
                priority=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                justification='Required for departmental operations and academic activities',
                estimated_amount=Decimal(random.randint(50000, 500000)),
                required_date=created_date.date() + timedelta(days=30),
                submitted_at=created_date if status != 'DRAFT' else None
            )
            req.created_at = created_date
            req.save()
            
            # Add requisition items
            num_items = random.randint(1, 5)
            for _ in range(num_items):
                item = random.choice(self.items)
                qty = random.randint(1, 20)
                unit_price = item.standard_price or Decimal(random.randint(1000, 50000))
                
                RequisitionItem.objects.create(
                    requisition=req,
                    item=item,
                    item_description=item.description,
                    specifications=f'Standard specifications for {item.name}',
                    quantity=Decimal(qty),
                    unit_of_measure=item.unit_of_measure,
                    estimated_unit_price=unit_price,
                    estimated_total=Decimal(qty) * unit_price
                )
            
            # Create approval records for non-draft requisitions
            if status != 'DRAFT':
                RequisitionApproval.objects.create(
                    requisition=req,
                    approval_stage='HOD',
                    approver=self.users['HOD'],
                    status='APPROVED' if status != 'SUBMITTED' else 'PENDING',
                    comments='Approved for procurement',
                    approval_date=created_date + timedelta(days=2) if status != 'SUBMITTED' else None,
                    sequence=1
                )
            
            self.requisitions.append(req)

    def create_tenders_and_bids(self):
        """Create tenders and bids"""
        self.tenders = []
        self.bids = []
        
        # Create tenders for approved requisitions
        approved_reqs = [r for r in self.requisitions if r.status == 'APPROVED'][:20]
        
        for req in approved_reqs:
            days_ago = (timezone.now() - req.created_at).days
            
            tender = Tender.objects.create(
                requisition=req,
                title=f'Tender for {req.title}',
                tender_type='RFQ',
                procurement_method=random.choice(['OPEN', 'RESTRICTED']),
                description=req.justification,
                publish_date=req.created_at + timedelta(days=5),
                closing_date=req.created_at + timedelta(days=20),
                bid_opening_date=req.created_at + timedelta(days=21),
                estimated_budget=req.estimated_amount,
                status='AWARDED' if days_ago > 60 else 'EVALUATING',
                created_by=self.users['PROCUREMENT']
            )
            tender.created_at = req.created_at + timedelta(days=3)
            tender.save()
            
            # Add invited suppliers
            relevant_suppliers = [s for s in self.suppliers if 
                                any(cat in s.categories.all() for cat in 
                                    [item.item.category for item in req.items.all() if item.item])]
            
            if relevant_suppliers:
                for supplier in random.sample(relevant_suppliers, min(3, len(relevant_suppliers))):
                    tender.invited_suppliers.add(supplier)
                    
                    # Create bids
                    bid = Bid.objects.create(
                        tender=tender,
                        supplier=supplier,
                        bid_amount=req.estimated_amount * Decimal(random.uniform(0.85, 1.15)),
                        validity_period_days=90,
                        delivery_period_days=random.randint(14, 60),
                        status='AWARDED' if tender.status == 'AWARDED' else 'QUALIFIED',
                        evaluation_score=Decimal(random.uniform(70, 95)),
                        technical_score=Decimal(random.uniform(65, 95)),
                        financial_score=Decimal(random.uniform(75, 100)),
                        submitted_at=tender.publish_date + timedelta(days=random.randint(1, 14))
                    )
                    
                    # Create bid items
                    for req_item in req.items.all():
                        BidItem.objects.create(
                            bid=bid,
                            requisition_item=req_item,
                            quoted_unit_price=req_item.estimated_unit_price * Decimal(random.uniform(0.9, 1.1)),
                            quoted_total=req_item.estimated_total * Decimal(random.uniform(0.9, 1.1)),
                            delivery_period_days=random.randint(14, 45),
                            warranty_period_months=random.randint(12, 36)
                        )
                    
                    self.bids.append(bid)
            
            self.tenders.append(tender)

    def create_purchase_orders(self):
        """Create purchase orders"""
        self.purchase_orders = []
        
        # Create POs for awarded bids
        awarded_bids = [b for b in self.bids if b.status == 'AWARDED'][:15]
        
        for bid in awarded_bids:
            days_ago = (timezone.now().date() - bid.submitted_at.date()).days
            
            status_choices = ['APPROVED', 'SENT', 'ACKNOWLEDGED', 'DELIVERED']
            status = random.choice(status_choices[:min(len(status_choices), max(1, days_ago // 30))])
            
            po = PurchaseOrder.objects.create(
                requisition=bid.tender.requisition,
                supplier=bid.supplier,
                bid=bid,
                delivery_date=timezone.now().date() + timedelta(days=bid.delivery_period_days),
                delivery_address='University Main Campus, Nairobi',
                subtotal=bid.bid_amount,
                tax_amount=bid.bid_amount * Decimal('0.16'),
                total_amount=bid.bid_amount * Decimal('1.16'),
                payment_terms='Net 30 days after delivery',
                status=status,
                approved_by=self.users['PROCUREMENT'],
                approved_at=bid.submitted_at + timedelta(days=5),
                sent_at=bid.submitted_at + timedelta(days=7) if status != 'DRAFT' else None,
                created_by=self.users['PROCUREMENT']
            )
            
            # Create PO items
            for bid_item in bid.items.all():
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    requisition_item=bid_item.requisition_item,
                    item_description=bid_item.requisition_item.item_description,
                    specifications=bid_item.requisition_item.specifications,
                    quantity=bid_item.requisition_item.quantity,
                    unit_of_measure=bid_item.requisition_item.unit_of_measure,
                    unit_price=bid_item.quoted_unit_price,
                    total_price=bid_item.quoted_total,
                    quantity_delivered=bid_item.requisition_item.quantity if status == 'DELIVERED' else 0
                )
            
            self.purchase_orders.append(po)

    def create_contracts(self):
        """Create contracts for large POs"""
        self.contracts = []
        
        # Create contracts for POs over certain amount
        large_pos = [po for po in self.purchase_orders if po.total_amount > 500000][:10]
        
        for po in large_pos:
            contract = Contract.objects.create(
                purchase_order=po,
                supplier=po.supplier,
                title=f'Contract for {po.requisition.title}',
                contract_type='GOODS',
                description=po.requisition.justification,
                contract_value=po.total_amount,
                start_date=po.po_date,
                end_date=po.delivery_date + timedelta(days=30),
                status='ACTIVE',
                payment_schedule='Payment upon delivery and acceptance',
                performance_bond_required=True,
                performance_bond_amount=po.total_amount * Decimal('0.1'),
                contract_manager=self.users['PROCUREMENT'],
                signed_by_supplier=True,
                signed_by_university=True,
                signing_date=po.po_date,
                created_by=self.users['PROCUREMENT']
            )
            
            # Create contract milestone
            ContractMilestone.objects.create(
                contract=contract,
                milestone_name='Delivery and Installation',
                description='Complete delivery and installation of goods',
                due_date=po.delivery_date,
                milestone_value=contract.contract_value,
                payment_percentage=Decimal('100'),
                status='COMPLETED' if po.status == 'DELIVERED' else 'IN_PROGRESS',
                deliverables='All items as per purchase order',
                acceptance_criteria='Items inspected and accepted',
                sequence=1
            )
            
            self.contracts.append(contract)

    def create_stores_and_inventory(self):
        """Create stores, GRNs, and inventory"""
        # Create stores
        self.stores = []
        stores_data = [
            ('Main University Store', 'MAIN', 'MAIN', None),
            ('ICT Store', 'ICT', 'ICT', self.departments[8] if len(self.departments) > 8 else None),
            ('Science Laboratory Store', 'LAB', 'LABORATORY', self.departments[0] if self.departments else None),
        ]
        
        for name, code, store_type, dept in stores_data:
            store = Store.objects.create(
                name=name,
                code=code,
                store_type=store_type,
                department=dept,
                location=f'{name} Location, Main Campus',
                store_keeper=self.users['STORES'],
                is_active=True
            )
            self.stores.append(store)
        
        # Create GRNs for delivered POs
        delivered_pos = [po for po in self.purchase_orders if po.status in ['DELIVERED', 'CLOSED']]
        
        for po in delivered_pos[:10]:
            grn = GoodsReceivedNote.objects.create(
                purchase_order=po,
                store=random.choice(self.stores),
                delivery_note_number=f'DN-{random.randint(10000, 99999)}',
                delivery_date=po.delivery_date,
                received_by=self.users['STORES'],
                inspected_by=self.users['STORES'],
                inspection_date=po.delivery_date + timedelta(days=1),
                status='ACCEPTED',
                general_condition='Goods received in good condition'
            )
            
            # Create GRN items and stock items
            for po_item in po.items.all():
                GRNItem.objects.create(
                    grn=grn,
                    po_item=po_item,
                    quantity_ordered=po_item.quantity,
                    quantity_delivered=po_item.quantity,
                    quantity_accepted=po_item.quantity,
                    item_status='ACCEPTED'
                )
                
                # Create or update stock item
                if po_item.requisition_item.item:
                    stock_item, created = StockItem.objects.get_or_create(
                        store=grn.store,
                        item=po_item.requisition_item.item,
                        defaults={
                            'quantity_on_hand': po_item.quantity,
                            'reorder_level': Decimal('10'),
                            'average_unit_cost': po_item.unit_price,
                            'total_value': po_item.total_price,
                            'last_restock_date': grn.delivery_date
                        }
                    )
                    
                    if not created:
                        stock_item.quantity_on_hand += po_item.quantity
                        stock_item.total_value += po_item.total_price
                        stock_item.average_unit_cost = stock_item.total_value / stock_item.quantity_on_hand
                        stock_item.last_restock_date = grn.delivery_date
                        stock_item.save()
                    
                    # Create stock movement
                    StockMovement.objects.create(
                        stock_item=stock_item,
                        movement_type='RECEIPT',
                        reference_number=grn.grn_number,
                        reference_type='GRN',
                        quantity=po_item.quantity,
                        unit_cost=po_item.unit_price,
                        balance_before=stock_item.quantity_on_hand - po_item.quantity,
                        balance_after=stock_item.quantity_on_hand,
                        to_store=grn.store,
                        performed_by=self.users['STORES']
                    )

    def create_invoices_and_payments(self):
        """Create invoices and payments"""
        # Create invoices for delivered POs
        delivered_pos = [po for po in self.purchase_orders if po.status in ['DELIVERED', 'CLOSED']][:10]
        
        for po in delivered_pos:
            invoice = Invoice.objects.create(
                invoice_number=f'INV-{timezone.now().year}-{random.randint(10000, 99999)}',
                supplier_invoice_number=f'SI-{random.randint(10000, 99999)}',
                purchase_order=po,
                supplier=po.supplier,
                invoice_date=po.delivery_date + timedelta(days=2),
                due_date=po.delivery_date + timedelta(days=32),
                subtotal=po.subtotal,
                tax_amount=po.tax_amount,
                total_amount=po.total_amount,
                status=random.choice(['APPROVED', 'PAID']),
                is_three_way_matched=True,
                verified_by=self.users['FINANCE'],
                verified_at=po.delivery_date + timedelta(days=3),
                approved_by=self.users['FINANCE'],
                approved_at=po.delivery_date + timedelta(days=5),
                submitted_by=self.users['PROCUREMENT']
            )
            
            # Create invoice items
            for po_item in po.items.all():
                InvoiceItem.objects.create(
                    invoice=invoice,
                    po_item=po_item,
                    description=po_item.item_description,
                    quantity=po_item.quantity,
                    unit_price=po_item.unit_price,
                    total_price=po_item.total_price,
                    tax_rate=Decimal('16'),
                    tax_amount=po_item.total_price * Decimal('0.16')
                )
            
            # Create payment if invoice is paid
            if invoice.status == 'PAID':
                payment = Payment.objects.create(
                    invoice=invoice,
                    payment_date=invoice.due_date - timedelta(days=5),
                    payment_amount=invoice.total_amount,
                    payment_method='BANK_TRANSFER',
                    payment_reference=f'PMT-{random.randint(100000, 999999)}',
                    bank_name=po.supplier.bank_name,
                    status='COMPLETED',
                    processed_by=self.users['FINANCE'],
                    approved_by=self.users['FINANCE']
                )
                
                invoice.payment_reference = payment.payment_number
                invoice.payment_date = payment.payment_date
                invoice.save()

    def create_notifications(self):
        """Create notifications for users"""
        notification_templates = [
            ('REQUISITION', 'New Requisition Submitted', 'A new requisition {} has been submitted for your approval', 'MEDIUM'),
            ('APPROVAL', 'Requisition Approved', 'Your requisition {} has been approved', 'LOW'),
            ('TENDER', 'New Tender Published', 'Tender {} has been published', 'MEDIUM'),
            ('PO', 'Purchase Order Created', 'Purchase Order {} has been created', 'MEDIUM'),
            ('DELIVERY', 'Goods Received', 'Goods for PO {} have been received', 'MEDIUM'),
            ('PAYMENT', 'Payment Processed', 'Payment {} has been processed', 'LOW'),
        ]
        
        for user_role, user in self.users.items():
            # Create 10-20 notifications per user
            for _ in range(random.randint(10, 20)):
                notif_type, title, msg_template, priority = random.choice(notification_templates)
                
                # Generate reference based on type
                if notif_type == 'REQUISITION' and self.requisitions:
                    ref = random.choice(self.requisitions).requisition_number
                elif notif_type == 'PO' and self.purchase_orders:
                    ref = random.choice(self.purchase_orders).po_number
                elif notif_type == 'PAYMENT':
                    ref = f'PAY-{timezone.now().year}-{random.randint(100000, 999999)}'
                else:
                    ref = f'REF-{random.randint(10000, 99999)}'
                
                is_read = random.choice([True, False, False])  # 33% read
                created_at = timezone.now() - timedelta(days=random.randint(0, 365))
                
                Notification.objects.create(
                    user=user,
                    notification_type=notif_type,
                    priority=priority,
                    title=title,
                    message=msg_template.format(ref),
                    link_url=f'/requisitions/{ref}',
                    is_read=is_read,
                    read_at=created_at + timedelta(hours=random.randint(1, 48)) if is_read else None,
                    created_at=created_at
                )

    def create_system_config(self):
        """Create system configuration and policies"""
        # System Configuration
        configs = [
            ('TAX_RATE', '16', 'DECIMAL', 'VAT tax rate percentage'),
            ('TENDER_THRESHOLD', '500000', 'DECIMAL', 'Minimum amount requiring tender'),
            ('APPROVAL_LEVELS', '3', 'INTEGER', 'Number of approval levels'),
            ('EMAIL_NOTIFICATIONS', 'true', 'BOOLEAN', 'Enable email notifications'),
            ('AUTO_PO_GENERATION', 'false', 'BOOLEAN', 'Automatically generate POs'),
        ]
        
        for key, value, data_type, desc in configs:
            SystemConfiguration.objects.create(
                key=key,
                value=value,
                data_type=data_type,
                description=desc,
                is_editable=True,
                updated_by=self.users['ADMIN']
            )
        
        # Approval Thresholds
        thresholds = [
            ('Level 1 - Below 100K', 0, 100000, True, False, True, True, False),
            ('Level 2 - 100K to 500K', 100000, 500000, True, True, True, True, False),
            ('Level 3 - 500K to 1M', 500000, 1000000, True, True, True, True, True),
            ('Level 4 - Above 1M', 1000000, None, True, True, True, True, True),
        ]
        
        for name, min_amt, max_amt, hod, fac, proc, fin, tender in thresholds:
            ApprovalThreshold.objects.create(
                name=name,
                min_amount=Decimal(min_amt),
                max_amount=Decimal(max_amt) if max_amt else None,
                requires_hod_approval=hod,
                requires_faculty_approval=fac,
                requires_procurement_approval=proc,
                requires_finance_approval=fin,
                requires_tender=tender,
                is_active=True
            )
        
        # Procurement Policies
        policies = [
            ('Procurement Policy 2024', 'POL-2024-001', 
             'University Procurement Policy', 
             'This policy governs all procurement activities within the university...',
             date(2024, 1, 1), None),
            ('Supplier Code of Conduct', 'POL-2024-002',
             'Code of Conduct for Suppliers',
             'All suppliers must adhere to ethical business practices...',
             date(2024, 1, 1), None),
            ('Emergency Procurement Guidelines', 'POL-2024-003',
             'Guidelines for Emergency Procurements',
             'Procedures for handling urgent procurement needs...',
             date(2024, 1, 1), None),
        ]
        
        for title, pol_num, desc, content, eff_date, exp_date in policies:
            ProcurementPolicy.objects.create(
                title=title,
                policy_number=pol_num,
                description=desc,
                content=content,
                effective_date=eff_date,
                expiry_date=exp_date,
                is_active=True,
                created_by=self.users['ADMIN']
            )
        
        # Create some audit logs
        self.create_audit_logs()
        
        # Create supplier performance reviews
        self.create_supplier_performance()

    def create_audit_logs(self):
        """Create audit log entries"""
        actions = ['CREATE', 'UPDATE', 'APPROVE', 'SUBMIT']
        models = ['Requisition', 'PurchaseOrder', 'Invoice', 'Payment']
        
        for _ in range(100):
            AuditLog.objects.create(
                user=random.choice(list(self.users.values())),
                action=random.choice(actions),
                model_name=random.choice(models),
                object_id=str(random.randint(1, 1000)),
                object_repr=f'Object {random.randint(1, 1000)}',
                changes={'field': 'old_value', 'new_field': 'new_value'},
                ip_address=f'192.168.1.{random.randint(1, 255)}',
                timestamp=timezone.now() - timedelta(days=random.randint(0, 365))
            )

    def create_supplier_performance(self):
        """Create supplier performance reviews"""
        for po in self.purchase_orders:
            if po.status == 'DELIVERED' and random.choice([True, False]):
                SupplierPerformance.objects.create(
                    supplier=po.supplier,
                    purchase_order=po,
                    quality_rating=random.randint(3, 5),
                    delivery_rating=random.randint(3, 5),
                    service_rating=random.randint(3, 5),
                    overall_rating=Decimal(random.uniform(3.5, 5.0)),
                    comments='Good service delivery overall',
                    reviewed_by=self.users['PROCUREMENT']
                )

    def random_date(self, start_date, end_date):
        """Generate random date between two dates"""
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        return start_date + timedelta(days=random_days)