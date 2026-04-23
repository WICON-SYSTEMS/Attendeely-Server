# Use Case Diagram Documentation

## Overview
This document describes all use cases (functionalities) available to different actors in the Attendeely system.

## Actors

### 1. **Admin/Manager**
- Primary user who manages the organization
- Has full control over organization settings, employees, and subscriptions
- Can approve/reject leave requests
- Can process payroll

### 2. **Employee**
- End user who uses the mobile portal
- Checks in/out for attendance
- Submits leave requests
- Views personal information

### 3. **Super Admin**
- System administrator with elevated privileges
- Can manage all organizations
- Has system-wide access

### 4. **System** (Automated)
- Automated processes that run without direct user interaction
- Handles webhooks, notifications, and background tasks

## Use Cases by Actor

### Admin/Manager Use Cases

#### Authentication & Account Management
- **UC-A1**: Sign up for account
  - Admin provides email, password, full name
  - System sends OTP to email
- **UC-A2**: Verify email with OTP
  - Admin enters OTP code
  - System verifies and activates account
- **UC-A3**: Resend OTP
  - Admin requests new OTP
  - System sends new OTP code
- **UC-A4**: Login
  - Admin provides email and password
  - System returns JWT access token
- **UC-A5**: Forgot password
  - Admin requests password reset
  - System sends reset token via email
- **UC-A6**: Reset password
  - Admin provides reset token and new password
  - System updates password
- **UC-A7**: View profile
  - Admin requests profile information
  - System returns admin details

#### Organization Management
- **UC-A8**: Create organization
  - Admin provides organization details (name, industry, country, etc.)
  - System creates organization and generates unique organization code
- **UC-A9**: View organization details
  - Admin requests organization information
  - System returns organization data
- **UC-A10**: Update organization
  - Admin updates organization fields (name, logo, industry, etc.)
  - System updates organization record
- **UC-A11**: Set geofence
  - Admin provides GPS coordinates
  - System sets 300m radius geofence for attendance validation
  - Requires Standard or Enterprise plan

#### Employee Management
- **UC-A12**: Create employee
  - Admin provides employee details (name, email, phone, department, etc.)
  - System creates employee and generates QR code
  - System checks employee limit based on subscription plan
- **UC-A13**: List all employees
  - Admin requests employee list
  - System returns paginated list of employees
- **UC-A14**: Get employee by code
  - Admin provides employee code
  - System returns employee details
- **UC-A15**: Update employee
  - Admin updates employee information
  - System updates employee record
- **UC-A16**: Delete employee
  - Admin requests employee deletion
  - System removes employee and related data

#### Leave Request Management
- **UC-A17**: View pending leave requests
  - Admin requests pending requests
  - System returns list of pending leave requests
- **UC-A18**: View all leave requests (with filters)
  - Admin requests leave requests with optional filters
  - System returns filtered list
- **UC-A19**: Approve leave request
  - Admin approves a leave request
  - System updates request status, creates excused attendance records if full-day
  - System sends notification to employee
- **UC-A20**: Reject leave request
  - Admin rejects a leave request with optional notes
  - System updates request status
  - System sends notification to employee

#### Payroll Management
- **UC-A21**: Process payroll
  - Admin selects month/year for payroll processing
  - System calculates payroll for all employees based on attendance
  - System creates/updates payroll records
  - Requires Standard or Enterprise plan (automated payroll feature)
- **UC-A22**: View payroll summary
  - Admin requests payroll summary
  - System returns total, paid, and pending amounts
- **UC-A23**: View employee payroll list
  - Admin requests payroll entries with optional status filter
  - System returns payroll records per employee
- **UC-A24**: Update payroll record
  - Admin updates deductions, bonuses, or status
  - System updates payroll record

#### Dashboard & Analytics
- **UC-A25**: View dashboard overview
  - Admin requests dashboard data
  - System returns KPIs (employees, attendance, payroll, compliance metrics)
