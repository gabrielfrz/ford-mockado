import { TestBed } from '@angular/core/testing';
import { RouterModule } from '@angular/router';
import { MessageService } from 'primeng/api';
import { App } from './app';
import { StateService } from './shared/state.service';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        App,
        RouterModule.forRoot([]),
      ],
      providers: [MessageService],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render the dashboard title', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.sidebar-title')?.textContent).toContain(
      'Engineering Dashboard',
    );
  });

  it('should allow the PMT filter to be unset', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const app = fixture.componentInstance;
    const state = TestBed.inject(StateService);
    const noPmtOption = app.allPmtCodes.find(option => option.value === null)!;

    expect(noPmtOption.label).toBe('No PMT');

    state.setSelectedPmtCode('300');
    app.onPmtCodeSelect({ value: noPmtOption });

    expect(state.getSelectedPmtCode()).toBeNull();
    expect(app.pmtCodeSidebar).toEqual(noPmtOption);
  });

});
