import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FedeStatusService } from '../../../services/fede-status.service';
import { MetricCardData } from '../../../shared/components/metrics-chart-module';
import { DonutMetricsChartComponent, DonutLegendItem } from '../../../shared/components/donut-metrics-chart';

@Component({
  selector: 'app-hir-metrics',
  standalone: true,
  imports: [DonutMetricsChartComponent],
  template: `
    <app-donut-metrics-chart
      [isLoading]="isLoading"
      [hasData]="hasData"
      [chartData]="chartData"
      [chartOptions]="chartOptions"
      [total]="totalAssessments"
      totalLabel="Total"
      [legendItems]="legendItems"
      [metricsData]="metricsData"
      [emptyMessage]="emptyMessage"
      [chartSize]="260">
    </app-donut-metrics-chart>
  `,
  styleUrl: './hir-metrics.scss'
})
/** Display live HIR completion metrics for the current filters. */
export class HirMetricsComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedProgram: string | null = null;
  @Input() selectedDvpTeam: string | null = null;
  @Input() selectedPmt: string | null = null;

  hasData = false;
  chartData: any;
  chartOptions: any;
  isLoading = false;
  emptyMessage = 'No data available';
  metricsData: MetricCardData[] = [];
  legendItems: DonutLegendItem[] = [];

  withEvidence = 0;
  withoutEvidence = 0;
  totalAssessments = 0;
  completionPercentage = 0;

  private readonly COLORS = ['#00B050', '#FF5252'];
  private readonly LABELS = ['With Evidence', 'Without Evidence'];

  constructor(private fedeStatusService: FedeStatusService) {
    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '72%',
      plugins: { legend: { display: false }, tooltip: { enabled: true } }
    };
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this.giCode) return;
    if (changes['giCode'] || changes['selectedProgram'] || changes['selectedDvpTeam'] || changes['selectedPmt']) {
      this.loadData();
    }
  }

  loadData() {
    if (!this.giCode) return;
    this.isLoading = true;
    this.hasData = false;

    // Set specific empty message based on selection
    if (this.selectedProgram && this.selectedDvpTeam) {
      this.emptyMessage = `No HIR data available for: ${this.selectedProgram} - ${this.selectedDvpTeam}`;
    } else if (this.selectedProgram) {
      this.emptyMessage = `No HIR data available for: ${this.selectedProgram}`;
    } else if (this.selectedDvpTeam) {
      this.emptyMessage = `No HIR data available for DVP Team: ${this.selectedDvpTeam}`;
    } else {
      this.emptyMessage = 'No HIR data available';
    }

    this.fedeStatusService.getHirCompletion(
      this.giCode,
      this.selectedProgram || null,
      this.selectedPmt,
      null,
      this.selectedDvpTeam || null
    ).subscribe({
      next: (response) => {
        if (!response.data || response.data.length === 0 || response.total_records === 0) {
          this.resetChart();
          this.isLoading = false;
          return;
        }

        // Aggregate data from all records
        const aggregated = response.data.reduce(
          (acc, item) => ({
            with_evidence: acc.with_evidence + item.with_evidence,
            without_evidence: acc.without_evidence + item.without_evidence,
            total_items: acc.total_items + item.total_items
          }),
          { with_evidence: 0, without_evidence: 0, total_items: 0 }
        );

        this.withEvidence = aggregated.with_evidence;
        this.withoutEvidence = aggregated.without_evidence;
        this.totalAssessments = aggregated.total_items;
        this.completionPercentage = this.totalAssessments > 0
          ? (this.withEvidence / this.totalAssessments) * 100
          : 0;

        this.buildData();
        this.hasData = true;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error loading HIR completion data:', err);
        this.resetChart();
        this.emptyMessage = 'Error loading HIR data. Please try again.';
        this.isLoading = false;
      }
    });
  }

  resetChart() {
    this.hasData = false;
    this.withEvidence = 0;
    this.withoutEvidence = 0;
    this.totalAssessments = 0;
    this.completionPercentage = 0;
    this.metricsData = [];
    this.legendItems = [];
    this.chartData = null;
  }

  buildData() {
    const values = [this.withEvidence, this.withoutEvidence];
    const pct = (value: number) => this.totalAssessments > 0
      ? ((value / this.totalAssessments) * 100).toFixed(1)
      : '0.0';

    this.metricsData = [
      {
        label: 'Total Items',
        value: this.totalAssessments,
        color: 'total'
      },
      {
        label: 'With Evidence',
        value: this.withEvidence,
        percent: parseFloat(pct(this.withEvidence)),
        color: 'meet'
      },
      {
        label: 'Without Evidence',
        value: this.withoutEvidence,
        percent: parseFloat(pct(this.withoutEvidence)),
        color: 'does-not-meet'
      },
      {
        label: 'Completion %',
        value: Math.round(this.completionPercentage),
        color: 'completion'
      }
    ];

    this.legendItems = this.LABELS.map((label, i) => ({
      label,
      value: values[i],
      pct: pct(values[i]),
      color: this.COLORS[i]
    })).filter(item => item.value > 0);

    this.chartData = {
      labels: this.LABELS,
      datasets: [{
        data: values,
        backgroundColor: this.COLORS,
        borderColor: '#FFFFFF',
        borderWidth: 2,
      }]
    };
  }
}
