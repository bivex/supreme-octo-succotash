# PostgreSQL Adapters for DDD Architecture

This document describes the PostgreSQL adapters (implementations) for the Domain-Driven Design (DDD) architecture in the Supreme Octo Succotash project.

## 📋 Overview

Following DDD principles, we maintain clean separation between:
- **Domain Layer** - Business logic and entities (ports/interfaces)
- **Infrastructure Layer** - Database implementations (adapters)
- **Application Layer** - Use cases and handlers
- **Presentation Layer** - API routes and controllers

## 🏗️ Architecture

```
Domain Layer (Ports/Interfaces)
├── repositories/
│   ├── ltv_repository.py
│   ├── retention_repository.py
│   └── form_repository.py

Infrastructure Layer (Adapters/Implementations)
├── repositories/
│   ├── postgres_ltv_repository.py      ← PostgreSQL Adapter
│   ├── postgres_retention_repository.py ← PostgreSQL Adapter
│   ├── postgres_form_repository.py     ← PostgreSQL Adapter
│   ├── in_memory_*_repository.py       ← In-Memory Adapters (dev/test)
│   └── sqlite_*_repository.py          ← SQLite Adapters (dev/test)

Application Layer
├── handlers/
│   ├── ltv_handler.py
│   ├── retention_handler.py
│   └── form_handler.py

Presentation Layer
├── routes/
│   ├── ltv_routes.py
│   ├── retention_routes.py
│   └── form_routes.py
```

## 🚀 Quick Start

### 1. Database Setup

```bash
# Run the database setup script
python setup_postgres_db.py
```

This creates:
- Database: `supreme_octosuccotash_db`
- User: `app_user` with password `app_password`
- Required tables and indexes

### 2. Test Adapters

```bash
# Test all PostgreSQL adapters
python test_postgres_adapters.py
```

### 3. Run Application

```python
# The container automatically uses PostgreSQL repositories
from src.container import container

# Get PostgreSQL-backed handlers
ltv_handler = container.get_ltv_handler()  # Uses PostgresLTVRepository
retention_handler = container.get_retention_handler()  # Uses PostgresRetentionRepository
form_handler = container.get_form_handler()  # Uses PostgresFormRepository
```

## 📊 Repository Interfaces (Ports)

### LTV Repository
```python
class LTVRepository(ABC):
    def save_customer_ltv(self, customer_ltv: CustomerLTV) -> None
    def get_customer_ltv(self, customer_id: str) -> Optional[CustomerLTV]
    def get_customers_by_segment(self, segment: str, limit: int = 100) -> List[CustomerLTV]
    def save_cohort(self, cohort: Cohort) -> None
    def get_cohort(self, cohort_id: str) -> Optional[Cohort]
    def get_ltv_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]
    # ... more methods
```

### Retention Repository
```python
class RetentionRepository(ABC):
    def save_retention_campaign(self, campaign: RetentionCampaign) -> None
    def get_retention_campaign(self, campaign_id: str) -> Optional[RetentionCampaign]
    def save_churn_prediction(self, prediction: ChurnPrediction) -> None
    def get_churn_prediction(self, customer_id: str) -> Optional[ChurnPrediction]
    def save_user_engagement_profile(self, profile: UserEngagementProfile) -> None
    def get_retention_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]
    # ... more methods
```

### Form Repository
```python
class FormRepository(ABC):
    def save_form_submission(self, submission: FormSubmission) -> None
    def get_form_submission(self, submission_id: str) -> Optional[FormSubmission]
    def save_lead(self, lead: Lead) -> None
    def get_lead(self, lead_id: str) -> Optional[Lead]
    def get_lead_by_email(self, email: str) -> Optional[Lead]
    def get_form_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]
    # ... more methods
```

## 🗄️ PostgreSQL Adapters (Implementations)

### Features

✅ **Connection Management**
- Automatic connection pooling
- Connection retry logic
- Proper connection cleanup

✅ **Data Persistence**
- ACID transactions
- JSONB support for complex data
- Optimized indexes
- Foreign key relationships

✅ **Performance**
- Prepared statements
- Batch operations support
- Query optimization

✅ **Error Handling**
- Graceful error handling
- Detailed logging
- Transaction rollback on errors

### Database Schema

#### Tables Created

1. **customer_ltv** - Customer Lifetime Value data
2. **cohorts** - Cohort analysis data
3. **ltv_segments** - LTV segment definitions
4. **retention_campaigns** - Retention campaign data
5. **churn_predictions** - Customer churn predictions
6. **user_engagement_profiles** - User engagement metrics
7. **form_submissions** - Form submission data
8. **leads** - Lead information
9. **lead_scores** - Lead scoring data
10. **validation_rules** - Form validation rules

