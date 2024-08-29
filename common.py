from enum import Enum

from pydantic import BaseModel, Field



class Term(BaseModel):
    section: str
    name: str
    description: str


class TermList(BaseModel):
    terms: list[Term]


class Task(BaseModel):
    description: str
    amount: str = Field(description="The $ amount to charge for the task")


class TaskRelevancy(BaseModel):
    contract_objective: str = Field(description="The main objective of the contract")
    relevant: bool = Field(description="Whether the task is relevant to main objective of the contract")
    ambiguous: bool = Field(description="Whether the relevancy of the task is ambiguous.")


class TaskJudgement(BaseModel):
    task: Task
    related_terms: TermList = Field(description="The terms related to the task")
    # ideally we'd use max_length, but OpenAI Structured Outputs don't support it
    explanation: str = Field(description="Short chain-of-thought reasoning for whether the task should be accepted or not.")
    ambiguous: bool = Field(description="Whether the validity of the task is ambiguous.")
    is_valid: bool = Field(description="Whether the task is valid or not.")
