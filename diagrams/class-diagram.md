# Class Diagram Documentation

## Overview
This document describes the database models (classes) and their relationships in the Attendeely system. These models are implemented using SQLAlchemy ORM.

## Core Models

### 1. User Model

**Table**: `users`

**Attributes**:
- `id` (Integer, Primary Key)
- `full_name` (String)
- `email` (String, Unique, Indexed)
- `hashed_password` (String)
- `is_super_admin` (Boolean, Default: False)
- `is_email_verified` (Boolean, Default: False)
- `is_active` (Boolean, Default: True)
- `reset_token` (String, Nullable)
- `reset_token_expiry` (DateTime, Nullable)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Relationships**:
- `otps` → One-to-Many → OTP
- `organization` → One-to-One → Organization
- `notifications` → One-to-Many → Notification
- `feedback` → One-to-Many → Feedback
- `payments` → One-to-Many → Payment

**Description**: Represents admin users who manage organizations. Can be regular admin or super admin.

---

### 2. Organization Model

**Table**: `organizations`

**Attributes**:
- `id` (Integer, Primary Key)
- `organization_name` (String, Indexed)
- `organization_code` (String(8), Unique, Indexed)
- `logo_url` (String, Nullable)
- `industry` (String)
- `employees_count_range` (String)
- `country` (String)
- `currency` (String)
- `plan` (String, Default: "Free Trial")
- `admin_id` (Integer, Foreign Key → users.id)
- `geofence_latitude` (Numeric(10,8), Nullable)
- `geofence_longitude` (Numeric(11,8), Nullable)
- `geofence_radius` (Numeric(10,2), Nullable)
- `is_active` (Boolean, Default: True)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Relationships**:
- `admin` → Many-to-One → User
- `employees` → One-to-Many → Employee
- `payroll_records` → One-to-Many → PayrollRecord
- `subscription` → One-to-One → Subscription

**Description**: Represents a company or organization using the system. Each organization has one admin and can have multiple employees.

---

### 3. Employee Model

**Table**: `employees`

**Attributes**:
- `id` (UUID, Primary Key)
- `full_name` (String)
- `email` (String, Indexed)
- `phone_number` (String)
- `gender` (Enum: MALE, FEMALE, OTHER)
- `date_of_birth` (Date, Nullable)
- `department` (String)
- `job_title` (String)
- `work_type` (Enum: FULL_TIME, PART_TIME, CONTRACT, INTERN)
- `joining_date` (Date)
- `role` (Enum: ADMIN, HR_MANAGER, STAFF)
- `photo_url` (String, Nullable)
- `shift` (String)
- `salary_per_hour` (Numeric(10,2), Nullable)
- `employee_code` (String(10), Indexed)
- `qr_code` (String(64), Unique, Indexed)
- `organization_id` (Integer, Foreign Key → organizations.id)
- `is_active` (Boolean, Default: True)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Unique Constraint**: (`employee_code`, `organization_id`)

**Relationships**:
- `organization` → Many-to-One → Organization
- `attendances` → One-to-Many → Attendance
- `sessions` → One-to-Many → EmployeeSession
- `leave_requests` → One-to-Many → LeaveRequest
- `notifications` → One-to-Many → Notification
- `payroll_records` → One-to-Many → PayrollRecord
- `feedback` → One-to-Many → Feedback

**Description**: Represents an employee within an organization. Each employee has a unique code within their organization and a QR code for identification.

---

### 4. Attendance Model

**Table**: `attendances`

**Attributes**:
- `id` (UUID, Primary Key)
- `employee_id` (UUID, Foreign Key → employees.id, Indexed)
- `attendance_type` (Enum: CHECK_IN, CHECK_OUT)
- `timestamp` (DateTime, Indexed)
- `location_latitude` (String, Nullable)
- `location_longitude` (String, Nullable)
- `notes` (String, Nullable)
- `hours_worked` (Numeric(5,2), Nullable)
- `check_in_id` (UUID, Foreign Key → attendances.id, Nullable)
- `created_at` (DateTime)

**Relationships**:
- `employee` → Many-to-One → Employee
- `check_in_record` → Self-referential (One-to-One)

**Description**: Represents attendance records (check-in/check-out). Check-out records reference their corresponding check-in record.

---

