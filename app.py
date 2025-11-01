from ProfilerClient import ProfilerClient
from KaggleAdapter import KaggleAdapter
import json
import nbformat
import os
from multiprocessing.pool import ThreadPool
from multiprocessing import Lock


def run_notebook_with_hooks(filepath):
    nb = nbformat.read(filepath, as_version=4)
    results = []

    client = ProfilerClient(nb, record_list=results)
    cell_count = client.execute()

    print(f"Executed {cell_count} cells, results for {len(results)} cells")

    return results


def start_worker(wl, final_results, competition_name: str, notebook_dir: str, nb: str):
    print(f"Running {competition_name}/{nb}")
    try:
        results = run_notebook_with_hooks(
            os.path.join(notebook_dir, nb))
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

    with ThreadPool() as pool:
        pool.starmap(start_worker, [tuple([wl, final_results, competition_name,
                     adapter.notebook_dir, nb]) for nb in os.listdir(adapter.notebook_dir)])

    output_file = os.path.join(adapter.output_dir, f"{competition_name}.json")
    with open(output_file, "w") as f:
        json.dump(final_results, f, indent=2)
    print(f"Execution complete. Results saved to {output_file}")
