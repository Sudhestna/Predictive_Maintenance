import traceback
import truststore
from Utils.dashboard import update_dashboard
truststore.inject_into_ssl()
import fitz
import io
import os,time,pickle
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid 
from PIL import Image
from paddleocr import PaddleOCR
import numpy as np
from langchain_core.documents import Document
from Services.llm import vector_store,kgraph,ocr
from langchain_community.document_loaders import PyPDFLoader
import os,time,pickle
from langchain_community.retrievers import BM25Retriever
from Services.llm import gpt_llm
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
from Services.guardrail import guard

def perform_ocr(image):

    result = list(ocr.predict(image))

    lines = []

    for page in result:

        rec_texts = page.get("rec_texts", [])
        rec_boxes = page.get("rec_boxes", [])
        items = []

        for box, text in zip(rec_boxes, rec_texts):

            if text.strip():

                x = box[0]
                y = box[1]

                items.append((y, x, text.strip()))

       
        items.sort(key=lambda t: (t[0], t[1]))


        current_line = []
        previous_y = None

        
        heights = []

        for box in rec_boxes:

            height = box[3] - box[1]

            heights.append(height)

        if heights:

            avg_height = sum(heights) / len(heights)
            LINE_THRESHOLD = avg_height * 0.5

        else:

            LINE_THRESHOLD = 15

        for y, x, text in items:

            if previous_y is None:

                current_line.append((x, text))
                previous_y = y

            elif abs(y - previous_y) <= LINE_THRESHOLD:

                current_line.append((x, text))

            else:

                current_line.sort(key=lambda t: t[0])

                line = " ".join(word for _, word in current_line)

                lines.append(line)

                current_line = [(x, text)]

                previous_y = y

        if current_line:

            current_line.sort(key=lambda t: t[0])

            line = " ".join(word for _, word in current_line)

            lines.append(line)

    update_dashboard("documents", "ocr_processed")
    return "\n".join(lines)


def page_to_image(page):

 
    pix = page.get_pixmap(dpi=150)

    image = np.array(Image.open(
        io.BytesIO(
            pix.tobytes("png")
        )
    ).convert("RGB")
    )

    return image

def process_pdf(pdf_path):

    doc = fitz.open(pdf_path)

    structured_document = []

    complete_text = ""

    ocr_cache = {}

    for page_no in range(len(doc)):

        print(f"\nProcessing Page {page_no + 1}")

        page = doc[page_no]

        blocks = page.get_text("dict")["blocks"]

        page_data = {
            "page": page_no + 1,
            "blocks": []
        }

        page_output = []

        for block in blocks:

            if block["type"] == 0:

                for line in block["lines"]:

                    line_text = []

                    font_sizes = []

                    bold = False

                    for span in line["spans"]:

                        txt = span["text"].strip()

                        if txt:

                            line_text.append(txt)

                            font_sizes.append(span["size"])

                            if "bold" in span["font"].lower():

                                bold = True

                    if not line_text:
                        continue

                    avg_size = (
                        sum(font_sizes) / len(font_sizes)
                        if font_sizes else 12
                    )

                    block_type = "paragraph"

                    if avg_size >= 16 or bold:

                        block_type = "heading"

                    text = " ".join(line_text)

                    page_data["blocks"].append({

                        "type": block_type,

                        "text": text,

                        "bbox": line["bbox"],

                        "font_size": avg_size

                    })

                    page_output.append(text)

            elif block["type"] == 1:

                print("Image block found")

                image_bytes = block.get("image")

                if image_bytes is None:
                    continue

                if image_bytes not in ocr_cache:

                    image = Image.open(
                        io.BytesIO(image_bytes)
                    )

                    if image.mode != "RGB":

                        image = image.convert("RGB")

                    image = np.array(image)

                    print("Running OCR...")

                    ocr_cache[image_bytes] = perform_ocr(image)

                ocr_text = ocr_cache[image_bytes]

                page_data["blocks"].append({

                    "type": "image",

                    "text": ocr_text,

                    "bbox": block["bbox"]

                })

                page_output.append(ocr_text)

        if len(page_data["blocks"]) == 0:

            print("Falling back to page OCR...")

            image = page_to_image(page)

            ocr_text = perform_ocr(image)

            page_data["blocks"].append({

                "type": "page",

                "text": ocr_text,

                "bbox": page.rect

            })

            page_output.append(ocr_text)

        structured_document.append(page_data)

        complete_text += "\n".join(page_output)
        #############

    doc.close()

    return structured_document, complete_text

