# Sequence Diagram Documentation

## Overview
This document describes the sequence of interactions for key workflows in the Attendeely system, showing the order of operations between actors and components.

## Key Sequence Diagrams

### 1. Admin Signup and Email Verification Flow

**Actors**: Admin, Attendeely API, PostgreSQL, Resend Email Service

```
Admin          Attendeely API        PostgreSQL        Resend Email
  │                  │                    │                  │
  │──POST /auth/signup───────────────────>│                  │
  │                  │                    │                  │
  │                  │──INSERT User──────>│                  │
  │                  │                    │                  │
  │                  │──INSERT OTP───────>│                  │
  │                  │                    │                  │
  │                  │──Send OTP Email──────────────────────>│
  │                  │                    │                  │
  │<──Response (Success)──────────────────│                  │
  │                  │                    │                  │
  │──POST /auth/verify-otp────────────────>│                  │
  │                  │                    │                  │
  │                  │──SELECT OTP───────>│                  │
  │                  │<──OTP Record──────│                  │
  │                  │                    │                  │
  │                  │──UPDATE User──────>│                  │
  │                  │  (is_email_verified=true)            │
  │                  │                    │                  │
  │<──Response (Email Verified)────────────│                  │
```

### 2. Admin Login Flow

**Actors**: Admin, Attendeely API, PostgreSQL

```
Admin          Attendeely API        PostgreSQL
  │                  │                    │
  │──POST /auth/login─────────────────────>│
  │                  │                    │
  │                  │──SELECT User───────>│
  │                  │  (by email)        │
  │                  │<──User Record──────│
  │                  │                    │
  │                  │──Verify Password   │
  │                  │  (bcrypt)          │
  │                  │                    │
  │                  │──Generate JWT Token│
  │                  │                    │
  │<──Response (Access Token)─────────────│
```

### 3. Employee Login Flow

**Actors**: Employee, Attendeely API, PostgreSQL

```
Employee       Attendeely API        PostgreSQL
  │                  │                    │
  │──POST /employee/login─────────────────>│
  │  (org_code, employee_code, email)     │
  │                  │                    │
  │                  │──SELECT Organization>│
  │                  │  (by org_code)     │
  │                  │<──Organization──────│
  │                  │                    │
  │                  │──SELECT Employee───>│
  │                  │  (by code & org_id)│
  │                  │<──Employee Record──│
  │                  │                    │
  │                  │──Invalidate Old Session│
  │                  │──DELETE Session────>│
  │                  │                    │
  │                  │──CREATE New Session>│
  │                  │──INSERT Session───>│
  │                  │                    │
  │                  │──Generate JWT Token│
  │                  │  (90-day expiration)│
  │                  │                    │
  │<──Response (Access Token)─────────────│
```

### 4. Employee Check-In Flow

**Actors**: Employee, Attendeely API, PostgreSQL

```
Employee       Attendeely API        PostgreSQL
  │                  │                    │
  │──POST /employee/attendance/check-in───>│
  │  (latitude, longitude)                 │
  │                  │                    │
  │                  │──SELECT Organization>│
  │                  │<──Organization──────│
  │                  │  (geofence data)   │
  │                  │                    │
  │                  │──Validate Geofence  │
  │                  │  (Haversine formula)│
  │                  │                    │
  │                  │──SELECT Attendance>│
  │                  │  (today's check-in)│
  │                  │<──No Record────────│
  │                  │                    │
  │                  │──INSERT Attendance>│
  │                  │  (CHECK_IN type)   │
  │                  │                    │
  │                  │──CREATE Notification│
  │                  │──INSERT Notification>│
  │                  │                    │
  │<──Response (Check-in Success)──────────│
```

### 5. Employee Check-Out Flow

**Actors**: Employee, Attendeely API, PostgreSQL

```
Employee       Attendeely API        PostgreSQL
  │                  │                    │
  │──POST /employee/attendance/check-out──>│
  │  (latitude, longitude)                │
  │                  │                    │
  │                  │──Validate Geofence │
  │                  │                    │
  │                  │──SELECT Check-in───>│
  │                  │  (today's)         │
  │                  │<──Check-in Record──│
  │                  │                    │
  │                  │──Calculate Hours   │
  │                  │  (check-out - check-in)│
  │                  │                    │
  │                  │──INSERT Attendance>│
  │                  │  (CHECK_OUT type)  │
  │                  │──UPDATE Check-in───>│
  │                  │  (link check-out)  │
  │                  │                    │
  │<──Response (Check-out Success, Hours)─│
```

