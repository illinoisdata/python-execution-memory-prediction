import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from IPython.core.inputtransformer2 import TransformerManager
import re
import json
import signal
from utils import load_file
from TreeParser import TreeParser
import textwrap

parser_code = load_file("./parser_utils.py")
gpu_profiler_code = load_file("./TorchGPUProfiler.py")
load_profiler_code = "%load_ext memory_profiler" + "\n"

PROFILER_PEAK_MEMORY = "peak memory:"
PROFILER_MEMORY_INCREMENT = "increment:"

PROFILER_PEAK_GPU = "peak gpu:"
PROFILER_GPU_INCREMENT = "gpu increment:"


def timeout_handler():
    raise Exception


class ProfilerClient(NotebookClient):
    def __init__(self, nb, data_source_name, notebook_name, timeout):
        self.results = []
        self.data_source_name = data_source_name
        self.timeout = timeout
        self.notebook_name = notebook_name

        self.parser = TreeParser()

        new_cells = [nbformat.v4.new_code_cell(parser_code), nbformat.v4.new_code_cell(
            gpu_profiler_code), nbformat.v4.new_code_cell(load_profiler_code)]
        self.new_cell_count = len(new_cells)

        new_nb_cells = []
        for cell in nb.cells:
            new_nb_cells.extend([nbformat.v4.new_code_cell(""), cell])

        nb.cells = new_cells + new_nb_cells
        super().__init__(nb)
        print("Initialized ProfilerClient")

    def clean_cell_for_input(self, code):
        kaggle_path = f'/kaggle/input/{self.data_source_name}'
        data_source_path = f'../input/{self.data_source_name}'
        if kaggle_path in code:
            code = code.replace(kaggle_path, '../input')
        if data_source_path in code:
            code = code.replace(data_source_path, '../input')
        return code

    def clean_cell_for_ast(self, code):
        code = code.replace('"""', '\"\"\"')
        lines = code.splitlines()
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("%") or stripped.startswith("!") or stripped.startswith("?"):
                continue
            if stripped.startswith("%%"):
                continue
            cleaned_lines.append(line)

        return repr("\n".join(cleaned_lines))

    def execute(self):
        cell_count = 0
        with self.setup_kernel():
            for i in range(self.new_cell_count):
                cell = self.nb.cells[i]
                if cell.cell_type != "code":
                    continue
                self.execute_cell(cell, i, should_profile=False)
            for i in range(self.new_cell_count, len(self.nb.cells), 2):
                profiling_cell = self.nb.cells[i]
                cell = self.nb.cells[i + 1]

                if cell.cell_type != "code":
                    continue

                try:
                    self.execute_cell(profiling_cell, i,
                                      cell, should_profile=True)

                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(self.timeout)

                    print(f"{self.notebook_name}: Executing cell {i}")
                    self.execute_cell(cell, i, should_profile=True)
                    cell_count += 1
                    print(f"{self.notebook_name}: Complete cell {i}")
                except Exception as e:
                    print(e)
                    print(f"{self.notebook_name}: Error cell {i}")
                    break
                finally:
                    signal.alarm(0)
        print(
            f"{self.notebook_name}: Total {len(self.nb.cells)} cells, executed {cell_count - self.new_cell_count} cells, results for {len(self.results)} cells")
        return self.results

    def profile_cell(self, cell, cell_index, source_cell, execution_count=None, store_history=True):
        tm = TransformerManager()
        cell_code = tm.transform_cell(source_cell['source'])

        imports, variables = self.parser.start(
            self.clean_cell_for_ast(cell_code))

        cell['source'] = f"""
        import json

        ip_variables = {{}}
        for id in json.loads({variables}):
            ip_variables[id] = get_variable_info(id)
        print(ip_variables)
        """

        result = super().execute_cell(cell, cell_index, execution_count, store_history)

        output_data_text = result['outputs'][-1].get('text', '\{\}')

        self.results.append(
            {'imports': imports, 'ip_variables': json.loads(output_data_text)})

        return result

    def execute_cell(self, cell, cell_index, execution_count=None, store_history=True, should_profile=False):
        if (should_profile):
            cell['source'] = self.clean_cell_for_input(cell['source'])
            cell['source'] = "%%memit" + "\n" + "with gpu_profiler():" + \
                "\n" + textwrap.indent(cell['source'], "\t")

        result = super().execute_cell(cell, cell_index, execution_count, store_history)

        if (should_profile):
            output_data_text = result['outputs'][-1].get('text', None)

            peak_memory_idx = -1
            memory_increment_idx = -1
            peak_gpu_idx = -1
            gpu_increment_idx = -1
            for i in range(len(result['outputs']) - 1, -1, -1):
                output_data_text = result['outputs'][i].get('text', None)
                if output_data_text is not None:
                    if output_data_text.find(PROFILER_PEAK_MEMORY) != -1:
                        peak_memory_idx = i
                    if output_data_text.find(PROFILER_MEMORY_INCREMENT) != -1:
                        memory_increment_idx = i
                    if output_data_text.find(PROFILER_PEAK_GPU) != -1:
                        peak_gpu_idx = i
                    if output_data_text.find(PROFILER_GPU_INCREMENT) != -1:
                        gpu_increment_idx = i

            output_data_text = ""
            start_idx = min(
                [peak_memory_idx, memory_increment_idx, peak_gpu_idx, gpu_increment_idx])
            end_idx = max([peak_memory_idx, memory_increment_idx,
                          peak_gpu_idx, gpu_increment_idx])
            for output in result['outputs'][start_idx: end_idx + 1]:
                output_data_text += output.get('text', '')

            if len(output_data_text) > 0:
                output = {}

                peak_memory_match = re.search(r"peak memory: (.*?) MiB",
                                              output_data_text, re.DOTALL)
                memory_increment_match = re.search(r"increment: (.*?) MiB",
                                                   output_data_text, re.DOTALL)
                peak_gpu_match = re.search(r"peak gpu: (.*?) MB",
                                           output_data_text, re.DOTALL)
                gpu_increment_match = re.search(r"gpu increment: (.*?) MB",
                                                output_data_text, re.DOTALL)

                if peak_memory_match and memory_increment_match:
                    peak_memory = float(peak_memory_match.group(
                        1).strip()) * 1.049  # MiB to MB
                    memory_increment = float(
                        memory_increment_match.group(1).strip()) * 1.049  # MiB to MB
                    output['memory_usage'] = {
                        'peak_memory': peak_memory,
                        'memory_increment': memory_increment
                    }
                if peak_gpu_match and gpu_increment_match:
                    peak_gpu = float(peak_gpu_match.group(1).strip())
                    gpu_increment = float(gpu_increment_match.group(1).strip())
                    output['gpu_usage'] = {
                        'peak_gpu': peak_gpu,
                        'gpu_increment': gpu_increment
                    }

                if len(list(output.keys())) > 0:
                    self.results[-1] = {**self.results[-1], **output}
        return result
