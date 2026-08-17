import { Component } from '@angular/core';
import { Sidebar } from '../sidebar/sidebar';
import { Chat } from '../chat/chat';

@Component({
  selector: 'app-workspace',
  imports: [Sidebar, Chat],
  templateUrl: './workspace.html',
  styleUrl: './workspace.css',
})
export class Workspace {}
