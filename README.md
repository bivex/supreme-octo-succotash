# Supreme Octo Succotash - DDD Affiliate Marketing Platform

## 1. Introduction

### 1.1 Purpose

This document provides comprehensive guidance for developers and system administrators working with the Supreme Octo
Succotash platform, a modern affiliate marketing system built using Domain-Driven Design (DDD) principles with Clean
Architecture. The platform provides comprehensive affiliate marketing functionality including campaign management, LTV
analytics, retention campaigns, lead processing, and real-time performance analytics.

### 1.2 Scope

This documentation covers:

- Installation and configuration of the Supreme Octo Succotash platform
- API usage and endpoint descriptions for all business domains
- Database setup and configuration (PostgreSQL primary, SQLite for testing)
- Business logic implementation and domain modeling
- Testing procedures and quality assurance
- Configuration management and deployment
- Troubleshooting common issues
- Architecture overview and design decisions

### 1.3 Audience

This document is intended for:

- **Software Developers**: Implementing client applications that integrate with the API
- **System Administrators**: Deploying and maintaining the platform service
- **Data Analysts**: Understanding LTV, retention, and lead analytics capabilities
- **Quality Assurance Engineers**: Testing API functionality and business logic
- **DevOps Engineers**: Configuring and monitoring production deployments
- **Product Managers**: Understanding business domain capabilities

### 1.4 Conventions Used in This Document

- **API endpoints** are shown in `monospace font`
- **Command-line instructions** are presented in code blocks with bash syntax highlighting
- **File paths** use forward slashes (/) for consistency
- **Important notes** are highlighted with ℹ️ symbol
- **Warning messages** are highlighted with ⚠️ symbol
- **New features** are highlighted with 🆕 symbol

## 2. Overview of the Software

### 2.1 Software Description

Supreme Octo Succotash is a comprehensive affiliate marketing platform built using Domain-Driven Design (DDD) with Clean
Architecture principles. The platform provides end-to-end affiliate marketing capabilities including campaign
management, advanced LTV analytics, automated retention campaigns, lead processing with scoring, and real-time
performance monitoring. The system has been fully refactored to eliminate mock data and implement production-ready
business logic.

### 2.2 Key Features

- **🆕 LTV Analytics**: Customer Lifetime Value calculation with cohort analysis and segmentation
- **🆕 Retention Campaigns**: Automated retention campaigns with churn prediction and user engagement profiling
- **🆕 Lead Processing**: Form submission handling, lead scoring, and conversion funnel analytics
- **Campaign Management**: Create, update, and monitor affiliate marketing campaigns
- **Click Tracking**: Track and validate affiliate clicks with fraud prevention
- **Analytics**: Real-time performance metrics and comprehensive reporting
- **🆕 Multi-Database Support**: PostgreSQL for production, SQLite for testing and development
- **Security**: Comprehensive input validation and fraud detection
- **DDD Architecture**: Domain-driven design with clean separation of concerns
- **Production Ready**: Full business logic implementation with no mock data

### 2.3 Architecture Overview

The application follows Domain-Driven Design (DDD) with Clean Architecture, implementing the Hexagonal Architecture
pattern:

```
src/
├── domain/                    # Business logic and rules (Core Business)
│   ├── entities/             # Core business objects (Campaign, LTV, Retention, Lead, etc.)
│   ├── value_objects/        # Value objects (Money, URL, LTVSegment, etc.)
│   ├── services/             # Domain services (LTV calculations, retention analysis, form validation)
│   └── repositories/         # Repository interfaces (ports/contracts)
├── application/              # Use cases and orchestration (Application Layer)
│   ├── commands/             # Command objects for write operations
│   ├── handlers/             # Command/query handlers (LTV, Retention, Form handlers)
│   └── queries/              # Query objects for read operations
├── infrastructure/           # External concerns and implementations (Adapters)
│   ├── repositories/         # Repository implementations (PostgreSQL & SQLite adapters)
│   │   ├── postgres_*/       # PostgreSQL implementations for production 🆕
│   │   ├── sqlite_*/         # SQLite implementations for testing
│   │   └── in_memory_*/      # In-memory implementations for development
│   └── external/             # External service adapters
├── presentation/             # HTTP layer and APIs (Delivery Mechanisms)
│   ├── routes/               # Flask route handlers (LTV, Retention, Form routes) 🆕
│   ├── dto/                  # Data Transfer Objects
│   └── middleware/           # HTTP middleware
└── config/                  # Configuration management
```

