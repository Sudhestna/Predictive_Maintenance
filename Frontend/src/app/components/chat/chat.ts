import { Component, inject, ChangeDetectorRef, ElementRef, ViewChild, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ChatInput } from '../chat-input/chat-input';
import { MessageComponent } from '../message/message';

import { ChatMessage } from '../../models/chat-message';
import { ChatResponse } from '../../models/chat-api';

import { SessionService } from '../../services/session';
import { ApiService } from '../../services/api';

import { PreviewDrawer } from '../preview-drawer/preview-drawer';
import { InterruptCard } from '../interrupt-card/interrupt-card';
import { ToastService } from '../../services/toast';

@Component({
  selector: 'app-chat',
  imports: [FormsModule, ChatInput, MessageComponent, PreviewDrawer, InterruptCard],
  templateUrl: './chat.html',
  styleUrl: './chat.css',
})
export class Chat implements OnInit {

  drawerOpen = false;

  drawerTitle = "";

  drawerChunks: string[] = [];

  drawerPdf = "";

  interruptOptions: string[] = [];

  selectedInterrupt: boolean | null = null;

  interruptWaiting = false;

  interruptActive = false;

  interruptThinking = false;

  interruptQuestion = "";

  showScrollButton = false;

  unreadMessages = 0;

  sessionId = "";

  private autoScroll = true;

  private toast = inject(ToastService);

  suggestedPrompts = [

      {
          icon: "description",
          title: "Summarize XML",
          prompt: "Summarize the uploaded XML report."
      },

      {
          icon: "manufacturing",
          title: "Root Cause",
          prompt: "Find the root cause of the machine failure."
      },

      {
          icon: "analytics",
          title: "Generate Report",
          prompt: "Generate a detailed maintenance report."
      },

      {
          icon: "warning",
          title: "Risk Analysis",
          prompt: "Analyze the operational risks."
      }

  ];


  private api = inject(ApiService);

  private session = inject(SessionService);

  private cdr = inject(ChangeDetectorRef);

  ngOnInit() {

        this.session.sessionId$.subscribe({

            next: (sessionId: string) => {

                if (!sessionId) {
                    return;
                }

                this.sessionId = sessionId;

                // Reset interrupt state when session changes
                this.interruptActive = false;
                this.interruptWaiting = false;
                this.interruptThinking = false;
                this.selectedInterrupt = null;
                this.interruptQuestion = '';
                this.interruptOptions = [];

                this.loadSession();

            }

        });

    }


  @ViewChild("messagesContainer")
  messagesContainer!: ElementRef<HTMLDivElement>;

  @ViewChild("bottomAnchor")
  bottomAnchor!: ElementRef<HTMLDivElement>;

  @ViewChild(ChatInput)
  chatInput!: ChatInput;

  messages: ChatMessage[] = [];

  receiveMessage(text: string) {

        const query = text.trim();

        if (!query || !this.sessionId) {
            return;
        }

        // Normal message
        this.messages.push({
            id: Date.now(),
            response: query,
            sender: 'user',
            loading: false,
            streaming: false,
            timestamp: new Date()
        });

        this.cdr.detectChanges();
        this.scrollToBottom();

        this.api.sendMessage(
            this.sessionId,
            {
                query: query
            }
        ).subscribe({

            next: (response: ChatResponse) => {

                console.log('CHAT RESPONSE:', response);
                console.log('INTERRUPT:', response.interrupt);
                console.log('QUESTION:', response.question);
                console.log('OPTIONS:', response.options);

                if (response.interrupt === true) {

                    this.interruptActive = true;
                    this.interruptWaiting = false;
                    this.interruptThinking = false;

                    this.selectedInterrupt = null;

                    this.interruptQuestion =
                        response.question ?? '';

                    this.interruptOptions =
                        response.options ?? ['YES', 'NO'];

                    this.cdr.detectChanges();

                    this.scrollToBottom(true);

                    return;
                }

                this.interruptActive = false;
                this.interruptQuestion = '';
                this.interruptOptions = [];

                this.messages.forEach(message => {
                    if (message.sender === 'assistant') {
                        message.isLatest = false;
                    }
                });

                const assistantMessage: ChatMessage = {
                    id: Date.now() + 1,
                    response: '',
                    sender: 'assistant',
                    loading: true,
                    streaming: false,
                    timestamp: new Date(),

                    // These belong ONLY to this backend response.
                    chunks: response.retrieved_chunks?.length
                        ? response.retrieved_chunks
                        : [],

                    sources: response.sources?.length
                        ? response.sources
                        : [],

                    filePath: response.pdf_path && response.pdf_path.trim() !== ""
                        ? response.pdf_path
                        : "",

                    audioPath: response.audio_path ?? "",

                    isLatest: true
                };

                this.messages.push(assistantMessage);

                this.cdr.detectChanges();
                this.scrollToBottom();

                this.streamResponse(
                    assistantMessage,
                    response.response ?? ''
                );
            },

            error: (error) => {

                console.error('Chat request failed:', error);

                this.toast.show(
                    'Unable to connect to backend.',
                    'error'
                );

                this.cdr.detectChanges();
            }
        });
    }

