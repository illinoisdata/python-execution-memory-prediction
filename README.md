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
docker run -v $(pwd):/workspace -w /workspace kaggle-profiler <competition-name> <max-notebooks>
```

**Multithreading**

```bash
cd python-execution-dataset
docker run -v $(pwd):/workspace -w /workspace kaggle-profiler <competition-name> <max-notebooks> multithread
```

### Paths

All downloads and outputs are stored in the `dataset` directory. Most paths on the downloaded notebooks are modified at runtime to follow these conventions.

-   Inputs are stored in `datasets/competition-name/input` directory.
-   Notebooks are stored in `datasets/competition-name/notebooks` directory.
-   Outputs are stored in `datasets/competition-name/output/competition-name.json` file.
