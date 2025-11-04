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


def run_notebook_with_hooks(notebook, competition_name):
    nb = nbformat.read(notebook, as_version=4)

    client = ProfilerClient(nb, competition_name, notebook, parser_code=parser_code,
                            disk_profiler_code=disk_profiler_code, load_profiler_code=load_profiler_code)
    results = client.execute()

    return results


def start_worker(final_results, competition_name: str, nb: str, wl=None):
    print(f"Running {competition_name}/{nb}")
    results = run_notebook_with_hooks(nb, competition_name)
    if wl is not None:
        wl.acquire()
    try:
        final_results.extend(results)
    finally:
        if wl is not None:
            wl.release()


def process_multithread(final_results, root_dir, notebook_dir, notebooks, multithread=True):
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


if __name__ == "__main__":
    competition_name = sys.argv[1] if len(sys.argv) > 1 else None

    if (competition_name is not None):
        adapter = KaggleAdapter(competition_name)

        max_notebooks = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        page = 0
        page_size = min(max_notebooks, 50)
        multithread = True if len(
            sys.argv) > 3 and sys.argv[3] == "multithread" else False

        final_results = []

        adapter.download_input_data()
        root_dir = os.getcwd()

        try:
            while (len(final_results) < max_notebooks):
                page += 1
                notebooks = adapter.download_notebooks(page, page_size)

                if (len(notebooks) == 0):
                    break

                process_multithread(
                    final_results, root_dir, adapter.notebook_dir, notebooks, multithread=multithread)
            save_output(competition_name, final_results, adapter.output_dir)
        except KeyboardInterrupt:
            os.chdir(root_dir)
            save_output(competition_name, final_results, adapter.output_dir)
