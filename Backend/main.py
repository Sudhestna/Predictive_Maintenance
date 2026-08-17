import warnings
warnings.filterwarnings(
    "ignore",
    message=".*allowed_objects.*"
)
import json
from datetime import datetime
from fastapi import HTTPException
import traceback
from fastapi import FastAPI,File,UploadFile
from pydantic import BaseModel
from uuid_utils import uuid4
from Graph.builder import graph
from langchain_core.messages import HumanMessage,AIMessage
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from Services.llm import client,text_to_speech
from Rag.rag_ingestion import rag_ingestion,ingest_graph_rag,save_text_as_pdf
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
from openinference.instrumentation.openai import OpenAIInstrumentor
from typing import Optional
from langgraph.types import Command
from fastapi.responses import JSONResponse
from Database.db import get_db,ChatSession
from fastapi.staticfiles import StaticFiles
from Utils.dashboard import update_dashboard

tracer_provider = register()

LangChainInstrumentor().instrument(
    tracer_provider=tracer_provider
)
OpenAIInstrumentor().instrument(
    tracer_provider=tracer_provider
)

import truststore
truststore.inject_into_ssl()

app = FastAPI()

app.mount(
    "/audio",
    StaticFiles(directory=r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\Audio"),
    name="audio"
)

app.mount(
    "/reports",
    StaticFiles(
        directory=r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\Reports"
    ),
    name="reports"
)

class ChatApiModel(BaseModel):
    query: Optional[str] = None
    interrupt: Optional[bool] = None
    answer : Optional[bool] = None

class AudioRequest(BaseModel):
    file_path: str

class FeedbackModel(BaseModel):
    session_id: str
    feedback: str
    comment: Optional[str] = None


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

############ DB API ENDPOINTS ############

@app.get("/new-session")
def new_session():

    try:
        update_dashboard("backend", "total_requests")
        update_dashboard("backend", "active_sessions")
        session_id = str(uuid4())
        with get_db() as db:
            db.add(ChatSession( session_id=session_id, messages=[]))
        update_dashboard("backend", "successful_requests")
        return JSONResponse(
            status_code=200,
            content={
                "response": session_id
            }
        )

    except Exception as e:
        update_dashboard("backend", "failed_requests")
        print("Error occurred while creating new session:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "response": "An error occurred while creating a new session."
            }
        )


@app.get("/loadsessions")
def get_sessions():
    update_dashboard("backend", "total_requests")
    with get_db() as db:
        sessions = ( db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all())
        update_dashboard("backend", "successful_requests")
        return [{"session_id": session.session_id, "updated_at": session.updated_at} for session in sessions]

load_sessions = set()
@app.get("/session/{session_id}")
def get_session(session_id: str):
    update_dashboard("backend", "total_requests")
    with get_db() as db:
        session = (db.query(ChatSession).filter(ChatSession.session_id == session_id).first())
        if session is None:
            raise HTTPException(status_code=404,detail="Session not found")
        be_history = []
        if session_id not in load_sessions:
            for msg in session.messages:
                if msg["role"] == "user": be_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant": be_history.append(AIMessage(content=msg["content"]))
            config = {"configurable":{"thread_id":session_id}}
            graph.update_state(config, {"messages":be_history}) 
            load_sessions.add(session_id)
        update_dashboard("backend", "successful_requests")
        return {"session_id": session.session_id, "messages": session.messages, "be_messages":be_history}


@app.delete("/deletesession/{session_id}")
def delete_session(session_id: str):
    update_dashboard("backend", "total_requests")
    with get_db() as db:
        session = (
            db.query(ChatSession).filter(ChatSession.session_id == session_id).first())
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        db.delete(session)
    update_dashboard("backend", "successful_requests")
    return {"deleted": True}



################### APPLICATION API ENDPOINTS ###################

