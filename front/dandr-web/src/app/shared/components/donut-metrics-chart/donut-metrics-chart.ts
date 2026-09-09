import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { MetricsGridComponent, MetricCardData } from '../metrics-chart-module';

/** Custom legend entry rendered beside a donut chart. */
export interface DonutLegendItem {
  label: string;
  value: number;
  pct: string;
  color: string;
}

@Component({
  selector: 'app-donut-metrics-chart',
  standalone: true,
  imports: [CommonModule, ChartModule, MetricsGridComponent],
  template: `
    <!-- Loading -->
    <div *ngIf="isLoading" class="dmc-loading">
      <div class="spinner"></div>
    </div>

    <!-- Content -->
    <div *ngIf="!isLoading && hasData" class="dmc-wrapper">
      <div class="dmc-layout">

        <!-- Left: metric cards grid -->
        <div class="dmc-cards">
          <app-metrics-grid [metrics]="metricsData"></app-metrics-grid>
        </div>

        <!-- Right: donut + dot legend -->
        <div class="dmc-chart-area">
          <div class="dmc-chart" [style.width.px]="chartSize" [style.height.px]="chartSize">
            <p-chart type="doughnut" [data]="chartData" [options]="chartOptions"></p-chart>
            <div class="dmc-total-center">
              <span class="total-number">{{ total }}</span>
              <span class="total-label">{{ totalLabel }}</span>
            </div>
          </div>

          <div class="dmc-dot-legend">
            <div class="dot-legend-item" *ngFor="let item of legendItems">
              <span class="dot" [style.background]="item.color"></span>
              <span class="dot-label">{{ item.label }}</span>
              <span class="dot-pct">{{ item.pct }}%</span>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Empty -->
    <div *ngIf="!isLoading && !hasData" class="dmc-empty">
      <p>{{ emptyMessage || 'No data available' }}</p>
    </div>
  `,
  styleUrl: './donut-metrics-chart.scss'
})
/** Reusable donut chart with metric cards and an optional legend. */
export class DonutMetricsChartComponent {
  @Input() isLoading = false;
  @Input() hasData = false;
  @Input() chartData: any;
  @Input() chartOptions: any;
  @Input() total: number = 0;
  @Input() totalLabel: string = 'Total';
  @Input() legendItems: DonutLegendItem[] = [];
  @Input() metricsData: MetricCardData[] = [];
  @Input() emptyMessage: string = 'No data available';
  @Input() chartSize: number = 260;
}
