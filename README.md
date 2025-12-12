# Travel Warning Map

## Project Description
This app serves as a proof of concept for my own investigation into inference models for coding. I aim to let the model write the application with minimal intervention, providing only the technical requirements. The goal is to achieve implementation as autonomously as possible by the inference model.

## Project Structure

This repository contains two main components:

- **[Backend](backend/README.md)**: FastAPI application handling data fetching and serving.
- **[Frontend](frontend/README.md)**: Angular application displaying the map and warnings.

## Getting Started

Clone the repository:

```bash
git clone https://github.com/asattelmaier/travel-warning-map.git
cd travel-warning-map
```

### 1. Start the Backend
Follow the instructions in the [Backend README](backend/README.md) to set up and start the API server.
It must be running on port 3000.

### 2. Start the Frontend
Follow the instructions in the [Frontend README](frontend/README.md) to set up and start the web application.
It will run on port 4200 and proxy requests to the backend.

## Environment Variables
Environment configuration is handled separately for backend and frontend. See the respective READMEs for details.



## Deployment
The application is automatically deployed to GitHub Pages when changes are pushed to the `main` branch. Deployment is handled via GitHub Actions.

## Technologies
- Angular
- Leaflet
- TypeScript
- GitHub Actions