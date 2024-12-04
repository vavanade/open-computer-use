from os_computer_use.utils import (
    send_bbox_request,
    draw_big_dot,
)
from os_computer_use.agent import QwenAgent

from qwen_agent.llm.schema import ContentItem
from gradio_client import handle_file

import shlex
import os
import tempfile
from PIL import Image

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

SYSTEM_PROMPT = """
Rules:
- Before starting a task, make a plan based on what you see.
- Before using the click tool, always use locate_coordinates to decide where to click.
- After opening an application, use `sleep 2` to wait for it to load.
- After finished a step, always go on to the next step until are are finished.
"""


class SandboxAgent(QwenAgent):
    functions = [
        {
            "name": "take_screenshot",
            "description": "",
            "parameters": {},
        },
        {
            "name": "send_key",
            "description": "",
            "parameters": {
                "name": "name",
                "type": "string",
                "description": "Key or combination (e.g. 'Return',  'Ctl-C')",
                "required": True,
            },
        },
        {
            "name": "type_text",
            "description": "",
            "parameters": {
                "name": "text",
                "type": "string",
                "description": "Text to type",
                "required": True,
            },
        },
        {
            "name": "run_command",
            "description": "",
            "parameters": {
                "name": "command",
                "type": "string",
                "description": "Shell command",
                "required": True,
            },
        },
        {
            "name": "run_background_command",
            "description": "",
            "parameters": {
                "name": "command",
                "type": "string",
                "description": "Shell command to run without waiting",
                "required": True,
            },
        },
        {
            "name": "locate_coordinates",
            "description": "",
            "parameters": {
                "name": "query",
                "type": "string",
                "description": "Action or UI element on the screen to return coordinates for",
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
                    "description": "Coordinate in pixels",
                    "required": True,
                },
                {
                    "name": "y",
                    "type": "number",
                    "description": "Coordinate in pixels",
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
            "take_screenshot": self.take_screenshot,
            "send_key": self.send_key,
            "type_text": self.type_text,
            "run_command": self.run_command,
            "run_background_command": self.run_background_command,
            "locate_coordinates": self.locate_coordinates,
            "click": self.click,
        }
        # Create temporary directory
        self.tmp_dir = tempfile.mkdtemp()
        self.image_counter = 0

    def save_image(self, image, prefix="image"):
        """Save image to temporary directory with incrementing counter."""
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
        print(f"Image: {filename}")
        self.latest_screenshot = filename
        return [ContentItem(image=filename)]

    def run_command(self, command):
        result = self.sandbox.commands.run(command, timeoutMs=5000)
        stdout, stderr = result.stdout, result.stderr
        if stdout and stderr:
            return [{"text": stdout + "\n" + stderr}]
        elif stdout or stderr:
            return [{"text": stdout + stderr}]
        else:
            return [{"text": "Done."}]

    def run_background_command(self, command):
        self.sandbox.commands.run(command, background=True)
        return [{"text": "Done."}]

    def send_key(self, name):
        self.sandbox.commands.run(f"xdotool key -- {name}")
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
        self.take_screenshot()
        original_image = Image.open(self.latest_screenshot)
        image_data = handle_file(self.latest_screenshot)
        x, y = send_bbox_request(image_data, query)

        # Save the image with dot instead of displaying
        dot_image = draw_big_dot(original_image, (x, y))
        filepath = self.save_image(dot_image, "location")
        print(f"Image: {filepath}")

        return f"({x},{y})"

    def click(self, x, y):
        self.sandbox.commands.run(f"xdotool mousemove --sync {x} {y}")
        self.sandbox.commands.run("xdotool click 1")
        return [{"text": "Done."}]

    def append_screenshot(self):
        self.messages.append({"role": "user", "content": self.take_screenshot()})

    def run(self, instruction):
        self.messages = self.messages or [
            {"role": "system", "content": [{"text": SYSTEM_PROMPT}]},
            {"role": "user", "content": [{"text": instruction}]},
        ]
        self.append_screenshot()
        super().run()
        self.append_screenshot()
