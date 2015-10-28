#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import biomass_basis
import bisect
import csv

class Plot(object):
    """Plots contain individual trees, grouped by year and species. Plots produce outputs of biomass ( Mg/ha ), volume (m\ :sup:`3`), Jenkins biomass ( Mg/ha ), TPH (number of trees/ ha), and basal area (m\ :sup:`2` / ha).

    .. Example:

    >>> A = Plot(cur, pcur, XFACTOR, queries, 'NCNA')
    >>> A.cur = <pymssql.Cursor object at 0x1007a4648>
    >>> A.pcur = <sqlite3.Cursor object at 0x10078cce0>
    >>> A.tree_list = "SELECT fsdbdata.dbo.tp00101.treeid, fsdbdata.dbo.tp00101.species..."
    >>> A.species_list = ""SELECT DISTINCT(fsdbdata.dbo.tp00101.species) from ..."
    >>> A.eqn_query = "SELECT SPECIES, EQNSET, FORM, H1, H2, H3, B1 ..."
    >>> A.eqns = {'abam': {'normal': <function Stand.select_eqns.<locals>.<lambda> at 0x1007d9730>}..."
    >>> A.od[1985]['abam'][4]['dead']
    >>> [('av06000400017', None, '6', '1985')]

    .. Note: shifted keys are the years with live trees; mortality only years are merged into these.

    >>> A.od.keys()
    >>> dict_keys([1985, 1987, 1988, 2007, 1993, 1978, 1981, 1998, 1983])
    >>> A.shifted.keys()
    >>> dict_keys([1993, 1978, 1988, 1998, 2007])
    >>> A.mortality_years
    >>> [1981, 1983, 1985, 1987]
 
    """
    def __init__(self, cur, pcur, XFACTOR, queries, plotid):
        self.plotid = plotid
        self.standid = plotid[0:4]
        self.cur = cur
        self.pcur = pcur
        self.tree_list = queries['plot']['query']
        self.tree_list_m = queries['plot']['query_trees_m']
        self.species_list = queries['plot']['query_species']
        self.eqn_query = queries['tree']['sql_1tree_eqn']
        self.study_id = ""
        self.my_area = 625.
        self.woodden_dict = {}
        self.proxy_dict = {}
        self.component_dict = {}
        self.eqns = {}
        self.od = {}
        self.shifted = {}
        self.mortality_years = []
        self.total_area_ref = {}
        self.additions = []
        self.replacement = ""



        # get the area of the plot
        self.get_my_area()


    def get_my_area(self, XFACTOR):
        """ Get the area of the one plot. Use the Capture object to determine it from unusual plot areas table. 

        **INTERNAL VARIABLES**

        :Capture.uplot_areas: contains the areas for all plots who do not have area of 625 (m\ :sup:`2`)
        """
        if self.standid not in XFACTOR.uplot_areas.keys():
            self.my_area = 625.

        else:
            try:
                integer_plot = int(self.plotid[4:8])
                self.my_area = XFACTOR.uplot_areas[self.standid][self.year][integer_plot]
            except Exception:
                try:
                    self.my_area = XFACTOR.