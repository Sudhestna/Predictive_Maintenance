import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Toast } from '../models/toast';

@Injectable({
    providedIn: 'root'
})
export class ToastService {

    private toasts = new BehaviorSubject<Toast[]>([]);

    toasts$ = this.toasts.asObservable();

    show(

        message: string,

        type: 'success' | 'error' | 'info' = 'info'

    ){

        const toast: Toast = {

            id: Date.now(),

            message,

            type

        };

        const list = [...this.toasts.value, toast];

        this.toasts.next(list);

        setTimeout(()=>{

            this.remove(toast.id);

        },3000);

    }

    remove(id:number){

        this.toasts.next(

            this.toasts.value.filter(

                toast=>toast.id!==id

            )

        );

    }

}