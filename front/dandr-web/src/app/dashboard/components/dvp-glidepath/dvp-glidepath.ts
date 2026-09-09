import { Component, Input, OnInit, OnChanges, SimpleChanges, OnDestroy, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgApexchartsModule } from 'ng-apexcharts';
import type {
  ApexAxisChartSeries,
  ApexChart,
  ApexXAxis,
  ApexYAxis,
  ApexLegend,
  ApexTooltip,
  ApexAnnotations,
  ApexDataLabels,
  ApexStroke,
  ApexFill
} from 'ng-apexcharts';
import { LoadingSpinnerComponent } from '../../../shared/components/loading-spinner/loading-spinner';
import { DvpGlidepathService, DvpGlidepathRecord } from '../../../services/dvp-glidepath.service';
import { Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-dvp-glidepath',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule, LoadingSpinnerComponent],
  templateUrl: './dvp-glidepath.html',
  styleUrl: './dvp-glidepath.scss',
})
/** Render DVP completion timelines and expose available chart filters. */
export class DvpGlidepathComponent implements OnInit, OnChanges, OnDestroy {
  @Input() giCode: string | null = null;
  @Input() selectedPmt: string | null = null;
  @Input() selectedMilestone: string | null = null;
  @Input() snapshotDate: string | null = null;

  @Output() pmtListChanged = new EventEmitter<string[]>();
  @Output() milestoneListChanged = new EventEmitter<string[]>();

  private destroy$ = new Subject<void>();

  // Chart state
  hasChartData = false;
  isLoadingGlidepath = false;
  errorMessage: string | null = null;

  apexSeries: ApexAxisChartSeries = [];
  apexChart: ApexChart = {
    type: 'line',
    height: 420,
    stacked: false,
    toolbar: { show: true },
    zoom: { enabled: false },
    animations: { enabled: true }
  };
  apexXAxis: ApexXAxis = {
    type: 'datetime',
    labels: {
      format: 'dd-MMM-yyyy',
      rotate: -45,
      rotateAlways: true,
      style: { fontSize: '10px', colors: '#6c757d' },
      datetimeUTC: false
    },
    title: {
      text: 'Date',
      style: { color: '#495057', fontWeight: '600', fontSize: '13px' }
    }
  };
  apexYAxis: ApexYAxis = {
    min: 0,
    max: 100,
    labels: {
      formatter: (val: number) => `${val.toFixed(0)}%`,
      style: { colors: '#6c757d', fontSize: '12px' }
    },
    title: {
      text: '% Completion',
      style: { color: '#495057', fontWeight: '600', fontSize: '13px' }
    }
  };
  apexColors: string[] = ['#28a745', '#FF9800'];
  apexStroke: ApexStroke = { width: [2.5, 2.5], curve: 'smooth' };
  apexDataLabels: ApexDataLabels = { enabled: false };
  apexLegend: ApexLegend = { show: false };
  apexTooltip: ApexTooltip = {
    shared: true,
    intersect: false,
    x: { format: 'dd-MMM-yyyy' },
    y: { formatter: (val: number) => val != null ? `${Math.round(val)}%` : 'N/A' }
  };
  apexFill: ApexFill = { opacity: [1, 1] };
  apexAnnotations: ApexAnnotations = {};

  constructor(private glidepathService: DvpGlidepathService) {}

  ngOnInit(): void {
    if (this.giCode) {
      this.fetchPmtsAndLoad();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['giCode'] && !changes['giCode'].firstChange && changes['giCode'].currentValue) {
      this.fetchPmtsAndLoad();
    } else if (changes['selectedPmt'] && !changes['selectedPmt'].firstChange) {
      this.fetchMilestonesAndLoad();
    } else if (changes['selectedMilestone'] && !changes['selectedMilestone'].firstChange) {
      this.loadData();
    } else if (changes['snapshotDate'] && !changes['snapshotDate'].firstChange) {
      this.loadData();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private fetchPmtsAndLoad(): void {
    if (!this.giCode) return;
    this.glidepathService.getPmts(this.giCode)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (pmts) => {
          this.pmtListChanged.emit(pmts);
          this.loadData();
        },
        error: () => {
          this.pmtListChanged.emit([]);
          this.loadData();
        }
      });
  }

