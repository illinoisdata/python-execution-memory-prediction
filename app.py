from ProfilerClient import ProfilerClient
import json
import nbformat
import os


def run_notebook_with_hooks(filepath):
    nb = nbformat.read(filepath, as_version=4)
    results = []

    client = ProfilerClient(nb, record_list=results)
    cell_count = client.execute()

    print(f"Executed {cell_count} cells, results for {len(results)} cells")

    return results


if __name__ == "__main__":
    notebooks_dir = "./dataset/notebooks"
    output_dir = "./dataset/output"

    for nb in os.listdir(notebooks_dir):
        print(f"Running {nb}")
        filename, extension = os.path.splitext(nb)
        results = run_notebook_with_hooks(
            os.path.join(notebooks_dir, nb))
        output_file = os.path.join(output_dir, f"{filename}.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Execution complete. Results saved to {output_file}")
