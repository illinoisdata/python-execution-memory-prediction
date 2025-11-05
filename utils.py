import argparse
import json
import os
from pathlib import Path


def load_file(path):
    with open(path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    return file_content


def save_output(notebook_dir, output_dir, competition_name, page, page_size, data):
    output_path = os.path.join(
        output_dir, f"{competition_name}-{page}-{page_size}.json")
    if (len(data) > 0):
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Execution complete. Results saved to {output_path}")
    else:
        print(f"Execution complete. No results to save")

    root = Path(notebook_dir)
    for path in root.rglob("*"):
        if path.is_file() and path.suffix != ".ipynb":
            print(f"Removing: {path}")
            path.unlink()

    for dirpath, dirnames, filenames in os.walk(notebook_dir, topdown=False):
        if not dirnames and not filenames:
            os.rmdir(dirpath)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c", "--competition",
        type=str,
        required=True,
        help="Name of the Kaggle competition"
    )

    parser.add_argument(
        "-p", "--page",
        type=int,
        default=1,
        help="Page number (1-indexed) to fetch (default: 1)"
    )

    parser.add_argument(
        "-ps", "--page-size",
        type=int,
        default=50,
        help="Number of notebooks to fetch in each page (default: 50)"
    )

    parser.add_argument(
        "-m", "--multithreading",
        action="store_true",
        default=False,
        help="Enable multithreading"
    )

    parser.add_argument(
        "-o", "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing notebooks and inputs for this competition"
    )

    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=(7 * 60),
        help="Timeout in seconds for each cell to complete execution (including AST parsing) (default: 7 minutes)"
    )

    return parser.parse_args()
