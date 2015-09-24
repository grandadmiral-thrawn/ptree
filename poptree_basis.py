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
        """ Connects to the MS SQL server database

        Configuration parameters are in config_2.yaml file. 
        """
        sql_server = self.config['server']
        sql_user = self.config['user']
        sql_pw = self.config['password']
        sql_db = self.config['database']
        conn = pymssql.connect(server = sql_server, user=sql_user, password=sql_pw, database = sql_db)
        cur = conn.cursor()
        return conn, cur

    def lite3_connect(self):
        """ Connects to the SQLite3 database

        Configuration parameters are in config_2.yaml file. 
        """
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
    """ This class creates a dictionary for stands and plots to reference if a plot is a detail plot, when it is a detail plot, which stand it is in, and the minimum dbh from that plot, which is the threshold for it being included in the main inventory or not. 

    The detail_reference dictionary is extended, which the expansion dictionary is condensed. This is mostly beacuse I''m not sure which will be the most useful yet. Call this dictionary ahead of calling anything from plots, trees, or stands to save big time. Otherwise there are so many queries

    :Example:
    >>> import poptree_basis
    >>> A.detail_reference.keys()
    >>> dict_keys(['AB08', 'AV14', 'AR07', 'RS01', 'TO11', 'AM16', 'AX15', 'RS29', 'RS02', 'RS30', 'RS28', 'TB13', 'RS32', 'AG05', 'TO04', 'AE10', 'RS31', 'PP17', 'AV06'])
    >>> A.detail_reference['AV14'].keys()
    >>> dict_keys([1984, 2000, 1990, 2008, 1978, 1995])
    >>> A.detail_reference['AV14'][1984].keys()
    >>> dict_keys([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    >>> A.detail_reference['AV14'][1984][1]
    >>> {'detail': False, 'area': 625, 'min': 5.0}

    >>> A.umins_reference['HR02'][1984][1]
    >>> 5.0

    >>> A.uplot_areas['MH03'].keys()
    >>> dict_keys([1952, 1989, 1994, 1965, 1934, 1999, 1971, 2005, 1945, 1939, 1930, 1983])
    >>> A.uplot_areas['MH03'][1952].keys()
    >>> dict_keys([1])
    >>> A.uplot_areas['MH03'][1952][1]
    >>> 4047.0


    :A: is an instance of the detail_reference object, used for reference here.
    :A.detail_reference.[standid]: the stand, containing the years that stand 
    :A.detail_reference.[standid][year]: the plots on that stand and year when at least 1 plot is detail
    :A.detail_reference.[standid][year][plotno]['detail']: Boolean True or False if a detail plot on that stand and plot and year
    :A.detail_reference.[standid][year][plotno]['area']: the area of that plot
    :A.detail_reference.[standid][year][plotno]['min']: the minimum dbh on that detail plot

    :A.umins_reference.[standid]: stands whose minimum dbhs in at least 1 year are not 15.
    :A.umins_reference.[standid][year]: the plots on that stand and year when at least 1 plot has a minimum dbh that is not 15
    :A.umins_reference[standid][year][plotno]: the minimum dbh for that stand, plot, and year, which is not 15.0

    :A.expansion[standid][year][plotid]: the expansion factor for the stand, year, and plot which will not be 1.0

    :A.uplots_areas[standid]: stands whose areas in at least 1 year are not 625 m2
    :A.uplots_areas[standid][year]: the plots on that stand and year when at least 1 plot has an area not 625 m2
    :A.uplots_areas[standid][year][plotno]: the area for the stand, year, and plot that is not 625

    """
    def __init__(self):
        self.pconn, self.pcur = YamlConn().lite3_connect()
        self.detail_reference = {}
        self.expansion = {}
        self.uplot_areas = {}
        self.umins_reference = {}

        self.create_detail_reference()
        self.condense_detail_reference()
        self.contains_unusual_plots()
        self.create_unusual_mins_reference()

    def create_detail_reference(self):
        """ This function creates a lookup for detail plots that any tree or stand can use

        .. Example : 
        >>> H = DetailCapture.detail_reference.keys()

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
                    self.detail_reference[each_stand][year]={plotno:{'area': area, 'detail': True, 'min': mindbh}}
                elif year in self.detail_reference[each_stand] and detail == 'T':
                    self.detail_reference[each_stand][year][plotno] = {'area': area, 'detail': True, 'min': mindbh}
                elif year not in self.detail_reference[each_stand] and detail != 'T':
                    self.detail_reference[each_stand][year]={plotno:{'area':area, 'detail': False, 'min': mindbh}}
                elif year in self.detail_reference[each_stand] and detail !='T':
                    self.detail_reference[each_stand][year][plotno] = {'area':area, 'detail':False, 'min':mindbh}

                else:
                    pass

    def create_unusual_mins_reference(self):
        """ This function creates a lookup for plots that do not have minimums of 15, but are not detail plots.

        Queries the plot table for plots where detailPlot is not true and minimum DBH is not 15. 
        :umins_reference: a lookup by stand, year, and plot for the minimum dbh of plots whose minimum dbh is not 15 and are not detail plots
        """
        
        sql = YamlConn().queries['stand']['query_unusual_plot_minimums']
        self.pcur.execute(sql)
        
        for row in self.pcur:

            try:
                mindbh = round(float(row[3]),3)
            except Exception:
                mindbh = 5.0

            try:
            
                if str(row[0]) not in self.umins_reference:
                    self.umins_reference[str(row[0])] = {int(row[2]) :{int(row[1]): mindbh}}

                elif str(row[0]) in self.umins_reference:
                    if int(row[2]) not in self.umins_reference[str(row[0])]:
                        self.umins_reference[str(row[0])][int(row[2])] = {int(row[1]) :mindbh}

                    elif int(row[2]) in self.umins_reference[str(row[0])]:
                        if int(row[1]) not in self.umins_reference[str(row[0])][int(row[2])]:
                            self.umins_reference[str(row[0])][int(row[2])][int(row[1])] = mindbh
                        else:
                            print("some error has occurred in finding unusual minimums on not-detail plots")
            except Exception as e17:
                pass

    def condense_detail_reference(self):
        """ Condenses the detail reference into a readable dictionary of expansion factors by plot


        Use the attribute of expansion to quickly look up the expansion factor, given a stand, year, and plot
        .. math :  given tree attribute * (area of all plots / area of all detail plots) = scaled tree attribute

        .. math : 10 Mg Biomass in small trees on detail plots * (10000 m2 all plots / 2000 m2 detail plots) = 50 Mg Biomass on detail plots

        """
        
        for each_stand in self.detail_reference.keys():
            for each_year in self.detail_reference[each_stand].keys():
                
                try:
                    total_area = sum([self.detail_reference[each_stand][each_year][x]['area'] for x in self.detail_reference[each_stand][each_year].keys()])
                except Exception as e3:
                    total_area = sum([self.detail_reference[each_stand][each_year][x]['area'] for x in self.detail_reference[each_stand][each_year].keys() if x != None])

            
                try:
                    detail_area = sum([self.detail_reference[each_stand][each_year][x]['area'] for x in self.detail_reference[each_stand][each_year].keys() if self.detail_reference[each_stand][each_year][x]['detail'] is not False])
                except Exception as e3:
                    detail_area = sum([self.detail_reference[each_stand][each_year][x]['area'] for x in self.detail_reference[each_stand][each_year].keys() if self.detail_reference[each_stand][each_year][x]['detail'] is not False and self.detail_reference[each_stand][each_year][x]['detail'] != None])

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

    def contains_unusual_plots(self):
        """ A lookup table for stands, plots, and years which have areas other than 625 m

        The query from 'query_unusual_plot' finds standid, plot, year, and area of all plots whose areas are not 625 m, in that order, and creates a nested look up to be passed to stand objects, so that only sql hits have to be performed when we can't assume 625.
        """

        sql = YamlConn().queries['stand']['query_unusual_plot']
        self.pcur.execute(sql)
        
        for row in self.pcur:
            try: 
                area = round(float(row[3]),2)
            except Exception as e8:
                area = None

            try:
                plot = int(row[2])
            except Exception:
                plot = None

            try:
                if str(row[0]) not in self.uplot_areas:
                    self.uplot_areas[str(row[0])]={plot:{int(row[1]): area}}
                elif str(row[0]) in self.uplot_areas:
                    if plot not in self.uplot_areas[str(row[0])]:
                        self.uplot_areas[str(row[0])][plot] = {int(row[1]): area}
                    elif plot in self.uplot_areas[str(row[0])]: 
                        self.uplot_areas[str(row[0])][plot].update({int(row[1]): area})
            except Exception as e9:
                pass