def process_image(image_path):

    print("Processing Image")

    image = np.array(Image.open(image_path).convert("RGB"))

    return perform_ocr(image)



def structure_aware_chunk(document,file_path,chunk_size=1200,chunk_overlap_blocks=1):

    documents = []
    chunk_blocks = []
    current_size = 0
    chunk_id = 0
    file_name = Path(file_path).name
    machine_id=file_name.split("_")[0]

    def save_chunk():
        nonlocal chunk_blocks
        nonlocal current_size
        nonlocal chunk_id

        if not chunk_blocks:
            return

        documents.append(
            Document(
                page_content="\n\n".join(
                    b["text"]
                    for b in chunk_blocks
                ),
                metadata={
                    "page": chunk_blocks[0]["page"],
                    "chunk_id": chunk_id,
                    "machine_id":machine_id,
                    "source": file_name
                }
            )

        )

        chunk_id += 1
        if chunk_overlap_blocks > 0:
            chunk_blocks[:] = chunk_blocks[-chunk_overlap_blocks:]
            current_size = sum(
                len(b["text"])
                for b in chunk_blocks
            )
        else:
            chunk_blocks.clear()
            current_size = 0

    for page in document:

        page_no = page["page"]
        for block in page["blocks"]:
            text = block["text"].strip()

            if not text:
                continue

            block = block.copy()
            block["page"] = page_no
            block_size = len(text)

            if (
                block["type"] == "heading"
                and len(chunk_blocks) > 0
            ):
                save_chunk()

            if (
                current_size + block_size > chunk_size
                and len(chunk_blocks) > 0
            ):

                save_chunk()
            chunk_blocks.append(block)
            current_size += block_size

    save_chunk()

    return documents


def chunking(complete_text,file_path,chunk_size=1000,chunk_overlap=200):   
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )
    chunks = splitter.split_text(complete_text)
    file_name = Path(file_path).name
    machine_id=file_name.split("_")[0]
    documents = []

    for chunk in chunks:
        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    "chunk_id": str(uuid.uuid4()),
                    "source": file_name,
                    "machine_id": machine_id
                }
            )
        )

    return documents

def extract_text(file_path):

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":

        return process_pdf(file_path)

    elif extension in [

        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp"

    ]:

        return process_image(file_path)

def rag_ingestion(path:Path):

    try:
        text,final_text = extract_text(path)



        doc_objects=structure_aware_chunk(text,path)

        ###### Anonymized Sensitive content before reaching Embedding model ######
        
        for obj in doc_objects:
            mask_data = guard.mask_pii(obj.page_content)
            obj.page_content = mask_data

        print(f"doc_objects:",doc_objects)
        
        vector_store.add_documents(
            documents=doc_objects
        )

        print("ChromaDB saved successfully.")
        return "success"
    
    except Exception as e:
        print("Error occurred during RAG ingestion:", repr(e))
        traceback.print_exc()
        return "failure"

