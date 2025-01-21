import inspect
import re
from types import FunctionType
from typing import Any, Dict, Type, get_type_hints
import importlib


def function_to_schema(func) -> dict:
    """Converts a Python function to a JSON Schema compatible dictionary.

    This function analyzes a Python function's signature and documentation to create a schema
    that follows the OpenAI function calling format. It maps Python types to JSON Schema types
    and captures required parameters.

    Args:
        func: The Python function to convert to a schema.

    Returns:
        dict: A dictionary containing the function schema with the following structure:
            {
                    "name": str,  # Function name
                    "description": str,  # Function docstring
                        "properties": dict,  # Parameter names and their types
                        "required": list  # List of required parameter names

    Raises:
        ValueError: If unable to get the function signature
        KeyError: If encountering an unknown type annotation

    Example:
        def greet(name: str, age: int = None):
            '''Greets a person'''
            pass

        schema = function_to_schema(greet)
        # Returns a schema with name and age parameters, where name is required
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for"
                f"parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }


def class_to_function(cls: Type[Any]) -> Dict[str, FunctionType]:
    """
    Converts a class's __init__ and public methods into standalone functions.

    - The constructor becomes `initialize_<classname_in_snake_case>`.
    - Each public method becomes `<methodname>_<classname_in_snake_case>`.
    - Generated functions preserve the original docstring and type hints.
    - For methods that require 'self', the generated function prepends
      a parameter referencing an instance of `cls`.

    Args:
        cls: The class to generate standalone functions for.

    Returns:
        A dictionary mapping each generated function name to the function
        object.
    """

    def snake_case(name: str) -> str:
        """Helper to convert CamelCase or PascalCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.lower()

    def generate_initialize_func(cls: Type[Any]) -> FunctionType:
        """
        Generate a function that calls the class's __init__. The function name
        will be `initialize_<classname_in_snake_case>`.
        """
        init_method = cls.__init__

        # Retrieve signature and type hints
        sig = inspect.signature(init_method)
        type_hints = get_type_hints(init_method)

        # Build the function name
        func_name = f"initialize_{snake_case(cls.__name__)}"

        # Build function parameter list (minus 'self')
        params_code = []
        for name, param in sig.parameters.items():
            if name == 'self':
                continue
            annotation = type_hints.get(name, Any)

            # Convert the annotation to string form for code generation
            # (Simple approach: use annotation.__name__ if available,
            # else "Any")
            annotation_str = getattr(annotation, '__name__', 'Any')

            if param.default is param.empty:
                # No default
                params_code.append(f"{name}: {annotation_str}")
            else:
                # Provide the default
                default_val = repr(param.default)
                params_code.append(f"{name}: {annotation_str} = {default_val}")

        # Combine parameter list into a string
        params_str = ", ".join(params_code)

        # Typically __init__ returns None, but let's see if we can find
        #  a return type
        return_annotation = type_hints.get('return', None)
        if return_annotation is None:
            return_annotation_str = " -> None"
        else:
            return_annotation_str = f" -> {
                getattr(return_annotation, '__name__', 'Any')
                }"

        # Get docstring from __init__
        docstring = init_method.__doc__ or ""

        # CHANGED: build the call args safely (without set subtraction)
        call_args_str = ", ".join(
            name for name in sig.parameters if name != 'self'
        )

        # Construct the function body. This function instantiates the class.
        func_code = f"""
def {func_name}({params_str}){return_annotation_str}:
    \"\"\"{docstring}\"\"\"
    return {cls.__name__}({call_args_str})
"""
        # Compile and return the function object
        scope: Dict[str, Any] = {
            cls.__name__: cls,
            "Any": Any
        }
        # Ensure all annotated types are in scope
        for ann in type_hints.values():
            if hasattr(ann, "__name__"):
                scope[ann.__name__] = ann
        exec(func_code, scope)
        return scope[func_name]

    def generate_method_func(
            method_name: str, method_obj: Any
            ) -> FunctionType:
        """
        Generate a standalone function for a public method. The new function
        will be named `<methodname>_<classname_in_snake_case>` and it will
        prepend a parameter referencing the instance of the class.
        """

        sig = inspect.signature(method_obj)
        type_hints = get_type_hints(method_obj)
        docstring = method_obj.__doc__ or ""

        # The new function name: e.g. "start_browsermanager"
        func_name = f"{method_name}_{snake_case(cls.__name__)}"

        # Build function parameter list: rename `self` to e.g.
        # `browser_manager: BrowserManager`
        params_code = []
        self_param_name = snake_case(cls.__name__)
        params_code.append(f"{self_param_name}: {cls.__name__}")

        for name, param in sig.parameters.items():
            if name == 'self':
                continue
            annotation = type_hints.get(name, Any)
            annotation_str = getattr(annotation, '__name__', 'Any')
            if param.default is param.empty:
                params_code.append(f"{name}: {annotation_str}")
            else:
                default_val = repr(param.default)
                params_code.append(f"{name}: {annotation_str} = {default_val}")

        params_str = ", ".join(params_code)

        return_annotation = type_hints.get('return', None)
        if return_annotation:
            return_annotation_str = f" -> {getattr(return_annotation,
                                                   '__name__', 'Any')}"
        else:
            return_annotation_str = ""

        # CHANGED: safely gather call args
        call_args_str = ", ".join(
            name for name in sig.parameters if name != 'self'
        )

        # Generate function code
        func_code = f"""
def {func_name}({params_str}){return_annotation_str}:
    \"\"\"{docstring}\"\"\"
    return {self_param_name}.{method_name}({call_args_str})
"""

        # Compile the function object in a dynamic scope
        scope: Dict[str, Any] = {
            cls.__name__: cls,
            "Any": Any
        }
        for ann in type_hints.values():
            if hasattr(ann, "__name__"):
                scope[ann.__name__] = ann
        exec(func_code, scope)
        return scope[func_name]

    # 1) Generate the initialize function for __init__
    functions = {}
    init_func = generate_initialize_func(cls)
    functions[init_func.__name__] = init_func

    # 2) Generate functions for each *public* method
    public_methods = [
        (name, obj)
        for name, obj in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")  # skip underscore methods
    ]

    for method_name, method_obj in public_methods:
        new_func = generate_method_func(method_name, method_obj)
        functions[new_func.__name__] = new_func

    return functions


def extract_functions_from_package(module_path):
    """
    Dynamically imports the given module_path and returns a list of
    the functions defined in that module.

    :param module_path: A string representing the path of the module/package,
                        e.g. "assistant.tools.grocery"
    :return: A list of function objects defined in the specified module.
    """
    # Import the module dynamically
    module = importlib.import_module(module_path)

    # Get all members of the module that are functions
    all_functions = inspect.getmembers(module, inspect.isfunction)

    # (Optional) Filter out functions not defined in this module
    # i.e. skip any function whose __module__ is not module_path
    # This avoids returning functions that might have been imported into the module.
    filtered_functions = [
        func for name, func in all_functions
        if func.__module__ == module.__name__
    ]

    return filtered_functions
