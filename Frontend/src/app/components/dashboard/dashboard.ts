import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChangeDetectorRef, Component, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatOptionModule } from '@angular/material/core';
import { MatSliderModule } from '@angular/material/slider';
import { MatButtonModule } from '@angular/material/button';
import { Chart, registerables } from 'chart.js';
import { debounceTime, Subject, forkJoin, of, timer, Subscription } from 'rxjs';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, switchMap } from 'rxjs/operators';
Chart.register(...registerables);

interface RobotSensors { [key: string]: number; }

interface RobotApi {
  machine_name: string;
  state: 'NORMAL' | 'WARNING';
  maintenance_completed: boolean;
  hits: number;
  change_frequency: number;
  sensors: RobotSensors;
  timestamp?: string;
}

interface Robot extends RobotApi { equipmentId: string; }

interface SensorApiResponse { sensor_data: { [key: string]: RobotApi }; }

@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css'],
  imports: [
    CommonModule,
    FormsModule,
    MatSliderModule,
    MatButtonModule,
    MatSelectModule,
    MatFormFieldModule,
    MatOptionModule
  ]
})
export class Dashboard implements OnDestroy {
  title = 'Predictive Maintenance Dashboard';
  robots: Robot[] = [];
  selectedEquipment = '';

  /** single array for slider values (index 0..4) */
  sliderValues: number[] = [0, 0, 0, 0, 0];

  private sliderChange$ = new Subject<void>();
  private pollingSub?: Subscription;
  private sliderSub?: Subscription;

  // anomaly counts per machine
  anomalyCounts: Record<string, number> = {};
  lastPredictions: { machine_id: string; prediction: string }[] = [];

  lineChart?: Chart;
  barChart?: Chart;

  constructor(private http: HttpClient, private cdr: ChangeDetectorRef, private snackBar: MatSnackBar) {}

  ngOnInit() {
    this.loadData();

    // subscribe to slider changes (debounced)
    this.sliderSub = this.sliderChange$.pipe(debounceTime(500)).subscribe(() => {
      this.callApiWithParams();
      this.updateChartData();
    });

    // start polling alerts every 15 seconds (immediate first tick)
    this.startAlertPolling();
  }

  ngOnDestroy() {
    this.pollingSub?.unsubscribe();
    this.sliderSub?.unsubscribe();
  }

  formatLabel(value: number): string { return `${value}`; }

  loadData() {
    this.http.get<SensorApiResponse>('http://127.0.0.1:5000/current-sensors')
      .subscribe(res => {
        this.robots = Object.entries(res.sensor_data).map(([key, robot]) => ({
          equipmentId: key,
          ...robot
        }));

        if (!this.selectedEquipment && this.robots.length > 0) {
          this.selectedEquipment = this.robots[0].equipmentId;
        }

        this.initSlidersForSelectedEquipment();

        // initialize anomalyCounts for all machines (start at 0)
        this.anomalyCounts = this.robots.reduce((acc, r) => {
          acc[r.equipmentId] = acc[r.equipmentId] ?? 0;
          return acc;
        }, {} as Record<string, number>);

        this.renderLineChart();
        this.renderBarChart();
        this.cdr.detectChanges();
      });
  }

  /** start polling alerts endpoint every 15 seconds and show snackbars */
  startAlertPolling() {
    // timer(0, 15000) emits immediately then every 15s
    this.pollingSub = timer(0, 15000).pipe(
      switchMap(() =>
        this.http.get<{ alerts: { timestamp: string; machine_id: string; message: string; assigned: boolean }[] }>(
          'http://localhost:8000/fetch-alerts'
        ).pipe(
          catchError(err => {
            console.error('Alert fetch failed', err);
            return of({ alerts: [] });
          })
        )
      )
    ).subscribe(res => {
      const alerts = res?.alerts ?? [];
      if (alerts.length) {
        // convert alerts to snackbar messages and queue them
        const messages = alerts.map(a => ({
          text: `${a.machine_id}: ${a.message}`,
          panelClass: ['warning-snackbar'],
          machineId: a.machine_id
        }));
        this.showSnackBarQueue(messages);
      }
    });
  }

  /** Call assign-alert endpoint for a machine */
  assignAlert(machineId: string) {
    if (!machineId) return;

    const url = `http://localhost:8000/assign-alert/${encodeURIComponent(machineId)}`;
    // Use POST; change to GET if your backend expects GET
    this.http.post(url, {}).pipe(
      catchError(err => {
        console.error(`Failed to assign alert for ${machineId}`, err);
        return of(null);
      })
    ).subscribe(res => {
      // optional: show a small confirmation snackbar
      if (res) {
        this.snackBar.open(`Assigned alert for ${machineId}`, 'Close', { duration: 2000, horizontalPosition: 'right', verticalPosition: 'bottom' });
      }
    });
  }
  /** called when user changes equipment from dropdown */
  onEquipmentChange() {
    this.initSlidersForSelectedEquipment();
    this.renderLineChart();
    this.renderBarChart(this.lastPredictions.length ? this.lastPredictions : undefined);
  }

