import random
from decimal import Decimal
from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from pms.models import (
    Requisition,
    RequisitionItem,
    RequisitionApproval,
    Department,
    Budget,
    Item
)

from django.contrib.auth import get_user_model

User = get_user_model()


KENYAN_REQUISITION_TITLES = [
    "Procurement of Office Stationery",
    "Supply of Laptop Computers",
    "Laboratory Chemicals Purchase",
    "Campus Network Equipment Acquisition",
    "Furniture for Lecture Halls",
    "Procurement of Cleaning Services",
    "Electrical Maintenance Materials",
    "Supply of Examination Printing Services",
    "Procurement of Library Books",
    "Catering Services for University Events",
]

KENYAN_ITEMS = [
    # ================= ICT & COMPUTING =================
    ("HP ProBook Laptop", "Intel Core i5, 8GB RAM, 512GB SSD"),
    ("Dell Latitude Laptop", "Intel Core i7, 16GB RAM, 1TB SSD"),
    ("Desktop Computers", "Intel Core i7, 16GB RAM, 24-inch monitor"),
    ("All-in-One Desktop PC", "Intel i5, 8GB RAM"),
    ("Laser Printer", "Network enabled, duplex printing"),
    ("Photocopier Machine", "High-speed multifunction copier"),
    ("UPS Power Backup", "3KVA online UPS"),
    ("Server Rack Cabinet", "42U rack with cooling fans"),
    ("Network Cabling", "CAT6 structured cabling"),
    ("Cisco Network Switch", "24-Port Gigabit managed switch"),
    ("Wireless Access Points", "Dual-band enterprise Wi-Fi"),
    ("Firewall Appliance", "Enterprise-grade network firewall"),

    # ================= OFFICE & ADMIN =================
    ("A4 Printing Paper", "80gsm white paper"),
    ("Office Chairs", "Ergonomic adjustable chairs"),
    ("Office Desks", "Wooden executive office desks"),
    ("Filing Cabinets", "Metal lockable cabinets"),
    ("Stationery Supplies", "Pens, notebooks, staplers"),
    ("Whiteboards", "Magnetic whiteboard 6ft x 4ft"),
    ("Notice Boards", "Cork bulletin boards"),
    ("Shredding Machine", "Heavy-duty document shredder"),

    # ================= TEACHING & CLASSROOM =================
    ("Projector", "Full HD multimedia projector"),
    ("Interactive Smart Board", "Touch-enabled digital board"),
    ("Lecture Hall Sound System", "PA system with microphones"),
    ("Student Desks", "Lecture hall seating desks"),
    ("Examination Answer Booklets", "University branded exam booklets"),
    ("Lecture Hall Curtains", "Fire-resistant fabric curtains"),

    # ================= LABORATORY & RESEARCH =================
    ("Laboratory Reagents", "Analytical grade chemicals"),
    ("Laboratory Glassware", "Beakers, flasks, test tubes"),
    ("Microscopes", "Binocular laboratory microscopes"),
    ("Centrifuge Machine", "High-speed laboratory centrifuge"),
    ("Fume Hood", "Laboratory safety fume hood"),
    ("Autoclave Machine", "Steam sterilization unit"),
    ("Lab Safety Equipment", "Gloves, goggles, lab coats"),

    # ================= LIBRARY & ACADEMIC =================
    ("Library Textbooks", "Latest academic editions"),
    ("Academic Journals Subscription", "Online research journals"),
    ("Library Shelving", "Metal library shelves"),
    ("E-Books Subscription", "Digital academic resources"),
    ("RFID Library System", "Book tracking and access control"),

    # ================= FACILITIES & MAINTENANCE =================
    ("Cleaning Detergents", "Industrial-grade detergents"),
    ("Floor Polishing Machine", "Commercial floor polisher"),
    ("Electrical Cables", "High-quality copper cables"),
    ("LED Lighting Fixtures", "Energy-saving LED lights"),
    ("Plumbing Materials", "Pipes, valves, fittings"),
    ("Water Storage Tanks", "10,000-litre plastic tanks"),
    ("Generator", "50KVA standby generator"),
    ("Solar Power System", "Solar panels with inverter"),

    # ================= SECURITY & SAFETY =================
    ("CCTV Cameras", "HD surveillance cameras"),
    ("Access Control System", "Biometric door access"),
    ("Fire Extinguishers", "CO2 and powder extinguishers"),
    ("Smoke Detectors", "Fire alarm smoke sensors"),
    ("Security Barriers", "Boom gates and bollards"),

    # ================= HEALTH & MEDICAL =================
    ("First Aid Kits", "Fully stocked first aid kits"),
    ("Medical Examination Beds", "Clinic examination beds"),
    ("Thermometers", "Digital infrared thermometers"),
    ("Blood Pressure Monitors", "Automatic BP machines"),

    # ================= CATERING & HOSPITALITY =================
    ("Catering Utensils", "Industrial kitchen utensils"),
    ("Food Warmers", "Electric food warmers"),
    ("Industrial Gas Cookers", "Large-scale kitchen cookers"),
    ("Refrigerators", "Commercial grade fridges"),
    ("Water Dispensers", "Hot and cold water dispensers"),

    # ================= TRANSPORT & LOGISTICS =================
    ("University Bus", "50-seater passenger bus"),
    ("Service Vehicles", "Pickup trucks for maintenance"),
    ("Motorcycles", "Campus transport motorcycles"),
    ("Vehicle Tyres", "All-terrain vehicle tyres"),

    # ================= EVENTS & SERVICES =================
    ("Tent Hire Services", "Large event tents"),
    ("Public Address System Hire", "Event PA systems"),
    ("Graduation Gowns", "University graduation attire"),
    ("Event Branding Materials", "Banners and signage"),
]