### 2.4 Business Domains 🆕

The platform implements three core business domains:

1. **LTV (Lifetime Value) Domain**
    - Customer LTV calculation and analysis
    - Cohort analysis and segmentation
    - Predictive CLV modeling

2. **Retention Domain**
    - Automated retention campaigns
    - Churn prediction and risk assessment
    - User engagement profiling

3. **Lead Processing Domain**
    - Form submission and validation
    - Lead scoring and qualification
    - Conversion funnel analytics

### 2.5 Database Architecture 🆕

- **Primary**: PostgreSQL for production deployments
- **Secondary**: SQLite for testing and development
- **In-Memory**: For unit testing and fast development cycles
- **Migration Support**: Easy switching between database implementations

## 3. Getting Started

### 3.1 Prerequisites

Before installing the Affiliate Marketing API, ensure your system meets these requirements:

- **Python**: Version 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 512 MB RAM
- **Disk Space**: Minimum 100 MB free space

### 3.2 Installation

#### 3.2.1 Install Python Dependencies

```bash
# Core dependencies
pip install flask pytest

# PostgreSQL support 🆕
pip install psycopg2-binary

# Additional dependencies for full functionality
pip install python-dotenv loguru
```

#### 3.2.2 Database Setup 🆕

**PostgreSQL Installation (Required for Production):**

```bash
# Windows: PostgreSQL is already installed at C:\Program Files\PostgreSQL\18
# The setup scripts will configure it automatically

# Run database setup
python setup_postgres_db.py

# Fix permissions if needed
python fix_postgres_permissions.py
```

#### 3.2.3 Verify Installation

Run the following command to verify installations:

```bash
python --version
pip --version
python test_postgres_connection.py  # Verify PostgreSQL connection 🆕
```

### 3.3 Configuration

#### 3.3.1 Environment Variables

Set the following environment variables before starting the application:

```bash
# Server Configuration
API_HOST=localhost
API_PORT=5000
DEBUG=true

# Security Configuration
SECRET_KEY=your-secret-key-here
RATE_LIMIT_REQUESTS=100

# Database Configuration 🆕
# Primary: PostgreSQL (Production)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=supreme_octosuccotash_db
DB_USER=app_user
DB_PASSWORD=app_password

# Secondary: SQLite (Testing/Development)
SQLITE_PATH=stress_test.db  # Path to SQLite database file (:memory: for in-memory)

# External Services (Optional)
IP_GEOLOCATION_API_KEY=your-api-key
REDIS_URL=redis://localhost:6379
```

#### 3.3.2 Configuration File

Create a `.env` file in the project root with the configuration variables listed above.

#### 3.3.3 Database Selection 🆕

The application automatically selects the database based on configuration:

- **PostgreSQL**: Used when `DB_HOST` and `DB_NAME` are configured (production default)
- **SQLite**: Used when `SQLITE_PATH` is set and PostgreSQL is not available
- **In-Memory**: Used for unit testing and development when no database is configured

### 3.4 Starting the Application

#### 3.4.1 Quick Start with PostgreSQL 🆕

For production-ready deployment with full business logic:

```bash
# Ensure PostgreSQL is running and configured
python test_postgres_connection.py

# Start the application (automatically uses PostgreSQL)
python src/main.py

# In new terminal, test the new business domains
curl http://localhost:5000/ltv/analysis
curl http://localhost:5000/retention/campaigns
curl http://localhost:5000/forms/analytics
```

#### 3.4.2 Development Mode with SQLite

For development and testing with SQLite database:

