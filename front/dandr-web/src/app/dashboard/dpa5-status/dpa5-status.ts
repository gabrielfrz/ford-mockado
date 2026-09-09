import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Dpa5MetricsComponent } from '../components/dpa5-metrics';

interface ProjectSummary {
  vehicleLine: string;
  status: string;
  lastUpdated?: string;
}

@Component({
  selector: 'app-dpa5-status',
  standalone: true,
  imports: [CommonModule, Dpa5MetricsComponent],
  templateUrl: './dpa5-status.html',
  styleUrl: './dpa5-status.scss',
})
/** Host the DPA5 dashboard for the current vehicle selections. */
export class Dpa5StatusComponent implements OnInit, OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedProgram: string | null = null;

  summaryData: ProjectSummary | null = null;

  constructor() {}

  ngOnInit(): void {
    console.log('[DPA5 STATUS] Component initialized');
    this.loadSummaryData();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['giCode'] || changes['selectedProgram']) {
      console.log('[DPA5 STATUS] Inputs changed:', {
        giCode: this.giCode,
        selectedProgram: this.selectedProgram
      });
      this.loadSummaryData();
    }
  }

  /**
   * Load summary data (mocked)
   */
  private loadSummaryData(): void {
    // Mock summary data
    this.summaryData = {
      vehicleLine: 'CD6',
      status: 'Active',
      lastUpdated: new Date().toISOString()
    };
  }
}
