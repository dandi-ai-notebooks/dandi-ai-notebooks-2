#!/usr/bin/env python

import click
import os
import shutil
from datetime import datetime
import yaml
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def create_config(output_dir: str, model: str, prompt: str, dandiset_id: str):
    """Create the config.yaml file in the output directory."""
    config = {
        'model': model,
        'prompt': prompt,
        'dandiset_id': dandiset_id
    }
    with open(os.path.join(output_dir, 'config.yaml'), 'w') as f:
        yaml.dump(config, f)

def copy_template_files(output_dir: str, prompt: str):
    """Copy required template files to the output directory."""
    templates_dir = 'templates'
    files_to_copy = [
        'tools.py',
        'tools_cli.py',
        'generate.py',
        f'{prompt}.txt'
    ]

    for file in files_to_copy:
        src = os.path.join(templates_dir, file)
        dst = os.path.join(output_dir, file)
        shutil.copy2(src, dst)

@click.command()
@click.argument('dandiset_id')
@click.argument('model')
@click.argument('prompt')
def main(dandiset_id: str, model: str, prompt: str):
    """Generate a new notebook directory with template files."""
    # Extract the model name after the last '/' if it exists
    model_name = model.split('/')[-1]

    # Create the output directory name with current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    output_dir = os.path.join('dandisets', dandiset_id, f'{current_date}-{model_name}-{prompt}')

    if os.path.exists(output_dir):
        raise Exception(f"Output directory {output_dir} already exists. Please choose a different name or remove the existing directory.")

    # Create the output directory and any necessary parent directories
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create config.yaml
    create_config(output_dir, model, prompt, dandiset_id)

    # Copy template files
    copy_template_files(output_dir, prompt)

    # Run generate.py in the new directory
    try:
        subprocess.run(['python', 'generate.py'], cwd=output_dir, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error running generate.py: {e}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    main()