### 6. Leave Request Creation and Approval Flow

**Actors**: Employee, Admin, Attendeely API, PostgreSQL, Resend Email

```
Employee       Attendeely API        PostgreSQL        Admin          Resend Email
  │                  │                    │              │                  │
  │──POST /leave-requests/create─────────>│              │                  │
  │  (type, dates, reason)               │              │                  │
  │                  │                    │              │                  │
  │                  │──INSERT LeaveRequest>│            │                  │
  │                  │  (status=PENDING)  │              │                  │
  │                  │                    │              │                  │
  │                  │──CREATE Notification│             │                  │
  │                  │──INSERT Notification>│             │                  │
  │                  │                    │              │                  │
  │                  │──Send Email─────────────────────────────────────────>│
  │                  │                    │              │                  │
  │<──Response (Request Created)──────────│              │                  │
  │                  │                    │              │                  │
  │                  │                    │              │                  │
  │                  │                    │──GET /leave-requests/pending───>│
  │                  │                    │              │                  │
  │                  │──SELECT LeaveRequests>│            │                  │
  │                  │<──Pending Requests──│              │                  │
  │                  │                    │              │                  │
  │                  │<──Response──────────│              │                  │
  │                  │                    │              │                  │
  │                  │                    │──PUT /leave-requests/{id}/approve>│
  │                  │                    │              │                  │
  │                  │──SELECT LeaveRequest>│             │                  │
  │                  │──UPDATE Status─────>│              │                  │
  │                  │  (APPROVED)        │              │                  │
  │                  │                    │              │                  │
  │                  │──IF Full Day:      │              │                  │
  │                  │──INSERT Attendance │              │                  │
  │                  │  (excused records) │              │                  │
  │                  │                    │              │                  │
  │                  │──CREATE Notification│             │                  │
  │                  │──INSERT Notification>│             │                  │
  │                  │                    │              │                  │
  │                  │──Send Email─────────────────────────────────────────>│
  │                  │                    │              │                  │
  │                  │<──Response──────────│              │                  │
```

### 7. Subscription Signup and Payment Flow

**Actors**: Admin, Attendeely API, PostgreSQL, Fapshi Payment Gateway

```
Admin          Attendeely API        PostgreSQL        Fapshi
  │                  │                    │              │
  │──POST /subscription/subscribe────────>│              │
  │  (plan_id)                            │              │
  │                  │                    │              │
  │                  │──SELECT Plan───────>│              │
  │                  │<──Plan Details─────│              │
  │                  │                    │              │
  │                  │──SELECT Subscription>│             │
  │                  │<──Existing Sub─────│              │
  │                  │                    │              │
  │                  │──UPDATE Subscription>│             │
  │                  │  (status=PENDING) │              │
  │                  │                    │              │
  │                  │──INSERT Payment───>│              │
  │                  │  (status=INITIATED)│              │
  │                  │                    │              │
  │                  │──Initiate Payment───────────────────────────────────>│
  │                  │  (amount, phone, email, externalId)│              │
  │                  │                    │              │
  │                  │<──Response (transId)─────────────────────────────────│
  │                  │                    │              │
  │                  │──UPDATE Payment───>│              │
  │                  │  (provider_ref=transId)│           │
  │                  │                    │              │
  │<──Response (Payment Initiation)───────│              │
  │  (transId, payment_url)              │              │
  │                  │                    │              │
  │                  │                    │              │
  │                  │                    │              │
  │                  │                    │              │──Payment Webhook──>│
  │                  │                    │              │  (transId, status) │
  │                  │                    │              │                  │
  │                  │──SELECT Payment───>│              │                  │
  │                  │  (by transId)     │              │                  │
  │                  │<──Payment Record──│              │                  │
  │                  │                    │              │                  │
  │                  │──UPDATE Payment───>│              │                  │
  │                  │  (status=SUCCESS)  │              │                  │
  │                  │                    │              │                  │
  │                  │──UPDATE Subscription>│            │                  │
  │                  │  (status=ACTIVE)  │              │                  │
  │                  │──SET billing dates│              │                  │
  │                  │──UPDATE Organization>│             │                  │
  │                  │  (plan)           │              │                  │
  │                  │                    │              │                  │
  │                  │──CREATE Notification│             │                  │
  │                  │──INSERT Notification>│             │                  │
  │                  │                    │              │                  │
  │<──Response (OK)────────────────────────│              │                  │
```

