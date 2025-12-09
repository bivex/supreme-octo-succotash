# Affiliate Marketing API - User Documentation

## 1. Introduction

### 1.1 Purpose
This document provides comprehensive guidance for developers and system administrators working with the Affiliate Marketing API, a refactored implementation using Clean Architecture principles. The API serves as a backend service for managing affiliate marketing campaigns, tracking clicks, and providing analytics.

### 1.2 Scope
This documentation covers:
- Installation and configuration of the Affiliate Marketing API
- API usage and endpoint descriptions
- Testing procedures and guidelines
- Configuration management
- Business rules and validation logic
- Troubleshooting common issues
- Future enhancement roadmap

### 1.3 Audience
This document is intended for:
- **Software Developers**: Implementing client applications that integrate with the API
- **System Administrators**: Deploying and maintaining the API service
- **Quality Assurance Engineers**: Testing API functionality and performance
- **DevOps Engineers**: Configuring and monitoring production deployments

### 1.4 Conventions Used in This Document
- **API endpoints** are shown in `monospace font`
- **Command-line instructions** are presented in code blocks with bash syntax highlighting
- **File paths** use forward slashes (/) for consistency
- **Important notes** are highlighted with ℹ️ symbol
- **Warning messages** are highlighted with ⚠️ symbol

## 2. Overview of the Software

### 2.1 Software Description
The Affiliate Marketing API is a RESTful web service that provides comprehensive affiliate marketing functionality including campaign management, click tracking, fraud prevention, and performance analytics. The software has been refactored using Clean Architecture principles to ensure maintainability, testability, and scalability.

### 2.2 Key Features
- **Campaign Management**: Create, update, and monitor affiliate marketing campaigns
- **Click Tracking**: Track and validate affiliate clicks with fraud prevention
- **Analytics**: Real-time performance metrics and reporting
- **Security**: Comprehensive input validation and fraud detection
- **Clean Architecture**: Modular design with clear separation of concerns

### 2.3 Architecture Overview
The application follows Clean Architecture with four distinct layers:

```
src/
├── domain/           # Business logic and rules
│   ├── entities/     # Core business objects (Campaign, Click, etc.)
│   ├── value_objects/# Value objects (Money, URL, etc.)
│   ├── services/     # Domain services (validation, business rules)
│   └── repositories/ # Repository interfaces (contracts)
├── application/      # Use cases and orchestration
│   ├── commands/     # Command objects for write operations
│   ├── handlers/     # Command/query handlers
│   └── queries/      # Query objects for read operations
├── infrastructure/   # External concerns and implementations
│   ├── repositories/ # Repository implementations (in-memory)
│   └── external/     # External service adapters
├── presentation/     # HTTP layer and APIs
│   ├── routes/       # Flask route handlers
│   ├── dto/          # Data Transfer Objects
│   └── middleware/   # HTTP middleware
└── config/          # Configuration management
```

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
pip install flask pytest
```

#### 3.2.2 Verify Installation
Run the following command to verify Python is properly installed:
```bash
python --version
pip --version
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

# External Services (Optional)
IP_GEOLOCATION_API_KEY=your-api-key
REDIS_URL=redis://localhost:6379

# Database Configuration (Future use)
DB_HOST=localhost
DB_NAME=affiliate_db
DB_USER=your-username
DB_PASSWORD=your-password
```

#### 3.3.2 Configuration File
Alternatively, create a `.env` file in the project root with the configuration variables listed above.

### 3.4 Starting the Application

#### 3.4.1 Development Mode
To start the application in development mode:
```bash
python main_clean.py
```

#### 3.4.2 Production Mode
For production deployment, set `DEBUG=false` and configure appropriate security settings.

#### 3.4.3 Verification
Once started, the API will be available at `http://localhost:5000`. Verify the installation by accessing the health endpoint:
```bash
curl http://localhost:5000/v1/health
```

## 4. Using the Software

### 4.1 API Endpoints

#### 4.1.1 Health and System Endpoints
- `GET /v1/health` - Performs a health check of the API service
- `POST /v1/reset` - Resets all mock data to initial state

#### 4.1.2 Campaign Management
- `GET /v1/campaigns` - Retrieves a list of all campaigns
- `POST /v1/campaigns` - Creates a new campaign
- `GET /v1/campaigns/{id}` - Retrieves details for a specific campaign

#### 4.1.3 Click Tracking
- `GET /v1/click` - Tracks a click and performs redirect (used by affiliate links)
- `GET /v1/click/{id}` - Retrieves details for a specific click
- `GET /v1/clicks` - Retrieves a list of all tracked clicks

#### 4.1.4 Mock Landing Pages
- `GET /mock-safe-page` - Displays a safe landing page for testing
- `GET /mock-offer-page` - Displays an offer landing page for testing

### 4.2 Testing

#### 4.2.1 Running Unit Tests
Execute the test suite using pytest:
```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test class
python -m pytest tests/unit/test_campaign_entity.py -v

# Run specific test method
python -m pytest tests/unit/test_campaign_entity.py::TestCampaign::test_campaign_creation -v
```

#### 4.2.2 Test Coverage Areas
The test suite covers:
- **Domain Entities**: Campaign and Click validation, business rules
- **Value Objects**: Money, URL, and ID generation/validation
- **Application Layer**: Command and query handling
- **Infrastructure**: Repository implementations

