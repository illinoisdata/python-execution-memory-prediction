import os


def get_notebooks_count():
    print("Competitions:")
    for d in os.listdir("./competitions"):
        print(d, len(os.listdir(os.path.join("./competitions", d, "notebooks"))))
    print("\n")
    for d in os.listdir("./competitions"):
        print(d, len(os.listdir(os.path.join("./datasets", d, "notebooks"))))