class Command(BaseCommand):
    help = "Seed requisitions, items, and approvals for past 3 years"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Seeding Requisitions (3 years historical data)...")

        users = list(User.objects.all())
        departments = list(Department.objects.all())
        budgets = list(Budget.objects.all())
        items = list(Item.objects.all())

        if not users or not departments or not budgets:
            self.stdout.write(self.style.ERROR(
                "❌ Users, Departments, or Budgets missing. Seed them first."
            ))
            return

        today = timezone.now().date()
        start_date = today - timedelta(days=365 * 3)

        requisitions_created = 0

        current_date = start_date

        while current_date <= today:
            for _ in range(random.randint(2, 6)):  # monthly volume
                department = random.choice(departments)
                user = random.choice(users)
                budget = random.choice(budgets)

                created_at = timezone.make_aware(
                    timezone.datetime.combine(current_date, timezone.datetime.min.time())
                )

                estimated_amount = Decimal(random.randint(50_000, 3_000_000))

                requisition = Requisition.objects.create(
                    title=random.choice(KENYAN_REQUISITION_TITLES),
                    department=department,
                    budget=budget,
                    requested_by=user,
                    status=random.choice([
                        "APPROVED",
                        "PROCUREMENT_APPROVED",
                        "BUDGET_APPROVED",
                        "REJECTED"
                    ]),
                    priority=random.choice(["LOW", "MEDIUM", "HIGH"]),
                    justification="Procurement required for smooth university operations.",
                    estimated_amount=estimated_amount,
                    required_date=current_date + timedelta(days=14),
                    is_emergency=random.choice([False, False, True]),
                    created_at=created_at,
                    submitted_at=created_at + timedelta(days=1),
                )

                # Override auto timestamps
                Requisition.objects.filter(id=requisition.id).update(
                    created_at=created_at,
                    submitted_at=created_at + timedelta(days=1),
                )

                # Create line items
                for _ in range(random.randint(1, 4)):
                    item_name, specs = random.choice(KENYAN_ITEMS)

                    RequisitionItem.objects.create(
                        requisition=requisition,
                        item=random.choice(items) if items else None,
                        item_description=item_name,
                        specifications=specs,
                        quantity=Decimal(random.randint(1, 20)),
                        unit_of_measure="Units",
                        estimated_unit_price=Decimal(random.randint(5_000, 250_000)),
                        notes="Estimated market price based on local suppliers",
                    )

                # Approval workflow
                approval_sequence = [
                    "HOD",
                    "FACULTY",
                    "BUDGET",
                    "PROCUREMENT",
                    "FINAL"
                ]

                for index, stage in enumerate(approval_sequence, start=1):
                    RequisitionApproval.objects.create(
                        requisition=requisition,
                        approval_stage=stage,
                        approver=random.choice(users),
                        status=random.choice(["APPROVED", "APPROVED", "REJECTED"]),
                        comments="Reviewed and processed.",
                        approval_date=created_at + timedelta(days=index),
                        sequence=index,
                        created_at=created_at + timedelta(days=index),
                    )

                requisitions_created += 1

            current_date += timedelta(days=30)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Successfully seeded {requisitions_created} requisitions covering 3 years"
        ))
