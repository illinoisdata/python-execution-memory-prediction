import os


def get_notebooks_count():
    print("Competitions:")
    competitions_dir = "./competitions"
    competitions_notebooks = 0
    for d in os.listdir(competitions_dir):
        count = len(os.listdir(os.path.join(competitions_dir, d, "notebooks")))
        print(d, count)
        competitions_notebooks += count
    print("\n")

    print("Datasets:")
    datasets_dir = "./datasets"
    datasets_notebooks = 0
    for d in os.listdir(datasets_dir):
        count = len(os.listdir(os.path.join(datasets_dir, d, "notebooks")))
        print(d, count)
        datasets_notebooks += count
    print("\n")

    print(f"Competition notebooks: {competitions_notebooks}")
    print(f"Dataset notebooks: {datasets_notebooks}")


get_notebooks_count()
