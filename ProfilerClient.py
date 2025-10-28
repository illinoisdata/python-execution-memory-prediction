from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from IPython.core.inputtransformer2 import TransformerManager
import re
import json
import ast

PROFILER_DATA_STARTS = "PROFILER_DATA_STARTS"
PROFILER_DATA_ENDS = "PROFILER_DATA_ENDS"


class ProfilerClient(NotebookClient):
    def __init__(self, nb, record_list):
        super().__init__(nb)
        print("Initialized ProfilerClient")
        self.records = record_list  # shared list to store results
        self.imports = {}
        with open('./TreeParser.py', 'r', encoding='utf-8') as file:
            file_content = file.read()
        self.parser_code = file_content

    def get_start_parse_code(self, code):
        return f"""
parser.start(ast.parse(\"\"\"{code}\"\"\"))
start = time.time()
        """

    def get_exit_parse_code(self, code):
        return f"""
end = time.time()
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
        return cell_count

    def execute_cell(self, cell, cell_index, execution_count=None, store_history=True):
        tm = TransformerManager()
        cell_code = tm.transform_cell(cell['source'])

        cell['source'] = cell_code

        cell['source'] = self.get_start_parse_code(
            cell_code) + "\n" + cell['source'] + "\n" + self.get_exit_parse_code(cell_code)

        if (cell_index == 1):
            cell['source'] = self.parser_code + "\n" + cell['source']

        result = super().execute_cell(cell, cell_index, execution_count, store_history)

        output_data_text = result['outputs'][-1].get('text', None)

        start_idx = -1
        end_idx = -1
        for i in range(len(result['outputs']) - 1, -1, -1):
            output_data_text = result['outputs'][i].get('text', None)
            if output_data_text is not None and output_data_text.find(PROFILER_DATA_STARTS) != -1:
                start_idx = i
            if output_data_text is not None and output_data_text.find(PROFILER_DATA_ENDS) != -1:
                end_idx = i

        output_data_text = ""
        for output in result['outputs'][start_idx: end_idx + 1]:
            output_data_text += output.get('text', '')

        if len(output_data_text) > 0:
            match = re.search(r"PROFILER_DATA_STARTS(.*?)PROFILER_DATA_ENDS",
                              output_data_text, re.DOTALL)
            if match:
                data = match.group(1).strip()
                self.records.append(ast.literal_eval(data))
        return result