- **UC-A26**: View daily attendance trends
  - Admin requests attendance time-series data
  - System returns daily attendance statistics
- **UC-A27**: View late vs absent breakdown
  - Admin requests daily breakdown
  - System returns late and absent employee counts

#### Subscription Management
- **UC-A28**: View all subscription plans
  - Admin requests available plans
  - System returns plan details (name, price, features)
- **UC-A29**: View current subscription
  - Admin requests current subscription status
  - System returns subscription details, features, employee limits
- **UC-A30**: Subscribe to plan
  - Admin selects a plan
  - System creates pending subscription
  - System initiates payment via Fapshi
  - System returns payment initiation details
- **UC-A31**: Cancel subscription
  - Admin requests cancellation
  - System sets subscription status to CANCELLED
- **UC-A32**: View payment history
  - Admin requests payment history
  - System returns paginated list of payments
- **UC-A33**: View subscription status by transaction ID
  - Admin provides Fapshi transaction ID
  - System returns subscription and payment status

#### Notifications
- **UC-A34**: View notifications
  - Admin requests notifications
  - System returns list of notifications
- **UC-A35**: Mark notification as read
  - Admin marks notification as read
  - System updates notification status
- **UC-A36**: Mark all notifications as read
  - Admin requests bulk read status update
  - System marks all notifications as read

### Employee Use Cases

#### Authentication
- **UC-E1**: Employee login
  - Employee provides organization code, employee code, and email
  - System validates credentials and returns JWT token (90-day expiration)
  - System enforces single-device login
- **UC-E2**: Refresh token
  - Employee requests token refresh
  - System extends session
- **UC-E3**: Employee logout
  - Employee logs out
  - System invalidates session

#### Attendance
- **UC-E4**: Check in
  - Employee provides GPS coordinates
  - System validates geofence (if set)
  - System creates check-in record
  - System validates one check-in per day
- **UC-E5**: Check out
  - Employee provides GPS coordinates
  - System validates geofence (if set)
  - System creates check-out record
  - System calculates hours worked
- **UC-E6**: View attendance history
  - Employee requests attendance records
  - System returns paginated list of attendance records
- **UC-E7**: View today's attendance
  - Employee requests today's attendance status
  - System returns current day attendance record

#### Leave Requests
- **UC-E8**: Create leave request
  - Employee provides request details (type, dates, reason)
  - System creates pending leave request
  - System sends notification to admin
- **UC-E9**: View my leave requests
  - Employee requests own leave requests
  - System returns list of employee's requests
- **UC-E10**: View leave request details
  - Employee requests specific request details
  - System returns request information
- **UC-E11**: Cancel leave request
  - Employee cancels pending request
  - System updates request status to CANCELLED

#### Profile & Information
- **UC-E12**: View profile
  - Employee requests profile information
  - System returns employee details
- **UC-E13**: Submit feedback
  - Employee provides feedback description and optional image
  - System stores feedback

#### Notifications
- **UC-E14**: View notifications
  - Employee requests notifications
  - System returns list of employee notifications
- **UC-E15**: Mark notification as read
  - Employee marks notification as read
  - System updates notification status
- **UC-E16**: Mark all notifications as read
  - Employee requests bulk read status update
  - System marks all notifications as read

### Super Admin Use Cases

- **UC-S1**: View all organizations
  - Super admin requests organization list
  - System returns all organizations
- **UC-S2**: View organization details
  - Super admin requests specific organization
  - System returns organization and subscription details
- **UC-S3**: View system analytics
  - Super admin requests system-wide statistics
  - System returns aggregated data

### System Use Cases (Automated)

- **UC-SYS1**: Process payment webhook
  - Fapshi sends payment status webhook
  - System updates payment status
  - System activates subscription if payment successful
  - System marks subscription as FAILED if payment failed
- **UC-SYS2**: Send email notifications
  - System triggers email sending
  - System sends email via Resend service
