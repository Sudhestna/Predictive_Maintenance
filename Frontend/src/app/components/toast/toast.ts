import { Component, inject } from '@angular/core';
import { ToastService } from '../../services/toast';
import { AsyncPipe } from '@angular/common';

@Component({

    selector:'app-toast',

    imports:[AsyncPipe],

    templateUrl:'./toast.html',

    styleUrl:'./toast.css'

})

export class ToastComponent{

    toastService = inject(ToastService);

}