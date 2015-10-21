#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import biomass_basis
import tps_Tree as _t
import tps_Stand as _s
import tps_NPP as _n
import math
import csv
import sys


#######
# Basic inputs are here, used to run all the things
#######
analysis_type = sys.argv[1] 
target_type = sys.argv[2]
target = sys.argv[3]
DATABASE_CONNECTION = poptree_basis.YamlConn()
conn, cur = DATABASE_CONNECTION.sql_connect()
pconn, pcur = DATABASE_CONNECTION.lite3_connect()
queries = DATABASE_CONNECTION.queries
XFACTOR = poptree_basis.Capture()


def choose_operation():
    """ Selects which analyses to run based on inputs...


    By species and aggregate inputs are together in a file, but the aggregate is called "ALL" for its species, and it has no density.
    
    :analysis_type: "t", "s", or "q" for tree, stand, or quality control.
    :target_type: "t", "w", "s", "p", "a" for one tree, whole stand by tree, one stand, one study, or "a" for all
    """
    # one tree, output
    if analysis_type == 't' and target_type == 't':
        single_tree_on_tree()

    # one tree, qc
    elif analysis_type == 'q' and target_type == 't':
        single_tree_qc()

    # whole stand by tree, output
    elif analysis_type == 't' and target_type == 's':
        stand_on_tree()

    # whole stand by tree, checks
    elif analysis_type == 'q' and target_type == 'w':
        stand_on_tree_qc()

    # whole stand, just one stand
    elif analysis_type == 's' and target_type == 's':
        single_stand_on_stand()

    # whole stand, all stands in a study
    elif analysis_type == 's' and target_type == 'p':
        study_on_stand()

    elif analysis_type == 's' and target_type == 'a':
        all_stand_on_stand()


    elif analysis_type == 'q' and target_type == 's':
        stand_qc()

    elif analysis_type == 'q' and target_type == 'a':
        all_stand_qc()

    else:
        print("You have input invalid parameters. Your first input was {x} -- is that in \'t\', \'s\', or \'q\'? \n Your next input was {y} -- is that in \'s\', \'p\', or \'a\'? Your final input must be a treeid, standid, studyid, or the letter \'a\' for all. Note you cannot run individual trees as \'a\' yet.".format(x=analysis_type, y=target_type))

def single_tree_on_tree():
    """ Computes a single tree's values. Needs "t","t", "tree id". 

    """

    A = _t.Tree(cur, pcur, queries, target)
    Bios = A.compute_biomasses()
    Details = A.is_detail(XFACTOR)
    Areas = A.is_unusual_area(XFACTOR)

    basic_name = target + "_basic.csv"

    A.only_output_attributes(Bios, Details, Areas, datafile = basic_name, mode = 'wt')

def single_tree_qc():
    """ Computes a single tree's checks for qc. Needs "q","t", "tree id". 
    """

    A = _t.Tree(cur, pcur, queries, target)
    Checks = A.check_trees()

    checks_name = target + "_checks.csv"

    A.only_output_checks(Checks, checkfile = checks_name, mode = 'wt')


def stand_on_tree():
    """ Computes all the trees on one stand as individuals. Needs "t","s","standid".
    Standid should be four upper case characters.
    """

    mod_target = target.upper()

    sql = queries['tree']['cli_stand_tree'].format(standid=target)

    trees_on_stand = []
    cur.execute(sql)

    for row in cur:
        if  trees_on_stand ==[] or str(row[0]) >= sample_trees[0]:
            trees_on_stand.append(str(row[0]))
        else:
            trees_on_stand.insert(0, str(row[0]))

    # create output with the first tree:
    First_Tree = _t.Tree(cur, pcur, queries, trees_on_stand[0])
    Bios = First_Tree.compute_biomasses()
    Details = First_Tree.is_detail(XFACTOR)
    Areas = First_Tree.is_unusual_area(XFACTOR)

    basic_name = target + "_basic.csv"

    First_Tree.only_output_attributes(Bios, Details, Areas, file3 = basic_name, mode = 'wt')

    # clear out the global variables by setting to empty arrays
    Bios = {}
    Details = {}
    Areas = {}

    for each_tree in trees_on_stand[1:]:
        A = _t.Tree(cur, pcur, queries, each_tree)
        Bios = A.compute_biomasses()
        Details = A.is_detail(XFACTOR)
        Areas = A.is_unusual_area(XFACTOR)
        A.only_output_attributes(Bios, Details, Areas, datafile = basic_name, mode = 'a')

        Bios = {}
        Details = {}
        Checks = {}
        Areas = {}

def stand_on_tree_qc():
    """ Computes all the trees on one stand as individuals. Needs "q","w","standid".
    Standid should be four upper case characters.
    """
    mod_target = target.upper()

    sql = queries['tree']['cli_stand_tree'].format(standid=target)

    trees_on_stand = []
    cur.execute(sql)

    for row in cur:
        if  trees_on_stand ==[] or str(row[0]) >= sample_trees[0]:
            trees_on_stand.append(str(row[0]))
        else:
            trees_on_stand.insert(0, str(row[0]))

    checks_name = target + "_checks.csv"

    # create output with the first tree:
    First_Tree = _t.Tree(cur, pcur, queries, trees_on_stand[0])
    Checks = First_Tree.check_trees()
    First_Tree.only_output_checks(Checks, checkfile=check_name, mode = 'wt')
        
    Checks = {}

    for index,each_tree in enumerate(sample_trees[1:]):
        A = _t.Tree(cur, pcur, queries, each_tree)
        Checks = A.check_trees()

        A.only_output_checks(Checks, checkfile=daystring_out, mode = 'a')
        print("now checking tree number " + str(index) + " --still doing things!")
        Checks = {}


        