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
  showModal = false;
  loadingProgress = { total: 0, loaded: 0, active: false };
  showProgressBar = true;
  statusMessage = 'Initializing...';

  private retryStartTime: number | null = null;
  private readonly MAX_RETRY_DURATION = 15000; // 15 seconds

  constructor(private travelWarningService: TravelWarningService) { }

  ngOnInit() {
    const dismissed = localStorage.getItem('experimental_modal_dismissed');
    if (!dismissed) {
      this.showModal = true;
    }

    // Start data sync immediately
    this.travelWarningService.getWarnings('en', true).subscribe();
    this.pollProgress();
  }

  pollProgress() {
    this.travelWarningService.syncProgress$.subscribe({
      next: (progress) => {
        this.loadingProgress = progress;
        this.showProgressBar = progress.active;
        this.errorMessage = null;

        if (progress.active) {
          this.statusMessage = progress.total > 0
            ? 'Loading cached data...'
            : 'Connecting...';
        }
      },
      error: () => {
        // This observable shouldn't error as it is a Subject, but just in case
        this.errorMessage = 'An error occurred while loading local data.';
        this.showProgressBar = false;
      }
    });
  }

  closeModal() {
    localStorage.setItem('experimental_modal_dismissed', 'true');
    this.showModal = false;
  }
}
