import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-interrupt-card',
  imports: [],
  templateUrl: './interrupt-card.html',
  styleUrl: './interrupt-card.css'
})
export class InterruptCard {

  @Input() question = "";

  @Input() options: string[] = [];

  @Input() selected: boolean | null = null;

  @Input() disabled = false;

  @Input() thinking = false;

  @Output() optionSelected = new EventEmitter<boolean>();


  choose(value: boolean){

    if(this.disabled){
      return;
    }

    this.optionSelected.emit(value);

  }

}