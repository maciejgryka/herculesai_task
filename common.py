from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    AMBIGUOUS = "ambiguous"


class Term(BaseModel):
    section: str
    name: str
    description: str


class TermList(BaseModel):
    terms: list[Term]


class Task(BaseModel):
    description: str
    amount: str = Field(description="The $ amount to charge for the task")


class TaskJudgement(BaseModel):
    task: Task
    task_status: TaskStatus
    related_terms: TermList
