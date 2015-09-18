#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import yaml
import pymssql
import sqlite3

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(HERE))

"""
poptree_basis.py contains the classes for connecting to the databases and reference files
"""

class YamlConn(object):
    """ connects to the yaml configuration file, config_2.yaml """
    def __init__(self):
        self.configfilename = os.path.join(HERE, "config_2.yaml")
        self.config = yaml.load(open(self.configfilename,'rb'))
        self.queries = yaml.load(open(os.path.join(HERE, self.config['query_file']), 'rb'))
        

    def sql_connect(self):
        """ connects to the sql server database"""
        sql_server = self.config['server']
        sql_user = self.config['user']
        sql_pw = self.config['password']
        sql_db = self.config['database']
        conn = pymssql.connect(server = sql_server, user=sql_user, password=sql_pw, database = sql_db)
        cur = conn.cursor()
        return conn, cur

    def lite3_connect(self, database):
        self.lite3conn = None

        lite3db = self.config['litedb']
        try:
            self.lite3conn = sqlite3.connect(lite3db)
            self.lite3cur = self.lite3conn.cursor()
        
        except sqlite3.Error as e:
            if self.lite3conn:
                self.lite3con.rollback()

            print("Error : ",e.args[0])
            sys.exit(1)
        return self.lite3conn, self.lite3cur
