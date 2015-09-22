#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import biomass_basis
import sys


class Plot(object):
    """The Plot object aggregates the biomasses for each plot.
    Plots are made for each year
    """
    def __init__(self, standid, plotid):


        self.standid = standid
        self.plotid = plotid
        self.is_detail = False
        self.big_trees ={'bio':None,'jbio':None,'vol':None,'TPA':None}
        self.small_trees={'bio':None,'jbio':None,'vol':None,'TPA':None}

    def is_small_plot(self):
        """ Determines if a plot is a detail plot and if so gets the appropriate expansion factor
        """
         if self.standid not in Xfactor.detail_reference.keys():
            return False

if __name__ == "__main__":
    """ Basic setup for computing trees, plots, stands, etc. Database connections and look up references"""
    standid = sys.argv[1]
    plotid = sys.argv[2]

    # Plotid should be an integer
    if not isinstance(plotid, int):
        try:
            plotid = int(plotid)
        except Exception as e4:
            print('plot id should be an integer -- error in tps_Plot.py')
            import pdb; pdb.set_trace()

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    pconn, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries

    # creates lookups for expansion factors
    Xfactor = poptree_basis.DetailCapture()