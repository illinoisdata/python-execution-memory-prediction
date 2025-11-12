import os
import json

competitions_dir = "./competitions"
datasets_dir = "./datasets"


def create_dataset():
    dataset = []
    for d in os.listdir(competitions_dir):
        output_dir = os.path.join(competitions_dir, d, "output")
        for o in os.listdir(output_dir):
            with open(os.path.join(output_dir, o), 'r') as f:
                dataset.extend(json.load(f))
    for d in os.listdir(datasets_dir):
        output_dir = os.path.join(datasets_dir, d, "output")
        for o in os.listdir(output_dir):
            with open(os.path.join(output_dir, o), 'r') as f:
                dataset.extend(json.load(f))
    with open('dataset.json', 'w') as json_file:
        json.dump(dataset, json_file, indent=4)


def get_notebooks_count():
    print("Competitions:")
    competitions_notebooks = 0
    for d in os.listdir(competitions_dir):
        count = len(os.listdir(os.path.join(competitions_dir, d, "notebooks")))
        print(d, count)
        competitions_notebooks += count
    print("\n")

    print("Datasets:")
    datasets_notebooks = 0
    for d in os.listdir(datasets_dir):
        count = len(os.listdir(os.path.join(datasets_dir, d, "notebooks")))
        print(d, count)
        datasets_notebooks += count
    print("\n")

    print(f"Competition notebooks: {competitions_notebooks}")
    print(f"Dataset notebooks: {datasets_notebooks}")