- **UC-SYS3**: Create notification records
  - System creates in-app notifications for events
  - System stores notification in database
- **UC-SYS4**: Auto-expire subscriptions
  - System checks subscription end dates
  - System updates expired subscriptions to EXPIRED status
- **UC-SYS5**: Auto-adjust attendance for approved leaves
  - System creates excused attendance records for approved full-day leaves

## Use Case Relationships

### Include Relationships
- **UC-A12** includes **Check Employee Limit** (before creating employee)
- **UC-A19** includes **Create Excused Attendance** (for full-day approved leaves)
- **UC-A21** includes **Calculate Attendance Days** (for payroll processing)
- **UC-E4** includes **Validate Geofence** (before check-in)
- **UC-E5** includes **Validate Geofence** (before check-out)
- **UC-E4** includes **Validate Single Check-in** (one per day)
- **UC-E8** includes **Send Notification to Admin** (after creating request)

### Extend Relationships
- **UC-A30** extends **Payment Processing** (if payment gateway available)
- **UC-E1** extends **Single Device Validation** (enforce one active session)

## Use Case Diagram Representation (Textual)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Admin/Manager                            │
└─────────────────────────────────────────────────────────────────┘
        │
        ├─── Authentication & Account
        │    ├── Sign Up
        │    ├── Verify Email (OTP)
        │    ├── Login
        │    ├── Forgot Password
        │    └── View Profile
        │
        ├─── Organization Management
        │    ├── Create Organization
        │    ├── View Organization
        │    ├── Update Organization
        │    └── Set Geofence
        │
        ├─── Employee Management
        │    ├── Create Employee
        │    ├── List Employees
        │    ├── Update Employee
        │    └── Delete Employee
        │
        ├─── Leave Request Management
        │    ├── View Pending Requests
        │    ├── Approve Request
        │    └── Reject Request
        │
        ├─── Payroll Management
        │    ├── Process Payroll
        │    ├── View Payroll Summary
        │    └── Update Payroll Record
        │
        ├─── Dashboard & Analytics
        │    ├── View Dashboard Overview
        │    ├── View Attendance Trends
        │    └── View Late/Absent Breakdown
        │
        ├─── Subscription Management
        │    ├── View Plans
        │    ├── Subscribe to Plan
        │    ├── Cancel Subscription
        │    └── View Payment History
        │
        └─── Notifications
             ├── View Notifications
             └── Mark as Read

┌─────────────────────────────────────────────────────────────────┐
│                            Employee                              │
└─────────────────────────────────────────────────────────────────┘
        │
        ├─── Authentication
        │    ├── Login
        │    ├── Refresh Token
        │    └── Logout
        │
        ├─── Attendance
        │    ├── Check In
        │    ├── Check Out
        │    ├── View Attendance History
        │    └── View Today's Attendance
        │
        ├─── Leave Requests
        │    ├── Create Leave Request
        │    ├── View My Requests
        │    └── Cancel Request
        │
        ├─── Profile
        │    ├── View Profile
        │    └── Submit Feedback
        │
        └─── Notifications
             ├── View Notifications
             └── Mark as Read

┌─────────────────────────────────────────────────────────────────┐
│                          Super Admin                            │
└─────────────────────────────────────────────────────────────────┘
        │
        ├─── View All Organizations
        ├─── View Organization Details
        └─── View System Analytics

┌─────────────────────────────────────────────────────────────────┐
│                            System                               │
└─────────────────────────────────────────────────────────────────┘
        │
        ├─── Process Payment Webhook
        ├─── Send Email Notifications
        ├─── Create Notification Records
        ├─── Auto-expire Subscriptions
        └─── Auto-adjust Attendance
```

## Notes

- Use cases marked with specific plan requirements (e.g., geofencing requires Standard/Enterprise) are enforced at the API level
- Some use cases are automatically triggered by system events (webhooks, scheduled tasks)
- Employee use cases are designed for mobile portal access with persistent sessions
- Admin use cases support web-based management interface
