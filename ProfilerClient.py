import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from IPython.core.inputtransformer2 import TransformerManager
import re
import ast
import signal
from utils import load_file
from TreeParser import TreeParser
import textwrap
import time

parser_code = load_file("./parser_utils.py")
gpu_profiler_code = load_file("./GPUProfiler.py")
load_profiler_code = "%load_ext memory_profiler" + "\n"


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
            new_nb_cells.extend([nbformat.v4.new_code_cell(
                ""), cell, nbformat.v4.new_code_cell("")])

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

    def get_cuda_allocation_type(self):
        for v in list(self.parser.imports.values()):
            if (v.startswith("torch")):
                return "torch"
            elif (v.startswith("tensorflow")):
                return "tensorflow"
        return None

    def execute(self):
        with self.setup_kernel():
            for i in range(self.new_cell_count):
                cell = self.nb.cells[i]
                if cell.cell_type != "code":
                    continue
                self.execute_cell(cell, i, should_profile=False)

            cell_count = 0
            for i in range(self.new_cell_count, len(self.nb.cells), 3):
                parsing_cell = self.nb.cells[i]
                cell = self.nb.cells[i + 1]
                post_parsing_cell = self.nb.cells[i + 2]

                if cell.cell_type != "code":
                    continue

                actual_cell_index = (i - self.new_cell_count) // 3 + 1
                try:
                    print(
                        f"{self.notebook_name}: Parsing for cell {actual_cell_index}")
                    variable_output = self.parse_cell(parsing_cell, i, cell)

                    try:
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(self.timeout)

                        print(
                            f"{self.notebook_name}: Executing cell {actual_cell_index}")
                        profiling_output = self.execute_cell(
                            cell, i + 1, should_profile=True)
                    except Exception:
                        raise
                    finally:
                        signal.alarm(0)

                    print(
                        f"{self.notebook_name}: Post-parsing for cell {actual_cell_index}")
                    post_variable_output = self.parse_cell(
                        post_parsing_cell, i + 2, cell, variable_output)

                    self.results.append(
                        {**variable_output, **post_variable_output, **profiling_output})
                    cell_count += 1
                    print(
                        f"{self.notebook_name}: Complete cell {actual_cell_index}")
                except Exception as e:
                    print(e)
                    print(f"{self.notebook_name}: Error cell {actual_cell_index}")
                    break
                finally:
                    signal.alarm(0)
        print(
            f"{self.notebook_name}: Total {(len(self.nb.cells) - self.new_cell_count)//2} cells, executed {cell_count} cells, results for {len(self.results)} cells")
        return self.results

    def parse_cell(self, cell, cell_index, source_cell, execution_count=None, store_history=True, variable_output=None):
        output = {}
        if variable_output is not None:
            variables = list(variable_output.keys())
        else:
            code, imports, variables = self.parser.start(source_cell['source'])
            output = {'code': code, 'imports': imports}

        cell['source'] = f"""
        ip_variables = {{}}
        for id in {variables}:
            ip_variables[id] = get_variable_info(id)
        print(ip_variables)
        """

        result = super().execute_cell(cell, cell_index, execution_count, store_history)

        output_data_text = result['outputs'][-1].get('text', '{}')

        var_output = {**ast.literal_eval(output_data_text)}

        for key in list(var_output.keys()):
            if var_output[key].get('ctx', None) == 'ClassDef':
                var_output[key]['ctx'] = self.parser.class_defs.get(
                    var_output[key]['type'], None)

        id = 'op_variables' if variable_output is not None else 'ip_variables'
        return {**output, id: var_output}

    def execute_cell(self, cell, cell_index, execution_count=None, store_history=True, should_profile=False):
        if (should_profile):
            tm = TransformerManager()
            cell_code = tm.transform_cell(cell['source'])
            cell['source'] = self.clean_cell_for_input(cell_code)
            cell['source'] = "%%memit" + "\n" + f"with gpu_profiler(type='{self.get_cuda_allocation_type()}'):" + \
                "\n" + textwrap.indent(cell['source'], "\t")

        start_time = time.perf_counter()
        result = super().execute_cell(cell, cell_index, execution_count, store_history)
        end_time = time.perf_counter()
        execution_time = end_time - start_time

        if (should_profile):
            output_data_text = "\n".join(
                [output.get('text', '') for output in result['outputs']])
            patterns = {
                "peak_gpu": r"peak gpu:\s*([\d\.]+)\s*MB",
                "gpu_increment": r"gpu increment:\s*([\d\.]+)\s*MB",
                "peak_memory": r"peak memory:\s*([\d\.]+)\s*MiB",
                "memory_increment": r"increment:\s*([\d\.]+)\s*MiB"
            }

            values = {key: float(re.search(pattern, output_data_text).group(
                1)) for key, pattern in patterns.items()}
            return {'execution_time': execution_time, 'memory_usage': values.get('memory_increment', None), 'gpu_usage': values.get('gpu_increment', None)}
        return {}
