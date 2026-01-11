"""
Django management command to seed users with realistic Kenyan data
File location: pms/management/commands/seed_users.py

Usage: python manage.py seed_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from pms.models import Department

User = get_user_model()

# Realistic Kenyan user data
USERS_DATA = [
    # System Administrator
    {
        'username': 'admin',
        'email': 'admin@university.ac.ke',
        'first_name': 'James',
        'last_name': 'Kamau',
        'role': 'ADMIN',
        'employee_id': 'EMP-2024-0001',
        'phone_number': '+254722123456',
    },
    {
        'username': 'admin1',
        'email': 'admin1@university.ac.ke',
        'first_name': 'Grace',
        'last_name': 'Wanjiku',
        'role': 'ADMIN',
        'employee_id': 'EMP-2024-0002',
        'phone_number': '+254733234567',
    },
    
    # Procurement Officers
    {
        'username': 'pkibui',
        'email': 'peter.kibui@gmail.com',
        'first_name': 'Peter',
        'last_name': 'Kibui',
        'role': 'PROCUREMENT',
        'employee_id': 'EMP-2024-1001',
        'phone_number': '+254720345678',
    },
    {
        'username': 'cmutua',
        'email': 'catherine.mutua@gmail.com',
        'first_name': 'Catherine',
        'last_name': 'Mutua',
        'role': 'PROCUREMENT',
        'employee_id': 'EMP-2024-1002',
        'phone_number': '+254731456789',
    },
    {
        'username': 'domondi',
        'email': 'david.omondi@gmail.com',
        'first_name': 'David',
        'last_name': 'Omondi',
        'role': 'PROCUREMENT',
        'employee_id': 'EMP-2024-1003',
        'phone_number': '+254722567890',
    },
    
    # Finance Officers
    {
        'username': 'mnjeri',
        'email': 'mary.njeri@gmail.com',
        'first_name': 'Mary',
        'last_name': 'Njeri',
        'role': 'FINANCE',
        'employee_id': 'EMP-2024-2001',
        'phone_number': '+254733678901',
    },
    {
        'username': 'jmwangi',
        'email': 'john.mwangi@gmail.com',
        'first_name': 'John',
        'last_name': 'Mwangi',
        'role': 'FINANCE',
        'employee_id': 'EMP-2024-2002',
        'phone_number': '+254720789012',
    },
    {
        'username': 'akilonzo',
        'email': 'alice.kilonzo@gmail.com',
        'first_name': 'Alice',
        'last_name': 'Kilonzo',
        'role': 'FINANCE',
        'employee_id': 'EMP-2024-2003',
        'phone_number': '+254734890123',
    },
    
    # Stores Officers
    {
        'username': 'sokumu',
        'email': 'samuel.okumu@gmail.com',
        'first_name': 'Samuel',
        'last_name': 'Okumu',
        'role': 'STORES',
        'employee_id': 'EMP-2024-3001',
        'phone_number': '+254721901234',
    },
    {
        'username': 'lwambui',
        'email': 'lucy.wambui@gmail.com',
        'first_name': 'Lucy',
        'last_name': 'Wambui',
        'role': 'STORES',
        'employee_id': 'EMP-2024-3002',
        'phone_number': '+254735012345',
    },
    {
        'username': 'vochieng',
        'email': 'victor.ochieng@gmail.com',
        'first_name': 'Victor',
        'last_name': 'Ochieng',
        'role': 'STORES',
        'employee_id': 'EMP-2024-3003',
        'phone_number': '+254722123890',
    },
    
    # Heads of Department (HOD)
    {
        'username': 'drkiprop',
        'email': 'daniel.kiprop@gmail.com',
        'first_name': 'Daniel',
        'last_name': 'Kiprop',
        'role': 'HOD',
        'employee_id': 'EMP-2024-4001',
        'phone_number': '+254733234901',
        'department_code': 'CS',  # Computer Science
    },
    {
        'username': 'profachieng',
        'email': 'prof.achieng@gmail.com',
        'first_name': 'Prof. Elizabeth',
        'last_name': 'Achieng',
        'role': 'HOD',
        'employee_id': 'EMP-2024-4002',
        'phone_number': '+254720345012',
        'department_code': 'MATH',  # Mathematics
    },
    {
        'username': 'drkaranja',
        'email': 'joseph.karanja@gmail.com',
        'first_name': 'Dr. Joseph',
        'last_name': 'Karanja',
        'role': 'HOD',
        'employee_id': 'EMP-2024-4003',
        'phone_number': '+254734456123',
        'department_code': 'PHYS',  # Physics
    },
    {
        'username': 'drmakena',
        'email': 'faith.makena@gmail.com',
        'first_name': 'Dr. Faith',
        'last_name': 'Makena',
        'role': 'HOD',
        'employee_id': 'EMP-2024-4004',
        'phone_number': '+254721567234',
        'department_code': 'CHEM',  # Chemistry
    },
    {
        'username': 'profwekesa',
        'email': 'prof.wekesa@gmail.com',
        'first_name': 'Prof. Michael',
        'last_name': 'Wekesa',
        'role': 'HOD',
        'employee_id': 'EMP-2024-4005',
        'phone_number': '+254735678345',
        'department_code': 'BIO',  # Biology
    },
    
    # Requesting Staff
    {
        'username': 'snyambura',
        'email': 'susan.nyambura@gmail.com',
        'first_name': 'Susan',
        'last_name': 'Nyambura',
        'role': 'STAFF',
        'employee_id': 'EMP-2024-5001',
        'phone_number': '+254722789456',
        'department_code': 'CS',
    },
    {
        'username': 'bokoth',
        'email': 'brian.okoth@gmail.com',
        'first_name': 'Brian',
        'last_name': 'Okoth',
        'role': 'STAFF',
        'employee_id': 'EMP-2024-5002',
        'phone_number': '+254733890567',
        'department_code': 'CS',
    },
    {
        'username': 'rnjoroge',
        'email': 'rachel.njoroge@gmail.com',
        'first_name': 'Rachel',
        'last_name': 'Njoroge',
        'role': 'STAFF',
        'employee_id': 'EMP-2024-5003',
        'phone_number': '+254720901678',
        'department_code': 'MATH',
    },
    {
        'username': 'emusyoka',
        'email': 'eric.musyoka@gmail.com',
        'first_name': 'Eric',
        'last_name': 'Musyoka',
        'role': 'STAFF',
        'employee_id': 'EMP-2024-5004',
        'phone_number': '+254734012789',
        'department_code': 'PHYS',
    },
    {
        'username': 'awanjala',
        'email': 'agnes.wanjala@gmail.com',
        'first_name': 'Agnes',
        'last_name': 'Wanjala',
        'role': 'STAFF',
        'employee_id': 'EMP-2024-5005',
        'phone_number': '+254721123890',
        'department_code': 'CHEM',
    },
    {
        'username': 'pkirui',
        'email': 'paul.kirui@gmail.com',
        'first_name': 'Paul',
        'last_name': 'Kirui',
        'role': 'STAFF',
        'employee_id': 'EMP-2024-5006',
        'phone_number': '+254735234901',
        'department_code': 'BIO',
    },
    {
        'username': 'mnyaga',
        'email': 'mercy.nyaga@gmail.com',
        'first_name': 'Mercy',
        'last_name': 'Nyaga',
        'role': 'STAFF',
        'employee_id': 'EMP-2024-5007',
        'phone_number': '+254722345012',
        'department_code': 'ENG',
    },
    {
        'username': 'komen',
        'email': 'kevin.omen@gmail.com',
        'first_name': 'Kevin',
        'last_name': 'Omen',
        'role': 'STAFF',
        'employee_id': 'EMP-2024-5008',
        'phone_number': '+254733456123',
        'department_code': 'ECO',
    },
    {
        'username': 'cwangari',
        'email': 'christine.wangari@gmail.com',
        'first_name': 'Christine',
        'last_name': 'Wangari',
        'role': 'STAFF',
        'employee_id': 'EMP-2024-5009',
        'phone_number': '+254720567234',
        'department_code': 'LAW',
    },
    {
        'username': 'motieno',
        'email': 'martin.otieno@gmail.com',
        'first_name': 'Martin',
        'last_name': 'Otieno',
        'role': 'STAFF',
        'employee_id': 'EMP-2024-5010',
        'phone_number': '+254734678345',
        'department_code': 'MED',
    },
    
    # Auditors
    {
        'username': 'akamau',
        'email': 'anne.kamau@gmail.com',
        'first_name': 'Anne',
        'last_name': 'Kamau',
        'role': 'AUDITOR',
        'employee_id': 'EMP-2024-6001',
        'phone_number': '+254721789456',
    },
    {
        'username': 'rndirangu',
        'email': 'robert.ndirangu@gmail.com',
        'first_name': 'Robert',
        'last_name': 'Ndirangu',
        'role': 'AUDITOR',
        'employee_id': 'EMP-2024-6002',
        'phone_number': '+254735890567',
    },
    
    # Suppliers (Vendors)
    {
        'username': 'supplier_techmart',
        'email': 'info.techmart@gmail.com',
        'first_name': 'TechMart',
        'last_name': 'Kenya',
        'role': 'SUPPLIER',
        'employee_id': 'SUP-2024-0001',
        'phone_number': '+254722901678',
    },
    {
        'username': 'supplier_officeplus',
        'email': 'sales.officeplus@gmail.com',
        'first_name': 'OfficePlus',
        'last_name': 'Supplies',
        'role': 'SUPPLIER',
        'employee_id': 'SUP-2024-0002',
        'phone_number': '+254733012789',
    },
    {
        'username': 'supplier_labequip',
        'email': 'contact.labequip@gmail.com',
        'first_name': 'LabEquip',
        'last_name': 'Solutions',
        'role': 'SUPPLIER',
        'employee_id': 'SUP-2024-0003',
        'phone_number': '+254720123890',
    },
    {
        'username': 'supplier_furniture',
        'email': 'info.furniture@gmail.com',
        'first_name': 'Modern',
        'last_name': 'Furniture Ltd',
        'role': 'SUPPLIER',
        'employee_id': 'SUP-2024-0004',
        'phone_number': '+254734234901',
    },
    {
        'username': 'supplier_stationery',
        'email': 'orders.stationery@gmail.com',
        'first_name': 'Best',
        'last_name': 'Stationery',
        'role': 'SUPPLIER',
        'employee_id': 'SUP-2024-0005',
        'phone_number': '+254721345012',
    },
]


class Command(BaseCommand):
    help = 'Seeds the database with realistic Kenyan user data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-passwords',
            action='store_true',
            help='Update passwords for all existing users to password123',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("STARTING USER SEEDING PROCESS"))
        self.stdout.write("=" * 70)
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        # Get department mapping
        department_map = {}
        try:
            departments = Department.objects.all()
            for dept in departments:
                department_map[dept.code] = dept
            self.stdout.write(f"\n✓ Found {len(department_map)} departments")
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"\n⚠ Error loading departments: {e}")
            )
            self.stdout.write("  Continuing without department assignments...")
        
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(f"Processing {len(USERS_DATA)} users...")
        self.stdout.write(f"{'='*70}\n")
        
        for user_data in USERS_DATA:
            username = user_data['username']
            
            try:
                # Check if user exists
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': user_data['email'],
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                    }
                )
                
                if created:
                    # New user - set all fields
                    user.role = user_data['role']
                    user.employee_id = user_data['employee_id']
                    user.phone_number = user_data['phone_number']
                    user.is_active = True
                    user.is_staff = True
                    
                    # Set superuser for admins
                    if user_data['role'] == 'ADMIN':
                        user.is_superuser = True
                    
                    # Assign department if provided
                    if 'department_code' in user_data and user_data['department_code'] in department_map:
                        user.department = department_map[user_data['department_code']]
                    
                    # Set password
                    user.set_password('password123')
                    user.save()
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ CREATED: {username:20} | {user_data['first_name']} {user_data['last_name']:15} | "
                            f"{user_data['role']:12} | {user_data['phone_number']}"
                        )
                    )
                    
                else:
                    # Existing user - update fields
                    user.email = user_data['email']
                    user.first_name = user_data['first_name']
                    user.last_name = user_data['last_name']
                    user.role = user_data['role']
                    user.employee_id = user_data['employee_id']
                    user.phone_number = user_data['phone_number']
                    user.is_active = True
                    user.is_staff = True
                    
                    # Set superuser for admins
                    if user_data['role'] == 'ADMIN':
                        user.is_superuser = True
                    
                    # Assign department if provided
                    if 'department_code' in user_data and user_data['department_code'] in department_map:
                        user.department = department_map[user_data['department_code']]
                    
                    # Update password to password123
                    user.set_password('password123')
                    user.save()
                    
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"↻ UPDATED: {username:20} | {user_data['first_name']} {user_data['last_name']:15} | "
                            f"{user_data['role']:12} | Password reset"
                        )
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ ERROR:   {username:20} | {str(e)}")
                )
        
        # Summary
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(self.style.SUCCESS("SEEDING COMPLETED"))
        self.stdout.write(f"{'='*70}")
        self.stdout.write(self.style.SUCCESS(f"✓ Created:  {created_count} users"))
        self.stdout.write(self.style.WARNING(f"↻ Updated:  {updated_count} users"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"✗ Errors:   {error_count} users"))
        self.stdout.write(f"{'='*70}")
        self.stdout.write(f"Total Users in Database: {User.objects.count()}")
        self.stdout.write(f"{'='*70}\n")
        
        # Display login credentials
        self.stdout.write(self.style.SUCCESS("DEFAULT LOGIN CREDENTIALS FOR ALL USERS:"))
        self.stdout.write("-" * 70)
        self.stdout.write(self.style.HTTP_INFO("Password: password123"))
        self.stdout.write("-" * 70)
        self.stdout.write("\nSample Logins:")
        self.stdout.write("  Admin:       username: admin       | password: password123")
        self.stdout.write("  Procurement: username: pkibui      | password: password123")
        self.stdout.write("  Finance:     username: mnjeri      | password: password123")
        self.stdout.write("  HOD:         username: drkiprop    | password: password123")
        self.stdout.write("  Staff:       username: snyambura   | password: password123")
        self.stdout.write("  Auditor:     username: akamau      | password: password123")
        self.stdout.write("  Supplier:    username: supplier_techmart | password: password123")
        self.stdout.write(f"{'='*70}\n")
        
        # Role breakdown
        self.stdout.write(self.style.SUCCESS("USERS BY ROLE:"))
        self.stdout.write("-" * 70)
        roles = User.objects.values('role').distinct()
        for role_dict in roles:
            role = role_dict['role']
            count = User.objects.filter(role=role).count()
            role_display = dict(User.ROLE_CHOICES).get(role, role)
            self.stdout.write(f"  {role_display:25} : {count:3} users")
        self.stdout.write(f"{'='*70}\n")
        
        self.stdout.write(self.style.SUCCESS("✓ User seeding completed successfully!"))