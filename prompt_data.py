import csv

try:
    import openpyxl
except ImportError:
    print("To use an Excel file openpyxl must be installed.")


# parses the prompts spreadsheet into the data format already used
# see end of file for format description


def process_rows(rows, headers):
    prompts = []
    standard_fields = ["name", "system", "skipPrompt", "skipTest"]

    for row in rows:
        row_dict = {
            key: str(value) if value is not None else ""
            for key, value in zip(headers, row)
        }

        prompt_dict = {field: row_dict[field] for field in standard_fields}

        # Add derived fields
        prompt_dict["putVariable"] = prompt_dict["name"]
        prompt_dict["dataOut"] = False
        if "includeOutput" in row_dict and (
            row_dict["includeOutput"].strip().lower() == "true"
            or row_dict["includeOutput"].strip() == "1"
        ):
            prompt_dict["dataOut"] = True

        # Add prompts list (remaining non-empty values)

        prompt_dict["prompts"] = []
        # Iterate through the columns after "prompt" to get non-blank values
        i = headers.index("prompts")

        while i < len(row) and row[i]:  # Only add non-blank values
            prompt_dict["prompts"].append(row[i])
            i += 1

        prompts.append(prompt_dict)

    return prompts


def read_prompt_xlsx(file_path):
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active
    headers = [str(cell.value) for cell in sheet[1]]  # Ensure headers are strings
    rows = [
        [str(cell) if cell is not None else "" for cell in row]
        for row in sheet.iter_rows(min_row=2, values_only=True)
    ]

    return process_rows(rows, headers)


def read_prompt_tsv(file_path, delimiter="\t"):
    with open(file_path, newline="", encoding="utf-8") as tsvfile:
        reader = csv.reader(tsvfile, delimiter=delimiter)
        headers = [str(header) for header in next(reader)]  # Convert headers to strings
        rows = [
            [str(cell) if cell else "" for cell in row] for row in reader
        ]  # Convert all values to strings

    return process_rows(rows, headers)


def read_prompt(file_path):
    if file_path.lower().endswith(".xlsx"):
        return read_prompt_xlsx(file_path)
    if file_path.lower().endswith(".csv"):
        return read_prompt_tsv(file_path, delimiter=",")
    return read_prompt_tsv(file_path)


prompt_data = None


def load_prompt_data(model_data):
    global prompt_data
    prompt_data = model_data.resolve_path(model_data.get("prompt_data"))
    print("load prompts from", prompt_data)

    prompt_data = read_prompt(prompt_data)


def get_prompt_data():
    return prompt_data


# Define your prompting structure here:

# Functions are used to check if the process should terminate by checking the previous output
# Can also be used to amend the output


# a preCheck determines if the prompt should be run at all
# This is useful for prompts that are only relevant if a certain condition is met
# In this case, the prompt will skip the stage if it is already a number


# The name is used for debug purposes
# The list of prompts are called in sequence - the notation [reply] always refers to the previous output
# [paper] is a special variable that is always available, and refers to the original paper text
# Paper Sections can also be referred to by [section_name] e.g., [methods]

# Other variables can be set by 'putVariable', then referred to in later prompts
# The 'check' function is used to determine if the prompt should exit early
# The 'dataOut' variable is used to store the output of the prompt in the final data structure csv
# The 'hide' variable is just used to hide the I/O from the debug output, so there isn't too much text
