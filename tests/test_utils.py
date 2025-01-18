from assistant.utils import (
    function_to_schema
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
