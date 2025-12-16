import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import csv
import shlex
import json
import re

PAD_X = 10
PAD_Y = 2

config = {}
prompts = {}


def isYes(answer):
    pattern = re.compile(r"^\s*[^\w_]*?(?:y(?:es)?|t(?:rue)?|1)\b", re.IGNORECASE)
    return bool(pattern.search(answer))


def labeled_checkbutton(parent, label, default=False):
    frame = ttk.Frame(parent)
    frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

    ttk.Label(frame, text=label, width=20, anchor="w").pack(side="left")

    var = tk.BooleanVar(value=default)
    entry = ttk.Checkbutton(frame, variable=var)
    entry.pack(side="right")

    config[label] = var

    return entry


def labeled_entry(parent, label, default=""):
    frame = ttk.Frame(parent)
    frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

    ttk.Label(frame, text=label, width=20, anchor="w").pack(side="left")

    var = tk.StringVar(value=default)
    entry = ttk.Entry(frame, textvariable=var)
    entry.pack(side="right", fill="x", expand=True)

    config[label] = var

    return entry


def add_config_row(parent, key="", value=""):
    frame = ttk.Frame(parent)
    frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

    key_var = tk.StringVar(value=key)
    val_var = tk.StringVar(value=value)

    key_entry = ttk.Entry(frame, textvariable=key_var, width=20)
    key_entry.grid(row=0, column=0, sticky="w", padx=(0, PAD_X))

    val_entry = ttk.Entry(frame, textvariable=val_var)
    val_entry.grid(row=0, column=1, sticky="ew")

    delete_btn = ttk.Button(frame, text="-", width=2)
    delete_btn.grid(row=0, column=2)

    frame.columnconfigure(1, weight=1)

    def sync_key(*_):
        old_keys = list(config.keys())
        for k in old_keys:
            if config[k] is val_var:
                del config[k]

        if key_var.get():
            config[key_var.get()] = val_var

    def delete_row():
        for k, v in list(config.items()):
            if v is val_var:
                del config[k]

        frame.destroy()

    delete_btn.config(command=delete_row)

    key_var.trace_add("write", sync_key)

    if key:
        config[key] = val_var

    return frame


def add_prompt_row(parent, data=None):
    frame = ttk.Frame(parent)
    frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

    row_vars = {
        "Name": tk.StringVar(value=(data.get("Name") if data else "")),
        "System": tk.StringVar(value=(data.get("System") if data else "")),
        "includeOutput": tk.BooleanVar(
            value=(data.get("includeOutput") if data else False)
        ),
        "skipPrompt": tk.BooleanVar(value=(data.get("skipPrompt") if data else False)),
        "skipTest": tk.StringVar(value=(data.get("skipTest") if data else "")),
        "prompt": tk.StringVar(value=(data.get("prompt") if data else "")),
    }

    prompts[frame] = row_vars

    def delete_row():
        prompts.pop(frame, None)
        frame.destroy()

    entries = [
        ttk.Entry(frame, textvariable=row_vars["Name"], width=15),
        ttk.Entry(frame, textvariable=row_vars["System"], width=15),
        ttk.Checkbutton(frame, variable=row_vars["includeOutput"]),
        ttk.Checkbutton(frame, variable=row_vars["skipPrompt"]),
        ttk.Entry(frame, textvariable=row_vars["skipTest"], width=10),
        ttk.Entry(frame, textvariable=row_vars["prompt"], width=30),
        ttk.Button(frame, text="-", width=2, command=delete_row),
    ]

    for i, widget in enumerate(entries):
        widget.grid(row=0, column=i, sticky="ew")

    frame.columnconfigure(5, weight=1)


def create_scrollable_tab(parent):
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

    scrollable = ttk.Frame(canvas)
    scrollable.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<Enter>", lambda e: canvas.bind("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind("<MouseWheel>"))

    return scrollable


def create_tabs(parent):
    notebook = ttk.Notebook(parent)
    notebook.pack(fill="both", expand=True)

    config_tab = ttk.Frame(notebook)
    notebook.add(config_tab, text="Config")
    config_top = ttk.Frame(config_tab)
    config_top.pack(fill="x", pady=PAD_Y)
    scrollable_config = create_scrollable_tab(config_tab)

    prompts_tab = ttk.Frame(notebook)
    notebook.add(prompts_tab, text="Prompts")
    prompts_top = ttk.Frame(prompts_tab)
    prompts_top.pack(fill="x", pady=PAD_Y)
    scrollable_prompts = create_scrollable_tab(prompts_tab)

    return (scrollable_config, config_top), (scrollable_prompts, prompts_top)


