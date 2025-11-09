import zipfile
import os
import shutil
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

# autopep8: off
from kaggle.api.kaggle_api_extended import KaggleApi
import kaggle

api = KaggleApi()
api.authenticate()

class DataSourceType(Enum):
    DATASET = "dataset"
    COMPETITION = "competition"

class KaggleAdapter():
    def __init__(self, dataset_name: str = None, competition_name: str = None, deleteExisting = False):
        """
        data_source_type: Either one of DATASET or COMPETITION
        main_dir: Top level directory for storage (dataset/competition)
        data_source: Name of the competition or dataset slug
        data_source_name: Human readable name for the competition or dataset for file/directory names and logging
        """
        self.data_source_type = DataSourceType.COMPETITION if competition_name is not None else DataSourceType.DATASET
        if self.data_source_type == DataSourceType.COMPETITION:
            self.main_dir = "./competitions"
            self.data_source = competition_name
            self.data_source_name = competition_name
        else:
            self.main_dir = "./datasets"
            self.data_source = dataset_name
            self.data_source_name = "_".join(dataset_name.split("/"))

        self.data_source_dir = os.path.join(self.main_dir, self.data_source_name)

        if os.path.exists(self.data_source_dir):
            print(f"Directory '{self.data_source_dir}' exists.")
            if (deleteExisting):
                try:
                    shutil.rmtree(self.data_source_dir)
                    print(
                        f"Directory '{self.data_source_dir}' and its contents removed successfully.")
                except OSError as e:
                    print(f"Error: {self.data_source_dir} : {e.strerror}")
        else:
            print(f"Directory '{self.data_source_dir}' does not exist.")

        self.input_dir = os.path.join(self.data_source_dir, "input")
        self.notebook_dir = os.path.join(self.data_source_dir, "notebooks")
        self.output_dir = os.path.join(self.data_source_dir, "output")

        os.makedirs(self.data_source_dir, exist_ok=True)
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.notebook_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def download_input_data(self):
        if len(os.listdir(self.input_dir)) > 0:
            return

        zip_file_path = os.path.join(
            self.input_dir, f"{self.data_source}.zip")

        if (self.data_source_type == DataSourceType.COMPETITION):
            api.competition_download_files(competition=self.data_source, path=self.input_dir)
        else:
            api.dataset_download_files(dataset=self.data_source, path=self.input_dir)

        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zf:
                zf.extractall(self.input_dir)
            os.remove(zip_file_path)
            print(
                f"Successfully downloaded and unzipped '{zip_file_path}' to '{self.input_dir}'")
        except zipfile.BadZipFile:
            print(f"Error: '{zip_file_path}' is not a valid ZIP file.")
        except FileNotFoundError:
            print(f"Error: ZIP file not found at '{zip_file_path}'.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def download_notebooks(self, page=1, page_size=50):
        downloaded_notebooks = []
        try:
            notebooks = []
            if (self.data_source_type == DataSourceType.COMPETITION):
                notebooks = api.kernels_list(competition=self.data_source, sort_by='hotness', page=page, page_size=page_size)
            else:
                notebooks = api.kernels_list(dataset=self.data_source, sort_by='votes', page=page, page_size=page_size)

            kernel_count = 0
            for kernel in notebooks:
                if (not kernel._is_private and not kernel._enable_tpu):
                    file_path = api.kernels_pull(kernel=kernel._ref,
                                     path=self.notebook_dir)
                    filename = os.path.basename(file_path)
                    if filename.endswith(".ipynb"):
                        downloaded_notebooks.append(filename)
                        kernel_count += 1
                    else:
                        os.remove(file_path)
            print(
                f"Successfully downloaded {kernel_count} notebooks from {len(notebooks)} available to '{self.notebook_dir}'")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            return downloaded_notebooks
