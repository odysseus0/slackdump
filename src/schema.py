from typing import List

from pydantic import BaseModel, Field


class StakeholderNote(BaseModel):
    stakeholder_name: str = Field(
        description="The name of the stakeholder. This should be the name of the partner company or project. It is never the name of an individual."
    )
    date: str = Field(
        description="The date when the meeting with or discussion about the partner happened. Use ISO 8601 date string",
    )
    title: str = Field(
        description="The title of the meeting or discussion. This should be a concise overview of the interaction."
    )
    summary: str = Field(
        description="A high-level summary of the meeting or discussion with the partner. Include key points, main outcomes, and any critical follow-up actions. This should be a concise overview of the interaction."
    )
    relevant_slack_threads: List[str] = Field(
        description="A list of unique identifiers for Slack threads related to this note. Each identifier should be in the format 'Username [UserID] @ Timestamp'. For example: 'Quintus [U03HT20PJES] @ 16/03/2024 14:09:39 Z:'"
    )


class StakeholderNotes(BaseModel):
    stakeholder_notes: list[StakeholderNote] = Field(
        default_factory=list,
        description="A list of StakeholderNote objects extracted from the given context",
    )


class PostProcessedStakeholderNote(StakeholderNote):
    full_slack_threads: str = Field(
        description="The full text of relevant Slack threads associated with this note."
    )

    def get_thread_markdown(self) -> str:
        return "\n".join(self.full_slack_threads)


if __name__ == "__main__":
    print(StakeholderNote.model_json_schema())
    print(StakeholderNotes.model_json_schema())
    print(PostProcessedStakeholderNote.model_json_schema())
