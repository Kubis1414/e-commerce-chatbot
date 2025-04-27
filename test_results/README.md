# Provider Test Results

This directory contains the results of LLM provider tests that are automatically generated when running `test_providers.py`.

## File Structure

The logging system creates two types of files:

1. **CSV Summary Files** (`provider_test_results_YYYY-MM-DD.csv`):
   - One CSV file per day containing all test results in tabular format
   - Includes basic metrics and scores for quick comparison

2. **JSON Detail Files** (`provider_test_detail_PROVIDER_YYYY-MM-DD_HH-MM-SS.json`):
   - Individual JSON files for each test execution
   - Contains complete test details including:
     - Full customer input
     - Chat history
     - Complete flow response
     - Detailed evaluation metrics and explanation

## How to Use

### Running Tests

Tests are run using pytest as normal:

```bash
# Run all provider tests
pytest tests/provider_tests/test_providers.py -v

# Run tests for a specific provider
pytest tests/provider_tests/test_providers.py::test_provider_openai -v
```

### Analyzing Results

#### For Quick Comparison

Open the CSV file for the current date in Excel, LibreOffice, or any CSV viewer:

```bash
# Example
open test_results/provider_test_results_2025-04-27.csv
```

This shows a table with all tests run today, allowing you to quickly compare:
- Accuracy/relevance ratings
- Grounding ratings
- Product recommendation ratings
- Total scores
- And other key metrics across providers

#### For Detailed Analysis

The JSON files contain the complete data including the full response from each provider:

```bash
# Example
cat test_results/provider_test_detail_OPENAI_2025-04-27_17-30-45.json
```

These files are useful for:
- Debugging specific response issues
- Analyzing exactly how providers handled particular inputs
- Extracting the raw data for further processing

## Implementation Details

The logging system automatically:
- Creates one CSV file per day for easy tracking
- Generates timestamped JSON files for each test execution
- Includes all relevant data from the test

Evaluation metrics include:
- accuracy_relevance_rating (1-10)
- grounding_rating (1-10)
- product_recommendation_rating (1-10)
- A detailed explanation of the ratings
