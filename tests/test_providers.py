import os, logging, csv
from pydantic import BaseModel, Field
from promptflow.client import PFClient
from pytest_csv_params.decorator import csv_params
from langchain.prompts.prompt import PromptTemplate

from utils.models import Models

pf_client = PFClient()


class RatingOutput(BaseModel):
    accuracy_relevance_rating: int = Field(..., description="A numerical rating of the answer to evaluate, how factually correct and relevant is the response according to the documents and the question.")
    grounding_rating: int = Field(..., description="A numerical rating of the answer to evaluate, how strictly is the response based on the knowledge in the documents (no hallucination).")
    product_recommendation_rating: int = Field(..., description="A numerical rating of the answer to evaluate, how appropriate and contextually relevant are the suggested products.")
    
    explanation: str = Field(..., description="An explanation of the rating, why the answer was rated as it was.")


def cast_to_list(value):
    if value == "[]":
        return []
    else:
        result = value.strip("[]").split(",")
        return result


def evaluate_flow_result(flow_result: dict, question: str, benchmark_answer: str) -> RatingOutput:    
    llm = Models.get_model("OPENAI", "normal")

    prompt = PromptTemplate.from_template('''
        You are an evaluation model. Your task is to rate an AI-generated response based on a given question, a benchmark response, and provided documents.  

        Your evaluation should focus primarily on the content (including strict grounding in the documents) and the form (clarity, grammar, coherence). Ignore any HTML tags or formatting; only assess the actual textual content.

        Your output:
        - accuracy_relevance_rating (integer 1-10): How factually correct and relevant is the response according to the documents and the question?  
        - grounding_rating (integer 1-10): How strictly is the response based on the knowledge in the documents (no hallucination)?  
        - product_recommendation_rating (integer 1-10): How appropriate and contextually relevant are the suggested products, if any?  
        - explanation (string in Czech language): Concise explanation why these ratings were assigned.

        Guidelines:  
        1. Compare the AI-generated response to the benchmark response.  
        2. Evaluate based on the provided documents:  
            - Accuracy and relevance: Factual correctness and relevance to the user's original question.  
            - Grounding: Whether the response strictly uses information from the documents and avoids hallucinations.  
            - Quality of product recommendations: Relevance and suitability of any suggested products to the context and the question.  
        3. Evaluate the form: clarity, structure, grammar, and readability (only mentioned in the explanation, not separately scored).  
        4. Ignore any HTML tags or formatting in the answer.

        Inputs:  
        - Question: "{question}"  
        - Benchmark answer: "{benchmark_answer}"  
        - Answer to evaluate: "{answer_to_evaluate}"  
        - Documents: "{documents}"
    ''')

    data = {
        "question": question,
        "benchmark_answer": benchmark_answer,
        "answer_to_evaluate": f'{flow_result["Response"]}',
        "documents": f'{flow_result["documents"]}'
    }
    
    structured_llm = llm.with_structured_output(RatingOutput, include_raw=True)
    chain = prompt | structured_llm
    
    output_data = chain.invoke(data)
    output = output_data.get("parsed")
    
    return output


def run_flow(llm_provider, customer_input, chat_history, person, benchmark_answer) -> RatingOutput:
    flow_path = "flow/"
    flow_input = {
        "customer_input": customer_input,
        "chat_history": chat_history,
        "context": {
            "page_title":"Domů - E-shop s elektronikou",
            "current_url": "https://eshop.cz/",
            "language": "CS"
        },
        "customer": {
            "customer_id": person,
        },
        "llm_provider": llm_provider
    }
    
    try:
        flow_result = pf_client.test(flow=flow_path, inputs=flow_input)
    except Exception as e:
        logging.error("Výjimka při spuštění pf_client.test: %s", e)
        flow_result = {"Response": "Chyba zpracování - {e}" }
    
    if flow_result is None:
        logging.error("Test failed with Question: %s \r\n and answer is: %s ", customer_input)
    else:
        logging.info("Test passed with Question: %s \r\n and answer is: %s ", customer_input, flow_result['Response'])
    
    # zpracujeme vysledek z flow a porovname ho s tim, co za odpoved ocekavame 
    result_evaluate = evaluate_flow_result(flow_result, customer_input, benchmark_answer)
    
    return result_evaluate


class CsvParamsDefaultDialect(csv.Dialect):
    delimiter = ","
    doublequote = True
    lineterminator = "\r\n"
    quotechar = '"'
    quoting = csv.QUOTE_ALL
    strict = True
    skipinitialspace = True


@csv_params(
    data_file = "tests/test_files/provider_test_data.csv",
    data_casts = {
        "customer_input": str,
        "chat_history": cast_to_list,
        "person": str,
        "benchmark_answer": str
    },
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    dialect = CsvParamsDefaultDialect,
)

def test_provider_google(customer_input, chat_history, person, benchmark_answer):
    result_evaluate = run_flow("GOOGLE", customer_input, chat_history, person, benchmark_answer)

    if ((result_evaluate.accuracy_relevance_rating + 
        result_evaluate.grounding_rating + 
        result_evaluate.product_recommendation_rating) >= 15
    ):
        good_answer = True
    else:
        good_answer = False
    
    assert good_answer


@csv_params(
    data_file = "tests/test_files/provider_test_data.csv",
    data_casts = {
        "customer_input": str,
        "chat_history": cast_to_list,
        "person": str,
        "benchmark_answer": str
    },
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    dialect = CsvParamsDefaultDialect,
)

def test_provider_xai(customer_input, chat_history, person, benchmark_answer):
    result_evaluate = run_flow("XAI", customer_input, chat_history, person, benchmark_answer)

    if ((result_evaluate.accuracy_relevance_rating + 
        result_evaluate.grounding_rating + 
        result_evaluate.product_recommendation_rating) >= 15
    ):
        good_answer = True
    else:
        good_answer = False
    
    assert good_answer


@csv_params(
    data_file = "tests/test_files/provider_test_data.csv",
    data_casts = {
        "customer_input": str,
        "chat_history": cast_to_list,
        "person": str,
        "benchmark_answer": str
    },
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    dialect = CsvParamsDefaultDialect,
)

def test_provider_openai(customer_input, chat_history, person, benchmark_answer):
    result_evaluate = run_flow("OPENAI", customer_input, chat_history, person, benchmark_answer)

    if ((result_evaluate.accuracy_relevance_rating + 
        result_evaluate.grounding_rating + 
        result_evaluate.product_recommendation_rating) >= 15
    ):
        good_answer = True
    else:
        good_answer = False
    
    assert good_answer


@csv_params(
    data_file = "tests/test_files/provider_test_data.csv",
    data_casts = {
        "customer_input": str,
        "chat_history": cast_to_list,
        "person": str,
        "benchmark_answer": str
    },
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    dialect = CsvParamsDefaultDialect,
)

def test_provider_anthropic(customer_input, chat_history, person, benchmark_answer):
    result_evaluate = run_flow("ANTHROPIC", customer_input, chat_history, person, benchmark_answer)

    if ((result_evaluate.accuracy_relevance_rating + 
        result_evaluate.grounding_rating + 
        result_evaluate.product_recommendation_rating) >= 15
    ):
        good_answer = True
    else:
        good_answer = False
    
    assert good_answer