  transcribeAudio(file: File){

      this.api.transcribe(file).subscribe({

          next:(response)=>{

              this.chatInput.setMessage(
                  response.transcript
              );

              this.cdr.detectChanges();

          },

          error:()=>{

              console.error(

                  "Unable to transcribe audio."

              );

          }

      });

  }

  interruptSelected(answer: boolean) {

        if (this.interruptWaiting) {
            return;
        }

        console.log('Interrupt selected:', answer);

        this.selectedInterrupt = answer;
        this.interruptWaiting = true;
        this.interruptThinking = true;

        this.messages.push({
            id: Date.now(),
            response: answer ? 'Yes' : 'No',
            sender: 'user',
            loading: false,
            streaming: false,
            timestamp: new Date()
        });

        this.cdr.detectChanges();
        this.scrollToBottom();

        const assistantMessage: ChatMessage = {
            id: Date.now() + 1,
            response: '',
            sender: 'assistant',
            loading: false,
            streaming: false,
            timestamp: new Date(),

            chunks: [],
            filePath: '',
            audioPath: '',
            sources: [],

            isLatest: true
        };

        this.api.sendMessage(
            this.sessionId,
            {
                interrupt: true,
                answer: answer
            }
        ).subscribe({

            next: (response: ChatResponse) => {

                console.log('INTERRUPT RESPONSE:', response);

                this.interruptWaiting = false;
                this.interruptThinking = false;
                this.selectedInterrupt = null;

                /*
                * Backend can potentially ask another interrupt.
                */
                if (response.interrupt === true) {

                    this.interruptActive = true;

                    this.interruptQuestion =
                        response.question ?? '';

                    this.interruptOptions =
                        response.options ?? ['YES', 'NO'];

                    this.cdr.detectChanges();

                    this.scrollToBottom(true);

                    return;
                }

                /*
                * Interrupt is now completed.
                */
                this.interruptActive = false;
                this.interruptQuestion = '';
                this.interruptOptions = [];

                this.messages.forEach(message => {
                    if (message.sender === 'assistant') {
                        message.isLatest = false;
                    }
                });

                assistantMessage.chunks =
                    response.retrieved_chunks?.length
                        ? response.retrieved_chunks
                        : [];

                assistantMessage.filePath =
                    response.pdf_path && response.pdf_path.trim() !== ""
                        ? response.pdf_path
                        : "";

                assistantMessage.audioPath =
                    response.audio_path ?? "";

                assistantMessage.sources =
                    response.sources?.length
                        ? response.sources
                        : [];

                assistantMessage.isLatest = true;

                this.messages.push(assistantMessage);

                this.cdr.detectChanges();
                this.scrollToBottom();

                this.streamResponse(
                    assistantMessage,
                    response.response ?? ''
                );
            },

            error: (error) => {

                console.error(
                    'Interrupt request failed:',
                    error
                );

                this.interruptWaiting = false;
                this.interruptThinking = false;
                this.selectedInterrupt = null;

                this.toast.show(
                    'Unable to process your response.',
                    'error'
                );

                this.cdr.detectChanges();
            }
        });
    }

