import asyncio
import subprocess

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, RichLog, Static
from textual.containers import VerticalScroll, Vertical
from textual import work


class CommandRunnerApp(App):
    TITLE = "TSim TUI"
    CSS_PATH = "tui.tcss"

    def on_mount(self) -> None:
        self.stream_command_output(["python3", "/home/agustin/5G_Setup/main.py", "-c", "/home/agustin/config/config.yaml", "-r", "/home/agustin/config/run.yaml", "-test"], "mainOutput")
        self.stream_logs("155.138.134.172", "amf", "log1")
        self.stream_logs("155.138.134.172", "ausf", "log3")
    
    
    def compose(self) -> ComposeResult:
        yield RichLog(
            id="mainOutput",
            highlight=True,
            markup=True,
            wrap=True,
        )

        with Vertical(classes="right-column"):
            yield Header(id="header")

            with VerticalScroll(id="right-pane"):
                for i in range(15):
                    yield RichLog(
                        id=f"log{i+1}",
                        highlight=True,
                        markup=True,
                        wrap=True,   
                    )
    
    def stream_logs(self, where, function, id):
        SCRIPT=f"sudo journalctl -fu open5gs-{function}d --no-pager"
        #HOST=self.config[where]["public_ip"]
        USER="root"

        command = ["ssh", f"{USER}@{where}", f"{SCRIPT}"]
        self.stream_command_output(command, id)


    @work(thread=True)
    def stream_command_output(self, command, id) -> None:
        log_widget = self.query_one(f"#{id}", RichLog)
        log_widget.clear()
        log_widget.write("[bold yellow]Starting command...[/]")

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            if process.stdout:
                for line in process.stdout:
                    log_widget.write(line.strip())

            process.wait()
            log_widget.write("[bold green]Finished successfully![/]")

        except Exception as e:
            log_widget.write(f"[bold red]Error running command: {e}[/]")


if __name__ == "__main__":
    app = CommandRunnerApp()
    app.run()