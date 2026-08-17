export interface ChatRequest {
  query?: string;
  interrupt?: boolean;
  answer?: boolean;
}

export interface ChatResponse{

    interrupt:boolean;

    response?:string;

    question?:string;

    options?:string[];

    audio_path?:string;

    pdf_path?:string;

    retrieved_chunks?:string[];

    sources?:string[];

}