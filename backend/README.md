# Travel Warning Map Backend

FastAPI backend for the Travel Warning Map application.

## Features

- ASGI-compliant FastAPI application
- Async HTTP client for fetching travel warnings
- Pydantic models for data validation
- CORS middleware for frontend integration
- Environment-based configuration

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
# For production
pip install .

# For development
pip install -e ".[dev]"
```

3. Create a `.env` file with the following variables:
```
PROJECT_NAME=Travel Warning Map Backend
VERSION=1.0.0
CORS_ORIGINS=["http://localhost:4200"]
```

## Development

Run the development server:
```bash
uvicorn app.main:app --reload --port 3000
```

The API will be available at `http://localhost:3000` with automatic API documentation at `/docs`.

## API Endpoints

- `GET /health`: Health check endpoint
- `GET /travel-warnings`: Get all travel warnings
- `GET /travel-warnings/{id}`: Get details for a specific travel warning

## Development Tools

The project uses several development tools that are installed with the `dev` extras:

- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Static type checking

Run the tools:
```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .
```

## Docker

Build and run the Docker container:
```bash
# Build
docker build -t travel-warning-map-backend .

# Run
docker run -p 3000:3000 travel-warning-map-backend
``` 