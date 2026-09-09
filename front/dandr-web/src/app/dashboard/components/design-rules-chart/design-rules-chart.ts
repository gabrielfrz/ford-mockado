import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import Chart from 'chart.js/auto';
import { LoadingSpinnerComponent } from '../../../shared/components/loading-spinner';
import { VehicleLineService } from '../../../services/vehicle-line.service';
import { MetricsGridComponent, MetricCardData } from '../../../shared/components/metrics-chart-module';

@Component({
  selector: 'app-design-rules-chart',
  standalone: true,
  imports: [CommonModule, ChartModule, LoadingSpinnerComponent, MetricsGridComponent],
  templateUrl: './design-rules-chart.html',
  styleUrl: './design-rules-chart.scss',
})
/** Render Design Rule classification totals as a dashboard chart. */
export class DesignRulesChart implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() modelYear: string | null = null;
  @Input() programName: string | null = null;
  @Input() selectedCpsc: string | null = null;
  @Input() view: 'evidences' | 'classification' = 'evidences';
  @Input() selectedPmt: string | null = null;

  evidencesChartData: any = null;
  evidencesChartOptions: any = null;
  evidencesMetrics: MetricCardData[] = [];
  evidencesLegend: { label: string; color: string; pct: string }[] = [];
  evidencesTotal = 0;
  isLoadingEvidences = false;

  classificationChartData: any = null;
  classificationChartOptions: any = null;
  classificationMetrics: MetricCardData[] = [];
  classificationLegend: { label: string; color: string; pct: string }[] = [];
  classificationTotal = 0;
  isLoadingClassification = false;

  constructor(private vehicleLineService: VehicleLineService) {
    this.registerChartPlugin();
  }

  private registerChartPlugin() {
    const plugin = { id: 'textCenter' };
    Chart.register(plugin);
  }

  ngOnChanges(changes: SimpleChanges) {
    const inputChanged = changes['giCode'] || changes['modelYear'] || changes['programName'] || changes['selectedCpsc'] || changes['view'] || changes['selectedPmt'];
    if (!inputChanged) return;

    if (this.view === 'evidences') {
      if (this.giCode) {
        this.loadEvidencesData();
      } else {
        this.evidencesChartData = null;
        this.evidencesMetrics = [];
      }
    } else {
      if (this.modelYear && this.programName) {
        this.loadClassificationData();
      } else {
        this.classificationChartData = null;
        this.classificationMetrics = [];
      }
    }
  }

  private loadEvidencesData() {
    this.isLoadingEvidences = true;
    this.evidencesChartData = null;

    this.vehicleLineService.getDrEvidencesByAssessment(this.giCode!, this.selectedCpsc, this.selectedPmt).subscribe({
      next: (res) => {
        const items: any[] = res?.data ?? [];

        const totalMeet = items.reduce((a: number, d: any) => a + (d.meet ?? 0), 0);
        const totalDnm  = items.reduce((a: number, d: any) => a + (d.does_not_meet ?? 0), 0);
        const totalUnassessed = items.reduce((a: number, d: any) => a + (d.unassessed ?? 0), 0);

        const labels = ['Meet', 'Does Not Meet', 'Unassessed'];
        const values = [totalMeet, totalDnm, totalUnassessed];
        const colors = ['#00B050', '#FF0000', '#FFC000'];
        this.evidencesTotal = totalMeet + totalDnm + totalUnassessed;

        this.evidencesChartData = {
          labels,
          datasets: [
            {
              label: 'Evidences',
              data: values,
              backgroundColor: colors,
              borderRadius: 6,
              borderSkipped: false,
              barPercentage: 0.5,
              categoryPercentage: 0.6
            }
          ]
        };

        this.evidencesMetrics = [
          { label: 'Meet',          value: totalMeet,      color: 'meet' },
          { label: 'Does Not Meet', value: totalDnm,       color: 'does-not-meet' },
          { label: 'Unassessed',    value: totalUnassessed, color: 'unassessed' }
        ];

        this.evidencesLegend = [
          { label: 'Meet',          color: '#00B050', pct: this.evidencesTotal ? ((totalMeet / this.evidencesTotal) * 100).toFixed(1) : '0' },
          { label: 'Does Not Meet', color: '#FF0000', pct: this.evidencesTotal ? ((totalDnm / this.evidencesTotal) * 100).toFixed(1) : '0' },
          { label: 'Unassessed',    color: '#FFC000', pct: this.evidencesTotal ? ((totalUnassessed / this.evidencesTotal) * 100).toFixed(1) : '0' }
        ];

        this.evidencesChartOptions = this.getSingleBarChartOptions();
        this.isLoadingEvidences = false;
      },
      error: () => {
        this.evidencesChartData = null;
        this.isLoadingEvidences = false;
      }
    });
  }

  private loadClassificationData() {
    this.isLoadingClassification = true;
    this.classificationChartData = null;

    this.vehicleLineService.getDrClassification(this.modelYear!, this.programName!, this.selectedPmt).subscribe({
      next: (res) => {
        const items: any[] = res?.data ?? [];

        // Aggregate totals across all rows (each row = one program/year combination)
        const totals = items.reduce(
          (acc: any, row: any) => ({
            applicable:     acc.applicable     + (row.applicable     ?? 0),
            carryover:      acc.carryover      + (row.carryover      ?? 0),
            not_applicable: acc.not_applicable + (row.not_applicable ?? 0),
            unclassified:   acc.unclassified   + (row.unclassified   ?? 0),
          }),
          { applicable: 0, carryover: 0, not_applicable: 0, unclassified: 0 }
        );

        const labels = ['Applicable', 'Carryover', 'Not Applicable', 'Unclassified'];
        const values = [totals.applicable, totals.carryover, totals.not_applicable, totals.unclassified];
        const colors = ['#00BFA5', '#2196F3', '#FF9800', '#455A64'];
        const colorTokens = ['dr-applicable', 'dr-carryover', 'dr-not-applicable', 'dr-unclassified'];

        this.classificationTotal = values.reduce((a, b) => a + b, 0);

        this.classificationChartData = {
          labels,
          datasets: [{
            label: 'Values',
            data: values,
            backgroundColor: colors,
            borderRadius: 6,
            borderSkipped: false,
            barPercentage: 0.8,
            categoryPercentage: 0.85
          }]
        };

        this.classificationMetrics = labels.map((label, i) => ({
          label,
          value: values[i],
          color: colorTokens[i]
        }));

        this.classificationLegend = labels.map((label, i) => ({
          label,
          color: colors[i],
          pct: this.classificationTotal ? ((values[i] / this.classificationTotal) * 100).toFixed(1) : '0'
        }));

        this.classificationChartOptions = this.getSingleBarChartOptions();
        this.isLoadingClassification = false;
      },
      error: () => {
        this.classificationChartData = null;
        this.isLoadingClassification = false;
      }
    });
  }

  private getSingleBarChartOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: true,
          backgroundColor: 'rgba(38, 50, 56, 0.95)',
          titleColor: '#ffffff',
          bodyColor: '#E0E0E0',
          borderColor: '#546E7A',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 6,
          displayColors: false,
          titleFont: { size: 12, weight: 'bold' },
          bodyFont: { size: 12 },
          callbacks: {
            title: (context: any) => context[0].label,
            label: (context: any) => 'Value: ' + context.parsed.y
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#263238', font: { size: 13, weight: '600' }, padding: 10 },
          grid: { display: false, drawBorder: false }
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#546E7A', font: { size: 11, weight: '500' }, padding: 10 },
          grid: { display: true, drawBorder: false, color: 'rgba(236, 239, 241, 0.5)', lineWidth: 1 }
        }
      }
    };
  }
}
