#!/usr/bin/env python3

import os
import json
import requests
import yaml
from pathlib import Path
from typing import Dict, Any
from typing import List, Tuple
from helpers.run_completion import run_completion

model = None
# model = "anthropic/claude-3.5-sonnet"


def find_notebooks(base_dir: str) -> List[Tuple[str, str]]:
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

            # Check for matching notebook
            notebook_name = f"{dandiset_id}.ipynb"
            notebook_path = os.path.join(subfolder_path, notebook_name)
            if os.path.isfile(notebook_path):
                notebook_paths.append((dandiset_id, notebook_path))

    return notebook_paths


def read_rate_system_prompt() -> str:
    """Read and process the system prompt template."""
    template_path = Path(__file__).parent / "templates" / "rate_system_prompt.txt"
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


def parse_assistant_response(assistant_response: str) -> Dict[str, Any]:
    ind1 = assistant_response.find("<notebook_rater>")
    ind2 = assistant_response.find("</notebook_rater>")
    if ind1 == -1 or ind2 == -1:
        raise ValueError("Invalid assistant response format")
    ind1 += len("<notebook_rater>")
    content = assistant_response[ind1:ind2]
    thinking_ind1 = content.find("<thinking>")
    thinking_ind2 = content.find("</thinking>")
    if thinking_ind1 == -1 or thinking_ind2 == -1:
        raise ValueError("Invalid assistant response format")
    thinking_ind1 += len("<thinking>")
    thinking = content[thinking_ind1:thinking_ind2].strip()
    score_ind1 = content.find("<score>")
    score_ind2 = content.find("</score>")
    if score_ind1 == -1 or score_ind2 == -1:
        raise ValueError("Invalid assistant response format")
    score_ind1 += len("<score>")
    score = content[score_ind1:score_ind2].strip()
    try:
        score = float(score)
    except ValueError:
        raise ValueError("Invalid score format")
    return {"thinking": thinking, "score": score}