```bash
# Set SQLite database path
export SQLITE_PATH=stress_test.db
python src/main.py

# Or for in-memory database (fast development)
export SQLITE_PATH=:memory:
python src/main.py
```

#### 3.4.3 Production Mode 🆕

For production deployment with PostgreSQL:

```bash
export DEBUG=false
export SECRET_KEY=your-production-secret-key
export DB_HOST=localhost
export DB_NAME=supreme_octosuccotash_db
export DB_USER=app_user
export DB_PASSWORD=app_password
python src/main.py
```

#### 3.4.4 Verification 🆕

Once started, the API will be available at `http://localhost:5000`. Verify all business domains:

```bash
# Health check
curl http://localhost:5000/v1/health

# LTV Analytics (Customer Lifetime Value)
curl http://localhost:5000/ltv/analysis

# Retention Campaigns
curl http://localhost:5000/retention/campaigns

# Form Analytics
curl http://localhost:5000/forms/analytics

# Campaign Management (Legacy)
curl http://localhost:5000/v1/campaigns
```

**Database Verification:**

```bash
# PostgreSQL: Check tables created
python -c "
import psycopg2
conn = psycopg2.connect('host=localhost dbname=supreme_octosuccotash_db user=app_user password=app_password')
cursor = conn.cursor()
cursor.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\'')
tables = cursor.fetchall()
print('PostgreSQL tables:', [t[0] for t in tables])
conn.close()
"

# SQLite: Check database file
ls -la stress_test.db
```

## 4. Using the Software

### 4.1 API Endpoints

#### 4.1.1 Health and System Endpoints

- `GET /v1/health` - Performs a health check of the API service
- `POST /v1/reset` - Resets all data to initial state (development only)

#### 4.1.2 LTV Analytics Domain 🆕

Customer Lifetime Value analysis and cohort management:

- `GET /ltv/analysis` - Comprehensive LTV analysis with cohort breakdown
- `GET /ltv/customer/{customer_id}` - Detailed LTV information for specific customer
- `GET /ltv/segments` - Overview of LTV segments and customer distribution

#### 4.1.3 Retention Campaigns Domain 🆕

Automated retention campaigns and churn management:

- `GET /retention/campaigns` - List all retention campaigns with status filtering
- `GET /retention/campaign/{campaign_id}/performance` - Detailed campaign performance metrics
- `GET /retention/user/{customer_id}/analysis` - User retention profile and churn risk
- `GET /retention/analytics` - Retention analytics and churn risk distribution

#### 4.1.4 Lead Processing Domain 🆕

Form submissions, lead scoring, and conversion analytics:

- `POST /forms/submit` - Process form submission with validation and lead creation
- `GET /forms/lead/{lead_id}` - Detailed lead information and scoring
- `GET /forms/analytics` - Form analytics and conversion funnel metrics
- `GET /forms/hot-leads` - Retrieve high-scoring leads above threshold

#### 4.1.5 Campaign Management (Legacy)

Traditional affiliate campaign management:

- `GET /v1/campaigns` - Retrieves a list of all campaigns
- `POST /v1/campaigns` - Creates a new campaign
- `GET /v1/campaigns/{id}` - Retrieves details for a specific campaign

#### 4.1.6 Click Tracking (Legacy)

Affiliate click tracking and validation:

- `GET /v1/click` - Tracks a click and performs redirect (used by affiliate links)
- `GET /v1/click/{id}` - Retrieves details for a specific click
- `GET /v1/clicks` - Retrieves a list of all tracked clicks

#### 4.1.7 Analytics and Reporting

Comprehensive analytics across all domains:

- `GET /v1/analytics` - Real-time analytics dashboard
- `GET /v1/analytics/realtime` - Live performance metrics

#### 4.1.8 Development Endpoints

- `GET /mock-safe-page` - Displays a safe landing page for testing
- `GET /mock-offer-page` - Displays an offer landing page for testing

### 4.2 Testing

#### 4.2.1 PostgreSQL Database Testing 🆕

Test the production database setup:

