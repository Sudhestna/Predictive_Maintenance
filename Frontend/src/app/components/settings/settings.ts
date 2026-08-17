import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [FormsModule],   // 👈 add this
  templateUrl: './settings.html',
  styleUrls: ['./settings.css']
})
export class Settings {
  title = 'Application Settings';
  darkMode = false;
  notifications = true;

  toggleDarkMode() { this.darkMode = !this.darkMode; }
  toggleNotifications() { this.notifications = !this.notifications; }
}
