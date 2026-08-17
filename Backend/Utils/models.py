

from typing import Literal,Optional,List
from pydantic import BaseModel, Field

class JudgeResult(BaseModel):

    violation: Literal[
        "NONE",
        "PROMPT_INJECTION",
        "JAILBREAK",
        "HARMFUL_REQUEST",
        "OUT_OF_SCOPE"
    ] = Field(
        description=(
            "Security classification for the user query. "
            "Return 'NONE' if no security or policy violation is detected."
        )
    )

    route: Literal[
        "NONE",
        "GREETING",
        "IN_DOMAIN"
    ] = Field(
        description=(
            "Choose how the application should handle the query. "
            "'GREETING' for normal LLM conversation like greetings, "
            "'NONE' if no specific handling is required, "
            "'IN_DOMAIN' if query is on manufacturing machine issues or related topics. "
        )
    )

    response: str = Field(
        description=(
            "Provide a direct response only when the route is 'GREETING'. "
            "Otherwise return an empty string."
        )
    )


class ExtractedEntities(BaseModel):

    machine_id: Optional[
        Literal["R101", "R102", "R103", "R104", "R105"]
    ] = Field(
        default=None,
        description="Manufacturing machine identifier."
    )

    clarification_response: Optional[str] = Field(
        default=None,
        description="Clarification question when the machine cannot be identified."
    )