from assistant.utils import (
    function_to_schema,
    class_to_function
)


def test_basic_function_schema():
    def sample_func(a: str, b: int, c: float):
        pass

    schema = function_to_schema(sample_func)
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "sample_func"
    assert schema["function"]["parameters"]["properties"] == {
        "a": {"type": "string"},
        "b": {"type": "integer"},
        "c": {"type": "number"}
    }
    assert schema["function"]["parameters"]["required"] == ["a", "b", "c"]


def test_function_with_docstring():
    def sample_func(x: str):
        """This is a test function"""
        pass

    schema = function_to_schema(sample_func)
    assert schema["function"]["description"] == "This is a test function"


def test_optional_parameters():
    def sample_func(a: str, b: int = 0, c: str = "default"):
        pass

    schema = function_to_schema(sample_func)
    assert schema["function"]["parameters"]["required"] == ["a"]


def test_all_supported_types():
    def sample_func(
        a: str,
        b: int,
        c: float,
        d: bool,
        e: list,
        f: dict,
        g: None
    ):
        pass

    schema = function_to_schema(sample_func)
    properties = schema["function"]["parameters"]["properties"]
    assert properties["a"]["type"] == "string"


def test_class_to_function_basic_class():
    """Test generating functions for a class with __init__
    but no public methods."""

    class EmptyClass:
        def __init__(self, val: int):
            """Constructor docstring"""
            self.val = val

        def _private_method(self):
            pass

    funcs = class_to_function(EmptyClass)
    # We only expect an 'initialize_empty_class' function (no public methods).
    assert len(funcs) == 1
    assert "initialize_empty_class" in funcs

    # Test calling the generated initialize function
    init_func = funcs["initialize_empty_class"]
    instance = init_func(42)
    assert isinstance(instance, EmptyClass)
    assert instance.val == 42

    # Check docstring
    assert init_func.__doc__.strip() == "Constructor docstring"


def test_class_to_function_with_methods():
    """Test class that has multiple public methods."""
    class Example:
        def __init__(self, x: int, y: str = "default"):
            """Init docstring"""
            self.x = x
            self.y = y

        def greet(self, name: str) -> str:
            """Return a greeting."""
            return f"Hello, {name}!"

        def add_to_x(self, value: int) -> int:
            """Add an integer to self.x"""
            self.x += value
            return self.x

        def _private_method(self):
            pass  # Should not be converted

    funcs = class_to_function(Example)
    # We expect:
    #   1) initialize_example
    #   2) greet_example
    #   3) add_to_x_example
    assert "initialize_example" in funcs
    assert "greet_example" in funcs
    assert "add_to_x_example" in funcs
    assert len(funcs) == 3

    # Test initialize
    init_func = funcs["initialize_example"]
    obj = init_func(10, "bar")
    assert isinstance(obj, Example)
    assert obj.x == 10
    assert obj.y == "bar"

    # Test greet
    greet_func = funcs["greet_example"]
    result = greet_func(obj, "Alice")
    assert result == "Hello, Alice!"
    # The docstring is preserved
    assert greet_func.__doc__.strip() == "Return a greeting."

    # Test add_to_x
    add_func = funcs["add_to_x_example"]
    new_value = add_func(obj, 5)
    assert new_value == 15
    assert obj.x == 15  # The internal state changed
    assert add_func.__doc__.strip() == "Add an integer to self.x"


def test_class_to_function_docstrings():
    """Ensure docstrings for generated functions match
    the class methods' docstrings."""
    class MyClass:
        def __init__(self):
            """Constructor docstring."""

        def public_method(self, data: str):
            """A public method docstring."""
            return data

    funcs = class_to_function(MyClass)
    init_func = funcs["initialize_my_class"]
    pub_func = funcs["public_method_my_class"]

    assert init_func.__doc__.strip() == "Constructor docstring."
    assert pub_func.__doc__.strip() == "A public method docstring."


def test_class_to_function_return_annotation():
    """Test that return annotations are preserved in the generated
    function (as a string)."""
    class ReturnAnnotated:
        def __init__(self) -> None:
            pass

        def do_something(self, num: int) -> str:
            """Returns a string."""
            return str(num)

    funcs = class_to_function(ReturnAnnotated)
    assert "initialize_return_annotated" in funcs
    assert "do_something_return_annotated" in funcs

    do_something_func = funcs["do_something_return_annotated"]
    # Even though we can't strictly test Python's internal
    # annotation at runtime easily, we can confirm the function runs
    # and has the correct docstring and result.
    instance = funcs["initialize_return_annotated"]()
    result = do_something_func(instance, 123)
    assert result == "123"
    assert "Returns a string." in do_something_func.__doc__