```bash
# Test PostgreSQL connection
python test_postgres_connection.py

# Run PostgreSQL adapter tests (when implemented)
python test_postgres_adapters.py
```

#### 4.2.2 Running Unit Tests

Execute the comprehensive test suite:

```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific domain tests
python -m pytest tests/unit/test_ltv_entity.py -v
python -m pytest tests/unit/test_retention_entity.py -v
python -m pytest tests/unit/test_form_entity.py -v

# Run specific test method
python -m pytest tests/unit/test_campaign_entity.py::TestCampaign::test_campaign_creation -v
```

#### 4.2.3 Integration Testing with Multiple Databases 🆕

Test with different database backends:

**PostgreSQL Integration Testing (Production):**

```bash
# Start server with PostgreSQL
python src/main.py &

# Run comprehensive business domain tests
python scripts/test_endpoints.py

# Test all new endpoints
curl http://localhost:5000/ltv/analysis
curl http://localhost:5000/retention/campaigns
curl -X POST http://localhost:5000/forms/submit -d '{"email":"test@example.com","first_name":"Test"}'
```

**SQLite Integration Testing (Development):**

```bash
# Start server with SQLite
export SQLITE_PATH=stress_test.db
python src/main.py &

# Run tests with SQLite backend
python scripts/test_endpoints.py
```

**Database Content Verification:**

```bash
# PostgreSQL: Check tables and data
python -c "
import psycopg2
conn = psycopg2.connect('host=localhost dbname=supreme_octosuccotash_db user=app_user password=app_password')
cursor = conn.cursor()
cursor.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\'')
tables = cursor.fetchall()
print('PostgreSQL tables:', [t[0] for t in tables])

# Check sample data
cursor.execute('SELECT COUNT(*) FROM customers_ltv')
count = cursor.fetchone()[0]
print(f'LTV records: {count}')
conn.close()
"

# SQLite: Check database file
ls -la stress_test.db
```

#### 4.2.4 Test Coverage Areas 🆕

The comprehensive test suite covers:

- **Domain Entities**: Campaign, LTV, Retention, Lead validation and business rules
- **Value Objects**: Money, URL, LTV segments, and ID generation/validation
- **Domain Services**: LTV calculations, retention analysis, form validation logic
- **Application Layer**: Command and query handlers for all business domains
- **Infrastructure**: Repository implementations (PostgreSQL, SQLite, in-memory)
- **Business Logic**: Real calculations instead of mock data (LTV, churn prediction, lead scoring)

### 4.3 Development Workflow

#### 4.3.1 DDD Code Structure 🆕

Following Domain-Driven Design principles:

- **Domain Layer**: Core business logic, entities, value objects, domain services, repository interfaces (Ports)
- **Application Layer**: Use cases, commands, queries, and handlers (Application Services)
- **Infrastructure Layer**: External concerns, repository implementations (Adapters), external APIs
- **Presentation Layer**: HTTP interfaces, API routes, DTOs (Delivery Mechanisms)

#### 4.3.2 Business Domain Development 🆕

Adding new business domains follows this DDD workflow:

1. **Domain Analysis**
    - Identify business entities and value objects
    - Define domain services and business rules
    - Create repository interfaces (Ports)

2. **Application Layer**
    - Define use cases as commands/queries
    - Implement application handlers
    - Orchestrate domain services

3. **Infrastructure Layer**
    - Implement repository interfaces (Adapters)
    - Add external service integrations
    - Configure database mappings

4. **Presentation Layer**
    - Create API routes and endpoints
    - Define request/response DTOs
    - Add validation and middleware

#### 4.3.3 Example: Adding New Business Domain 🆕

