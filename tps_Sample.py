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
    _, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = poptree_basis.Capture()

    sample_trees = []

    cur.execute(queries['testing']['test_tree'])
        
    for row in cur:
        if  sample_trees ==[] or str(row[0]) >= sample_trees[0]:
            sample_trees.append(str(row[0]))
        else:
            sample_trees.insert(0, str(row[0]))

    # create output with the first tree in the sample_trees list.
    First_Tree = _t.Tree(cur, pcur, queries, sample_trees[0])

    d = datetime.datetime.now()
    daystring_out = str(d.month) + str(d.day) + "_agg_test_NCNA.csv"
    #import pdb; pdb.set_trace()

    Bios = First_Tree.compute_biomasses()
    Details = First_Tree.is_detail(XFACTOR)
    Areas = First_Tree.is_unusual_area(XFACTOR)
    First_Tree.only_output_attributes(Bios, Details, Areas, datafile = daystring_out, mode = 'wt')

    Bios = {}
    Areas = {}
    Details = {}

    # iterate over the rest of the trees (should be around 4000 trees on NCNA)
    for index,each_tree in enumerate(sample_trees[1:]):
        A = _t.Tree(cur, pcur, queries, each_tree)

        print("now calculating tree number " + str(index) + " --still doing things!")
        
        Bios = A.compute_biomasses()
        Areas = A.is_unusual_area(XFACTOR)
        Details = A.is_detail(XFACTOR)
        A.only_output_attributes(Bios, Details, Areas, datafile = daystring_out, mode = 'a')

        Bios = {}
        Areas = {}
        Details = {}

def do_NCNA_by_tree_qc():
    """ do NCNA stand for each tree
    """
    DATABASE_CONNECTION = poptree_basis.YamlConn()
    _, cur = DATABASE_CONNECTION.sql_connect()
    _, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = poptree_basis.Capture()

    sample_trees = []

    cur.execute(queries['testing']['test_tree'])
        
    for row in cur:
        if  sample_trees ==[] or str(row[0]) >= sample_trees[0]:
            sample_trees.append(str(row[0]))
        else:
            sample_trees.insert(0, str(row[0]))


    d = datetime.datetime.now()
    daystring_out = str(d.month) + str(d.day) + "_check_test_NCNA.csv"

    # create output with the first tree in the sample_trees list.
    First_Tree = _t.Tree(cur, pcur, queries, sample_trees[0])
    Checks = First_Tree.check_trees()
    First_Tree.only_output_checks(Checks, checkfile=daystring_out, mode = 'wt')

    Checks = {}

    for index,each_tree in enumerate(sample_trees[1:]):
        A = _t.Tree(cur, pcur, queries, each_tree)
        Checks = A.check_trees()

        A.only_output_checks(Checks, checkfile=daystring_out, mode = 'a')
        print("now checking tree number " + str(index) + " --still doing things!")
        Checks = {}
        
def do_NCNA_whole_stand():
    """ Computes the remeasurement biomass etc. on NCNA
    """
    DATABASE_CONNECTION = poptree_basis.YamlConn()
    _, cur = DATABASE_CONNECTION.sql_connect()
    _, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = poptree_basis.Capture()
 
    test_stands = ["NCNA"]
    for each_stand in test_stands:
        
        A = _s.Stand(cur, pcur, XFACTOR, queries, each_stand)

        # tries to compute biomass without invoking special conditions for detail plots.
        BM, _ = A.compute_normal_biomasses(XFACTOR)
        
        # if special conditions need to be invoked, call them because Biomasses returns empty
        if BM == {}:
            Biomasses,_ = A.compute_special_biomasses(XFACTOR)
            # Aggregate those biomasses
            Biomasses_aggregate = A.aggregate_biomasses(Biomasses)
            A.write_stand_composite(Biomasses, Biomasses_Agg, XFACTOR)
    
        else:
            BMA = A.aggregate_biomasses(BM)
            A.write_stand_composite(BM, BMA, XFACTOR)

def do_NCNA_QC():
    """ Compute various information about trees getting lost, or maybe not!
    """
    DATABASE_CONNECTION = poptree_basis.YamlConn()
    _, cur = DATABASE_CONNECTION.sql_connect()
    _, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = poptree_basis.Capture()

    test_stands = ["NCNA"]
    for each_stand in test_stands:
        
        Q = _s.QC(each_stand.lower())


if __name__ == "__main__":
    # Comment in any or all of the below to test on NCNA.

    #do_NCNA_by_tree()
    #do_NCNA_by_tree_qc()
    #do_NCNA_whole_stand()
    #lt = do_NCNA_QC()
