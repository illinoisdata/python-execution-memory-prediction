import zipfile
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

# autopep8: off
from kaggle.api.kaggle_api_extended import KaggleApi
import kaggle

api = KaggleApi()
api.authenticate()


class KaggleAdapter():
    def __init__(self, competition_name: str):
        self.competition_name = competition_name
        self.main_dir = "./dataset"
        self.competition_dir = os.path.join(
            self.main_dir, self.competition_name)

        if os.path.exists(self.competition_dir):
            try:
                shutil.rmtree(self.competition_dir)
                print(
                    f"Directory '{self.competition_dir}' and its contents removed successfully.")
            except OSError as e:
                print(f"Error: {self.competition_dir} : {e.strerror}")
        else:
            print(f"Directory '{self.competition_dir}' does not exist.")

        self.input_dir = os.path.join(self.competition_dir, "input")
        self.notebook_dir = os.path.join(self.competition_dir, "notebooks")
        self.output_dir = os.path.join(self.competition_dir, "output")

        os.makedirs(self.competition_dir, exist_ok=True)
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.notebook_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def __download_input_data(self):
        zip_file_path = os.path.join(
            self.input_dir, f"{self.competition_name}.zip")
        try:
            api.competition_download_files(
                competition=self.competition_name, path=self.input_dir)
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

    def __download_notebooks(self, page=1, page_size=50):
        downloaded_notebooks = []
        try:
            notebooks = api.kernels_list(
                competition=self.competition_name, sort_by='hotness', page=page, page_size=page_size)
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

    def execute(self, page=1, page_size=50):
        self.__download_input_data()
        return self.__download_notebooks(page, page_size)
