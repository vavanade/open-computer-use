from e2b import Sandbox as SandboxBase
from typing import Callable, Optional
import uuid


class Sandbox(SandboxBase):
    default_template = "desktop"

    def screenshot(
        self,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
    ):
        """
        Take a screenshot and save it to the given name.
        :param name: The name of the screenshot file to save locally.
        """
        screenshot_path = f"/home/user/screenshot-{uuid.uuid4()}.png"

        self.commands.run(
            f"scrot --pointer {screenshot_path}",
            on_stderr=on_stderr,
            on_stdout=on_stdout,
            cwd="/home/user",
        )

        return self.files.read(screenshot_path, format="bytes")
