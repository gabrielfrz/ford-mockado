import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DvpStatus } from './dvp-status';

describe('DvpStatus', () => {
  let component: DvpStatus;
  let fixture: ComponentFixture<DvpStatus>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DvpStatus]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DvpStatus);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize chart state before data is loaded', () => {
    expect(component.assessmentChartData).toBeNull();
    expect(component.assessmentChartOptions).toBeNull();
    expect(component.cpscChartData).toBeNull();
    expect(component.cpscChartOptions).toBeNull();
  });

  it('should retain the selected DVP team', () => {
    component.selectedDvpTeam = 'Team A';

    expect(component.selectedDvpTeam).toBe('Team A');
  });
});
