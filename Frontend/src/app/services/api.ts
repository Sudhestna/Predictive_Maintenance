import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';

import { ChatRequest, ChatResponse } from '../models/chat-api';
import { Session } from '../models/session';
import { FeedbackRequest } from '../models/feedback';

@Injectable({
  providedIn: 'root',
})
export class ApiService {

  private http = inject(HttpClient);

  private baseUrl = "http://localhost:8000";

  // -------------------------
  // Session APIs
  // -------------------------

  createSession(){

      return this.http.get<{

          response:string

      }>(

          this.baseUrl + "/new-session",

          {}

      );

  }

  loadSessions() {

      return this.http.get<Session[]>(

          this.baseUrl + "/loadsessions"

      );

  }

  loadSession(sessionId: string) {

    return this.http.get<any>(
      `${this.baseUrl}/session/${sessionId}`
    );

  }

  deleteSession(sessionId: string){

      return this.http.delete(

          `${this.baseUrl}/deletesession/${sessionId}`

      );

  }

  

  // -------------------------
  // Chat
  // -------------------------

  sendMessage(
    sessionId: string,
    request: ChatRequest
  ) {

    return this.http.post<ChatResponse>(
      `${this.baseUrl}/chat/${sessionId}`,
      request
    );

  }

  // -------------------------
  // Upload
  // -------------------------

  uploadDocument(file: File) {

    const formData = new FormData();

    formData.append(
      "file",
      file
    );

    return this.http.post(
      `${this.baseUrl}/upload-document`,
      formData
    );

  }

  transcribe(file: File){

      const formData = new FormData();

      formData.append(
          "file",
          file
      );

      return this.http.post<{

          transcript:string

      }>(

          `${this.baseUrl}/transcribe`,

          formData

      );

  }

  submitFeedback(

      sessionId: string,

      feedback: string,

      comment?: string

  ){

      return this.http.post(

          `${this.baseUrl}/feedback`,

          {

              session_id: sessionId,

              feedback,

              comment

          }

      );

  }

  health(){

      return this.http.get<{

          status:boolean

      }>(

          `${this.baseUrl}/health`

      );

  }
  

}