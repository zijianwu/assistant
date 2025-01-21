
from openai import OpenAI
import os
import json
from assistant.browser import BrowserManager
from assistant.agents.agent_utils import (
    process_functions, append_message, call_planner)

EXECUTOR_MODEL = 'gpt-4o-mini'
PLANNER_MODEL = 'o1-mini'
PLANNER_PROMPT = """
You are a household manager. You will receive a list of website
links to recipes. Your task is to create a detailed plan to review the recipes,
determine if any of them cannot be made due to lack of ingredients available
at the grocery store, and create a shopping list aggregating all the
ingredients needed for the recipes that can be made, including quantities.

You will have access to an LLM agent that is responsible for executing the plan that you create and will return results.

The LLM agent has access to the following functions:
{functions}

When creating a plan for the LLM to execute, break your instructions into a logical, step-by-step order, using the specified format:
    - **Main actions are numbered** (e.g., 1, 2, 3).
    - **Sub-actions are lettered** under their relevant main actions (e.g., 1a, 1b).
        - **Sub-actions should start on new lines**
    - **Specify conditions using clear 'if...then...else' statements** (e.g., 'If the product was purchased within 30 days, then...').
    - **For actions that require using one of the above functions defined**, write a step to call a function using backticks for the function name (e.g., `call the get_inventory_status function`).
        - Ensure that the proper input arguments are given to the model for instruction. There should not be any ambiguity in the inputs.
    - **The last step** in the instructions should always be calling the `instructions_complete` function. This is necessary so we know the LLM has completed all of the instructions you have given it.
    - **Detailed steps** The plan generated must be extremely detailed and thorough with explanations at every step.
Use markdown format when generating the plan with each step and sub-step.

Please find the list of recipe links below.
{text}
"""
EXECUTOR_PROMPT = """
You are a helpful assistant responsible for executing the plan on household 
management. Your task is to follow the plan exactly as it is written 
and perform the necessary actions the tools available to you and asked of you.

You must explain your decision-making process across various steps.

# Steps

1. **Read and Understand plan**: Carefully read and fully understand the given plan on household management.
2. **Identify the exact step in the plan**: Determine which step in the plan you are at, and execute the instructions according to the policy.
3. **Decision Making**: Briefly explain your actions and why you are performing them.
4. **Action Execution**: Perform the actions required by calling any relevant functions and input parameters.

PLAN:
{plan}

"""
TOOLS_SOURCES = [
    "assistant.tools.grocery",
    "assistant.tools.webscraper",
    BrowserManager
]


def call_executor(system_prompt, plan, tools_schema, func_map, message_list, executor_model=EXECUTOR_MODEL):
    executor_plan_prompt = system_prompt.replace("{plan}", plan)
    messages = [
        {'role': 'system', 'content': executor_plan_prompt},
    ]

    while True:
        response = client.chat.completions.create(
            model=executor_model,
            messages=messages,
            tools=tools_schema,
            parallel_tool_calls=False
        )
        
        assistant_message = response.choices[0].message.to_dict()
        print(assistant_message)
        messages.append(assistant_message)

        append_message({'type': 'assistant', 'content': assistant_message.get('content', '')}, message_list)

        if (response.choices[0].message.tool_calls and
            response.choices[0].message.tool_calls[0].function.name == 'instructions_complete'):
            break

        if not response.choices[0].message.tool_calls:
            continue

        for tool in response.choices[0].message.tool_calls:
            tool_id = tool.id
            function_name = tool.function.name
            input_arguments_str = tool.function.arguments
            print(f"#########################################################TOOL USE:", function_name, input_arguments_str)

            append_message({'type': 'tool_call', 'function_name': function_name, 'arguments': input_arguments_str}, message_list)

            try:
                input_arguments = json.loads(input_arguments_str)
            except (ValueError, json.JSONDecodeError):
                continue

            if function_name in func_map:
                try:
                    function_response = func_map[function_name](**input_arguments)
                except Exception as e:
                    function_response = {'error': str(e)}
            else:
                function_response = {'error': f"Function '{function_name}' not implemented."}

            try:
                serialized_output = json.dumps(function_response)
            except (TypeError, ValueError):
                serialized_output = str(function_response)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": serialized_output
            })

            append_message({'type': 'tool_response', 'function_name': function_name, 'response': serialized_output}, message_list)

    return messages


client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
(func_map,
 func_desc_map,
 tools_schema) = process_functions(TOOLS_SOURCES, client=client)

message_list = []
append_message(
    {'type': 'status', 'message': 'Generating plan...'}, message_list)
plan = call_planner(
    system_prompt=PLANNER_PROMPT, 
    func_desc_map=func_desc_map, 
    text="[https://thewoksoflife.com/turnip-cake-lo-bak-go/, https://thewoksoflife.com/braised-eggs-with-noodles/, https://thewoksoflife.com/sesame-chicken/]",
    client=client)
append_message({'type': 'plan', 'content': plan}, message_list)
append_message(
    {'type': 'status', 'message': 'Executing plan...'}, message_list)
messages = call_executor(
    system_prompt=EXECUTOR_PROMPT,
    plan=plan,
    tools_schema=tools_schema,
    func_map=func_map,
    message_list=message_list)
append_message(
    {'type': 'status', 'message': 'Processing complete.'}, message_list)
