# Attendeely Backend API

A comprehensive attendance management system backend built with FastAPI, PostgreSQL, and modern authentication mechanisms. Attendeely provides organizations with a complete solution for managing employee attendance, leave requests, geofencing, and more.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Authentication](#authentication)
- [Key Features Explained](#key-features-explained)
- [Testing](#testing)
- [Contributing](#contributing)

## ✨ Features

### Admin/Manager Features
- **User Authentication**: Secure signup with email verification via OTP
- **Organization Management**: Create and manage organization profiles with logo upload
- **Employee Management**: Create, update, delete, and view employees with QR code generation
- **Geofencing**: Set location-based attendance boundaries (20m radius)
- **Leave Request Management**: Review, approve, or reject employee leave requests
- **Dashboard**: View pending approvals, filter requests, and audit history
- **Email Notifications**: Receive notifications for new leave requests

### Employee Features
- **Mobile Portal Login**: Persistent login (90-day sessions) using organization code, employee code, and email
- **Attendance Tracking**: Check-in and check-out with automatic hours calculation
- **Location Verification**: Geofence validation for attendance
- **Leave Requests**: Submit permission/leave requests with multiple types (Permission, Leave, Sick, Vacation, Custom)
- **Request Management**: View request status, cancel pending requests
- **Profile Access**: View personal information and attendance history
- **Email Notifications**: Receive notifications for leave request decisions

### System Features
- **Session Management**: Single-device login enforcement
- **Automatic Attendance Adjustment**: Approved leaves automatically adjust attendance records
- **Data Isolation**: Organization-level data segregation
- **QR Code Generation**: Unique QR codes for employee identification
- **Secure File Upload**: Cloudinary integration for image storage
- **Email Service**: Resend API integration for transactional emails
- **In-App Notifications**: Unified notification feed for admins and employees

## 🛠 Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy ORM 2.0.23
- **Authentication**: JWT (JSON Web Tokens) with python-jose
- **Password Hashing**: bcrypt via passlib
- **Migrations**: Alembic 1.12.1
- **File Storage**: Cloudinary 1.36.0
- **Email Service**: Resend 0.8.0
- **Validation**: Pydantic 2.5.0
- **Server**: Uvicorn with ASGI

## 📦 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)
- Virtual environment (recommended)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Attendeely-backend
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   # App Configuration
   APP_NAME=Attendeely
   FRONTEND_URL=http://localhost:3000

   # Database
   DATABASE_URL=postgresql://username:password@localhost:5432/attendeely_db

   # JWT
   SECRET_KEY=your-secret-key-here-minimum-32-characters
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   EMPLOYEE_TOKEN_EXPIRE_DAYS=90

   # Email (Resend)
   RESEND_API_KEY=your-resend-api-key
   RESEND_FROM_EMAIL=onboarding@resend.dev
   RESEND_FROM_NAME=Attendeely

   # Cloudinary
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret

   # OTP
   OTP_EXPIRY_MINUTES=10
   ```

## 🗄 Database Setup

1. **Create PostgreSQL database**
   ```bash
   createdb attendeely_db
   ```

2. **Run migrations**
   ```bash
   alembic upgrade head
   ```

3. **Create a new migration (when needed)**
   ```bash
   alembic revision --autogenerate -m "description_of_changes"
   alembic upgrade head
   ```

## ▶️ Running the Application

### Development Mode
```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided script:
```bash
chmod +x dev.sh
./dev.sh
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication Endpoints (`/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/signup` | Create admin account | No |
| POST | `/auth/verify-otp` | Verify email with OTP | No |
| POST | `/auth/resend-otp` | Resend OTP code | No |
| POST | `/auth/login` | Admin login | No |
| POST | `/auth/forgot-password` | Request password reset | No |
| POST | `/auth/reset-password` | Reset password with token | No |
| GET | `/auth/profile` | Get admin profile | Yes |

### Organization Endpoints (`/organization`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/organization/create` | Create organization | Yes (Admin) |
| GET | `/organization/me` | Get organization details | Yes (Admin) |
| PUT | `/organization/update` | Update organization | Yes (Admin) |
| POST | `/organization/set-geofence` | Set geofence coordinates | Yes (Admin) |

### Employee Management Endpoints (`/employees`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/employees/create` | Create employee | Yes (Admin) |
| GET | `/employees` | List all employees | Yes (Admin) |
| GET | `/employees/{employee_code}` | Get employee by code | Yes (Admin) |
| PUT | `/employees/{employee_code}` | Update employee | Yes (Admin) |
| DELETE | `/employees/{employee_code}` | Delete employee | Yes (Admin) |

### Employee Portal Endpoints (`/employee`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/employee/login` | Employee login | No |
| POST | `/employee/refresh-token` | Refresh access token | Yes (Employee) |
| POST | `/employee/logout` | Employee logout | Yes (Employee) |
| GET | `/employee/profile` | Get employee profile | Yes (Employee) |
| POST | `/employee/attendance/check-in` | Check in | Yes (Employee) |
| POST | `/employee/attendance/check-out` | Check out | Yes (Employee) |
| GET | `/employee/attendance/history` | Get attendance history | Yes (Employee) |
| GET | `/employee/attendance/today` | Get today's attendance | Yes (Employee) |

### Leave Request Endpoints (`/leave-requests`)

#### Employee Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/leave-requests/create` | Create leave request | Yes (Employee) |
| GET | `/leave-requests/my-requests` | Get my requests | Yes (Employee) |
| GET | `/leave-requests/my-requests/{id}` | Get request details | Yes (Employee) |
| PUT | `/leave-requests/my-requests/{id}/cancel` | Cancel request | Yes (Employee) |

#### Admin/Manager Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/leave-requests/pending` | Get pending requests | Yes (Admin) |
| GET | `/leave-requests` | Get all requests (with filters) | Yes (Admin) |
| PUT | `/leave-requests/{id}/approve` | Approve request | Yes (Admin) |
| PUT | `/leave-requests/{id}/reject` | Reject request | Yes (Admin) |

### Dashboard Endpoints (`/dashboard`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/dashboard/overview` | Aggregate KPIs (employees, attendance, payroll, compliance) | Yes (Admin) |
| GET | `/dashboard/daily-attendance` | Time-series data for attendance trend | Yes (Admin) |
| GET | `/dashboard/late-absent` | Daily late vs absent breakdown | Yes (Admin) |

### Payroll Endpoints (`/payroll`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/payroll/process` | Generate or refresh monthly payroll records in real time | Yes (Admin) |
| GET | `/payroll/summary` | Retrieve total, paid, and pending payroll metrics | Yes (Admin) |
| GET | `/payroll/employees` | List payroll entries per employee (supports status filter) | Yes (Admin) |
| PUT | `/payroll/records/{id}` | Update deductions, bonuses, or status for a payroll record | Yes (Admin) |

### Notification Endpoints (`/notifications`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/notifications/admin` | List admin notifications | Yes (Admin) |
| PUT | `/notifications/admin/{id}/read` | Mark an admin notification as read | Yes (Admin) |
| PUT | `/notifications/admin/mark-all-read` | Mark all admin notifications as read | Yes (Admin) |
| GET | `/notifications/employee` | List employee notifications | Yes (Employee) |
| PUT | `/notifications/employee/{id}/read` | Mark an employee notification as read | Yes (Employee) |
| PUT | `/notifications/employee/mark-all-read` | Mark all employee notifications as read | Yes (Employee) |

### Support Endpoints (`/support`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/support/contact` | Send a contact/support message to `support@attendeely.com` | No |

## 📁 Project Structure

```
Attendeely-backend/
├── alembic/                  # Database migrations
│   ├── versions/            # Migration files
│   └── env.py               # Alembic environment config
├── app/
│   ├── api/
│   │   └── v1/              # API version 1 routes
│   │       ├── auth.py      # Authentication endpoints
│   │       ├── employee.py  # Employee management
│   │       ├── employee_auth.py  # Employee portal
│   │       ├── leave_request.py  # Leave requests
│   │       └── organization.py   # Organization management
│   ├── core/
│   │   ├── config.py        # Application settings
│   │   ├── database.py      # Database connection
│   │   ├── dependencies.py # FastAPI dependencies
│   │   └── security.py      # Security utilities
│   ├── models/              # SQLAlchemy models
│   │   ├── attendance.py
│   │   ├── employee.py
│   │   ├── employee_session.py
│   │   ├── leave_request.py
│   │   ├── organization.py
│   │   ├── otp.py
│   │   └── user.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── attendance.py
│   │   ├── auth.py
│   │   ├── employee.py
│   │   ├── leave_request.py
│   │   ├── organization.py
│   │   └── response.py
│   ├── services/            # External service integrations
│   │   ├── cloudinary_service.py
│   │   └── email_service.py
│   ├── utils/               # Utility functions
│   │   ├── generators.py
│   │   ├── geofence.py
│   │   └── otp.py
│   └── main.py              # FastAPI application
├── alembic.ini              # Alembic configuration
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in repo)
└── README.md               # This file
```

## 🔐 Authentication

### Admin Authentication
1. **Signup**: Create account with email and password
2. **OTP Verification**: Verify email with 6-digit OTP
3. **Login**: Receive JWT token (30-minute expiration)
4. **Token Usage**: Include in header: `Authorization: Bearer <token>`

### Employee Authentication
1. **Login**: Use organization code, employee code, and email
2. **Token**: Receive JWT token (90-day expiration for persistent mobile login)
3. **Refresh**: Call `/employee/refresh-token` to extend session
4. **Single Device**: Only one active session per employee

## 🎯 Key Features Explained

### Geofencing
- Admins set geofence coordinates from their device location
- 20-meter radius using Haversine formula
- Employees must be within geofence to check in
- Distance calculation for validation

### Leave Request System
- **Types**: Permission, Leave, Sick, Vacation, Custom
- **Status Flow**: Pending → Approved/Rejected/Cancelled
- **Automatic Adjustment**: Approved full-day leaves create excused attendance records
- **Partial Permissions**: Hours deducted tracked via `hours_deducted` field
- **Notifications**: Email alerts for managers and employees

### Attendance Tracking
- **Check-in**: Once per day, validates geofence
- **Check-out**: Calculates hours worked automatically
- **History**: View all attendance records with filtering
- **Today's Status**: Quick view of current day attendance

### Session Management
- **Single Device**: Login on new device invalidates previous session
- **Persistent Login**: 90-day tokens for mobile employees
- **Token Refresh**: Extend session without re-login
- **Secure Storage**: Token hashing for session tracking

## 🧪 Testing

### Manual Testing
Use the interactive API documentation at `/docs` to test endpoints:
1. Start the server
2. Navigate to http://localhost:8000/docs
3. Use "Authorize" button to add JWT tokens
4. Test endpoints directly from the browser

### Example API Calls

**Admin Signup:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

**Employee Login:**
```bash
curl -X POST "http://localhost:8000/api/v1/employee/login" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_code": "ORG123",
    "employee_code": "EMP456",
    "email": "employee@example.com"
  }'
```

**Check In:**
```bash
curl -X POST "http://localhost:8000/api/v1/employee/attendance/check-in" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.7128,
    "longitude": -74.0060
  }'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `APP_NAME` | Application name | No | Attendeely |
| `FRONTEND_URL` | Frontend application URL | No | http://localhost:3000 |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `SECRET_KEY` | JWT secret key (min 32 chars) | Yes | - |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Admin token expiration | No | 30 |
| `EMPLOYEE_TOKEN_EXPIRE_DAYS` | Employee token expiration | No | 90 |
| `RESEND_API_KEY` | Resend email API key | Yes | - |
| `RESEND_FROM_EMAIL` | Email sender address | No | onboarding@resend.dev |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | Yes | - |
| `CLOUDINARY_API_KEY` | Cloudinary API key | Yes | - |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | Yes | - |
| `OTP_EXPIRY_MINUTES` | OTP expiration time | No | 10 |

## 🚨 Error Handling

All API responses follow a consistent format:

**Success Response:**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "status_code": 200
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Error description",
  "status_code": 400
}
```

## 📝 Database Models

- **User**: Admin users with email verification
- **Organization**: Company/organization details
- **Employee**: Employee profiles with QR codes
- **Attendance**: Check-in/check-out records
- **EmployeeSession**: Active session tracking
- **LeaveRequest**: Leave and permission requests
- **OTP**: Email verification codes

## 🔒 Security Features

- Password hashing with bcrypt
- JWT token-based authentication
- Single-device session enforcement
- Organization-level data isolation
- Geofence validation for attendance
- Secure file upload validation
- SQL injection protection (SQLAlchemy ORM)
- CORS configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 📞 Support

For support, email support@attendeely.com or create an issue in the repository.

## 🎉 Acknowledgments

- FastAPI for the excellent web framework
- SQLAlchemy for robust ORM
- All contributors and maintainers

---

**Version**: 1.0.0  
**Last Updated**: 2024


