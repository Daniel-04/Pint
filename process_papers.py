import csv
import os
import json
import subprocess
import sys
import re

from .utils import log_traceback
from . import utils as u
from .parse_pubmed_json import parse_pubmed_data

prechecks = {
    "is_yes": u.isYes,
    "yes": u.isYes,
    "is_no": u.isNo,
    "no": u.isNo,
    "is_number": u.isNumber,
    "number": u.isNumber,
    "is_not_number": u.isNotNumber,
    "is_json": u.isJson,
    "json": u.isJson,
    "is_not_json": u.isNotJson,
    "is_comma_separated_list": u.isCommaSeparatedList,
    "comma_separated_list": u.isCommaSeparatedList,
    "is_not_comma_separated_list": u.isNotCommaSeparatedList,
    "not_comma_separated_list": u.isNotCommaSeparatedList,
    "is_json_list": u.isJsonList,
    "json_list": u.isJsonList,
    "is_not_json_list": u.isNotJsonList,
    "not_json_list": u.isNotJsonList,
    "is_short": u.isShort,
    "is_long": u.isLong,
    "is_greater_than": u.isGreaterThan,
    "is_less_than": u.isLessThan,
    "is_script_error": u.isError,
}


def preprocess_prompt_old(prompt, ctx, escape=False):
    for key in ctx.data_store:
        new_text = ctx.data_store[key]
        if escape:
            new_text = repr(new_text)

        prompt = prompt.replace(f"[{key}]", new_text)

    return prompt


def preprocess_prompt(prompt, ctx, max_length=None, escape=False, overlap=500):
    if max_length is None:
        max_length = ctx.max_prompt_length
    # Track original text and substitutions for splitting later if needed
    substitutions = []
    result = prompt

    # First pass: identify all substitutions
    for key in ctx.data_store:
        placeholder = f"[{key}]"
        if placeholder in result:
            new_text = ctx.data_store[key]
            if escape:
                new_text = repr(new_text)

            # Record information about each substitution
            for match_pos in [
                m.start() for m in re.finditer(f"(?={re.escape(placeholder)})", result)
            ]:
                substitutions.append(
                    {
                        "key": key,
                        "placeholder": placeholder,
                        "replacement": new_text,
                        "position": match_pos,
                        "length": len(new_text),
                    }
                )

    # Sort substitutions by position (to maintain order)
    substitutions.sort(key=lambda x: x["position"])

    # Apply substitutions to get the processed text
    processed_prompt = prompt
    for sub in substitutions:
        processed_prompt = processed_prompt.replace(
            sub["placeholder"], sub["replacement"], 1
        )

    # If the processed prompt is within limits, return it as a single-item list
    if len(processed_prompt) <= max_length:
        return [processed_prompt]

    # Otherwise, find the longest substitution to split
    if not substitutions:
        # If no substitutions but still too long, simply truncate
        return [processed_prompt[:max_length]]

    # Find the longest substitution
    longest_sub = max(substitutions, key=lambda x: x["length"])

    if longest_sub["length"] <= overlap:
        # If even the longest substitution is too short to split meaningfully,
        # truncate the result
        return [processed_prompt[:max_length]]

    # Split the longest substitution
    original_text = longest_sub["replacement"]
    split_point = len(original_text) // 2

    # Ensure the split point provides proper overlap
    part1 = original_text[: split_point + overlap]
    part2 = original_text[split_point:]

    # Create two new data stores with the split substitution
    new_prompts = []

    # For each split part, create a new prompt
    for _, part in enumerate([part1, part2]):
        # Create a copy of the data store with the modified substitution
        temp_data_store = dict(ctx.data_store)
        temp_data_store[longest_sub["key"]] = part

        # Create a temporary data context
        original_data_store = ctx.data_store
        ctx.data_store = temp_data_store

        # Recursively process with the updated substitution
        split_results = preprocess_prompt(prompt, ctx, max_length, escape, overlap)
        new_prompts.extend(split_results)

        # Restore original data store
        ctx.data_store = original_data_store

    return new_prompts


