# Attendeely SaaS Backend API

A modern attendance management system built with FastAPI, PostgreSQL, and JWT authentication.

## 🚀 Features
 
### ✅ Authentication System
- **Signup**: Create admin account with email verification
- **Email Verification**: 6-digit OTP sent via email
- **Login**: JWT-based authentication
- **Resend OTP**: Request new verification code

### ✅ Organization Management
- **Create Organization**: Admin can create organization with name and logo
- **Auto-generated Organization Code**: 8-character unique code (e.g., A7K9X2M4)
- **Logo Upload**: Upload company logo to Cloudinary
- **Get Organization**: Retrieve organization details
- **Update Organization**: Update name and/or logo

### 🔧 Technology Stack
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy 2.0.23
- **Authentication**: JWT (python-jose) + bcrypt
- **Email**: aiosmtplib (async SMTP)
- **Image Storage**: Cloudinary
- **Migrations**: Alembic 1.12.1
- **Server**: Uvicorn with auto-reload

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database
- SMTP email account (Gmail, SendGrid, etc.)
- Cloudinary account (for logo uploads)

## 🛠️ Setup Instructions

### 1. Clone the repository
```bash
cd Attendeely-backend
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```

Edit `.env` file with your credentials:
```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/attendeely_db

# JWT
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (Resend)
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=onboarding@resend.dev
RESEND_FROM_NAME=Attendeely

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# OTP
OTP_EXPIRY_MINUTES=10

# App
APP_NAME=Attendeely
FRONTEND_URL=http://localhost:3000
```

### 5. Run database migrations
```bash
alembic upgrade head
```

### 6. Start the development server
```bash
./dev.sh
# Or manually:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### Authentication (`/api/v1/auth`)

#### POST `/api/v1/auth/signup`
Create a new admin account.

**Request Body:**
```json
{
  "full_name": "John Doe",
  "email": "admin@company.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Account created successfully. Please check your email for the OTP code.",
  "status_code": 201,
  "data": {
    "user_id": 1,
    "full_name": "John Doe",
    "email": "admin@company.com",
    "is_email_verified": false,
    "created_at": "2025-11-10T01:00:00"
  }
}
```

#### POST `/api/v1/auth/verify-otp`
Verify email with OTP code.

**Request Body:**
```json
{
  "email": "admin@company.com",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email verified successfully",
  "status_code": 200,
  "data": {
    "user_id": 1,
    "email": "admin@company.com",
    "is_email_verified": true,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

#### POST `/api/v1/auth/login`
Login with email and password.

**Request Body:**
```json
{
  "email": "admin@company.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "status_code": 200,
  "data": {
    "user_id": 1,
    "full_name": "John Doe",
    "email": "admin@company.com",
    "is_email_verified": true,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

### Organization (`/api/v1/organization`)

#### POST `/api/v1/organization/create`
Create a new organization (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (multipart/form-data):**
- `organization_name` (required): Name of the organization
- `logo` (optional): Company logo image file (JPEG, PNG, WEBP, max 5MB)

**Response:**
```json
{
  "success": true,
  "message": "Organization created successfully",
  "status_code": 201,
  "data": {
    "id": 1,
    "organization_name": "Acme Corporation",
    "organization_code": "A7K9X2M4",
    "logo_url": "https://res.cloudinary.com/...",
    "admin_id": 1,
    "is_active": true,
    "created_at": "2025-11-10T01:00:00"
  }
}
```

#### GET `/api/v1/organization/me`
Get current user's organization (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Organization retrieved successfully",
  "status_code": 200,
  "data": {
    "id": 1,
    "organization_name": "Acme Corporation",
    "organization_code": "A7K9X2M4",
    "logo_url": "https://res.cloudinary.com/...",
    "admin_id": 1,
    "is_active": true,
    "created_at": "2025-11-10T01:00:00"
  }
}
```

#### PUT `/api/v1/organization/update`
Update organization details (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (multipart/form-data):**
- `organization_name` (optional): New organization name
- `logo` (optional): New company logo image file

**Response:**
```json
{
  "success": true,
  "message": "Organization updated successfully",
  "status_code": 200,
  "data": {
    "id": 1,
    "organization_name": "Updated Company Name",
    "organization_code": "A7K9X2M4",
    "logo_url": "https://res.cloudinary.com/...",
    "admin_id": 1,
    "is_active": true,
    "created_at": "2025-11-10T01:00:00"
  }
}
```

## 🔐 Password Requirements

Passwords must meet the following criteria:
- At least 8 characters long
- One lowercase letter
- One uppercase letter
- One number
- One special character (!@#$%^&*(),.?":{}|<>)

## 📧 Email Templates

The system sends beautiful HTML emails for:
1. **Email Verification**: 6-digit OTP code
2. **Welcome Email**: Sent after organization creation
3. **Password Reset**: (Coming soon)

## 🗄️ Database Schema

### Users Table
- `id`: Primary key
- `full_name`: User's full name
- `email`: Unique email address
- `hashed_password`: Bcrypt hashed password
- `is_email_verified`: Email verification status
- `is_active`: Account active status
- `created_at`, `updated_at`: Timestamps

### Organizations Table
- `id`: Primary key
- `organization_name`: Company name
- `organization_code`: Unique 8-character code
- `logo_url`: Cloudinary URL for logo
- `admin_id`: Foreign key to users table
- `is_active`: Organization active status
- `created_at`, `updated_at`: Timestamps

### OTPs Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `otp_code`: 6-digit code
- `is_used`: Usage status
- `expires_at`: Expiration timestamp
- `created_at`: Creation timestamp

## 🧪 Testing with cURL

### 1. Signup
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "admin@company.com",
    "password": "SecurePass123!"
  }'
```

### 2. Verify OTP
```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "otp_code": "123456"
  }'
```

### 3. Create Organization
```bash
curl -X POST http://localhost:8000/api/v1/organization/create \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "organization_name=Acme Corporation" \
  -F "logo=@/path/to/logo.png"
```

## 🚧 Coming Soon

- Employee management
- Attendance tracking (check-in/check-out)
- Reports and analytics
- Role-based access control
- Mobile app integration

## 📝 License

MIT License

## 👥 Contributors

Built with ❤️ by the Attendeely team
