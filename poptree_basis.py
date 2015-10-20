#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import yaml
import pymssql
import sqlite3

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(HERE))

class YamlConn(object):
    """ This class connects to the YAML files containing the configuration to run the ptree program, including the database connection in the Config File and the Queries in the Query File.

    :Example:
    
    >>> A = YamlConn()
    >>> A.configfilename = "config_2.yaml"
    >>> A.config = <class 'dict'>
    >>> A.queries= <class 'dict'>
    >>> <pymssql.connection, pymssql.cursor> = A.sql_connect()

    .. warning:: pymssql dependency. pymssql is required to connect to FSDB.

    **METHODS**

    """
    def __init__( self ):
        self.configfilename = os.path.join( HERE, "config_2.yaml" )
        self.config = yaml.load( open( self.configfilename, 'rb' ))
        self.queries = yaml.load( open( os.path.join(HERE, self.config['query_file']), 'rb'))


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

class Capture(object):
    """ This class contains dictionaries to be used in Stand computations for indexing the unique cases of minimum dbh's, stand areas, and detail plot expansions. Stands use the parameters in Capture to do specific calculations when the default case of area 625 m\ :sup:`2`,  minimum dbh 15.0 cm, detailPlot is False does not apply.

    Here is a brief display of the common usage of Capture attributes within TPS.

    .. Example:

    >>> import poptree_basis
    >>> A = poptree_basis.Capture()

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

    >>> A.expansion['RS32'][2006]
    >>> 4.0

    **METHODS**

    :A: in this example, an instance of the Capture class.
    :A.detail_reference.keys(): the standids that contain detail plots for at least 1 plot in 1 remeasurement.
    :A.detail_reference.[standid]: the years that `standid` contains at least 1 detail plot
    :A.detail_reference.[standid][year]: the `plotnos` on that stand and year when at least 1 plot is a detail plot
    :A.detail_reference.[standid][year][plotno]['detail']: Boolean True or False if a detail plot on that stand and plot and year
    :A.detail_reference.[standid][year][plotno]['area']: the area m\ :sup:`2` of that plot
    :A.detail_reference.[standid][year][plotno]['min']: the minimum dbh on that detail plot

    :A.umins_reference.[standid]: stands whose minimum dbhs in at least 1 year are not 15.0 cm.
    :A.umins_reference.[standid][year]: the plots on that stand and year when at least 1 plot has a minimum dbh that is not 15.0 cm
    :A.umins_reference[standid][year][plotno]: the minimum dbh for that stand, plot, and year, which is not 15.0 cm.

    :A.uplots_areas[standid]: stands whose areas in at least 1 year are not 625 m\ :sup:`2`
    :A.uplots_areas[standid][year]: the plots on that stand and year when at least 1 plot has an area not 625 m\ :sup:`2`
    :A.uplots_areas[standid][year][plotno]: the area for the stand, year, and plot that is not 625 m\ :sup:`2`

    :A.expansion[standid][year][plotid]: the expansion factor for the stand, year, and plot which will not be 1.0

    """
    def __init__(self):
        self.pconn, self.pcur = YamlConn().lite3_connect()
        self.detail_reference = {}
        self.expansion = {}
        self.uplot_areas = {}
        self.umins_reference = {}
        self.total_areas = {}
        self.num_plots = {}
        self.additions = {
        'gmnf': 1996, 'hgbk': 1982, 'ncna': 1980, 'pila': 1983, 'rs01': 1978, 'rs02': 1978, 'rs03': 1977, 'rs13':[1981, 1982], 'sucr': 1983, 'tctr': 1997, 'ws02': 1982
        }
        self.replacements = {
        'gmnf': 1994, 'hgbk': 1988, 'ncna': 1984, 'pila': 1988, 'rs01': 1983, 'rs02': 1983, 'rs03': 1981, 'rs13':1986, 'sucr': 1988, 'tctr': 2001, 'ws02': 1988
        }

        self.create_detail_reference()
        self.condense_detail_reference()
        self.contains_unusual_plots()
        self.create_unusual_mins_reference()
        self.get_total_stand_area()
        self.create_num_plots()

    def create_detail_reference(self):
        """ Creates a reference for detail plots that any instance of Tree (called by tps_Tree) or Stand (calld by tps_Stand) can use.

        Here is a case where the stand, year, and plot in question is NOT a detail plot.

        .. Example: 

        >>> H = Capture.detail_reference.keys()
        >>> dict_keys(['AB08', 'AV14', 'AR07', 'RS01', 'TO11', 'AM16', 'AX15', 'RS29', 'RS02', 'RS30', 'RS28', 'TB13', 'RS32', 'AG05', 'TO04', 'AE10', 'RS31', 'PP17', 'AV06'])
        >>> H.detail_reference['RS01'].keys()
        >>> dict_keys([1976, 1971, 1988, 2009, 1992, 2004, 1978, 1998, 1983])
        >>> H.detail_reference['RS01'][2004][1]['area']
        >>> 625
        >>> H.detail_reference['RS01'][2004][1]['detail']
        >>> False
        >>> H.detail_reference['RS01'][2004][1]['min']
        >>> 15.0

        Here is a case where the stand, year, and plot in question is a detail plot.

        .. Example :
        
        >>> H.detail_reference['RS01'][2004][3]['area']
        >>> 625
        >>> H.detail_reference['RS01'][2004][3]['detail']
        >>> True
        >>> H.detail_reference['RS01'][2004][3]['min']
        >>> 5.0

        **RETURNS**

        :Capture.detail_reference: the name of the lookup table created, which can be referenced as an attribute of the Capture object.

        .. warning : Currently calls from the sqlite3 database for the references of stands, plots, and years. Will need to be updated to call to FSDB.
        """
        stands_with_details = []
        sql = YamlConn().queries['stand']['lite_context_dtl']
        self.pcur.execute(sql)
        
        for row in self.pcur:
            stands_with_details.append(str(row[0]))


        for each_stand in stands_with_details:

            if each_stand.rstrip().lower() not in self.detail_reference:
                self.detail_reference[each_stand.rstrip().lower()] = {}

            elif each_stand.rstrip().lower() in self.detail_reference:
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

                if year not in self.detail_reference[each_stand.rstrip().lower()] and detail == 'T':
                    self.detail_reference[each_stand.rstrip().lower()][year]={plotno:{'area': area, 'detail': True, 'min': mindbh}}
                elif year in self.detail_reference[each_stand.rstrip().lower()] and detail == 'T':
                    self.detail_reference[each_stand.rstrip().lower()][year][plotno] = {'area': area, 'detail': True, 'min': mindbh}
                elif year not in self.detail_reference[each_stand.rstrip().lower()] and detail != 'T':
                    self.detail_reference[each_stand.rstrip().lower()][year]={plotno:{'area':area, 'detail': False, 'min': mindbh}}
                elif year in self.detail_reference[each_stand.rstrip().lower()] and detail !='T':
                    self.detail_reference[each_stand.rstrip().lower()][year][plotno] = {'area':area, 'detail':False, 'min':mindbh}

                else:
                    pass

    def create_unusual_mins_reference(self):
        """ Creates a lookup for plots that do not have minimums of 15, but are not detail plots.

        `create_unusual_mins_reference` queries the database to create a reference for plots where detailPlot is not 'T' and minimum DBH is not 15.0 cm 

        .. Example:
        
        >>> H = poptree_basis.Capture()
        >>> H.umins_reference.keys()
        >>> dict_keys(['YBNF', 'SRNF', 'MRNA', 'CH10',...
        >>> H.umins_reference['PF28'][1959][3]
        >>> 10.0

        **RETURNS**

        :Capture.umins_reference: the name of the lookup table created, which can be referenced as an attribute of the Capture object.

        .. warning: Currently calls from the sqlite3 database for the references of stands, plots, and years. Will need to be updated to call to FSDB.

        """
        
        sql = YamlConn().queries['stand']['query_unusual_plot_minimums']
        self.pcur.execute(sql)
        
        for row in self.pcur:

            try:
                mindbh = round(float(row[3]),3)
            except Exception:
                mindbh = 5.0

            try:

                if str(row[0]).rstrip().lower() not in self.umins_reference:
                    self.umins_reference[str(row[0]).rstrip().lower()] = {int(row[2]): {int(row[1]): mindbh}}

                elif str(row[0]).rstrip().lower() in self.umins_reference:
                    if int(row[2]) not in self.umins_reference[str(row[0]).rstrip().lower()]:
                        self.umins_reference[str(row[0]).rstrip().lower()][int(row[2])] = {int(row[1]):mindbh}

                    elif int(row[2]) in self.umins_reference[str(row[0]).rstrip().lower()]:
                        if int(row[1]) not in self.umins_reference[str(row[0]).rstrip().lower()][int(row[2])]:
                            self.umins_reference[str(row[0]).rstrip().lower()][int(row[2])][int(row[1])] = mindbh
                        else:
                            print("some error has occurred in finding unusual minimums on not-detail plots")
            except Exception as e17:
                # any errors here can be passed, and the site will get the default values
                pass

    def condense_detail_reference(self):
        """ Condenses the detail reference into a readable dictionary of expansion factors by plot

        The expansion factor only applies to trees whose dbhs are greater than the minimum dbh (usually 5.0 cm) and less than the smallest dbh for the not-detail plots (usually 15.0 cm). The terms `large` and `small` are used casually throughout the program to refer to these size groups.
        
        .. Example:

        `Given stand attribute * (area of all plots / area of all detail plots) = Representative stand attribute`

        10 Mg Biomass in small trees on detail plots * (10000 (m\ :sup:`2`) all plots / 2000 (m\ :sup:`2`) detail plots) = 50 Mg Biomass on detail plots

        .. Example:

        >>> H = poptree_basis.Capture()
        >>> H.expansion.keys()
        >>> dict_keys(['RS32', 'AG05', 'RS02', 'RS01', 'TO04', 'AV14', 'AR07', 'TB13', 'AE10', 'TO11', 'PP17', 'AM16', 'RS31', 'RS28', 'AB08', 'AX15', 'RS29', 'AV06', 'RS30'])
        >>> H.expansion['RS32'][2006]
        >>> 4.0

        **RETURNS**

        :Capture.expansion: the name of the lookup table created, which can be referenced as an attribute of the Capture object.

        .. note: Unlike the other Capture methods, expansion does not require the "plot" attribute to be called.

        .. warning: Currently calls from the sqlite3 database for the references of stands, plots, and years. Will need to be updated to call to FSDB.
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

                if each_stand.rstrip().lower() not in self.expansion:
                    self.expansion[each_stand.rstrip().lower()] = {each_year:expansion_factor_to_stand}
                elif each_stand.rstrip().lower() in self.expansion:
                    if each_year not in self.expansion[each_stand.rstrip().lower()]:
                        self.expansion[each_stand.rstrip().lower()][each_year] = expansion_factor_to_stand
                    else:
                        pass

    def contains_unusual_plots(self):
        """ Creates a lookup table for stands, plots, and years which have areas other than 625 m\ :sup:`2`

        While many of the plots have the same area, those that do not can be called from the database explicitly. It is then easier to add all the plots together to get the total area of the stand, or to apply this area to the individual trees per hectare method.
        
        .. Example:

        >>> H = poptree_basis.Capture()
        >>> H.uplot_areas.keys()
        >>> dict_keys(['YBNF', 'GP04', 'CH10', ...
        >>> H.uplot_areas['GP04'][1957][1]
        >>> 4047.0

        **RETURNS**

        :Capture.uplot_areas: the name of the lookup table created, which can be referenced as an attribute of the Capture object.

        .. warning: Currently calls from the sqlite3 database for the references of stands, plots, and years. Will need to be updated to call to FSDB.
        """

        sql = YamlConn().queries['stand']['query_unusual_plot']
        self.pcur.execute(sql)
        
        for row in self.pcur:
            try: 
                area = round(float(row[3]),2)
            except Exception:
                area = None

            try:
                plot = int(row[2])
            except Exception:
                plot = None

            try:
                if str(row[0]).rstrip().lower() not in self.uplot_areas:
                    self.uplot_areas[str(row[0]).rstrip().lower()]={plot:{int(row[1]): area}}
                elif str(row[0].rstrip().lower()) in self.uplot_areas:
                    if plot not in self.uplot_areas[str(row[0]).rstrip().lower()]:
                        self.uplot_areas[str(row[0]).rstrip().lower()][plot] = {int(row[1]): area}
                    elif plot in self.uplot_areas[str(row[0]).rstrip().lower()]: 
                        self.uplot_areas[str(row[0]).rstrip().lower()][plot].update({int(row[1]): area})
            except Exception:
                pass

    def get_total_stand_area(self):
        """ Creates a lookup table for stands total areas in m\ :sup:`2`

        The sum of the areas of each plots is calculated in the sql, i.e. "select year, standid, sum(area_m2_corr) from plotAreas group by standid, year"

        It's faster to just have this here then do it for each one of the stands individually if you are running this in bulk.
        
        .. Example:

        >>> H = poptree_basis.Capture()
        >>> H.total_areas.keys()
        >>> dict_keys(['YBNF', 'GP04', 'CH10', ...
        >>> H.total_areas['sp06'][2001]
        >>> 2500.0

        **RETURNS**

        :Capture.total_areas: the total area of all the plots for that stand and year.

        .. warning: Currently calls from the sqlite3 database for the references of stands, plots, and years. Will need to be updated to call to FSDB.
        """
        sql = YamlConn().queries['stand']['query_total_stand']
        self.pcur.execute(sql)

        for row in self.pcur:
            try: 
                area = round(float(row[2]),2)
            except Exception:
                area = None

            try:
                stand = str(row[1])
            except Exception:
                stand = "None"

            try:
                year = int(row[0])
            except Exception:
                year = None

            try:
                if stand.rstrip().lower() not in self.total_areas:
                    self.total_areas[stand.rstrip().lower()]={year: area}
                elif str(stand.rstrip().lower()) in self.total_areas:
                    if year not in self.total_areas[stand.rstrip().lower()]:
                        self.total_areas[stand.rstrip().lower()][year] = area
                    elif year in self.total_areas[stand.rstrip().lower()]: 
                        print("error in assembling total areas - this should never be called")
            except Exception:
                pass


    def create_num_plots(self):
        """ Creates a number of plots count for each stand and year.

        **RETURNS**

        :Capture.num_plots: the number of plots for that stand and year.

        .. warning: Currently calls from the sqlite3 database for the references of stands, plots, and years. Will need to be updated to call to FSDB.
        """

        np = {}
        sql = YamlConn().queries['plot']['query_dist_plots']
        self.pcur.execute(sql)

        for row in self.pcur:
            try: 
                plot = str(row[2])
            except Exception:
                plot = "None"

            try:
                stand = str(row[0])
            except Exception:
                stand = "None"

            try:
                year = int(row[1])
            except Exception:
                year = None

            try:
                if stand.rstrip().lower() not in np:
                    np[stand.rstrip().lower()] = {year: [plot]}
                elif str(stand.rstrip().lower()) in np:
                    if year not in np[stand.rstrip().lower()]:
                        np[stand.rstrip().lower()][year] = [plot]
                    elif year in np[stand.rstrip().lower()]: 
                        np[stand.rstrip().lower()][year].append(plot)
            except Exception:
                pass

        for each_stand in np.keys():
            if each_stand not in self.num_plots.keys():
                self.num_plots[each_stand] = {x:len(np[each_stand][x]) for x in np[each_stand].keys()}

            elif each_stand in self.num_plots.keys():
                pass

if __name__ =="__main__":
    DATABASE_CONNECTION = YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    pconn, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = Capture()

    XFACTOR.num_plots.keys()
