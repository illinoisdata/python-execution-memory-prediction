import ast

class TreeParser(ast.NodeTransformer):
    def __init__(self):
        self.imports = {}
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
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        return node

    def visit_Name(self, node: ast.Name):
        node_id = node.id

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
        node = ast.parse(code)
        self.generic_visit(node)
        return self.local_imports, list(self.variables)
