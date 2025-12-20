import ast
from IPython.core.inputtransformer2 import TransformerManager
import builtins


class TreeParser(ast.NodeTransformer):
    def __init__(self):
        self.imports = {}
        self.class_defs = {}
        self.variables = set()

    def visit_Import(self, node: ast.Import):
        for name in node.names:
            self.imports[name.asname if name.asname is not None else name.name] = name.name
            name.asname = None
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for name in node.names:
            self.imports[
                name.asname if name.asname is not None else name.name] = f"{node.module}.{name.name}"
            name.asname = None
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_defs[node.name] = ast.unparse(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        return node

    def visit_Name(self, node: ast.Name):
        node_id = node.id

        if node_id == "_" or getattr(builtins, node_id, None) is not None:
            self.generic_visit(node)
            return node

        if node_id in list(self.imports.keys()):
            node.id = self.imports[node_id]
            self.local_imports[node_id] = self.imports[node_id]
        else:
            self.variables.add(node_id)

        self.generic_visit(node)
        return node

    def start(self, code):
        self.local_imports = {}
        self.variables = set()

        # Clean code
        lines = code.splitlines()
        cleaned_lines = []

        for line in lines:
            if line.startswith("%") or line.startswith("!") or line.startswith("?"):
                continue
            if line.startswith("%%"):
                continue
            if line.startswith("#"):
                continue
            cleaned_lines.append(line)

        code = "\n".join(cleaned_lines)
        tm = TransformerManager()
        code = tm.transform_cell(code)

        node = ast.parse(code)
        self.generic_visit(node)
        return code, self.local_imports, list(self.variables)
