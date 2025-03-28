# Receipt Scanner

A modern Python API template demonstrating **Vertical Slice Architecture** complemented by **Domain-Driven Design (DDD)** and clean architecture principles, with advanced AI capabilities for receipt analysis. While implemented as a receipt scanner, this project serves as a robust reference architecture for building scalable, type-safe APIs.

## Core Technologies

### API Framework
- **FastAPI**: Modern web framework with automatic OpenAPI documentation
- **SQLModel**: Type-safe ORM combining SQLAlchemy and Pydantic
- **Pydantic**: Data validation and settings management

### AI Integration
- **Pydantic AI**: Structured AI response handling and validation
- **Gemini Vision**: Advanced image analysis and text extraction

## Architecture & Design

### Patterns
- **Vertical Slice Architecture**: Organizing codebase into self-contained, feature-specific modules
- **Domain-Driven Design**: Explicit modeling of business logic and domain boundaries within each vertical slice
- **Clean Architecture**: Separation of concerns across layers
  - Data Models
  - Services
  - API Endpoints
- **Asynchronous Design**: Non-blocking operations throughout
- **Dependency Injection**: Modular and testable components

### Infrastructure
- **Database**: PostgreSQL with async drivers
- **Containerization**: Docker-based development and deployment
- **CI Pipeline**: Automated testing and quality checks

## Quality & Development

### Code Quality
- **Type Safety**: Comprehensive type hints and validation
- **Linting**: Automated code formatting with Ruff
- **Testing**: Pytest suite with async support and coverage
- **Documentation**: Auto-generated OpenAPI specs

### Developer Tools
- **Migration System**: Version-controlled schema changes
- **Development Scripts**: Streamlined workflow commands
- **Environment Management**: Containerized development
- **Hot Reload**: Automatic server restart on changes

## Documentation

- [Development Guide](DEVELOPMENT.md)
- API Reference:
  - Interactive (Swagger) - http://localhost:8000/docs
  - Reference (ReDoc) - http://localhost:8000/redoc

## License

See [LICENSE](LICENSE) file.
