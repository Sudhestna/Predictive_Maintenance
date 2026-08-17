import json,time, traceback
import os,re
import pickle,uuid,requests
from Graph.state import AgentState
from Services.guardrail import guard
from Services.llm import structured_llm_for_guardrail,vector_store,kgraph,gpt_llm,structured_llm_for_entity,invoke_llm_with_retry,reranker
from Utils.dashboard import update_dashboard
from Utils.prompts import System_prompt_for_Guardrails,System_prompt_for_rag_system,System_prompt_for_Entity_Extraction
from langchain_core.messages import AIMessage, HumanMessage,SystemMessage
from langgraph.constants import Send
from langgraph.graph import StateGraph,START,END
from langchain_neo4j import Neo4jGraph
from langchain_core.documents import Document
from langgraph.prebuilt import ToolNode
from Tools.mcp_client import mcp_func
from langgraph.types import interrupt
from ML_prediction.detectanomaly import predict_anomaly

def guardrail_node(state: AgentState):

    try:
        print("Guardrail Node Invoked")
        print("STATE in GUARDRAIL NODE : ",state["messages"])

        validation = guard.validate_text(state["messages"][-1].content)
        update_dashboard("llm", "guardrail_calls")
        if not validation["allowed"]:
            if validation["reason"] == "PROFANITY":
                update_dashboard("guardrails", "profanity_detected")
                return {"messages": AIMessage(content="Message not allowed due to profanity")}
            if validation["reason"] == "TOXICITY":
                update_dashboard("guardrails", "toxicity_detected")
                return {"messages": AIMessage(content="Message not allowed due to toxicity")}
            return {"messages": AIMessage(content="Message not allowed")}
        else:
            print("LLM invoked in Guardrail Node")
            llm_response = invoke_llm_with_retry([
                                    SystemMessage(content=System_prompt_for_Guardrails),
                                    HumanMessage(content=validation["anonymized_text"])
                                ],structured_llm_for_guardrail)

            if llm_response is None:
                return {"messages": AIMessage(content="An error occurred please try again later !")}
            
            response = llm_response.model_dump()

        if response["violation"] == "OUT_OF_SCOPE":
            update_dashboard("guardrails", "out_of_scope")
            return {"messages": AIMessage(content=f"Please ask questions related to Manufacturing Machine issues.")}
        
        if response["violation"] != "NONE":
            update_dashboard("guardrails", "prompt_injection_or_jailbreak")
            return {"messages": AIMessage(content=f"Message not allowed since the query comes under {response['violation']}")}
        
        if response["route"] == "GREETING":
            return {"messages": AIMessage(content=str(response["response"]))}
        elif response["route"] == "IN_DOMAIN":
            return {"intent": "IN_DOMAIN"}
        else:
            return {"messages": AIMessage(content="An error occurred please try again later !")}

    except Exception as e:
        print("\n" + "=" * 100)
        print("Error in Tool Node")
        traceback.print_exc()
        print("=" * 100 + "\n")
        return {"messages": AIMessage(content="An error occurred please try again later !")}


def intent_router(state:AgentState):
    try:
        print("Intent Router Invoked")

        if isinstance(state["messages"][-1],AIMessage):
            return END

        intent = state["intent"]
        if intent == "IN_DOMAIN":
            return "IN_DOMAIN"
        else:
            return END
        
    except Exception as e:
        print("\n" + "=" * 100)
        print("Error occurred in Intent Router node : ")
        traceback.print_exc()
        print("=" * 100 + "\n")
        return END

def entity_extraction_node(state: AgentState):

    try:
        print("Entity Extraction Node Invoked")

        query = state["messages"][-1].content
        update_dashboard("llm", "entity_extraction_calls")
        print("LLM invoked in Entity Extraction Node")
        llm_response = invoke_llm_with_retry([
                                                SystemMessage(content=System_prompt_for_Entity_Extraction),
                                                HumanMessage(content=query)
                                            ],structured_llm_for_entity)

        if llm_response is None:
            return {"messages": AIMessage(content="An error occurred please try again later !")}
        
        response = llm_response.model_dump()

        machine =  None

        if response["clarification_response"] is not None:
            return {"messages": AIMessage(content=response["clarification_response"])}
        if response["machine_id"] is not None:
            machine = response["machine_id"]

        args = {
        "m_id": machine
        }

        tool_calls = [
            {
                "name": "get_sensor_data",
                "args": args,
                "id": str(uuid.uuid4())
            }
        ]

        return {"messages": AIMessage(content="", tool_calls=tool_calls),
                "machine_id": machine,
            }
    
    except Exception as e:
        print("\n" + "=" * 100)
        print("Error occurred in Entity Extraction node :")
        traceback.print_exc()
        print("=" * 100 + "\n")
        return {"messages": AIMessage(content="An error occurred please try again later !")}


