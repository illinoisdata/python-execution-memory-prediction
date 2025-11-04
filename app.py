from ProfilerClient import ProfilerClient
from KaggleAdapter import KaggleAdapter
import nbformat
import os
from multiprocessing.pool import ThreadPool
from multiprocessing import Lock
from utils import parse_args, get_output_file_path, save_output


def run_notebook_with_hooks(notebook, competition_name):
    args = parse_args()
    nb = nbformat.read(notebook, as_version=4)

    client = ProfilerClient(nb, competition_name,
                            notebook, timeout=args.timeout)
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

            save_output(get_output_file_path(
                adapter.output_dir, adapter.competition_name, page, page_size), final_results)
    except KeyboardInterrupt:
        os.chdir(root_dir)
        save_output(get_output_file_path(
            adapter.output_dir, adapter.competition_name, page, page_size), final_results)
    except Exception:
        os.chdir(root_dir)
        save_output(get_output_file_path(
            adapter.output_dir, adapter.competition_name, page, page_size), final_results)
