import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InterruptCard } from './interrupt-card';

describe('InterruptCard', () => {
  let component: InterruptCard;
  let fixture: ComponentFixture<InterruptCard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InterruptCard],
    }).compileComponents();

    fixture = TestBed.createComponent(InterruptCard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
