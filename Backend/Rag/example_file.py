import traceback
import truststore
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
from langchain_neo4j import Neo4jGraph
import xml.etree.ElementTree as ET
from datetime import datetime

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

def ingest_graph_rag(path:Path):

    try:

        tree = ET.parse(path)
        root = tree.getroot()
        events = root.findall("event")
        total = len(events)

        QUERY = """
        MERGE (m:Machine {id:$machine})
        MERGE (r:Reason {name:$reason})
        MERGE (e:Event {id:$event})
        SET
            e.start_time = $start, e.end_time = $end, e.duration = $duration, e.severity = $severity
        MERGE (m)-[:HAS_EVENT]->(e)
        MERGE (e)-[:HAS_REASON]->(r)
        """

        print(f"[{datetime.now().strftime("%H:%M:%S")}] Loading {total} events...\n")
        for index, event in enumerate(events, start=1):
            machine = event.find("machine_id").text
            event_id = event.find("event_id").text
            start = event.find("start_time").text
            end = event.find("end_time").text
            duration = int(event.find("duration_minutes").text)
            reason = event.find("reason").text
            severity = event.find("severity").text
            print(f"[{datetime.now().strftime("%H:%M:%S")}] ({index}/{total}) Loading {event_id}")
            kgraph.query(
                QUERY,
                {
                    "machine": machine, "event": event_id,
                    "start": start, "end": end,
                    "duration": duration, "reason": reason, "severity": severity,
                },
            )
        print(f"\n[{datetime.now().strftime("%H:%M:%S")}] Knowledge Graph Loaded Successfully!")

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

        print(f"PDF saved to: {output_path}")
        
    except Exception as e:  
        print("Error occurred while saving text as PDF:", repr(e))
        traceback.print_exc()
