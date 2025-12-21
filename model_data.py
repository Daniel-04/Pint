from pathlib import Path
import csv
import json
from typing import Dict, Any, Union, List


class ModelDataLoader:
    def __init__(self):
        self.data = {}
        self.config_root = Path.cwd()

    def load_model_data(self, filename: Union[str, Path]) -> None:
        path = Path(filename).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {filename}")

        self.config_root = path.parent
        self.data["config_root"] = str(self.config_root)

        if path.suffix.lower() == ".csv":
            self.load_csv(path)
        elif path.suffix.lower() == ".xlsx":
            self.load_xlsx(path)
        elif path.suffix.lower() == ".json":
            self.load_json(path)
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")

    def load_csv(self, path: Path) -> None:
        try:
            with open(path, "r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                self.process_rows(reader)
        except Exception as e:
            raise RuntimeError(f"Error reading CSV config file {path}: {e}") from e

    def load_xlsx(self, path: Path) -> None:
        try:
            import openpyxl
        except ModuleNotFoundError as e:
            raise RuntimeError(
                "To use an Excel file openpyxl must be installed.  csv files need no other libraries."
            ) from e
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb.active
            self.process_rows(sheet.iter_rows(values_only=True))
        except Exception as e:
            raise RuntimeError(f"Error reading XLSX config file {path}: {e}") from e

    def load_json(self, path: Path) -> None:
        try:
            with open(path, "r", newline="", encoding="utf-8") as file:
                data = json.load(file)

                if not isinstance(data, dict):
                    raise ValueError("Config must be a JSON object (key-value mapping)")

                rows = []
                for key, value in data.items():
                    if isinstance(value, list):
                        rows.append([key, *value])
                    else:
                        rows.append([key, value])

                self.process_rows(rows)
        except Exception as e:
            raise RuntimeError(f"Error reading JSON config file {path}: {e}") from e

    def process_rows(self, rows: List[Any]) -> None:
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

            if key.lower().endswith(("folder", "root", "path", "file")):
                values = [self.resolve_path(v) for v in values]

            self.data[key] = values[0] if len(values) == 1 else values

    def resolve_path(self, path: Union[str, Path]) -> str:
        """Convert relative paths to absolute, based on working directory."""
        p = Path(path)
        if not p.is_absolute():
            p = Path(self.get("config_root")) / p
        return str(p.resolve())

    def get(self, field: str, default: Any = None) -> Any:
        return self.data.get(field, default)
