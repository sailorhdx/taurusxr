#!/usr/bin/env python
# coding=utf-8
import os
import cmd
import subprocess
import sys
from toughradius.shell import shell_tag
from toughradius.shell import BaiscCli

class SysCli(cmd.Cmd, BaiscCli):
    """ main cmd view
    """

    def __init__(self, config):
        cmd.Cmd.__init__(self)
        self.config = config
        self.prompt = shell_tag(u'/toughshell/sys ~ ')

    def emptyline(self):
        print ''