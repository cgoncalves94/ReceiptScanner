# Receipt Scanner

A modern Python API template showcasing the integration of FastAPI, SQLModel, async database operations, Pydantic, and Pydantic AI. While implemented as a receipt scanner, this project serves as a reference architecture for building robust APIs with these technologies.

## Technical Overview

This project demonstrates the powerful combination of:

- **FastAPI**: High-performance async web framework with automatic OpenAPI documentation
- **SQLModel**: Unified model system combining SQLAlchemy and Pydantic for type-safe ORM
- **Async Database Operations**: Full async/await pattern for database interactions
- **Pydantic**: Type validation and settings management
- **Pydantic AI**: Structured AI response handling with Gemini Vision integration

The project also implements:

- Domain-driven design organization
- Clean architecture with proper separation of concerns:
  - **Data/Model Layer**: Defines data structures and validation rules using SQLModel and Pydantic
  - **Repository Layer**: Manages data access and persistence operations
  - **Service Layer**: Handles business logic, validation, and orchestration
- Dependency injection pattern with efficient resource management
- Comprehensive error handling with FastAPI's exception handler system
- Docker containerization
- CI workflow with pre-commit hooks for code quality

## Development

For detailed development setup and instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## License

See [LICENSE](LICENSE) file.
