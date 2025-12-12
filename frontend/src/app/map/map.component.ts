import { Component, OnInit, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';
import { TravelWarningService } from '../services/travel-warning.service';
import { TravelWarningSummary } from '../models/travel-warning';
import { LeafletModule } from '@bluehalo/ngx-leaflet';
import { ModalComponent } from '../modal/modal.component';
import tokens from '../../design-tokens.json';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss'],
  standalone: true,
  imports: [CommonModule, LeafletModule, ModalComponent]
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

  constructor(private travelWarningService: TravelWarningService, private elementRef: ElementRef) { }

  ngOnInit(): void {
    this.loadTravelWarnings();
    // Listen for modal opened event
    this.elementRef.nativeElement.addEventListener('modalOpened', () => {
      this.isModalOpen = true;
      // Close any open popups
      this.map?.closePopup();
    });
  }

  private loadTravelWarnings(): void {
    this.travelWarningService.getWarnings().subscribe({
      next: (warnings: TravelWarningSummary[]) => {
        this.travelWarnings = warnings;
        this.initializeMap(); // Map erst initialisieren, wenn Daten da sind
      },
      error: () => {
        // Error handling without console output
      }
    });
  }

  private initializeMap(): void {
    this.map = L.map('map', {
      zoomControl: false,
      attributionControl: false
    }).setView([51.1657, 10.4515], 4);

    // Add Tile Layer (OpenStreetMap.de)
    // The original layout requested by the user
    L.tileLayer('https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 20
    }).addTo(this.map);

    // Set Map Background (Water Color) - This will be mostly covered by the tile layer now, but kept for consistency if tiles fail.
    this.map.getContainer().style.backgroundColor = tokens.colors.brand.blue;

    // Load GeoJSON data
    fetch(this.countriesGeoJsonUrl)
      .then(response => response.json())
      .then(data => {
        this.geoJsonLayer = L.geoJSON(data, {
          style: (feature) => {
            const countryCode = feature?.properties?.['ISO3166-1-Alpha-2'];
            const warning = this.travelWarnings.find(w => w.countryCode === countryCode);

            const baseStyle = {
              color: 'transparent',
              weight: 1,
              fillOpacity: 0 // Default transparent to show map tiles
            };

            if (warning) {
              if (warning.warning) {
                return {
                  ...baseStyle,
                  fillColor: tokens.colors.brand.red,
                  fillOpacity: 0.6, // Semi-transparent to see underlying map details
                  color: tokens.colors.brand.red,
                  weight: 1
                };
              } else if (warning.partialWarning) {
                return {
                  ...baseStyle,
                  fillColor: tokens.colors.brand.yellow,
                  fillOpacity: 0.6,
                  color: tokens.colors.brand.yellow,
                  weight: 1
                };
              }
            }

            // Safe / Neutral Land -> Transparent (Show Tiles)
            return baseStyle;
          },
          onEachFeature: (feature, layer) => {
            const countryCode = feature?.properties?.['ISO3166-1-Alpha-2'];
            const warning = this.travelWarnings.find(w => w.countryCode === countryCode);
            // Name: Prefer warning name (German translation usually), fallback to GeoJSON property if exists
            const countryName = warning?.countryName || feature?.properties?.['name'] || feature?.properties?.['NAME'] || '';

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
                        <div class="min-w-[300px] font-sans text-slate-800">
                          <!-- Header -->
                          <div class="bg-brand-offwhite px-5 py-3 border-b border-ui-border flex items-center justify-between">
                             <h3 class="text-lg font-bold text-text-primary">${warning.countryName}</h3>
                             <div class="${warning.warning ? 'bg-brand-red' : warning.partialWarning ? 'bg-brand-yellow' : 'bg-brand-green'} text-white rounded-full p-1.5">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
                                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                                </svg>
                             </div>
                          </div>
                          
                          <!-- Body -->
                          <div class="p-5 bg-surface">
                            <div class="space-y-3 mb-5">
                              <div class="flex items-start justify-between">
                                <span class="text-sm text-text-secondary font-medium">Status</span>
                                <span class="font-bold ${warning.warning ? 'text-brand-red' : warning.partialWarning ? 'text-brand-yellow' : 'text-brand-green'}">${warning.warning ? 'Reisewarnung' : warning.partialWarning ? 'Teilweise Reisewarnung' : 'Keine Reisewarnung'}</span>
                              </div>
                              <div class="flex items-start justify-between">
                                <span class="text-sm text-text-secondary font-medium">Aktualisiert</span>
                                <span class="font-semibold text-text-primary">${new Date(details.response[warning.id].lastModified * 1000).toLocaleDateString('de-DE')}</span>
                              </div>
                              <div class="flex items-start justify-between">
                                <span class="text-sm text-text-secondary font-medium">Gültig seit</span>
                                <span class="font-semibold text-text-primary">${new Date(details.response[warning.id].effective * 1000).toLocaleDateString('de-DE')}</span>
                              </div>
                            </div>
                            
                            <button class="w-full bg-cta hover:bg-cta-hover text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 group toggle-modal-btn" onclick="document.querySelector('app-modal').dispatchEvent(new CustomEvent('openModal')); document.querySelector('app-map').dispatchEvent(new CustomEvent('modalOpened'));">
                              Details anzeigen
                              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4 group-hover:translate-x-1 transition-transform">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      `;

                      layer.bindPopup(popupContent, {
                        closeButton: false,
                        offset: [0, -10],
                        className: 'custom-popup'
                      }).openPopup();
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

  private updateMapStyles(): void {
    if (this.geoJsonLayer) {
      this.geoJsonLayer.setStyle((feature) => {
        const countryCode = feature?.properties?.['ISO3166-1-Alpha-2'];
        const warning = this.travelWarnings.find(w => w.countryCode === countryCode);

        if (warning) {
          if (warning.warning) {
            return {
              fillColor: tokens.colors.brand.red,
              fillOpacity: 0.6,
              color: tokens.colors.brand.red,
              weight: 1
            };
          } else if (warning.partialWarning) {
            return {
              fillColor: tokens.colors.brand.yellow,
              fillOpacity: 0.6,
              color: tokens.colors.brand.yellow,
              weight: 1
            };
          }
        }

        // Safe / Neutral -> Transparent
        return {
          fillColor: 'transparent',
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
