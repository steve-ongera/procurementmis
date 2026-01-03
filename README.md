# University Procurement Management Information System (PMIS)

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2%2B-green.svg)](https://www.djangoproject.com/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

A comprehensive, enterprise-grade Procurement Management Information System designed specifically for university environments. This system supports transparent, efficient, and compliant procurement of goods, services, and works while aligning with university governance structures, public/private procurement regulations, budgetary controls, and audit requirements.

---

## 📋 Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Modules Overview](#modules-overview)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)
- [Author](#author)

---

## 🚀 Features

### Core Functionality

- **🔐 Role-Based Access Control (RBAC)**
  - 8 distinct user roles with granular permissions
  - Hierarchical approval workflows
  - Comprehensive audit trails

- **📝 Requisition Management**
  - Online purchase requisition creation
  - Multi-level approval workflows
  - Budget availability checking
  - Real-time status tracking

- **💰 Budget Integration**
  - Commitment accounting
  - Budget consumption tracking
  - Multi-dimensional budget allocation (Department/Project/Grant)
  - Budget reallocation management

- **🏢 Supplier Management**
  - Comprehensive supplier registry
  - Compliance document management
  - Performance evaluation system
  - Blacklisting and suspension handling

- **📊 Tendering & Quotation**
  - RFQ, RFP, and ITB support
  - Multiple procurement methods (Open, Restricted, Direct)
  - Online bid submission
  - Automated evaluation scoring

- **📦 Purchase Order Management**
  - Automated PO generation
  - PO amendments and variations
  - Supplier notifications
  - Status tracking

- **📄 Contract Management**
  - Full contract lifecycle management
  - Milestone tracking
  - Contract variations
  - Expiry alerts

- **🏪 Inventory Management**
  - Multi-store support
  - Goods Received Notes (GRN)
  - Stock movements tracking
  - Asset register integration

- **💳 Invoice & Payment Processing**
  - 3-way matching (Requisition-PO-GRN)
  - Invoice verification workflows
  - Payment tracking
  - Integration-ready for financial systems

- **📈 Reporting & Analytics**
  - Procurement spend analysis
  - Supplier performance reports
  - Budget utilization tracking
  - Compliance reports
  - Export to PDF/Excel

### University-Specific Features

- Research grant procurement
- Emergency procurement handling
- Capital project management
- Donor-funded purchase tracking
- PPRA compliance (Kenyan public universities)
- Sustainability and ethical sourcing support

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  (Web Interface / Mobile App / API Consumers)               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Django  │ │   REST   │ │  Celery  │ │  Redis   │      │
│  │   Web    │ │   API    │ │  Tasks   │ │  Cache   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     Business Logic Layer                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  15 Core Modules with Independent Logic             │   │
│  │  - User Management    - Requisitions                │   │
│  │  - Budget Control     - Tendering                   │   │
│  │  - Supplier Registry  - Purchase Orders             │   │
│  │  - Inventory          - Contracts                   │   │
│  │  - Invoicing          - Reporting                   │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  PostgreSQL  │  │  File Storage│  │   S3/MinIO   │     │
│  │   Database   │  │    (Local)   │  │  (Optional)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Backend Framework**: Django 4.2+
- **Database**: PostgreSQL 13+
- **Cache**: Redis 6+
- **Task Queue**: Celery
- **API**: Django REST Framework
- **Frontend**: React/Vue.js (separate repository)
- **File Storage**: Local/AWS S3/MinIO
- **Email**: SMTP/SendGrid
- **Reporting**: ReportLab, Pandas, Openpyxl

---

## 📥 Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 13 or higher
- Redis 6 or higher
- Virtual environment tool (venv/virtualenv)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/university-pmis.git
cd university-pmis
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Database Setup

```bash
# Create PostgreSQL database
createdb university_pmis

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 6: Load Initial Data (Optional)

```bash
python manage.py loaddata fixtures/initial_data.json
```

### Step 7: Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=university_pmis
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password

# File Storage
MEDIA_ROOT=/path/to/media
MEDIA_URL=/media/

# AWS S3 (Optional)
USE_S3=False
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

### Database Settings

Update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
```

---

## 📚 Modules Overview

### 1. User & Role Management
- Extended User model with university-specific fields
- 8 predefined roles with customizable permissions
- Comprehensive audit logging for all user actions

### 2. Organizational Structure
- Faculty and Department hierarchy
- Support for Academic, Administrative, and Support departments

### 3. Budget Management
- Multi-year budget planning
- Hierarchical budget categories
- Budget types: Departmental, Project, Grant, Capital
- Real-time budget consumption tracking
- Budget reallocation workflows

### 4. Item Catalog
- Master item catalog
- Category hierarchy (Goods, Services, Works)
- Standard pricing and specifications

### 5. Supplier/Vendor Management
- Complete supplier registry
- Compliance document tracking
- Performance evaluation system
- Supplier categorization and rating

### 6. Requisition Management
- Online requisition creation
- Multi-item requisitions
- Supporting document attachments
- Budget validation
- Priority and emergency handling

### 7. Approval Workflow
- Configurable approval thresholds
- Multi-stage approvals (HOD → Faculty → Budget → Procurement)
- Automated routing based on amount
- Approval delegation support

### 8. Tendering & Quotation
- RFQ, RFP, and ITB management
- Multiple procurement methods
- Supplier invitation system
- Online bid submission
- Bid evaluation with scoring matrices

### 9. Purchase Orders
- Automated PO generation from approved requisitions
- Multi-item PO support
- PO amendments and cancellations
- Supplier acknowledgment tracking
- Delivery status monitoring

### 10. Contract Management
- Contract lifecycle management
- Milestone and deliverable tracking
- Contract variations
- Performance bond management
- Renewal and expiry alerts

### 11. Stores & Inventory
- Multi-store/warehouse support
- Goods Received Notes (GRN)
- Stock movements (receipts, issues, transfers, adjustments)
- Stock issue to departments
- Fixed asset register
- Reorder level monitoring

### 12. Invoice & Payment Processing
- Supplier invoice submission
- 3-way matching (Requisition → PO → GRN)
- Invoice verification workflows
- Payment approval and processing
- Payment method tracking

### 13. Reporting & Analytics
- Procurement spend analysis
- Supplier performance reports
- Budget utilization reports
- Departmental spend analysis
- Compliance and audit reports
- Custom report builder

### 14. Notifications & Communication
- In-app notifications
- Email notifications
- SMS notifications (optional)
- Configurable alert rules
- Escalation mechanisms

### 15. System Administration
- System configuration management
- Procurement policy repository
- User management
- Role and permission management
- System logs and monitoring

---

## 🔌 API Documentation

### Authentication

All API endpoints require authentication using JWT tokens.

```bash
# Obtain token
POST /api/token/
{
    "username": "your-username",
    "password": "your-password"
}

# Refresh token
POST /api/token/refresh/
{
    "refresh": "your-refresh-token"
}
```

### Example Endpoints

```bash
# Requisitions
GET    /api/requisitions/              # List all requisitions
POST   /api/requisitions/              # Create requisition
GET    /api/requisitions/{id}/         # Get requisition detail
PUT    /api/requisitions/{id}/         # Update requisition
DELETE /api/requisitions/{id}/         # Delete requisition
POST   /api/requisitions/{id}/submit/  # Submit for approval

# Purchase Orders
GET    /api/purchase-orders/           # List purchase orders
POST   /api/purchase-orders/           # Create PO
GET    /api/purchase-orders/{id}/      # Get PO detail

# Suppliers
GET    /api/suppliers/                 # List suppliers
POST   /api/suppliers/                 # Register supplier
GET    /api/suppliers/{id}/            # Get supplier detail

# Reports
GET    /api/reports/spend-analysis/    # Spend analysis report
GET    /api/reports/budget-utilization/ # Budget utilization
```

Full API documentation available at `/api/docs/` when running the server.

---

## 🧪 Testing

### Run All Tests

```bash
python manage.py test
```

### Run Specific Module Tests

```bash
python manage.py test procurement.tests.test_requisitions
python manage.py test procurement.tests.test_approvals
```

### Run with Coverage

```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML coverage report
```

### Test Data Fixtures

```bash
python manage.py loaddata fixtures/test_data.json
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure proper `SECRET_KEY`
- [ ] Set up production database (PostgreSQL)
- [ ] Configure Redis for caching
- [ ] Set up Celery workers
- [ ] Configure email service
- [ ] Set up file storage (S3/MinIO)
- [ ] Enable HTTPS
- [ ] Configure firewall
- [ ] Set up backup system
- [ ] Configure monitoring (Sentry/Prometheus)
- [ ] Set up logging

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

---

## 🤝 Contributing

This is proprietary software. Contributions are by invitation only.

For authorized contributors:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

**Copyright © 2025 Steve Ongera. All Rights Reserved.**

This software is proprietary and confidential. Unauthorized copying, distribution, modification, or use of this software, via any medium, is strictly prohibited.

**License Type**: Proprietary Commercial License

For licensing inquiries, please contact:

- **Name**: Steve Ongera
- **Email**: steveongera001@gmail.com
- **Phone**: +254 757 790 687

---

## 📞 Support

### Technical Support

For technical support, bug reports, or feature requests:

- **Email**: steveongera001@gmail.com
- **Phone**: +254 757 790 687

### Documentation

- User Manual: `docs/user-manual.pdf`
- Administrator Guide: `docs/admin-guide.pdf`
- API Documentation: `http://your-domain.com/api/docs/`

### Training

Custom training sessions available upon request. Contact us for scheduling.

---

## 👨‍💻 Author

**Steve Ongera**

- Email: steveongera001@gmail.com
- Phone: +254 757 790 687
- GitHub: [@steveongera](https://github.com/steveongera)
- LinkedIn: [Steve Ongera](https://linkedin.com/in/steveongera)

---

## 🙏 Acknowledgments

This system was designed and developed specifically for university procurement environments, incorporating best practices from:

- Public Procurement and Asset Disposal Act (PPRA) - Kenya
- International public procurement standards
- University governance frameworks
- Enterprise resource planning (ERP) systems

---

## 📊 Project Status

- **Version**: 1.0.0
- **Status**: Production Ready
- **Last Updated**: January 2025
- **Minimum Django Version**: 4.2
- **Minimum Python Version**: 3.8

---

## 🔮 Roadmap

### Version 1.1 (Q2 2025)
- [ ] Mobile application (iOS/Android)
- [ ] Advanced analytics dashboard
- [ ] Machine learning for spend prediction
- [ ] Blockchain integration for contract verification

### Version 1.2 (Q3 2025)
- [ ] Multi-tenancy support
- [ ] Integration with popular ERP systems
- [ ] Vendor portal
- [ ] E-procurement marketplace

### Version 2.0 (Q4 2025)
- [ ] AI-powered procurement assistant
- [ ] Automated compliance checking
- [ ] Advanced fraud detection
- [ ] Real-time bidding platform

---

**Built with passion for Universities by Steve Ongera**

---

*For the latest updates and releases, visit our repository or contact the author directly.*