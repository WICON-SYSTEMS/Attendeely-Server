# Architectural Design Documentation

## Overview
Attendeely is a comprehensive attendance management system built with a modern, scalable architecture. This document describes the system's architectural patterns, layers, components, and design decisions.

## Architecture Style

### Primary Architecture Pattern
**Layered Architecture (N-Tier Architecture)**

The system follows a layered architecture pattern with clear separation of concerns:

1. **Presentation Layer** (API Endpoints)
2. **Application Layer** (Business Logic)
3. **Data Access Layer** (ORM Models & Database)
4. **External Services Layer** (Third-party Integrations)

## System Layers

### 1. Presentation Layer (API Layer)

**Location**: `app/api/v1/`

**Components**:
- FastAPI route handlers
- Request/Response validation via Pydantic schemas
- Authentication middleware
- Error handling

**Responsibilities**:
- Receive HTTP requests
- Validate input data
- Authenticate and authorize users
- Call application layer services
- Format and return responses
- Handle exceptions

**Key Files**:
- `auth.py` - Authentication endpoints
- `organization.py` - Organization management
- `employee.py` - Employee CRUD operations
- `employee_auth.py` - Employee portal authentication
- `leave_request.py` - Leave request management
- `payroll.py` - Payroll processing
- `subscription.py` - Subscription management
- `dashboard.py` - Analytics and reporting
- `notification.py` - Notification management
- `attendance_tracking.py` - Attendance tracking
- `support.py` - Support/contact endpoints
- `feedback.py` - Feedback submission
- `super_admin.py` - Super admin operations

**Design Patterns Used**:
- **RESTful API Design**: Standard HTTP methods (GET, POST, PUT, DELETE)
- **Dependency Injection**: FastAPI's Depends() for authentication and database sessions
- **Middleware Pattern**: CORS, request logging, error handling

---

### 2. Application Layer (Business Logic Layer)

**Location**: `app/core/`, `app/utils/`, `app/services/`

**Components**:

#### Core Components (`app/core/`)
- **config.py**: Application configuration and settings
- **database.py**: Database connection and session management
- **dependencies.py**: FastAPI dependencies (authentication, authorization)
- **security.py**: Security utilities (JWT, password hashing, token management)
- **subscription_access.py**: Subscription and feature access control

#### Utility Functions (`app/utils/`)
- **generators.py**: Code generation (organization codes, employee codes, QR codes)
- **geofence.py**: Geofence validation using Haversine formula
- **otp.py**: OTP generation and validation
- **subscription_features.py**: Feature access definitions and plan limits

#### Service Layer (`app/services/`)
- **email_service.py**: Email sending via Resend API
- **cloudinary_service.py**: Image upload and management via Cloudinary
- **fapshi_service.py**: Payment processing via Fapshi gateway
- **notification_service.py**: In-app notification creation

**Responsibilities**:
- Implement business logic
- Coordinate between data access and external services
- Enforce business rules
- Handle cross-cutting concerns (security, validation)
- Manage feature access based on subscriptions

**Design Patterns Used**:
- **Service Pattern**: Encapsulate business logic in service classes
- **Factory Pattern**: Feature requirement dependencies
- **Strategy Pattern**: Different payment providers, email providers

---

### 3. Data Access Layer

**Location**: `app/models/`

**Components**:
- SQLAlchemy ORM models
- Database relationships
- Enums and constraints

**Key Models**:
- `user.py` - Admin users
- `organization.py` - Organizations
- `employee.py` - Employees
- `attendance.py` - Attendance records
- `leave_request.py` - Leave requests
- `payroll.py` - Payroll records
- `subscription.py` - Subscriptions and payments
- `notification.py` - Notifications
- `otp.py` - OTP codes
- `employee_session.py` - Employee sessions
- `feedback.py` - Feedback submissions

**Responsibilities**:
- Define database schema
- Manage relationships between entities
- Handle data persistence
- Enforce data integrity

