import traceback
from detoxify import Detoxify
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
import re
from better_profanity import profanity

import truststore

from Utils.dashboard import update_dashboard
truststore.inject_into_ssl()

try:

    class Guardrails:

        def __init__(self):

            self.detoxify = Detoxify("original")
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            profanity.load_censor_words()
            self.operators = {
                "EMAIL_ADDRESS": OperatorConfig(
                    "replace",
                    {"new_value": "<EMAIL>"}
                ),
                "PHONE_NUMBER": OperatorConfig(
                    "replace",
                    {"new_value": "<PHONE>"}
                ),
                "PERSON": OperatorConfig(
                    "replace",
                    {"new_value": "<PERSON>"}
                ),
                "DEFAULT": OperatorConfig(
                    "replace",
                    {"new_value": "<PII>"}
                )
            }
            self.regex_patterns = {

                "AADHAAR": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
                "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
                "PASSPORT": r"\b[A-Z][0-9]{7}\b",
                "IFSC": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
                "UPI": r"\b[a-zA-Z0-9._-]+@[a-zA-Z]{2,}\b",
                "IPV4": r"\b(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}\b",
                "IPV6": r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b",
                "MAC_ADDRESS": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b",
                "AWS_ACCESS_KEY": r"\bAKIA[0-9A-Z]{16}\b",
                "AWS_SECRET_KEY": r"\b[A-Za-z0-9/+=]{40}\b",
                "OPENAI_API_KEY": r"\bsk-[A-Za-zA-Z0-9]{20,}\b",
                "GITHUB_TOKEN": r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b",
                "SLACK_TOKEN": r"\bxox[baprs]-[A-Za-z0-9-]+\b",
            }

        def toxicity(self,query:str)-> dict:

            scores = self.detoxify.predict(query)

            return {
            "allowed": bool(scores["toxicity"] < 0.7),
            "reason": "TOXICITY" if scores["toxicity"] >= 0.7 else None,
            "scores": {k: float(v) for k, v in scores.items()}
        }

        def profanity(self, query: str) -> dict:

            contains = profanity.contains_profanity(query)
                
            print(f"Profanity check for query: {query}, contains profanity: {contains}")
            return {
                "allowed": not contains,
                "censored_text": profanity.censor(query)
            }

        def detect_pii(self,query:str):

            entities = self.analyzer.analyze(
                text=query,
                language="en",
                entities=[
                "PERSON",
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "CREDIT_CARD",
                "IBAN_CODE",
                "LOCATION"
            ])

            return entities

        def mask_pii(self, query: str) -> str:

            entities = self.detect_pii(query)

            if entities:
                update_dashboard("guardrails", "pii_masked")
                text = self.anonymizer.anonymize(
                    text=query,
                    analyzer_results=entities,
                    operators=self.operators
                ).text
            else:
                text = query

            for entity, pattern in self.regex_patterns.items():
                text = re.sub(pattern, f"<{entity}>", text)

            return text

        def validate_text(self,query:str) -> dict:

            profanity_result = self.profanity(query)

            if not profanity_result["allowed"]:

                return {
                    "allowed": False,
                    "reason": "PROFANITY"
                }

            toxicity = self.toxicity(query)

            if toxicity["allowed"]:

                anonymized_text = self.mask_pii(query)
                toxicity["anonymized_text"] = anonymized_text

            return toxicity


    guard = Guardrails()
    print("guard object created")

except Exception as e:
    
    print("Error occurred while creating Guardrails object:", repr(e))
    traceback.print_exc()