def ingest_graph_rag(file_path:Path):

    try:

        CONSTRAINTS = [
                "CREATE CONSTRAINT robot_id IF NOT EXISTS FOR (r:Robot) REQUIRE r.robot_id IS UNIQUE",
                "CREATE CONSTRAINT stage_id IF NOT EXISTS FOR (s:Stage) REQUIRE s.stage_id IS UNIQUE",
                "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.component_id IS UNIQUE",
                "CREATE CONSTRAINT sensor_id IF NOT EXISTS FOR (s:Sensor) REQUIRE s.sensor_id IS UNIQUE",
                "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:FailureEvent) REQUIRE e.event_id IS UNIQUE",
                "CREATE CONSTRAINT record_id IF NOT EXISTS FOR (m:MaintenanceRecord) REQUIRE m.record_id IS UNIQUE",
                "CREATE CONSTRAINT failure_mode_name IF NOT EXISTS FOR (f:FailureMode) REQUIRE f.name IS UNIQUE",
                "CREATE CONSTRAINT root_cause_name IF NOT EXISTS FOR (rc:RootCause) REQUIRE rc.name IS UNIQUE",
                "CREATE CONSTRAINT technician_id IF NOT EXISTS FOR (t:Technician) REQUIRE t.technician_id IS UNIQUE",
            ]
    
        LOAD_EQUIPMENT = """
        UNWIND $rows AS row
        MERGE (s:Stage {stage_id: row.stage_id}) ON CREATE SET s.name = row.stage_name
        MERGE (r:Robot {robot_id: row.robot_id})
        SET r.name = row.robot_name,
            r.model = row.model,
            r.manufacturer = row.manufacturer,
            r.install_date = row.install_date,
            r.criticality = row.criticality,
            r.rated_cycles_per_day = toInteger(row.rated_cycles_per_day),
            r.last_calibration_date = row.last_calibration_date
        MERGE (r)-[:OPERATES_AT]->(s)
        """
    
        LOAD_COMPONENTS = """
        UNWIND $rows AS row
        MATCH (r:Robot {robot_id: row.robot_id})
        MERGE (c:Component {component_id: row.component_id})
        SET c.name = row.component_name,
            c.type = row.component_type
        MERGE (r)-[:HAS_COMPONENT]->(c)
        """
    
        LOAD_SENSORS = """
        UNWIND $rows AS row
        MATCH (c:Component {component_id: row.component_id})
        MERGE (sn:Sensor {sensor_id: row.sensor_id})
        SET sn.name = row.sensor_name,
            sn.type = row.sensor_type,
            sn.unit = row.unit,
            sn.warning_threshold = toFloat(row.warning_threshold),
            sn.critical_threshold = toFloat(row.critical_threshold)
        MERGE (sn)-[:MONITORS]->(c)
        """
    
        LOAD_FAILURE_EVENTS = """
        UNWIND $rows AS row
        MATCH (r:Robot {robot_id: row.robot_id})
        MATCH (c:Component {component_id: row.component_id})
        MATCH (sn:Sensor {sensor_id: row.triggering_sensor_id})
        MERGE (fm:FailureMode {name: row.failure_mode})
        MERGE (rc:RootCause {name: row.root_cause})
        MERGE (fm)-[:TYPICALLY_CAUSED_BY]->(rc)
        MERGE (fe:FailureEvent {event_id: row.event_id})
        SET fe.onset_ts = row.onset_ts,
            fe.source_file = $file_name,
            fe.detected_ts = row.detected_ts,
            fe.resolved_ts = row.resolved_ts,
            fe.severity = row.severity,
            fe.downtime_hrs = toFloat(row.downtime_hrs),
            fe.time_to_detect_hrs = toFloat(row.time_to_detect_hrs),
            fe.production_units_affected = toInteger(row.production_units_affected),
            fe.quality_impact = row.quality_impact,
            fe.estimated_cost_impact_usd = toFloat(row.estimated_cost_impact_usd),
            fe.wing_unit_range_start = row.wing_unit_range_start,
            fe.wing_unit_range_end = row.wing_unit_range_end,
            fe.threshold_breached = row.threshold_breached,
            fe.threshold_value = toFloat(row.threshold_value),
            fe.reading_value_at_detection = toFloat(row.reading_value_at_detection),
            fe.status = row.status
        MERGE (r)-[:EXPERIENCED]->(fe)
        MERGE (fe)-[:INVOLVES_COMPONENT]->(c)
        MERGE (fe)-[:TRIGGERED_BY]->(sn)
        MERGE (fe)-[:CLASSIFIED_AS]->(fm)
        MERGE (fe)-[:CAUSED_BY]->(rc)
        """
    
        LOAD_MAINTENANCE = """
        UNWIND $rows AS row
        MATCH (c:Component {component_id: row.component_id})
        MERGE (t:Technician {technician_id: row.technician_id})
        SET t.name = row.technician_name,
            t.certification_level = row.technician_certification_level
        MERGE (m:MaintenanceRecord {record_id: row.record_id})
        SET m.record_type = row.record_type,
            m.date = row.date,
            m.source_file = $file_name,
            m.scheduled_or_unscheduled = row.scheduled_or_unscheduled,
            m.action_taken = row.action_taken,
            m.downtime_hrs = toFloat(row.downtime_hrs),
            m.labor_hours = toFloat(row.labor_hours),
            m.parts_replaced = row.parts_replaced,
            m.total_cost_usd = toFloat(row.total_cost_usd),
            m.post_repair_test_result = row.post_repair_test_result,
            m.notes = row.notes
        MERGE (m)-[:ON_COMPONENT]->(c)
        MERGE (m)-[:PERFORMED_BY]->(t)
        WITH m, row
        WHERE row.event_id IS NOT NULL AND row.event_id <> ""
        MATCH (fe:FailureEvent {event_id: row.event_id})
        MERGE (fe)-[:RESOLVED_BY]->(m)
        """
    
        for stmt in CONSTRAINTS:
            kgraph.query(stmt)
    
        file_name = file_path.name.lower()
    
        if "equipment" in file_name:
            query = LOAD_EQUIPMENT
    
        elif "component" in file_name:
            query = LOAD_COMPONENTS
    
        elif "sensor" in file_name:
            query = LOAD_SENSORS
    
        elif "failure" in file_name:
            query = LOAD_FAILURE_EVENTS
    
        elif "maintenance" in file_name:
            query = LOAD_MAINTENANCE
    
        else:
            raise ValueError("Unable to identify the uploaded CSV type.")
    
        if "sensor" in file_name:
            df = pd.read_csv(file_path, encoding="cp1252")
        else:
            df = pd.read_csv(file_path)
    
        kgraph.query(
            query,
            {
                "rows": df.to_dict("records"),
                "file_name": file_path.name
            }
        )
    
        print(f"{file_path.name} ingested success")
        return "success"
    except Exception as e:  
        print("Error occurred during Graph RAG ingestion:", repr(e))
        traceback.print_exc()
        return "failure"



