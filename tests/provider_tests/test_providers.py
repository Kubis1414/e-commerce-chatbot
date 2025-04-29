import os, logging, csv, datetime, json
import pytest
from pathlib import Path
from pydantic import BaseModel, Field
from promptflow.client import PFClient
from pytest_csv_params.decorator import csv_params
from langchain.prompts.prompt import PromptTemplate

from utils.models import Models

# Setup logging for test results
RESULTS_DIR = Path("test_results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DETAIL_DIR = RESULTS_DIR / "test_results_detail"
RESULTS_DETAIL_DIR.mkdir(parents=True, exist_ok=True)

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
        "answer_to_evaluate": f'{flow_result["response"]}',
        "documents": f'{flow_result["documents"]}'
    }
    
    structured_llm = llm.with_structured_output(RatingOutput, include_raw=True)
    chain = prompt | structured_llm
    
    output_data = chain.invoke(data)
    output = output_data.get("parsed")
    
    return output


def log_test_result(llm_provider, customer_input, chat_history, person, flow_result, result_evaluate, duration=0):
    """Log test results to a CSV file with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_file = RESULTS_DIR / f"provider_test_results_{timestamp.split('_')[0]}.csv"
    
    # Create header if file doesn't exist
    is_new_file = not results_file.exists()
    
    with open(results_file, 'a', newline='', encoding='utf-8') as f:
        fieldnames = [
            'timestamp', 'llm_provider', 'accuracy_relevance_rating', 'grounding_rating', 'product_recommendation_rating',
            'total_score', 'duration', 'cost', 'customer_input', 'flow_response'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if is_new_file:
            writer.writeheader()
        
        # Prepare data for CSV
        row = {
            'timestamp': timestamp,
            'llm_provider': llm_provider,
            'customer_input': customer_input,
            'accuracy_relevance_rating': result_evaluate.accuracy_relevance_rating,
            'grounding_rating': result_evaluate.grounding_rating,
            'product_recommendation_rating': result_evaluate.product_recommendation_rating,
            'total_score': (result_evaluate.accuracy_relevance_rating + 
                           result_evaluate.grounding_rating + 
                           result_evaluate.product_recommendation_rating),
            'flow_response': flow_result.get('response', 'Error: No response'),
            'duration': duration if duration is not None else 'N/A',
            'cost': flow_result.get('cost', 'N/A')
        }
        
        writer.writerow(row)
    
    # Also save detailed JSON for further analysis
    json_file = RESULTS_DETAIL_DIR / f"provider_test_detail_{llm_provider}_{timestamp}.json"
    json_data = {
        'timestamp': timestamp,
        'llm_provider': llm_provider,
        'customer_input': customer_input,
        'chat_history': chat_history,
        'person': person,
        'evaluation': {
            'accuracy_relevance_rating': result_evaluate.accuracy_relevance_rating,
            'grounding_rating': result_evaluate.grounding_rating,
            'product_recommendation_rating': result_evaluate.product_recommendation_rating,
            'explanation': result_evaluate.explanation
        },
        'flow_result': flow_result,
        'duration': duration
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Test results logged to {results_file} and {json_file}")


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
        start_time = datetime.datetime.now()
        flow_result = pf_client.test(flow=flow_path, inputs=flow_input)
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        logging.info(f"Flow execution time: {duration} seconds")
    except Exception as e:
        logging.error("Výjimka při spuštění pf_client.test: %s", e)
        flow_result = {"response": f"Chyba zpracování - {e}" }
    
    if flow_result is None:
        logging.error("Test failed with Question: %s \r\n and answer is: %s ", customer_input)
        flow_result = {"response": "Test failed - flow_result is None"}
    else:
        logging.info("Test passed with Question: %s \r\n and answer is: %s ", customer_input, flow_result['response'])
    
    # zpracujeme vysledek z flow a porovname ho s tim, co za odpoved ocekavame 
    result_evaluate = evaluate_flow_result(flow_result, customer_input, benchmark_answer)
    
    # Log test results
    log_test_result(llm_provider, customer_input, chat_history, person, flow_result, result_evaluate, duration)
        
    return result_evaluate


class CsvParamsDefaultDialect(csv.Dialect):
    delimiter = ","
    doublequote = True
    lineterminator = "\r\n"
    quotechar = '"'
    quoting = csv.QUOTE_ALL
    strict = True
    skipinitialspace = True


@pytest.mark.providers
@csv_params(
    data_file = "tests/provider_tests/test_files/provider_test_data.csv",
    data_casts = {
        "customer_input": str,
        "chat_history": cast_to_list,
        "person": str,
        "benchmark_answer": str
    },
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
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


@pytest.mark.providers
@csv_params(
    data_file = "tests/provider_tests/test_files/provider_test_data.csv",
    data_casts = {
        "customer_input": str,
        "chat_history": cast_to_list,
        "person": str,
        "benchmark_answer": str
    },
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
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


@pytest.mark.providers
@csv_params(
    data_file = "tests/provider_tests/test_files/provider_test_data.csv",
    data_casts = {
        "customer_input": str,
        "chat_history": cast_to_list,
        "person": str,
        "benchmark_answer": str
    },
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
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


@pytest.mark.providers
@csv_params(
    data_file = "tests/provider_tests/test_files/provider_test_data.csv",
    data_casts = {
        "customer_input": str,
        "chat_history": cast_to_list,
        "person": str,
        "benchmark_answer": str
    },
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
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
