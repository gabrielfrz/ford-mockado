import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TimelineMilestones } from './timeline-milestones';

describe('TimelineMilestones', () => {
  let component: TimelineMilestones;
  let fixture: ComponentFixture<TimelineMilestones>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TimelineMilestones]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TimelineMilestones);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});