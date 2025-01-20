import inspect


def function_to_schema(func) -> dict:
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


from typing import Any, Dict, List, Optional, Type


def class_to_function(cls: Type) -> Dict[str, callable]:
    """
    Convert a class's __init__ and public methods into standalone functions.

    Args:
        cls: The class to convert

    Returns:
        Dict[str, callable]: A dictionary mapping function names to their callable implementations
    """
    functions = {}

    # Get all class attributes including base classes
    class_dict = {}
    for c in inspect.getmro(cls):
        class_dict.update(c.__dict__)

    # Get all imports from the class's module
    module = inspect.getmodule(cls)
    module_dict = {} if module is None else module.__dict__.copy()

    # Get all public methods (excluding dunder methods)
    methods = inspect.getmembers(cls, predicate=inspect.isfunction)
    public_methods = [(name, method) for name, method in methods
                     if not name.startswith('_') or name == '__init__']

    for method_name, method in public_methods:
        # Get the method's signature
        sig = inspect.signature(method)
        params = list(sig.parameters.values())

        # Remove 'self' parameter for instance methods
        if params and params[0].name == 'self':
            params = params[1:]

        # Create new signature without 'self'
        sig.replace(parameters=params)

        # Get the method's docstring and properly format it
        docstring = inspect.getdoc(method) or ""
        formatted_docstring = f'"""{docstring}"""' if docstring else '""""""'

        # Generate the new function name
        if method_name == '__init__':
            new_name = f"initialize_{cls.__name__.lower()}"
        else:
            new_name = f"{method_name}_{cls.__name__.lower()}"

        # Create the new function
        def create_function(method_name=method_name, params=params):
            # Create function argument string
            param_str = ', '.join(str(p) for p in params)

            # Create the function body
            if method_name == '__init__':
                # For __init__, create and return an instance
                func_body = f"""
def {new_name}({param_str}):
    {formatted_docstring}
    instance = {cls.__name__}()
    for key, value in locals().items():
        if key != 'instance' and not key.startswith('__'):
            setattr(instance, key, value)
    return instance
"""
            else:
                # For other methods, create an instance and call the method
                param_names = [p.name for p in params]
                param_pass = ', '.join(param_names)
                func_body = f"""
def {new_name}({param_str}):
    {formatted_docstring}
    instance = {cls.__name__}()
    return getattr(instance, '{method_name}')({param_pass})
"""

            # Create function namespace with all necessary context
            namespace = {
                'cls': cls,
                **class_dict,
                **module_dict,
                'Optional': Optional,
                'List': List,
                'Dict': Dict,
                'Any': Any,
                'Type': Type
            }

            # Execute the function definition
            exec(func_body.strip(), namespace)

            # Return the created function
            return namespace[new_name]

        # Store the created function
        functions[new_name] = create_function()

    return functions


# Example usage:
def convert_and_print_example(cls: Type) -> None:
    """
    Convert a class to functions and print their signatures and docstrings.

    Args:
        cls: The class to convert
    """
    functions = class_to_function(cls)

    print(f"Generated functions from class {cls.__name__}:\n")
    for name, func in sorted(functions.items()):
        print(f"Function: {name}")
        print(f"Signature: {inspect.signature(func)}")
        if doc := inspect.getdoc(func):
            print(f"Docstring:\n{doc}\n")
        else:
            print("No docstring\n")
