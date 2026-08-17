import { Component, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-analytics',
  standalone: true,
  templateUrl: './analytics.html',
  styleUrls: ['./analytics.css']
})
export class Analytics implements AfterViewInit {
  title = 'Analytics Overview';

  @ViewChild('performanceChart') performanceChart!: ElementRef<HTMLCanvasElement>;
  @ViewChild('failureChart') failureChart!: ElementRef<HTMLCanvasElement>;

  ngAfterViewInit() {
    new Chart(this.performanceChart.nativeElement, {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        datasets: [{
          label: 'Efficiency %',
          data: [92, 88, 95, 90, 93],
          borderColor: '#2563eb',
          tension: 0.3,
          fill: false
        }]
      }
    });

    new Chart(this.failureChart.nativeElement, {
      type: 'pie',
      data: {
        labels: ['Motor', 'Pump', 'Conveyor', 'Sensor'],
        datasets: [{
          data: [35, 25, 20, 20],
          backgroundColor: ['#ef4444', '#f59e0b', '#10b981', '#3b82f6']
        }]
      }
    });
  }
}
