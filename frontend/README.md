# Travel Warning Map Frontend

Angular frontend for the Travel Warning Map application, visualizing global travel warnings using OpenStreetMap and official government data.



## Prerequisites

- Node.js (v18 or higher recommended)
- NPM

## Setup

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

## Development Server

Start the development server with proxying to the local backend:

```bash
npm start
```

- Access the application at: `http://localhost:4200`
- The application proxies API requests (`/travel-warnings/*`) to `http://localhost:3000`. Ensure the backend is running.

## Build

Build the project for production:

```bash
npm run build
```

The build artifacts will be stored in the `dist/` directory.
