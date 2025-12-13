# Admin Panel - Clean Architecture & DDD Implementation

## Architecture Overview

This application follows **Domain-Driven Design (DDD)**, **Clean Architecture**, **Hexagonal Architecture (Ports & Adapters)**, and **SOLID Principles**.

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  (PyQt6 UI, Views, Dialogs, ViewModels, Dark Theme)        │
│  Depends on: Application Layer                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│  (Use Cases, DTOs, Application Services)                    │
│  Depends on: Domain Layer (entities, repositories)          │
│  Defines: Ports for infrastructure                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                     DOMAIN LAYER                             │
│  ✓ Entities (Campaign, Goal, Click, Conversion)            │
│  ✓ Value Objects (Money, Budget, DateRange)                │
│  ✓ Repository Interfaces (Ports)                            │
│  ✓ Domain Services                                          │
│  ✓ Domain Exceptions                                        │
│  Dependencies: NONE (Pure business logic)                   │
└─────────────────────────────────────────────────────────────┘
                   ▲
┌──────────────────┴──────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                         │
│  (Adapters implementing domain ports)                        │
│  - API Client Adapter                                        │
│  - Repository Implementations                                │
│  - Configuration                                             │
│  - Logging                                                   │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Domain Layer (`domain/`)
- **Pure business logic** with zero external dependencies
- **Entities**: Objects with identity (Campaign, Goal, etc.)
- **Value Objects**: Immutable objects (Money, Budget, DateRange)
- **Repository Interfaces**: Contracts for persistence (ports)
- **Domain Events**: Business-significant occurrences
- **Domain Services**: Operations that don't belong to entities
- **Invariants**: Business rules enforced within entities

### Application Layer (`application/`)
- **Use Cases**: Orchestrate domain operations
- **DTOs**: Data transfer objects for layer boundaries
- **Application Services**: Coordinate use cases
- **Ports**: Interfaces for external services (notifications, etc.)

### Infrastructure Layer (`infrastructure/`)
- **Adapters**: Implement domain/application ports
- **API Client**: HTTP communication with backend
- **Repositories**: Data persistence implementations
- **Configuration**: External config (env vars, files)
- **Logging**: Structured logging

### Presentation Layer (`presentation/`)
- **Views**: PyQt6 UI components
- **Dialogs**: Modal windows for user input
- **View Models**: UI state management
- **Styles**: Dark theme CSS

## SOLID Principles Applied

### Single Responsibility Principle (SRP)
- Each module has one reason to change
- Entities manage their own invariants
- Use cases handle single business operations
- Repositories handle only data access

### Open/Closed Principle (OCP)
- Extend behavior via new implementations
- Repository interfaces allow multiple implementations
- Strategy pattern for different budget types

### Liskov Substitution Principle (LSP)
- All repository implementations are interchangeable
- Subtypes don't break client expectations

### Interface Segregation Principle (ISP)
- Small, focused repository interfaces
- Clients depend only on methods they use

### Dependency Inversion Principle (DIP)
- High-level modules depend on abstractions
- Domain defines repository interfaces
- Infrastructure implements them
- Dependencies injected via constructor

## Key Patterns

### Hexagonal Architecture (Ports & Adapters)
- **Ports**: Interfaces defined by domain/application
- **Adapters**: Infrastructure implementations
- **Primary Adapters**: UI, API controllers (drive the app)
- **Secondary Adapters**: Databases, external APIs (driven by app)

### Repository Pattern
- Abstract data access behind interfaces
- Domain doesn't know about persistence details

### Factory Pattern
- Entity creation encapsulated in factory methods
- Example: `Campaign.create(...)`

### Dependency Injection
- All dependencies injected via constructors
- DI container wires up the application
- No service locators or global state

## Domain Model

### Aggregates
**Campaign** (Aggregate Root)
- Identity: `id`
- Value Objects: `Budget`, `DateRange`
- Business Rules:
  - Must have positive budget
  - Can only pause active campaigns
  - Cannot modify completed campaigns
  - Target URL must be valid HTTP(S)

**Goal** (Entity)
- Belongs to Campaign
- Has monetary value
- Can match URLs for conversion tracking

### Value Objects
**Money**
- Immutable
- Currency-aware
- Prevents negative amounts

**Budget**
- Composition of Money + BudgetType
- Enforces positive amounts

**DateRange**
- Start and optional end date
- Validates start < end

## Data Flow

### Creating a Campaign (Write Operation)
```
UI (Dialog) → Use Case → Domain Entity → Repository → API → Backend
```

1. User fills `CampaignDialog`
2. Presentation calls `CreateCampaignUseCase`
3. Use case creates domain `Campaign` entity
4. Campaign validates its invariants
5. Use case calls repository.save()
6. Repository adapter calls API client
7. Response mapped back to domain entity
8. Use case returns DTO to UI

### Listing Campaigns (Read Operation)
```
UI (View) → Use Case → Repository → API → Mapper → DTOs → UI
```

1. View requests campaign list
2. `ListCampaignsUseCase` called
3. Repository fetches from API
4. Entities created from API response
5. Use case converts to DTOs
6. DTOs returned to UI for display

## Testing Strategy

### Unit Tests (Fast, Isolated)
- Domain entities and value objects
- Use cases with mocked repositories
- Business rule validation

### Integration Tests
- Repository implementations against real API
- End-to-end use case flows

### UI Tests
- Critical user workflows
- Visual regression tests

## Configuration

### Environment-based
- API URLs
- Authentication tokens
- Feature flags

### Never in Code
- Secrets
- API keys
- Environment-specific settings

## Error Handling

### Domain Exceptions
- `ValidationError`: Business rule violations
- `EntityNotFoundError`: Missing entities
- `InvalidBudgetError`: Budget constraints

### Application Layer
- Catches domain exceptions
- Translates to user-friendly messages
- Logs errors appropriately

### Infrastructure Layer
- Network errors
- API errors (4xx, 5xx)
- Retry logic with exponential backoff

## Security

- Authentication via bearer tokens
- Input validation at boundaries
- No sensitive data in logs
- SQL injection prevention (N/A - REST API)

## Observability

- Structured logging
- Key events logged
- Performance metrics
- Error tracking

## Benefits of This Architecture

1. **Testability**: Domain logic tested in isolation
2. **Maintainability**: Clear separation of concerns
3. **Flexibility**: Easy to swap implementations
4. **Independence**: Domain doesn't depend on frameworks
5. **Scalability**: Can split into microservices if needed
6. **Team Collaboration**: Clear boundaries between teams
7. **Onboarding**: New developers understand structure quickly

## Trade-offs

- More files and folders
- Initial complexity
- Requires discipline
- Mapping between layers (DTOs ↔ Entities)

For a team working on a long-lived, business-critical application, these trade-offs are worthwhile.
