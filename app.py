from ProfilerClient import ProfilerClient
from KaggleAdapter import KaggleAdapter
import json
import nbformat
import os
import sys
from multiprocessing.pool import ThreadPool
from multiprocessing import Lock
import argparse


def load_file(path):
    with open(path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    return file_content


parser_code = load_file("./TreeParser.py")
disk_profiler_code = load_file("./DiskProfiler.py")
load_profiler_code = "%load_ext memory_profiler" + "\n"


def run_notebook_with_hooks(notebook, competition_name):
    nb = nbformat.read(notebook, as_version=4)

    client = ProfilerClient(nb, competition_name, notebook, parser_code=parser_code,
                            disk_profiler_code=disk_profiler_code, load_profiler_code=load_profiler_code)
    results = client.execute()

    return results


def start_worker(final_results, competition_name: str, nb: str, wl=None):
    try:
        print(f"Running {competition_name}/{nb}")
        results = run_notebook_with_hooks(nb, competition_name)
        if wl is not None:
            wl.acquire()
        try:
            final_results.extend(results)
        finally:
            if wl is not None:
                wl.release()
    except Exception as e:
        print(f"An unexpected error occurred while executing {nb}: {e}")


def process_notebooks(final_results, root_dir, competition_name, notebook_dir, notebooks, multithread=True):
    os.chdir(notebook_dir)

    if multithread:
        wl = Lock()
        with ThreadPool() as pool:
            pool.starmap(start_worker, [tuple(
                [final_results, competition_name, nb, wl]) for nb in notebooks])
    else:
        for nb in notebooks:
            start_worker(final_results, competition_name, nb)
    os.chdir(root_dir)


def save_output(competition_name, final_results, output_dir):
    output_file = os.path.join(output_dir, f"{competition_name}.json")
    with open(output_file, "w") as f:
        json.dump(final_results, f, indent=2)
    print(f"Execution complete. Results saved to {output_file}")


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

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    adapter = KaggleAdapter(
        competition_name=args.competition, deleteExisting=args.overwrite)

    max_notebooks = args.notebooks
    page = args.page - 1
    page_size = min(max_notebooks, args.page_size)

    final_results = []

    adapter.download_input_data()
    root_dir = os.getcwd()

    try:
        while (len(final_results) < max_notebooks):
            page += 1
            notebooks = adapter.download_notebooks(page, page_size)

            if (len(notebooks) == 0):
                break

            process_notebooks(
                final_results, root_dir, adapter.competition_name, adapter.notebook_dir, notebooks, multithread=args.multithreading)
        save_output(adapter.competition_name,
                    final_results, adapter.output_dir)
    except KeyboardInterrupt:
        os.chdir(root_dir)
        save_output(adapter.competition_name,
                    final_results, adapter.output_dir)
    except Exception:
        os.chdir(root_dir)
        save_output(adapter.competition_name,
                    final_results, adapter.output_dir)
