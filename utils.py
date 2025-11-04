import argparse
import json
import os


def load_file(path):
    with open(path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    return file_content


def get_output_file_path(output_dir, competiton_name, page, page_size):
    return os.path.join(output_dir, f"{competiton_name}-{page}-{page_size}.json")


def save_output(path, data):
    if (len(data) > 0):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Execution complete. Results saved to {path}")
    else:
        print(f"Execution complete. No results to save")


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
        "-nb", "--notebooks",
        type=int,
        default=50,
        help="Number of notebooks to process (default: 50)"
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