import re

def format_markdown(line: str):

    # Bold
    line = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        line
    )

    # Italic
    line = re.sub(
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
        r"<i>\1</i>",
        line
    )

    return line


####### Report pdf generation function ##################

from reportlab.platypus import SimpleDocTemplate, Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os

def save_text_as_pdf(text: str, output_path: str):

    try:

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        doc = SimpleDocTemplate(output_path)
        styles = getSampleStyleSheet()

        story = []

        for line in text.splitlines():

            line = line.strip()

            # Empty line
            if not line:
                story.append(Spacer(1, 8))
                continue

            line = format_markdown(line)

            # -------- Headings --------

            if line.startswith("### "):
                story.append(
                    Paragraph(line[4:], styles["Heading3"])
                )
                continue

            if line.startswith("## "):
                story.append(
                    Paragraph(line[3:], styles["Heading2"])
                )
                continue

            if line.startswith("# "):
                story.append(
                    Paragraph(line[2:], styles["Heading1"])
                )
                continue

            # -------- Bullets --------

            if line.startswith("- "):
                story.append(
                    Paragraph(
                        f"&#8226; {line[2:]}",
                        styles["BodyText"]
                    )
                )
                continue

            if line.startswith("* "):
                story.append(
                    Paragraph(
                        f"&#8226; {line[2:]}",
                        styles["BodyText"]
                    )
                )
                continue

            # -------- Markdown formatting --------

            # **bold**
            line = re.sub(
                r"\*\*(.*?)\*\*",
                r"<b>\1</b>",
                line
            )

            # *italic*
            line = re.sub(
                r"\*(.*?)\*",
                r"<i>\1</i>",
                line
            )

            story.append(
                Paragraph(line, styles["BodyText"])
            )

        doc.build(story)

        update_dashboard("chat", "reports_generated")
        print(f"PDF saved to: {output_path}")
        
    except Exception as e:  
        print("Error occurred while saving text as PDF:", repr(e))
        traceback.print_exc()