import os
import shutil
import time
import yaml
import json
import platform
from minicline import perform_task

def generate():
    working_dir = 'working'

    # if working dir exists, raise error
    if os.path.exists(working_dir):
        raise Exception(f"Working directory {working_dir} already exists. Please remove it before running the script.")

    # Create the working directory and copy files
    os.makedirs(working_dir, exist_ok=True)
    shutil.copy('tools.py', working_dir + '/tools.py')
    shutil.copy('tools_cli.py', working_dir + '/tools_cli.py')

    # Read config.yaml
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    model = config['model']
    prompt_fname = config['prompt'] + ".txt"
    dandiset_id = config['dandiset_id']

    # read the prompt
    with open(prompt_fname, 'r') as f:
        prompt = f.read()
    prompt = prompt.replace('{{ DANDISET_ID }}', dandiset_id)

    timer = time.time()
    r = perform_task(
        instructions=prompt,
        cwd=working_dir,
        model=model,
        vision_model=None,
        log_file=working_dir + '/minicline.log',
        auto=True,
        approve_all_commands=True
    )
    elapsed_sec = time.time() - timer

    metadata = {
        'dandiset_id': dandiset_id,
        'model': model,
        'prompt': prompt_fname,
        'total_prompt_tokens': r.total_prompt_tokens,
        'total_completion_tokens': r.total_completion_tokens,
        'total_vision_prompt_tokens': r.total_vision_prompt_tokens,
        'total_vision_completion_tokens': r.total_vision_completion_tokens,
        'elapsed_time_seconds': elapsed_sec,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        "system_info": {
            "platform": platform.platform(),
            "hostname": platform.node(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
    }

    with open('metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    # copy working/notebook.ipynb to {dandiset_id}.ipynb
    notebook_path = os.path.join(working_dir, 'notebook.ipynb')
    if os.path.exists(notebook_path):
        shutil.copy(notebook_path, f'{dandiset_id}.ipynb')
    else:
        raise Exception(f"Notebook file {notebook_path} does not exist.")

if __name__ == '__main__':
    generate()
