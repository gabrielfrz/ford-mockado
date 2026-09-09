import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { VehicleLineService } from '../../../services/vehicle-line.service';
import { MetricsGridComponent, MetricCardData } from '../../../shared/components/metrics-chart-module';

interface CaeCommodityData {
  program: string;
  total_assessments: number;
  meet: number;
  unassessed: number;
  approved_deviation: number;
  does_not_meet: number;
  cannot_assess: number;
  not_applicable: number;
}

@Component({
  selector: 'app-cae-commodity',
  standalone: true,
  imports: [CommonModule, ChartModule, MetricsGridComponent],
  template: `
    <!-- Loading Spinner -->
    <div *ngIf="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p class="loading-text">Loading data...</p>
    </div>

    <!-- Empty State - No commodity selected -->
    <div *ngIf="!isLoading && !selectedProgram" class="empty-state">
      <p>Select a commodity to view assessments</p>
    </div>

    <!-- Content -->
    <div *ngIf="!isLoading && selectedProgram && commodityData" class="cae-commodity-wrapper">
      <!-- Title -->
      <h3 class="section-title">CAE ASSESSMENT BY {{ selectedProgram | uppercase }}</h3>

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

    <!-- Empty State - No data available -->
    <div *ngIf="!isLoading && selectedProgram && !commodityData" class="empty-state">
      <p>No data available for {{ selectedProgram }}</p>
    </div>
  `,
  styleUrl: './cae-commodity.scss'
})
/** Display CAE conformance metrics grouped by commodity. */
export class CaeCommodityComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedProgram: string | null = null;

  commodityData: any;
  chartData: any;
  chartOptions: any;
  isLoading = false;
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
    if (changes['selectedProgram']) {
      this.loadCaeCommodityData();
    }
  }

  loadCaeCommodityData() {
    if (!this.giCode || !this.selectedProgram) return;

    this.isLoading = true;
    this.vehicleLineService.getCaeTotalAssessments(this.giCode).subscribe({
      next: (response: any) => {
        const commodityData = response.data.find(
          (item: CaeCommodityData) => item.program === this.selectedProgram
        );

        if (commodityData) {
          this.commodityData = commodityData;
          this.metrics = {
            meet: commodityData.meet || 0,
            unassessed: commodityData.unassessed || 0,
            approved_deviation: commodityData.approved_deviation || 0,
            does_not_meet: commodityData.does_not_meet || 0,
            cannot_assess: commodityData.cannot_assess || 0,
            not_applicable: commodityData.not_applicable || 0,
          };
          this.totalAssessments = commodityData.total_assessments || 0;
          this.buildMetricsData();
          this.updateChart();
        } else {
          this.commodityData = null;
        }

        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error loading CAE commodity data:', err);
        this.isLoading = false;
        this.commodityData = null;
      }
    });
  }

  buildMetricsData() {
    this.metricsData = [
      {
        label: 'Meet',
        value: this.metrics.meet,
        percent: this.calculatePercent(this.metrics.meet),
        color: 'meet'
      },
      {
        label: 'Unassessed',
        value: this.metrics.unassessed,
        percent: this.calculatePercent(this.metrics.unassessed),
        color: 'unassessed'
      },
      {
        label: 'Approved Deviation',
        value: this.metrics.approved_deviation,
        percent: this.calculatePercent(this.metrics.approved_deviation),
        color: 'approved-deviation'
      },
      {
        label: 'Does Not Meet',
        value: this.metrics.does_not_meet,
        percent: this.calculatePercent(this.metrics.does_not_meet),
        color: 'does-not-meet'
      },
      {
        label: 'Cannot Assess',
        value: this.metrics.cannot_assess,
        percent: this.calculatePercent(this.metrics.cannot_assess),
        color: 'cannot-assess'
      },
      {
        label: 'Not Applicable',
        value: this.metrics.not_applicable,
        percent: this.calculatePercent(this.metrics.not_applicable),
        color: 'not-applicable'
      }
    ];
  }

  calculatePercent(value: number): string {
    if (this.totalAssessments === 0) return '0';
    const percent = (value / this.totalAssessments) * 100;
    return percent.toFixed(1);
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
            this.metrics.not_applicable
          ],
          backgroundColor: ['#00B050', '#FFC000', '#FF9900', '#FF0000', '#808080', '#CCCCCC'],
          borderColor: ['#00B050', '#FFC000', '#FF9900', '#FF0000', '#808080', '#CCCCCC'],
          borderWidth: 2
        }
      ]
    };
  }

  clearData() {
    this.commodityData = null;
    this.metricsData = [];
    this.chartData = null;
    this.metrics = {
      meet: 0,
      unassessed: 0,
      approved_deviation: 0,
      does_not_meet: 0,
      cannot_assess: 0,
      not_applicable: 0,
    };
    this.totalAssessments = 0;
  }
}
