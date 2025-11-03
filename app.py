from ProfilerClient import ProfilerClient
from KaggleAdapter import KaggleAdapter
import json
import nbformat
import os
import sys
from multiprocessing.pool import ThreadPool
from multiprocessing import Lock


def load_file(path):
    with open(path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    return file_content


parser_code = load_file("./TreeParser.py")
disk_profiler_code = load_file("./DiskProfiler.py")
load_profiler_code = "%load_ext memory_profiler" + "\n"


def run_notebook_with_hooks(notebook):
    nb = nbformat.read(notebook, as_version=4)

    client = ProfilerClient(nb, parser_code=parser_code,
                            disk_profiler_code=disk_profiler_code, load_profiler_code=load_profiler_code)
    results = client.execute()

    return results


def start_worker(wl, final_results, competition_name: str, nb: str):
    print(f"Running {competition_name}/{nb}")
    try:
        results = run_notebook_with_hooks(nb)
        wl.acquire()
        try:
            final_results.extend(results)
        finally:
            wl.release()
    except Exception as e:
        print(f"An unexpected error occurred while executing {nb}: {e}")


def process_multithread(final_results, notebook_dir, notebooks):
    wl = Lock()

    root_dir = os.getcwd()
    os.chdir(notebook_dir)
    with ThreadPool() as pool:
        pool.starmap(start_worker, [tuple(
            [wl, final_results, competition_name, nb]) for nb in notebooks])
    os.chdir(root_dir)


if __name__ == "__main__":
    competition_name = sys.argv[1] if len(sys.argv) > 1 else None

    if (competition_name is not None):
        adapter = KaggleAdapter(competition_name)

        max_notebooks = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        page = 0
        page_size = min(max_notebooks, 50)

        final_results = []

        while (len(final_results) < max_notebooks):
            page += 1
            notebooks = adapter.execute(page, page_size)

            if (len(notebooks) == 0):
                break

            process_multithread(final_results, adapter.notebook_dir, notebooks)

        output_file = os.path.join(
            adapter.output_dir, f"{competition_name}.json")
        with open(output_file, "w") as f:
            json.dump(final_results, f, indent=2)
        print(f"Execution complete. Results saved to {output_file}")
