from ProfilerClient import ProfilerClient
from KaggleAdapter import KaggleAdapter
import json
import nbformat
import os
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


def start_worker(wl, final_results, competition_name: str, notebook_dir: str, nb: str):
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


if __name__ == "__main__":
    competition_name = "digit-recognizer"
    max_notebooks = 10
    adapter = KaggleAdapter(competition_name, max_notebooks)
    adapter.execute()

    final_results = []
    wl = Lock()

    root_dir = os.getcwd()
    os.chdir(adapter.notebook_dir)
    with ThreadPool() as pool:
        pool.starmap(start_worker, [tuple([wl, final_results, competition_name,
                     adapter.notebook_dir, nb]) for nb in os.listdir(adapter.notebook_dir)])
    os.chdir(root_dir)

    output_file = os.path.join(adapter.output_dir, f"{competition_name}.json")
    with open(output_file, "w") as f:
        json.dump(final_results, f, indent=2)
    print(f"Execution complete. Results saved to {output_file}")