  /** initialize sliderValues[] from current robot sensors or defaults */
  initSlidersForSelectedEquipment() {
    const sensors = this.sensorMap[this.selectedEquipment] || [];
    const robot = this.robots.find(r => r.equipmentId === this.selectedEquipment);
    this.sliderValues = sensors.map((s, i) => {
      const val = robot?.sensors?.[s];
      if (typeof val === 'number') return val;
      const range = this.sensorRanges[this.selectedEquipment]?.[i];
      if (range) return +(((range.min + range.max) / 2).toFixed(this.stepDecimals(range.step)));
      return 0;
    });
  }

  private stepDecimals(step: number) {
    const s = String(step);
    return s.includes('.') ? s.split('.')[1].length : 0;
  }

  onSliderChange(index: number, event: any) {
    const value = Number(event.value ?? event.target?.value ?? 0) || 0;
    this.sliderValues[index] = value;
    this.sliderChange$.next();
  }

  resetSliders() {
    const sensors = this.sensorMap[this.selectedEquipment] || [];
    this.sliderValues = sensors.map((_, i) => {
      const r = this.sensorRanges[this.selectedEquipment]?.[i];
      return r ? +(((r.min + r.max) / 2).toFixed(this.stepDecimals(r.step))) : 0;
    });

    this.cdr.detectChanges();
    this.callApiWithParams();
    this.updateChartData();
  }

  // Sensor mapping for each equipment
  sensorMap: Record<string, string[]> = {
    R101: ['joint_temperature_c', 'motor_current_a', 'joint_vibration_mm_s', 'encoder_position_deg', 'torque_nm'],
    R102: ['welding_temperature_c', 'spindle_torque_nm', 'coolant_flow_rate_lpm', 'motor_current_a', 'vibration_mm_s'],
    R103: ['pneumatic_pressure_bar', 'riveting_force_kn', 'motor_current_a', 'vibration_mm_s', 'encoder_position_deg'],
    R104: ['paint_pressure_bar', 'paint_flow_rate_lpm', 'nozzle_temperature_c', 'pump_current_a', 'robot_speed_mm_s'],
    R105: ['camera_temperature_c', 'laser_thickness_sensor_um', 'lighting_intensity_lux', 'cpu_temperature_c', 'camera_position_encoder_deg']
  };

  sliderLabels: Record<string, string[]> = {
    R101: ['Joint Temperature', 'Motor Current', 'Joint Vibration', 'Encoder Position', 'Torque'],
    R102: ['Welding Temperature', 'Spindle Torque', 'Coolant Flow Rate', 'Motor Current', 'Vibration'],
    R103: ['Pneumatic Pressure', 'Riveting Force', 'Motor Current', 'Vibration', 'Encoder Position'],
    R104: ['Paint Pressure', 'Paint Flow Rate', 'Nozzle Temperature', 'Pump Current', 'Robot Speed'],
    R105: ['Camera Temperature', 'Laser Thickness', 'Lighting Intensity', 'CPU Temperature', 'Camera Position']
  };

  sensorUnits: Record<string, string> = {
    joint_temperature_c: '°C', welding_temperature_c: '°C', camera_temperature_c: '°C', cpu_temperature_c: '°C',
    motor_current_a: 'A', pump_current_a: 'A',
    joint_vibration_mm_s: 'mm/s', vibration_mm_s: 'mm/s',
    encoder_position_deg: 'deg', camera_position_encoder_deg: 'deg',
    torque_nm: 'Nm', spindle_torque_nm: 'Nm',
    coolant_flow_rate_lpm: 'L/min', paint_flow_rate_lpm: 'L/min',
    pneumatic_pressure_bar: 'bar', paint_pressure_bar: 'bar',
    riveting_force_kn: 'kN', robot_speed_mm_s: 'mm/s',
    laser_thickness_sensor_um: 'µm', lighting_intensity_lux: 'lux'
  };

