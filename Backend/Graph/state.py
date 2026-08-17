from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str
    machine_id : str
    graph_data : list
    maintenance_logs : list[Document]
    operationals_logs:list
    sensor_and_eq_data : dict
    final_docs : list
    source : list[str]
    report : bool