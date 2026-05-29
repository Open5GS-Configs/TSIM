from subprocess import run


SEPARATOR = ' '+'='*5+' '


class CommandLineManager():

    def runCommand(self, command, input=None):
        if len(command) > 2:
            commandName = f"{command[0]} {command[2]}"
        else:
            commandName = command[0]
        
        print("\n"+SEPARATOR+f"Running: {commandName}"+SEPARATOR+"\n\n")
        res = run(command, input=input)

        if(res.returncode != 0):
            print(f"Command ({commandName}) presented an error [Status code: {res.returncode}]")
            return res.returncode
        else:
            print(f"Command ({commandName}) was succesful")
            return 0