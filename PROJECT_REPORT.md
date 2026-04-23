# Attendeely Backend API - Project Report

**Project Name:** Attendeely - Comprehensive Attendance Management System  
**Version:** 1.0.0  
**Date:** 2024  
**Type:** Backend API Development

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Problem Identification](#2-problem-identification)
3. [General Solution](#3-general-solution)
4. [Tools Used During Development](#4-tools-used-during-development)
5. [Requirements Gathering](#5-requirements-gathering)
6. [Requirement Analysis and Prioritization](#6-requirement-analysis-and-prioritization)
7. [Functional Requirements](#7-functional-requirements)
8. [Non-Functional Requirements](#8-non-functional-requirements)

---

## 1. Introduction

### 1.1 Project Overview

Attendeely is a comprehensive, cloud-based attendance management system designed to streamline workforce management for organizations of all sizes. The system provides a robust backend API that enables organizations to efficiently track employee attendance, manage leave requests, process payroll, and maintain detailed workforce analytics.

The system addresses the critical need for modern, automated attendance tracking solutions that eliminate manual processes, reduce administrative overhead, and provide real-time insights into workforce patterns. Built with modern web technologies and following industry best practices, Attendeely offers a scalable, secure, and user-friendly solution for attendance management.

### 1.2 Project Scope

The Attendeely backend API encompasses the following core functionalities:

- **User Authentication & Authorization**: Secure authentication system for administrators and employees with role-based access control
- **Organization Management**: Complete organization profile management with customizable settings
- **Employee Management**: Comprehensive employee lifecycle management with QR code generation
- **Attendance Tracking**: Real-time attendance tracking with geofencing capabilities
- **Leave Request Management**: Automated leave and permission request workflow
- **Payroll Processing**: Automated payroll calculation based on attendance records
- **Subscription Management**: Flexible subscription plans with payment integration
- **Dashboard & Analytics**: Real-time insights and reporting capabilities
- **Notification System**: Multi-channel notification system for important events

### 1.3 Target Audience

The system serves two primary user groups:

1. **Administrators/Managers**: Organization administrators who manage employees, approve leave requests, process payroll, and view analytics
2. **Employees**: End users who check in/out, submit leave requests, and view their attendance history

### 1.4 Project Objectives

The primary objectives of this project are:

- To develop a scalable and maintainable backend API using modern web technologies
- To provide secure authentication and authorization mechanisms
- To automate attendance tracking and reduce manual administrative tasks
- To enable real-time attendance monitoring with location verification
- To streamline leave request workflows and approval processes
- To automate payroll calculations based on attendance data
- To provide comprehensive analytics and reporting capabilities
- To support multiple subscription tiers with feature-based access control

---

## 2. Problem Identification

### 2.1 Current Challenges in Attendance Management

Traditional attendance management systems face numerous challenges that impact organizational efficiency and employee satisfaction:

#### 2.1.1 Manual and Time-Consuming Processes
- **Problem**: Many organizations still rely on manual attendance tracking methods such as paper-based sign-in sheets, Excel spreadsheets, or basic time clocks
- **Impact**: 
  - Significant time investment required for data entry and verification
  - High probability of human errors in data recording
  - Difficulty in generating accurate reports
  - Inability to track real-time attendance status

#### 2.1.2 Lack of Location Verification
- **Problem**: Traditional systems cannot verify that employees are physically present at the workplace
- **Impact**:
  - Potential for attendance fraud (buddy punching)
  - Inability to enforce workplace attendance policies
  - Difficulty in managing remote or field employees
  - Lack of accountability for attendance records

#### 2.1.3 Inefficient Leave Management
- **Problem**: Leave request processes are often handled through emails, paper forms, or informal communication
- **Impact**:
  - Requests can be lost or overlooked
  - No centralized tracking of leave balances
  - Difficulty in coordinating team schedules
  - Lack of audit trail for leave approvals/rejections
  - Time-consuming approval workflows

#### 2.1.4 Disconnected Payroll Processing
- **Problem**: Attendance data and payroll systems are often separate, requiring manual data transfer
- **Impact**:
  - Increased risk of errors in payroll calculations
  - Time-consuming manual data entry
  - Difficulty in reconciling attendance with payroll
  - Delayed payroll processing
  - Lack of transparency in payroll calculations

#### 2.1.5 Limited Analytics and Reporting
- **Problem**: Traditional systems lack comprehensive analytics and reporting capabilities
- **Impact**:
  - Difficulty in identifying attendance patterns
  - Inability to make data-driven decisions
  - Limited visibility into workforce productivity
  - Challenges in compliance reporting
  - No predictive insights for workforce planning

#### 2.1.6 Security and Access Control Issues
- **Problem**: Many systems lack proper security measures and role-based access control
- **Impact**:
  - Risk of unauthorized access to sensitive data
  - Difficulty in managing user permissions
  - Lack of audit trails for system access
  - Compliance challenges with data protection regulations

#### 2.1.7 Scalability Limitations
- **Problem**: Existing solutions may not scale effectively as organizations grow
- **Impact**:
  - Performance degradation with increased users
  - Difficulty in managing multiple organizations
  - Limited customization options
  - High costs for enterprise-level features

### 2.2 Market Gap

The current market lacks a comprehensive, affordable, and scalable attendance management solution that:

- Provides both web and mobile access
- Integrates attendance tracking with payroll processing
- Offers flexible subscription models
- Supports geofencing for location verification
- Provides real-time analytics and reporting
- Ensures data security and compliance
- Scales with organizational growth

### 2.3 Business Impact

These challenges result in:

- **Increased Operational Costs**: Manual processes require significant human resources
- **Reduced Productivity**: Time spent on administrative tasks reduces focus on core business activities
- **Compliance Risks**: Inaccurate attendance records can lead to legal and regulatory issues
- **Employee Dissatisfaction**: Cumbersome processes negatively impact employee experience
- **Limited Growth Potential**: Inefficient systems hinder organizational scalability

---

## 3. General Solution

### 3.1 Solution Overview

Attendeely addresses the identified problems through a comprehensive, cloud-based attendance management system that automates core attendance tracking processes, integrates seamlessly with payroll systems, and provides real-time insights into workforce patterns.

### 3.2 Solution Architecture

The solution is built using a **layered architecture** pattern with clear separation of concerns:

#### 3.2.1 Presentation Layer (API Layer)
- RESTful API endpoints using FastAPI framework
- Standardized request/response formats
- Comprehensive error handling
- API versioning support

#### 3.2.2 Application Layer (Business Logic)
- Service-oriented architecture
- Feature-based access control
- Subscription management
- Business rule enforcement

#### 3.2.3 Data Access Layer
- SQLAlchemy ORM for database abstraction
- PostgreSQL for data persistence
- Relationship management and data integrity
- Optimized query performance

#### 3.2.4 External Services Integration
- Fapshi payment gateway for subscription payments
- Cloudinary for image storage and management
- Resend for transactional email delivery

### 3.3 Key Solution Components

#### 3.3.1 Automated Attendance Tracking
- **Mobile-based check-in/check-out**: Employees can check in/out using their mobile devices
- **Geofencing**: Location verification ensures employees are physically present at designated locations
- **Automatic hours calculation**: System automatically calculates hours worked based on check-in/check-out times
- **Real-time status**: Administrators can view real-time attendance status of all employees

#### 3.3.2 Integrated Leave Management
- **Digital leave requests**: Employees submit leave requests through the system
- **Automated workflow**: Requests are routed to administrators for approval
- **Automatic attendance adjustment**: Approved leaves automatically adjust attendance records
- **Notification system**: Real-time notifications for request status changes

#### 3.3.3 Automated Payroll Processing
- **Integration with attendance**: Payroll calculations are based on actual attendance records
- **Automatic calculations**: System calculates base salary, deductions, bonuses, and net pay
- **Monthly processing**: Automated monthly payroll generation
- **Transparency**: Employees can view their payroll records

#### 3.3.4 Subscription-Based Access Control
- **Multiple subscription tiers**: Free, Standard, and Enterprise plans
- **Feature-based access**: Different features available based on subscription level
- **Flexible payment**: Integration with mobile money payment gateway
- **Automatic renewal**: Subscription management with payment tracking

#### 3.3.5 Comprehensive Analytics
- **Dashboard overview**: Key performance indicators at a glance
- **Attendance trends**: Time-series analysis of attendance patterns
- **Compliance metrics**: Automated compliance reporting
- **Customizable reports**: Flexible reporting capabilities

### 3.4 Solution Benefits

#### 3.4.1 For Organizations
- **Reduced Administrative Overhead**: Automation eliminates manual data entry and processing
- **Improved Accuracy**: Automated calculations reduce human errors
- **Real-time Visibility**: Instant access to attendance and workforce data
- **Cost Efficiency**: Reduced need for administrative staff
- **Scalability**: System grows with organizational needs
- **Compliance**: Automated compliance reporting and audit trails

#### 3.4.2 For Administrators
- **Streamlined Workflows**: Automated processes reduce manual intervention
- **Better Decision Making**: Analytics provide insights for workforce planning
- **Time Savings**: Reduced time spent on administrative tasks
- **Centralized Management**: Single platform for all attendance-related activities

#### 3.4.3 For Employees
- **Convenience**: Easy check-in/check-out from mobile devices
- **Transparency**: Access to personal attendance and payroll records
- **Faster Leave Processing**: Digital leave request workflow
- **Real-time Notifications**: Instant updates on request status

### 3.5 Technology Choices

The solution leverages modern, proven technologies:

- **FastAPI**: High-performance Python web framework for building APIs
- **PostgreSQL**: Robust relational database for data persistence
- **SQLAlchemy**: Python ORM for database abstraction
- **JWT**: Secure token-based authentication
- **RESTful Architecture**: Standard API design for interoperability

---

## 4. Tools Used During Development

### 4.1 Programming Languages and Frameworks

#### 4.1.1 Python 3.8+
- **Purpose**: Primary programming language for backend development
- **Rationale**: 
  - Extensive library ecosystem
  - Excellent support for web development
  - Strong community support
  - Rapid development capabilities

#### 4.1.2 FastAPI 0.104.1
- **Purpose**: Web framework for building RESTful APIs
- **Rationale**:
  - High performance (comparable to Node.js and Go)
  - Automatic API documentation generation
  - Built-in data validation with Pydantic
  - Modern Python features (type hints, async/await)
  - Excellent developer experience

#### 4.1.3 SQLAlchemy 2.0.23
- **Purpose**: Object-Relational Mapping (ORM) framework
- **Rationale**:
  - Database abstraction layer
  - Relationship management
  - Query optimization
  - Migration support
  - Type safety

### 4.2 Database Technologies

#### 4.2.1 PostgreSQL 12+
- **Purpose**: Primary relational database management system
- **Rationale**:
  - Robust ACID compliance
  - Advanced indexing capabilities
  - Support for complex queries
  - Excellent performance
  - Open-source and cost-effective
  - Strong data integrity features

#### 4.2.2 Alembic 1.12.1
- **Purpose**: Database migration tool
- **Rationale**:
  - Version control for database schema
  - Automated migration generation
  - Rollback capabilities
  - Team collaboration support

### 4.3 Authentication and Security

#### 4.3.1 python-jose 3.3.0
- **Purpose**: JWT (JSON Web Token) implementation
- **Rationale**:
  - Secure token-based authentication
  - Stateless authentication
  - Industry standard
  - Token expiration support

#### 4.3.2 passlib 1.7.4 with bcrypt 4.0.1
- **Purpose**: Password hashing and verification
- **Rationale**:
  - Secure password storage
  - Industry-standard hashing algorithm
  - Protection against brute-force attacks
  - One-way hashing

### 4.4 Data Validation and Serialization

#### 4.4.1 Pydantic 2.5.0
- **Purpose**: Data validation and settings management
- **Rationale**:
  - Automatic data validation
  - Type safety
  - JSON schema generation
  - Settings management
  - Excellent error messages

#### 4.4.2 pydantic-settings 2.1.0
- **Purpose**: Settings management from environment variables
- **Rationale**:
  - Centralized configuration
  - Environment-based settings
  - Type-safe configuration
  - Validation of settings

### 4.5 External Service Integrations

#### 4.5.1 requests 2.31.0
- **Purpose**: HTTP client library for external API calls
- **Rationale**:
  - Simple API for HTTP requests
  - Support for various HTTP methods
  - Session management
  - Error handling

#### 4.5.2 cloudinary 1.36.0
- **Purpose**: Cloud-based image and video management
- **Rationale**:
  - Image storage and CDN delivery
  - Automatic image optimization
  - Transformation capabilities
  - Secure uploads

#### 4.5.3 resend 0.8.0
- **Purpose**: Transactional email service
- **Rationale**:
  - Reliable email delivery
  - API-based email sending
  - Template support
  - Delivery tracking

### 4.6 Development Tools

#### 4.6.1 Uvicorn 0.24.0
- **Purpose**: ASGI server for running FastAPI applications
- **Rationale**:
  - High-performance ASGI server
  - Hot reload for development
  - Production-ready
  - Support for async operations

#### 4.6.2 python-dotenv 1.0.0
- **Purpose**: Environment variable management
- **Rationale**:
  - Secure credential management
  - Environment-based configuration
  - Easy deployment configuration

#### 4.6.3 python-multipart 0.0.6
- **Purpose**: Multipart form data handling
- **Rationale**:
  - File upload support
  - Form data parsing
  - Required for FastAPI file uploads

#### 4.6.4 email-validator 2.1.0
- **Purpose**: Email address validation
- **Rationale**:
  - Input validation
  - Email format verification
  - Integration with Pydantic

### 4.7 Database Drivers

#### 4.7.1 psycopg2-binary 2.9.9
- **Purpose**: PostgreSQL database adapter for Python
- **Rationale**:
  - Native PostgreSQL support
  - High performance
  - Full feature support
  - Binary distribution for easy installation

### 4.8 Development Environment Tools

#### 4.8.1 Git
- **Purpose**: Version control system
- **Usage**: Code versioning, collaboration, change tracking

#### 4.8.2 Virtual Environment (venv)
- **Purpose**: Python environment isolation
- **Usage**: Dependency management, project isolation

#### 4.8.3 PostgreSQL Client Tools
- **Purpose**: Database management and querying
- **Usage**: Database administration, query testing

### 4.9 Documentation and Design Tools

#### 4.9.1 PlantUML
- **Purpose**: UML diagram generation
- **Usage**: System design documentation, architecture diagrams

#### 4.9.2 Markdown
- **Purpose**: Documentation format
- **Usage**: README files, API documentation, project documentation

### 4.10 Testing and Quality Assurance

#### 4.10.1 FastAPI Interactive Documentation
- **Purpose**: Built-in API testing interface
- **Usage**: Endpoint testing, API exploration, Swagger UI

#### 4.10.2 Postman/HTTP Clients
- **Purpose**: API testing and debugging
- **Usage**: Manual testing, integration testing

### 4.11 Deployment and Infrastructure

#### 4.11.1 Environment Variables (.env)
- **Purpose**: Configuration management
- **Usage**: Secure credential storage, environment-specific settings

#### 4.11.2 Docker (Optional)
- **Purpose**: Containerization
- **Usage**: Consistent deployment environments, scalability

---

## 5. Requirements Gathering

### 5.1 Requirements Gathering Methodology

The requirements gathering process followed a structured approach combining multiple techniques:

#### 5.1.1 Stakeholder Interviews
- **Participants**: Organization administrators, HR managers, employees
- **Purpose**: Understand current pain points and desired features
- **Outcome**: Identified core functional requirements and user expectations

#### 5.1.2 Market Research
- **Analysis**: Review of existing attendance management solutions
- **Purpose**: Identify market gaps and competitive features
- **Outcome**: Feature differentiation and unique value propositions

#### 5.1.3 User Story Mapping
- **Technique**: Agile user story creation
- **Purpose**: Break down features into user-centric requirements
- **Outcome**: Prioritized feature list based on user value

#### 5.1.4 Prototype Review
- **Approach**: Iterative prototype development and feedback
- **Purpose**: Validate requirements and gather early feedback
- **Outcome**: Refined requirements based on user feedback

### 5.2 Stakeholder Analysis

#### 5.2.1 Primary Stakeholders

**Administrators/Managers**
- **Needs**: 
  - Efficient employee management
  - Real-time attendance monitoring
  - Automated payroll processing
  - Comprehensive reporting
  - Leave request management
- **Pain Points**:
  - Manual data entry
  - Time-consuming processes
  - Lack of real-time visibility
  - Integration challenges

**Employees**
- **Needs**:
  - Easy check-in/check-out process
  - Access to attendance history
  - Simple leave request submission
  - Transparent payroll information
- **Pain Points**:
  - Cumbersome attendance processes
  - Lack of visibility into records
  - Slow leave approval processes

**System Administrators**
- **Needs**:
  - Scalable architecture
  - Secure system
  - Easy maintenance
  - Performance optimization
- **Pain Points**:
  - System downtime
  - Security vulnerabilities
  - Performance issues

### 5.3 Requirements Categories

Requirements were categorized into:

1. **Functional Requirements**: What the system should do
2. **Non-Functional Requirements**: How the system should perform
3. **Business Requirements**: Business objectives and constraints
4. **Technical Requirements**: Technical constraints and standards

### 5.4 Requirements Documentation

Requirements were documented using:

- **User Stories**: Feature descriptions from user perspective
- **Use Cases**: Detailed interaction scenarios
- **Functional Specifications**: Detailed feature descriptions
- **Technical Specifications**: Implementation details
- **API Specifications**: Endpoint definitions and contracts

### 5.5 Requirements Validation

Requirements were validated through:

- **Stakeholder Review**: Approval from key stakeholders
- **Technical Feasibility**: Assessment of technical viability
- **Resource Estimation**: Evaluation of development effort
- **Risk Assessment**: Identification of potential risks

---

## 6. Requirement Analysis and Prioritization

### 6.1 Prioritization Framework

Requirements were prioritized using the **MoSCoW Method** (Must Have, Should Have, Could Have, Won't Have) combined with **Value vs. Effort** analysis.

### 6.2 Priority Categories

#### 6.2.1 Must Have (Critical - P0)
**Definition**: Core functionality without which the system cannot function

**Requirements**:
1. **User Authentication System**
   - Admin signup and login
   - Employee login
   - JWT token-based authentication
   - Password security

2. **Organization Management**
   - Organization creation
   - Organization profile management
   - Organization code generation

3. **Employee Management**
   - Employee creation and management
   - Employee code generation
   - Basic employee information storage

4. **Basic Attendance Tracking**
   - Check-in functionality
   - Check-out functionality
   - Attendance record storage

5. **Database Infrastructure**
   - PostgreSQL database setup
   - Data models and relationships
   - Data persistence

**Rationale**: These are foundational features that form the core of the system. Without these, the system cannot provide basic attendance management functionality.

#### 6.2.2 Should Have (Important - P1)
**Definition**: Important features that significantly enhance system value

**Requirements**:
1. **Email Verification**
   - OTP-based email verification
   - Email service integration

2. **Leave Request Management**
   - Leave request submission
   - Leave request approval/rejection
   - Leave request status tracking

3. **Geofencing**
   - Location-based attendance verification
   - Geofence boundary setting
   - Distance calculation

4. **Dashboard and Analytics**
   - Basic dashboard overview
   - Attendance statistics
   - Employee count metrics

5. **Notification System**
   - In-app notifications
   - Email notifications
   - Notification status tracking

**Rationale**: These features significantly improve user experience and provide essential management capabilities. They differentiate the system from basic attendance tracking solutions.

#### 6.2.3 Could Have (Nice to Have - P2)
**Definition**: Features that add value but are not critical for initial release

**Requirements**:
1. **Payroll Processing**
   - Automated payroll calculation
   - Payroll record management
   - Payroll status tracking

2. **Advanced Analytics**
   - Attendance trends analysis
   - Late/absent breakdown
   - Compliance metrics

3. **Subscription Management**
   - Multiple subscription tiers
   - Payment integration
   - Feature-based access control

4. **QR Code Generation**
   - Employee QR code generation
   - QR code-based identification

5. **Super Admin Features**
   - System-wide administration
   - Multi-organization management

**Rationale**: These features provide advanced capabilities and monetization opportunities. They can be developed after core functionality is stable.

#### 6.2.4 Won't Have (Future - P3)
**Definition**: Features deferred to future releases

**Requirements**:
1. **Mobile App Development**
   - Native mobile applications
   - Push notifications

2. **Advanced Reporting**
   - Custom report builder
   - Export capabilities (PDF, Excel)

3. **Third-party Integrations**
   - HRIS system integration
   - Accounting software integration

4. **Advanced Features**
   - Biometric authentication
   - Facial recognition
   - Shift management

**Rationale**: These features require significant additional development effort and can be prioritized based on user feedback and market demand.

### 6.3 Value vs. Effort Analysis

Requirements were analyzed based on:

**Value Factors**:
- User impact (high/medium/low)
- Business value (revenue, efficiency)
- Competitive differentiation
- User satisfaction

**Effort Factors**:
- Development complexity
- Time required
- Resource requirements
- Technical risk

### 6.4 Dependencies Analysis

Requirements were analyzed for dependencies:

**Critical Dependencies**:
- Authentication must be implemented before any protected features
- Organization management must precede employee management
- Attendance tracking requires employee management
- Payroll processing depends on attendance tracking

**Feature Dependencies**:
- Geofencing requires location services
- Notifications require email service integration
- Subscription management requires payment gateway integration
- Analytics require data collection infrastructure

### 6.5 Risk-Based Prioritization

Requirements were also prioritized based on risk:

**High Risk, High Value**: Prioritized early
- Authentication and security (critical for system trust)
- Payment integration (critical for monetization)

**Low Risk, High Value**: Prioritized early
- Basic CRUD operations
- Standard API endpoints

**High Risk, Low Value**: Deferred or simplified
- Complex integrations
- Advanced features

### 6.6 Iterative Development Approach

Requirements were implemented in iterations:

**Iteration 1 (MVP)**:
- Core authentication
- Basic organization and employee management
- Basic attendance tracking

**Iteration 2**:
- Email verification
- Leave request management
- Geofencing

**Iteration 3**:
- Dashboard and analytics
- Notification system
- Payroll processing

**Iteration 4**:
- Subscription management
- Payment integration
- Advanced features

---

## 7. Functional Requirements

### 7.1 Authentication and Authorization

#### FR-1: Admin Authentication
- **FR-1.1**: System shall allow administrators to sign up with email, password, and full name
- **FR-1.2**: System shall send OTP code to admin email for verification
- **FR-1.3**: System shall verify OTP code before activating admin account
- **FR-1.4**: System shall allow admins to resend OTP if not received
- **FR-1.5**: System shall authenticate admins using email and password
- **FR-1.6**: System shall issue JWT access tokens upon successful authentication
- **FR-1.7**: System shall validate JWT tokens for protected endpoints
- **FR-1.8**: System shall allow password reset via email token
- **FR-1.9**: System shall enforce password complexity requirements
- **FR-1.10**: System shall hash passwords using bcrypt before storage

#### FR-2: Employee Authentication
- **FR-2.1**: System shall allow employees to login using organization code, employee code, and email
- **FR-2.2**: System shall issue JWT tokens with 90-day expiration for employees
- **FR-2.3**: System shall enforce single-device login per employee
- **FR-2.4**: System shall invalidate previous session when employee logs in from new device
- **FR-2.5**: System shall allow token refresh to extend session
- **FR-2.6**: System shall allow employees to logout, invalidating their session

#### FR-3: Authorization
- **FR-3.1**: System shall implement role-based access control (Admin, Employee, Super Admin)
- **FR-3.2**: System shall restrict employee access to their own data only
- **FR-3.3**: System shall restrict admin access to their organization's data only
- **FR-3.4**: System shall implement feature-based access control based on subscription plans
- **FR-3.5**: System shall block access to premium features for expired subscriptions

### 7.2 Organization Management

#### FR-4: Organization Operations
- **FR-4.1**: System shall allow admins to create organization with name, industry, country, currency
- **FR-4.2**: System shall generate unique 8-character organization code automatically
- **FR-4.3**: System shall allow admins to view organization details
- **FR-4.4**: System shall allow admins to update organization information
- **FR-4.5**: System shall allow admins to upload organization logo (JPEG, PNG, WEBP, max 5MB)
- **FR-4.6**: System shall store organization logo in cloud storage (Cloudinary)
- **FR-4.7**: System shall enforce one organization per admin

### 7.3 Employee Management

#### FR-5: Employee CRUD Operations
- **FR-5.1**: System shall allow admins to create employees with full details (name, email, phone, department, etc.)
- **FR-5.2**: System shall generate unique employee code within organization
- **FR-5.3**: System shall generate unique QR code for each employee
- **FR-5.4**: System shall allow admins to view list of all employees (paginated)
- **FR-5.5**: System shall allow admins to view employee details by employee code
- **FR-5.6**: System shall allow admins to update employee information
- **FR-5.7**: System shall allow admins to delete employees
- **FR-5.8**: System shall enforce employee code uniqueness within organization
- **FR-5.9**: System shall check employee limit based on subscription plan before creation
- **FR-5.10**: System shall allow admins to upload employee photos

### 7.4 Attendance Tracking

#### FR-6: Check-In/Check-Out
- **FR-6.1**: System shall allow employees to check in once per day
- **FR-6.2**: System shall allow employees to check out after check-in
- **FR-6.3**: System shall require GPS coordinates (latitude, longitude) for check-in/check-out
- **FR-6.4**: System shall validate employee location against geofence (if set)
- **FR-6.5**: System shall calculate distance from geofence center using Haversine formula
- **FR-6.6**: System shall reject check-in/check-out if outside geofence (300m radius)
- **FR-6.7**: System shall automatically calculate hours worked on check-out
- **FR-6.8**: System shall link check-out record to corresponding check-in record
- **FR-6.9**: System shall store attendance timestamp and location
- **FR-6.10**: System shall prevent duplicate check-ins on same day

#### FR-7: Attendance History
- **FR-7.1**: System shall allow employees to view their attendance history
- **FR-7.2**: System shall provide paginated attendance records
- **FR-7.3**: System shall allow employees to view today's attendance status
- **FR-7.4**: System shall display check-in time, check-out time, and hours worked

### 7.5 Geofencing

#### FR-8: Geofence Management
- **FR-8.1**: System shall allow admins to set geofence coordinates (latitude, longitude)
- **FR-8.2**: System shall set default geofence radius of 300 meters
- **FR-8.3**: System shall require Standard or Enterprise subscription for geofencing feature
- **FR-8.4**: System shall validate employee location against geofence during check-in/check-out
- **FR-8.5**: System shall calculate distance using Haversine formula

### 7.6 Leave Request Management

#### FR-9: Leave Request Submission
- **FR-9.1**: System shall allow employees to submit leave requests
- **FR-9.2**: System shall support multiple leave types (Permission, Leave, Sick, Vacation, Custom)
- **FR-9.3**: System shall require start date, end date, and reason for leave request
- **FR-9.4**: System shall allow full-day or partial-day leave requests
- **FR-9.5**: System shall track hours deducted for partial permissions
- **FR-9.6**: System shall set leave request status to PENDING upon submission
- **FR-9.7**: System shall send notification to admin when leave request is submitted

#### FR-10: Leave Request Management
- **FR-10.1**: System shall allow admins to view pending leave requests
- **FR-10.2**: System shall allow admins to view all leave requests with filters
- **FR-10.3**: System shall allow admins to approve leave requests
- **FR-10.4**: System shall allow admins to reject leave requests with optional notes
- **FR-10.5**: System shall allow employees to cancel pending leave requests
- **FR-10.6**: System shall automatically create excused attendance records for approved full-day leaves
- **FR-10.7**: System shall send notification to employee when request is approved/rejected
- **FR-10.8**: System shall track reviewer and review time for each request

### 7.7 Payroll Processing

#### FR-11: Payroll Calculation
- **FR-11.1**: System shall allow admins to process payroll for a specific month/year
- **FR-11.2**: System shall require Standard or Enterprise subscription for payroll processing
- **FR-11.3**: System shall calculate payroll for all active employees in organization
- **FR-11.4**: System shall calculate attendance days based on attendance records
- **FR-11.5**: System shall calculate working days for the period
- **FR-11.6**: System shall calculate base salary based on employee salary_per_hour
- **FR-11.7**: System shall allow admins to add deductions and bonuses
- **FR-11.8**: System shall calculate net pay (base salary + bonus - deductions)
- **FR-11.9**: System shall create/update payroll records for each employee
- **FR-11.10**: System shall enforce one payroll record per employee per month

#### FR-12: Payroll Management
- **FR-12.1**: System shall allow admins to view payroll summary (total, paid, pending)
- **FR-12.2**: System shall allow admins to view payroll records per employee
- **FR-12.3**: System shall allow filtering payroll records by status
- **FR-12.4**: System shall allow admins to update payroll record (deductions, bonuses, status)
- **FR-12.5**: System shall track payroll status (PENDING, PAID)

### 7.8 Subscription Management

#### FR-13: Subscription Plans
- **FR-13.1**: System shall provide three subscription plans (Free, Standard, Enterprise)
- **FR-13.2**: System shall define features for each subscription plan
- **FR-13.3**: System shall define employee limits for each plan (Free: 10, Standard: 100, Enterprise: Unlimited)
- **FR-13.4**: System shall allow admins to view all available plans
- **FR-13.5**: System shall display plan features, pricing, and limits

#### FR-14: Subscription Operations
- **FR-14.1**: System shall allow admins to subscribe to a plan
- **FR-14.2**: System shall create pending subscription upon plan selection
- **FR-14.3**: System shall initiate payment via Fapshi payment gateway
- **FR-14.4**: System shall activate subscription upon successful payment
- **FR-14.5**: System shall set subscription status to FAILED if payment fails
- **FR-14.6**: System shall allow admins to cancel subscription
- **FR-14.7**: System shall automatically expire subscriptions after end date
- **FR-14.8**: System shall block premium features for expired/failed subscriptions
- **FR-14.9**: System shall track subscription start date, end date, and billing dates

#### FR-15: Payment Processing
- **FR-15.1**: System shall integrate with Fapshi payment gateway
- **FR-15.2**: System shall initiate payment with amount, phone, email, and external ID
- **FR-15.3**: System shall receive payment status via webhook
- **FR-15.4**: System shall update payment status (INITIATED, SUCCESS, FAILED)
- **FR-15.5**: System shall store payment transaction ID (transId)
- **FR-15.6**: System shall allow admins to view payment history
- **FR-15.7**: System shall allow querying subscription status by transaction ID

### 7.9 Dashboard and Analytics

#### FR-16: Dashboard Overview
- **FR-16.1**: System shall provide dashboard with key performance indicators
- **FR-16.2**: System shall display total employee count
- **FR-16.3**: System shall display attendance statistics
- **FR-16.4**: System shall display payroll summary metrics
- **FR-16.5**: System shall display compliance metrics

#### FR-17: Analytics
- **FR-17.1**: System shall provide daily attendance trends (time-series data)
- **FR-17.2**: System shall provide late vs absent employee breakdown
- **FR-17.3**: System shall calculate attendance percentages
- **FR-17.4**: System shall aggregate data by date ranges

### 7.10 Notification System

#### FR-18: Notifications
- **FR-18.1**: System shall create notifications for important events
- **FR-18.2**: System shall support notifications for admins and employees
- **FR-18.3**: System shall categorize notifications (General, Leave, Attendance, System)
- **FR-18.4**: System shall allow users to view their notifications
- **FR-18.5**: System shall allow users to mark notifications as read
- **FR-18.6**: System shall allow users to mark all notifications as read
- **FR-18.7**: System shall send email notifications for critical events
- **FR-18.8**: System shall track notification read status and read time

### 7.11 Support and Feedback

#### FR-19: Support
- **FR-19.1**: System shall provide contact/support endpoint
- **FR-19.2**: System shall allow users to send support messages
- **FR-19.3**: System shall send support messages to support@attendeely.com

#### FR-20: Feedback
- **FR-20.1**: System shall allow users and employees to submit feedback
- **FR-20.2**: System shall allow optional image upload with feedback
- **FR-20.3**: System shall store feedback with timestamp

### 7.12 Super Admin Features

#### FR-21: Super Admin Operations
- **FR-21.1**: System shall provide super admin role with elevated privileges
- **FR-21.2**: System shall allow super admin to view all organizations
- **FR-21.3**: System shall allow super admin to view organization details
- **FR-21.4**: System shall allow super admin to view system-wide analytics

---

## 8. Non-Functional Requirements

### 8.1 Performance Requirements

#### NFR-1: Response Time
- **NFR-1.1**: System shall respond to API requests within 2 seconds for 95% of requests
- **NFR-1.2**: System shall respond to authentication requests within 1 second
- **NFR-1.3**: System shall process database queries within 500ms for simple queries
- **NFR-1.4**: System shall handle concurrent requests from multiple users
- **NFR-1.5**: System shall support at least 100 concurrent users per organization

#### NFR-2: Throughput
- **NFR-2.1**: System shall handle at least 1000 requests per minute
- **NFR-2.2**: System shall process attendance check-ins within 1 second
- **NFR-2.3**: System shall generate reports within 5 seconds

#### NFR-3: Scalability
- **NFR-3.1**: System shall scale horizontally to support multiple organizations
- **NFR-3.2**: System shall support database connection pooling (minimum 5 connections)
- **NFR-3.3**: System shall handle increasing data volume without performance degradation
- **NFR-3.4**: System architecture shall support adding more application servers

### 8.2 Security Requirements

#### NFR-4: Authentication Security
- **NFR-4.1**: System shall use JWT tokens with HS256 algorithm
- **NFR-4.2**: System shall enforce token expiration (30 minutes for admin, 90 days for employee)
- **NFR-4.3**: System shall hash passwords using bcrypt with appropriate cost factor
- **NFR-4.4**: System shall never store plain-text passwords
- **NFR-4.5**: System shall validate token signatures before processing requests

#### NFR-5: Authorization Security
- **NFR-5.1**: System shall implement role-based access control
- **NFR-5.2**: System shall enforce organization-level data isolation
- **NFR-5.3**: System shall prevent unauthorized access to other organizations' data
- **NFR-5.4**: System shall validate user permissions for each request
- **NFR-5.5**: System shall enforce feature-based access control based on subscriptions

#### NFR-6: Data Security
- **NFR-6.1**: System shall use HTTPS for all API communications
- **NFR-6.2**: System shall encrypt sensitive data in transit
- **NFR-6.3**: System shall store API keys and secrets in environment variables
- **NFR-6.4**: System shall protect against SQL injection using parameterized queries
- **NFR-6.5**: System shall validate and sanitize all user inputs
- **NFR-6.6**: System shall implement CORS policies appropriately

#### NFR-7: Session Security
- **NFR-7.1**: System shall enforce single-device login for employees
- **NFR-7.2**: System shall invalidate sessions on logout
- **NFR-7.3**: System shall hash session tokens before storage
- **NFR-7.4**: System shall track session expiration times

### 8.3 Reliability Requirements

#### NFR-8: Availability
- **NFR-8.1**: System shall maintain 99% uptime availability
- **NFR-8.2**: System shall handle database connection failures gracefully
- **NFR-8.3**: System shall implement connection retry mechanisms
- **NFR-8.4**: System shall handle external service failures without crashing

#### NFR-9: Error Handling
- **NFR-9.1**: System shall provide meaningful error messages to users
- **NFR-9.2**: System shall log all errors for debugging
- **NFR-9.3**: System shall handle validation errors gracefully
- **NFR-9.4**: System shall return appropriate HTTP status codes
- **NFR-9.5**: System shall implement global exception handling

#### NFR-10: Data Integrity
- **NFR-10.1**: System shall enforce database constraints and relationships
- **NFR-10.2**: System shall use database transactions for critical operations
- **NFR-10.3**: System shall maintain referential integrity
- **NFR-10.4**: System shall prevent data corruption through validation

### 8.4 Usability Requirements

#### NFR-11: API Usability
- **NFR-11.1**: System shall provide RESTful API with consistent endpoint naming
- **NFR-11.2**: System shall provide comprehensive API documentation (Swagger/OpenAPI)
- **NFR-11.3**: System shall use standard HTTP methods (GET, POST, PUT, DELETE)
- **NFR-11.4**: System shall return consistent JSON response format
- **NFR-11.5**: System shall provide clear error messages with error codes

#### NFR-12: User Experience
- **NFR-12.1**: System shall provide intuitive API endpoints
- **NFR-12.2**: System shall support pagination for large result sets
- **NFR-12.3**: System shall provide filtering and sorting capabilities
- **NFR-12.4**: System shall return relevant data without unnecessary nesting

### 8.5 Maintainability Requirements

#### NFR-13: Code Quality
- **NFR-13.1**: System shall follow Python PEP 8 coding standards
- **NFR-13.2**: System shall use type hints for better code documentation
- **NFR-13.3**: System shall implement proper error handling
- **NFR-13.4**: System shall include code comments for complex logic
- **NFR-13.5**: System shall follow consistent naming conventions

#### NFR-14: Documentation
- **NFR-14.1**: System shall provide comprehensive README documentation
- **NFR-14.2**: System shall document all API endpoints
- **NFR-14.3**: System shall provide setup and installation instructions
- **NFR-14.4**: System shall document database schema and relationships
- **NFR-14.5**: System shall provide architecture and design documentation

#### NFR-15: Modularity
- **NFR-15.1**: System shall follow layered architecture pattern
- **NFR-15.2**: System shall separate concerns (API, business logic, data access)
- **NFR-15.3**: System shall use dependency injection for testability
- **NFR-15.4**: System shall implement reusable service components

### 8.6 Compatibility Requirements

#### NFR-16: Platform Compatibility
- **NFR-16.1**: System shall run on Linux, Windows, and macOS development environments
- **NFR-16.2**: System shall support Python 3.8 and above
- **NFR-16.3**: System shall work with PostgreSQL 12 and above
- **NFR-16.4**: System shall be deployable on standard cloud platforms

#### NFR-17: Integration Compatibility
- **NFR-17.1**: System shall integrate with Fapshi payment gateway API
- **NFR-17.2**: System shall integrate with Cloudinary image storage API
- **NFR-17.3**: System shall integrate with Resend email service API
- **NFR-17.4**: System shall support standard HTTP/HTTPS protocols
- **NFR-17.5**: System shall support JSON data format

### 8.7 Portability Requirements

#### NFR-18: Deployment Portability
- **NFR-18.1**: System shall be deployable using environment variables for configuration
- **NFR-18.2**: System shall support Docker containerization
- **NFR-18.3**: System shall be independent of specific hosting providers
- **NFR-18.4**: System shall support database migrations for schema changes

### 8.8 Compliance Requirements

#### NFR-19: Data Protection
- **NFR-19.1**: System shall protect user personal information
- **NFR-19.2**: System shall implement secure password storage
- **NFR-19.3**: System shall provide audit trails for sensitive operations
- **NFR-19.4**: System shall support data privacy requirements

### 8.9 Monitoring and Logging Requirements

#### NFR-20: Logging
- **NFR-20.1**: System shall log all API requests and responses
- **NFR-20.2**: System shall log authentication attempts
- **NFR-20.3**: System shall log errors with sufficient detail for debugging
- **NFR-20.4**: System shall use structured logging format
- **NFR-20.5**: System shall include timestamps in all log entries

#### NFR-21: Monitoring
- **NFR-21.1**: System shall provide health check endpoint
- **NFR-21.2**: System shall track API response times
- **NFR-21.3**: System shall monitor database connection status
- **NFR-21.4**: System shall track external service integration status

### 8.10 Backup and Recovery Requirements

#### NFR-22: Data Backup
- **NFR-22.1**: System shall support database backup mechanisms
- **NFR-22.2**: System shall maintain database migration history
- **NFR-22.3**: System shall support data recovery procedures

---

## Conclusion

This project report provides a comprehensive overview of the Attendeely backend API development project, covering all aspects from problem identification to detailed functional and non-functional requirements. The system addresses critical challenges in attendance management through automation, integration, and modern technology stack.



---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Prepared By**: Development Team  
**Status**: Complete
