import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PreviewDrawer } from './preview-drawer';

describe('PreviewDrawer', () => {
  let component: PreviewDrawer;
  let fixture: ComponentFixture<PreviewDrawer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PreviewDrawer],
    }).compileComponents();

    fixture = TestBed.createComponent(PreviewDrawer);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
