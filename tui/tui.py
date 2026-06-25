import asyncio
import subprocess

from sys import argv

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, RichLog, Static
from textual.containers import VerticalScroll, Vertical
from textual.message import Message
from textual import work


class Main_Output(RichLog):

    def __init__(self) -> None:
        super().__init__(
            id="mainOutput",
            highlight=True,
            markup=True,
            wrap=True,
        )

    def ansible(self) -> None:
        self.post_message(self.Command("ansible"))

    def readyForOutput(self) -> None:
        self.post_message(self.Command("test"))


class SetupComplete(Message):
    pass


class TSim(App):
    TITLE = "TSim TUI"
    CSS_PATH = "tui.tcss"

    def __init__(self, config, run, cwd):
        self.config = config
        self.run = run
        self.cwd = cwd

        for i in range(len(run)):
            if isinstance(run[i], dict) and "logs" in run[i].keys():
                self.logs = run[i]["logs"]
                self.numLogs = len(self.logs)

                if self.numLogs == 0:
                    raise Exception("When in TUI mode, run file most contain at least one component to be logged.")

        super().__init__()


    def  on_setup_complete(self, message: SetupComplete) -> None:
        print("Handler entered")
        self.callTest()

        for i in range(self.numLogs):
            self.stream_logs(self.logs[i]["where"], self.logs[i]["func"], f"log{i+1}")

        
    def on_mount(self) -> None:
        self.stream_provider_ansible()
        
        for i in range(self.numLogs):
            childLog = self.query_one(f"#log{i+1}")
            childLog.styles.height = f"{100/self.numLogs}%"
    
    
    def compose(self) -> ComposeResult: 
        yield Main_Output()

        with Vertical(classes="right-column"):
            yield Header(id="header")

            with VerticalScroll(id="right-pane"):
                for i in range(self.numLogs):
                    yield RichLog(
                        id=f"log{i+1}",
                        highlight=True,
                        markup=True,
                        wrap=True,  
                        classes="child-log" 
                    )
    

    @work(thread=True)
    def callTest(self):
        command = ["python3"]
        argv.remove("--tui")
        argv.remove("ansible_tags")

        command.extend(argv)
        command.append("-test")
        self.stream_command_output(["python3", "/home/agustin/5G_Setup/main.py", "-c", "/home/agustin/config/config.yaml", "-r", "/home/agustin/config/run.yaml", "-test"], "mainOutput")


    @work(thread=True)
    def stream_logs(self, where, function, id):
        SCRIPT=f"sudo journalctl -fu open5gs-{function}d --no-pager"
        HOST=self.config[where]["public_ip"]
        USER="root" if self.config["location"] == "cloud" else "vagrant"

        command = ["ssh", f"{USER}@{where}", f"{SCRIPT}"]
        self.stream_command_output(command, id)


    @work(thread=True)
    def stream_provider_ansible(self):
        command = ["python3"]
        argv.remove("--tui")

        # removes ansible tags that will be added later
        for i in range(len(argv)):
            if argv[i] == "ansible_tags":
                argv = argv[:i]

        command.extend(argv)
        command.extend(["--ansible_tags", "install_stage config_stage services_stage"])
        if "testing_stage" not in self.config["ansible_tags"].split(" ") or "test" not in self.config.keys():
            self.stream_command_output(command, "mainOutput")
        
        print("Posting SetupComplete")
        self.call_from_thread(
            self.post_message,
            SetupComplete()
        )


    def stream_command_output(self, command, id) -> None:
        print("Command being executed " + str(command))
        log_widget = self.query_one(f"#{id}", RichLog)
        log_widget.clear()
        log_widget.write(str(argv))
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
    app = TSim({"config": False})
    app.run()