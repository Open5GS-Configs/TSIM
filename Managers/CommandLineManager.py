from subprocess import run


SEPARATOR = ' '+'='*10+' '


class CommandLineManager():

    def runCommand(self, command, input=None, noOutput=False, cwd=None):
        commandName = ""
        for c in command:
            commandName += c + " "
        
        print("\n"+SEPARATOR+f"Running: {commandName}"+SEPARATOR+"\n\n")
        res = run(command, input=input, capture_output=noOutput, text=noOutput, cwd=cwd)

        if(res.returncode != 0):
            print(f"Command ({commandName}) presented an error [Status code: {res.returncode}]")
            return res 
        else:
            print(f"Command ({commandName}) was succesful")
            return res

