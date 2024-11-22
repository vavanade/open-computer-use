from os_computer_use.utils import (
    convert_to_base64,
    send_bbox_request,
    extract_bbox_midpoint,
    draw_big_dot,
)
from os_computer_use.agent import QwenAgent

from qwen_agent.llm.schema import ContentItem

import shlex
import json
from PIL import Image
from IPython import display

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50
SCREENSHOT_PATH = "./screenshot.png"


class SandboxAgent(QwenAgent):
    functions = [
        {
            "name": "screenshot",
            "description": "Captures a screenshot of the current system view.",
            "parameters": {},
        },
        {
            "name": "send_key",
            "description": "Send a single key or key combination to the system using xdotool.",
            "parameters": {
                "name": "text",
                "type": "string",
                "description": "The key or key combination to send",
                "required": True,
            },
        },
        {
            "name": "type_text",
            "description": "Type text into the system using xdotool with a specified delay.",
            "parameters": {
                "name": "text",
                "type": "string",
                "description": "The text to type",
                "required": True,
            },
        },
        {
            "name": "run_command",
            "description": "Run a command on the system.",
            "parameters": {
                "name": "command",
                "type": "string",
                "description": "The command to run",
                "required": True,
            },
        },
        {
            "name": "run_background_command",
            "description": "Run a command on the system without waiting for it to finish.",
            "parameters": {
                "name": "command",
                "type": "string",
                "description": "The command to run",
                "required": True,
            },
        },
        {
            "name": "locate_coordinates",
            "description": "",
            "parameters": {
                "name": "query",
                "type": "string",
                "description": "The action or UI element on the screen to return coordinates for.",
                "required": True,
            },
        },
        {
            "name": "click",
            "description": "",
            "parameters": [
                {
                    "name": "x",
                    "type": "number",
                    "description": "The x-coordinate in pixels.",
                    "required": True,
                },
                {
                    "name": "y",
                    "type": "number",
                    "description": "The y-coordinate in pixels.",
                    "required": True,
                },
            ],
        },
    ]

    def __init__(self, qwen, sandbox):
        super().__init__(qwen)
        self.sandbox = sandbox
        self.latest_screenshot = None
        self.function_map = {
            "screenshot": self.screenshot,
            "send_key": self.send_key,
            "type_text": self.type_text,
            "run_command": self.run_command,
            "run_background_command": self.run_background_command,
            "locate_coordinates": self.locate_coordinates,
            "click": self.click,
        }

    def screenshot(self):
        filename = SCREENSHOT_PATH
        with open(filename, "wb") as f:
            file = self.sandbox.screenshot()
            f.write(file)
        display.display(display.Image(filename))
        self.latest_screenshot = filename
        return [
            ContentItem(image=filename),
            ContentItem(text=f"(The URL of this image is {filename})"),
        ]

    def run_command(self, command):
        result = self.sandbox.commands.run(command)
        return [{"text": json.dumps({"output": result.stdout, "error": result.stderr})}]

    def run_background_command(self, command):
        self.sandbox.commands.run(command, background=True)
        return [{"text": "Done."}]

    def send_key(self, text):
        self.sandbox.commands.run(f"xdotool key -- {text}")
        return [{"text": "Done."}]

    def type_text(self, text):
        def chunks(text, n):
            for i in range(0, len(text), n):
                yield text[i : i + n]

        results = []
        for chunk in chunks(text, TYPING_GROUP_SIZE):
            cmd = f"xdotool type --delay {TYPING_DELAY_MS} -- {shlex.quote(chunk)}"
            results.append(self.sandbox.commands.run(cmd))
        return [{"text": "Done."}]

    def locate_coordinates(self, query):
        self.screenshot()
        original_image = Image.open(self.latest_screenshot)
        image_base64, mime_type = convert_to_base64(original_image)
        bbox_response = send_bbox_request(image_base64, mime_type, query)
        x_scaled, y_scaled = extract_bbox_midpoint(bbox_response)
        image_width, image_height = original_image.size
        x, y = int(x_scaled * image_width / 1000), int(y_scaled * image_height / 1000)
        display.display(draw_big_dot(original_image, (x, y)))
        return f"({x},{y})"

    def click(self, x, y):
        self.sandbox.commands.run(f"xdotool mousemove --sync {x} {y}")
        self.sandbox.commands.run("xdotool click 1")

    def run(self, instruction):
        super().initialize(instruction)
        self.screenshot()
        super().run(instruction)
        self.screenshot()
