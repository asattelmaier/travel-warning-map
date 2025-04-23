import { Injectable } from '@angular/core';

declare const window: any;

@Injectable({
  providedIn: 'root'
})
export class EnvironmentService {
  get googleMapsApiKey(): string {
    const key = window.__env?.GOOGLE_MAPS_API_KEY || '';
    console.log('Google Maps API Key:', key ? 'Found' : 'Not found');
    return key;
  }
} 