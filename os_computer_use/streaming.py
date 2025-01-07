from e2b_desktop import Sandbox as SandboxBase
import asyncio
import os
import signal


class Sandbox(SandboxBase):

    def start_stream(self):
        command = "ffmpeg -f x11grab -s 1024x768 -framerate 30 -i :99 -vcodec libx264 -preset ultrafast -tune zerolatency -f mpegts -listen 1 http://localhost:8080"
        process = self.commands.run(
            command,
            background=True,
        )
        self.process = process
        return f"https://{self.get_host(8080)}"

    def kill(self):
        if hasattr(self, "process"):
            self.process.kill()
        super().kill()


class DisplayClient:
    def __init__(self, output_dir="."):
        self.process = None
        self.output_stream = f"{output_dir}/output.ts"
        self.output_file = f"{output_dir}/output.mp4"

    async def start_display_client(self, stream_url):
        self.process = await asyncio.create_subprocess_shell(
            f"ffmpeg -reconnect 1 -i {stream_url} -c:v libx264 -preset fast -crf 23 "
            f"-c:a aac -b:a 128k -f mpegts -loglevel quiet - | tee {self.output_stream} | "
            f"ffplay -autoexit -i -loglevel quiet -",
            preexec_fn=os.setsid,
            stdin=asyncio.subprocess.DEVNULL,
        )

    async def stop_display_client(self):
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            await self.process.wait()

    async def save_stream(self):
        process = await asyncio.create_subprocess_shell(
            f"ffmpeg -i {self.output_stream} -c:v copy -c:a copy -loglevel quiet {self.output_file}"
        )
        await process.wait()

        if process.returncode == 0:
            print(f"Stream saved successfully as {self.output_file}.")
        else:
            print(f"Failed to save the stream as {self.output_file}.")
