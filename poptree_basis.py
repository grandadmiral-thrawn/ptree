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

class DetailCapture(object):
    """ This class encapsulates a dictionary for if a plot is a detail plot, when, which stand it is in, and the minimum dbh from that plot. 

    The detail_reference dictionary is extended, which the expansion dictionary is condensed. This is mostly beacuse I''m not sure which will be the most useful yet. Call this dictionary ahead of calling anything from plots, trees, or stands to save big time. Otherwise there are so many queries

    :Example:
    >>> import sys
    >>> import os
    >>> import yaml
    >>> import pymssql
    >>> import poptree_basis
    >>> H = A.detail_reference
    >>> H.keys()
    >>> dict_keys(['AB08', 'AE10', 'RS01', 'PP17', 'RS02', 'AV06', 'AR07', 'TO04', 'RS28', 'TB13', 'AM16', 'AG05', 'RS31', 'RS29', 'AX15', 'AV14', 'RS30', 'RS32', 'TO11'])
    >>> H['RS02'].keys()
    >>> dict_keys([1971, 1988, 2005, 2009, 1976, 1993, 1978, 1983, 1999])
    >>> H['RS02'][1993]
    >>> {'all_areas': [625, 625, 625, 625, 625, 625, 625, 625, 625, 625, 625, 625, 625, 625, 625, 625], 'all_mins': [15.0, 15.0, 5.0, 15.0, 15.0, 5.0, 15.0, 15.0, 15.0, 15.0, 5.0, 15.0, 5.0, 5.0, 5.0, 5.0], 'all_plots': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], 'T_areas': [625, 625, 625, 625, 625, 625, 625], 'T_plots': [3, 6, 11, 13, 14, 15, 16]}

    """
    def __init__(self):
        self.pconn, self.pcur = YamlConn().lite3_connect()
        self.detail_reference = {}
        self.expansion = {}

        self.create_detail_reference()
        self.condense_detail_reference()

    def create_detail_reference(self):
        """ This function creates a lookup for detail plots that any tree or stand can use
        """
        stands_with_details = []
        sql = YamlConn().queries['stand']['lite_context_dtl']
        self.pcur.execute(sql)
        
        for row in self.pcur:
            stands_with_details.append(str(row[0]))


        for each_stand in stands_with_details:

            if each_stand not in self.detail_reference:
                self.detail_reference[each_stand] = {}
            elif each_stand in self.detail_reference:
                pass

            sql = YamlConn().queries['stand']['lite_context_dtl_2'].format(standid=each_stand)
            self.pcur.execute(sql)
            
            for row in self.pcur:
                plotno = int(row[0])
                year = int(row[1])
                detail = str(row[2])
                
                # default area is 625
                try:
                    area = int(row[3])
                except Exception:
                    area = 625

                # default min dbh is 5
                try:
                    mindbh = round(float(row[4]),1)
                except Exception:
                    mindbh = 5.0

                if year not in self.detail_reference[each_stand] and detail == 'T':
                    self.detail_reference[each_stand][year]={'T_plots':[plotno], 'T_areas':[area],'all_plots':[plotno], 'all_areas':[area], 'all_mins': [mindbh]}
                elif year in self.detail_reference[each_stand] and detail == 'T':
                    self.detail_reference[each_stand][year]['T_plots'].append(plotno)
                    self.detail_reference[each_stand][year]['T_areas'].append(area)
                    self.detail_reference[each_stand][year]['all_plots'].append(plotno)
                    self.detail_reference[each_stand][year]['all_areas'].append(area)
                    self.detail_reference[each_stand][year]['all_mins'].append(mindbh)
                elif year not in self.detail_reference[each_stand] and detail != 'T':
                    self.detail_reference[each_stand][year]={'T_plots':[], 'T_areas':[], 'all_plots':[plotno], 'all_areas':[area], 'all_mins':[mindbh]}
                elif year in self.detail_reference[each_stand] and detail !='T':
                    self.detail_reference[each_stand][year]['all_plots'].append(plotno)
                    self.detail_reference[each_stand][year]['all_areas'].append(area)
                    self.detail_reference[each_stand][year]['all_mins'].append(mindbh)

                else:
                    pass
        
    def condense_detail_reference(self):
        """ Condenses the detail reference dictionary into a readable dictionary of expansion factors by plot

        .. math :  given tree attribute * (area of all plots / area of all detail plots) = scaled tree attribute

        .. math : 10 Mg Biomass in small trees on detail plots * (10000 m2 all plots / 2000 m2 detail plots) = 50 Mg Biomass on detail plots

        """
        self.expansion = {}
        for each_stand in self.detail_reference.keys():
            for each_year in self.detail_reference[each_stand].keys():
                
                try:
                    total_area = sum(self.detail_reference[each_stand][each_year]['all_areas'])
                except Exception as e3:
                    total_area = sum([x for x in self.detail_reference[each_stand][each_year]['all_areas'] if x != None])

                try:
                    detail_area = sum(self.detail_reference[each_stand][each_year]['T_areas'])
                except Exception as e3:
                    detail_area = sum([x for x in self.detail_reference[each_stand][each_year]['T_areas'] if x != None])

                try:
                    expansion_factor_to_stand = round(float(total_area/detail_area),2)
                except Exception as e4:
                    expansion_factor_to_stand = 1.

                if each_stand not in self.expansion:
                    self.expansion[each_stand] = {each_year:expansion_factor_to_stand}
                elif each_stand in self.expansion:
                    if each_year not in self.expansion[each_stand]:
                        self.expansion[each_stand][each_year] = expansion_factor_to_stand
                    else:
                        pass


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
