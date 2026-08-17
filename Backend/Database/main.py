import uuid
from fastapi import FastAPI, HTTPException
# from graph import graph
from db import ChatSession,get_db
from langchain_core.messages import AIMessage, HumanMessage
app = FastAPI()

@app.post("/createsession")
def create_session():
    session_id = str(uuid.uuid4())
    with get_db() as db:
        db.add(ChatSession( session_id=session_id, messages=[]))
    return {"session_id": session_id}


@app.get("/loadsessions")
def get_sessions():
    with get_db() as db:
        sessions = ( db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all())
        return [{"session_id": session.session_id, "updated_at": session.updated_at} for session in sessions]


@app.get("/session/{session_id}")
def get_session(session_id: str):
    with get_db() as db:
        session = (db.query(ChatSession).filter(ChatSession.session_id == session_id).first())
        if session is None:
            raise HTTPException(status_code=404,detail="Session not found")
        be_history = []
        for msg in session.messages:
            if msg["role"] == "user": be_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant": be_history.append(AIMessage(content=msg["content"]))
        config = {"configurable":{"thread_id":session_id}}
        # graph.update_state(config, {"messages":be_history})
        return {"session_id": session.session_id, "messages": session.messages}
    
    
@app.post("/chat/{session_id}")
def chat(session_id: str, query:str="Hi", interrupt_flag: bool=False):
    with get_db() as db:
        session = (db.query(ChatSession).filter(ChatSession.session_id == session_id).first())
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        query = query.strip()
        response = "Hi gowtham"
        session.messages = session.messages + [{"role": "user","content": query}, {"role": "assistant","content": response}]
        return {"answer": response}


@app.delete("/deletesession/{session_id}")
def delete_session(session_id: str):
    with get_db() as db:
        session = (
            db.query(ChatSession).filter(ChatSession.session_id == session_id).first())
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        db.delete(session)
    return {"deleted": True}