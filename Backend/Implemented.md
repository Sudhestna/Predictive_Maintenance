
## **Features In Application**

### **Backend**
1. FastAPI
2. Structured HTTP Responses
3. Pydantic Models
4. Exception Handling
5. Retry Logic for LLM Calls
6. Health Check Endpoint
7. Persistent Memory (SQLite Checkpointer)
8. Multiple Chat Sessions
9. JSON Feedback Storage
10. Logging (Planned)
### **AI / LLM**
1. LangGraph
2. MCP Server Integration
3. Tool Calling
4. Human-in-the-Loop (Interrupt & Resume)
5. Structured LLM Outputs (Pydantic)
6. Prompt-based Guardrails
7. Entity Extraction
8. Intent Classification
### **Retrieval**
1. ChromaDB
2. Graph RAG (Neo4j)
3. Hybrid RAG
4. ReRanker (Jina)
4. Structure-aware Chunking
5. OCR-based Document Ingestion
6. Metadata Filtering
7. Citations (Planned)
### **Responsible AI**
1. Prompt Injection Detection
2. Jailbreak Detection
3. Domain Restriction
4. PII Detection & Masking (Presidio)
5. Toxicity Detection (Detoxify)
6. Profanity Filtering
### **Frontend**
1. Angular
2. Voice Input (Whisper-speech-to-text)
3. Voice Output (edge-text-to-speech)
4. Human-in-the-Loop Dialog
5. PDF Report Download
6. User Feedback Collection
### **Evaluation & Monitoring**
1. Phoenix Observability
2. RAGAS Evaluation
### **Document Processing**
1. PDF Upload
2. OCR Extraction
3. XML Log Processing
### **Reports**
1. AI-generated PDF Reports





### **Machines**

1. **Robot R101** – Wing Positioning & Fixturing Robot
2. **Robot R102** – Friction Stir Welding Robot
3. **Robot R103** – Automated Riveting Robot
4. **Robot R104** – Paint & Protective Coating Robot
5. **Robot R105** – Vision Inspection Robot







Only 5 sensors for each machine

1) Robot R101 – Wing Positioning & Fixturing
Sensor	                  Why
Joint Temperature	      Servo overheating
Motor Current	          Overload detection
Joint Vibration	          Bearing wear
Encoder Position	      Position accuracy
Torque Sensor	          Mechanical resistance

2) Robot R102 – Friction Stir Welding
Sensor	                  Why
Welding Temperature	      Weld quality
Spindle Torque	          Tool load
Coolant Flow Rate	      Cooling efficiency
Motor Current	          Motor health
Vibration	              Bearing/tool wear

3) Robot R103 – Automated Riveting
Sensor	                  Why
Pneumatic Pressure	      Rivet quality
Riveting Force	          Proper insertion
Motor Current	          Servo health
Vibration	              Bearing wear
Encoder Position	      Rivet accuracy

4) Robot R104 – Paint & Protective Coating
Sensor	                  Why
Paint Pressure	          Uniform coating
Paint Flow Rate	          Paint quantity
Nozzle Temperature	      Clogging detection
Pump Current	          Pump health
Robot Speed	Paint         thickness consistency

5) Robot R105 – Vision Inspection
Sensor	                  Why
Camera Temperature	      Camera health
Laser Thickness Sensor    Paint thickness
Lighting Intensity	      Inspection quality
CPU Temperature	          Vision processor health
Camera Position Encoder	  Inspection accuracy

