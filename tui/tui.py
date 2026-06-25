import asyncio
import subprocess
import sys

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

    def __init__(self, config, run, cwd, setup) -> None:
        self.setup = setup

        self.config = config
        self.runCmd = run
        self.cwd = cwd
        self.f = open("tui/logs.txt", "w")

        self.arguments = sys.argv
        if "--tui" in self.arguments: self.arguments.remove("--tui")
        # removes tags from arguments (are added later)
        if "--ansible_tags" in self.arguments: 
            for i in range(len(self.arguments)):
                if self.arguments[i] == "--ansible_tags":
                    self.arguments = self.arguments[:i]
                    break
        if "-test" in self.arguments: self.arguments.remove("-test")

        # extracts components to be logged during testing from run file
        for i in range(len(self.runCmd)):
            if isinstance(self.runCmd[i], dict) and "logs" in self.runCmd[i].keys():
                self.logs = self.runCmd[i]["logs"]
                self.numLogs = len(self.logs)

                if self.numLogs == 0:
                    raise Exception("When in TUI mode, run file most contain at least one component to be logged.")

        super().__init__()


    def on_unmount(self) -> None:
        self.f.close()

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


    def  on_setup_complete(self, message: SetupComplete) -> None:
        self.f.write("Handler entered \n")
        self.callTest()

        for i in range(self.numLogs):
            self.stream_logs(self.logs[i]["where"], self.logs[i]["func"], f"log{i+1}")
    

    @work(thread=True)
    def callTest(self):
        command = ["python3"]
        
        command.extend(self.arguments)
        command.append("-test")
        self.stream_command_output(command, "mainOutput")


    @work(thread=True)
    def stream_logs(self, where, function, id):
        SCRIPT=f"sudo journalctl -fu open5gs-{function}d --no-pager"
        self.f.write(str(self.config[where].keys()) + "\n")
        HOST=self.config[where]["public_ip"]
        USER="root" if self.config["location"] == "cloud" else "vagrant"

        command = ["ssh", f"{USER}@{HOST}", f"{SCRIPT}"]
        self.stream_command_output(command, id)


    @work(thread=True)
    def stream_provider_ansible(self):
        command = ["python3"]

        tags = ""
        if len(self.config["ansible_tags"]) != 0:
            for tag in self.config['ansible_tags'][0].split():
                if "testing_stage" in tag: continue
                tags = tag + " "

        command.extend(self.arguments)
        if len(tags) != 0: command.extend(["--ansible_tags", tags])
        self.f.write("First config" + str(self.config) + "\n")
        if "testing_stage" not in self.config["ansible_tags"] and not self.config["test"]:
            self.stream_command_output(command, "mainOutput")
        
        self.f.write("Posting SetupComplete \n")
        
        # updates config with IPs or ports
        self.setup.strategy.readIPs()
        self.config = self.setup.config
        self.f.write("Updated config" + str(self.config) + "\n")
        self.call_from_thread(
            self.post_message,
            SetupComplete()
        )


    def stream_command_output(self, command, id) -> None:
        self.f.write("Command being executed " + str(command) + "\n")
        log_widget = self.query_one(f"#{id}", RichLog)
        log_widget.clear()
        log_widget.write(f"[bold yellow]Starting command...[/]\n {command}")

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
    app = TSim(config, run, cwd, setup)
    app.run()