**Design Patterns Used**:
- **Active Record Pattern**: SQLAlchemy ORM
- **Repository Pattern**: Implicit through SQLAlchemy queries

---

### 4. Schema Layer (Data Transfer Objects)

**Location**: `app/schemas/`

**Components**:
- Pydantic models for request/response validation
- Input/output data structures

**Key Schemas**:
- Request schemas (e.g., `CreateEmployeeRequest`, `SubscribeRequest`)
- Response schemas (e.g., `EmployeeResponse`, `SubscriptionResponse`)
- Webhook schemas (e.g., `FapshiWebhookRequest`)

**Responsibilities**:
- Validate incoming data
- Serialize outgoing data
- Define API contracts
- Type safety

---

### 5. External Services Layer

**Integrations**:

#### Fapshi Payment Gateway
- **Purpose**: Process subscription payments
- **Integration**: REST API
- **Flow**: Initiate payment → Receive webhook → Update subscription
- **Service**: `app/services/fapshi_service.py`

#### Cloudinary
- **Purpose**: Image storage and management
- **Integration**: REST API
- **Usage**: Organization logos, employee photos
- **Service**: `app/services/cloudinary_service.py`

#### Resend Email Service
- **Purpose**: Send transactional emails
- **Integration**: REST API
- **Usage**: OTP emails, password resets, notifications
- **Service**: `app/services/email_service.py`

---

## Database Architecture

### Database System
**PostgreSQL** (Relational Database)

### Design Patterns

#### 1. **Normalization**
- Third Normal Form (3NF) compliance
- Separate tables for related entities
- Foreign key relationships

#### 2. **Indexing Strategy**
- Primary keys automatically indexed
- Foreign keys indexed
- Frequently queried fields indexed (status, dates, codes)
- Composite indexes for common query patterns

#### 3. **Enum Types**
- PostgreSQL ENUMs for status fields
- Type safety and data integrity

#### 4. **UUID vs Integer IDs**
- UUIDs for entities that may be exposed publicly (Employee, Attendance, LeaveRequest)
- Integers for internal entities (User, Organization, Subscription)

### Connection Management
- **Connection Pooling**: SQLAlchemy connection pool
- **Pool Size**: Configurable (default: 5 connections)
- **Max Overflow**: Additional connections when needed
- **Connection Recycling**: Prevents stale connections

---

## Authentication & Authorization Architecture

### Authentication Methods

#### 1. Admin Authentication
- **Method**: JWT (JSON Web Tokens)
- **Flow**: Signup → OTP Verification → Login → JWT Token
- **Token Expiration**: 30 minutes
- **Storage**: Token sent in Authorization header

#### 2. Employee Authentication
- **Method**: JWT with extended expiration
- **Flow**: Login with org_code, employee_code, email → JWT Token
- **Token Expiration**: 90 days (for mobile persistence)
- **Single Device**: Only one active session per employee
- **Session Tracking**: Hashed tokens stored in database

### Authorization

#### Role-Based Access Control (RBAC)
- **Admin Role**: Full access to organization management
- **Employee Role**: Limited to own data and attendance
- **Super Admin Role**: System-wide access

#### Feature-Based Access Control
- **Subscription Plans**: Free, Standard, Enterprise
- **Feature Gating**: Certain features require specific plans
- **Employee Limits**: Plan-based employee count limits

**Implementation**: `app/core/subscription_access.py`

---

## API Architecture

### RESTful API Design

#### Endpoint Structure
```
/api/v1/{resource}/{action}
```

#### HTTP Methods
- **GET**: Retrieve resources
- **POST**: Create resources or trigger actions
- **PUT**: Update resources
- **DELETE**: Delete resources

#### Response Format
Standardized response structure:
```json
{
  "success": boolean,
  "message": string,
  "data": object | null,
  "status_code": integer,
  "timestamp": datetime
}
```