def get_text_from_prompt(prompt, system, ctx, model_data):
    if prompt.startswith("#py"):
        prompt = prompt[3:]
        if prompt.startswith("#python"):
            prompt = prompt[7:]

        full_prompt = preprocess_prompt(
            prompt, ctx, escape=True, max_length=sys.maxsize
        )
        result = prompt
        full_prompt = full_prompt[0]

        try:
            result = str(eval(full_prompt))
        except Exception as e:
            print("Error processing python prompt")
            print(e)
            log_traceback(model_data.get("error_file", "error.log"))

        result = " ".join(result.split())
        return result

    # special case to indicate that the prompt should be generated but not processed
    # i.e., for retrieving variables or direct quotes from the input file
    if prompt.startswith("#"):
        full_prompt = preprocess_prompt(prompt, ctx, max_length=sys.maxsize)
        full_prompt = full_prompt[0]
        # more special case to call a script
        if prompt.startswith("#!"):
            full_prompt = full_prompt[0]
            params = full_prompt[2:].split(" ", 1)

            script_folder = model_data.get("script_folder", "scripts")

            exe = os.path.join(script_folder, params[0])
            params = params[1]
            result = subprocess.run(
                [exe, params], shell=True, text=True, capture_output=True
            )
            if result.returncode != 0:
                ctx.script_returncode = result.returncode

            result = result.stdout

        else:
            result = full_prompt[1:]
    else:
        full_prompt = preprocess_prompt(prompt, ctx)
        results = []
        for pr in full_prompt:
            results.append(ctx.llm_engine.prompt(pr, system))
        result = " ".join(results)

    # remove characters that are not printable, including newlines and tabs
    result = " ".join(result.split())

    return result


def process_line(line, ctx, model_data):
    system = line["system"]

    name = line["name"]
    if len(name) == 0 and len(line["prompts"]) == 0:
        return ctx.data_store["reply"]

    preCheck = None
    result = None
    if line["skipTest"]:
        preCheck = line["skipPrompt"]

        preCheckResult = get_text_from_prompt(
            preCheck, ctx.precheck_system, ctx, model_data
        )
        preCheckTest = line["skipTest"].split()
        param = preCheckTest[1] if len(preCheckTest) > 1 else ""

        preCheckTest = preCheckTest[0]

        preCheckTestFunction = prechecks.get(preCheckTest, u.isYes)

        # if the answer is yes, then we jump to the next stage
        # If no, we will use this prompt

        if preCheckTestFunction(preCheckResult, param):
            #    print("Skipping",preCheckTest)
            return ctx.data_store["reply"]

    for prompt in line["prompts"]:
        result = get_text_from_prompt(prompt, system, ctx, model_data)

        if result.lower() == "!cancel!":
            print("cancelled")
            return None

        ctx.data_store["reply"] = result
        ctx.reply_count += 1
        ctx.data_store[f"reply_{ctx.reply_count}"] = result

    if result:
        ctx.data_store["reply"] = result
        ctx.data_store[name] = result

        if line["dataOut"]:

            ctx.output_data[name] = result

            if name not in ctx.ordered_column_list:
                ctx.ordered_column_list.append(name)
    else:
        print("No result for", name)

    #    print(f"{name}: {result}")
    return result


def process_document(pmid, document_data, ctx, model_data, parser):
    try:
        text = document_data["text"]
        sections = document_data["sections"]

        result = None
        ctx.reply_count = 0
        ctx.output_data = {}
        ctx.data_store = {"paper": text}
        ctx.data_store["cancel"] = "!cancel!"

        for section in sections:
            ctx.data_store[section] = sections[section]

        for m in model_data.data:
            if m.startswith("["):
                variable = m[1:-1]
                ctx.data_store[variable] = model_data.get(m)

        print(f"Processing {pmid}")
        prompt_data = parser.get_prompt_data()

        for process in prompt_data:

            result = process_line(process, ctx, model_data)

            if result is None:
                break

        if result is not None:
            result = ctx.output_data.copy()
        ctx.debug[pmid] = ctx.data_store.copy()

        return result

    except Exception as e:
        print(f"Error processing document {pmid}: {e}")
        log_traceback(model_data.get("error_file", "error.log"))
        return None


def get_pubmed_from_local(pubmed_id, model_data):
    script_path = model_data.get("get_pubmed_path")

    # call an external script to get the data, passing in the pubmed id
    data = []
    try:
        data = subprocess.check_output([script_path, pubmed_id])
        data = json.loads(data)
    except subprocess.CalledProcessError as e:
        print("Error", e)

    return data


def get_text_from_local(filename, ctx):
    filename = os.path.join(ctx.data_folder, filename)

    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")

    if filename.lower().endswith(".pdf"):
        try:
            from pdfminer.high_level import extract_text

            all_text = extract_text(filename)
        except Exception as e:
            print(
                "Error processing pdf - pfminder.six must be installed, or use text or json files"
            )
            print(e)
            log_traceback()

    elif filename.lower().endswith(".json"):
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            all_text = ""
            if "text" in data:
                all_text = data["text"]
            elif "sections" in data:
                for section in data["sections"]:
                    all_text += data["sections"][section] + "\n"

            if "sections" in data:
                data = {"text": all_text, "sections": data["sections"]}
                return data

    else:
        with open(filename, "r", encoding="utf-8", errors="ignore") as file:

            print("read", filename)
            all_text = file.read()

    data = {"text": all_text, "sections": {"paper": all_text}}

    return data