def parallel_nodes_router(state: AgentState):

    try:
        print("Parallel Nodes Router Invoked")

        if isinstance(state["messages"][-1],AIMessage):
            if len(state["messages"][-1].tool_calls)>0:
                return [
                        Send("tool_node", state),
                        Send("rag_retrieval_node", state),
                        Send("graph_rag_retrieval", state),
                        ]
            else:
                return END
                

    except Exception as e:
        print("\n" + "=" * 100)
        print("Error in Parallel Nodes Router node :")
        traceback.print_exc()
        print("=" * 100 + "\n")
        return END


def rag_retrieval_node(state: AgentState):

    try:

        print("RAG Retrieval Node Invoked")
        query = state["messages"][-2].content

        
        filter={
            "machine_id": state["machine_id"]
        }

        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 10,
                "fetch_k": 20,
                "lambda_mult": 0.5
            },
            filter=filter
        )

        documents = retriever.invoke(query)
        print("RAG Retrieved successfully.")
        update_dashboard("retrieval", "vector_searches")
        return {"maintenance_logs": documents}
    
    except Exception as e:
        print("\n" + "=" * 100)
        print("Error occurred in RAG Retrieval node : ")
        traceback.print_exc()
        print("=" * 100 + "\n")
        return {"messages": AIMessage(content="An error occurred please try again later !")}


def graph_rag_retrieval(state: AgentState):

    try:
        print("Graph node invoked")
        robot_id = state["machine_id"]
        ROOT_CAUSE_CHAIN_QUERY = """
        MATCH (r:Robot {robot_id: $robot_id})-[:EXPERIENCED]->(fe:FailureEvent)
            -[:CLASSIFIED_AS]->(fm:FailureMode), (fe)-[:CAUSED_BY]->(rc:RootCause)
        RETURN fe.event_id AS event_id, fe.severity AS severity, fe.onset_ts AS onset,
            fm.name AS failure_mode, rc.name AS root_cause, fe.source_file AS source
        ORDER BY fe.onset_ts DESC LIMIT 10
        """
        DOWNTIME_COST_SUMMARY_QUERY = """
        MATCH (r:Robot {robot_id: $robot_id})-[:EXPERIENCED]->(fe:FailureEvent)
        RETURN count(fe) AS total_events, sum(fe.downtime_hrs) AS total_downtime_hrs,
            sum(fe.estimated_cost_impact_usd) AS total_cost_usd,
            avg(fe.time_to_detect_hrs) AS avg_detection_time_hrs,
            collect(DISTINCT fe.source_file)[0] AS source
        """
    
        kgraph.refresh_schema()
        def get_root_cause_chain(robot_id: str) -> str:
            """Get the failure/root-cause history for a robot_id (e.g. 'R103').
            Use when asked WHY a specific robot keeps failing."""
            rows = kgraph.query(ROOT_CAUSE_CHAIN_QUERY, {"robot_id": robot_id})
            return [Document(
                    page_content=f"Event {r['event_id']} on {robot_id}: {r['failure_mode']} "
                                f"caused by {r['root_cause']} (severity: {r['severity']}, onset: {r['onset']})",
                    metadata={"source": r["source"], "event_id": r["event_id"], "robot_id": robot_id},)
                    for r in rows]
    
        def get_downtime_cost_summary(robot_id: str) -> str:
            """Get total downtime hours, event count, and cost impact for a robot_id.
            Use for KPI/analytics questions."""
            rows = kgraph.query(DOWNTIME_COST_SUMMARY_QUERY, {"robot_id": robot_id})
            r = rows[0]
            return [Document(
                    page_content=f"{robot_id} downtime summary: {r['total_events']} events, "
                                f"{r['total_downtime_hrs']} total downtime hrs, "
                                f"${r['total_cost_usd']:.2f} total cost, "
                                f"avg detection time {r['avg_detection_time_hrs']:.2f} hrs",
                    metadata={"source": r["source"], "robot_id": robot_id},)]

        return {"graph_data": get_root_cause_chain(robot_id)}
            

    except Exception as e:
        print("\n" + "=" * 100)
        print("Error in Graph RAG Retrieval node : ")
        traceback.print_exc()
        print("=" * 100 + "\n")
        return {"messages": AIMessage(content="An error occurred please try again later !")}


