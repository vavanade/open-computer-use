import json

SYSTEM_PROMPT = """
Follow the request below. Every time you want to take an action, make a system call to the appropriate function.
Before using the click tool, always use locate_coordinates to decide where you should click.
You can start GUI applications, but you need to use run_background_command instead of run_command.
GUI apps run this way may take some time to appear. Take a screenshot to confirm it did.
The command to open Firefox GUI is firefox-esr (use a background command).
When there is a next step, always procede to the next step without being asked.
"""


def extract_message_values(obj):
    values = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key != "role":
                values.extend(extract_message_values(value))
    elif isinstance(obj, list):
        for item in obj:
            values.extend(extract_message_values(item))
    else:
        values.append(str(obj))
    return values


def format_message(obj):
    role = obj.get("role", "")
    values = extract_message_values(obj)
    return f"{role.upper()}: {' '.join(value for value in values if value)}"


class QwenAgent:
    functions = []

    def __init__(self, qwen):
        self.qwen = qwen
        self.messages = []
        self.function_map = {}

    def call_function(self, function_call):
        def function_response(message):
            return {"role": "function", "name": func_name, "content": message}

        func_name = function_call["name"].lower()
        func_impl = self.function_map.get(func_name)
        if func_impl:
            try:
                func_args = json.loads(function_call["arguments"])
                result = func_impl(**func_args) if func_args else func_impl()
                return function_response(result)
            except Exception as e:
                return function_response(
                    [{"text": f"Error executing function: {str(e)}"}]
                )
        else:
            return function_response([{"text": "Function not implemented."}])

    def execute_function_calls(self, responses):
        called_function = False
        for rsp in responses:
            if rsp.get("function_call", None):
                called_function = True
                func_rsp = self.call_function(rsp["function_call"])
                self.messages.append(func_rsp)
                print(format_message(func_rsp))
        return called_function

    def initialize(self, instruction):
        self.messages = [
            {"role": "system", "content": [{"text": SYSTEM_PROMPT}]},
            {"role": "user", "content": [{"text": instruction}]},
        ]

    def run(self, instruction):
        if not len(self.messages):
            self.initialize()

        responses = []
        should_continue = True
        n = 1

        while should_continue:
            response_stream = self.qwen.chat(
                messages=self.messages, functions=self.functions
            )
            responses = list(response_stream)[-1]
            for response in responses:
                print(format_message(response))
            self.messages.extend(responses)
            should_continue = self.execute_function_calls(responses)
            n = n + 1
