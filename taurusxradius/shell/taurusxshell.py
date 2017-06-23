#!/usr/bin/env python
# coding=utf-8
import os
import cmd
import subprocess
import sys
from taurusxradius.shell import sys_shell
from taurusxradius.shell import db_shell
from taurusxradius.shell import shell_tag
from taurusxradius.shell import BaiscCli

class CLI(cmd.Cmd, BaiscCli):

    def __init__(self, config):
        cmd.Cmd.__init__(self)
        self.config = config
        self.prompt = shell_tag(u'/taurusxshell ~ ')
        self.sys_cli = sys_shell.SysCli(config)
        self.db_cli = db_shell.DbCli(config)

    def emptyline(self):
        print ''

    def do_sys(self, args):
        """ system view
        """
        self.sys_cli.cmdloop()

    def do_db(self, args):
        """ database view
        """
        self.db_cli.cmdloop()

    def do_quit(self, args):
        """ quit taurusxshell cmd
        """
        return True


welcome_str = "\nHello, This is a taurusxradius cmd tools. \n\nType 'help' or '?' list available subcommands and some. \n\n"

def main(config):
    cli = CLI(config)
    try:
        cli.cmdloop(welcome_str)
    except KeyboardInterrupt as e:
        pass

    print 'Bye!'