  sensorRanges: Record<string, { min: number; max: number; step: number }[]> = {
    R101: [
      { min: 64.8, max: 65.3, step: 0.1 },
      { min: 12.9, max: 13.1, step: 0.1 },
      { min: 1.98, max: 2.01, step: 0.01 },
      { min: 0.39, max: 0.46, step: 0.01 },
      { min: 729.91, max: 730.21, step: 0.1 }
    ],
    R102: [
      { min: 261, max: 264, step: 1 },
      { min: 963.02, max: 967.02, step: 0.1 },
      { min: 15.98, max: 16.04, step: 0.01 },
      { min: 21.84, max: 22.24, step: 0.01 },
      { min: 2.257, max: 2.297, step: 0.001 }
    ],
    R103: [
      { min: 5.01, max: 7.01, step: 0.01 },
      { min: 7.2, max: 8.2, step: 0.01 },
      { min: 13, max: 13.2, step: 0.01 },
      { min: 3.09, max: 3.11, step: 0.01 },
      { min: 0.16, max: 0.26, step: 0.01 }
    ],
    R104: [
      { min: 5.6, max: 5.8, step: 0.01 },
      { min: 24.01, max: 26.01, step: 0.01 },
      { min: 51.50, max: 54.50, step: 0.01 },
      { min: 10.1, max: 10.3, step: 0.01 },
      { min: 148, max: 152, step: 1 }
    ],
    R105: [
      { min: 45.6, max: 45.8, step: 0.01 },
      { min: 48, max: 50, step: 0.1 },
      { min: 978, max: 980, step: 1 },
      { min: 0.03, max: 0.05, step: 0.01 },
      { min: 0.11, max: 0.13, step: 0.01 }
    ]
  };

  /**
   * Posts sensor values for the selected equipment (one POST per sensor),
   * waits for all POSTs to complete, then fetches anomaly predictions
   * and re-renders the bar chart using the prediction response.
   */
  callApiWithParams() {
    const sensors = this.sensorMap[this.selectedEquipment] || [];

    const postCalls = sensors.map((sensorName, idx) => {
      const payload = {
        machine_id: this.selectedEquipment,
        sensor_name: sensorName,
        reading: Number(this.sliderValues[idx] ?? 0)
      };

      return this.http.post('http://127.0.0.1:5000/simulate-sensor', payload).pipe(
        catchError(err => {
          console.error(`POST failed for ${sensorName}`, err);
          return of(null);
        })
      );
    });

    forkJoin(postCalls).pipe(
      switchMap(() => this.getAnomalyPredictions())
    ).subscribe({
      next: (predRes) => {
        const predictions = predRes?.data ?? [];
        this.lastPredictions = predictions;

        // Update anomalyCounts: increment only for machines with anomaly prediction
        predictions.forEach(p => {
          if (!p || !p.machine_id) return;
          const isAnomaly = String(p.prediction || '').toLowerCase().includes('anomaly');
          if (isAnomaly) {
            this.anomalyCounts[p.machine_id] = (this.anomalyCounts[p.machine_id] ?? 0) + 1;
          } else {
            this.anomalyCounts[p.machine_id] = this.anomalyCounts[p.machine_id] ?? 0;
          }
        });

        this.renderBarChart(predictions);
      },
      error: (err) => {
        console.error('Error in posting sensors or fetching predictions', err);
        this.renderBarChart();
      }
    });
  }

