#!/usr/bin/env python3

import os
import json
import base64
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
from helpers.run_completion import run_completion

model = None

def find_notebooks(base_dir: str) -> List[Tuple[str, str]]:
    """Find notebooks matching the pattern dandisets/<DANDISET_ID>/subfolder/<DANDISET_ID>.ipynb."""
    notebook_paths = []

    for dandiset_id in os.listdir(base_dir):
        dandiset_path = os.path.join(base_dir, dandiset_id)
        if not os.path.isdir(dandiset_path):
            continue

        for subfolder in os.listdir(dandiset_path):
            subfolder_path = os.path.join(dandiset_path, subfolder)
            if not os.path.isdir(subfolder_path):
                continue

            notebook_name = f"{dandiset_id}.ipynb"
            notebook_path = os.path.join(subfolder_path, notebook_name)
            if os.path.isfile(notebook_path):
                notebook_paths.append((dandiset_id, notebook_path))

    return notebook_paths

def read_plot_rate_system_prompt() -> str:
    """Read and process the plot rating system prompt template."""
    template_path = Path(__file__).parent / "templates" / "plot_rate_system_prompt.txt"
    with open(template_path, "r") as f:
        content = f.read()
    return content

def parse_assistant_response(assistant_response: str) -> Dict[str, Any]:
    """Parse the assistant's response into thinking and score."""
    ind1 = assistant_response.find("<plot_rater>")
    ind2 = assistant_response.find("</plot_rater>")
    if ind1 == -1 or ind2 == -1:
        raise ValueError("Invalid assistant response format")
    ind1 += len("<plot_rater>")
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

def rate_plot(
    *,
    image_data_url: str,
    question: Dict[str, Any],
    model: str | None = None,
    num_repeats: int = 3
) -> Dict[str, Any]:
    """Rate a single plot using the provided question and rubric."""
    if not model:
        model = "google/gemini-2.0-flash-001"

    system_prompt = read_plot_rate_system_prompt()
    reps = []

    for repnum in range(num_repeats):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": [{"type": "image_url", "image_url": {"url": image_data_url}}]}
        ]

        user_message = f"Please rate the plot based on the following question: {question['question']}\n\n"
        user_message += f"Rubric:\n"
        for rub in question["rubric"]:
            user_message += f"- {rub['score']}: {rub['description']}\n"
        user_message += """
Remember that your output should be in the following format:

<plot_rater>
    <thinking>Your reasoning for the score</thinking>
    <score>numeric_score</score>
</plot_rater>
"""
        messages.append({"role": "user", "content": user_message})

        assistant_response, _, _, _ = run_completion(messages=messages, model=model)

        a = parse_assistant_response(assistant_response)
        reps.append({
            "score": a["score"],
            "thinking": a["thinking"],
            "repnum": repnum
        })

    average_score = sum([rep["score"] for rep in reps]) / len(reps)
    return {
        "name": question["name"],
        "version": question["version"],
        "score": average_score,
        "reps": reps
    }

