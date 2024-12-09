from os_computer_use.utils import (
    send_bbox_request,
    draw_big_dot,
)
from os_computer_use.agent import QwenAgent, format_message

from qwen_agent.llm.schema import ContentItem
from gradio_client import handle_file

import shlex
import os
import tempfile
from PIL import Image

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50


class SandboxAgent(QwenAgent):
    functions = [
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
            "name": "click",
            "description": "",
            "parameters": [
                {
                    "name": "query",
                    "type": "string",
                    "description": "Item or UI element on the screen to click",
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
            "send_key": self.send_key,
            "type_text": self.type_text,
            "run_command": self.run_command,
            "run_background_command": self.run_background_command,
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

    def click(self, query):
        self.take_screenshot()
        original_image = Image.open(self.latest_screenshot)
        image_data = handle_file(self.latest_screenshot)
        x, y = send_bbox_request(image_data, query)

        # Save the image with dot instead of displaying
        dot_image = draw_big_dot(original_image, (x, y))
        filepath = self.save_image(dot_image, "location")
        print(f"Image: {filepath}")

        self.sandbox.commands.run(f"xdotool mousemove --sync {x} {y}")
        self.sandbox.commands.run("xdotool click 1")
        return [{"text": "Done."}]

    def append_screenshot(self):
        # self.messages.append({"role": "user", "content": self.take_screenshot()})
        messages = [
            *self.messages,
            {"role": "user", "content": self.take_screenshot()},
            {
                "role": "user",
                "content": [
                    {
                        "text": "Describe anything you see that might be useful."  # and recommend an action to take (using the keyboard, mouse, or shell commands). Alternatively, you can wait for a couple of seconds."
                    }
                ],
            },
        ]
        # print(messages)
        response_stream = self.qwen.chat(messages=messages)
        new_messages = list(response_stream)[-1]
        # print(new_messages)
        for response in new_messages:
            print(format_message(response))
        return new_messages
        # self.messages.extend(new_messages)

    def run(self, instruction):

        self.messages.extend(
            [
                {"role": "user", "content": [{"text": instruction}]},
            ]
        )

        responses = []
        should_continue = True
        n = 1

        while should_continue:
            screen_contents = self.append_screenshot()
            response_stream = self.qwen.chat(
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "text": "You are an AI assistant with the ability to click, type and run commands on a computer."
                            }
                        ],
                    },
                    *self.messages,
                    *screen_contents,
                    {
                        "role": "assistant",
                        "content": [{"text": "Let's think step by step."}],
                    },
                ],
                functions=self.functions,
            )
            responses = list(response_stream)[-1]
            for response in responses:
                print(format_message(response))
            self.messages.extend(responses)
            should_continue = self.execute_function_calls(responses)
            n = n + 1
