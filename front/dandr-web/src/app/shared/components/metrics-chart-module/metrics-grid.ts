import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

/** Display data and semantic color for one metric card. */
export interface MetricCardData {
  label: string;
  value: string | number;
  percent?: string | number;
  color?: 'meet' | 'unassessed' | 'approved-deviation' | 'does-not-meet' | 'cannot-assess' | 'not-applicable' | string;
}

@Component({
  selector: 'app-metrics-grid',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="metrics-grid">
      <div
        class="metric-item"
        *ngFor="let metric of metrics"
        [ngClass]="metric.color ? metric.color : ''"
      >
        <span class="metric-label">{{ metric.label }}</span>
        <span class="metric-value">{{ metric.value }}</span>
        <span class="metric-percent" *ngIf="metric.percent">({{ metric.percent }}%)</span>
      </div>
    </div>
  `,
  styleUrls: ['./metrics-grid.scss'],
  host: { '[attr.metrics]': '"true"' }
})
/** Responsive grid that renders normalized metric-card data. */
export class MetricsGridComponent {
  @Input() metrics: MetricCardData[] = [];
}
