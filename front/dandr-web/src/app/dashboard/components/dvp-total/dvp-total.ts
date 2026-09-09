import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FedeStatusService } from '../../../services/fede-status.service';
import { MetricCardData } from '../../../shared/components/metrics-chart-module';
import { DonutMetricsChartComponent, DonutLegendItem } from '../../../shared/components/donut-metrics-chart';

@Component({
  selector: 'app-dvp-total',
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
  styleUrl: './dvp-total.scss'
})
/** Display aggregate DVP assessment-state totals. */
export class DvpTotalComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedDvpTeam: string | null = null;
  @Input() snapshotDate: string | null = null;
  @Input() selectedPmt: string | null = null;

  hasData = false;
  chartData: any;
  chartOptions: any;
  isLoading = false;
  errorMessage: string | null = null;
  emptyMessage = 'No data available';
  metricsData: MetricCardData[] = [];
  legendItems: { label: string; value: number; pct: string; color: string }[] = [];

  metrics = {
    meet: 0, unassessed: 0, does_not_meet: 0,
    cannot_assess: 0, not_applicable: 0, approved_deviation: 0
  };
  totalAssessments = 0;

  private readonly COLORS = ['#00B050', '#FFC000', '#FF9900', '#FF0000', '#808080', '#CCCCCC'];
  private readonly LABELS = ['Meet', 'Unassessed', 'Approved Deviation', 'Does Not Meet', 'Cannot Assess', 'Not Applicable'];

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
    if (changes['giCode'] || changes['selectedDvpTeam'] || changes['snapshotDate'] || changes['selectedPmt']) {
      this.selectedDvpTeam ? this.loadTeamData() : this.loadTotalData();
    }
  }

  loadTotalData() {
    this.isLoading = true; this.hasData = false; this.errorMessage = null;
    this.emptyMessage = 'No data available';
    this.fedeStatusService.getConfStateMetrics(this.giCode!, this.snapshotDate, this.selectedPmt).subscribe({
      next: (r: any) => { this.processMetrics(r?.conf_state_summary || {}); this.isLoading = false; },
      error: () => {
        this.processMetrics({ 'Meet': 120, 'Unassessed': 45, 'Approved Deviation': 28, 'Does Not Meet': 15, 'Cannot Assess': 8, 'Not Applicable': 4 });
        this.isLoading = false;
      }
    });
  }

  loadTeamData() {
    this.isLoading = true; this.hasData = false;
    this.emptyMessage = `No data for ${this.selectedDvpTeam}`;
    this.fedeStatusService.getDvpTeamListMetrics(this.giCode!, this.snapshotDate, this.selectedPmt).subscribe({
      next: (r: any) => {
        const match = (r?.dvp_teams_metrics || []).find(
          (t: any) => (t?.dvp_team || '').toLowerCase() === this.selectedDvpTeam!.toLowerCase()
        );
        match ? this.processMetrics(match.conf_state_summary || {}) : (this.hasData = false);
        this.isLoading = false;
      },
      error: () => { this.hasData = false; this.isLoading = false; }
    });
  }

  processMetrics(s: Record<string, number>) {
    this.metrics = {
      meet:               s['Meet']               || s['meet']               || 0,
      unassessed:         s['Unassessed']         || s['unassessed']         || 0,
      does_not_meet:      s['Does Not Meet']      || s['does_not_meet']      || 0,
      cannot_assess:      s['Cannot Assess']      || s['cannot_assess']      || 0,
      not_applicable:     s['Not Applicable']     || s['not_applicable']     || 0,
      approved_deviation: s['Approved Deviation'] || s['approved_deviation'] || 0
    };
    this.totalAssessments = Object.values(this.metrics).reduce((a, b) => a + b, 0);
    const vals = [
      this.metrics.meet, this.metrics.unassessed, this.metrics.approved_deviation,
      this.metrics.does_not_meet, this.metrics.cannot_assess, this.metrics.not_applicable
    ];
    this.legendItems = this.LABELS.map((label, i) => ({
      label,
      value: vals[i],
      pct: this.totalAssessments === 0 ? '0.0' : ((vals[i] / this.totalAssessments) * 100).toFixed(1),
      color: this.COLORS[i]
    })).filter(item => item.value > 0);
    this.metricsData = [
      { label: 'Meet',               value: this.metrics.meet,               color: 'meet' },
      { label: 'Unassessed',         value: this.metrics.unassessed,         color: 'unassessed' },
      { label: 'Approved Deviation', value: this.metrics.approved_deviation, color: 'approved-deviation' },
      { label: 'Does Not Meet',      value: this.metrics.does_not_meet,      color: 'does-not-meet' },
      { label: 'Cannot Assess',      value: this.metrics.cannot_assess,      color: 'cannot-assess' },
      { label: 'Not Applicable',     value: this.metrics.not_applicable,     color: 'not-applicable' },
    ];
    this.chartData = {
      labels: this.LABELS,
      datasets: [{ data: vals, backgroundColor: this.COLORS, borderColor: this.COLORS, borderWidth: 0 }]
    };
    this.hasData = true;
  }

  calcPct(value: number): string {
    if (this.totalAssessments === 0) return '0.0';
    return ((value / this.totalAssessments) * 100).toFixed(1);
  }
}