def load_config(infile, parent):
    with open(infile, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if not row:
                continue

            key = row[0]
            values = row[1:]
            display_value = shlex.join(values)

            var = config.get(key)
            if var is None:
                add_config_row(parent, key, display_value)
                continue

            if isinstance(var, tk.BooleanVar):
                var.set(isYes(display_value))
            else:
                var.set(display_value)


def save_config(outfile):
    with open(outfile, "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        for key, widget in config.items():
            raw = str(widget.get())

            try:
                parsed = shlex.split(raw)
            except Exception as e:
                raise ValueError(f"Errr parsing value for key {key}: {e}")

            writer.writerow([key] + parsed)

def load_prompts(infile, parent):
    with open(infile, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for parts in reader:
            data = {
                "Name": (parts[0:1] or [""])[0],
                "System": (parts[1:2] or [""])[0],
                "includeOutput": isYes((parts[2:3] or ["False"])[0]),
                "skipPrompt": isYes((parts[3:4] or ["False"])[0]),
                "skipTest": (parts[4:5] or [""])[0],
                "prompt": shlex.join(parts[5:] or [""]),
            }
            add_prompt_row(parent, data)


def save_prompts(outfile):
    with open(outfile, "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        for row_vars in prompts.values():
            row = [
                row_vars["Name"].get(),
                row_vars["System"].get(),
                str(row_vars["includeOutput"].get()),
                str(row_vars["skipPrompt"].get()),
                row_vars["skipTest"].get(),
                *shlex.split(row_vars["prompt"].get()),
            ]
            writer.writerow(row)


def on_save(save_func):
    outfile = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if outfile:
        try:
            save_func(outfile)
            messagebox.showinfo("Success", f"Configuration saved to {outfile}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")


def on_load(load_func, parent):
    infile = filedialog.askopenfilename(
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if infile:
        try:
            load_func(infile, parent)
            messagebox.showinfo("Success", f"Configuration loaded from {infile}")
        except FileNotFoundError:
            messagebox.showinfo("Error", f"File {infile} not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")


def create_config_tab(parent, top):
    # loading and saving generated config files
    save_button = ttk.Button(top, text="Save", command=lambda: on_save(save_config))
    save_button.pack(side="left", padx=PAD_X)

    load_button = ttk.Button(
        top, text="Load", command=lambda: on_load(load_config, parent)
    )
    load_button.pack(side="left", padx=PAD_X)

    # toggles for:
    #   use_pubmed_search: False,
    #   use_pubmed_api: True
    use_pubmed_search_checkbox = labeled_checkbutton(parent, "use_pubmed_search")
    use_pubmed_api_checkbox = labeled_checkbutton(parent, "use_pubmed_api", True)

    # selection dropdown for:
    #   model: Calude, OpenAI, External
    model_var = tk.StringVar(value="OpenAI")

    model_frame = ttk.Frame(parent)
    model_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

    ttk.Label(model_frame, text="model", width=20, anchor="w").pack(side="left")

    model_menu = ttk.OptionMenu(
        model_frame,
        model_var,
        "Claude",
        "OpenAI",
        "External",
    )
    model_menu.pack(side="right", fill="x", expand=True)
    config["model"] = model_var

    # text input for:
    #   model_name: No default,
    #   documents_data: No default,
    #   column_name: filename,
    #   start_position: 0,
    #   prompt_data: No default,
    #   pubmed_url: No default,
    #   sections: No default,
    #   output_filename: output.csv,
    #   output_folder: output,
    #   files_folder: .,
    #   script_folder: scripts,
    #   data_cache_folder: cache/data,
    #   api_cache_folder: cache/api
    model_name_entry = labeled_entry(parent, "model_name")
    documents_data_entry = labeled_entry(parent, "documents_data")
    column_name_entry = labeled_entry(parent, "column_name", "filename")
    start_position_entry = labeled_entry(parent, "start_position", "0")
    prompt_data_entry = labeled_entry(parent, "prompt_data")
    pubmed_url_entry = labeled_entry(parent, "pubmed_url")
    sections_entry = labeled_entry(parent, "sections")
    output_filename_entry = labeled_entry(parent, "output_filename", "output.csv")
    output_folder_entry = labeled_entry(parent, "output_folder", "output")
    files_folder_entry = labeled_entry(parent, "files_folder", ".")
    script_folder_entry = labeled_entry(parent, "script_folder", "scripts")
    data_cache_folder_entry = labeled_entry(parent, "data_cache_folder", "cache/data")
    api_cache_folder_entry = labeled_entry(parent, "api_cache_folder", "cache/api")

    add_button = ttk.Button(
        parent,
        text="+ Add config entry",
        command=lambda: add_config_row(parent),
    )
    add_button.pack(pady=PAD_Y)


def create_prompts_tab(parent, top):
    buttons_frame = ttk.Frame(top)
    buttons_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

    save_button = ttk.Button(
        buttons_frame, text="Save", command=lambda: on_save(save_prompts)
    )
    save_button.pack(side="left", padx=PAD_X)

    load_button = ttk.Button(
        buttons_frame,
        text="Load",
        command=lambda: on_load(load_prompts, parent),
    )
    load_button.pack(side="left", padx=PAD_X)

    headers_frame = ttk.Frame(top)
    headers_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

    headers = [
        "Name",
        "System",
        "includeOutput",
        "skipPrompt",
        "skipTest",
        "prompt",
        "",
    ]
    for i, h in enumerate(headers):
        ttk.Label(headers_frame, text=h, width=15 if i < 6 else 2, anchor="w").grid(
            row=0, column=i, sticky="w"
        )

    add_prompt_btn = ttk.Button(
        parent,
        text="+ Add prompt",
        command=lambda: add_prompt_row(parent),
    )
    add_prompt_btn.pack(pady=PAD_Y)

    add_prompt_row(parent)


def main():
    root = tk.Tk()
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    root.title("Pint Config GUI")
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    (scrollable_config, config_top), (scrollable_prompts, prompts_top) = create_tabs(
        root
    )
    create_config_tab(scrollable_config, config_top)
    create_prompts_tab(scrollable_prompts, prompts_top)

    root.mainloop()


if __name__ == "__main__":
    main()
