import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

/** Deliverable dashboard that is currently active. */
export type ChartType = 'dvp' | 'designRules' | 'cae' | 'hir' | 'costs' | 'dpa5' | null;

@Injectable({ providedIn: 'root' })
/** Central reactive store for cross-component dashboard selections. */
export class StateService {
  private vehicleNameSource = new BehaviorSubject<string>('None');
  vehicleName$ = this.vehicleNameSource.asObservable();

  private giCodeSource = new BehaviorSubject<string | null>(null);
  giCode$ = this.giCodeSource.asObservable();

  private milestonesSource = new BehaviorSubject<{ key: string, value: any }[]>([]);
  milestones$ = this.milestonesSource.asObservable();

  private activeChartSource = new BehaviorSubject<ChartType>('cae');
  activeChart$ = this.activeChartSource.asObservable();

  private selectedDvpTeamSource = new BehaviorSubject<string | null>(null);
  selectedDvpTeam$ = this.selectedDvpTeamSource.asObservable();

  private selectedMilestoneSource = new BehaviorSubject<string | null>(null);
  selectedMilestone$ = this.selectedMilestoneSource.asObservable();

  private selectedPmtCodeSource = new BehaviorSubject<string | null>(null);
  selectedPmtCode$ = this.selectedPmtCodeSource.asObservable();

  /** Update the selected vehicle display name. */
  setVehicleName(name: string) {
    this.vehicleNameSource.next(name);
  }

  /** Update the selected GI code. */
  setGiCode(code: string | null) {
    this.giCodeSource.next(code);
  }

  /** Replace the milestone timeline for the selected vehicle. */
  setMilestones(list: { key: string, value: any }[]) {
    this.milestonesSource.next(list);
  }

  /** Activate a deliverable dashboard. */
  setActiveChart(chartType: ChartType) {
    this.activeChartSource.next(chartType);
  }

  /** Return the current deliverable dashboard. */
  getActiveChart() {
    return this.activeChartSource.value;
  }

  /** Update the globally selected DVP team. */
  setSelectedDvpTeam(team: string | null) {
    this.selectedDvpTeamSource.next(team);
  }

  /** Return the globally selected DVP team. */
  getSelectedDvpTeam() {
    return this.selectedDvpTeamSource.value;
  }

  /** Update the globally selected milestone. */
  setSelectedMilestone(milestone: string | null) {
    this.selectedMilestoneSource.next(milestone);
  }

  /** Return the globally selected milestone. */
  getSelectedMilestone() {
    return this.selectedMilestoneSource.value;
  }

  /** Update the canonical PMT selected in the sidebar. */
  setSelectedPmtCode(pmt: string | null) {
    this.selectedPmtCodeSource.next(pmt);
  }

  /** Return the canonical PMT selected in the sidebar. */
  getSelectedPmtCode() {
    return this.selectedPmtCodeSource.value;
  }
}

