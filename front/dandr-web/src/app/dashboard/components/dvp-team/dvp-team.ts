import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { FedeStatusService } from '../../../services/fede-status.service';
import { MetricsGridComponent, MetricCardData } from '../../../shared/components/metrics-chart-module';

@Component({
  selector: 'app-dvp-team',
  standalone: true,
  imports: [CommonModule, ChartModule, MetricsGridComponent],
  template: `
    <!-- Loading Spinner -->
    <div *ngIf="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p class="loading-text">Loading data...</p>
    </div>

    <!-- Empty State - No team selected -->
    <div *ngIf="!isLoading && !selectedDvpTeam" class="empty-state">
      <p>Select a DVP Team to view assessments</p>
    </div>

    <!-- Content -->
    <div *ngIf="!isLoading && selectedDvpTeam && dvpTeamData" class="dvp-team-wrapper">
      <!-- Title -->
      <h3 class="section-title">DVP ASSESSMENT BY {{ selectedDvpTeam | uppercase }}</h3>

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
    <div *ngIf="!isLoading && selectedDvpTeam && !dvpTeamData" class="empty-state">
      <p>No data available for {{ selectedDvpTeam }}</p>
    </div>
  `,
  styleUrl: './dvp-team.scss'
})
/** Display assessment-state metrics for the selected DVP team. */
export class DvpTeamComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedDvpTeam: string | null = null;

  dvpTeamData: any;
  chartData: any;
  chartOptions: any;
  isLoading = false;
  metricsData: MetricCardData[] = [];

  metrics = {
    meet: 0,
    unassessed: 0,
    does_not_meet: 0,
    cannot_assess: 0,
    not_applicable: 0,
    approved_deviation: 0
  };
  totalAssessments = 0;

  constructor(private fedeStatusService: FedeStatusService) {
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
    if ((changes['giCode'] || changes['selectedDvpTeam']) && this.giCode && this.selectedDvpTeam) {
      this.loadDvpTeamData();
    } else if (!this.selectedDvpTeam) {
      this.clearData();
    }
  }

  loadDvpTeamData() {
    if (!this.giCode || !this.selectedDvpTeam) return;

    this.isLoading = true;

    // Load all DVP team metrics for the current GI code, then filter selected team
    this.fedeStatusService.getDvpTeamListMetrics(this.giCode).subscribe({
      next: (response: any) => {
        const teams = response?.dvp_teams_metrics || [];
        const selectedTeamData = teams.find(
          (item: any) => (item?.dvp_team || '').toLowerCase() === this.selectedDvpTeam!.toLowerCase()
        );

        if (!selectedTeamData) {
          this.dvpTeamData = null;
          this.clearData();
          this.isLoading = false;
          return;
        }

        this.dvpTeamData = selectedTeamData;
        this.processDvpTeamData(selectedTeamData);
        this.buildMetricsData();
        this.updateChart();
        this.isLoading = false;
      },
      error: (err: any) => {
        console.error('Error loading DVP team metrics list:', err);
        this.dvpTeamData = null;
        this.clearData();
        this.isLoading = false;
      }
    });
  }

  processDvpTeamData(data: any) {
    const summary: Record<string, number> = data?.conf_state_summary || {};

    this.metrics = {
      meet: summary['Meet'] || summary['meet'] || 0,
      unassessed: summary['Unassessed'] || summary['unassessed'] || 0,
      does_not_meet: summary['Does Not Meet'] || summary['does_not_meet'] || 0,
      cannot_assess: summary['Cannot Assess'] || summary['cannot_assess'] || 0,
      not_applicable: summary['Not Applicable'] || summary['not_applicable'] || 0,
      approved_deviation: summary['Approved Deviation'] || summary['approved_deviation'] || 0
    };
    this.totalAssessments = Object.values(this.metrics).reduce((a, b) => a + b, 0);
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
    this.dvpTeamData = null;
    this.metricsData = [];
    this.chartData = null;
    this.metrics = {
      meet: 0,
      unassessed: 0,
      does_not_meet: 0,
      cannot_assess: 0,
      not_applicable: 0,
      approved_deviation: 0
    };
    this.totalAssessments = 0;
  }
}