```python
# 1. Domain Layer - Define entities and repository interface
# src/domain/entities/new_feature.py
@dataclass
class NewFeature:
    id: str
    name: str
    # ... business properties

# src/domain/repositories/new_feature_repository.py
class NewFeatureRepository(ABC):
    @abstractmethod
    def save(self, feature: NewFeature) -> None: pass
    @abstractmethod
    def find_by_id(self, feature_id: str) -> Optional[NewFeature]: pass

# 2. Application Layer - Define use cases
# src/application/handlers/new_feature_handler.py
class NewFeatureHandler:
    def __init__(self, repository: NewFeatureRepository):
        self._repository = repository

# 3. Infrastructure Layer - Implement adapters
# src/infrastructure/repositories/postgres_new_feature_repository.py
class PostgresNewFeatureRepository(NewFeatureRepository):
    # PostgreSQL implementation

# 4. Presentation Layer - Add API endpoints
# src/presentation/routes/new_feature_routes.py
class NewFeatureRoutes:
    def __init__(self, handler: NewFeatureHandler):
        self._handler = handler
```

## 5. Reference

### 5.1 Configuration Parameters

#### 5.1.1 Server Configuration

| Parameter  | Description        | Default   | Required |
|------------|--------------------|-----------|----------|
| `API_HOST` | Server hostname    | localhost | No       |
| `API_PORT` | Server port number | 5000      | No       |
| `DEBUG`    | Enable debug mode  | true      | No       |

#### 5.1.2 Database Configuration 🆕

| Parameter     | Description                | Default                  | Required            |
|---------------|----------------------------|--------------------------|---------------------|
| `DB_HOST`     | PostgreSQL server hostname | localhost                | No (for PostgreSQL) |
| `DB_PORT`     | PostgreSQL server port     | 5432                     | No                  |
| `DB_NAME`     | PostgreSQL database name   | supreme_octosuccotash_db | No                  |
| `DB_USER`     | PostgreSQL username        | app_user                 | No                  |
| `DB_PASSWORD` | PostgreSQL password        | app_password             | No                  |
| `SQLITE_PATH` | SQLite database file path  | :memory:                 | No (fallback)       |

#### 5.1.3 Security Configuration

| Parameter             | Description              | Default | Required |
|-----------------------|--------------------------|---------|----------|
| `SECRET_KEY`          | Application secret key   | -       | Yes      |
| `RATE_LIMIT_REQUESTS` | Requests per time window | 100     | No       |

#### 5.1.4 External Services

| Parameter                | Description                | Default | Required |
|--------------------------|----------------------------|---------|----------|
| `IP_GEOLOCATION_API_KEY` | IP geolocation service key | -       | No       |
| `REDIS_URL`              | Redis connection URL       | -       | No       |

### 5.2 Business Rules

#### 5.2.1 LTV Domain Rules 🆕

- **LTV Calculation**: CLV = (Average Order Value × Purchase Frequency) × Customer Lifespan
- **Cohort Analysis**: Customers grouped by acquisition month/quarter with retention tracking
- **Segmentation**: Automatic customer segmentation based on predicted CLV (VIP, High, Medium, Low)
- **Historical Analysis**: Minimum 12-month customer history for reliable LTV predictions
- **Segment Transitions**: Customers can move between segments based on updated behavior

#### 5.2.2 Retention Domain Rules 🆕

- **Churn Risk Assessment**: Multi-factor analysis (recency, frequency, engagement score)
- **Campaign Automation**: Automated campaign creation based on churn predictions
- **User Segmentation**: Dynamic segmentation (New, Active, At-Risk, Low Engagement, Churned)
- **Engagement Scoring**: 0-100 scale based on sessions, clicks, conversions, and session duration
- **Campaign Performance**: Tracking open rates, click rates, and conversion rates

#### 5.2.3 Lead Processing Domain Rules 🆕

- **Form Validation**: Required fields, email format, phone validation, duplicate detection
- **Lead Scoring**: 0-100 scale based on contact completeness, professional info, and engagement
- **Spam Detection**: IP-based rate limiting, suspicious content analysis, honeypot validation
- **Lead Qualification**: Automatic qualification based on score thresholds (Hot: 70+, Qualified: 60+)
- **Conversion Tracking**: Full funnel tracking from submission to final conversion

#### 5.2.4 Campaign Management Rules (Legacy)

