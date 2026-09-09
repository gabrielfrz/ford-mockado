import { Component, Input, OnInit, OnChanges, SimpleChanges, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgApexchartsModule } from 'ng-apexcharts';
import type {
  ApexAxisChartSeries,
  ApexChart,
  ApexXAxis,
  ApexYAxis,
  ApexPlotOptions,
  ApexLegend,
  ApexTooltip,
  ApexAnnotations,
  ApexDataLabels,
  ApexStroke,
  ApexFill
} from 'ng-apexcharts';
import { LoadingSpinnerComponent } from '../../../shared/components/loading-spinner/loading-spinner';
import { DonutMetricsChartComponent, DonutLegendItem } from '../../../shared/components/donut-metrics-chart';
import { MetricCardData } from '../../../shared/components/metrics-chart-module';
import { Dpa5Service, Dpa5GlidepathPoint } from '../../../services/dpa5.service';

interface Dpa5GlidepathData {
  date: string;
  milestoneName: string | null;
  compliant: number;
  notCompliant: number;
  notAssessable: number;
  assessmentGoal: number | null;
  complianceGoal: number | null;
  compliancePrediction: number | null;
}

interface Dpa5Metrics {
  compliant: number;
  notCompliant: number;
  notAssessable: number;
  total: number;
  complianceRate: number;
}

@Component({
  selector: 'app-dpa5-metrics',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule, LoadingSpinnerComponent, DonutMetricsChartComponent],
  templateUrl: './dpa5-metrics.html',
  styleUrl: './dpa5-metrics.scss',
})
/** Display DPA5 summary metrics and milestone glidepath targets. */
export class Dpa5MetricsComponent implements OnInit, OnChanges, OnDestroy {
  @Input() giCode: string | null = null;
  @Input() selectedProgram: string | null = null;
  @Input() selectedPmt: string | null = null;
  @Input() selectedCpsc: string | null = null;
  @Input() snapshotDate: string | null = null;

  // Donut chart properties
  isLoadingDonut = false;
  hasDonutData = false;
  donutChartData: any;
  donutChartOptions: any;
  donutMetricsData: MetricCardData[] = [];
  donutLegendItems: DonutLegendItem[] = [];
  totalItems = 0;

  private readonly DONUT_COLORS = ['#28a745', '#dc3545', '#007bff'];
  private readonly DONUT_LABELS = ['Compliant', 'Not Compliant', 'Not Assessable'];

  // Chart state
  hasChartData = false;

  // Loading states
  isLoadingGlidepath = false;

  // Error
  errorMessage: string | null = null;

  // ApexCharts properties
  apexSeries: ApexAxisChartSeries = [];
  apexChart: ApexChart = {
    type: 'bar',
    height: 420,
    stacked: true,
    toolbar: { show: true },
    zoom: { enabled: false },
    animations: { enabled: true }
  };
  apexXAxis: ApexXAxis = { categories: [] };
  apexYAxis: ApexYAxis = {
    min: 0,
    max: 100,
    labels: {
      formatter: (val: number) => `${val}%`,
      style: { colors: '#6c757d', fontSize: '12px' }
    },
    title: {
      text: 'Percentage (%)',
      style: { color: '#495057', fontWeight: '600', fontSize: '13px' }
    }
  };
  apexColors: string[] = ['#28a745', '#dc3545', '#007bff', '#6c757d', '#17a2b8', '#ffc107'];
  apexStroke: ApexStroke = {
    width: [0, 0, 0, 2.5, 2.5, 2.5],
    curve: 'smooth',
    dashArray: [0, 0, 0, 0, 0, 6]
  };
  apexPlotOptions: ApexPlotOptions = {
    bar: { columnWidth: '70%' }
  };
  apexDataLabels: ApexDataLabels = { enabled: false };
  apexLegend: ApexLegend = { show: false };
  apexTooltip: ApexTooltip = {
    shared: true,
    intersect: false,
    y: { formatter: (val: number) => val != null ? `${val.toFixed(1)}%` : 'N/A' }
  };
  apexFill: ApexFill = { opacity: [1, 1, 1, 1, 1, 1] };
  apexAnnotations: ApexAnnotations = {};

  // Current metrics for display
  currentMetrics: Dpa5Metrics = {
    compliant: 0,
    notCompliant: 0,
    notAssessable: 0,
    total: 0,
    complianceRate: 0
  };

