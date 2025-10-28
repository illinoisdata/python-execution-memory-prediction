import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from IPython.core.inputtransformer2 import TransformerManager
import re
import ast

PROFILER_DATA_STARTS = "PROFILER_DATA_STARTS"
PROFILER_DATA_ENDS = "PROFILER_DATA_ENDS"
PROFILER_PEAK_MEMORY = "peak memory:"
PROFILER_MEMORY_INCREMENT = "increment:"


class ProfilerClient(NotebookClient):
    def __init__(self, nb, record_list):
        self.records = record_list  # shared list to store results
        self.imports = {}
        parser_cell = nbformat.v4.new_code_cell(
            self.load_file("./TreeParser.py"))
        disk_profiler_cell = nbformat.v4.new_code_cell(
            self.load_file("./DiskProfiler.py"))
        load_profiler_cell = nbformat.v4.new_code_cell(self.load_profilers())
        new_cells = [parser_cell, disk_profiler_cell,
                     load_profiler_cell]
        self.new_cell_count = len(new_cells)
        nb.cells = new_cells + nb.cells
        super().__init__(nb)
        print("Initialized ProfilerClient")

    def load_file(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            file_content = file.read()
        return file_content

    def load_profilers(self):
        return "%load_ext memory_profiler" + "\n"

    def get_cell_profiler_code(self):
        return "%%memit" + "\n"

    def get_start_parse_code(self, code):
        return f"""
parser.start(ast.parse(\"\"\"{code}\"\"\"))
diskProfiler.start()
start = time.time()
        """

    def get_exit_parse_code(self, code):
        return f"""
end = time.time()
diskProfiler.stop()
tree = ast.parse(\"\"\"{code}\"\"\")
parser.exit(tree)

print("{PROFILER_DATA_STARTS}")
print({{
    "code": ast.unparse(tree),
    "actual_code": \"\"\"{code}\"\"\",
    "ip_variables": parser.variables_ip,
    "op_variables": parser.variables_op,
    "imports": parser.local_imports,
    "execution_time": end - start,
    "disk_usage": {{
        "peak_disk": diskProfiler.peak_used,
        "increment": diskProfiler.increment
    }}
}})
print("{PROFILER_DATA_ENDS}")
        """

    def execute(self):
        cell_count = 0
        with self.setup_kernel():
            for i, cell in enumerate(self.nb.cells):
                if cell.cell_type != "code":
                    continue
                self.execute_cell(cell, i)
                cell_count += 1
        return cell_count - self.new_cell_count

    def execute_cell(self, cell, cell_index, execution_count=None, store_history=True):
        should_profile = cell_index > self.new_cell_count

        if (should_profile):
            tm = TransformerManager()
            cell_code = tm.transform_cell(cell['source'])

            cell['source'] = cell_code

            cell['source'] = self.get_cell_profiler_code() + self.get_start_parse_code(
                cell_code) + "\n" + cell['source'] + "\n" + self.get_exit_parse_code(cell_code)

        result = super().execute_cell(cell, cell_index, execution_count, store_history)

        if (should_profile):
            output_data_text = result['outputs'][-1].get('text', None)

            data_start_idx = -1
            data_end_idx = -1
            peak_memory_idx = -1
            memory_increment_idx = -1
            for i in range(len(result['outputs']) - 1, -1, -1):
                output_data_text = result['outputs'][i].get('text', None)
                if output_data_text is not None:
                    if output_data_text.find(PROFILER_DATA_STARTS) != -1:
                        data_start_idx = i
                    if output_data_text.find(PROFILER_DATA_ENDS) != -1:
                        data_end_idx = i
                    if output_data_text.find(PROFILER_PEAK_MEMORY) != -1:
                        peak_memory_idx = i
                    if output_data_text.find(PROFILER_MEMORY_INCREMENT) != -1:
                        memory_increment_idx = i

            output_data_text = ""
            start_idx = min([data_start_idx, data_end_idx,
                            peak_memory_idx, memory_increment_idx])
            end_idx = max([data_start_idx, data_end_idx,
                           peak_memory_idx, memory_increment_idx])
            for output in result['outputs'][start_idx: end_idx + 1]:
                output_data_text += output.get('text', '')

            if len(output_data_text) > 0:
                output = {}

                data_match = re.search(r"PROFILER_DATA_STARTS(.*?)PROFILER_DATA_ENDS",
                                       output_data_text, re.DOTALL)
                if data_match:
                    data = data_match.group(1).strip()
                    output = {**ast.literal_eval(data)}

                peak_memory_match = re.search(r"peak memory: (.*?) MiB",
                                              output_data_text, re.DOTALL)
                memory_increment_match = re.search(r"increment: (.*?) MiB",
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

                if len(list(output.keys())) > 0:
                    self.records.append(output)
        return result
