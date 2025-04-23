import { Component, OnInit, ElementRef } from '@angular/core';
import * as L from 'leaflet';
import { TravelWarningService } from '../services/travel-warning.service';
import { TravelWarningSummary } from '../models/travel-warning';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss']
})
export class MapComponent implements OnInit {
  private map: L.Map | null = null;
  private geoJsonLayer: L.GeoJSON | null = null;
  private travelWarnings: TravelWarningSummary[] = [];
  private countriesGeoJsonUrl = 'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson';

  // Modal state
  isModalOpen = false;
  modalTitle = '';
  modalStatus = '';
  modalLastModified = '';
  modalEffective = '';
  modalContent = '';

  constructor(private travelWarningService: TravelWarningService, private elementRef: ElementRef) {}

  ngOnInit(): void {
    this.initializeMap();
    this.loadTravelWarnings();

    // Listen for modal opened event
    this.elementRef.nativeElement.addEventListener('modalOpened', () => {
      this.isModalOpen = true;
      // Close any open popups
      this.map?.closePopup();
    });
  }

  private initializeMap(): void {
    this.map = L.map('map').setView([51.1657, 10.4515], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    // Load GeoJSON data
    fetch(this.countriesGeoJsonUrl)
      .then(response => response.json())
      .then(data => {
        this.geoJsonLayer = L.geoJSON(data, {
          style: (feature) => {
            const countryCode = feature?.properties?.['ISO3166-1-Alpha-2'];
            const warning = this.travelWarnings.find(w => w.countryCode === countryCode);
            
            if (warning) {
              if (warning.warning) {
                return {
                  fillColor: '#ff0000',
                  fillOpacity: 0.4,
                  color: 'transparent',
                  weight: 0
                };
              } else if (warning.partialWarning) {
                return {
                  fillColor: '#ffa500',
                  fillOpacity: 0.4,
                  color: 'transparent',
                  weight: 0
                };
              }
            }
            
            return {
              fillColor: '#ffffff',
              fillOpacity: 0,
              color: 'transparent',
              weight: 0
            };
          },
          onEachFeature: (feature, layer) => {
            const countryCode = feature?.properties?.['ISO3166-1-Alpha-2'];
            const warning = this.travelWarnings.find(w => w.countryCode === countryCode);
            
            if (warning) {
              layer.on('click', () => {
                this.travelWarningService.getWarningDetails(warning.id).subscribe({
                  next: (details) => {
                    // Set modal data
                    this.modalTitle = warning.countryName;
                    this.modalStatus = warning.warning ? 'Reisewarnung' : warning.partialWarning ? 'Teilweise Reisewarnung' : 'Keine Reisewarnung';
                    this.modalLastModified = new Date(details.response[warning.id].lastModified * 1000).toLocaleDateString('de-DE');
                    this.modalEffective = new Date(details.response[warning.id].effective * 1000).toLocaleDateString('de-DE');
                    this.modalContent = details.response[warning.id].content || 'Keine Beschreibung verfügbar';

                    // Only show popup if modal is not open
                    if (!this.isModalOpen) {
                      // Show popup
                      const popupContent = `
                        <div class="map-popup">
                          <h3>${warning.countryName}</h3>
                          <div class="info-container">
                            <p><strong>Status:</strong> ${warning.warning ? 'Reisewarnung' : warning.partialWarning ? 'Teilweise Reisewarnung' : 'Keine Reisewarnung'}</p>
                            <p><strong>Letzte Aktualisierung:</strong> ${new Date(details.response[warning.id].lastModified * 1000).toLocaleDateString('de-DE')}</p>
                            <p><strong>Gültig seit:</strong> ${new Date(details.response[warning.id].effective * 1000).toLocaleDateString('de-DE')}</p>
                          </div>
                          <button class="details-button" onclick="document.querySelector('app-modal').dispatchEvent(new CustomEvent('openModal')); document.querySelector('app-map').dispatchEvent(new CustomEvent('modalOpened'));">
                            Mehr Details anzeigen
                          </button>
                        </div>
                      `;
                      layer.bindPopup(popupContent).openPopup();
                    } else {
                      // If modal is open, just update its content
                      this.isModalOpen = true;
                    }
                  },
                  error: () => {
                    if (!this.isModalOpen) {
                      layer.bindPopup('Fehler beim Laden der Details').openPopup();
                    }
                  }
                });
              });
            }
          }
        }).addTo(this.map!);
      });
  }

  private loadTravelWarnings(): void {
    this.travelWarningService.getWarnings().subscribe({
      next: (warnings: TravelWarningSummary[]) => {
        this.travelWarnings = warnings;
        this.updateMapStyles();
      },
      error: () => {
        // Error handling without console output
      }
    });
  }

  private updateMapStyles(): void {
    if (this.geoJsonLayer) {
      this.geoJsonLayer.setStyle((feature) => {
        const countryCode = feature?.properties?.['ISO3166-1-Alpha-2'];
        const warning = this.travelWarnings.find(w => w.countryCode === countryCode);
        
        if (warning) {
          if (warning.warning) {
            return {
              fillColor: '#ff0000',
              fillOpacity: 0.4,
              color: 'transparent',
              weight: 0
            };
          } else if (warning.partialWarning) {
            return {
              fillColor: '#ffa500',
              fillOpacity: 0.4,
              color: 'transparent',
              weight: 0
            };
          }
        }
        
        return {
          fillColor: '#ffffff',
          fillOpacity: 0,
          color: 'transparent',
          weight: 0
        };
      });
    }
  }

  closeModal(): void {
    this.isModalOpen = false;
  }
}