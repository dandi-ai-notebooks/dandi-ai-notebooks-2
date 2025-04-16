#!/usr/bin/env python3

import os
import json
import requests
from pathlib import Path
from typing import Dict, Any
from typing import List, Tuple
import re
from helpers.run_completion import run_completion

prompt_version = '1'

model_for_cells = "google/gemini-2.0-flash-001"
model_for_summary = "anthropic/claude-3.7-sonnet"

def find_notebooks(base_dir: str, *, prefix: str) -> List[Tuple[str, str]]:
    """Find notebooks matching the pattern dandisets/<DANDISET_ID>/subfolder/<DANDISET_ID>.ipynb."""
    notebook_paths = []

    # List dandiset directories
    for dandiset_id in os.listdir(base_dir):
        dandiset_path = os.path.join(base_dir, dandiset_id)
        if not os.path.isdir(dandiset_path):
            continue

        # List subdirectories within dandiset
        for subfolder in os.listdir(dandiset_path):
            subfolder_path = os.path.join(dandiset_path, subfolder)
            if not os.path.isdir(subfolder_path):
                continue

            dirname = subfolder_path.split("/")[-1]
            if not dirname.startswith(prefix):
                continue

            # Check for matching notebook
            notebook_name = f"{dandiset_id}.ipynb"
            notebook_path = os.path.join(subfolder_path, notebook_name)
            if os.path.isfile(notebook_path):
                notebook_paths.append((dandiset_id, notebook_path))

    return notebook_paths

def read_notebook_critic_system_prompt() -> str:
    """Read and process the system prompt template."""
    template_path = Path(__file__).parent / "templates" / "notebook_critic_system_prompt.txt"
    with open(template_path, "r") as f:
        content = f.read()
    return content

def read_notebook_critic_summary_system_prompt() -> str:
    """Read and process the summary system prompt template."""
    template_path = Path(__file__).parent / "templates" / "notebook_critic_summary_system_prompt.txt"
    with open(template_path, "r") as f:
        content = f.read()
    return content

