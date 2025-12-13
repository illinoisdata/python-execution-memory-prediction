from IPython import get_ipython
import sys
from io import StringIO


def get_shape(variable):
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


def get_variable_value(variable):
    classname = variable.__class__
    module = classname.__module__
    name = classname.__name__

    try:
        base_classes = variable.__class__.__bases__

        if name in ['int', 'float', 'str', 'bool', 'NoneType']:
            return {'value': variable, id: name}
        elif "torch.nn.modules.module" in base_classes:
            return {'value': str(variable), id: classname.__base__.__module__}
        elif "keras.src.models.model" in base_classes:
            s = StringIO()
            variable.summary(print_fn=lambda x: s.write(x + "\n"))
            summary_str = s.getvalue()
            return {'value': summary_str, id: classname.__base__.__module__}
        else:
            return {'value': 'NoValue', id: name if module == 'builtins' else f"{module}.{name}"}
    except:
        return {'value': 'NoValue', id: name if module == 'builtins' else f"{module}.{name}"}


def get_variable_info(id):
    variable = get_ipython().user_ns.get(id, None)

    if variable is None:
        return None

    try:
        classname = variable.__class__
        name = classname.__name__

        if name != 'function':
            shape = get_shape(variable)
            size = sys.getsizeof(variable)
            variable_info = {
                **get_variable_value(variable), 'shape': shape, 'size': size}
            return variable_info
        else:
            return None
    except Exception:
        return None