  /**
   * Render bar chart. If `predictions` is provided (array of { machine_id, prediction }),
   * use anomalyCounts for y values. If not provided, fallback to robots.hits.
   */
  renderBarChart(predictions?: { machine_id: string; prediction: string }[]) {
    if (this.barChart) this.barChart.destroy();

    const predMap = (predictions || []).reduce((acc, p) => {
      if (p?.machine_id) acc[p.machine_id] = p.prediction;
      return acc;
    }, {} as Record<string, string>);

    if (predictions && predictions.length > 0) {
      const labels = predictions.map(p => p.machine_id);
      const data: number[] = labels.map(id => this.anomalyCounts[id] ?? 0);
      const backgroundColor = predictions.map(p =>
        String(p.prediction || '').toLowerCase().includes('anomaly') ? 'rgba(239,68,68,0.9)' : 'rgba(34,197,94,0.9)'
      );

      const maxCount = data.length ? Math.max(...data) : 1;
      const suggestedMax = Math.max(1, maxCount + 1);

      this.barChart = new Chart('anomalyChart', {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Anomaly Count', data, backgroundColor }] },
        options: {
          responsive: true,
          plugins: {
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  const machine = labels[ctx.dataIndex] || '';
                  const pred = predMap[machine] || 'No prediction';
                  const count = this.anomalyCounts[machine] ?? 0;
                  return [`Machine: ${machine}`, `Prediction: ${pred}`, `Anomaly Count: ${count}`];
                }
              }
            },
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { stepSize: 1, precision: 0 },
              suggestedMax,
              title: { display: true, text: 'Anomalies' }
            },
            x: { title: { display: true, text: 'Machine ID' } }
          }
        }
      });

      return;
    }

    // Fallback: use robots.hits
    const labels = this.robots.map(d => d.equipmentId);
    const data = this.robots.map(d => d.hits);
    const bg = this.robots.map(d => d.state === 'WARNING' ? 'orange' : 'green');

    this.barChart = new Chart('anomalyChart', {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label: 'Issues (Hits)', data, backgroundColor: bg }]
      },
      options: {
        responsive: true,
        plugins: {
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const robot = this.robots[ctx.dataIndex];
                return [
                  `State: ${robot.state}`,
                  `Hits: ${robot.hits}`,
                  ...Object.entries(robot.sensors).map(([k, v]) => `${k}: ${v}`)
                ];
              }
            }
          },
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1 },
            suggestedMax: Math.max(5, Math.max(...data) + 1),
            title: { display: true, text: 'Anomalies' }
          },
          x: { title: { display: true, text: 'Machine Name' } }
        }
      }
    });
  }

  /**
   * Fetch anomaly predictions from the API that returns:
   * { data: [{ machine_id: 'R101', prediction: 'Anomaly detected' }, ...] }
   */
  getAnomalyPredictions() {
    return this.http.get<{ data: { machine_id: string; prediction: string }[] }>(
      'http://127.0.0.1:5000/simulate-sensor'
    ).pipe(
      catchError(err => {
        console.error('Failed to fetch anomaly predictions', err);
        return of({ data: [] });
      })
    );
  }

  /** Queue and show snackbars sequentially */
  /**
   * messages: array of { text: string; panelClass: string[]; machineId?: string }
   * When each snackbar is dismissed, call assignAlert(machineId) if provided.
   */
  showSnackBarQueue(messages: { text: string; panelClass: string[]; machineId?: string }[]) {
    let index = 0;

    const showNext = () => {
      if (index >= messages.length) return;

      const msg = messages[index++];
      const ref = this.snackBar.open(msg.text, 'Close', {
        duration: 4000,
        horizontalPosition: 'right',
        verticalPosition: 'bottom',
        panelClass: msg.panelClass
      });

      // When snackbar is dismissed (timeout or user closed), call assign API if machineId present
      ref.afterDismissed().subscribe(() => {
        if (msg.machineId) {
          this.assignAlert(msg.machineId);
        }
        // show next message in queue
        showNext();
      });

      // If user clicks the action button, also call assign immediately and continue
      ref.onAction().subscribe(() => {
        if (msg.machineId) {
          this.assignAlert(msg.machineId);
        }
        // after action, the snackbar will be dismissed and afterDismissed will fire too,
        // but calling assign twice is harmless because assignAlert tolerates duplicates.
      });
    };

    showNext();
  }

  renderLineChart() {
    if (this.lineChart) this.lineChart.destroy();

    const sensors = this.sensorMap[this.selectedEquipment] || [];
    const labels = this.robots.map(r => new Date(r.timestamp || Date.now()).toLocaleTimeString());

    const datasets = sensors.map((sensorName, idx) => {
      const data = this.robots.map(r => r.sensors?.[sensorName] ?? 0);
      return {
        label: `${this.selectedEquipment} - ${this.sliderLabels[this.selectedEquipment]?.[idx] || sensorName}`,
        data,
        borderColor: this.getColor(idx),
        backgroundColor: this.getColor(idx, 0.25),
        fill: false,
        tension: 0.3
      };
    });

    this.lineChart = new Chart('sensorChart', {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          title: { display: true, text: `Sensor Trends for Equipment ${this.selectedEquipment}` },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const datasetLabel = ctx.dataset.label || '';
                const sensorKey = this.sensorMap[this.selectedEquipment]?.[ctx.datasetIndex ?? 0];
                const unit = sensorKey ? (this.sensorUnits[sensorKey] || '') : '';
                const robot = this.robots[ctx.dataIndex] || { equipmentId: this.selectedEquipment, machine_name: '' };
                return [
                  `Equipment: ${robot.equipmentId}`,
                  `Machine: ${robot.machine_name}`,
                  `Sensor: ${datasetLabel}`,
                  `Value: ${ctx.formattedValue}${unit}`
                ];
              }
            }
          }
        },
        scales: {
          x: { title: { display: true, text: 'Time' } },
          y: { title: { display: true, text: 'Reading' }, beginAtZero: true }
        }
      }
    });
  }

  updateChartData() {
    if (!this.lineChart) return;

    const time = new Date().toLocaleTimeString();
    this.lineChart.data.labels?.push(time);

    const sensors = this.sensorMap[this.selectedEquipment] || [];
    sensors.forEach((_, idx) => {
      const ds = this.lineChart?.data.datasets?.[idx];
      if (ds) {
        (ds.data as number[]).push(Number(this.sliderValues[idx] ?? 0));
      }
    });

    const maxPoints = 30;
    if ((this.lineChart.data.labels?.length ?? 0) > maxPoints) {
      this.lineChart.data.labels?.shift();
      this.lineChart.data.datasets?.forEach(ds => (ds.data as any[]).shift());
    }

    this.lineChart.update();
  }

  private getColor(idx: number, alpha = 1) {
    const palette = ['#2563eb', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6'];
    const color = palette[idx % palette.length];
    if (alpha === 1) return color;
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }
}