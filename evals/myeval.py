"""
This module supports basic evaluations of the quality of the answers given by
Chat implementation modules.

it uses a custom evaluator (we will look into existing evalutation libraries later)
"""

import csv
from pydantic import BaseModel
from dotenv import load_dotenv
from src.chat.Chat import Chat
from src.schemas.ChatSchemas import ChatMessage
from openai import AzureOpenAI
import os

load_dotenv()


class Datum(BaseModel):
    input: str
    target: str
    source: str


class Evaluation(BaseModel):
    correct: bool


type Dataset = list[Datum]

openai_client = AzureOpenAI(azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"))


def get_dataset_from_csv(filepath: str) -> Dataset:
    "load an evaluation dataset from a CSV"
    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [Datum(**d) for d in reader]


def evaluate_chat_implementation_on_dataset(
    chat_implementation: Chat, data: Dataset
) -> dict:
    promptbase = """

    You are a teacher evaluating answers.
    You will be given a question, and answer and a ground truth (a correct answer)

    You should judge whether the answer is correct.
    The answer may contain more or less information than the ground truth, but IT MUST 
    actually answer the question, and not disagree with the the ground truth in any 
    respect.
    Otherwise the answer is incorrect.

    """
    results = []
    chat = chat_implementation()
    for datum in data:
        question = datum.input
        answer = datum.target
        history = [ChatMessage(role="user", content=question)]
        response = chat.chat_query(chat_history=history).content
        prompt_extension = (
            f"question: {question} \n answer: {response} \n ground truth: {answer}"
        )

        eval_history = [
            ChatMessage(role="user", content=promptbase + prompt_extension).model_dump()
        ]

        eval_response = openai_client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=eval_history,
            temperature=0.7,
            max_tokens=500,
            response_format=Evaluation,
        )

        results.append(
            {
                "query": question,
                "response": response,
                "answer": answer,
                "eval": eval_response.choices[0].message.parsed.correct,
            }
        )

    score = sum(t["eval"] for t in results)

    print(f"score: {score}/{len(results)}")

    report = {"score": f"{score}/{len(results)}", "questions": results}

    return report


if __name__ == "__main__":
    pass