@app.post("/transcribe")
async def process_audio(file: UploadFile = File(...)):

    try:
        update_dashboard("backend", "total_requests")
        audio_path = Path(r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\Audio") / file.filename

        audio_path.parent.mkdir(parents=True, exist_ok=True)

        with open(audio_path, "wb") as f:
            f.write(await file.read())

        if audio_path.exists():

            with open(audio_path, "rb") as audio:
                transcript = client.audio.transcriptions.create(
                    model="azure/genailab-maas-whisper",
                    file=audio
                )
            print(transcript.text)

            update_dashboard("chat", "voice_queries")
            update_dashboard("backend", "successful_requests")
            return JSONResponse(
                        status_code=200,
                        content={
                            "transcript": transcript.text
                        }
                    )
        
        else:

            print("transcript", audio_path)
            update_dashboard("backend", "successful_requests")
            return JSONResponse(
                status_code=404,
                content={
                    "transcript": "Audio file not found."
                }
            )
        
    except Exception as e:
        update_dashboard("backend", "failed_requests")
        print("Error occurred while processing audio:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "transcript": "An error occurred while processing the audio."
            }
        )
    
@app.post("/chat/{session_id}")
async def main_api(session_id:str,request:ChatApiModel):

    try:
        update_dashboard("backend", "total_requests")
        config = {
            "configurable": {
            "thread_id": session_id
            }}

        if request.interrupt:

            response = await graph.ainvoke(Command(resume=request.answer),config=config)
            update_dashboard("chat", "interrupts_triggered")
        else:
            response = await graph.ainvoke(
                {"messages": [HumanMessage(content=request.query)]},
                config=config
            )
            update_dashboard("chat", "text_queries")

        print("STATE in main.py:",response["messages"])

        snapshot = graph.get_state(config)

        if snapshot.interrupts:
            return JSONResponse(
                status_code=200,
                content={
                    "interrupt": True,
                    "question": snapshot.interrupts[0].value,
                    "options":["YES","NO"]
                }
            )

        update_dashboard("backend", "text_queries")
        audio_path = await text_to_speech(response["messages"][-1].content)
        pdf_path = None
        retrieved_chunks = None
        sources = None

        if response.get("report"):
            pdf_path = "C:\\Users\\GenAIHYDSYPUSR35\\Desktop\\PNC_AI_TEAM\\Reports\\report.pdf"
            save_text_as_pdf(
                response["messages"][-1].content,
                pdf_path
            )

        if response.get("maintenance_logs"):
            retrieved_chunks = [chunk.page_content for chunk in response["maintenance_logs"]]

        if response.get("source"):
            sources = response["source"]

        with get_db() as db:
            session = (db.query(ChatSession).filter(ChatSession.session_id == session_id).first())
            if session is None:
                raise HTTPException(status_code=404, detail="Session not found")
            
            if request.query:
                session.messages = session.messages + [{"role": "user","content": request.query}, {"role": "assistant","content": response["messages"][-1].content}]
            else:
                session.messages = session.messages + [{"role": "user","content":response["messages"][-3].content}, {"role": "assistant","content": response["messages"][-1].content}]
            
        update_dashboard("backend", "successful_requests")
        update_dashboard("chat", "total_queries")
        return JSONResponse(
                        status_code=200,
                        content={
                            "interrupt": False,
                            "response": response["messages"][-1].content,
                            "audio_path": audio_path,
                            "pdf_path": pdf_path,
                            "retrieved_chunks": retrieved_chunks,
                            "sources": sources
                        })
    
    except Exception as e:
        update_dashboard("backend", "failed_requests")
        print("Error occurred while processing chat request:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "response": "An error occurred while processing the chat request."
            }
        )