### 5. EmployeeSession Model

**Table**: `employee_sessions`

**Attributes**:
- `id` (UUID, Primary Key)
- `employee_id` (UUID, Foreign Key → employees.id, Indexed)
- `token_hash` (String, Unique, Indexed)
- `is_active` (Boolean, Default: True)
- `created_at` (DateTime)
- `expires_at` (DateTime, Indexed)

**Relationships**:
- `employee` → Many-to-One → Employee

**Description**: Tracks active employee sessions for single-device login enforcement. Stores hashed JWT tokens.

---

### 6. LeaveRequest Model

**Table**: `leave_requests`

**Attributes**:
- `id` (UUID, Primary Key)
- `employee_id` (UUID, Foreign Key → employees.id, Indexed)
- `request_type` (Enum: PERMISSION, LEAVE, SICK, VACATION, CUSTOM)
- `custom_type` (String, Nullable)
- `start_date` (DateTime, Indexed)
- `end_date` (DateTime, Indexed)
- `reason` (Text)
- `status` (Enum: PENDING, APPROVED, REJECTED, CANCELLED, Indexed)
- `reviewer_id` (Integer, Foreign Key → users.id, Nullable)
- `review_time` (DateTime, Nullable)
- `review_notes` (Text, Nullable)
- `is_full_day` (Boolean, Default: True)
- `hours_deducted` (Numeric(5,2), Nullable)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Relationships**:
- `employee` → Many-to-One → Employee
- `reviewer` → Many-to-One → User

**Description**: Represents leave and permission requests submitted by employees and reviewed by admins.

---

### 7. PayrollRecord Model

**Table**: `payroll_records`

**Attributes**:
- `id` (UUID, Primary Key)
- `organization_id` (Integer, Foreign Key → organizations.id, Indexed)
- `employee_id` (UUID, Foreign Key → employees.id, Indexed)
- `period_year` (Integer, Indexed)
- `period_month` (Integer, Indexed)
- `base_salary` (Numeric(12,2), Default: 0.00)
- `attendance_days` (Integer, Default: 0)
- `working_days` (Integer, Default: 0)
- `deductions` (Numeric(12,2), Default: 0.00)
- `bonus` (Numeric(12,2), Default: 0.00)
- `net_pay` (Numeric(12,2), Default: 0.00)
- `status` (Enum: PENDING, PAID, Indexed)
- `processed_at` (DateTime, Nullable)
- `notes` (String, Nullable)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Unique Constraint**: (`employee_id`, `period_year`, `period_month`)

**Index**: (`organization_id`, `period_year`, `period_month`)

**Relationships**:
- `organization` → Many-to-One → Organization
- `employee` → Many-to-One → Employee

**Description**: Represents monthly payroll records for employees. One record per employee per month.

---

### 8. SubscriptionPlan Model

**Table**: `subscription_plans`

**Attributes**:
- `id` (Integer, Primary Key)
- `name` (String(50), Unique, Indexed)
- `amount` (Numeric(10,2))
- `currency` (String(3), Default: "XAF")
- `interval` (String(20), Default: "monthly")
- `is_active` (Boolean, Default: True, Indexed)
- `description` (String(500), Nullable)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Relationships**:
- `subscriptions` → One-to-Many → Subscription

**Description**: Stores available subscription plans (Free, Standard, Enterprise) with pricing and details.

---

### 9. Subscription Model

**Table**: `subscriptions`

**Attributes**:
- `id` (Integer, Primary Key)
- `organization_id` (Integer, Foreign Key → organizations.id, Unique, Indexed)
- `plan_id` (Integer, Foreign Key → subscription_plans.id, Indexed)
- `plan` (Enum: Free, Standard, Enterprise, Nullable) [Legacy field]
- `status` (Enum: PENDING, ACTIVE, TRIAL, PAST_DUE, EXPIRED, CANCELLED, FAILED, Indexed)
- `start_date` (DateTime, Indexed, Nullable)
- `next_billing_date` (DateTime, Indexed, Nullable)
- `last_paid_date` (DateTime, Nullable)
- `grace_ends_at` (DateTime, Nullable)
- `trial_start_date` (DateTime, Nullable)
- `trial_end_date` (DateTime, Nullable)
- `subscription_start_date` (DateTime, Nullable)
- `subscription_end_date` (DateTime, Nullable)
- `monthly_price` (Numeric(10,2), Nullable)
- `is_active` (Boolean, Default: True, Indexed)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Relationships**:
- `organization` → One-to-One → Organization
- `plan_details` → Many-to-One → SubscriptionPlan
- `payments` → One-to-Many → Payment