- **Status Transitions**: Campaigns follow Draft → Active → Paused/Completed workflow
- **Budget Validation**: Daily budget must not exceed total budget
- **Schedule Validation**: Campaign start date must precede end date
- **Performance Tracking**: System tracks clicks, conversions, CTR, CR, and ROI

#### 5.2.5 Click Tracking and Fraud Prevention (Legacy)

- **Bot Detection**: Analyzes user agent strings for suspicious patterns
- **IP Validation**: Performs geographic and blacklist validation
- **Referrer Validation**: Prevents malicious redirect attempts
- **Rate Limiting**: Implements request throttling to prevent abuse
- **Conversion Attribution**: Tracks sales and lead conversions

#### 5.2.6 Cross-Domain Integration Rules 🆕

- **Customer Journey Tracking**: Unified customer view across all domains
- **Attribution Modeling**: Proper credit assignment for conversions across touchpoints
- **Data Consistency**: Single source of truth for customer and campaign data
- **Real-time Updates**: Live synchronization between domains for accurate analytics

### 5.3 Architecture Components

#### 5.3.1 Domain Layer (Core Business) 🆕

Contains the core business logic and rules following DDD principles:

- **Entities**: Core business objects with identity and lifecycle
- **Value Objects**: Immutable objects representing concepts without identity
- **Domain Services**: Business logic that doesn't naturally fit entities
- **Repository Interfaces**: Abstract contracts for data access (Ports)
- **Domain Events**: Notifications of important business events

#### 5.3.2 Application Layer (Use Cases) 🆕

Orchestrates business use cases following CQRS pattern:

- **Commands**: Write operations that change system state
- **Queries**: Read operations for data retrieval
- **Handlers**: Application services that orchestrate domain operations
- **DTOs**: Data Transfer Objects for request/response contracts

#### 5.3.3 Infrastructure Layer (Adapters) 🆕

Implements external concerns using Adapter pattern:

- **Repository Implementations**: Concrete data access adapters (PostgreSQL, SQLite, In-Memory)
- **External Services**: Adapters for third-party APIs and services
- **Framework Integration**: HTTP frameworks, message queues, caching layers
- **Configuration**: Environment-specific settings and dependency injection

#### 5.3.4 Presentation Layer (Delivery) 🆕

Handles external communication using various delivery mechanisms:

- **REST API**: HTTP endpoints with JSON request/response
- **Middleware**: Cross-cutting concerns (authentication, logging, CORS)
- **Error Handling**: Consistent error responses and exception management
- **API Documentation**: OpenAPI/Swagger specifications

## 6. Troubleshooting

### 6.1 Common Issues

#### 6.1.1 Server Won't Start

**Problem**: Application fails to start on the specified port.

**Possible Causes**:

- Port already in use by another application
- Insufficient permissions to bind to port
- Missing environment variables

**Solutions**:

1. Check if port is available: `netstat -an | grep :5000`
2. Try different port: Set `API_PORT` to an available port
3. Verify environment variables are set correctly

#### 6.1.2 Import Errors

**Problem**: Python import errors during startup.

**Possible Causes**:

- Missing dependencies
- Incorrect Python path
- Virtual environment issues

**Solutions**:

1. Install dependencies: `pip install -r requirements.txt`
2. Activate virtual environment if using one
3. Check Python path: `python -c "import sys; print(sys.path)"`

#### 6.1.3 Database Connection Issues

**Problem**: Unable to connect to external databases.

**Possible Causes**:

- Incorrect connection parameters
- Database server not running
- Network connectivity issues

**Solutions**:

1. Verify database server is running
2. Check connection parameters in environment variables
3. Test network connectivity to database host

#### 6.1.4 Test Failures

**Problem**: Unit tests are failing.

**Possible Causes**:

- Code changes broke existing functionality
- Missing test dependencies
- Environment configuration issues

**Solutions**:

1. Run tests with verbose output: `pytest -v`
2. Check test environment setup
3. Review recent code changes for breaking changes

#### 6.1.5 SQLite Database Issues

**Problem**: SQLite database not working correctly.

**Possible Causes**:

- Incorrect SQLITE_PATH environment variable
- Permission issues with database file location
- Corrupted database file

**Solutions**:

1. Verify SQLITE_PATH is set: `echo $SQLITE_PATH`
2. Check file permissions: `ls -la stress_test.db`
3. Recreate database: `rm stress_test.db && python main_clean.py`
4. Check database integrity:
   `python -c "import sqlite3; sqlite3.connect('stress_test.db').execute('PRAGMA integrity_check').fetchone()"`

### 6.2 Getting Help

If you encounter issues not covered in this troubleshooting section:

1. Check the application logs for error messages
2. Review the test suite for expected behavior
3. Consult the code documentation in docstrings
4. Check GitHub issues for similar problems

## Appendix A: Database Integration

### A.1 Multi-Database Architecture 🆕

The platform supports multiple database implementations with clean architecture:

**Primary Database - PostgreSQL (Production):**

```bash
# Automatic PostgreSQL usage (when configured)
python src/main.py

# Database contains full business data:
# - customer_ltv: LTV calculations and segments
# - cohorts: Cohort analysis data
# - retention_campaigns: Automated retention campaigns
# - churn_predictions: Customer churn risk assessments
# - user_engagement_profiles: User behavior analytics
# - form_submissions: Form processing data
# - leads: Lead management and scoring
```

**Secondary Database - SQLite (Development/Testing):**

```bash
# Fallback to SQLite when PostgreSQL unavailable
export SQLITE_PATH=stress_test.db
python src/main.py

# Or use in-memory SQLite for fast development
export SQLITE_PATH=:memory:
python src/main.py
```

**Testing Database - In-Memory (Unit Tests):**

```python
# Used automatically in unit tests
# No persistence, fast test execution
```

### A.2 Database Schema 🆕

Complete schema for all business domains:

```sql
-- LTV Domain
CREATE TABLE customer_ltv (id, total_revenue, predicted_clv, segment, ...);
CREATE TABLE cohorts (id, name, customer_count, total_revenue, retention_rates, ...);
CREATE TABLE ltv_segments (id, name, min_ltv, max_ltv, customer_count, ...);

-- Retention Domain
CREATE TABLE retention_campaigns (id, name, status, triggers, budget, ...);
CREATE TABLE churn_predictions (customer_id, churn_probability, risk_level, ...);
CREATE TABLE user_engagement_profiles (customer_id, engagement_score, segment, ...);

-- Lead Processing Domain
CREATE TABLE form_submissions (id, form_id, form_data, is_valid, ...);
CREATE TABLE leads (id, email, lead_score, status, tags, ...);
CREATE TABLE lead_scores (lead_id, total_score, grade, is_hot_lead, ...);
CREATE TABLE validation_rules (id, field_name, rule_type, error_message, ...);
```

### A.3 Business Domain Expansion 🆕

Current implementation includes three core business domains:

**LTV Domain:**

- ✅ Customer Lifetime Value calculations
- ✅ Cohort analysis and segmentation
- ✅ Predictive CLV modeling

**Retention Domain:**

- ✅ Automated retention campaigns
- ✅ Churn prediction algorithms
- ✅ User engagement profiling

**Lead Processing Domain:**

- ✅ Form validation and processing
- ✅ Lead scoring and qualification
- ✅ Conversion funnel analytics

### A.4 Future Enhancements

**Phase 2 Features:**

- **JWT Authentication**: Replace current API key authentication
- **Redis Caching**: Implement caching for analytics and sessions
- **Async Processing**: Add background job processing capabilities
- **API Versioning**: Implement v1/v2 endpoint management
- **Monitoring**: Add Prometheus metrics and health checks

**Phase 3 - Microservices:**
Future versions may include splitting into separate services:

- **Campaign Service**: Dedicated campaign management
- **LTV Service**: Specialized lifetime value analytics
- **Retention Service**: Advanced retention and churn management
- **Lead Service**: Comprehensive lead processing and CRM integration
- **Auth Service**: Centralized authentication and authorization