### API Versioning
- Current version: `v1`
- Prefix: `/api/v1`
- Future versions: `/api/v2`, etc.

### Error Handling
- **Global Exception Handler**: Catches unhandled exceptions
- **HTTP Status Codes**: Standard REST status codes
- **Error Messages**: User-friendly error descriptions

---

## Security Architecture

### Security Layers

#### 1. **Input Validation**
- Pydantic schema validation
- Type checking
- Constraint validation

#### 2. **Authentication**
- JWT token validation
- Token expiration checks
- Token signature verification

#### 3. **Authorization**
- Role-based access control
- Feature-based access control
- Organization-level data isolation

#### 4. **Data Protection**
- Password hashing (bcrypt)
- Token hashing for sessions
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration

#### 5. **External Service Security**
- API keys stored in environment variables
- Secure credential management
- HTTPS for external API calls

---

## Scalability Considerations

### Horizontal Scaling
- **Stateless API**: No server-side session storage
- **Database Connection Pooling**: Handles concurrent connections
- **External Service Integration**: Asynchronous where possible

### Performance Optimization
- **Database Indexing**: Optimized query performance
- **Connection Pooling**: Efficient database connections
- **Lazy Loading**: SQLAlchemy relationship loading
- **Pagination**: Large result sets paginated

### Caching Strategy
- Currently: No caching layer
- Future: Redis for session management and frequently accessed data

---

## Deployment Architecture

### Application Server
- **Framework**: FastAPI (ASGI)
- **Server**: Uvicorn
- **Workers**: Configurable (production: 4+ workers)

### Database
- **PostgreSQL**: Primary data store
- **Migrations**: Alembic for schema versioning

### External Services
- **Fapshi**: Payment processing
- **Cloudinary**: Image storage (CDN)
- **Resend**: Email delivery

### Environment Configuration
- **Development**: Local PostgreSQL, sandbox services
- **Production**: Production PostgreSQL, live services
- **Configuration**: Environment variables via `.env`

---

## Data Flow Architecture

### Request Flow
```
Client Request
    ↓
FastAPI Middleware (CORS, Logging)
    ↓
Route Handler (Authentication Check)
    ↓
Dependency Injection (Database Session, User)
    ↓
Business Logic (Service Layer)
    ↓
Data Access Layer (SQLAlchemy ORM)
    ↓
PostgreSQL Database
    ↓
Response (JSON)
```

### Payment Flow
```
Admin Request Subscription
    ↓
Create Pending Subscription
    ↓
Initiate Payment (Fapshi Service)
    ↓
Fapshi Payment Gateway
    ↓
Webhook Received (Payment Status)
    ↓
Update Payment Record
    ↓
Activate Subscription (if successful)
```

### Notification Flow
```
Event Occurs (e.g., Leave Request Created)
    ↓
Notification Service
    ↓
Create Notification Record (Database)
    ↓
Send Email (Resend Service)
    ↓
User Receives Notification
```

---

## Design Patterns & Principles

### Design Patterns

1. **Dependency Injection**
   - FastAPI's Depends() for injecting dependencies
   - Database sessions, authentication, authorization

2. **Factory Pattern**
   - Feature requirement dependencies
   - Service creation

3. **Repository Pattern** (Implicit)
   - SQLAlchemy ORM abstracts data access

4. **Service Pattern**
   - Business logic encapsulated in services
   - External integrations abstracted

5. **Middleware Pattern**
   - Request/response processing
   - CORS, logging, error handling

### SOLID Principles

- **Single Responsibility**: Each module has a single purpose
- **Open/Closed**: Extensible via dependency injection
- **Liskov Substitution**: Interfaces and abstractions
- **Interface Segregation**: Focused service interfaces
- **Dependency Inversion**: Depend on abstractions (services)

---

## Technology Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework
- **Python 3.8+**: Programming language

### Database
- **PostgreSQL**: Relational database
- **SQLAlchemy**: ORM framework
- **Alembic**: Database migrations

