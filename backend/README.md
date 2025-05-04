# Travel Warning Map Backend

FastAPI backend for the Travel Warning Map application.

## Features

- ASGI-compliant FastAPI application
- Google Drive integration for travel warnings
- Pydantic models for data validation (see `app/travel_warning/`)
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

3. Set up Google Cloud authentication for local development:
```bash
# Login with your Google account
gcloud auth application-default login
```

4. Create a `.env` file with the following variables:
```
PROJECT_NAME=Travel Warning Map Backend
VERSION=1.0.0
CORS_ORIGINS=["http://localhost:4200"]
DRIVE_FOLDER_ID=your_drive_folder_id_here
```

## Local Development

1. **Google Drive Access**
   - Ensure you have access to the Google Drive folder
   - The folder ID can be found in the URL when opening the folder in Google Drive
   - Example: `https://drive.google.com/drive/folders/1234567890` → `1234567890`
   - The folder should contain a date-based structure with travel warning files

2. **Testing Drive Access**
   ```bash
   # Start the development server
   uvicorn app.main:app --reload --port 3000
   
   # Test the health endpoint
   curl http://localhost:3000/health
   
   # Test travel warnings endpoint
   curl http://localhost:3000/travel-warnings
   
   # Test specific travel warning
   curl http://localhost:3000/travel-warnings/220416
   ```

3. **Troubleshooting**
   - If you get permission errors, ensure:
     - You're logged in with `gcloud auth application-default login`
     - You have access to the Google Drive folder
     - The `DRIVE_FOLDER_ID` is correct
   - Check the logs for detailed error messages
   - Verify that the Google Drive folder structure is correct:
     - Root folder → Date folder (YYYY-MM-DD) → travelwarning.json and travelwarning folder

## API Endpoints

- `GET /health`: Health check endpoint
- `GET /travel-warnings`: Get all travel warnings
  - Returns a response object containing all travel warnings
  - Optional query parameter: `language` (default: "en")
- `GET /travel-warnings/{id}`: Get details for a specific travel warning
  - Returns a response object containing the specific travel warning
  - Optional query parameter: `language` (default: "en")

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