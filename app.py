from ProfilerClient import ProfilerClient
import json
import nbformat


def run_notebook_with_hooks(filepath):
    nb = nbformat.read(filepath, as_version=4)
    results = []

    client = ProfilerClient(nb, record_list=results)
    cell_count = client.execute()

    print(f"Executed {cell_count} cells, results for {len(results)} cells")

    return results


if __name__ == "__main__":
    results = run_notebook_with_hooks("mnist-naive-bayesian-classifier.ipynb")

    with open("cell_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Execution complete. Results saved to cell_metrics.json")
