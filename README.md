This repository makes use of [kaggle/python](https://www.kaggle.com/discussions/general/20036) Docker image to replicate the virtual environment to run Kaggle notebooks.

### Building the image
``` bash
cd python-execution-dataset
docker build -t kaggle-profiler .
```

### Running the image
``` bash
cd python-execution-dataset
docker run -v $(pwd):/workspace -w /workspace kaggle-profiler <competition-name> <max-notebooks>
```

### Paths
All downloads and outputs are stored in the `dataset` directory.
- Inputs are stored in `datasets/competition-name/input` directory.
- Notebooks are stored in `datasets/competition-name/notebooks` directory.
- Outputs are stored in `datasets/competition-name/output/competition-name.json` file.