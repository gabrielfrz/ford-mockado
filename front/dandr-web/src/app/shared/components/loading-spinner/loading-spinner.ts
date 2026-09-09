import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="loading-state">
      <div class="spinner"></div>
      <p class="loading-text">Loading data...</p>
      <p *ngIf="showSlowMessage" class="slow-load-message">
        This is taking longer than usual... The dataset may be large. Please wait a moment.
      </p>
    </div>
  `,
  styleUrls: ['./loading-spinner.scss']
})
/** Reusable animated loading indicator with configurable messages. */
export class LoadingSpinnerComponent implements OnInit, OnDestroy {
  showSlowMessage = false;
  private timer: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.timer = setTimeout(() => { this.showSlowMessage = true; }, 10000);
  }

  ngOnDestroy(): void {
    if (this.timer) clearTimeout(this.timer);
  }
}