def rate_notebook(
    *,
    notebook_path_or_url: str,
    model: str | None = None,
    existing_ratings: dict | None = None,
):
    num_repeats = 3

    # load questions
    with open("rubric.yml", "r") as f:
        questions = yaml.safe_load(f)

    assert "questions" in questions, "questions.yaml must contain a 'questions' key"
    for question in questions["questions"]:
        assert "name" in question, "Each question must have a 'name' key"
        assert "version" in question, "Each question must have a 'version' key"
        assert "question" in question, "Each question must have a 'question' key"
        assert "rubric" in question, "Each question must have a 'rubric' key"
        for rub in question["rubric"]:
            assert "score" in rub, "Each rubric must have a 'score' key"
            assert "description" in rub, "Each rubric must have a 'description' key"

    if not model:
        model = "google/gemini-2.0-flash-001"

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

    new_result = {
        "notebook": notebook_path_or_url,
        "dandiset_id": notebook_path_or_url.split("/")[-3],
        "subfolder": notebook_path_or_url.split("/")[-2],
        "overall_score": 0,
        "scores": []
    }
    if metadata:
        new_result["metadata"] = metadata

    for question in questions["questions"]:
        existing_score = None
        if existing_ratings is not None:
            for existing_score0 in existing_ratings["scores"]:
                if (
                    existing_score0["name"] == question["name"]
                    and existing_score0["version"] == question["version"]
                ):
                    if len(existing_score0["reps"]) == num_repeats:
                        existing_score = existing_score0
                        print(
                            f"Found existing score for question {question['name']} version {question['version']}: {existing_score0['score']}"
                        )
                        break
                    else:
                        print(
                            f"Found existing score for question {question['name']} version {question['version']}, but it has {len(existing_score0['reps'])} repetitions. Repeating the question."
                        )
        if existing_score:
            new_result["scores"].append(existing_score)
            print(
                f"Skipping question {question['name']} version {question['version']} as it already exists in the results."
            )
            continue

        reps = []
        for repnum in range(num_repeats):
            system_prompt = read_rate_system_prompt()
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": system_prompt}
            ]
            for cell in cells:
                content = create_user_message_content_for_cell(cell)
                messages.append({"role": "system", "content": content})

            user_message = f"Please rate the notebook based on the following question: {question['question']}\n\n"
            user_message += f"Rubric:\n"
            for rub in question["rubric"]:
                user_message += f"- {rub['score']}: {rub['description']}\n"
            user_message += """
    Remember that your output should be in the following format:

    <notebook_rater>
        <thinking>Your reasoning for the score</thinking>
        <score>numeric_score</score>
    </notebook_rater>
    """
            messages.append({"role": "user", "content": user_message})
            print(
                f"Rating question {question['name']} version {question['version']} Repetition {repnum + 1}/{num_repeats}"
            )
            print(question["question"])
            assistant_response, _, prompt_tokens, completion_tokens = run_completion(
                messages=messages, model=model
            )
            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens

            print(assistant_response)
            print(
                f"Prompt tokens: {total_prompt_tokens}, Completion tokens: {total_completion_tokens}"
            )

            a = parse_assistant_response(assistant_response)
            reps.append(
                {"score": a["score"], "thinking": a["thinking"], "repnum": repnum}
            )
        average_score = sum([rep["score"] for rep in reps]) / len(reps)
        print(f"Score: {average_score} : {[rep['score'] for rep in reps]}")
        new_result["scores"].append(
            {
                "name": question["name"],
                "version": question["version"],
                "score": average_score,
                "reps": reps,
            }
        )

    print("")
    # Print a summary of all the scores
    for question in new_result["scores"]:
        print(question["name"])
        print(f"{question['score']:.2f} {[rep['score'] for rep in question['reps']]}")
        print("")

    # Fill in the overall score
    new_result["overall_score"] = sum(
        [question["score"] for question in new_result["scores"]]
    )

    # Report number of tokens used
    print(f"Total prompt tokens: {total_prompt_tokens}")
    print(f"Total completion tokens: {total_completion_tokens}")

    return new_result, total_prompt_tokens, total_completion_tokens


def main():
    # Find all matching notebooks
    notebooks = find_notebooks("dandisets")
    print(f"Found {len(notebooks)} notebooks to process")

    ratings_fname = "ratings.json"
    if os.path.exists(ratings_fname):
        with open(ratings_fname, "r") as f:
            ratings = json.load(f)
    else:
        ratings = []

    total_prompt_tokens = 0
    total_completion_tokens = 0

    # Process each notebook
    for i, (dandiset_id, notebook_path) in enumerate(notebooks, 1):
        print(f"\nProcessing notebook {i}/{len(notebooks)}")
        print(f"Dandiset: {dandiset_id}")
        print(f"Path: {notebook_path}")

        existing_notebook_rating = None
        for rating in ratings:
            if rating["notebook"] == notebook_path:
                existing_notebook_rating = rating
                break

        try:
            new_rating, prompt_tokens, completion_tokens = rate_notebook(
                notebook_path_or_url=notebook_path,
                model=model,
                existing_ratings=existing_notebook_rating,
            )
            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens
            # replace rating in ratings
            if existing_notebook_rating is not None:
                ratings.remove(existing_notebook_rating)
            ratings.append(new_rating)
            # sort ratingss
            ratings.sort(key=lambda x: x["notebook"])
            # save ratings
            with open(ratings_fname, "w") as f:
                json.dump(ratings, f, indent=2)
            print(f"Rating saved for {notebook_path}")
            print(f"Total prompt tokens: {total_prompt_tokens}")
            print(f"Total completion tokens: {total_completion_tokens}")
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error processing {notebook_path}: {e}")

        # # Skip the pause after the last notebook
        # if i < len(notebooks):
        #     input("\nPress Enter to continue to next notebook...")
        print("")
        print("")


if __name__ == "__main__":
    main()