**Description**: Represents an organization's subscription. Tracks subscription status, billing dates, and payment history.

---

### 10. Payment Model

**Table**: `payments`

**Attributes**:
- `id` (Integer, Primary Key)
- `user_id` (Integer, Foreign Key → users.id, Indexed)
- `subscription_id` (Integer, Foreign Key → subscriptions.id, Indexed)
- `amount` (Numeric(10,2))
- `currency` (String(3), Default: "XAF")
- `status` (Enum: INITIATED, SUCCESS, FAILED, Indexed)
- `provider` (Enum: FAPSHI, Indexed)
- `provider_ref` (String(255), Unique, Indexed)
- `provider_response` (String, Nullable)
- `created_at` (DateTime, Indexed)
- `updated_at` (DateTime)

**Indexes**:
- (`user_id`, `subscription_id`)
- (`status`, `created_at`)

**Relationships**:
- `user` → Many-to-One → User
- `subscription` → Many-to-One → Subscription

**Description**: Tracks payment transactions for subscriptions. Links to Fapshi payment gateway via provider_ref (transId).

---

### 11. OTP Model

**Table**: `otps`

**Attributes**:
- `id` (Integer, Primary Key)
- `user_id` (Integer, Foreign Key → users.id, Indexed)
- `code` (String(6))
- `expires_at` (DateTime, Indexed)
- `is_used` (Boolean, Default: False)
- `created_at` (DateTime)

**Relationships**:
- `user` → Many-to-One → User

**Description**: Stores OTP codes for email verification. Codes expire after a set time period.

---

### 12. Notification Model

**Table**: `notifications`

**Attributes**:
- `id` (UUID, Primary Key)
- `recipient_type` (Enum: USER, EMPLOYEE, Indexed)
- `user_id` (Integer, Foreign Key → users.id, Indexed, Nullable)
- `employee_id` (UUID, Foreign Key → employees.id, Indexed, Nullable)
- `title` (String(150))
- `message` (String)
- `category` (Enum: GENERAL, LEAVE, ATTENDANCE, SYSTEM, Indexed)
- `payload` (JSON, Nullable)
- `is_read` (Boolean, Default: False, Indexed)
- `read_at` (DateTime, Nullable)
- `created_at` (DateTime, Indexed)

**Indexes**:
- (`user_id`, `is_read`)
- (`employee_id`, `is_read`)

**Relationships**:
- `user` → Many-to-One → User
- `employee` → Many-to-One → Employee

**Description**: Stores in-app notifications for both admins and employees. Supports different categories and read status tracking.

---

### 13. Feedback Model

**Table**: `feedback`

**Attributes**:
- `id` (UUID, Primary Key)
- `user_id` (Integer, Foreign Key → users.id, Indexed, Nullable)
- `employee_id` (UUID, Foreign Key → employees.id, Indexed, Nullable)
- `description` (Text)
- `image_url` (String, Nullable)
- `created_at` (DateTime, Indexed)

**Relationships**:
- `user` → Many-to-One → User
- `employee` → Many-to-One → Employee

**Description**: Stores feedback submissions from users or employees. Can include text and optional images.

---

## Class Diagram Representation (Textual)

