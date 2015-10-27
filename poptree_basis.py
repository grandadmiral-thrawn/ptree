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

    .. warning:: pymssql dependency. pymssql is required to connect to FSDB.

    .. note: SQLite3 support removed 10-27-2015

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

class Capture(object):
    """ This class contains dictionaries to be used in Stand computations for indexing the unique cases of minimum dbh's, stand areas, and detail plot expansions. Stands use the parameters in Capture to do specific calculations when the default case of area 625 m\ :sup:`2`,  minimum dbh 15.0 cm, detailPlot is False does not apply.

    Here is a brief display of the common usage of Capture attributes within TPS.

    .. warning: To initiate a class of capture, you must first create a connection and a cursor explicitly using YamlConn(), like so: conn, cur = A.sql_connect()

    .. Example:

    >>> import poptree_basis
    >>> A = poptree_basis.Capture()

    >>> A.detail_reference.keys()
    >>> dict_keys(['AB08', 'AV14', 'AR07', 'RS01', 'TO11', 'AM16', 'AX15', 'RS29', 'RS02', 'RS30', 'RS28', 'TB13', 'RS32', 'AG05', 'TO04', 'AE10', 'RS31', 'PP17', 'AV06'])
    >>> A.detail_reference['AV14'].keys()
    >>> dict_keys([1984, 2000, 1990, 2008, 1978, 1995])
    >>> A.detail_reference['AV14'][1984].keys()
    >>> dict_keys(['AV140001', 'AV140002', 'AV140003', 'AV140004', 'AV140005', 'AV140006', 'AV140007', 'AV140008', 'AV140009', 'AV140010', 'AV140011', 'AV140012', 'AV140013', 'AV140014', 'AV140015', 'AV140016'])
    >>> A.detail_reference['AV14'][1984][1]
    >>> {'detail': False, 'area': 625, 'min': 5.0}

    >>> A.umins_reference['HR02'][1984]['HR020001']
    >>> 5.0

    >>> A.uplot_areas['MH03'].keys()
    >>> dict_keys([1952, 1989, 1994, 1965, 1934, 1999, 1971, 2005, 1945, 1939, 1930, 1983])
    >>> A.uplot_areas['MH03'][1952].keys()
    >>> dict_keys(['MH030001'])
    >>> A.uplot_areas['MH03'][1952]['MH030001']
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
    def __init__(self, cursor, queries):
        self.detail_reference = {}
        self.expansion = {}
        self.uplot_areas = {}
        self.umins_reference = {}
        self.total_areas = {}
        self.num_plots = {}
        self.additions = {}
        # {'gmnf': 1996, 'hgbk': 1982, 'ncna': 1980, 'pila': 1983, 'rs01': 1978, 'rs02': 1978, 'rs03': 1977, 'rs13':[1981, 1982], 'sucr': 1983, 'tctr': 1997, 'ws02': 1982
        # }
        self.mortalities = {}
        # not sure how replacements differ from additions?
        # {'gmnf': 1994, 'hgbk': 1988, 'ncna': 1984, 'pila': 1988, 'rs01': 1983, 'rs02': 1983, 'rs03': 1981, 'rs13':1986, 'sucr': 1988, 'tctr': 2001, 'ws02': 1988
        # }
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
        """ generates the look-up of plots which are "additions"
        """
        sql = self.queries['stand']['query_additions']

        self.cur.execute(sql)

        for row in self.cur:
            standid = str(row[0])[0:4]
            plotid = str(row[0])
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
        """ generates the look-up of stands, years, and plots which are "mortality checks"
        """
        sql = self.queries['stand']['query_mortalities']

        self.cur.execute(sql)

        for row in self.cur:
            standid = str(row[0])[0:4]
            plotid = str(row[0])
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
        """ Creates a reference for detail plots that any instance of Tree (called by tps_Tree) or Stand (calld by tps_Stand) can use. The reference contains the area of the plot in question (`area`), the status as detail or not detail plot in that given year (`detail`), and the minimum dbh for the plot (whether detail or not, `min`).

        Here is a case where the stand, year, and plot in question is NOT a detail plot.

        .. Example: 

        >>> H = Capture.detail_reference.keys()
        >>> dict_keys(['AB08', 'AV14', 'AR07', 'RS01', 'TO11', 'AM16', 'AX15', 'RS29', 'RS02', 'RS30', 'RS28', 'TB13', 'RS32', 'AG05', 'TO04', 'AE10', 'RS31', 'PP17', 'AV06'])
        >>> H.detail_reference['RS01'].keys()
        >>> dict_keys([1976, 1971, 1988, 2009, 1992, 2004, 1978, 1998, 1983])
        >>> H.detail_reference['RS01'][2004]['RS010001']['area']
        >>> 625
        >>> H.detail_reference['RS01'][2004]['RS010001']['detail']
        >>> False
        >>> H.detail_reference['RS01'][2004]['RS010001']['min']
        >>> 15.0

        Here is a case where the stand, year, and plot in question is a detail plot. See how the `min` is smaller.

        .. Example :
        
        >>> H.detail_reference['RS01'][2004]['RS010003']['area']
        >>> 625
        >>> H.detail_reference['RS01'][2004]['RS010003']['detail']
        >>> True
        >>> H.detail_reference['RS01'][2004]['RS010003']['min']
        >>> 5.0

        **RETURNS**

        :Capture.detail_reference: The name of the lookup table for detail plots and their areas and minimum dbh's. If not otherwise specified, the minimum dbh for a tree on a non-detail plot or the cutoff for a big tree on a detail plot is 15 cm. 

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
        """ Creates a lookup for plots that do not have minimum dbh of 15 cm, but are also not detail plots. That is, they are still sampled proportionally to the rest of the stand in their given year, but for whatever reason in that year, the minimum dbh is not 15 cm. 

        :create_unusual_mins_reference: queries the database to create a reference for plots where detailPlot is not 'T' and minimum DBH is not 15.0 cm 

        .. Example:
        
        >>> H = poptree_basis.Capture()
        >>> H.umins_reference.keys()
        >>> dict_keys(['YBNF', 'SRNF', 'MRNA', 'CH10',...
        >>> H.umins_reference['PF28'][1959][3]
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
        >>> dict_keys(['RS32', 'AG05', 'RS02', 'RS01', 'TO04', 'AV14', 'AR07', 'TB13', 'AE10', 'TO11', 'PP17', 'AM16', 'RS31', 'RS28', 'AB08', 'AX15', 'RS29', 'AV06', 'RS30'])
        >>> H.expansion['RS32'][2006]
        >>> 4.0

        **RETURNS**

        :Capture.expansion: the name of the lookup table created, which can be referenced as an attribute of the Capture object.

        .. note: Unlike the other Capture methods, expansion does not require the "plot" attribute to be called. Expasion has already found the aggregate of the plots and that aggregate is the same regardless of which detail plot one is on.

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
        """ Creates a lookup table for stands, plots, and years which have areas other than 625 m\ :sup:`2`. This is the most common area.

        While many of the plots have the same area, those that do not can be called from the database explicitly. It is then easier to add all the plots together to get the total area of the stand, or to apply this area to the individual trees per hectare method.
        
        .. Example:

        >>> H = poptree_basis.Capture()
        >>> H.uplot_areas.keys()
        >>> dict_keys(['YBNF', 'GP04', 'CH10', ...
        >>> H.uplot_areas['GP04'][1957][1]
        >>> 4047.0

        **RETURNS**

        :Capture.uplot_areas: A referenced table for the areas of plots which are not 625 m\ :sup:`2`.

        .. warning: Currently calls from the sqlite3 database for the references of stands, plots, and years. Will need to be updated to call to FSDB.
        .. warning: Discussions on watersheds lead us to thinking there may be another dimension for this which isn't in the current program.
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
        >>> dict_keys(['YBNF', 'GP04', 'CH10', ...
        >>> H.total_areas['sp06'][2001]
        >>> 2500.0

        **RETURNS**

        :Capture.total_areas: the total area of all the plots for that stand and year. All stands and years are included here.

        .. warning: Currently calls from the sqlite3 database for the references of stands, plots, and years. Will need to be updated to call to FSDB.
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


    # def create_num_plots(self):
    #     """ Creates a number of plots count for each stand and year.

    #     **RETURNS**

    #     :Capture.num_plots: the number of plots for that stand and year. Serves no purpose in computation and is only used to generated the required outputs. 

    #     .. warning: Currently calls from the sqlite3 database for the references of stands, plots, and years. Will need to be updated to call to FSDB.
    #     """

    #     np = {}
    #     sql = YamlConn().queries['plot']['query_dist_plots']
    #     self.pcur.execute(sql)

    #     for row in self.pcur:
    #         try: 
    #             plot = str(row[2])
    #         except Exception:
    #             plot = "None"

    #         try:
    #             stand = str(row[0])
    #         except Exception:
    #             stand = "None"

    #         try:
    #             year = int(row[1])
    #         except Exception:
    #             year = None

    #         try:
    #             if stand.rstrip().lower() not in np:
    #                 np[stand.rstrip().lower()] = {year: [plot]}
    #             elif str(stand.rstrip().lower()) in np:
    #                 if year not in np[stand.rstrip().lower()]:
    #                     np[stand.rstrip().lower()][year] = [plot]
    #                 elif year in np[stand.rstrip().lower()]: 
    #                     np[stand.rstrip().lower()][year].append(plot)
    #         except Exception:
    #             pass

    #     for each_stand in np.keys():
    #         if each_stand not in self.num_plots.keys():
    #             self.num_plots[each_stand] = {x:len(np[each_stand][x]) for x in np[each_stand].keys()}

    #         elif each_stand in self.num_plots.keys():
    #             pass

if __name__ =="__main__":
    DATABASE_CONNECTION = YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = Capture(cur, queries)

