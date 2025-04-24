import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-info-modal',
  templateUrl: './info-modal.component.html',
  styleUrls: ['./info-modal.component.scss'],
  standalone: true,
  imports: [CommonModule]
})
export class InfoModalComponent {
  @Output() close = new EventEmitter<void>();

  closeModal() {
    this.close.emit(); // Emit an event to close the modal
  }
}
