"""This module contains high-level convenience functions for safe
command execution that properly escape arguments and raise an
exception on error"""
import os
import sys
import commands

class ExecError(Exception):
    pass

def _fmt_command(command, args):
    return command + " ".join([commands.mkarg(arg) for arg in args])

def system(command, *args):
    """Executes <command> with <*args> -> None
    If command returns non-zero exitcode raises ExecError"""

    sys.stdout.flush()
    sys.stderr.flush()

    command = _fmt_command(command, args)
    error = os.system(command)
    if error:
        exitcode = os.WEXITSTATUS(error)
        raise ExecError("system command returned non-zero exitcode", command, exitcode)

def getoutput(command, *args):
    """Executes <command> with <*args> -> output
    If command returns non-zero exitcode raises ExecError"""
    
    command = _fmt_command(command, args)
    error, output = commands.getstatusoutput(command)
    if error:
        exitcode = os.WEXITSTATUS(error)
        raise ExecError("getoutput command returned non-zero exitcode", command, exitcode, output)

    return output

