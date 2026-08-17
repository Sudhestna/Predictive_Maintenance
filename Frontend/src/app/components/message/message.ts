import { Component, EventEmitter, Input, Output, inject, DoCheck, ViewEncapsulation } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ChatMessage } from '../../models/chat-message';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';
import hljs from 'highlight.js';
import { OnChanges, SimpleChanges } from '@angular/core';
import { ToastService } from '../../services/toast';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-message',
  imports: [FormsModule, DatePipe],
  templateUrl: './message.html',
  styleUrl: './message.css',
  encapsulation: ViewEncapsulation.None
})
export class MessageComponent implements DoCheck {

  private previousResponse = "";

  private toast = inject(ToastService);

  private static currentAudio: HTMLAudioElement | null = null;

  isPlaying = false;

  @Input({ required: true})
  message!: ChatMessage;

  @Output()
  showChunks = new EventEmitter<string[]>();

  @Output()
  showPdf = new EventEmitter<string>();

  @Output()
  feedback = new EventEmitter<{
      feedback:string,
      comment?:string
  }>();

  private sanitizer = inject(DomSanitizer);

  renderedResponse: SafeHtml = "";


  copyMessage(){

      navigator.clipboard.writeText(this.message.response);

      this.toast.show(

          "Copied to clipboard",

          "success"

      );

  }

  openChunks(){

      this.showChunks.emit(this.message.chunks ?? []);

  }

  openPdf(){

      this.showPdf.emit(this.message.filePath ?? "");

  }

  private renderMarkdown() {

      marked.setOptions({

          gfm: true,

          breaks: true

      });

      marked.use({

          renderer: {

              code(token) {

                  const language = hljs.getLanguage(token.lang || "")

                      ? token.lang!

                      : "plaintext";

                  const highlighted = hljs.highlight(

                      token.text,

                      {

                          language

                      }

                  ).value;

                  return `

  <pre><code class="hljs ${language}">

  ${highlighted}

  </code></pre>

  `;

              }

          }

      });

      const html = marked.parse(

          this.message.response || ""

      ) as string;

      this.renderedResponse =

          this.sanitizer.bypassSecurityTrustHtml(html);

  }


  ngDoCheck() {

      if (this.previousResponse !== this.message.response) {

          this.previousResponse = this.message.response;

          this.renderMarkdown();

      }

  }

  playAudio(path: string) {

      if (!path) {
          return;
      }

      // Same audio is playing -> Pause
      if (
          MessageComponent.currentAudio &&
          this.isPlaying
      ) {

          MessageComponent.currentAudio.pause();

          MessageComponent.currentAudio.currentTime = 0;

          MessageComponent.currentAudio = null;

          this.isPlaying = false;

          return;

      }

      // Stop previous audio
      if (MessageComponent.currentAudio) {

          MessageComponent.currentAudio.pause();

          MessageComponent.currentAudio.currentTime = 0;

      }

      const audio = new Audio(
          "http://localhost:8000" + path
      );

      MessageComponent.currentAudio = audio;

      this.isPlaying = true;

      audio.play();

      audio.onended = () => {

          this.isPlaying = false;

          MessageComponent.currentAudio = null;

      };

  }

  feedbackComment = "";

  feedbackOptions = [
    'Hallucination',
    'Incorrect answer',
    'Missing information',
    'Poor explanation',
    'Others'
    ];

    selectedFeedback = "";

  get showFeedbackBox(){
      return this.message.feedbackOpen ?? false;
  }


  positiveFeedback() {

    this.feedback.emit({
        feedback: "helpful"
    });

  }

  negativeFeedback() {

        this.message.feedbackOpen = true;

        this.selectedFeedback = "";
        this.feedbackComment = "";

    }

    selectFeedbackOption(option: string) {

    this.selectedFeedback = option;

    }

  submitNegativeFeedback() {

  if (!this.selectedFeedback) {
    return;
  }

  const comment = this.feedbackComment.trim();

  // "Others" requires a comment.
  if (this.selectedFeedback === "Others" && !comment) {
    return;
  }

  this.feedback.emit({
    feedback: this.selectedFeedback,
    comment: comment || undefined
  });

  this.message.feedbackOpen = false;
  this.selectedFeedback = "";
  this.feedbackComment = "";

}

}
