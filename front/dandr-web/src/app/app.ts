import { Component, OnDestroy, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { ToastModule } from 'primeng/toast';
import { Subject, takeUntil } from 'rxjs';
import { StateService } from './shared/state.service';
import { ToastService } from './shared/toast.service';

interface MilestoneOption { label: string; value: string; }
interface PmtOption { label: string; value: string | null; }

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    CommonModule,
    FormsModule,
    AutoCompleteModule,
    ToastModule
  ],
  templateUrl: './app.html',
  styleUrls: ['./app.scss']
})
/** Root application shell that coordinates navigation and global filters. */
export class App implements OnInit, OnDestroy {
  private noVehicleToastTimeout: ReturnType<typeof setTimeout> | null = null;
  private readonly destroying$ = new Subject<void>();

  activeChart: 'dvp' | 'designRules' | 'cae' | 'hir' | 'costs' | 'dpa5' | null = null;
  isSidebarVisible = true;
  isProfileMenuOpen = false;
  isIframe = false;
  loginDisplay = true;

  userName = 'Demo Visitor';
  userInitial = 'DV';

  activeItem = 'Home';

  programMilestoneSidebar: any = null;
  filteredMilestonesSidebar: MilestoneOption[] = [];

  allMilestones: MilestoneOption[] = [];

  // PMT codes for sidebar dropdown
  // NOTE: In the future these values will come from the backend
  // via a DVP service. For now we provide mocked data here.
  pmtCodeSidebar: PmtOption | null = null;
  allPmtCodes: PmtOption[] = [];
  filteredPmtCodes: PmtOption[] = [];

  currentVehicleDisplay = 'None';

  constructor(
    private state: StateService,
    private toast: ToastService,
  ) {}

  ngOnInit() {
    this.isIframe = window !== window.parent && !window.opener;

    this.state.vehicleName$.pipe(takeUntil(this.destroying$)).subscribe(name => {
      this.currentVehicleDisplay = name || 'None';
      // Start the guidance timer while no vehicle is selected.
      if (this.currentVehicleDisplay === 'None') {
        if (!this.noVehicleToastTimeout) {
          this.noVehicleToastTimeout = setTimeout(() => {
            this.showNoVehicleToast();
            this.noVehicleToastTimeout = null;
          }, 10000);
        }
      } else {
        // Cancel the guidance timer as soon as the user starts a search.
        if (this.noVehicleToastTimeout) {
          clearTimeout(this.noVehicleToastTimeout);
          this.noVehicleToastTimeout = null;
        }
      }
    });

    // Sincroniza activeChart com o StateService
    this.state.activeChart$.pipe(takeUntil(this.destroying$)).subscribe(chart => {
      this.activeChart = chart;
    });

    this.state.milestones$.pipe(takeUntil(this.destroying$)).subscribe(list => {
      this.allMilestones = list.map(m => ({
        label: (m.key || '').toUpperCase(),
        value: m.key
      }));

      this.filteredMilestonesSidebar = [...this.allMilestones];
    });

    // Mock PMT codes (100, 200, ..., 600). Replace with DVP service later.
    this.allPmtCodes = [
      { label: 'No PMT', value: null },
      ...[100, 200, 300, 400, 500, 600].map(n => ({ label: String(n), value: String(n) })),
    ];
    this.filteredPmtCodes = [...this.allPmtCodes];

    this.state.selectedPmtCode$
      .pipe(takeUntil(this.destroying$))
      .subscribe(pmtCode => {
        this.pmtCodeSidebar = this.allPmtCodes.find(option => option.value === pmtCode)
          ?? (pmtCode ? { label: pmtCode, value: pmtCode } : this.allPmtCodes[0]);
      });
  }

  filterMilestonesSidebar(event: any) {
    const q = event.query || '';
    this.filteredMilestonesSidebar = this.allMilestones.filter(m =>
      (m.label || '').toLowerCase().includes(q.toLowerCase())
    );
  }

  filterPmtCodes(event: any) {
    const q = event.query || '';
    this.filteredPmtCodes = this.allPmtCodes.filter(m =>
      (m.label || '').toLowerCase().includes(q.toLowerCase())
    );
  }

  toggleSidebar() {
    this.isSidebarVisible = !this.isSidebarVisible;
  }

  toggleProfileMenu() {
    this.isProfileMenuOpen = !this.isProfileMenuOpen;
  }

  selectMenu(item: any) {
    this.activeItem = item?.label || 'Home';
    if (window.innerWidth <= 768) this.isSidebarVisible = false;
  }

  handleLogout(): void {
    window.location.reload();
  }

  handleDVPStatus() {
    if (this.currentVehicleDisplay === 'None') {
      this.showNoVehicleToast();
      return;
    }
    const current = this.state.getActiveChart();
    this.state.setActiveChart(current === 'dvp' ? null : 'dvp');
  }

  handleDesignRules() {
    if (this.currentVehicleDisplay === 'None') {
      this.showNoVehicleToast();
      return;
    }
    const current = this.state.getActiveChart();
    this.state.setActiveChart(current === 'designRules' ? null : 'designRules');
  }

  handleHIRStatus() {
    if (this.currentVehicleDisplay === 'None') {
      this.showNoVehicleToast();
      return;
    }
    const current = this.state.getActiveChart();
    this.state.setActiveChart(current === 'hir' ? null : 'hir');
  }

  handleCAEStatus() {
    if (this.currentVehicleDisplay === 'None') {
      this.showNoVehicleToast();
      return;
    }
    const current = this.state.getActiveChart();
    this.state.setActiveChart(current === 'cae' ? null : 'cae');
  }

  handleCADStatus() {
    if (this.currentVehicleDisplay === 'None') {
      this.showNoVehicleToast();
      return;
    }
    this.toast.show({
      severity: 'info',
      summary: 'CAD Status',
      detail: 'CAD Status will be available soon.',
      life: 3000
    });
  }

  handleCostsStatus() {
    if (this.currentVehicleDisplay === 'None') {
      this.showNoVehicleToast();
      return;
    }
    const current = this.state.getActiveChart();
    this.state.setActiveChart(current === 'costs' ? null : 'costs');
  }

  handleDPA5Status() {
    if (this.currentVehicleDisplay === 'None') {
      this.showNoVehicleToast();
      return;
    }
    const current = this.state.getActiveChart();
    this.state.setActiveChart(current === 'dpa5' ? null : 'dpa5');
  }

  onPmtCodeSelect(event: any) {
    const selectedOption = event?.value;
    const value = selectedOption && typeof selectedOption === 'object' && 'value' in selectedOption
      ? selectedOption.value
      : selectedOption;
    this.state.setSelectedPmtCode(value ? String(value) : null);
  }

  onPmtCodeClear() {
    this.pmtCodeSidebar = null;
    this.state.setSelectedPmtCode(null);
  }

  showNoVehicleToast() {
    this.toast.show({
      severity: 'warn',
      summary: 'No Program Loaded',
      detail: 'Please search and select a program to enable sidebar options.',
      life: 4000
    });
  }

  ngOnDestroy(): void {
    if (this.noVehicleToastTimeout) {
      clearTimeout(this.noVehicleToastTimeout);
    }

    this.destroying$.next();
    this.destroying$.complete();
  }

}
