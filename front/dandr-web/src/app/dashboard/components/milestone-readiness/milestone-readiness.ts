import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { combineLatest, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { MilestoneReadinessService, MilestoneReadinessResponse, MilestoneMetric } from '../../../services/milestone-readiness.service';
import { StateService, ChartType } from '../../../shared/state.service';

@Component({
  selector: 'app-milestone-readiness',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './milestone-readiness.html',
  styleUrls: ['./milestone-readiness.scss'],
})
/** Display cross-deliverable readiness for the selected milestone. */
export class MilestoneReadinessComponent implements OnInit, OnDestroy {
  apiResponse: MilestoneReadinessResponse | null = null;
  activeChart: ChartType = null;
  isLoading = false;
  errorMessage: string | null = null;

  readonly SOURCE_MAP: Record<Exclude<ChartType, null>, string> = {
    cae: 'CAE',
    dvp: 'DVP',
    designRules: 'Design Rules',
    hir: 'HIR',
    costs: 'Costs',
    dpa5: 'DPA5'
  };

  private sub = new Subscription();

  constructor(
    private readinessService: MilestoneReadinessService,
    private state: StateService
  ) {}

  ngOnInit() {
    this.sub.add(
      this.state.activeChart$.subscribe(chart => (this.activeChart = chart))
    );

    this.sub.add(
      combineLatest([this.state.giCode$, this.state.selectedMilestone$, this.state.selectedPmtCode$])
        .pipe(filter(([gi, ms]) => !!gi && !!ms))
        .subscribe(([gi, ms, pmt]) => this.loadReadiness(gi!, ms!, pmt))
    );
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  get currentTarget(): MilestoneMetric | null {
    if (!this.apiResponse?.metrics?.length || !this.activeChart) return null;
    const sourceName = this.SOURCE_MAP[this.activeChart];
    return this.apiResponse.metrics.find(m => m.source === sourceName) ?? null;
  }

  private loadReadiness(giCode: string, milestone: string, pmtCode: string | null) {
    this.isLoading = true;
    this.errorMessage = null;
    this.apiResponse = null;

    this.readinessService.getReadiness(giCode, milestone, pmtCode).subscribe({
      next: (res) => {
        this.apiResponse = res;
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        if (err.status === 404) {
          this.errorMessage = 'Milestone date not defined for this program.';
        } else {
          this.errorMessage = 'Error loading metrics. Please try again later.';
        }
      }
    });
  }
}
