#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import csv
import biomass_basis
import tps_Tree as _t
import tps_Stand as _s
import tps_NPP as _n
import datetime


def do_computations():
    """ A simple test run through some stands so that we can test the functionality of the program.
    """

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = poptree_basis.Capture(cur, queries)

    test_stands = ['RS01', 'RS02', 'RS30', 'TB13', 'AR07', 'AM16', 'RS29', 'RS32', 'AE10', 'AV06', 'TO04']
    
    for each_stand in test_stands:
        
        A = _s.Stand(cur, XFACTOR, queries, each_stand.lower())

        K = _s.Plot(A, XFACTOR, [])
        BM, BTR, ROB= A.compute_biomasses(XFACTOR)

        BM_plot = K.compute_biomasses_plot(XFACTOR)
    
        BMA = A.aggregate_biomasses(BM)

        BMA_plot = K.aggregate_biomasses_plot(BM_plot)

        _n.write_NPP_composite_stand(A, BM, BMA)
        _n.write_NPP_composite_plot(K, BM_plot, BMA_plot)