  private fetchMilestonesAndLoad(): void {
    if (!this.giCode || !this.selectedPmt) {
      this.milestoneListChanged.emit([]);
      this.loadData();
      return;
    }
    this.glidepathService.getMilestones(this.giCode, this.selectedPmt)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (milestones) => {
          this.milestoneListChanged.emit(milestones);
          this.loadData();
        },
        error: () => {
          this.milestoneListChanged.emit([]);
          this.loadData();
        }
      });
  }

  loadGlidepathData(): void {
    this.loadData();
  }

  private loadData(): void {
    if (!this.giCode) return;

    this.isLoadingGlidepath = true;
    this.errorMessage = null;
    this.hasChartData = false;

    this.glidepathService.getData(this.giCode, this.selectedPmt, this.selectedMilestone, this.snapshotDate)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (records) => {
          this.buildCumulativeSeries(records);
          this.isLoadingGlidepath = false;
        },
        error: (err) => {
          this.errorMessage = 'Failed to load glidepath data';
          this.isLoadingGlidepath = false;
          console.error('DVP Glidepath error:', err);
        }
      });
  }

  private buildCumulativeSeries(records: DvpGlidepathRecord[]): void {
    if (records.length === 0) {
      this.hasChartData = false;
      return;
    }

    const total = records.length;

    // Scheduled series — cumulative % by scheduled_finished date
    const scheduledSorted = records
      .filter(r => r.scheduled_finished)
      .sort((a, b) => a.scheduled_finished!.localeCompare(b.scheduled_finished!));

    const scheduledRaw = scheduledSorted.map((r, i) => ({
      x: new Date(r.scheduled_finished!).getTime(),
      y: Math.round((i + 1) / total * 100)
    }));

    // Deduplicate: same date keeps the highest y (last in sorted order)
    const scheduledMap = new Map<number, number>();
    for (const pt of scheduledRaw) {
      scheduledMap.set(pt.x, pt.y);
    }
    const scheduledData = Array.from(scheduledMap.entries())
      .map(([x, y]) => ({ x, y }))
      .sort((a, b) => a.x - b.x);

    // Actual series — cumulative % by actual_finished date (nulls ignored)
    const actualSorted = records
      .filter(r => r.actual_finished)
      .sort((a, b) => a.actual_finished!.localeCompare(b.actual_finished!));

    const actualRaw = actualSorted.map((r, i) => ({
      x: new Date(r.actual_finished!).getTime(),
      y: Math.round((i + 1) / total * 100)
    }));

    // Deduplicate: same date keeps the highest y
    const actualMap = new Map<number, number>();
    for (const pt of actualRaw) {
      actualMap.set(pt.x, pt.y);
    }
    const actualData = Array.from(actualMap.entries())
      .map(([x, y]) => ({ x, y }))
      .sort((a, b) => a.x - b.x);

    // Milestone vertical annotation — only when a milestone filter is active.
    // The date comes from the records returned by the API (already filtered).
    const milestoneDate = this.selectedMilestone
      ? (records.find(r => r.milestone)?.milestone ?? null)
      : null;
    if (milestoneDate) {
      this.apexAnnotations = {
        xaxis: [{
          x: new Date(milestoneDate).getTime(),
          borderColor: '#1E40AF',
          borderWidth: 2,
          strokeDashArray: 0,
          label: {
            text: `Milestone: ${this.formatDate(milestoneDate)}`,
            borderColor: '#1E40AF',
            style: {
              color: '#fff',
              background: '#1E40AF',
              fontSize: '11px',
              fontWeight: '600',
              padding: { left: 6, right: 6, top: 3, bottom: 3 }
            },
            orientation: 'vertical',
            position: 'top',
            offsetY: 0
          }
        }]
      };
    } else {
      this.apexAnnotations = {};
    }

    this.apexSeries = [
      { name: 'Scheduled Finished', data: scheduledData },
      { name: 'Actual Finished', data: actualData }
    ];

    this.hasChartData = true;
  }

  private formatDate(dateStr: string): string {
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    const d = new Date(+parts[0], +parts[1] - 1, +parts[2]);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  }
}