  constructor(private dpa5Service: Dpa5Service) {
    this.donutChartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '72%',
      plugins: { legend: { display: false }, tooltip: { enabled: true } }
    };
  }

  ngOnInit(): void {
    if (this.giCode && this.selectedPmt) {
      this.loadDonutData();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['giCode'] || changes['selectedPmt'] || changes['selectedCpsc'] || changes['snapshotDate']) && this.giCode && this.selectedPmt) {
      this.loadDonutData();
    }
    if (changes['selectedPmt'] && !this.selectedPmt) {
      this.resetData();
    }
  }

  ngOnDestroy(): void {
    // ApexCharts cleanup is handled by NgApexchartsModule automatically
  }

  /**
   * Load all DPA5 data (donut + glidepath) from the real API.
   */
  private loadDonutData(): void {
    if (!this.giCode) return;
    this.isLoadingDonut = true;
    this.isLoadingGlidepath = true;
    this.errorMessage = null;

    this.dpa5Service.getSummary(this.giCode, this.selectedCpsc ?? undefined, this.selectedPmt ?? undefined, this.snapshotDate ?? undefined).subscribe({
      next: (resp) => {
        const { summary, glidepath } = resp;

        // --- Donut ---
        const compliant     = summary.compliant;
        const notCompliant  = summary.not_compliant;
        const notAssessable = summary.not_assessable;
        this.totalItems = summary.total;

        const values = [compliant, notCompliant, notAssessable];

        this.donutMetricsData = [
          { label: 'Total Items', value: this.totalItems },
          ...this.DONUT_LABELS.map((label, i) => ({
            label,
            value: values[i],
            percent: this.totalItems ? Math.round((values[i] / this.totalItems) * 100) : 0,
            color: ['compliant', 'not-compliant', 'not-assessable'][i]
          }))
        ];

        this.donutLegendItems = this.DONUT_LABELS.map((label, i) => ({
          label,
          value: values[i],
          pct: this.totalItems ? ((values[i] / this.totalItems) * 100).toFixed(1) : '0',
          color: this.DONUT_COLORS[i]
        }));

        this.donutChartData = {
          labels: this.DONUT_LABELS,
          datasets: [{
            data: values,
            backgroundColor: this.DONUT_COLORS,
            borderColor: '#FFFFFF',
            borderWidth: 2,
          }]
        };

        this.hasDonutData = true;
        this.isLoadingDonut = false;

        // --- Glidepath ---
        if (!glidepath || glidepath.length === 0) {
          this.hasChartData = false;
          this.isLoadingGlidepath = false;
          return;
        }

        const chartData: Dpa5GlidepathData[] = glidepath.map((p: Dpa5GlidepathPoint) => ({
          date:                p.milestone_date,
          milestoneName:       p.milestone_name ?? null,
          compliant:           p.compliant,
          notCompliant:        p.not_compliant,
          notAssessable:       p.not_assessable,
          assessmentGoal:      p.assessment_goal_curve,
          complianceGoal:      p.compliance_goal_curve,
          compliancePrediction: p.compliance_prediction,
        }));

        this.processGlidepathData(chartData);
        this.isLoadingGlidepath = false;
      },
      error: (err) => {
        console.error('[DPA5 METRICS] Error loading data:', err);
        this.errorMessage = err.error?.detail || 'Error loading DPA5 data';
        this.isLoadingDonut = false;
        this.isLoadingGlidepath = false;
        this.hasDonutData = false;
        this.hasChartData = false;
      }
    });
  }

  /**
   * Public method called from HTML "Try Again" button.
   */
  loadGlidepathData(): void {
    this.loadDonutData();
  }

  private resetData(): void {
    this.hasDonutData = false;
    this.hasChartData = false;
    this.errorMessage = null;
    this.isLoadingDonut = false;
    this.isLoadingGlidepath = false;
    this.totalItems = 0;
    this.donutChartData = null;
    this.donutMetricsData = [];
    this.donutLegendItems = [];
    this.apexSeries = [];
    this.currentMetrics = { compliant: 0, notCompliant: 0, notAssessable: 0, total: 0, complianceRate: 0 };
  }

  private processGlidepathData(data: Dpa5GlidepathData[]): void {
    if (data.length === 0) {
      this.hasChartData = false;
      return;
    }

    const latest = data[data.length - 1];
    this.currentMetrics = {
      compliant: latest.compliant,
      notCompliant: latest.notCompliant,
      notAssessable: latest.notAssessable,
      total: latest.compliant + latest.notCompliant + latest.notAssessable,
      complianceRate: (latest.compliant + latest.notCompliant) > 0
        ? Math.round((latest.compliant / (latest.compliant + latest.notCompliant)) * 100)
        : 0
    };

    this.hasChartData = true;
    try {
      this.renderChart(data);
    } catch (error) {
      console.error('[DPA5 METRICS] Error rendering chart:', error);
      this.errorMessage = 'Failed to render chart';
      this.hasChartData = false;
    }
  }

  /**
   * Render chart with ApexCharts
   */
  private renderChart(chartData: Dpa5GlidepathData[]): void {
    console.log('[DPA5 METRICS] Rendering chart with ApexCharts...');
    console.log('[DPA5 METRICS] chartData length:', chartData.length);

    // Prepare labels — try YYYY-MM-DD parse, fall back to raw string
    const labels = chartData.map(item => {
      const isoMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(item.date);
      if (isoMatch) {
        const date = new Date(+isoMatch[1], +isoMatch[2] - 1, +isoMatch[3]);
        return date.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
      }
      return item.date; // milestone name like "UPV1 09-Jan-2026"
    });

    const safe = (v: number | null | undefined, total: number) =>
      (v != null && total > 0) ? parseFloat(((v / total) * 100).toFixed(1)) : null;

    const computed = chartData.map(item => {
      const total = item.compliant + item.notCompliant + item.notAssessable;
      return {
        compliantPct:          safe(item.compliant, total),
        notCompliantPct:       safe(item.notCompliant, total),
        notAssessablePct:      safe(item.notAssessable, total),
        assessmentGoalPct:     item.assessmentGoal != null ? item.assessmentGoal : null,
        complianceGoalPct:     item.complianceGoal != null ? item.complianceGoal : null,
        compliancePredictionPct: item.compliancePrediction != null ? item.compliancePrediction : null
      };
    });

    // Update series (triggers ApexCharts re-render via Angular binding)
    this.apexSeries = [
      {
        name: 'Compliant',
        type: 'bar',
        data: computed.map(d => d.compliantPct)
      },
      {
        name: 'Not Compliant',
        type: 'bar',
        data: computed.map(d => d.notCompliantPct)
      },
      {
        name: 'Not Assessable',
        type: 'bar',
        data: computed.map(d => d.notAssessablePct)
      },
      {
        name: 'Assessment Goal',
        type: 'line',
        data: computed.map(d => d.assessmentGoalPct)
      },
      {
        name: 'Compliance Goal',
        type: 'line',
        data: computed.map(d => d.complianceGoalPct)
      },
      {
        name: 'Compliance Prediction',
        type: 'line',
        data: computed.map(d => d.compliancePredictionPct)
      }
    ];

    // Update X axis categories
    this.apexXAxis = {
      categories: labels,
      tickAmount: 10,
      labels: {
        rotate: -45,
        rotateAlways: true,
        style: { fontSize: '10px', colors: '#6c757d' },
        hideOverlappingLabels: true
      },
      title: {
        text: 'Date',
        style: { color: '#495057', fontWeight: '600', fontSize: '13px' }
      },
      axisBorder: { show: true, color: '#dee2e6' },
      axisTicks: { show: true }
    };

    // Build milestone vertical annotations using milestoneName from backend.
    // Each data point has a milestoneName (e.g. "UPV1 09-Jan-2026") — we annotate
    // the FIRST occurrence of each unique milestone type (UPV0, UPV1, FDJ, SOP, etc.)
    const annotatedTypes = new Set<string>();
    const xAnnotations = chartData
      .map((item, i) => {
        const name = item.milestoneName;
        if (!name) return null;
        // Extract short milestone type (e.g. "UPV1" from "UPV1 09-Jan-2026")
        const shortType = name.split(' ')[0];
        if (annotatedTypes.has(shortType)) return null;
        annotatedTypes.add(shortType);
        return { label: shortType, category: labels[i] };
      })
      .filter((x): x is { label: string; category: string } => x !== null);

    this.apexAnnotations = {
      xaxis: xAnnotations.map(m => ({
        x: m.category,
        borderColor: '#868e96',
        borderWidth: 2,
        strokeDashArray: 5,
        label: {
          text: m.label,
          borderColor: '#495057',
          style: {
            color: '#fff',
            background: '#495057',
            fontSize: '11px',
            fontWeight: '600',
            padding: { left: 6, right: 6, top: 3, bottom: 3 }
          },
          orientation: 'vertical',
          position: 'top',
          offsetY: 0
        }
      }))
    };

    console.log('[DPA5 METRICS] ApexCharts data set successfully');
  }
}
