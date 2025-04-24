# Travel Warning Map

## Project Description
This app serves as a proof of concept for my own investigation into inference models for coding. I aim to let the model write the application with minimal intervention, providing only the technical requirements. The goal is to achieve implementation as autonomously as possible by the inference model.

## Getting Started

Clone the repository:

```bash
git clone https://github.com/asattelmaier/travel-warning-map.git
cd travel-warning-map
```

2. Install the dependencies:
   ```bash
   npm install
   ```

3. Set the environment variable for the API URL:
   ```bash
   export TRAVEL_WARNINGS_API_URL='https://your-proxy-server.com/api'
   ```

## Environment Variables
- `TRAVEL_WARNINGS_API_URL`: The URL of the backend server from which travel warnings are fetched.

## Commands
- **Start the application**:
  ```bash
  npm start
  ```

- **Build the application**:
  ```bash
  npm run build
  ```

- **Watch the application**:
  ```bash
  npm run watch
  ```

## Deployment
The application is automatically deployed to GitHub Pages when changes are pushed to the `main` branch. Deployment is handled via GitHub Actions.

## Technologies
- Angular
- Leaflet
- TypeScript
- GitHub Actions