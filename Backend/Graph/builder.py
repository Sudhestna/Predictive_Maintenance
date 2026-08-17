from langgraph.graph import StateGraph,START,END
from Graph.graph_nodes import parallel_nodes_router,tool_node,guardrail_node,intent_router,graph_rag_retrieval,rag_retrieval_node,llm_node_for_rag,reranking_node,entity_extraction_node
from Graph.state import AgentState
from langgraph.checkpoint.memory import InMemorySaver



builder = StateGraph(AgentState)

builder.add_node("guardrail", guardrail_node)
builder.add_node("reranking_node", reranking_node)
builder.add_node("rag_retrieval_node", rag_retrieval_node)
builder.add_node("graph_rag_retrieval", graph_rag_retrieval)
builder.add_node("llm_node_for_rag", llm_node_for_rag)
builder.add_node("entity_extraction_node", entity_extraction_node)
builder.add_node("tool_node", tool_node)

builder.add_edge(START, "guardrail")

builder.add_conditional_edges("guardrail",
                              intent_router,
                              {END:END,
                               "IN_DOMAIN":"entity_extraction_node"}
                               )

builder.add_conditional_edges("entity_extraction_node",parallel_nodes_router)

builder.add_edge(
    ["tool_node", "rag_retrieval_node", "graph_rag_retrieval"],
    "reranking_node",
)


builder.add_edge("reranking_node", "llm_node_for_rag")

builder.add_edge("llm_node_for_rag", END)

graph = builder.compile(checkpointer=InMemorySaver())