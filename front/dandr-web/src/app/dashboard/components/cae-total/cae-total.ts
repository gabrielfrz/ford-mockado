import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { VehicleLineService } from '../../../services/vehicle-line.service';
import { MetricsChartContainerComponent, MetricsGridComponent, MetricCardData } from '../../../shared/components/metrics-chart-module';

interface CaeTotalData {
  program: string;
  total_assessments: number;
  meet: number;
  unassessed: number;
  approved_deviation: number;
  does_not_meet: number;
  cannot_assess: number;
  not_applicable: number;
}

interface CaeTotalResponse {
  gi_code: string;
  data: CaeTotalData[];
  total_records: number;
}

@Component({
  selector: 'app-cae-total',
  standalone: true,
  imports: [CommonModule, ChartModule, MetricsGridComponent],
  template: `
    <!-- Loading Spinner -->
    <div *ngIf="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p class="loading-text">Loading data...</p>
    </div>

    <!-- Content using Metrics Chart Module -->
    <div *ngIf="!isLoading && caeTotalData" class="cae-total-wrapper">
      <!-- Title -->
      <h3 class="section-title">CAE ASSESSMENT TOTAL</h3>

      <!-- Metrics Grid + Chart in Container -->
      <div class="metrics-content">
        <!-- Left: Cards Section -->
        <div class="metrics-section">
          <app-metrics-grid [metrics]="metricsData"></app-metrics-grid>
        </div>

        <!-- Right: Chart Section -->
        <p-chart
          type="doughnut"
          [data]="chartData"
          [options]="chartOptions"
          class="chart-section">
        </p-chart>
      </div>
    </div>

    <!-- Empty State -->
    <div *ngIf="!isLoading && !caeTotalData" class="empty-state">
      <p>No CAE data available</p>
    </div>
  `,
  styleUrl: './cae-total.scss'
})
/** Aggregate and visualize total CAE assessment states. */
export class CaeTotalComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedProgram: string | null = null;

  caeTotalData: any;
  chartData: any;
  chartOptions: any;
  isLoading = false;
  rawData: CaeTotalData[] = [];
  metricsData: MetricCardData[] = [];

  metrics = {
    meet: 0,
    unassessed: 0,
    approved_deviation: 0,
    does_not_meet: 0,
    cannot_assess: 0,
    not_applicable: 0,
  };
  totalAssessments = 0;

  constructor(private vehicleLineService: VehicleLineService) {
    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      layout: {
        padding: {
          bottom: 20
        }
      },
      plugins: {
        legend: {
          position: 'bottom',
          align: 'center',
          labels: {
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 12,
            font: { size: 13, weight: 500 },
            color: '#333333'
          }
        }
      }
    };
  }

  ngOnChanges(changes: SimpleChanges) {
    if ((changes['giCode'] && this.giCode) || (changes['selectedProgram'] && this.selectedProgram)) {
      this.loadCaeTotalData();
    }
  }

  loadCaeTotalData() {
    if (!this.giCode) return;

    this.isLoading = true;

    this.vehicleLineService.getCaeTotalAssessments(this.giCode, this.selectedProgram || undefined).subscribe({
      next: (response: CaeTotalResponse) => {
        this.rawData = response.data || [];

        if (this.rawData.length > 0) {
          // Aggregate all returned program records.
          const aggregated = this.rawData.reduce((acc, item) => ({
            meet: acc.meet + item.meet,
            unassessed: acc.unassessed + item.unassessed,
            approved_deviation: acc.approved_deviation + item.approved_deviation,
            does_not_meet: acc.does_not_meet + item.does_not_meet,
            cannot_assess: acc.cannot_assess + item.cannot_assess,
            not_applicable: acc.not_applicable + item.not_applicable,
            total: acc.total + item.total_assessments,
          }), {
            meet: 0,
            unassessed: 0,
            approved_deviation: 0,
            does_not_meet: 0,
            cannot_assess: 0,
            not_applicable: 0,
            total: 0,
          });

          this.metrics = {
            meet: aggregated.meet,
            unassessed: aggregated.unassessed,
            approved_deviation: aggregated.approved_deviation,
            does_not_meet: aggregated.does_not_meet,
            cannot_assess: aggregated.cannot_assess,
            not_applicable: aggregated.not_applicable,
          };
          this.totalAssessments = aggregated.total;

          this.buildMetricsData();
          this.updateChart();
          this.caeTotalData = true;
        } else {
          this.caeTotalData = null;
        }

        this.isLoading = false;
      },
      error: (err: any) => {
        console.error('Failed to load CAE totals:', err);
        this.isLoading = false;
      }
    });
  }

  buildMetricsData() {
    this.metricsData = [
      {
        label: 'Total Assessments',
        value: this.totalAssessments
      },
      {
        label: 'Meet',
        value: this.metrics.meet,
        percent: this.getPercent(this.metrics.meet),
        color: 'meet'
      },
      {
        label: 'Unassessed',
        value: this.metrics.unassessed,
        percent: this.getPercent(this.metrics.unassessed),
        color: 'unassessed'
      },
      {
        label: 'Approved Deviation',
        value: this.metrics.approved_deviation,
        percent: this.getPercent(this.metrics.approved_deviation),
        color: 'approved-deviation'
      },
      {
        label: 'Does Not Meet',
        value: this.metrics.does_not_meet,
        percent: this.getPercent(this.metrics.does_not_meet),
        color: 'does-not-meet'
      },
      {
        label: 'Cannot Assess',
        value: this.metrics.cannot_assess,
        percent: this.getPercent(this.metrics.cannot_assess),
        color: 'cannot-assess'
      },
      {
        label: 'Not Applicable',
        value: this.metrics.not_applicable,
        percent: this.getPercent(this.metrics.not_applicable),
        color: 'not-applicable'
      }
    ];
  }

  updateChart() {
    this.chartData = {
      labels: ['Meet', 'Unassessed', 'Approved Deviation', 'Does Not Meet', 'Cannot Assess', 'Not Applicable'],
      datasets: [
        {
          data: [
            this.metrics.meet,
            this.metrics.unassessed,
            this.metrics.approved_deviation,
            this.metrics.does_not_meet,
            this.metrics.cannot_assess,
            this.metrics.not_applicable,
          ],
          backgroundColor: [
            '#00B050', // Green - Meet
            '#FFC000', // Yellow - Unassessed
            '#FF9900', // Orange - Approved Deviation
            '#FF0000', // Red - Does Not Meet
            '#808080', // Gray - Cannot Assess
            '#CCCCCC', // Light Gray - Not Applicable
          ],
          borderColor: '#FFFFFF',
          borderWidth: 2,
        }
      ]
    };
  }

  getPercent(value: number): number {
    if (this.totalAssessments === 0) return 0;
    return Math.round((value / this.totalAssessments) * 100);
  }
}
