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
Follow the request below. Every time you want to take an action, make a system call to the appropriate function.
Before using the click tool, always use locate_coordinates to decide where you should click.
You can start GUI applications, but you need to use run_background_command instead of run_command.
GUI apps run this way may take some time to appear. Take a screenshot to confirm it did.
The command to open Firefox GUI is firefox-esr (use a background command).
When there is a next step, always procede to the next step without being asked.
"""


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

    def screenshot(self):
        file = self.sandbox.take_screenshot()
        filename = self.save_image(file, "screenshot")
        print(f"Image: {filename}")
        self.latest_screenshot = filename
        return [
            ContentItem(image=filename),
        ]

    def run_command(self, command):
        result = self.sandbox.commands.run(command, timeout=5)
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
        self.messages.append({"role": "user", "content": self.screenshot()})

    def run(self, instruction):
        self.messages = self.messages or [
            {"role": "system", "content": [{"text": SYSTEM_PROMPT}]},
            {"role": "user", "content": [{"text": instruction}]},
        ]
        self.append_screenshot()
        super().run()
        self.append_screenshot()
