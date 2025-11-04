import builtins
import ast
import sys
from IPython import get_ipython


class TreeParser(ast.NodeTransformer):
    def get_shape(self, variable):
        try:
            if hasattr(variable, "shape") and not hasattr(variable.shape, "__call__"):
                shape = tuple(variable.shape)
                if len(shape) > 0:
                    return shape
                else:
                    return None
            elif hasattr(variable, "__len__"):
                return len(variable)
            else:
                return None
        except Exception:
            return None

    def get_variable_info(self, variable, sliced=False):
        try:
            classname = variable.__class__
            module = classname.__module__
            name = classname.__name__

            if name != 'function':
                shape = self.get_shape(variable)
                size = sys.getsizeof(variable)
                id = name if module == 'builtins' else f"{module}.{name}"
                variable_info = {
                    'id': id, 'shape': shape, 'size': size, 'sliced': sliced}
                return variable_info
            else:
                return None
        except Exception:
            return None

    def eval_slice(self, slice_node):
        try:
            if isinstance(slice_node, ast.Slice):
                lower = eval(compile(ast.Expression(slice_node.lower),
                                     '', 'eval')) if slice_node.lower else None
                upper = eval(compile(ast.Expression(slice_node.upper),
                                     '', 'eval')) if slice_node.upper else None
                step = eval(compile(ast.Expression(slice_node.step),
                            '', 'eval')) if slice_node.step else None
                return slice(lower, upper, step)
            elif isinstance(slice_node, ast.Tuple):
                return tuple(self.eval_slice(elt) for elt in slice_node.elts)
            else:
                return eval(compile(ast.Expression(slice_node), '', 'eval'))
        except Exception:
            return None

    def visit_Import(self, node):
        for name in node.names:
            self.imports[name.asname if name.asname is not None else name.name] = name.name
            name.asname = None
        return node

    def visit_ImportFrom(self, node):
        for name in node.names:
            self.imports[
                name.asname if name.asname is not None else name.name] = f"{node.module}.{name.name}"
            name.asname = None
        return node

    def visit_Subscript(self, node: ast.Subscript):
        try:
            if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name):
                node.value.value = self.visit_Name(
                    node.value.value, node.slice, node.value.attr)
            elif isinstance(node.value, ast.Name):
                node.value = self.visit_Name(node.value, node.slice)
            else:
                self.generic_visit(node)
            return node
        except Exception:
            return node

    def visit_Name(self, node: ast.Name, _slice: ast.Slice = None, attr: str = None):
        try:
            node_id = node.id
            if getattr(builtins, node_id, None) is not None:
                self.generic_visit(node)
                return node

            if node_id in list(self.imports.keys()):
                node.id = self.imports[node_id]
                self.local_imports[node_id] = self.imports[node_id]
                self.generic_visit(node)
                return node

            variable = get_ipython().user_ns.get(node_id, None)
            if attr is not None and hasattr(variable, attr):
                variable = getattr(variable, attr)
                node_id = f"{node_id}.{attr}"
            if _slice is not None and isinstance(_slice, ast.Slice):
                _s = self.eval_slice(_slice)
                if _s is None:
                    return node
                else:
                    variable = variable[_s]

            if variable is not None:
                variable_info = self.get_variable_info(
                    variable, sliced=_slice is not None)
                if variable_info is not None:
                    self.variables[node_id] = variable_info
                    node.id = variable_info['id']
            else:
                self.variables[node_id] = None

            self.generic_visit(node)
            return node
        except Exception:
            return node

    def visit_Call(self, node: ast.Call):
        self.generic_visit(node)
        return node

    def start(self, code):
        self.local_imports = {}
        self.cell_code = code
        node = ast.parse(self.cell_code)
        self.generic_visit(node)
        self.variables_ip = self.variables.copy()
        self.variables = {}

    def exit(self):
        self.local_imports = {}
        node = ast.parse(self.cell_code)
        self.generic_visit(node)
        self.variables_op = self.variables.copy()
        self.variables = {}
        cell_code = self.cell_code
        self.cell_code = None
        return cell_code, ast.unparse(node)

    def __init__(self):
        self.imports = {}
        self.variables = {}
        self.cell_code = None


parser = TreeParser()