### 4.3 Development Workflow

#### 4.3.1 Code Structure
- **Domain Layer**: Contains business logic and rules
- **Application Layer**: Handles use cases and orchestrates operations
- **Infrastructure Layer**: Implements external concerns and data persistence
- **Presentation Layer**: Manages HTTP interfaces and API endpoints

#### 4.3.2 Adding New Features
1. Define domain entities and value objects
2. Create application commands/queries
3. Implement handlers in the application layer
4. Add repository interfaces in the domain layer
5. Implement repository interfaces in the infrastructure layer
6. Create API routes in the presentation layer

## 5. Reference

### 5.1 Configuration Parameters

#### 5.1.1 Server Configuration
| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `API_HOST` | Server hostname | localhost | No |
| `API_PORT` | Server port number | 5000 | No |
| `DEBUG` | Enable debug mode | true | No |

#### 5.1.2 Security Configuration
| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `SECRET_KEY` | Application secret key | - | Yes |
| `RATE_LIMIT_REQUESTS` | Requests per time window | 100 | No |

#### 5.1.3 External Services
| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `IP_GEOLOCATION_API_KEY` | IP geolocation service key | - | No |
| `REDIS_URL` | Redis connection URL | - | No |

### 5.2 Business Rules

#### 5.2.1 Campaign Management Rules
- **Status Transitions**: Campaigns follow Draft → Active → Paused/Completed workflow
- **Budget Validation**: Daily budget must not exceed total budget
- **Schedule Validation**: Campaign start date must precede end date
- **Performance Tracking**: System tracks clicks, conversions, CTR, CR, and ROI

#### 5.2.2 Click Tracking and Fraud Prevention
- **Bot Detection**: Analyzes user agent strings for suspicious patterns
- **IP Validation**: Performs geographic and blacklist validation
- **Referrer Validation**: Prevents malicious redirect attempts
- **Rate Limiting**: Implements request throttling to prevent abuse
- **Conversion Attribution**: Tracks sales and lead conversions

#### 5.2.3 Analytics Rules
- **Real-time Metrics**: Provides live tracking of clicks, conversions, and revenue
- **Performance Calculations**: Computes CTR, CR, EPC, and ROI metrics
- **Breakdown Analysis**: Supports analysis by date, source, and landing page

### 5.3 Architecture Components

#### 5.3.1 Domain Layer
Contains the core business logic and rules that are independent of any external frameworks.

#### 5.3.2 Application Layer
Orchestrates use cases and contains commands and queries that represent user intentions.

#### 5.3.3 Infrastructure Layer
Implements external concerns such as data persistence, external APIs, and framework integrations.

#### 5.3.4 Presentation Layer
Handles HTTP requests, responses, and provides the API interface to clients.

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

### 6.2 Getting Help

If you encounter issues not covered in this troubleshooting section:
1. Check the application logs for error messages
2. Review the test suite for expected behavior
3. Consult the code documentation in docstrings
4. Check GitHub issues for similar problems

## Appendix A: Future Enhancements

### A.1 Database Integration
The application is designed to support various database backends. To migrate from in-memory storage to PostgreSQL:

```python
# In src/container.py, replace:
from infrastructure.repositories.in_memory_campaign_repository import InMemoryCampaignRepository

# With:
from infrastructure.repositories.postgresql_campaign_repository import PostgreSQLCampaignRepository
```

### A.2 Planned Features
- **JWT Authentication**: Replace current API key authentication
- **Redis Caching**: Implement caching for analytics and sessions
- **Async Processing**: Add background job processing capabilities
- **API Versioning**: Implement v1/v2 endpoint management
- **Monitoring**: Add Prometheus metrics and health checks

### A.3 Microservices Architecture
Future versions may include splitting into separate services:
- **Campaign Service**: Dedicated campaign management
- **Click Service**: Specialized click tracking and analytics
- **Auth Service**: Centralized authentication and authorization

## Appendix B: Code Quality Improvements

### B.1 Before Refactoring
The original codebase exhibited several quality issues:
- **Code Smells**: Over 250 identified issues
- **Architecture**: Monolithic design with mixed concerns
- **Testability**: Difficult to test business logic in isolation
- **Maintainability**: Hard to modify and extend functionality

### B.2 After Refactoring
The refactored codebase provides significant improvements:
- **Clean Separation**: Clear domain, application, infrastructure, and presentation layers
- **SOLID Compliance**: Proper application of software design principles
- **Test Coverage**: Comprehensive unit tests for core business logic
- **Type Safety**: Full type hints compatible with mypy
- **Configuration**: Environment-based configuration without hardcoded values

## Appendix C: Benefits Achieved

The refactoring provides the following key benefits:

1. **Maintainability**: Changes are isolated to specific architectural layers
2. **Testability**: Domain logic can be tested without external dependencies
3. **Scalability**: Easy to add new features and swap implementations
4. **Security**: Comprehensive input validation and fraud prevention
5. **Developer Experience**: Clear code structure with type hints and documentation
6. **Production Readiness**: Proper error handling, logging, and configuration management

The refactored codebase follows industry best practices and is prepared for production deployment with proper database integration and monitoring capabilities.