@app.post("/upload-document")
def upload_document(file: UploadFile = File(...)):

    try:
        update_dashboard("backend", "total_requests")
        file_path = Path("C:\\Users\\GenAIHYDSYPUSR35\\Desktop\\PNC_AI_TEAM\\Rag\\Rag_Documents\\" + file.filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        extension = "." + file.filename.rsplit(".", 1)[-1].lower()

        if extension==".csv":
            if ingest_graph_rag(file_path)=="success":
                update_dashboard("backend", "successful_requests")
                update_dashboard("documents", "documents_uploaded")
                return JSONResponse(
                    status_code=200,
                    content={
                        "response": f"Document {file.filename} uploaded successfully."
                    }
                )
            else:
                update_dashboard("backend", "failed_requests")
                return JSONResponse(
                    status_code=400,
                    content={
                        "response": f"Document {file.filename} upload failed."
                    }
                )
            
        elif extension==".pdf":
            if rag_ingestion(file_path)=="success":
                update_dashboard("backend", "successful_requests")
                update_dashboard("documents", "documents_uploaded")
                return JSONResponse(
                    status_code=200,
                    content={
                        "response": f"Document {file.filename} uploaded successfully."
                    }
                )
            
            else:
                update_dashboard("backend", "failed_requests")
                return JSONResponse(
                    status_code=400,
                    content={
                        "response": f"Document {file.filename} upload failed."
                    }
                )
        
        return JSONResponse(
            status_code=400,
            content={
                "response": f"Document {file.filename} upload failed."
            }
        )
    
    except Exception as e:

        update_dashboard("backend", "failed_requests")
        print("Error occurred while uploading document:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "response": "An error occurred while uploading the document."
            }
        )




@app.post("/feedback")
async def submit_feedback(request: FeedbackModel):

    update_dashboard("backend", "total_requests")
    feedback_entry = {
        "session_id": request.session_id,
        "feedback": request.feedback,
        "comment": request.comment,
        "timestamp": datetime.now().isoformat()
    }

    try:

        FEEDBACK_FILE = Path(r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\Utils\feedback.json")
        if FEEDBACK_FILE.exists() and FEEDBACK_FILE.stat().st_size > 0:

            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)

        else:

            feedbacks = []

        feedbacks.append(feedback_entry)

        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(
                feedbacks,
                f,
                indent=4,
                ensure_ascii=False
            )
        update_dashboard("backend", "successful_requests")
        return JSONResponse(
            status_code=200,
            content={
            "success": True,
            "message": "Feedback submitted successfully."
        })

    except Exception as e:
        update_dashboard("backend", "failed_requests")
        print("Error occurred while submitting feedback:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An error occurred while submitting feedback."
            }
        )

@app.get("/dashboard")
def get_dashboard():
    try:

        DASHBOARD_FILE = Path(r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\Utils\dashboard_data.json")

        with open(DASHBOARD_FILE, "r") as f:
            dashboard_data = json.load(f)
        update_dashboard("backend", "successful_requests")
        return JSONResponse(
            status_code=200,
            content={"dashboard_data": dashboard_data}
        )
    
    except Exception as e:
        update_dashboard("backend", "failed_requests")
        print("Error occurred while fetching dashboard data:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An error occurred while fetching dashboard data."
            }
        )

@app.get("/health")
def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status": True
        }
    )


ALERTS_FILE = r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\ML_prediction\alerts.json"

@app.get("/fetch-alerts")
def fetch_alerts():

    try:

        with open(ALERTS_FILE, "r") as f:
            alerts = json.load(f)

        if not alerts:
            return JSONResponse(
                status_code=200,
                content={"alerts":[]}
            )

        unassigned_alerts = [
            alert for alert in alerts
            if not alert.get("assigned", False)
        ]

        return JSONResponse(
            status_code=200,
            content={"alerts":unassigned_alerts}
        )

    except json.JSONDecodeError:
        # File exists but is empty
        return JSONResponse(
            status_code=200,
            content=[]
        )

    except FileNotFoundError:
        # alerts.json doesn't exist yet
        return JSONResponse(
            status_code=200,
            content=[]
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={"message": str(e)}
        )


@app.post("/assign-alert/{machine_id}")
def assign_alert(machine_id):

    try:

        with open(ALERTS_FILE, "r") as f:
            alerts = json.load(f)

        updated = False

        for alert in alerts:
            if (
                alert["machine_id"] == machine_id
                and alert["assigned"] is False
            ):
                alert["assigned"] = True
                updated = True

        with open(ALERTS_FILE, "w") as f:
            json.dump(alerts, f, indent=4)

        if not updated:
            return JSONResponse(
                status_code=404,
                content={"message": "No unassigned alerts found for the given machine."}
            )

        return JSONResponse(
            status_code=200,
            content={"message": "Alert assigned successfully."}
        )

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={"message": str(e)}
        )