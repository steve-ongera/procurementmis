"""
Management command to seed procurement plan data
File: management/commands/seed_procurement_plans.py
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import random
from datetime import datetime, timedelta

from pms.models import (
    ProcurementPlan, ProcurementPlanItem, ProcurementPlanAmendment,
    BudgetYear, Department, Budget, Item, ItemCategory, User
)


class Command(BaseCommand):
    help = 'Seeds procurement plan data with realistic sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing procurement plans before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing procurement plans...'))
            ProcurementPlanAmendment.objects.all().delete()
            ProcurementPlanItem.objects.all().delete()
            ProcurementPlan.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing data'))

        with transaction.atomic():
            self.stdout.write('Starting procurement plan seeding...')
            
            # Get required data
            self.get_prerequisites()
            
            # Create procurement plans
            self.create_procurement_plans()
            
            # Create plan amendments
            self.create_plan_amendments()
            
            self.stdout.write(self.style.SUCCESS('Successfully seeded procurement plan data!'))

    def get_prerequisites(self):
        """Get or verify required data exists"""
        self.stdout.write('Checking prerequisites...')
        
        # Get budget years
        self.budget_years = list(BudgetYear.objects.all().order_by('-start_date'))
        if not self.budget_years:
            self.stdout.write(self.style.ERROR('No budget years found. Please seed budget years first.'))
            return
        
        # Get active budget year
        self.active_year = BudgetYear.objects.filter(is_active=True).first()
        if not self.active_year:
            self.active_year = self.budget_years[0]
        
        # Get departments
        self.departments = list(Department.objects.filter(is_active=True))
        if not self.departments:
            self.stdout.write(self.style.ERROR('No departments found. Please seed departments first.'))
            return
        
        # Get budgets
        self.budgets = list(Budget.objects.filter(is_active=True))
        if not self.budgets:
            self.stdout.write(self.style.WARNING('No budgets found. Some features may be limited.'))
            self.budgets = []
        
        # Get item categories
        self.item_categories = list(ItemCategory.objects.filter(is_active=True))
        
        # Get items
        self.items = list(Item.objects.filter(is_active=True))
        
        # Get users
        self.procurement_users = list(User.objects.filter(role='PROCUREMENT'))
        self.admin_users = list(User.objects.filter(role='ADMIN'))
        
        if not self.procurement_users:
            self.procurement_users = list(User.objects.filter(is_staff=True))
        
        if not self.admin_users:
            self.admin_users = list(User.objects.filter(is_superuser=True))
        
        self.stdout.write(self.style.SUCCESS(
            f'Found: {len(self.budget_years)} budget years, '
            f'{len(self.departments)} departments, '
            f'{len(self.budgets)} budgets, '
            f'{len(self.items)} items'
        ))

    def create_procurement_plans(self):
        """Create procurement plans for departments"""
        self.stdout.write('Creating procurement plans...')
        
        plans_created = 0
        items_created = 0
        
        # Plan statuses to distribute
        statuses = ['DRAFT', 'SUBMITTED', 'APPROVED', 'ACTIVE', 'AMENDED']
        
        # Create plans for each department and budget year combination
        for budget_year in self.budget_years[:2]:  # Last 2 years
            for department in self.departments[:5]:  # First 5 departments
                
                # Skip if plan already exists
                if ProcurementPlan.objects.filter(
                    budget_year=budget_year,
                    department=department
                ).exists():
                    continue
                
                # Determine status based on year
                if budget_year == self.active_year:
                    status = random.choice(['DRAFT', 'SUBMITTED', 'APPROVED', 'ACTIVE'])
                else:
                    status = random.choice(['APPROVED', 'ACTIVE', 'AMENDED'])
                
                # Create plan
                plan = ProcurementPlan.objects.create(
                    budget_year=budget_year,
                    department=department,
                    title=f"{department.name} Annual Procurement Plan {budget_year.name}",
                    description=f"Comprehensive procurement plan for {department.name} covering all operational and capital expenditure requirements for fiscal year {budget_year.name}",
                    status=status,
                    submitted_by=random.choice(self.procurement_users) if self.procurement_users else None,
                    submitted_at=timezone.now() - timedelta(days=random.randint(30, 90)) if status != 'DRAFT' else None,
                    approved_by=random.choice(self.admin_users) if self.admin_users and status in ['APPROVED', 'ACTIVE', 'AMENDED'] else None,
                    approved_at=timezone.now() - timedelta(days=random.randint(10, 60)) if status in ['APPROVED', 'ACTIVE', 'AMENDED'] else None,
                    is_amended=status == 'AMENDED',
                    amendment_count=random.randint(1, 3) if status == 'AMENDED' else 0
                )
                
                plans_created += 1
                
                # Create plan items
                num_items = random.randint(8, 20)
                items_created += self.create_plan_items(plan, num_items)
                
                self.stdout.write(f'  Created plan: {plan.plan_number} ({status}) with {num_items} items')
        
        self.stdout.write(self.style.SUCCESS(
            f'Created {plans_created} procurement plans with {items_created} items'
        ))

    def create_plan_items(self, plan, count):
        """Create items for a procurement plan"""
        
        # Sample procurement items with realistic data
        sample_items = [
            {
                'type': 'GOODS',
                'description': 'Desktop Computers - Dell OptiPlex Series',
                'specifications': 'Intel Core i5, 8GB RAM, 256GB SSD, 21.5" Monitor',
                'quantity_range': (5, 20),
                'unit': 'Units',
                'cost_range': (45000, 65000),
                'method': 'OPEN_TENDER'
            },
            {
                'type': 'GOODS',
                'description': 'Laptop Computers - HP ProBook Series',
                'specifications': 'Intel Core i7, 16GB RAM, 512GB SSD, 15.6" Display',
                'quantity_range': (10, 30),
                'unit': 'Units',
                'cost_range': (55000, 75000),
                'method': 'OPEN_TENDER'
            },
            {
                'type': 'GOODS',
                'description': 'Office Furniture - Executive Desks',
                'specifications': 'Wooden desk with drawers, 1.6m x 0.8m',
                'quantity_range': (5, 15),
                'unit': 'Pieces',
                'cost_range': (25000, 35000),
                'method': 'RFQ'
            },
            {
                'type': 'GOODS',
                'description': 'Office Chairs - Ergonomic Design',
                'specifications': 'Adjustable height, lumbar support, mesh back',
                'quantity_range': (20, 50),
                'unit': 'Pieces',
                'cost_range': (8000, 12000),
                'method': 'RFQ'
            },
            {
                'type': 'GOODS',
                'description': 'Printer - Multifunction Laser',
                'specifications': 'Print, Scan, Copy, Network enabled, A3 capability',
                'quantity_range': (2, 5),
                'unit': 'Units',
                'cost_range': (45000, 65000),
                'method': 'RFQ'
            },
            {
                'type': 'GOODS',
                'description': 'Photocopier Machine - High Volume',
                'specifications': 'A3/A4, 45 ppm, Network, Duplex, Finisher',
                'quantity_range': (1, 3),
                'unit': 'Units',
                'cost_range': (250000, 450000),
                'method': 'RESTRICTED_TENDER'
            },
            {
                'type': 'SERVICES',
                'description': 'Annual IT Support and Maintenance',
                'specifications': 'On-site and remote support, 24/7 helpdesk, hardware maintenance',
                'quantity_range': (1, 1),
                'unit': 'Annual Contract',
                'cost_range': (500000, 1200000),
                'method': 'RESTRICTED_TENDER'
            },
            {
                'type': 'SERVICES',
                'description': 'Cleaning Services',
                'specifications': 'Daily office cleaning, waste management, sanitation',
                'quantity_range': (12, 12),
                'unit': 'Months',
                'cost_range': (150000, 250000),
                'method': 'OPEN_TENDER'
            },
            {
                'type': 'SERVICES',
                'description': 'Security Services',
                'specifications': '24-hour security guards, CCTV monitoring',
                'quantity_range': (12, 12),
                'unit': 'Months',
                'cost_range': (300000, 500000),
                'method': 'OPEN_TENDER'
            },
            {
                'type': 'GOODS',
                'description': 'Stationery Supplies',
                'specifications': 'Papers, pens, folders, staplers, etc.',
                'quantity_range': (1, 1),
                'unit': 'Lot',
                'cost_range': (80000, 150000),
                'method': 'RFQ'
            },
            {
                'type': 'GOODS',
                'description': 'Air Conditioning Units - Split Type',
                'specifications': '2.5 HP, Energy efficient, Inverter technology',
                'quantity_range': (3, 10),
                'unit': 'Units',
                'cost_range': (65000, 85000),
                'method': 'RFQ'
            },
            {
                'type': 'SERVICES',
                'description': 'Internet Connectivity Services',
                'specifications': 'Dedicated fiber, 100Mbps minimum, 99.9% uptime',
                'quantity_range': (12, 12),
                'unit': 'Months',
                'cost_range': (80000, 120000),
                'method': 'DIRECT_PROCUREMENT'
            },
            {
                'type': 'GOODS',
                'description': 'Projectors - HD Multimedia',
                'specifications': 'Full HD 1080p, 3500 lumens, HDMI/VGA',
                'quantity_range': (3, 8),
                'unit': 'Units',
                'cost_range': (35000, 55000),
                'method': 'RFQ'
            },
            {
                'type': 'WORKS',
                'description': 'Office Renovation and Painting',
                'specifications': 'Interior painting, minor repairs, electrical work',
                'quantity_range': (1, 1),
                'unit': 'Project',
                'cost_range': (400000, 800000),
                'method': 'RESTRICTED_TENDER'
            },
            {
                'type': 'GOODS',
                'description': 'Water Dispenser Units',
                'specifications': 'Hot and cold, floor standing, stainless steel',
                'quantity_range': (3, 8),
                'unit': 'Units',
                'cost_range': (12000, 18000),
                'method': 'RFQ'
            },
            {
                'type': 'GOODS',
                'description': 'Filing Cabinets - 4 Drawer',
                'specifications': 'Steel construction, lockable, vertical',
                'quantity_range': (5, 15),
                'unit': 'Pieces',
                'cost_range': (15000, 22000),
                'method': 'RFQ'
            },
            {
                'type': 'GOODS',
                'description': 'Backup Generator - Diesel',
                'specifications': '100 KVA, automatic changeover, soundproof canopy',
                'quantity_range': (1, 1),
                'unit': 'Unit',
                'cost_range': (1500000, 2500000),
                'method': 'OPEN_TENDER'
            },
            {
                'type': 'SERVICES',
                'description': 'Staff Training and Development',
                'specifications': 'Professional development workshops, certifications',
                'quantity_range': (1, 1),
                'unit': 'Program',
                'cost_range': (300000, 600000),
                'method': 'DIRECT_PROCUREMENT'
            },
            {
                'type': 'GOODS',
                'description': 'CCTV Camera System',
                'specifications': '16 channel DVR, 8 IP cameras, night vision, 2TB storage',
                'quantity_range': (1, 2),
                'unit': 'System',
                'cost_range': (180000, 280000),
                'method': 'RESTRICTED_TENDER'
            },
            {
                'type': 'GOODS',
                'description': 'UPS - Uninterruptible Power Supply',
                'specifications': '5KVA, Online, Battery backup 30 mins',
                'quantity_range': (3, 10),
                'unit': 'Units',
                'cost_range': (65000, 95000),
                'method': 'RFQ'
            },
        ]
        
        # Get department budgets
        dept_budgets = list(Budget.objects.filter(
            department=plan.department,
            budget_year=plan.budget_year,
            is_active=True
        ))
        
        if not dept_budgets and self.budgets:
            dept_budgets = random.sample(self.budgets, min(3, len(self.budgets)))
        
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        source_of_funds_options = [
            'Government Budget',
            'Internally Generated Revenue',
            'Development Partners',
            'Special Projects Fund',
            'Capitation'
        ]
        
        items_created = 0
        selected_items = random.sample(sample_items, min(count, len(sample_items)))
        
        for idx, item_data in enumerate(selected_items, 1):
            quantity = Decimal(str(random.randint(*item_data['quantity_range'])))
            unit_cost = Decimal(str(random.randint(*item_data['cost_range'])))
            total_cost = quantity * unit_cost
            
            # Select catalog item if available
            catalog_item = None
            if self.items:
                matching_items = [
                    i for i in self.items 
                    if item_data['type'].lower() in i.category.category_type.lower()
                ]
                if matching_items:
                    catalog_item = random.choice(matching_items)
            
            # Create plan item
            plan_item = ProcurementPlanItem.objects.create(
                procurement_plan=plan,
                item=catalog_item,
                item_type=item_data['type'],
                description=item_data['description'],
                specifications=item_data['specifications'],
                quantity=quantity,
                unit_of_measure=item_data['unit'],
                estimated_cost=total_cost,
                budget=random.choice(dept_budgets) if dept_budgets else None,
                procurement_method=item_data['method'],
                planned_quarter=random.choice(quarters),
                source_of_funds=random.choice(source_of_funds_options),
                status='PLANNED',
                sequence=idx,
                notes=''
            )
            
            # Randomly set some items to other statuses
            if plan.status in ['ACTIVE', 'AMENDED']:
                status_choice = random.random()
                if status_choice < 0.2:
                    plan_item.status = 'IN_PROGRESS'
                    plan_item.quantity_requisitioned = quantity * Decimal('0.5')
                    plan_item.amount_committed = total_cost * Decimal('0.5')
                elif status_choice < 0.3:
                    plan_item.status = 'COMPLETED'
                    plan_item.quantity_requisitioned = quantity
                    plan_item.amount_committed = total_cost
                
                plan_item.save()
            
            items_created += 1
        
        return items_created

    def create_plan_amendments(self):
        """Create sample amendments for some plans"""
        self.stdout.write('Creating plan amendments...')
        
        # Get amended or active plans
        plans = list(ProcurementPlan.objects.filter(
            status__in=['APPROVED', 'ACTIVE', 'AMENDED']
        ))
        
        if not plans:
            self.stdout.write(self.style.WARNING('No plans available for amendments'))
            return
        
        amendment_types = [
            'ADD_ITEM',
            'REMOVE_ITEM',
            'MODIFY_ITEM',
            'BUDGET_CHANGE',
            'QUARTER_CHANGE',
            'METHOD_CHANGE'
        ]
        
        statuses = ['PENDING', 'APPROVED', 'REJECTED']
        
        amendments_created = 0
        
        # Create 1-3 amendments for random plans
        for plan in random.sample(plans, min(5, len(plans))):
            num_amendments = random.randint(1, 3)
            
            for _ in range(num_amendments):
                amendment_type = random.choice(amendment_types)
                status = random.choice(statuses)
                
                # Select a plan item if needed
                plan_item = None
                if amendment_type in ['REMOVE_ITEM', 'MODIFY_ITEM', 'BUDGET_CHANGE', 'QUARTER_CHANGE', 'METHOD_CHANGE']:
                    plan_items = list(plan.items.all())
                    if plan_items:
                        plan_item = random.choice(plan_items)
                
                # Create amendment
                justification = self.get_amendment_justification(amendment_type)
                old_values, new_values = self.get_amendment_values(amendment_type, plan_item)
                
                amendment = ProcurementPlanAmendment.objects.create(
                    procurement_plan=plan,
                    amendment_type=amendment_type,
                    plan_item=plan_item,
                    justification=justification,
                    old_values=old_values,
                    new_values=new_values,
                    status=status,
                    requested_by=random.choice(self.procurement_users) if self.procurement_users else None,
                    approved_by=random.choice(self.admin_users) if self.admin_users and status == 'APPROVED' else None,
                    approved_at=timezone.now() - timedelta(days=random.randint(1, 30)) if status == 'APPROVED' else None,
                    rejection_reason=self.get_rejection_reason() if status == 'REJECTED' else ''
                )
                
                amendments_created += 1
                
                # Update plan amendment count
                plan.amendment_count = plan.amendments.count()
                plan.is_amended = plan.amendments.filter(status='APPROVED').exists()
                plan.save()
        
        self.stdout.write(self.style.SUCCESS(f'Created {amendments_created} amendments'))

    def get_amendment_justification(self, amendment_type):
        """Generate realistic justification based on amendment type"""
        justifications = {
            'ADD_ITEM': (
                "Due to the expansion of our operations and increased staff capacity, "
                "we need to procure additional equipment that was not anticipated during "
                "the initial planning phase. This item is critical for maintaining operational "
                "efficiency and meeting our departmental objectives for this fiscal year."
            ),
            'REMOVE_ITEM': (
                "After careful review of our operational requirements and budget constraints, "
                "we have determined that this item is no longer a priority for this fiscal year. "
                "The funds can be better utilized for other critical procurement needs that have "
                "emerged since the plan was initially developed."
            ),
            'MODIFY_ITEM': (
                "Based on updated market research and stakeholder consultations, we need to modify "
                "the specifications and quantity of this item to better align with our current needs. "
                "The revised specifications will provide better value for money and ensure the item "
                "meets our operational requirements more effectively."
            ),
            'BUDGET_CHANGE': (
                "A reallocation of budget is necessary due to changes in project priorities and "
                "funding availability. This adjustment will ensure that critical procurement items "
                "have adequate funding while maintaining overall budget discipline within the approved "
                "departmental allocation for this fiscal year."
            ),
            'QUARTER_CHANGE': (
                "The timeline for this procurement needs to be adjusted due to operational considerations "
                "and dependency on other departmental projects. Moving the procurement to a different quarter "
                "will ensure better coordination with project implementation schedules and optimal resource "
                "utilization."
            ),
            'METHOD_CHANGE': (
                "Based on the complexity of the requirement and updated procurement regulations, we need to "
                "change the procurement method to ensure transparency, competitiveness, and value for money. "
                "The revised method will allow for a more thorough evaluation process and attract qualified "
                "suppliers who can meet our specifications."
            )
        }
        
        return justifications.get(amendment_type, "Amendment requested due to operational requirements.")

    def get_amendment_values(self, amendment_type, plan_item):
        """Generate old and new values for amendments"""
        if not plan_item:
            return None, None
        
        if amendment_type == 'MODIFY_ITEM':
            return (
                {
                    'quantity': float(plan_item.quantity),
                    'estimated_cost': float(plan_item.estimated_cost),
                    'specifications': plan_item.specifications
                },
                {
                    'quantity': float(plan_item.quantity) * 1.5,
                    'estimated_cost': float(plan_item.estimated_cost) * 1.3,
                    'specifications': plan_item.specifications + ' - Enhanced specifications'
                }
            )
        elif amendment_type == 'BUDGET_CHANGE':
            return (
                {'budget_code': plan_item.budget.category.code if plan_item.budget else 'N/A'},
                {'budget_code': 'NEW-BUDGET-CODE'}
            )
        elif amendment_type == 'QUARTER_CHANGE':
            quarters = ['Q1', 'Q2', 'Q3', 'Q4']
            old_quarter = plan_item.planned_quarter
            new_quarter = random.choice([q for q in quarters if q != old_quarter])
            return (
                {'quarter': old_quarter},
                {'quarter': new_quarter}
            )
        elif amendment_type == 'METHOD_CHANGE':
            methods = ['OPEN_TENDER', 'RESTRICTED_TENDER', 'RFQ', 'DIRECT_PROCUREMENT']
            old_method = plan_item.procurement_method
            new_method = random.choice([m for m in methods if m != old_method])
            return (
                {'method': old_method},
                {'method': new_method}
            )
        
        return None, None

    def get_rejection_reason(self):
        """Generate sample rejection reasons"""
        reasons = [
            "Insufficient justification provided for the proposed amendment. Please provide more detailed explanation of why this change is necessary.",
            "The proposed budget reallocation exceeds departmental limits. Please revise to align with approved budget ceilings.",
            "The amendment does not align with institutional priorities for this fiscal year. Consider deferring to next planning cycle.",
            "Technical specifications in the amendment are unclear. Please provide more detailed specifications for proper evaluation.",
            "The proposed timeline change conflicts with other departmental procurement activities. Please propose an alternative schedule."
        ]
        return random.choice(reasons)