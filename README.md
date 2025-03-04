# Receipt Scanner API

A modern FastAPI application for scanning and analyzing receipts using Google's Gemini Vision API.

## Technical Overview

This project demonstrates several modern architectural patterns and technologies:

### Clean Architecture & AI Pipeline

- **Computer Vision Processing**: OpenCV-based preprocessing for image enhancement
- **Gemini Vision AI**: Advanced receipt text extraction and analysis
- **Structured Data Extraction**: Intelligent parsing of receipt information
- **Automatic Categorization**: Smart classification of receipt items

### Modern Backend Architecture

- **API Layer**: FastAPI routes with dependency injection and validation
- **Service Layer**: Business logic orchestration with transaction management
- **Repository Layer**: Clean data access abstraction with SQLModel
- **Domain Layer**: Unified Pydantic/SQLModel schemas

### Advanced Patterns

- **Repository Pattern**: Decoupled data access with clean abstractions
- **Unit of Work**: Transaction management with SAVEPOINT support
- **Async Architecture**: Non-blocking operations from API to database
- **Error Handling**: Global exception handlers with proper mapping

### Project Structure
```
app/
├── api/          # REST endpoints, route handlers, and request/response models
├── core/         # Application core: config, DB setup, exceptions, decorators
├── integrations/ # External service integrations
├── middlewares/  # Request/response middleware, error handlers, auth
├── models/       # Domain models combining SQLModel (ORM) and Pydantic schemas
├── repositories/ # Data access layer with database operations
├── services/     # Business logic and service orchestration
└── main.py       # Application bootstrap and configuration
```

## How It Works

1. **Upload**: User submits a receipt image via the API
2. **Process**: Image is enhanced using computer vision techniques
3. **Analyze**: Gemini Vision AI extracts text and understands receipt structure
4. **Extract**: Structured data is parsed from the AI response
5. **Categorize**: Items are intelligently categorized
6. **Store**: Data is saved to PostgreSQL with proper relationships

## Key Endpoints

- `POST /api/v1/receipts/scan/` - Upload and analyze a receipt image
- `GET /api/v1/receipts/` - List all processed receipts
- `GET /api/v1/receipts/{receipt_id}` - Get a specific receipt with items
- `GET /api/v1/categories/` - List all item categories

## Development

For detailed development setup and instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## License

See [LICENSE](LICENSE) file.