### 8. Payroll Processing Flow

**Actors**: Admin, Attendeely API, PostgreSQL

```
Admin          Attendeely API        PostgreSQL
  │                  │                    │
  │──POST /payroll/process───────────────>│
  │  (year, month)                       │
  │                  │                    │
  │                  │──Validate Plan─────>│
  │                  │  (Standard/Enterprise)│           │
  │                  │                    │
  │                  │──SELECT Employees──>│
  │                  │  (active, org_id)  │
  │                  │<──Employee List────│
  │                  │                    │
  │                  │──FOR EACH Employee:│
  │                  │                    │
  │                  │──SELECT Attendance─>│
  │                  │  (for period)      │
  │                  │<──Attendance Records│
  │                  │                    │
  │                  │──Calculate:        │
  │                  │  - Attendance Days │
  │                  │  - Working Days    │
  │                  │  - Base Salary     │
  │                  │  - Net Pay         │
  │                  │                    │
  │                  │──UPSERT PayrollRecord>│
  │                  │  (unique constraint)│
  │                  │                    │
  │                  │──CREATE Notification│
  │                  │──INSERT Notification>│
  │                  │                    │
  │<──Response (Payroll Processed)─────────│
```

### 9. Dashboard Data Retrieval Flow

**Actors**: Admin, Attendeely API, PostgreSQL

```
Admin          Attendeely API        PostgreSQL
  │                  │                    │
  │──GET /dashboard/overview─────────────>│
  │                  │                    │
  │                  │──SELECT COUNT(Employees)>│
  │                  │<──Employee Count───│
  │                  │                    │
  │                  │──SELECT Attendance Stats>│
  │                  │<──Attendance Data──│
  │                  │                    │
  │                  │──SELECT Payroll Summary>│
  │                  │<──Payroll Data────│
  │                  │                    │
  │                  │──SELECT Compliance Metrics>│
  │                  │<──Compliance Data──│
  │                  │                    │
  │                  │──Aggregate Data   │
  │                  │                    │
  │<──Response (Dashboard KPIs)──────────│
  │  (employees, attendance, payroll, compliance)│
```

### 10. Organization Logo Upload Flow

**Actors**: Admin, Attendeely API, PostgreSQL, Cloudinary

```
Admin          Attendeely API        PostgreSQL        Cloudinary
  │                  │                    │              │
  │──PUT /organization/update────────────>│              │
  │  (multipart/form-data with logo)      │              │
  │                  │                    │              │
  │                  │──Validate File─────│              │
  │                  │  (size, type)      │              │
  │                  │                    │              │
  │                  │──Upload Image──────────────────────────────────────>│
  │                  │                    │              │
  │                  │<──Image URL─────────────────────────────────────────│
  │                  │                    │              │
  │                  │──UPDATE Organization>│             │
  │                  │  (logo_url)        │              │
  │                  │                    │              │
  │<──Response (Organization Updated)────│              │
```

## Sequence Diagram Notes

### Timing Considerations
- **Synchronous Operations**: Most API operations are synchronous and return immediately
- **Asynchronous Operations**: Email sending and payment webhooks are handled asynchronously
- **Database Transactions**: All database operations are wrapped in transactions for consistency

### Error Handling
- Each sequence includes error handling paths (not shown for brevity)
- Errors return appropriate HTTP status codes
- Database rollbacks occur on transaction failures

### Security
- All authenticated endpoints require JWT token validation
- Token validation occurs before any business logic
- Geofence validation occurs before attendance record creation

### Key Patterns
1. **CRUD Operations**: Standard Create-Read-Update-Delete patterns
2. **Validation Before Action**: Always validate before persisting data
3. **Notification Creation**: Many operations trigger notification creation
4. **Status Updates**: State machines for leave requests, subscriptions, payments
5. **Aggregation**: Dashboard endpoints aggregate data from multiple sources

## Additional Sequence Scenarios

### Password Reset Flow
1. Admin requests password reset
2. System generates reset token
3. System sends email with reset link
4. Admin clicks link and provides new password
5. System validates token and updates password

### Subscription Cancellation Flow
1. Admin requests cancellation
2. System updates subscription status to CANCELLED
3. System sets is_active to False
4. System creates notification
5. System returns confirmation

### Notification Marking as Read Flow
1. User requests to mark notification as read
2. System updates notification record
3. System sets read_at timestamp
4. System returns updated notification