## Appendix B: Code Quality Improvements

### B.1 Original Implementation

The initial codebase had typical monolithic architecture issues:

- **Mock Data**: Extensive use of hardcoded mock responses
- **Tight Coupling**: Business logic mixed with HTTP handlers
- **Single Database**: Only SQLite support, no production database
- **Limited Domains**: Only basic campaign and click tracking
- **No DDD**: Traditional layered architecture without domain modeling

### B.2 Current DDD Implementation 🆕

The refactored codebase implements modern software architecture:

**Domain-Driven Design:**

- ✅ **Ubiquitous Language**: Business domain terminology throughout codebase
- ✅ **Bounded Contexts**: Separate domains for LTV, Retention, and Lead Processing
- ✅ **Entities & Value Objects**: Rich domain modeling with business rules
- ✅ **Domain Services**: Business logic encapsulated in domain services
- ✅ **Repository Pattern**: Clean data access abstractions (Ports & Adapters)

**Clean Architecture:**

- ✅ **Dependency Inversion**: Business logic doesn't depend on external frameworks
- ✅ **Single Responsibility**: Each class has one reason to change
- ✅ **Open/Closed**: Open for extension, closed for modification
- ✅ **Interface Segregation**: Client-specific interfaces
- ✅ **Dependency Injection**: Clean dependency management via container

**Production Quality:**

- ✅ **Real Business Logic**: No more mock data - full LTV, retention, and lead processing
- ✅ **PostgreSQL Support**: Production-ready database with proper schema
- ✅ **Error Handling**: Comprehensive exception handling and logging
- ✅ **Type Safety**: Full type hints with modern Python typing
- ✅ **Configuration**: Environment-based config without hardcoded values

## Appendix C: Benefits Achieved

The DDD refactoring with PostgreSQL integration provides comprehensive benefits:

### 🏗️ **Architecture Benefits**

1. **Domain-Driven Design**: Business logic modeled using domain expert terminology
2. **Clean Architecture**: Dependency inversion with business logic independent of frameworks
3. **Hexagonal Architecture**: Ports & Adapters pattern for external concerns
4. **CQRS Pattern**: Separate read/write models optimized for their use cases

### 💼 **Business Benefits**

1. **Complete Business Logic**: Full LTV calculations, retention campaigns, and lead processing
2. **Real Analytics**: Production-ready analytics instead of mock data
3. **Multi-Domain Support**: Three distinct business domains working together
4. **Automated Processes**: Self-managing retention campaigns and lead scoring

### 🛠️ **Technical Benefits**

1. **PostgreSQL Production Database**: ACID-compliant, scalable data persistence
2. **Multi-Database Support**: Easy switching between PostgreSQL, SQLite, and In-Memory
3. **Type Safety**: Full Python typing with modern type hints
4. **Dependency Injection**: Clean dependency management via container pattern
5. **Comprehensive Testing**: Business logic tested with real database operations

### 👥 **Developer Experience**

1. **Clear Code Organization**: Domain, Application, Infrastructure, Presentation layers
2. **Easy Maintenance**: Changes isolated to specific architectural boundaries
3. **Framework Independence**: Business logic not tied to external frameworks
4. **Rich Domain Models**: Entities and value objects with business behavior
5. **Comprehensive Documentation**: API docs, business rules, and architecture guides

### 📊 **Production Readiness**

1. **Database Migrations**: Automatic schema creation and management
2. **Error Handling**: Comprehensive exception handling and logging
3. **Configuration Management**: Environment-based configuration
4. **Security**: Input validation, fraud prevention, and secure data handling
5. **Monitoring Ready**: Structured for adding metrics and health checks

### 🚀 **Scalability & Performance**

1. **Database Optimization**: Proper indexing and query optimization
2. **Connection Pooling**: Efficient database connection management
3. **Async Ready**: Architecture prepared for async operations
4. **Caching Ready**: Infrastructure prepared for Redis/memcached integration

The platform is now a production-ready, enterprise-grade affiliate marketing system with real business value, following
modern software architecture best practices.
