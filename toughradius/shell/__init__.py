#!/usr/bin/env python
# coding=utf-8
import os
import cmd
import subprocess
import sys
welcome_str = "\nHello, This is a toughradius cmd tools. \n\nType 'help' or '?' list available subcommands and some. \n\n"
shell_tag = lambda tag: u'\x1b[32m\x1b[1m{0}\x1b[0m'.format(tag).encode('utf-8')

def syscmd(args):
    subshell = subprocess.Popen(args, shell=True, stdin=None, stdout=None)
    subshell.communicate()
    subshell.terminate()
    return


class BaiscCli(object):

    def do_quit(self, args):
        """ quit current view
        """
        return True

    def do_exit(self, args):
        """ quit toughell cmd
        """
        sys.exit()

    def do_shell(self, args):
        """run a shell commad"""
        try:
            subshell = subprocess.Popen(args, shell=True, stdin=None, stdout=None)
            subshell.communicate()
            subshell.terminate()
        except:
            pass

        print ''
        return