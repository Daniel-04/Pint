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

The configuration file (Excel, CSV, or JSON format) controls all aspects of processing:
- Which LLM to use
- Data source locations
- Prompt specifications
- Additional settings

## Input/Output

**Input:**
- Excel, CSV, or JSON file with a specified column containing either:
  - PubMed ID (PMC number)
  - Filename (if not numerical or PMC format)

**Output:**
- CSV and JSON files containing the ID and requested extracted data

## Example

Simple examples using PDF files are provided in the examples folder:

```bash
python -m pint_lib examples/Claude/test_config_pdf.xlsx
```

## Configuration

Configuration is handled via Excel, CSV, or JSON files.

A GUI for configuration generation is included:

``` bash
python config_gui.py
```

or

``` bash
python -m pint_lib.config_gui
```

Multi value input can be entered space separated, quoting text makes it all a single value:
- `abstract introduction conclusion` is treated as: `["abstract", "introduction", "conclusion"]`
- `"this is an example prompt"` -> "this is an example prompt"

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
