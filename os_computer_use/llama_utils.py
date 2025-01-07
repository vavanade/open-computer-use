import json
import re


def create_llama_function_list(definitions):
    functions = []

    for name, details in definitions.items():
        properties = {}
        required = []

        for param_name, param_desc in details["params"].items():
            properties[param_name] = {"type": "string", "description": param_desc}
            required.append(param_name)

        function_def = {
            "type": "function",
            "function": {
                "name": name,
                "description": details["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
        functions.append(function_def)

    return functions


def parse_llama_tool_calls(content, tool_calls):

    combined_tool_calls = []
    for tool_call in tool_calls:
        try:
            parameters = json.loads(tool_call.function.arguments)
            combined_tool_calls.append(
                {
                    "type": "function",
                    "name": tool_call.function.name,
                    "parameters": parameters,
                }
            )
        except json.JSONDecodeError:
            print(
                f"Error decoding JSON for tool call arguments: {tool_call.function.arguments}"
            )

    if content and not tool_calls:
        try:
            tool_call = json.loads(re.search(r"\{.*\}", content).group(0))
            if tool_call.get("name") and tool_call.get("parameters"):
                combined_tool_calls.append(tool_call)
                return None, combined_tool_calls
        except Exception as e:
            pass

    return content, combined_tool_calls
