from os_computer_use.grounding import draw_big_dot, extract_bbox_midpoint
from os_computer_use.llm import (
    call_grounding_model,
    call_action_model,
    call_vision_model,
    Message,
    Text,
    Image as Base64Image,
)
from os_computer_use.utils import print_colored

import shlex
import os
import tempfile
from PIL import Image
import json

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

tools = {
    "stop": {
        "description": "Indicate that the task has been completed.",
        "params": {},
    }
}


class SandboxAgent:

    def __init__(self, sandbox):
        super().__init__()
        self.messages = []
        self.sandbox = sandbox
        self.latest_screenshot = None
        self.tmp_dir = tempfile.mkdtemp()
        self.image_counter = 0

    def call_function(self, name, arguments):

        func_impl = getattr(self, name.lower()) if name.lower() in tools else None
        if func_impl:
            try:
                func_args = json.loads(arguments)
                result = func_impl(**func_args) if func_args else func_impl()
                return result
            except Exception as e:
                return f"Error executing function: {str(e)}"
        else:
            return "Function not implemented."

    def tool(description, params):
        def decorator(func):
            tools[func.__name__] = {"description": description, "params": params}
            return func

        return decorator

    def save_image(self, image, prefix="image"):
        self.image_counter += 1
        filename = f"{prefix}_{self.image_counter}.png"
        filepath = os.path.join(self.tmp_dir, filename)
        if isinstance(image, Image.Image):
            image.save(filepath)
        else:
            with open(filepath, "wb") as f:
                f.write(image)
        return filepath

    def take_screenshot(self):
        file = self.sandbox.take_screenshot()
        filename = self.save_image(file, "screenshot")
        print_colored(f"screenshot {filename}", color="gray")
        self.latest_screenshot = filename
        with open(filename, "rb") as image_file:
            return image_file.read()

    @tool(
        description="Run a shell command and return the result.",
        params={"command": "Shell command to run"},
    )
    def run_command(self, command):
        result = self.sandbox.commands.run(command, timeout=5)
        stdout, stderr = result.stdout, result.stderr
        if stdout and stderr:
            return stdout + "\n" + stderr
        elif stdout or stderr:
            return stdout + stderr
        else:
            return "Done."

    @tool(
        description="Run a shell command in the background.",
        params={"command": "Shell command to run without waiting"},
    )
    def run_background_command(self, command):
        self.sandbox.commands.run(command, background=True)
        return "Done."

    @tool(
        description="Send a key or combination of keys to the system.",
        params={"name": "Key or combination (e.g. 'Return', 'Ctl-C')"},
    )
    def send_key(self, name):
        self.sandbox.commands.run(f"xdotool key -- {name}")
        return "Done."

    @tool(
        description="Type a specified text into the system.",
        params={"text": "Text to type"},
    )
    def type_text(self, text):
        def chunks(text, n):
            for i in range(0, len(text), n):
                yield text[i : i + n]

        results = []
        for chunk in chunks(text, TYPING_GROUP_SIZE):
            cmd = f"xdotool type --delay {TYPING_DELAY_MS} -- {shlex.quote(chunk)}"
            results.append(self.sandbox.commands.run(cmd))
        return "Done."

    @tool(
        description="Click on a specified UI element.",
        params={"query": "Item or UI element on the screen to click"},
    )
    def click(self, query):
        self.take_screenshot()
        bbox, image_url = call_grounding_model(
            query + "\nReturn the response in the form of a bbox",
            self.latest_screenshot,
        )
        position = extract_bbox_midpoint(bbox)
        print_colored(f"bbox {image_url}", color="gray")

        dot_image = draw_big_dot(Image.open(self.latest_screenshot), position)
        filepath = self.save_image(dot_image, "location")
        print_colored(f"click {filepath})", color="gray")

        x, y = position
        self.sandbox.commands.run(f"xdotool mousemove --sync {x} {y}")
        self.sandbox.commands.run("xdotool click 1")
        return "Done."

    def append_screenshot(self):
        convert_to_content = lambda message: (
            Base64Image(message) if isinstance(message, bytes) else Text(message)
        )
        return call_vision_model(
            [
                *self.messages,
                Message(
                    map(
                        convert_to_content,
                        [
                            "QUESTION: What is the best next action to take in order to complete the objective?",
                            "CONTEXT: Use this screenshot to decide what to do:",
                            self.take_screenshot(),
                            "You can click, type, use keyboard commands and run shell commands. Be concise.",
                            "If the objective appears to be complete, then simply state the the objective is complete.",
                            "DECISION:",
                        ],
                    ),
                    role="user",
                    log=False,
                ),
            ]
        )

    def run(self, instruction):

        self.messages.append(Message(f"OBJECTIVE: {instruction}", log=False))

        should_continue = True
        while should_continue:

            content, tool_calls = call_action_model(
                [
                    Message(
                        "You are an AI assistant with computer use abilities.",
                        role="system",
                        log=False,
                    ),
                    *self.messages,
                    Message(f"CONTEXT: {self.append_screenshot()}", color="green"),
                    Message(
                        "I will now use tool calls to take these actions, or use the stop command if the objective is complete.",
                        log=False,
                    ),
                ],
                tools,
            )

            if content:
                self.messages.append(Message(f"THOUGHT: {content}", color="blue"))

            should_continue = False
            for tool_call in tool_calls:
                should_continue = tool_call.function.name != "stop"
                if not should_continue:
                    break

                name, arguments = tool_call.function.name, tool_call.function.arguments
                self.messages.append(
                    Message(f"ACTION: {name} {str(arguments)}", color="red")
                )

                result = self.call_function(name, arguments)
                self.messages.append(Message(f"OBSERVATION: {result}", color="yellow"))