```
┌─────────────────────────────────────────────────────────────┐
│                          User                                │
├─────────────────────────────────────────────────────────────┤
│ +id: Integer (PK)                                            │
│ +full_name: String                                           │
│ +email: String (Unique)                                      │
│ +hashed_password: String                                     │
│ +is_super_admin: Boolean                                     │
│ +is_email_verified: Boolean                                  │
│ +is_active: Boolean                                          │
│ +reset_token: String                                         │
│ +reset_token_expiry: DateTime                                │
│ +created_at: DateTime                                        │
│ +updated_at: DateTime                                        │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         │ 1                  │ 1                  │ 1
         │                    │                    │
    ┌────▼────┐         ┌─────▼─────┐       ┌─────▼─────┐
    │   OTP   │         │Organization│       │ Payment  │
    └─────────┘         └────────────┘       └───────────┘
                              │
                              │ 1
                              │
                         ┌────▼────┐
                         │Employee │
                         └─────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    ┌────▼────┐         ┌─────▼─────┐       ┌─────▼─────┐
    │Attendance│         │LeaveRequest│       │PayrollRecord│
    └─────────┘         └────────────┘       └────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    SubscriptionPlan                         │
├─────────────────────────────────────────────────────────────┤
│ +id: Integer (PK)                                           │
│ +name: String (Unique)                                      │
│ +amount: Numeric                                            │
│ +currency: String                                           │
│ +interval: String                                           │
│ +is_active: Boolean                                         │
│ +description: String                                         │
└─────────────────────────────────────────────────────────────┘
         │
         │ 1
         │
    ┌────▼──────────┐
    │ Subscription  │
    ├───────────────┤
    │ +organization_id (FK)                                   │
    │ +plan_id (FK)                                           │
    │ +status: Enum                                           │
    │ +start_date: DateTime                                   │
    │ +next_billing_date: DateTime                            │
    └───────────────┘
         │
         │ 1
         │
    ┌────▼────┐
    │ Payment │
    └─────────┘
```

## Relationship Summary

### One-to-One Relationships
- User ↔ Organization (via `admin_id`)
- Organization ↔ Subscription (via `organization_id`)

### One-to-Many Relationships
- User → OTP
- User → Notification
- User → Feedback
- User → Payment
- Organization → Employee
- Organization → PayrollRecord
- Employee → Attendance
- Employee → EmployeeSession
- Employee → LeaveRequest
- Employee → Notification
- Employee → PayrollRecord
- Employee → Feedback
- SubscriptionPlan → Subscription
- Subscription → Payment

### Many-to-One Relationships
- Employee → Organization
- Attendance → Employee
- LeaveRequest → Employee, User (reviewer)
- PayrollRecord → Organization, Employee
- Payment → User, Subscription
- Notification → User, Employee
- Feedback → User, Employee

### Self-Referential Relationships
- Attendance → Attendance (check_in_id references another attendance record)

## Enumerations

### Gender
- MALE
- FEMALE
- OTHER

### WorkType
- FULL_TIME
- PART_TIME
- CONTRACT
- INTERN

### EmployeeRole
- ADMIN
- HR_MANAGER
- STAFF

### AttendanceType
- CHECK_IN
- CHECK_OUT

### LeaveRequestType
- PERMISSION
- LEAVE
- SICK
- VACATION
- CUSTOM

### LeaveRequestStatus
- PENDING
- APPROVED
- REJECTED
- CANCELLED

### SubscriptionStatus
- PENDING
- ACTIVE
- TRIAL
- PAST_DUE
- EXPIRED
- CANCELLED
- FAILED

### PaymentStatus
- INITIATED
- SUCCESS
- FAILED

### PaymentProvider
- FAPSHI

### PayrollStatus
- PENDING
- PAID

### NotificationCategory
- GENERAL
- LEAVE
- ATTENDANCE
- SYSTEM

### NotificationRecipient
- USER
- EMPLOYEE

## Database Constraints

### Unique Constraints
- `users.email` (unique)
- `organizations.organization_code` (unique)
- `employees.qr_code` (unique)
- `employees.employee_code + organization_id` (composite unique)
- `subscriptions.organization_id` (unique)
- `payments.provider_ref` (unique)
- `payroll_records.employee_id + period_year + period_month` (composite unique)

### Foreign Key Constraints
- All foreign keys maintain referential integrity
- Cascade delete configured for dependent records (e.g., deleting organization deletes employees)

### Indexes
- Primary keys are automatically indexed
- Foreign keys are indexed for query performance
- Frequently queried fields are indexed (status, dates, codes)
- Composite indexes for common query patterns

## Notes

- UUIDs are used for Employee, Attendance, LeaveRequest, PayrollRecord, Notification, and Feedback IDs
- Integers are used for User, Organization, Subscription, Payment, and OTP IDs
- All models include `created_at` and `updated_at` timestamps for auditing
- Soft deletes are supported via `is_active` flags where applicable
- Enums are stored as PostgreSQL ENUM types for type safety
