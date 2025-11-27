import csv
import os


class ModelDataLoader:
    def __init__(self):
        self.data = {}

    def process_rows(self, rows):
        for row in rows:
            # Convert the first cellt os tring, handling None case
            first_cell = str(row[0]).strip() if row[0] is not None else ""

            # Skip empty rows or rows with empty first cell
            if not row or first_cell == "":
                continue

            key = first_cell

            # Convert all other cells to strings, handling None case
            values = []
            for item in row[1:]:
                item_str = str(item).strip() if item is not None else ""
                if item_str:  # Only add non-empty strings
                    values.append(item_str)

            self.data[key] = values[0] if len(values) == 1 else values

    def load_model_data(self, filename):
        self.data["config_root"] = os.path.dirname(filename)

        if filename.lower().endswith(".csv"):
            with open(filename, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                self.process_rows(reader)
        elif filename.lower().endswith(".xlsx"):
            try:
                import openpyxl
            except ModuleNotFoundError as e:
                raise RuntimeError(
                    "To use an Excel file openpyxl must be installed.  csv files need no other libraries."
                ) from e
            wb = openpyxl.load_workbook(filename, data_only=True)
            sheet = wb.active
            self.process_rows(sheet.iter_rows(values_only=True))

    def resolve_path(self, path):
        """Convert relative paths to absolute, based on working directory."""
        if not os.path.isabs(path):
            return os.path.join(self.get("config_root"), path)
        return path

    def get(self, field, default=None):
        return self.data.get(field, default)
