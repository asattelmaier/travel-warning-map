import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MapComponent } from './map/map.component';
import { InfoModalComponent } from './info-modal/info-modal.component';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  standalone: true,
  imports: [CommonModule, MapComponent, InfoModalComponent]
})
export class AppComponent {
  errorMessage: string | null = null;
  showModal = true; // Set to true to show the modal initially

  closeModal() {
    this.showModal = false; // Hide the modal
  }
}
