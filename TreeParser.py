import builtins
import ast
import sys
from IPython import get_ipython


class TreeParser(ast.NodeTransformer):
    def get_shape(self, variable):
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

    def get_variable_info(self, variable, sliced=False):
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

    def eval_slice(self, slice_node):
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

    def visit_Import(self, node):
        print(ast.dump(node, indent=4))
        for name in node.names:
            self.imports[name.asname if name.asname is not None else name.name] = name.name
        return node

    def visit_ImportFrom(self, node):
        print(ast.dump(node, indent=4))
        for name in node.names:
            self.imports[
                name.asname if name.asname is not None else name.name] = f"{node.module}.{name.name}"
        return node

    def visit_Subscript(self, node: ast.Subscript):
        node.name = self.visit_Name(node.value, node.slice)
        return node

    def visit_Name(self, node: ast.Name, _slice: ast.Slice = None):
        print(ast.dump(node, indent=4))

        if getattr(builtins, node.id, None) is not None or node.id in list(self.imports.keys()):
            self.generic_visit(node)
            return node

        variable = get_ipython().user_ns.get(node.id, None)
        if _slice is not None and isinstance(_slice, ast.Slice):
            variable = variable[self.eval_slice(_slice)]

        if variable is not None:
            variable_info = self.get_variable_info(
                variable, sliced=_slice is not None)
            if variable_info is not None:
                self.variables[node.id] = variable_info
                node.id = variable_info['id']
        else:
            self.variables[node.id] = None

        self.generic_visit(node)
        return node

    def visit_Call(self, node: ast.Call):
        self.generic_visit(node)

        if isinstance(node.func, ast.Name):
            if getattr(builtins, node.func.id, None) is not None:
                self.functions[node.func.id] = {'id': node.func.id, 'args': [arg.id if isinstance(arg, ast.Name) else arg.value for arg in node.args], 'kwargs': {
                    kwarg.arg: kwarg.value.id if isinstance(kwarg.value, ast.Name) else kwarg.value.value for kwarg in node.keywords}}
        return node

    def start(self, node):
        # print(ast.dump(node, indent=4))
        self.generic_visit(node)
        self.variables_ip = self.variables.copy()
        self.variables = {}

    def exit(self, node):
        self.generic_visit(node)
        self.variables_op = self.variables.copy()
        self.variables = {}

    def __init__(self, imports={}):
        self.imports = imports
        self.variables = {}
        self.functions = {}
