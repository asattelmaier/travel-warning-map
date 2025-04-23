import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  isGoogleMapsReady = true; // Always true now since we're using Leaflet
  errorMessage: string | null = null;
}
