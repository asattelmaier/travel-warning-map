import { Component, Input, Output, EventEmitter, ElementRef, AfterViewInit } from '@angular/core';


@Component({
  selector: 'app-modal',
  templateUrl: './modal.component.html',
  styleUrls: ['./modal.component.scss'],
  standalone: true,
  imports: []
})
export class ModalComponent implements AfterViewInit {
  @Input() isOpen = false;
  @Input() title = '';
  @Input() status = '';
  @Input() lastModified = '';
  @Input() effective = '';
  @Input() content = '';
  @Output() closeModal = new EventEmitter<void>();

  constructor(private elementRef: ElementRef) {}

  ngAfterViewInit() {
    this.elementRef.nativeElement.addEventListener('openModal', () => {
      this.isOpen = true;
    });
  }

  close() {
    this.isOpen = false;
    this.closeModal.emit();
  }
} 