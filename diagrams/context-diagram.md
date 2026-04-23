# Context Diagram Documentation

## Overview
The Context Diagram shows Attendeely as the central system and its interactions with external entities (actors, systems, and services).

## System Boundary
**Attendeely Backend API** - The core attendance management system

## External Entities

### 1. **Admin/Manager**
- **Type**: Human Actor
- **Interactions**:
  - Signs up and authenticates
  - Creates and manages organization
  - Manages employees (CRUD operations)
  - Sets geofence boundaries
  - Reviews and approves/rejects leave requests
  - Views dashboard analytics
  - Processes payroll
  - Manages subscription plans
  - Views notifications

### 2. **Employee**
- **Type**: Human Actor
- **Interactions**:
  - Logs into mobile portal
  - Checks in/out for attendance
  - Submits leave/permission requests
  - Views attendance history
  - Views profile information
  - Views notifications
  - Submits feedback

### 3. **Frontend Application**
- **Type**: External System
- **Interactions**:
  - Sends HTTP requests to API endpoints
  - Receives JSON responses
  - Handles authentication tokens
  - Displays data to users

### 4. **PostgreSQL Database**
- **Type**: External System (Data Store)
- **Interactions**:
  - Stores all application data
  - Provides data persistence
  - Handles transactions and queries
  - Manages relationships between entities

### 5. **Fapshi Payment Gateway**
- **Type**: External Service
- **Interactions**:
  - Receives payment initiation requests
  - Processes mobile money payments
  - Sends payment status webhooks
  - Provides transaction IDs

### 6. **Cloudinary**
- **Type**: External Service
- **Interactions**:
  - Stores organization logos
  - Stores employee photos
  - Provides image URLs
  - Handles image transformations

### 7. **Resend Email Service**
- **Type**: External Service
- **Interactions**:
  - Sends OTP verification emails
  - Sends password reset emails
  - Sends leave request notifications
  - Sends general notifications

### 8. **Super Admin**
- **Type**: Human Actor (Special Role)
- **Interactions**:
  - Manages all organizations
  - Views system-wide analytics
  - Performs administrative operations

## Data Flows

### Admin → Attendeely
- Authentication credentials
- Organization data
- Employee data
- Geofence coordinates
- Leave request decisions
- Payroll data
- Subscription selections

### Attendeely → Admin
- Authentication tokens
- Organization details
- Employee lists
- Dashboard analytics
- Leave requests
- Payroll summaries
- Subscription status

### Employee → Attendeely
- Login credentials (org code, employee code, email)
- Check-in/check-out requests with GPS coordinates
- Leave request submissions
- Feedback submissions

### Attendeely → Employee
- Authentication tokens
- Attendance records
- Leave request status
- Notifications
- Profile information

### Attendeely → PostgreSQL
- SQL queries (SELECT, INSERT, UPDATE, DELETE)
- Transaction commits
- Relationship queries

### PostgreSQL → Attendeely
- Query results
- Stored data
- Relationship data

### Attendeely → Fapshi
- Payment initiation requests (amount, phone, email, externalId)
- Transaction references

### Fapshi → Attendeely
- Payment status webhooks (transId, status, externalId)
- Transaction confirmations

### Attendeely → Cloudinary
- Image uploads (logos, photos)
- Image deletion requests

### Cloudinary → Attendeely
- Image URLs
- Upload confirmations

### Attendeely → Resend
- Email sending requests (to, subject, HTML content)
- OTP codes

### Resend → Attendeely
- Email delivery confirmations
- Email IDs

## Diagram Representation (Textual)

```
                    ┌─────────────────────────────────┐
                    │                                 │
                    │   Attendeely Backend API        │
                    │   (FastAPI Application)         │
                    │                                 │
                    │  ┌──────────────────────────┐  │
                    │  │   API Endpoints          │  │
                    │  │   - /auth                │  │
                    │  │   - /organization        │  │
                    │  │   - /employees           │  │
                    │  │   - /employee            │  │
                    │  │   - /leave-requests      │  │
                    │  │   - /payroll             │  │
                    │  │   - /subscription        │  │
                    │  │   - /dashboard           │  │
                    │  │   - /notifications       │  │
                    │  └──────────────────────────┘  │
                    │                                 │
                    └─────────────────────────────────┘
                              │         │         │
                              │         │         │
        ┌─────────────────────┼─────────┼─────────┼─────────────────────┐
        │                     │         │         │                     │
        │                     │         │         │                     │
    ┌───▼───┐          ┌──────▼──────┐ │  ┌──────▼──────┐      ┌───────▼──────┐
    │ Admin │          │  Employee   │ │  │  Frontend    │      │  Super Admin │
    │       │          │             │ │  │  Application │      │              │
    └───┬───┘          └──────┬──────┘ │  └──────┬──────┘      └───────┬──────┘
        │                     │         │         │                     │
        └─────────────────────┼─────────┼─────────┼─────────────────────┘
                              │         │         │
                    ┌─────────▼─────────▼─────────▼─────────┐
                    │                                         │
                    │      PostgreSQL Database               │
                    │      (Data Persistence)                │
                    │                                         │
                    └─────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    ┌───▼──────┐        ┌─────▼──────┐      ┌──────▼──────┐
    │ Fapshi   │        │ Cloudinary  │      │   Resend    │
    │ Payment  │        │   Storage   │      │   Email     │
    │ Gateway  │        │             │      │   Service   │
    └──────────┘        └─────────────┘      └─────────────┘
```

## Key Interactions Summary

1. **Authentication Flow**: Admin/Employee → Attendeely → PostgreSQL (verify credentials)
2. **Payment Flow**: Admin → Attendeely → Fapshi → Attendeely (webhook) → PostgreSQL
3. **File Upload Flow**: Admin → Attendeely → Cloudinary → Attendeely → PostgreSQL
4. **Email Flow**: Attendeely → Resend → User Email
5. **Data Query Flow**: Frontend → Attendeely → PostgreSQL → Attendeely → Frontend

## Security Boundaries

- **Authentication**: All API requests (except public endpoints) require JWT tokens
- **Authorization**: Role-based access control (Admin vs Employee)
- **Data Isolation**: Organization-level data segregation
- **External Services**: API keys and credentials stored securely in environment variables

## Notes

- The system acts as a RESTful API, receiving HTTP requests and returning JSON responses
- All external service integrations are asynchronous where possible
- Database operations use SQLAlchemy ORM for abstraction
- Payment webhooks are received via POST endpoints
- Image uploads are handled via multipart/form-data
