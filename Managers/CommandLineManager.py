from subprocess import run
from time import time

from .console import console


SEPARATOR = ' '+'='*10+' '


class CommandLineManager():
    def runCommand(self, command, input=None, capture_output=False, text=False, cwd=None, name=None, titleJustify="center", ruleAndResult=True):
        commandName = ""
        for c in command:
                commandName += c + " "
             
        if not ruleAndResult:
            pass
        elif name != None:
            console.print("\n")
            console.rule(name, align=titleJustify)
            console.print("\n")
        else:
            console.print("\n")
            console.rule("Running: "+commandName)
            console.print("\n")
        
        start_time = time()
        res = run(command, input=input, capture_output=capture_output, text=text, cwd=cwd)

        if not ruleAndResult:
            pass
        elif res.returncode != 0:
            console.print(f"\n:warning:  Command ({commandName}) presented an [red]error[/] [Status code: {res.returncode}]\n\n")
        else:
            console.print(f"\n:thumbs_up:  Command ({commandName}) was completed in [bold]{(time()-start_time):.3f}[/] seconds\n\n")           
        return res


    def consolePrint(self, string):
        console.print(string)


    def consoleRule(self, string):
        console.rule(string)

