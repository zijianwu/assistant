import inspect
from assistant.utils import (extract_functions_from_package,
                             function_to_schema,
                             class_to_function)
from typing import List, Union, Type

SIMPLE_LLM_MODEL = 'gpt-4o-mini'
EXECUTOR_MODEL = 'gpt-4o-mini'
PLANNER_MODEL = 'o1-mini'


def append_message(message, message_list):
    """
    Appends a message to a message list and prints it according to its type.

    This function handles different types of messages ('status', 'plan', 'assistant',
    'function_call', 'function_response') and formats their output accordingly.

    Args:
        message (dict): The message to append. Expected to have a 'type' key and content
                       specific to the message type:
                       - 'status': requires 'message' key
                       - 'plan', 'assistant': requires 'content' key
                       - 'function_call': requires 'function_name' and 'arguments' keys
                       - 'function_response': requires 'function_name' and 'response' keys
        message_list (list): The list to append the message to

    Returns:
        None

    Example:
        >>> message = {'type': 'status', 'message': 'Processing...'}
        >>> messages = []
        >>> append_message(message, messages)
        Processing...
    """
    message_list.append(message)
    # Optionally, print the message for immediate feedback
    message_type = message.get('type', '')
    if message_type == 'status':
        print(message['message'])
    elif message_type == 'plan':
        print("\nPlan:\n", message['content'])
    elif message_type == 'assistant':
        print("\nAssistant:\n", message['content'])
    elif message_type == 'function_call':
        print(f"\nFunction call: {message['function_name']} with arguments {message['arguments']}")
    elif message_type == 'function_response':
        print(f"\nFunction response for {message['function_name']}: {message['response']}")
    else:
        # Handle any other message types or default case
        print(message.get('content', ''))


def simple_call_gpt_model(system_prompt, text,
                          client, max_tokens, model=SIMPLE_LLM_MODEL):
    """
    Make a simple API call to GPT model with a system prompt and text input.

    Args:
        system_prompt (str): The system prompt template with {text} placeholder
        text (str): The text to be inserted into system prompt
        client (OpenAI): The OpenAI client instance
        max_tokens (int): Maximum number of tokens in the response
        model (str, optional): The GPT model to use. Defaults to SIMPLE_LLM_MODEL.

    Returns:
        str: The stripped response content from the GPT model

    Example:
        >>> prompt = "Summarize the following text: {text}"
        >>> text = "Long article content..."
        >>> response = simple_call_gpt_model(prompt, text, client, 100)
    """
    prompt = system_prompt.replace("{text}", text)
    messages = [{'role': 'system', 'content': prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()


def get_simple_planner_func_desc(functions_archive: dict,
                                 client,
                                 model=SIMPLE_LLM_MODEL,
                                 max_tokens=200,):
    """
    Creates simplified descriptions of functions from a function archive.
    Function archive is a dict with function names as keys and dictionaries with
    'function' and 'description' as values.

    This function takes a dictionary of functions and their descriptions, and generates
    concise, user-friendly descriptions of what each function does using an LLM model.

    Args:
        functions_archive (dict): Dictionary containing function names as keys and
            dictionaries with 'function' and 'description' as values.
        client: The LLM client used to generate descriptions.
        model (str, optional): The LLM model to use. Defaults to SIMPLE_LLM_MODEL.
        max_tokens (int, optional): Maximum number of tokens for the response.
            Defaults to 200.

    Returns:
        dict: A dictionary mapping function signatures to their simplified descriptions.
    """
    FUNCTION_CLEANUP_PROMPT = """
    You are a helpful assistant responsible for creating concise
    descriptions of functions.

    You will be given a function signature and a brief description of the
    function's purpose. You should return a concise summary of what
    the function does (not how it does it) that is understandable
    to a general audience.

    Function Signature:
    {text}
    """
    func_desc_map = {f"{name}{inspect.signature(func_and_desc['function'])}":
                     func_and_desc['description'] for name, func_and_desc
                     in functions_archive.items()}
    func_desc_map = {name: simple_call_gpt_model(FUNCTION_CLEANUP_PROMPT,
                                                 desc,
                                                 client,
                                                 max_tokens,
                                                 model)
                     for name, desc in func_desc_map.items()}
    return func_desc_map


def process_functions(sources: List[Union[str, Type]], client) -> tuple:
    """
    Process a list of Python modules (as strings) or classes to extract functions and metadata.

    Args:
        sources (List[Union[str, Type]]): A list of module names (strings) or class types.
        client: OpenAI client object for making API calls.

    Returns:
        tuple: Contains:
            - func_map: A dictionary mapping function names to function objects.
            - func_desc_map: A dictionary mapping function names to descriptions.
            - tools_schema: A list of tool schemas generated from the functions.
    """
    functions_archive = {}

    for source in sources:
        if isinstance(source, str):
            # Process modules
            functions_list = [func for func in extract_functions_from_package(source)]
        elif inspect.isclass(source):
            # Process classes
            functions_list = class_to_function(source).values()
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

        functions_archive.update({
            func.__name__: {
                'function': func,
                'description': inspect.getdoc(func)
            } for func in functions_list
        })

    func_map = {name: func_and_desc['function'] for name, func_and_desc in functions_archive.items()}
    tools_schema = [function_to_schema(func) for func in func_map.values()]
    tools_schema.append({
        "type": "function",
        "function": {
            "name": "instructions_complete",
            "description": "Function should be called when we have completed ALL of the instructions.",
        },
    })

    func_desc_map = get_simple_planner_func_desc(
        functions_archive=functions_archive,
        client=client,
        model=SIMPLE_LLM_MODEL,
        max_tokens=200
    )

    return func_map, func_desc_map, tools_schema


def call_planner(system_prompt, func_desc_map, text, client):
    """
    Calls the AI planner to generate a plan based on system prompt, available functions, and input text.
    Args:
        system_prompt (str): Template string containing placeholders for functions and text
        func_desc_map (dict): Dictionary mapping function names to their descriptions
        text (str): Input text to be processed
        client: OpenAI client instance for making API calls
    Returns:
        str: Generated plan from the AI model
    The function:
    1. Formats function descriptions into a string
    2. Replaces placeholders in system prompt with functions and text
    3. Makes API call to get completion
    4. Returns generated plan text
    Example:
        func_map = {
            "analyze": "Analyzes text sentiment",
            "summarize": "Creates text summary"
        }
        plan = call_planner(prompt_template, func_map, "Process this text", client)
    """
    func_desc_text = "\n    ".join([f"- {name}: {desc}" for name, desc in func_desc_map.items()])
    system_prompt = system_prompt.replace("{functions}", func_desc_text)
    system_prompt = system_prompt.replace("{text}", text)
    prompt = system_prompt + "\n\nPlease provide the next steps in your plan."

    response = client.chat.completions.create(
        model=PLANNER_MODEL,
        messages=[{'role': 'user', 'content': prompt}]
    )
    plan = response.choices[0].message.content

    return plan