def rate_notebook_plots(
    *,
    notebook_path: str,
    model: str | None = None,
    existing_ratings: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Rate all plots in a notebook."""
    # load plot rating questions
    with open("plot_rubric.yml", "r") as f:
        questions = yaml.safe_load(f)

    # validate questions
    assert "questions" in questions, "plot_rubric.yml must contain a 'questions' key"
    for question in questions["questions"]:
        assert "name" in question, "Each question must have a 'name' key"
        assert "version" in question, "Each question must have a 'version' key"
        assert "question" in question, "Each question must have a 'question' key"
        assert "rubric" in question, "Each question must have a 'rubric' key"
        for rub in question["rubric"]:
            assert "score" in rub, "Each rubric must have a 'score' key"
            assert "description" in rub, "Each rubric must have a 'description' key"

    # Load notebook
    with open(notebook_path, "r") as f:
        notebook = json.load(f)

    if not "cells" in notebook:
        raise Exception("Invalid notebook format. No cells found.")

    # Initialize result structure
    result = {
        "notebook": notebook_path,
        "dandiset_id": notebook_path.split("/")[-3],
        "subfolder": notebook_path.split("/")[-2],
        "plots": []
    }

    # get metadata if exists
    notebook_parent_path = os.path.dirname(notebook_path)
    metadata_path = os.path.join(notebook_parent_path, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            result["metadata"] = json.load(f)

    plot_count = 0
    for cell_idx, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue

        for output_idx, output in enumerate(cell.get("outputs", [])):
            if output["output_type"] not in ["display_data", "execute_result"]:
                continue

            if "image/png" not in output["data"]:
                continue

            plot_count += 1
            plot_id = f"cell_{cell_idx}_output_{output_idx}"

            # Check if we already have ratings for this plot
            existing_plot_ratings = None
            if existing_ratings and "plots" in existing_ratings:
                for plot in existing_ratings["plots"]:
                    if plot["plot_id"] == plot_id:
                        existing_plot_ratings = plot
                        break

            # Create plot_images directory in the notebook's directory if it doesn't exist
            plot_images_dir = os.path.join(notebook_parent_path, "plot_images")
            os.makedirs(plot_images_dir, exist_ok=True)

            # Get the base64 data
            png_base64 = output["data"]["image/png"]

            # Save PNG file if it doesn't exist
            png_file = os.path.join(plot_images_dir, f"{plot_id}.png")
            if not os.path.exists(png_file):
                png_bytes = base64.b64decode(png_base64)
                with open(png_file, "wb") as f:
                    f.write(png_bytes)

            if existing_plot_ratings:
                result["plots"].append(existing_plot_ratings)
                print(f"Using existing ratings for plot {plot_id}")
                continue

            print(f"\nRating plot {plot_count} (ID: {plot_id})")

            # Create the plot ratings entry
            plot_entry = {
                "plot_id": plot_id,
                "cell_index": cell_idx,
                "output_index": output_idx,
                "scores": []
            }

            # Get the image data URL for rating
            image_data_url = f"data:image/png;base64,{png_base64}"

            # Rate the plot for each question
            for question in questions["questions"]:
                print(f"Rating question: {question['name']} version {question['version']}")
                score_result = rate_plot(
                    image_data_url=image_data_url,
                    question=question,
                    model=model
                )
                plot_entry["scores"].append(score_result)
                print(f"Score: {score_result['score']:.2f}")

            result["plots"].append(plot_entry)

    # Print summary
    print(f"\nProcessed {plot_count} plots in {notebook_path}")
    for plot in result["plots"]:
        print(f"\nPlot {plot['plot_id']}:")
        for score in plot["scores"]:
            print(f"{score['name']}: {score['score']:.2f}")

    return result

def main():
    notebooks = find_notebooks("dandisets")
    print(f"Found {len(notebooks)} notebooks to process")

    ratings_fname = "plot_ratings.json"
    if os.path.exists(ratings_fname):
        with open(ratings_fname, "r") as f:
            all_ratings = json.load(f)
    else:
        all_ratings = []

    for i, (dandiset_id, notebook_path) in enumerate(notebooks, 1):
        print(f"\nProcessing notebook {i}/{len(notebooks)}")
        print(f"Dandiset: {dandiset_id}")
        print(f"Path: {notebook_path}")

        existing_notebook_rating = None
        for rating in all_ratings:
            if rating["notebook"] == notebook_path:
                existing_notebook_rating = rating
                break

        try:
            new_rating = rate_notebook_plots(
                notebook_path=notebook_path,
                model=model,
                existing_ratings=existing_notebook_rating
            )

            # Replace or append the new rating
            if existing_notebook_rating:
                all_ratings.remove(existing_notebook_rating)
            all_ratings.append(new_rating)

            # Sort and save ratings
            all_ratings.sort(key=lambda x: x["notebook"])
            with open(ratings_fname, "w") as f:
                json.dump(all_ratings, f, indent=2)

            print(f"Ratings saved for {notebook_path}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error processing {notebook_path}: {e}")

        print("\n")

if __name__ == "__main__":
    main()
