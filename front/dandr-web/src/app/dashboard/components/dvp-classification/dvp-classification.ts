import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FedeStatusService } from '../../../services/fede-status.service';
import { MetricCardData } from '../../../shared/components/metrics-chart-module';
import { DonutMetricsChartComponent, DonutLegendItem } from '../../../shared/components/donut-metrics-chart';

@Component({
  selector: 'app-dvp-classification',
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
  `
})
/** Visualize classified and unclassified DVP requirements. */
export class DvpClassificationComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedDvpTeam: string | null = null;
  @Input() selectedCpsc: string | null = null;
  @Input() snapshotDate: string | null = null;
  @Input() selectedPmt: string | null = null;

  hasData = false;
  chartData: any;
  chartOptions: any;
  isLoading = false;
  emptyMessage = 'Select a CPSC to view classification data';
  metricsData: MetricCardData[] = [];
  legendItems: DonutLegendItem[] = [];
  totalAssessments = 0;

  // Colors/labels for CPSC classification view (2 slices)
  private readonly CPSC_COLORS = ['#00B050', '#FF0000'];
  private readonly CPSC_LABELS = ['Classified', 'Not Classified'];

  // Colors/labels for conf_state view (6 slices)
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

    if (changes['selectedCpsc'] || changes['snapshotDate'] || changes['selectedPmt']) {
      const cpsc = this.selectedCpsc;
      if (cpsc && cpsc !== 'null') {
        this.loadClassificationMetrics(cpsc);
      } else {
        this.resetChart('Select a CPSC to view classification data');
      }
      return;
    }

    if (changes['giCode'] || changes['selectedDvpTeam'] || changes['snapshotDate']) {
      // If a CPSC is already selected, reload classification metrics
      if (this.selectedCpsc && this.selectedCpsc !== 'null') {
        this.loadClassificationMetrics(this.selectedCpsc);
        return;
      }
      this.selectedDvpTeam && this.selectedDvpTeam !== 'null'
        ? this.loadTeamData()
        : this.loadTotalData();
    }
  }

  loadClassificationMetrics(cpsc: string) {
    if (!this.giCode) return;
    this.isLoading = true;
    this.hasData = false;
    this.chartData = null;   // clear stale data before new request
    this.emptyMessage = `No classification data for CPSC: ${cpsc}`;

    this.fedeStatusService.getDvpClassification(this.giCode, cpsc, this.snapshotDate, this.selectedPmt).subscribe({
      next: (r) => {
        const classified = r?.classified ?? 0;
        const notClassified = r?.not_classified ?? 0;
        const total = r?.total ?? (classified + notClassified);

        if (total === 0) {
          this.resetChart(`No data for CPSC: ${cpsc}`);
          this.isLoading = false;
          return;
        }

        this.totalAssessments = total;
        const pct = (v: number) => total === 0 ? '0.0' : ((v / total) * 100).toFixed(1);

        this.legendItems = [
          { label: 'Classified',     value: classified,    pct: pct(classified),    color: this.CPSC_COLORS[0] },
          { label: 'Not Classified', value: notClassified, pct: pct(notClassified), color: this.CPSC_COLORS[1] },
        ].filter(item => item.value > 0);

        this.metricsData = [
          { label: 'Classified',     value: classified,    color: 'meet' },
          { label: 'Not Classified', value: notClassified, color: 'does-not-meet' },
        ];

        this.chartData = {
          labels: this.CPSC_LABELS,
          datasets: [{
            data: [classified, notClassified],
            backgroundColor: this.CPSC_COLORS,
            borderColor: this.CPSC_COLORS,
            borderWidth: 0
          }]
        };

        this.hasData = true;
        this.isLoading = false;
      },
      error: () => {
        this.resetChart('Error loading classification data');
        this.isLoading = false;
      }
    });
  }

  loadTotalData() {
    this.isLoading = true;
    this.hasData = false;
    this.emptyMessage = 'No classification data available';
    this.fedeStatusService.getConfStateMetrics(this.giCode!, this.snapshotDate, this.selectedPmt).subscribe({
      next: (r: any) => {
        this.processMetrics(r?.conf_state_summary || {});
        this.isLoading = false;
      },
      error: () => { this.resetChart('No classification data available'); this.isLoading = false; }
    });
  }

  loadTeamData() {
    this.isLoading = true;
    this.hasData = false;
    this.emptyMessage = `No classification data for ${this.selectedDvpTeam}`;
    this.fedeStatusService.getDvpTeamListMetrics(this.giCode!, this.snapshotDate, this.selectedPmt).subscribe({
      next: (r: any) => {
        const match = (r?.dvp_teams_metrics || []).find(
          (t: any) => (t?.dvp_team || '').toLowerCase() === this.selectedDvpTeam!.toLowerCase()
        );
        match ? this.processMetrics(match.conf_state_summary || {}) : this.resetChart(this.emptyMessage);
        this.isLoading = false;
      },
      error: () => { this.resetChart(this.emptyMessage); this.isLoading = false; }
    });
  }

  private resetChart(message: string) {
    this.hasData = false;
    this.totalAssessments = 0;
    this.legendItems = [];
    this.metricsData = [];
    this.chartData = null;
    this.emptyMessage = message;
  }

  processMetrics(s: Record<string, number>) {
    const m = {
      meet:               s['Meet']               || s['meet']               || 0,
      unassessed:         s['Unassessed']         || s['unassessed']         || 0,
      does_not_meet:      s['Does Not Meet']      || s['does_not_meet']      || 0,
      cannot_assess:      s['Cannot Assess']      || s['cannot_assess']      || 0,
      not_applicable:     s['Not Applicable']     || s['not_applicable']     || 0,
      approved_deviation: s['Approved Deviation'] || s['approved_deviation'] || 0,
    };
    this.totalAssessments = Object.values(m).reduce((a, b) => a + b, 0);
    const vals = [m.meet, m.unassessed, m.approved_deviation, m.does_not_meet, m.cannot_assess, m.not_applicable];
    const pct = (v: number) => this.totalAssessments === 0 ? '0.0' : ((v / this.totalAssessments) * 100).toFixed(1);

    this.legendItems = this.LABELS.map((label, i) => ({
      label, value: vals[i], pct: pct(vals[i]), color: this.COLORS[i]
    })).filter(item => item.value > 0);

    this.metricsData = [
      { label: 'Meet',               value: m.meet,               color: 'meet' },
      { label: 'Unassessed',         value: m.unassessed,         color: 'unassessed' },
      { label: 'Approved Deviation', value: m.approved_deviation, color: 'approved-deviation' },
      { label: 'Does Not Meet',      value: m.does_not_meet,      color: 'does-not-meet' },
      { label: 'Cannot Assess',      value: m.cannot_assess,      color: 'cannot-assess' },
      { label: 'Not Applicable',     value: m.not_applicable,     color: 'not-applicable' },
    ];

    this.chartData = {
      labels: this.LABELS,
      datasets: [{ data: vals, backgroundColor: this.COLORS, borderColor: this.COLORS, borderWidth: 0 }]
    };
    this.hasData = true;
  }
}