async def tool_node(state: AgentState):

    try:
        print("Tool Node Invoked")
        tools = await mcp_func()
        node = ToolNode(tools)

        result = await node.ainvoke(state)

        msg = result["messages"][-1]

        if msg.status == "error":
            raise RuntimeError("Tool execution failed")

        text = msg.content if isinstance(msg.content, str) else msg.content[0]["text"]

        data = json.loads(text)
        update_dashboard("retrieval", "tool_calls")


        ###############Operational_logs##########
        if state.get("machine_id"):
            response = requests.get(
                f"http://localhost:5000/operational-logs/{state["machine_id"]}",
                timeout=10
            )
            operational_logs = response.json()
            return {"sensor_and_eq_data": data,"operationals_logs":operational_logs["logs"]}

        return {"sensor_and_eq_data": data}
    
    except Exception as e:
        print("\n" + "=" * 100)
        print("Error occurred in Tool node : ")
        traceback.print_exc()
        print("=" * 100 + "\n")
        return {"messages": AIMessage(content="An error occurred please try again later !")}


def reranking_node(state: AgentState):

    try:
        
        print("Rerank Node Invoked")
        results = reranker.compress_documents(documents=state["maintenance_logs"] , query=state["messages"][-2].content)[0:5]
        sources = []
        for result in results:
            if result.metadata["source"] not in sources:
                sources.append(result.metadata["source"])
        print("Sources in Rerank Node : ",sources)
        update_dashboard("retrieval", "citations_generated")

        return {"final_docs": (
            [result.page_content for result in results] +
            [state["graph_data"][0].page_content]
            +[state["sensor_and_eq_data"]]
            +state["operationals_logs"]
            ),
            "source": sources + [state["graph_data"][0].metadata["source"]] + ["sensor_and_eq_data"]+["operational_logs"]}

    except Exception as e:
        print("\n" + "=" * 100)
        print("Error in Rerank node : ")
        traceback.print_exc()
        print("=" * 100 + "\n")
        return {"messages": AIMessage(content="An error occurred please try again later !")}

def llm_node_for_rag(state: AgentState):

    try:

        print("LLM Node for RAG Invoked")
        sensors = None
        machine = None
        prediction = None

        if state.get("machine_id"):
            machine = state["machine_id"]
            response = requests.get(
                f"http://localhost:5000/machine-sensors/{machine}",
                timeout=10
            )
            sensors = response.json()["sensors"]

        if sensors is not None and machine is not None:
            response = predict_anomaly(machine,sensors)
            if response == -1:
                prediction = f"Anomaly detected for sensors of Machine id {machine}"
            else:
                prediction = f"No Anomaly detected for sensors of Machine id {machine}"

        ############# Anonymizing data before reaching LLM ##############

        docs,final_docs = state["final_docs"],[]
        for chunk in docs:
            if type(chunk)==str:
                mask_data = guard.mask_pii(chunk)
                final_docs.append(mask_data)
            else:
                final_docs.append(chunk)

        query = HumanMessage(content=f"""Please answer the below questions using the below chunk please be grounded never answer from your knowledge
                    Question : {state["messages"][-2].content}
                    Chunks Retrieved : {final_docs}
                    Anomaly detection by ML model for sensors : {prediction} 
                    """)
        
        print("LLM invoked in RAG Description Node")
        response = response = invoke_llm_with_retry([
                                                        SystemMessage(content=System_prompt_for_rag_system),
                                                        query
                                                    ],gpt_llm)
        update_dashboard("llm", "rag_generation_calls")
        if response is None:
            return {
                "messages": AIMessage(
                    content="An error occurred please try again later !"
                )
            }

        validation = guard.validate_text(response.content)

        if not validation["allowed"]:

            return {"messages":AIMessage(content="Please try after some time")}
    
    except Exception as e:
        print("\n" + "=" * 100)
        print("Error occurred in LLM node for RAG : ")
        traceback.print_exc()
        print("=" * 100 + "\n")
        return {"messages": AIMessage(content="An error occurred please try again later !")}

    answer = interrupt("Do you want me to generate a Report?")

    return {"messages": AIMessage(content=validation["anonymized_text"]),
            "report":answer}


def report_node(state:AgentState):
    ...


def response_node(state: AgentState):

    return state

