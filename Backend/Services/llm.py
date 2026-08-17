import joblib
import asyncio, edge_tts
import time,re
import traceback
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
import httpx
from typing import Literal
from paddleocr import PaddleOCR
from pydantic import BaseModel, Field
from openai import OpenAI
from langchain_chroma import Chroma
from Utils.dashboard import update_dashboard
from Utils.models import JudgeResult,ExtractedEntities
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph
from langchain_community.document_compressors import JinaRerank
from langchain_core.documents import Document

from uuid import uuid4
from pathlib import Path


import truststore
truststore.inject_into_ssl()

try:

    gpt_llm = ChatOpenAI(
        model = "",
        api_key = "",
        base_url = "",
        http_client=httpx.Client(verify=False,timeout=60.0),
        temperature=0
    )

    client = OpenAI(
        api_key="",
        base_url="",
        http_client=httpx.Client(verify=False, timeout=60.0),
        timeout=60.0
    )

    embedding_model = OpenAIEmbeddings(
        api_key="",
        base_url="",
        model = "",
        http_client=httpx.Client(verify=False, timeout=60.0),
        timeout=60.0
    )

    ocr = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    )

    def clean_markdown(text: str) -> str:
            text = re.sub(r"```[\s\S]*?```", "", text)
            text = re.sub(r"`([^`]*)`", r"\1", text)
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
            text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
            text = re.sub(r"(\*\*|\*|__|_)", "", text)
            text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
            text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
            text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
            text = re.sub(r"\n{2,}", "\n", text)
            text = re.sub(r"[ \t]+", " ", text)
            return text.strip()
    
    AUDIO_DIR = Path(r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\Audio")

    async def text_to_speech(text: str):

        text = clean_markdown(text=text)
        
        filename = f"{uuid4()}.mp3"

        audio_path = AUDIO_DIR / filename

        conn = edge_tts.Communicate(
            text=text,
            voice="en-US-GuyNeural"  
        )
        
        await conn.save(str(audio_path))
        print(audio_path)
        print(audio_path.exists())
        return f"/audio/{filename}"

    vector_store = Chroma(
            collection_name="knowledge_base",
            embedding_function=embedding_model,
            persist_directory="chroma_db"
        )

    structured_llm_for_guardrail = gpt_llm.with_structured_output(JudgeResult)

    structured_llm_for_entity = gpt_llm.with_structured_output(ExtractedEntities)

    kgraph = Neo4jGraph(url="bolt://127.0.0.1:7687", username="neo4j", password="Hanuman@123", database="graph-db",)
    transformer = LLMGraphTransformer(llm=gpt_llm, ignore_tool_usage=True)
    print("Neo4j and transformer initialized")

    reranker = JinaRerank(
        jina_api_key="",
        model="")

    ######### ML Models ############


    def invoke_llm_with_retry( messages,llm,retries=3, delay=1):

        for attempt in range(retries):

            try:

                if llm is not None:
                    return llm.invoke(messages)

            except Exception:
                update_dashboard("llm", "retry_count")
                print("\n" + "=" * 100)
                print(f"LLM Invocation Failed (Attempt {attempt + 1}/{retries})")
                traceback.print_exc()
                print("=" * 100 + "\n")

                if attempt < retries - 1:
                    time.sleep(delay)

        return None

except Exception as e:

    print("Error occurred while initializing LLM objects:", repr(e))
    traceback.print_exc()



