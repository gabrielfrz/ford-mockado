import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { VehicleLineService } from '../../../services/vehicle-line.service';
import { MetricCardData } from '../../../shared/components/metrics-chart-module';
import { DonutMetricsChartComponent, DonutLegendItem } from '../../../shared/components/donut-metrics-chart';

interface CaeData {
  program: string;
  total_assessments: number;
  meet: number;
  unassessed: number;
  approved_deviation: number;
  does_not_meet: number;
  co: number;
  carryover?: number;
}

@Component({
  selector: 'app-cae-metrics',
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
  styleUrl: './cae-metrics.scss'
})
/** Present the CAE metric summary for the current vehicle filters. */
export class CaeMetricsComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedProgram: string | null = null;
  @Input() selectedPmt: string | null = null;

  hasData = false;
  chartData: any;
  chartOptions: any;
  isLoading = false;
  emptyMessage = 'No data available';
  metricsData: MetricCardData[] = [];
  legendItems: DonutLegendItem[] = [];

  metrics = {
    meet: 0, unassessed: 0, approved_deviation: 0,
    does_not_meet: 0, carryover: 0,
  };
  totalAssessments = 0;

  private readonly COLORS = ['#00B050', '#FFC000', '#FF9900', '#FF0000', '#808080'];
  private readonly LABELS = ['Meet', 'Unassessed', 'Approved Deviation', 'Does Not Meet', 'CO'];

  constructor(private vehicleLineService: VehicleLineService) {
    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '72%',
      plugins: { legend: { display: false }, tooltip: { enabled: true } }
    };
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this.giCode) return;
    if (changes['giCode'] || changes['selectedProgram'] || changes['selectedPmt']) {
      this.loadData();
    }
  }

  loadData() {
    if (!this.giCode) return;
    this.isLoading = true;
    this.hasData = false;
    this.emptyMessage = this.selectedProgram
      ? `No data available for ${this.selectedProgram}`
      : 'No data available';

    this.vehicleLineService
      .getCaeTotalAssessments(this.giCode, this.selectedProgram || undefined, this.selectedPmt)
      .subscribe({
        next: (response: any) => {
          const rawData: CaeData[] = response.data || [];
          if (rawData.length > 0) {
            const agg = rawData.reduce(
              (acc, item) => ({
                meet: acc.meet + item.meet,
                unassessed: acc.unassessed + item.unassessed,
                approved_deviation: acc.approved_deviation + item.approved_deviation,
                does_not_meet: acc.does_not_meet + item.does_not_meet,
                carryover: acc.carryover + (item.carryover || 0),
                total_assessments: acc.total_assessments + item.total_assessments,
              }),
              { meet: 0, unassessed: 0, approved_deviation: 0, does_not_meet: 0, carryover: 0, total_assessments: 0 }
            );
            this.metrics = {
              meet: agg.meet, unassessed: agg.unassessed,
              approved_deviation: agg.approved_deviation, does_not_meet: agg.does_not_meet,
              carryover: agg.carryover,
            };
            this.totalAssessments = agg.total_assessments;
            this.buildData();
            this.hasData = true;
          }
          this.isLoading = false;
        },
        error: () => { this.isLoading = false; }
      });
  }

  buildData() {
    const values = [
      this.metrics.meet, this.metrics.unassessed, this.metrics.approved_deviation,
      this.metrics.does_not_meet, this.metrics.carryover,
    ];
    this.metricsData = [
      { label: 'Total Assessments', value: this.totalAssessments },
      ...this.LABELS.map((label, i) => ({
        label,
        value: values[i],
        percent: this.totalAssessments ? Math.round((values[i] / this.totalAssessments) * 100) : 0,
        color: ['meet', 'unassessed', 'approved-deviation', 'does-not-meet', 'cannot-assess'][i]
      }))
    ];
    this.legendItems = this.LABELS.map((label, i) => ({
      label,
      value: values[i],
      pct: this.totalAssessments ? ((values[i] / this.totalAssessments) * 100).toFixed(1) : '0',
      color: this.COLORS[i]
    }));
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