def get_pubmed_from_api(pubmed_id, model_data):
    try:
        import requests
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "To use an External PubMed API, requests must be installed."
        ) from e
    api_url = (
        "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/"
        + str(pubmed_id)
        + "/unicode"
    )
    if "pubmed_url" in model_data.data:
        api_url = model_data.get("pubmed_url") + str(pubmed_id) + "/unicode"

    data = []
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        data = response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")

    return data


# Function to fetch PubMed data via API or from a local file
def fetch_pubmed_data(pubmed_id, sections_to_extract, data_folder, ctx, model_data):
    # if it is numberical or a PMC id, then we assume it is pubmed
    # otherwise we assume it is a local file

    is_pubmed = pubmed_id.isnumeric() or (
        pubmed_id[:3] == "PMC" and pubmed_id[3:].isnumeric()
    )

    json_file_path = os.path.join(data_folder, f"{pubmed_id}.json")

    # Check if the JSON file already exists, to cache it
    if os.path.exists(json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    else:

        if is_pubmed:

            # Fetch the data from PubMed API (alternative is a local script)
            if ctx.use_pubmed_api:
                data = get_pubmed_from_api(pubmed_id, model_data)
            else:
                data = get_pubmed_from_local(pubmed_id, model_data)
        else:
            data = get_text_from_local(pubmed_id, ctx)

        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    # Extract the relevant sections from the JSON data
    if is_pubmed:
        parsed_data = parse_pubmed_data(data, sections_to_extract)
    else:
        parsed_data = data

    return parsed_data


# Function to process each PubMed ID
def process_pubmed_id(
    pubmed_id,
    processed_documents,
    sections_to_extract,
    data_folder,
    ctx,
    model_data,
    parser,
):
    document_data = fetch_pubmed_data(
        pubmed_id, sections_to_extract, data_folder, ctx, model_data
    )
    document_text = document_data.get("text")

    print("got text", pubmed_id, len(document_text))
    # print(document_text
    if len(document_text) > ctx.max_doc_length:
        print("document too long")
        return

    if document_text:
        if len(document_text) > 1:
            processed_documents.append(document_text)
            result = process_document(pubmed_id, document_data, ctx, model_data, parser)
            if result:
                ctx.final_output[pubmed_id] = result


def output_csv_old(output_data, outputfile, ctx):
    columns = set()
    for key in output_data:
        columns.update(output_data[key].keys())

    # Convert the set to a sorted list to maintain column order
    columns = sorted(columns)
    column_name = ctx.column_name
    # Step 2: Write to CSV
    with open(outputfile, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=[column_name] + columns, quoting=csv.QUOTE_ALL
        )
        writer.writeheader()

        # Step 3: Write data rows
        for key, values in output_data.items():
            row = {column_name: key}  # Start row with the main key
            row.update(values)  # Update the row with the nested dictionary
            normalized_row = {k: normalize_newlines(v) for k, v in row.items()}

            writer.writerow(normalized_row)


def output_csv(output_data, outputfile, ctx):
    columns = set()
    # column_name is the global for the key of the dictionary
    column_name = ctx.column_name
    # Collect all possible columns from the nested dictionaries
    for key in output_data:
        columns.update(output_data[key].keys())

    # Ensure columns appear in the specified order, filtering only those present in output_data
    ordered_columns = [col for col in ctx.ordered_column_list if col in columns]
    extra_columns = sorted(
        columns - set(ctx.ordered_column_list)
    )  # Additional columns in sorted order
    final_columns = ordered_columns + extra_columns  # Merge ordered and extra columns

    # Prepend the 'id' column for the key
    header = [column_name] + final_columns

    with open(outputfile, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        # Write data rows: add the key as the 'id' field for each row
        for key, values in output_data.items():
            row = {column_name: key}
            row.update(values)
            normalized_row = {k: normalize_newlines(v) for k, v in row.items()}
            writer.writerow(normalized_row)


def save_output(data, csv_file, json_file, ctx, model_data):
    try:
        output_csv(data, csv_file, ctx)
    except Exception as e:
        print("error", csv_file)
        print(e)
        log_traceback(model_data.get("error_file", "error.log"))

    try:
        with open(json_file, "w", encoding="utf-8") as json_out:
            json.dump(data, json_out, indent=4)
    except Exception as e:

        print("error", json_file)
        print(e)
        log_traceback(model_data.get("error_file", "error.log"))


NEWLINE_CHARS = [
    "\r\n",  # CRLF
    "\r",  # CR
    "\n",  # LF
    "\f",  # FORM FEED
    "\v",  # VERTICAL TAB
    "\u0085",  # NEXT LINE
    "\u2028",  # LINE SEPARATOR
    "\u2029",  # PARAGRAPH SEPARATOR
]
newline_re = re.compile("|".join(map(re.escape, NEWLINE_CHARS)))


def normalize_newlines(text, max_len=10000):
    if not isinstance(text, str):
        return text

    text = text[:max_len]
    text = text.replace('"', "")
    return newline_re.sub(r" \n ", text)
