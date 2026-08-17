import { Component, Output, EventEmitter, Input, ChangeDetectorRef, NgZone, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-chat-input',
  imports: [FormsModule],
  templateUrl: './chat-input.html',
  styleUrl: './chat-input.css',
  standalone: true,
})
export class ChatInput {
  message = "";
  isLoading = false;
  private mediaRecorder?: MediaRecorder;

  private mediaStream?: MediaStream;

  private audioChunks: Blob[] = [];

  recording = false;

  private cdr = inject(ChangeDetectorRef);

  private zone = inject(NgZone);



  @Input()
  disabled=false;

  @Output()
  messageSent = new EventEmitter<string>();

  @Output()
  audioRecorded = new EventEmitter<File>();

  constructor() {
      console.log("CHAT INPUT COMPONENT LOADED");
  }

  sendMessage() {

        const text = this.message.trim();

        if (!text) {
            return;
        }

        this.messageSent.emit(text);

        this.message = "";

    }

  setMessage(text: string){

      this.zone.run(() => {

          this.message = text;

          this.cdr.detectChanges();

      });

  }

  async toggleRecording() {

    console.log("Component instance:", this);
      console.log("before:", this.recording);
      if (!this.recording) {

          this.mediaStream = await navigator.mediaDevices.getUserMedia({
              audio: true
          });

          this.audioChunks = [];

          this.mediaRecorder = new MediaRecorder(this.mediaStream);

          this.mediaRecorder.ondataavailable = (event) => {

              if (event.data.size > 0) {

                  this.audioChunks.push(event.data);

              }

          };

          this.mediaRecorder.onstop = () => {

              const blob = new Blob(
                  this.audioChunks,
                  {
                      type: "audio/webm"
                  }
              );

              const file = new File(
                  [blob],
                  "recording.webm",
                  {
                      type: "audio/webm"
                  }
              );

              this.audioRecorded.emit(file);

              this.mediaStream?.getTracks().forEach(track => track.stop());

              this.zone.run(() => {

                  this.recording = false;

                  this.cdr.detectChanges();

              });

          };

          this.mediaRecorder.start(250);

          this.zone.run(() => {

                this.recording = true;
                this.cdr.markForCheck();
                this.cdr.detectChanges();

          });

          await new Promise(resolve => setTimeout(resolve, 100));

          console.log("Recording Started");

      }
      else {

          console.log("Stopping...");

          this.mediaRecorder?.stop();

      }

  }
}
