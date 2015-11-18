#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import yaml
import pymssql

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

    **RETURNS**

    A instance of the YamlConn connection object, used to keep you plugged into the database.
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

class Capture(object):
    """ This class contains dictionaries to be used in Stand computations for indexing the unique cases of minimum dbh's, stand areas, and detail plot expansions. If there is not data about a stand, a default case of area 625 m\ :sup:`2`,  minimum dbh 15.0 cm, detailPlot is False is generally assumed unless programmatic failure occurs.

    Here is a brief display of the common usage of Capture attributes within ``tps``.

    .. warning: To initiate a class of capture, you must first create a connection and a cursor explicitly using YamlConn(), like so: conn, cur = A.sql_connect()

    .. Example:

    >>> import poptree_basis
    >>> A = poptree_basis.Capture()

    >>> A.detail_reference.keys()
    >>> dict_keys(['ab08', 'av14', 'ar07', 'rs01', 'to11', 'am16', 'ax15', 'rs29', 'rs02', 'rs30', 'rs28', 'tb13', 'rs32', 'ag05', 'to04', 'ae10', 'rs31', 'pp17', 'av06'])
    >>> A.detail_reference['av14'].keys()
    >>> dict_keys([1984, 2000, 1990, 2008, 1978, 1995])
    >>> A.detail_reference['av14'][1984].keys()
    >>> dict_keys(['av140001', 'av140002', 'av140003', 'av140004', 'av140005', 'av140006', 'av140007', 'av140008', 'av140009', 'av140010', 'av140011', 'av140012', 'av140013', 'av140014', 'av140015', 'av140016'])
    >>> A.detail_reference['av14'][1984][1]
    >>> {'detail': False, 'area': 625, 'min': 5.0}

    >>> A.umins_reference['hr02'][1984]['HR020001']
    >>> 5.0

    >>> A.uplot_areas['mh03'].keys()
    >>> dict_keys([1952, 1989, 1994, 1965, 1934, 1999, 1971, 2005, 1945, 1939, 1930, 1983])
    >>> A.uplot_areas['mh03'][1952].keys()
    >>> dict_keys(['mh030001'])
    >>> A.uplot_areas['mh03'][1952]['mh030001']
    >>> 4047.0

    >>> A.expansion['rs32'][2006]
    >>> 4.0

    >>> A.additions['pila']
    >>> {1983: ['pila0010', 'pila0011', 'pila0012', 'pila0013', 'pila0014', 'pila0015', 'pila0016', 'pila0017', 'pila0018']}

    **RETURNS**

    This is a description of all the properties of a Capture class. Throughout the program, this class is often named XFACTOR.

    :A: in this example, an instance of the Capture class.

    The following attribute of the Capture class will be shown with all the nested structure written out. Other attributes, we just show the full nested structure written out as keys following the main object.

    :A.detail_reference.keys(): the standids that contain detail plots for at least 1 plot in 1 remeasurement.
    :A.detail_reference.[standid]: the years that the standid contains at least 1 detail plot
    :A.detail_reference.[standid][year]: the plotids on that standid and year when at least 1 plot is a detail plot
    :A.detail_reference.[standid][year][plotno]['detail']: Boolean True or False if a detail plot on that stand and plot and year
    :A.detail_reference.[standid][year][plotno]['area']: the area m\ :sup:`2` of the detail plot (not expanded)
    :A.detail_reference.[standid][year][plotno]['min']: the minimum dbh on that detail plot

    :A.umins_reference[standid][year][plotno]: the minimum dbh for that standid, plotid, and year, which is not 15.0 cm

    :A.uplots_areas[standid][year][plotno]: the area for the standid, year, and plotid that is not 625 m\ :sup:`2`

    :A.expansion[standid][year][plotid]: the expansion factor for the standid, year, and plotid which will not be 1.0

    :A.mortalities[standid][year][plotid]: mortality plots by stand id and year. Years in this are the actual years of the mortality measurements.

    :A.additions[standid][year][plotid]: addition plots by stand id and year. Years in this are the actual years of the addition measurements.

    :A.total_areas[standid][year]: the area of the whole stand for a given year by summing the plots.

    .. note:

    A slot exists for computing the number of plots, although we currently do not use this output.
    
    """
    def __init__(self, cursor, queries):
        self.detail_reference = {}
        self.expansion = {}
        self.uplot_areas = {}
        self.umins_reference = {}
        self.total_areas = {}
        self.num_plots = {}
        self.additions = {}
        self.mortalities = {}
        self.cur = cursor
        self.queries = queries
        self.create_additions()
        self.create_mortalities()
        self.create_detail_reference()
        self.condense_detail_reference()
        self.contains_unusual_plots()
        self.create_unusual_mins_reference()
        self.get_total_stand_area()
        #self.create_num_plots()

    def create_additions(self):
        """ Generates the look-up of plots which are "additions" in the database (activity code is A).

        **RETURNS**

        :Capture.additions: Additions plots, indexed by standid, year, and plot id.
        """
        sql = self.queries['stand']['query_additions']

        self.cur.execute(sql)

        for row in self.cur:
            plotid = str(row[0]).rstrip().lower()
            standid = plotid[0:4]
            year = int(row[1])

            if standid not in self.additions:
                self.additions[standid] = {year:[plotid]}
            elif standid in self.additions:
                if year not in self.additions[standid]:
                    self.additions[standid][year] = [plotid]
                elif year in self.additions[standid]:
                    if plotid not in self.additions[standid][year]:
                        self.additions[standid][year].append(plotid)
                    else:
                        print("the plotid : " + plotid + " is already listed as an addition for this stand and year")

        return self.additions

    def create_mortalities(self):
        """ Generates the look-up of stands, years, and plots which are "mortality checks"

        **RETURNS**

        :Capture.mortalities: Mortality plots, indexed by standid, year, and plotid
        """
        sql = self.queries['stand']['query_mortalities']

        self.cur.execute(sql)

        for row in self.cur:
            plotid = str(row[0]).rstrip().lower()
            standid = plotid[0:4]
            year = int(row[1])

            if standid not in self.mortalities:
                self.mortalities[standid] = {year:[plotid]}
            elif standid in self.mortalities:
                if year not in self.mortalities[standid]:
                    self.mortalities[standid][year] = [plotid]
                elif year in self.mortalities[standid]:
                    if plotid not in self.mortalities[standid][year]:
                        self.mortalities[standid][year].append(plotid)
                    else:
                        print("the plotid : " + plotid + " is already listed as an addition for this stand and year")
        
        return self.mortalities

    def create_detail_reference(self):
        """ Creates a reference for detail plots that any instance of Tree (called by tps_Tree) or Stand (calld by tps_Stand) can use. The reference contains the area of the plot in question (``area``), the status as detail or not detail plot in that given year (``detail``), and the minimum dbh for the plot (whether the plot is detail or not, as ``min``).

        Here is a case where the stand, year, and plot in question is NOT a detail plot.

        .. Example: 

        >>> H = Capture.detail_reference.keys()
        >>> dict_keys(['ab08', 'av14', 'ar07', 'rs01', 'to11', 'am16', 'ax15', 'rs29', 'rs02', 'rs30', 'rs28', 'tb13', 'rs32', 'ag05', 'to04', 'ae10', 'rs31', 'pp17', 'av06'])
        >>> H.detail_reference['rs01'].keys()
        >>> dict_keys([1976, 1971, 1988, 2009, 1992, 2004, 1978, 1998, 1983])
        >>> H.detail_reference['rs01'][2004]['rs010001']['area']
        >>> 625
        >>> H.detail_reference['rs01'][2004]['rs010001']['detail']
        >>> False
        >>> H.detail_reference['rs01'][2004]['rs010001']['min']
        >>> 15.0

        Here is a case where the stand, year, and plot in question is a detail plot. See how the `min` is smaller.

        .. Example :
        
        >>> H.detail_reference['rs01'][2004]['rs010003']['area']
        >>> 625
        >>> H.detail_reference['rs01'][2004]['rs010003']['detail']
        >>> True
        >>> H.detail_reference['rs01'][2004]['rs010003']['min']
        >>> 5.0

        **RETURNS**

        :Capture.detail_reference: The name of the lookup table for detail plots and their areas and minimum dbh's. If not otherwise specified, the minimum dbh for a tree on a non-detail plot or the cutoff for a big tree on a detail plot is 15.0 cm. 
        """
        stands_with_details = []
        sql = self.queries['stand']['query_context_dtl']
        self.cur.execute(sql)
        
        for row in self.cur:
            standid = str(row[0])[0:4]
            if standid not in stands_with_details:
                stands_with_details.append(standid)
            else:
                pass

        for each_stand in stands_with_details:

            if each_stand.rstrip().lower() not in self.detail_reference:
                self.detail_reference[each_stand.rstrip().lower()] = {}

            elif each_stand.rstrip().lower() in self.detail_reference:
                pass

            sql = self.queries['stand']['query_context_dtl1'].format(standid=each_stand)
            self.cur.execute(sql)
            
            for row in self.cur:
                # plot is now a string in the new method from sql server - 8 character string
                plotid = str(row[0]).rstrip().lower()
                year = int(row[1])
                detail = str(row[2])
                
                # default area is 625
                try:
                    area = int(row[3])
                except Exception:
                    area = 625.

                # default min dbh is 5
                try:
                    mindbh = round(float(row[4]),1)
                except Exception:
                    mindbh = 5.0

                if year not in self.detail_reference[each_stand.rstrip().lower()] and detail == 'Y':
                    self.detail_reference[each_stand.rstrip().lower()][year]={plotid:{'area': area, 'detail': True, 'min': mindbh}}
                elif year in self.detail_reference[each_stand.rstrip().lower()] and detail == 'Y':
                    self.detail_reference[each_stand.rstrip().lower()][year][plotid] = {'area': area, 'detail': True, 'min': mindbh}
                elif year not in self.detail_reference[each_stand.rstrip().lower()] and detail != 'Y':
                    self.detail_reference[each_stand.rstrip().lower()][year]={plotid:{'area':area, 'detail': False, 'min': mindbh}}
                elif year in self.detail_reference[each_stand.rstrip().lower()] and detail !='Y':
                    self.detail_reference[each_stand.rstrip().lower()][year][plotid] = {'area':area, 'detail':False, 'min':mindbh}

                else:
                    pass

    def create_unusual_mins_reference(self):
        """ Creates a lookup for plots that do not have minimum dbh of 15.0 cm, but are also not detail plots. That is, they are still sampled proportionally to the rest of the stand in their given year, but for whatever reason in that year, the minimum dbh is not 15.0 cm. 

        :create_unusual_mins_reference: queries the database to create a reference for plots where detailPlot is not 'T' and minimum DBH is not 15.0 cm 

        .. Example:
        
        >>> H = poptree_basis.Capture()
        >>> H.umins_reference.keys()
        >>> dict_keys(['ybnf', 'srnf', 'mrna', 'ch10',...
        >>> H.umins_reference['pf28'][1959][3]
        >>> 10.0

        **RETURNS**

        :Capture.umins_reference: The unusual minimums table contains the stand, year, and plot that have a minimum that is not 15.0 cm and is also not a detail plot.
        """
        
        sql = self.queries['stand']['query_unusual_plot_minimums_sql']
        self.cur.execute(sql)
        
        for row in self.cur:
            # returns plotid, year, plot areas
            try:
                mindbh = round(float(row[2]),3)
            except Exception:
                mindbh = 5.0


            try:
                plotid = str(row[0]).rstrip().lower() 
                standid = plotid[0:4]
            except Exception:
                plotid = "None"
                standid = "None"
            try:
                if standid not in self.umins_reference:
                    self.umins_reference[standid] = {int(row[1]): {plotid: mindbh}}

                elif standid in self.umins_reference:
                    if int(row[1]) not in self.umins_reference[standid]:
                        self.umins_reference[standid][int(row[1])] = {plotid:mindbh}

                    elif int(row[1]) in self.umins_reference[standid]:
                        if plotid not in self.umins_reference[standid][int(row[1])]:
                            self.umins_reference[standid][int(row[1])][plotid] = mindbh
                        else:
                            print("some error has occurred in finding unusual minimums on non-detail plots")

            except Exception:
                # any errors can be skipped here, and the plot in question will get the default values
                pass

    def condense_detail_reference(self):
        """ Condenses the detail reference into a readable dictionary of expansion factors by plot. The expansion factor relates the area of the detail plots (in total) to the area of the stand, in total. For example, if there are 4 detail plots of 625 m\ :sup:`2` each which is a total of 2500 m\ :sup:`2` of detail plots representing a whole stand which has 16 plots of 625 m\ :sup: `2` each on it with a total of 10000 m\ :sup: `2` (one Ha), then the expansion in this case is 4. Each Mg of biomass or single tree measured in the `detail` study is worth 4 x itself in the full sized study. In the final synopsis these are back weighted by the proportionate area of the plots to the whole

        The expansion factor only applies to trees whose dbhs are greater than the minimum dbh (usually 5.0 cm) and less than the smallest dbh for the not-detail plots (usually 15.0 cm). The terms `large` and `small` are used casually throughout the program to refer to these size groups.
        
        .. Example:

        `Given stand attribute * (area of all plots / area of all detail plots) = Representative stand attribute`

        10 Mg Biomass in small trees on detail plots * (10000 (m\ :sup:`2`) all plots / 2000 (m\ :sup:`2`) detail plots) = 50 Mg Biomass on detail plots

        .. Example:

        >>> H = poptree_basis.Capture()
        >>> H.expansion.keys()
        >>> dict_keys(['rs32', 'ag05', 'rs02', 'rs01', 'to04', 'av14', 'ar07', 'tb13', 'ae10', 'to11', 'pp17', 'am16', 'rs31', 'rs28', 'ab08', 'ax15', 'rs29', 'av06', 'rs30'])
        >>> H.expansion['rs32'][2006]
        >>> 4.0

        **RETURNS**

        :Capture.expansion: the name of the lookup table created, which can be referenced as an attribute of the Capture object.

        .. note: Unlike the other Capture methods, expansion does not require the "plot" attribute to be called. Expasion has already found the aggregate of the plots and that aggregate is the same regardless of which detail plot one is on.
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
        """ Creates a lookup table for stands, plots, and years which have areas other than 625 m\ :sup:`2`. This is the most common area.

        While many of the plots have the same area, those that do not can be called from the database explicitly. It is then easier to add all the plots together to get the total area of the stand, or to apply this area to the individual trees per hectare method.
        
        .. Example:

        >>> H = poptree_basis.Capture()
        >>> H.uplot_areas.keys()
        >>> dict_keys(['ybnf', 'gp04', 'ch10', ...
        >>> H.uplot_areas['GP04'][1957][1]
        >>> 4047.0

        **RETURNS**

        :Capture.uplot_areas: A referenced table for the areas of plots which are not 625 m\ :sup:`2`.

        .. warning: Discussions on watersheds lead us to thinking there may be another dimension for this which isn't in the current program. I.e. there are some plots whose shape matters?
        """

        sql = self.queries['stand']['query_unusual_plot_sql']
        self.cur.execute(sql)
        
        for row in self.cur:
            try: 
                area = round(float(row[2]),2)
            except Exception:
                area = None

            try:
                plotid = str(row[0]).rstrip().lower()
                standid = plotid[0:4]
            except Exception:
                plotid = "None"
                standid="None"

            try:
                year = int(row[1])
            except Exception:
                year = None


            if standid not in self.uplot_areas:
                self.uplot_areas[standid]={plotid:{year: area}}
            
            elif standid in self.uplot_areas:
                if plotid not in self.uplot_areas[standid]:
                    self.uplot_areas[standid][plotid] = {year: area}
                elif plotid in self.uplot_areas[standid]: 
                    self.uplot_areas[standid][plotid].update({year: area})

    def get_total_stand_area(self):
        """ Creates a lookup table for stands total areas in m\ :sup:`2`.

        Summing must be done locally for this because we now list the plots independently
        
        .. Example:

        >>> H = poptree_basis.Capture()
        >>> H.total_areas.keys()
        >>> dict_keys(['ybnf', 'gp04', 'ch10', ...
        >>> H.total_areas['sp06'][2001]
        >>> 2500.0

        **RETURNS**

        :Capture.total_areas: the total area of all the plots for that stand and year. All stands and years are included here.
        """
        sql = self.queries['stand']['query_total_stand_sql']
        self.cur.execute(sql)

        for row in self.cur:
            try: 
                area_plot = round(float(row[2]),2)
            except Exception:
                area_plot = None

            try:
                standid = str(row[1]).rstrip().lower()[0:4]
            except Exception:
                standid = "None"

            try:
                year = int(row[0])
            except Exception:
                year = None

            try:
                if standid not in self.total_areas:
                    self.total_areas[standid]={year: area_plot}
                elif standid in self.total_areas:
                    if year not in self.total_areas[standid]:
                        self.total_areas[standid][year] = area_plot
                    # if the year is already listed for that stand then add the area of the chosen plot    
                    elif year in self.total_areas[standid]: 
                        self.total_areas[standid][year]+=area_plot
            except Exception:
                pass

if __name__ =="__main__":
    DATABASE_CONNECTION = YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = Capture(cur, queries)

