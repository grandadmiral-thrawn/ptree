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
    """ This class connects to the YAML files containing the configuration to run the ptree program, including the database connection in the Config File and the Queries in the Query File.

    :Example:
    >>> import sys
    >>> import os
    >>> import yaml
    >>> import pymssql
    >>> import sqlite3
    >>> A = YamlConn()
    >>> A.configfilename = "config_2.yaml"
    >>> A.config = <class 'dict'>
    >>> A.queries= <class 'dict'>
    >>> <pymssql.connection, pymssql.cursor> = A.sql_connect()

    .. warning:: pymssql dependency.

    METHODS

    """
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

    def lite3_connect(self):
        lite3conn = None

        lite3db = self.config['litedb']
        try:
            lite3conn = sqlite3.connect(lite3db)
            lite3cur = lite3conn.cursor()

        except sqlite3.Error as e:
            if lite3conn:
                lite3con.rollback()

            print("Error : ",e.args[0])
            sys.exit(1)
        return lite3conn, lite3cur

class BasicQC(object):
    """ This class provides basic functions for computing plot/stand scale metrics.

    The methods provided here do ...

    """
    def __init__(self):
        self.pconn, self.pcur = YamlConn().lite3_connect()
        self.queries = YamlConn().queries

    def get_interval(self, list_live_years, dead_year):
        """ Returns [prior_year, subsequent year]

        The bisect right function determines the windowing years from a given list around a given input year. For mortality plots, this tells us from which year to which year we need to aggregate.

        :list_of_live_years: a list of years when checks were performed that were not mortality only
        :dead_year: the year of the mortality check to be aggregated to a selection from list_of_live_years
        """
        list_live_years = []
        i = bisect.bisect_right(list_live_years,dead_year)
        return list_live_years[i-1:i+1]
