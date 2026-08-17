from dotenv import load_dotenv
from datasets import Dataset
from dashboard import generate_dashboard
import os
import httpx

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from ragas import evaluate

from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

from sample_data import (
    questions,
    answers,
    ground_truths,
    contexts,
)
import truststore
truststore.inject_into_ssl()

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "text-embedding-3-small"
)



judge_llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=OPENAI_API_KEY,
    base_url=BASE_URL,
    http_client=httpx.Client(
    verify=False,
    timeout=60.0,
),
    temperature=0,
)


embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=OPENAI_API_KEY,
    base_url=BASE_URL,
    http_client=httpx.Client(
    verify=False,
    timeout=60.0,
)
)

dataset = Dataset.from_dict(
    {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }
)

result = evaluate(
    dataset=dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ],
    llm=judge_llm,
    embeddings=embeddings
)
for attr in dir(result):
    if not attr.startswith("_"):
        print(attr, ":", getattr(result, attr))
generate_dashboard(result)