  private streamResponse(
      message: ChatMessage,
      fullResponse: string
  ) {

      message.loading = false;
      message.streaming = true;
      message.response = "";

      if (!this.isNearBottom()) {

          this.showScrollButton = true;

          this.autoScroll = false;

          this.unreadMessages++;

      }

      const words = fullResponse.split(" ");

      let index = 0;

      const timer = setInterval(() => {

          if (index >= words.length) {

              clearInterval(timer);

              message.streaming = false;

              message.timestamp = new Date();

              this.cdr.detectChanges();

              return;
          }

          message.response += (index === 0 ? "" : " ") + words[index];

          if (!this.isNearBottom()) {

              this.showScrollButton = true;

              this.autoScroll = false;

              this.unreadMessages = 1;

          }

          this.cdr.detectChanges();

          this.scrollToBottom();

          index++;

      }, 80);

  }


  private scrollToBottom(force = false) {

      if (!this.autoScroll && !force) {

          return;

      }

      setTimeout(() => {

          this.bottomAnchor.nativeElement.scrollIntoView({

              behavior: "smooth",

              block: "end"

          });

      });

  }

  scrollToLatest() {

      this.autoScroll = true;

      this.showScrollButton = false;

      this.unreadMessages = 0;

      this.scrollToBottom(true);

  }

  onMessagesScroll() {

      const container = this.messagesContainer.nativeElement;

      const distance =

          container.scrollHeight -

          container.scrollTop -

          container.clientHeight;

      this.showScrollButton = distance > 120;

      this.autoScroll = !this.showScrollButton;

      if (!this.showScrollButton) {

          this.unreadMessages = 0;

      }

  }

  openChunks(chunks: string[]) {

      this.drawerTitle = "Retrieved Context";

      this.drawerChunks = chunks;

      this.drawerPdf = "";

      this.drawerOpen = true;

  }

  openPdf(path: string) {

        console.log("PDF path received:", path);

        let pdfUrl = path;

        // Backend may return a Windows filesystem path.
        // Convert it to the URL exposed by FastAPI's /reports mount.
        if (path.includes("\\Reports\\")) {

            pdfUrl = "/reports/" +
                path.split("\\Reports\\").pop();

        }
        // Backend may already return /reports/report.pdf
        else if (path.startsWith("/")) {

            pdfUrl = path;

        }

        // If the path is just report.pdf
        else if (!path.startsWith("http")) {

            pdfUrl = "/reports/" + path;

        }

        const fullUrl =
            `http://localhost:8000${pdfUrl}?t=${Date.now()}`;

        console.log("Final PDF URL:", fullUrl);

        this.drawerTitle = "Generated Report";
        this.drawerChunks = [];
        this.drawerPdf = fullUrl;
        this.drawerOpen = true;
    }

  closeDrawer() {

      this.drawerOpen = false;

  }

  loadSession(){

      this.api.loadSession(this.sessionId).subscribe({

          next:(response)=>{

              this.messages = response.messages.map((message:any,index:number)=>({

                  id:index,

                  sender:message.role,

                  response:message.content,

                  loading:false,

                  streaming:false,

                  timestamp:new Date(),

                  chunks:[],

                  filePath:"",

                  audioPath:"",

                  sources:[],

                  isLatest:false

              }));

              this.cdr.detectChanges();

              this.scrollToBottom(true);

          },

          error:()=>{

              console.error(

                  "Unable to load session."

              );

          }

      });

  }

  showWelcome(): boolean {

      return !this.messages.some(

          message => message.sender === "user"

      );

  }

  sendSuggestedPrompt(prompt: string){

      this.receiveMessage(prompt);

      setTimeout(() => {

          this.scrollToBottom(true);

      }, 50);

  }

  private isNearBottom(): boolean {

      const container = this.messagesContainer.nativeElement;

      const distance =

          container.scrollHeight -

          container.scrollTop -

          container.clientHeight;

      return distance < 120;

  }

  submitFeedback(

      message: ChatMessage,

      event: {

          feedback: string,

          comment?: string

      }

  ){

      this.api.submitFeedback(

          this.sessionId,

          event.feedback,

          event.comment

      ).subscribe({

          next: () => {

              message.feedbackSubmitted = true;

              message.feedbackOpen = false;

              this.toast.show(

                  "Thanks for your feedback!",

                  "success"

              );

          },

          error: () => {

              this.toast.show(

                  "Unable to submit feedback.",

                  "error"

              );

          }

      });

  }

}
