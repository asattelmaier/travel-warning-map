import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  errorMessage: string | null = null;
  showModal = true; // Set to true to show the modal initially

  closeModal() {
    this.showModal = false; // Hide the modal
  }
}
