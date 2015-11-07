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


def do_NCNA_by_tree():
    """ do NCNA stand for each tree
    """
    DATABASE_CONNECTION = poptree_basis.YamlConn()
    _, cur = DATABASE_CONNECTION.sql_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = poptree_basis.Capture(cur, queries)

    sample_trees = []

    cur.execute(queries['testing']['test_tree'])
        
    for row in cur:
        if  sample_trees ==[] or str(row[0]) >= sample_trees[0]:
            sample_trees.append(str(row[0]))
        else:
            sample_trees.insert(0, str(row[0]))

    # create output with the first tree in the sample_trees list.
    First_Tree = _t.Tree(cur, queries, sample_trees[0])

    d = datetime.datetime.now()
    daystring_out = str(d.month) + str(d.day) + "_agg_test_NCNA.csv"
    #import pdb; pdb.set_trace()

    Bios = First_Tree.compute_biomasses()
    Checks = First_Tree.check_trees()

    First_Tree.only_output_attributes(Bios, datafile = daystring_out, mode = 'wt')
    First_Tree.only_output_checks(Checks, checkfile = daystring_out, mode = 'wt')

    Bios = {}
    Checks = {}

    # iterate over the rest of the trees (should be around 4000 trees on NCNA)
    for index,each_tree in enumerate(sample_trees[1:]):
        A = _t.Tree(cur, queries, each_tree)

        print("now calculating tree number " + str(index) + " --still doing things!")
        
        Bios = A.compute_biomasses()
        A.only_output_attributes(Bios, datafile = daystring_out, mode = 'a')

        Bios = {}

        
def do_NCNA_whole_stand():
    """ Computes the remeasurement biomass etc. on NCNA
    """
    DATABASE_CONNECTION = poptree_basis.YamlConn()
    _, cur = DATABASE_CONNECTION.sql_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = poptree_basis.Capture(cur, queries)
 
    test_stands = ["NCNA"]
    for each_stand in test_stands:
        
        A = _s.Stand(cur, XFACTOR, queries, each_stand)

        # tries to compute biomass without invoking special conditions for detail plots.
        BM, BTR, _ = A.compute_biomasses(XFACTOR)
        BMA = A.aggregate_biomasses(BM)
        A.write_stand_composite(BM, BMA, XFACTOR, 'all_stands_biomass_composite_output.csv', 'w')


if __name__ == "__main__":
    # Comment in any or all of the below to test on NCNA.

    do_NCNA_by_tree()
    #do_NCNA_by_tree_qc()
    do_NCNA_whole_stand()
    #lt = do_NCNA_QC()
