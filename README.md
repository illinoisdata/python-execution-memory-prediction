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

```bash
cd python-execution-dataset
docker run -v $(pwd):/workspace -w /workspace kaggle-profiler -c <competition-name>
```

**Command line arguments**

-   `-c or --competition` **(Required)**: Name of the Kaggle competition.
-   `-p or --page`: Page number (1-indexed) to fetch (default: 1).
-   `-ps or --page-size`: Number of notebooks to fetch in each page (default: 50). Minimum of this value and number of notebooks to process.
-   `-nb or --notebooks`: Number of notebooks to process (default: 50). More notebooks are downloaded if the initial download does not meet this requirement.
-   `-m or --multithreading`: Enable multithreading.
-   `-o or --overwrite`: Overwrite existing notebooks and inputs for this competition.
-   `-t or --timeout`: Timeout in seconds for each cell to complete execution (including AST parsing) after which it is stopped and further processing of the notebook is abandoned (default: 7 minutes).

### Paths

All downloads and outputs are stored in the `dataset` directory. Most paths on the downloaded notebooks are modified at runtime to follow these conventions.

-   Inputs are stored in `datasets/competition-name/input` directory.
-   Notebooks are stored in `datasets/competition-name/notebooks` directory.
-   Outputs are stored in `datasets/competition-name/output` directory.

### Miscellaneous

-   There is a time limit specified by the `--timeout` argument (defaults to 7 minutes) for each cell to complete execution. At timeout, the current notebook is stopped and the next notebook begins execution.
-   On recieving a KeyboardInterrupt, all executions are aborted and the last set of results are stored in the output file.
