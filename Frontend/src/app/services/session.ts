import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class SessionService {

    private sessionIdSource = new BehaviorSubject<string>("");

    sessionId$ = this.sessionIdSource.asObservable();

    currentSessionId = "";

    setSession(sessionId: string){

        this.currentSessionId = sessionId;

        this.sessionIdSource.next(sessionId);

    }

}