### Configuration

```python
# Default configuration in container.py
PostgresLTVRepository(
    host="localhost",
    port=5432,
    database="supreme_octosuccotash_db",
    user="app_user",
    password="app_password"
)
```

## 🧪 Testing

### Unit Tests
```bash
# Test individual adapters
python -m pytest tests/unit/test_postgres_ltv_repository.py
python -m pytest tests/unit/test_postgres_retention_repository.py
python -m pytest tests/unit/test_postgres_form_repository.py
```

### Integration Tests
```bash
# Test with real PostgreSQL database
python -m pytest tests/integration/test_postgres_adapters.py
```

### Manual Testing
```bash
# Run the test script
python test_postgres_adapters.py
```

## 🔄 Switching Between Databases

The architecture supports multiple database implementations:

```python
# In container.py - switch implementations easily

# For development (fast, in-memory)
def get_ltv_repository(self):
    return InMemoryLTVRepository()

# For testing (persistent, fast)
def get_ltv_repository(self):
    return SQLiteLTVRepository(":memory:")

# For production (scalable, robust)
def get_ltv_repository(self):
    return PostgresLTVRepository(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
```

## 📈 Performance Considerations

### Indexes
- Primary keys on all tables
- Foreign key indexes
- JSONB GIN indexes for JSON queries
- Composite indexes for common query patterns

### Connection Pooling
```python
# For high-traffic applications, consider connection pooling
from psycopg2.pool import SimpleConnectionPool

pool = SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    host="localhost",
    database="supreme_octosuccotash_db",
    user="app_user",
    password="app_password"
)
```

### Query Optimization
- Use `EXPLAIN ANALYZE` to optimize slow queries
- Consider partitioning for large tables
- Use appropriate data types (INET for IPs, JSONB for flexible data)

## 🔧 Maintenance

### Backup
```bash
# Backup database
pg_dump -U app_user -h localhost supreme_octosuccotash_db > backup.sql

# Restore database
psql -U app_user -h localhost -d supreme_octosuccotash_db < backup.sql
```

### Monitoring
```sql
-- Check active connections
SELECT * FROM pg_stat_activity;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🚨 Troubleshooting

### Common Issues

1. **Connection refused**
   ```bash
   # Check PostgreSQL status
   pg_isready -h localhost -p 5432

   # Start PostgreSQL service
   sudo systemctl start postgresql  # Linux
   # or Windows Services → postgresql-x64-18 → Start
   ```

2. **Authentication failed**
   ```sql
   -- Change password in psql
   ALTER USER app_user PASSWORD 'new_password';
   ```

3. **Permission denied**
   ```sql
   -- Grant permissions
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;
   ```

## 📚 API Usage Examples

### LTV Analytics
```python
from src.container import container

ltv_handler = container.get_ltv_handler()

# Get LTV analysis
analysis = ltv_handler.get_ltv_analysis()
print(f"Average LTV: ${analysis['average_ltv']}")

# Get customer details
customer = ltv_handler.get_customer_ltv_details("customer_123")
print(f"Customer segment: {customer['segment']}")
```

### Retention Campaigns
```python
retention_handler = container.get_retention_handler()

# Get active campaigns
campaigns = retention_handler.get_retention_campaigns()
print(f"Active campaigns: {len(campaigns['campaigns'])}")

# Analyze user retention
analysis = retention_handler.analyze_user_retention("user_456")
print(f"Churn risk: {analysis['churn_risk']['risk_level']}")
```

### Form Processing
```python
form_handler = container.get_form_handler()

# Submit form
result = form_handler.submit_form({
    "email": "user@example.com",
    "first_name": "John",
    "company": "Acme Corp"
})
print(f"Lead created: {result['lead_id']}")

# Get analytics
analytics = form_handler.get_form_analytics()
print(f"Total submissions: {analytics['submission_metrics']['total_submissions']}")
```

## 🎯 Best Practices

1. **Repository Pattern** - Always use repositories, never direct database access
2. **Dependency Injection** - Container manages all dependencies
3. **Transaction Management** - Use database transactions for data consistency
4. **Connection Management** - Properly close connections
5. **Error Handling** - Implement comprehensive error handling
6. **Testing** - Test with real database, not just mocks
7. **Migrations** - Use proper database migration tools for schema changes

## 🔗 Related Documentation

- [DDD Architecture Overview](./README.md)
- [API Documentation](./openapi.yaml)
- [Business Logic](./scripts/check_BL.py)
- [PostgreSQL Official Documentation](https://www.postgresql.org/docs/)

---

**Your DDD application now supports PostgreSQL as the primary database with clean architecture!** 🎉
