import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MapComponent } from './map/map.component';
import { InfoModalComponent } from './info-modal/info-modal.component';
import { TravelWarningService } from './services/travel-warning.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  standalone: true,
  imports: [CommonModule, MapComponent, InfoModalComponent]
})
export class AppComponent implements OnInit {
  errorMessage: string | null = null;
  showModal = true;
  loadingProgress = { total: 0, loaded: 0, active: false };
  showProgressBar = true;
  statusMessage = 'Initializing...';

  private retryStartTime: number | null = null;
  private readonly MAX_RETRY_DURATION = 15000; // 15 seconds

  constructor(private travelWarningService: TravelWarningService) { }

  ngOnInit() {
    this.pollProgress();
  }

  pollProgress() {
    this.travelWarningService.getCacheProgress().subscribe({
      next: (progress) => {
        // Success - connection established
        this.retryStartTime = null; // Reset retry timer
        this.loadingProgress = progress;
        this.showProgressBar = progress.active;
        this.errorMessage = null;

        if (progress.active) {
          this.statusMessage = `Loading data... ${progress.loaded} / ${progress.total}`;
          setTimeout(() => this.pollProgress(), 1000);
        }
      },
      error: () => {
        // Connection failed
        if (this.retryStartTime === null) {
          this.retryStartTime = Date.now();
        }

        const elapsed = Date.now() - this.retryStartTime;
        if (elapsed > this.MAX_RETRY_DURATION) {
          this.errorMessage = 'An error occurred while loading the application. Please reload the page.';
          this.showProgressBar = false;
        } else {
          this.showProgressBar = true;
          this.statusMessage = 'Collecting data...';
          // Retry after 1 second
          setTimeout(() => this.pollProgress(), 1000);
        }
      }
    });
  }

  closeModal() {
    this.showModal = false;
  }
}