### Authentication
- **python-jose**: JWT handling
- **passlib**: Password hashing (bcrypt)

### Validation
- **Pydantic**: Data validation and serialization

### External Libraries
- **requests**: HTTP client for external APIs
- **cloudinary**: Image management SDK
- **resend**: Email service SDK

### Development Tools
- **Uvicorn**: ASGI server
- **Alembic**: Database migrations
- **Python logging**: Logging framework

---

## File Structure

```
Attendeely-backend/
├── alembic/                  # Database migrations
│   ├── versions/            # Migration files
│   └── env.py               # Alembic configuration
├── app/
│   ├── api/
│   │   └── v1/              # API endpoints (Presentation Layer)
│   ├── core/                # Core functionality (Application Layer)
│   ├── models/              # Database models (Data Access Layer)
│   ├── schemas/             # Pydantic schemas (DTOs)
│   ├── services/            # External service integrations
│   ├── utils/               # Utility functions
│   └── main.py              # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── alembic.ini              # Alembic configuration
└── .env                     # Environment variables
```

---

## Future Architectural Considerations

### Potential Enhancements

1. **Caching Layer**
   - Redis for session management
   - Cache frequently accessed data
   - Reduce database load

2. **Message Queue**
   - Celery + Redis/RabbitMQ for async tasks
   - Background job processing
   - Email queue processing

3. **API Gateway**
   - Rate limiting
   - Request throttling
   - API analytics

4. **Microservices Architecture**
   - Split into domain-specific services
   - Independent scaling
   - Service mesh

5. **Event-Driven Architecture**
   - Event sourcing for audit trails
   - Pub/Sub for notifications
   - Decoupled services

6. **Monitoring & Observability**
   - Application performance monitoring (APM)
   - Log aggregation (ELK stack)
   - Metrics collection (Prometheus)

---

## Architectural Diagrams

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Applications                     │
│              (Web Frontend, Mobile Apps)                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ HTTP/REST API
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ API Routes   │  │ Middleware   │  │ Dependencies │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Services     │  │ Utils        │  │ Security     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│  PostgreSQL    │  │   Fapshi       │  │   Cloudinary   │
│   Database     │  │   Payment      │  │   Storage      │
└────────────────┘  └────────────────┘  └────────────────┘
        │
┌───────▼────────┐
│    Resend      │
│    Email       │
└────────────────┘
```

### Component Interaction

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ HTTP Request
       │
┌──────▼──────────────────────────────────────┐
│         FastAPI Route Handler                │
│  - Validate Request (Pydantic)              │
│  - Authenticate (JWT)                       │
│  - Authorize (RBAC/Feature Check)           │
└──────┬───────────────────────────────────────┘
       │
       │ Call Service/Business Logic
       │
┌──────▼──────────────────────────────────────┐
│         Business Logic Layer                 │
│  - Service Classes                           │
│  - Utility Functions                         │
│  - Feature Access Control                    │
└──────┬───────────────────────────────────────┘
       │
       │ Database Operations
       │
┌──────▼──────────────────────────────────────┐
│         Data Access Layer                    │
│  - SQLAlchemy ORM                           │
│  - Database Queries                          │
│  - Transaction Management                    │
└──────┬──────────────────────────────────────┘
       │
       │ SQL Queries
       │
┌──────▼──────────────────────────────────────┐
│         PostgreSQL Database                  │
│  - Data Storage                              │
│  - Relationships                             │
│  - Constraints                               │
└──────────────────────────────────────────────┘
```

---

## Conclusion

Attendeely follows a clean, layered architecture that promotes:
- **Separation of Concerns**: Clear boundaries between layers
- **Maintainability**: Easy to understand and modify
- **Scalability**: Can scale horizontally
- **Security**: Multiple security layers
- **Testability**: Components can be tested independently

The architecture supports current requirements while allowing for future enhancements and scaling.
