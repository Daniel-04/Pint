# PubMed Integrated NLP Tool (PINT)

A tool for serial processing of open-source PubMed Central papers with various Large Language Models.

## Overview

PINT allows you to process academic papers from PubMed using your choice of:
- OpenAI models
- Anthropic's Claude
- External shell script integration


## Dependencies

* pdfminer.six - for reading pdf files
* openpyxl - for reading .xlsx files
* requests - to use PubMed API
* anthropic - to use anthropic's Clause API
* openai - to use OpenAI's ChatGPT API
* tkinter - to use the config GUI

## Installation
```bash
pip install pint_lib
```

## Basic Installation
Without dependencies - you can install separately only those you need 

```bash
pip install pint_lib[base]
```
## Usage

```bash
python -m pint_lib <Config_file>
```

The configuration file (Excel or CSV format) controls all aspects of processing:
- Which LLM to use
- Data source locations
- Prompt specifications
- Additional settings

## Input/Output

**Input:**
- CSV or Excel file with a specified column containing either:
  - PubMed ID (PMC number)
  - Filename (if not numerical or PMC format)

**Output:**
- CSV file containing the ID and requested extracted data

## Example

Simple examples using PDF files are provided in the examples folder:

```bash
python -m pint_lib examples/Claude/test_config_pdf.xlsx
```

## Configuration

Configuration is handled via Excel or CSV files.  

## Usage with [llm_server](https://github.com/PubLLicanProject/llm_server)
Run `pip install Pint` in the venv created by the `build.sh` script of llm_server.
Then, in the config set:
- model: openai
- model_name: [name of the ollama model to use]
- api_url: http://localhost:11434/v1 (The actual port may be different, check when activating the venv, or export OLLAMA_HOST=127.0.0.1:11434)
- api_key: ollama
While the venv is activated, run pint.

## Notes

- You can substitute CSV files for Excel files throughout, though Excel provides better document formatting.
```
