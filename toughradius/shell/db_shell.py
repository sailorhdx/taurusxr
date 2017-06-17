#!/usr/bin/env python
# coding=utf-8
import os
import cmd
import subprocess
import sys
from toughradius.shell import BaiscCli
from toughradius.shell import shell_tag
from toughradius.toughlib import config as iconfig
from toughradius.toughlib import utils

class DbCli(cmd.Cmd, BaiscCli):
    """ main cmd view
    """

    def __init__(self, config):
        cmd.Cmd.__init__(self)
        self.config = config
        self.prompt = shell_tag(u'/toughshell/db ~ ')

    def emptyline(self):
        print ''

    def do_init(self, args):
        """ Initialize the database, 
        if the database already exists and has data, 
        will delete all tables, and re initialization
        """
        pstr = 'This operation will clear the database,\nand rebuild the database table, \nthe operation can not be revoked, \nto confirm the initial database\xef\xbc\x9fy/n'
        isy = raw_input(pstr)
        if isy == 'y':
            from toughradius.common import initdb as init_db
            init_db.update(self.config, force=True)
        else:
            print 'do nothing'

    def do_add_table(self, tablename):
        """ add table for models define name
        """
        from toughradius.common import initdb as init_db
        init_db.create_table(self.config, tablename)

    def do_tables(self, tablename):
        """ show tables
        """
        from toughradius.common import initdb as init_db
        init_db.show_tables(self.config)

    def do_add_column(self, args):
        """ add_column <table> <column> <type> <default>
        """
        try:
            from toughradius.common import initdb as init_db
            arrs = args.split()
            if len(arrs) != 4:
                print 'params error, must  add_column <table> <column> <type> <default>'
            table, column, ctype, defval = arrs
            defval = defval.replace('"', '')
            defval = defval.replace("'", '')
            defval = defval.replace('null', '')
            init_db.add_column(self.config, table, column, ctype, defval)
        except Exception as err:
            print err.message