def create_user_message_content_for_cell(cell: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create user message content for a given cell."""
    content: List[Dict[str, Any]] = []
    if cell["cell_type"] == "markdown":
        markdown_source = cell["source"]
        content.append(
            {"type": "text", "text": "INPUT-MARKDOWN: " + "".join(markdown_source)}
        )
    elif cell["cell_type"] == "code":
        code_source = cell["source"]
        content.append({"type": "text", "text": "INPUT-CODE: " + "".join(code_source)})
        for x in cell["outputs"]:
            output_type = x["output_type"]
            if output_type == "stream":
                content.append(
                    {"type": "text", "text": "OUTPUT-TEXT: " + "\n".join(x["text"])}
                )
            elif output_type == "display_data" or output_type == "execute_result":
                if "image/png" in x["data"]:
                    png_base64 = x["data"]["image/png"]
                    image_data_url = f"data:image/png;base64,{png_base64}"
                    content.append(
                        {"type": "image_url", "image_url": {"url": image_data_url}}
                    )
                elif "text/plain" in x["data"]:
                    content.append(
                        {
                            "type": "text",
                            "text": "OUTPUT-TEXT: " + "".join(x["data"]["text/plain"]),
                        }
                    )
                elif "text/html" in x["data"]:
                    content.append(
                        {
                            "type": "text",
                            "text": "OUTPUT-HTML: " + "".join(x["data"]["text/html"]),
                        }
                    )
                else:
                    print(
                        f"Warning: got output type {output_type} but no image/png data or text/plain or text/html"
                    )
            else:
                print(f"Warning: unsupported output type {output_type}")
    else:
        print(f'Warning: unsupported cell type {cell["cell_type"]}')
        content.append({"type": "text", "text": "Unsupported cell type"})
    return content

def critique_notebook(*,
    notebook_path_or_url: str
):
    # If it's a notebook in a GitHub repo then translate the notebook URL to raw URL
    if notebook_path_or_url.startswith("https://github.com/"):
        notebook_path_or_url = notebook_path_or_url.replace(
            "github.com", "raw.githubusercontent.com"
        ).replace("/blob/", "/")

    # If notebook_path_or_url is a URL, download the notebook and read it as JSON
    # otherwise, read the file directly
    if notebook_path_or_url.startswith("http://") or notebook_path_or_url.startswith(
        "https://"
    ):
        response = requests.get(notebook_path_or_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download notebook from {notebook_path_or_url}")
        notebook_content = response.content.decode("utf-8")
        notebook = json.loads(notebook_content)
    else:
        with open(notebook_path_or_url, "r") as f:
            notebook_content = f.read()
        notebook = json.loads(notebook_content)

    if not "cells" in notebook:
        raise Exception(f"Invalid notebook format. No cells found in the notebook.")

    total_prompt_tokens = 0
    total_completion_tokens = 0
    cells = notebook["cells"]

    # get metadata from metadata.json
    notebook_parent_path = os.path.dirname(notebook_path_or_url)
    metadata_path = os.path.join(notebook_parent_path, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    else:
        metadata = None

    result = {
        "notebook": notebook_path_or_url,
        "dandiset_id": notebook_path_or_url.split("/")[-3],
        "subfolder": notebook_path_or_url.split("/")[-2],
        "prompt_version": prompt_version,
        "cell_critiques": []
    }
    if metadata:
        result["metadata"] = metadata

    print(f"Critiquing notebook {notebook_path_or_url}")
    system_prompt = read_notebook_critic_system_prompt()
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]
    for i, cell in enumerate(cells):
        print(f'Processing cell {i + 1}/{len(cells)}')
        print("==================")
        content = create_user_message_content_for_cell(cell)
        messages.append(
            {
                "role": "user",
                "content": content
            }
        )
        assistant_response, new_messagse, prompt_tokens, completion_tokens = run_completion(
            messages=messages, model=model_for_cells
        )

        result["cell_critiques"].append(assistant_response)
        print(assistant_response)
        print("")

        messages = new_messagse
        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens

    return result, total_prompt_tokens, total_completion_tokens

def get_summary_critique(cell_critiques: List[Dict[str, Any]]) -> Tuple[str, int, int]:
    """Get summary critique for the notebook."""
    system_prompt = read_notebook_critic_summary_system_prompt()
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]
    user_message = 'Here are the cell critiques for the notebook:\n\n'
    for i, cell_critique in enumerate(cell_critiques):
        user_message += f'Cell {i + 1}:\n\n'
        user_message += f'{cell_critique}\n\n'
    user_message += 'Please summarize the critiques as you were instructed.\n\n'
    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )
    assistant_response, _, prompt_tokens, completion_tokens = run_completion(
        messages=messages, model=model_for_summary
    )
    print(assistant_response)
    print("")
    return assistant_response, prompt_tokens, completion_tokens

def do_cell_critiques():
    notebooks = find_notebooks("dandisets", prefix="2025-04-16")
    print(f"Found {len(notebooks)} notebooks to process")

    critiques_fname = Path(__file__).parent / "notebook_critiques.json"
    if os.path.exists(critiques_fname):
        with open(critiques_fname, "r") as f:
            critiques = json.load(f)
    else:
        critiques = []

    total_prompt_tokens = 0
    total_completion_tokens = 0

    # Do the cell critiques
    for i, (dandiset_id, notebook_path) in enumerate(notebooks, 1):
        print(f"\nProcessing notebook {i}/{len(notebooks)}")
        print(f"Dandiset: {dandiset_id}")
        print(f"Path: {notebook_path}")

        existing_notebook_critique = None
        for critique in critiques:
            if critique["notebook"] == notebook_path:
                if critique["prompt_version"] == prompt_version:
                    existing_notebook_critique = critique
                    break

        if existing_notebook_critique:
            print("Notebook already critiqued, skipping...")
            continue

        new_critique, prompt_tokens, completion_tokens = critique_notebook(
            notebook_path_or_url=notebook_path
        )
        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens
        critiques = [cc for cc in critiques if cc["notebook"] != notebook_path]
        critiques.append(new_critique)
        critiques.sort(key=lambda x: x["notebook"])
        with open(critiques_fname, "w") as f:
            json.dump(critiques, f, indent=2)
        print(f"Critiques saved to {critiques_fname}")
        print(f"Total prompt tokens: {total_prompt_tokens}")
        print(f"Total completion tokens: {total_completion_tokens}")


def do_summary_critiques():
    notebooks = find_notebooks("dandisets", prefix="2025-04-16")
    print(f"Found {len(notebooks)} notebooks to process")

    critiques_fname = Path(__file__).parent / "notebook_critiques.json"
    if os.path.exists(critiques_fname):
        with open(critiques_fname, "r") as f:
            critiques = json.load(f)
    else:
        critiques = []

    total_prompt_tokens = 0
    total_completion_tokens = 0

    # do the summary critiques
    for i, (dandiset_id, notebook_path) in enumerate(notebooks, 1):
        print(f"\nProcessing notebook {i}/{len(notebooks)}")
        print(f"Dandiset: {dandiset_id}")
        print(f"Path: {notebook_path}")

        existing_notebook_critique = None
        for critique in critiques:
            if critique["notebook"] == notebook_path:
                if critique["prompt_version"] == prompt_version:
                    existing_notebook_critique = critique
                    break

        if not existing_notebook_critique:
            print("Notebook not critiqued, skipping...")
            continue

        if not existing_notebook_critique.get("summary_critique"):
            summary_critique, prompt_tokens, completion_tokens = get_summary_critique(
                existing_notebook_critique.get("cell_critiques")
            )
            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens
            existing_notebook_critique["summary_critique"] = summary_critique
            with open(critiques_fname, "w") as f:
                json.dump(critiques, f, indent=2)
            print(f"Critiques saved to {critiques_fname}")
            print(f"Total prompt tokens: {total_prompt_tokens}")
            print(f"Total completion tokens: {total_completion_tokens}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2 or sys.argv[1] not in ["cells", "summaries"]:
        print("Usage: python critique_notebooks.py <cells|summaries>")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "cells":
        do_cell_critiques()
    else:
        do_summary_critiques()
