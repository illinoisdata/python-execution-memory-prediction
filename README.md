This repository makes use of the [Kaggle API](https://www.kaggle.com/docs/api) to download datesets and notebooks from Kaggle, and the [kaggle/python](https://www.kaggle.com/discussions/general/20036) Docker image to replicate the virtual environment to run the Kaggle notebooks.

### Environment Variables

In order to build and run this image, you would need an API key from Kaggle. Create a `.env` file at the root directory of the repository and add the following values to it.

```
KAGGLE_USERNAME=<username>
KAGGLE_KEY=<key>
```

### Building the image

```bash
cd python-execution-dataset
docker build -t kaggle-profiler .
```

### Running the image

**As root**

All generated files are owned by `root` user and cannot be written or deleted outside the Docker container.

```bash
cd python-execution-dataset
docker run -v $(pwd):/workspace -w /workspace kaggle-profiler -c <competition-name>
```

**As user**

To own and allow editing of files that were created inside of the Docker container, pass the current user to the `docker run` command.

```bash
cd python-execution-dataset
docker run -e HOST_UID=$(id -u) -e HOST_GID=$(id -g) -v $(pwd):/workspace -w /workspace kaggle-profiler -c <competition-name>
```

**Command line arguments**

-   `-c or --competition` **(Required)**: Name of the Kaggle competition.
-   `-d or --dataset` **(Required)**: Slug of the Kaggle dataset. **Use either dataset or competition, not both.**
-   `-p or --page`: Page number (1-indexed) to fetch (default: 1).
-   `-ps or --page-size`: Number of notebooks to fetch in each page (default: 50). Minimum of this value and number of notebooks to process.
-   `-m or --multithreading`: Enable multithreading.
-   `--overwrite`: Overwrite existing notebooks and inputs for this competition.
-   `--timeout`: Timeout in seconds for each cell to complete execution (including AST parsing) after which it is stopped and further processing of the notebook is abandoned (default: 7 minutes).

### Paths

All downloads and outputs from a competition are stored in the `competitions` directory, and `datasets` for dataset-based downloads. Most paths on the downloaded notebooks are modified at runtime to follow these conventions.

-   The base path is either `competitions/competition-name` or `datasets/dataset-name` depending on the type of download.
-   Inputs are stored in `/input` directory.
-   Notebooks are stored in `/notebooks` directory.
-   Outputs are stored in `/output` directory.

### Miscellaneous

-   There is a time limit specified by the `--timeout` argument (defaults to 7 minutes) for each cell to complete execution. At timeout, the current notebook is stopped and the next notebook begins execution.
-   On recieving a KeyboardInterrupt, all executions are aborted and the last set of results are stored in the output file.
