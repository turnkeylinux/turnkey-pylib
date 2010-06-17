# Copyright (c) 2008 Liraz Siri <liraz@turnkeylinux.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of 
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""This module contains high-level convenience functions for safe
command execution that properly escape arguments and raise an
ExecError exception on error"""
import os
import sys
import commands

mkarg = commands.mkarg

class ExecError(Exception):
    """Accessible attributes:
    command	executed command
    exitcode	non-zero exitcode returned by command
    output	error output returned by command
    """
    def __init__(self, command, exitcode, output=None):
        Exception.__init__(self, command, exitcode, output)

        self.command = command
        self.exitcode = exitcode
        self.output = output

    def __str__(self):
        str = "non-zero exitcode (%d) for command: %s" % (self.exitcode,
                                                          self.command)
        if self.output:
            str += "\n" + self.output
        return str

def fmt_command(command, *args):
    return command + " ".join([mkarg(arg) for arg in args])

def system(command, *args):
    """Executes <command> with <*args> -> None
    If command returns non-zero exitcode raises ExecError"""

    sys.stdout.flush()
    sys.stderr.flush()

    command = fmt_command(command, *args)
    error = os.system(command)
    if error:
        exitcode = os.WEXITSTATUS(error)
        raise ExecError(command, exitcode)

def getoutput(command, *args):
    """Executes <command> with <*args> -> output
    If command returns non-zero exitcode raises ExecError"""
    
    command = fmt_command(command, *args)
    error, output = commands.getstatusoutput(command)
    if error:
        exitcode = os.WEXITSTATUS(error)
        raise ExecError(command, exitcode, output)

    return output
