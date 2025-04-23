/**
 * Declare runtime environment variables exposed on the window object
 */
declare interface Window {
  __env: {
    /** Google Maps API key */
    GOOGLE_MAPS_API_KEY: string;
    [key: string]: any;
  };
}