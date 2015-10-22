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


def choose_operation(analysis_type, target_type, target):
    """ Selects which analyses to run based on inputs...

    By species and aggregate inputs are together in a file, but the aggregate is called "ALL" for its species, and it has no density.

    :analysis_type: "t", "s", or "q" for tree, stand, or quality control.
    :target_type: "t", "w", "s", "p", "a" for one tree, whole stand by tree, one stand, one study, or "a" for all
    """
    # one tree, output
    if analysis_type == 't' and target_type == 't':
        print("you are processing a single tree for its individual biomass et al. output. you entered \'t\', \'t\', and \'"+target+"\'")
        single_tree_on_tree(target)

    # one tree, qc
    elif analysis_type == 'q' and target_type == 't':
        print("you are conducting historical qc checks on a single tree. you entered \'q\', \'t\', and \'"+target+"\'")
        single_tree_qc(target)

    # whole stand by tree, output
    elif analysis_type == 't' and target_type == 's':
        print("you are processing a whole stand, tree by tree (this might take a while!). you entered \'t\', \'s\', and \'"+target+"\'")
        stand_on_tree(target)

    # whole stand by tree, checks
    elif analysis_type == 'q' and target_type == 'w':
        print("you are conducting historical population checks, tree by tree (this might take a while!). you entered \'q\', \'w\', and \'"+target+"\'")
        stand_on_tree_qc()

    # whole stand, just one stand
    elif analysis_type == 's' and target_type == 's':
        print("you are processing one stand. you entered \'s\', \'s\', and \'"+target+"\'")
        stand_on_stand(target)

    # whole stand, checks
    elif analysis_type == 'q' and target_type == 's':
        print("you are conducting historical population checks, for stand discrepancies between remeasurements. you entered \'q\', \'s\', and \'"+target+"\'")
        stand_on_stand_qc(target)

    # whole stand, all stands in a study
    elif analysis_type == 's' and target_type == 'p':
        print("you are now processing a whole study. you entered \'s\',\'p\', and \'"+target+"\'")
        study_on_stand(target)

    # # all the stands
    # elif analysis_type == 's' and target_type == 'a':
    #     all_stand_on_stand()

    # # npp, by stand
    # elif analysis_type == 'n' and target_type == 's':
    #     stand_qc()

    else:
        print("You have input invalid parameters. Your first input was {x} -- is that in \'t\', \'s\', or \'q\'? \n Your next input was {y} -- is that in \'s\', \'p\', or \'a\'? Your final input must be a treeid, standid, studyid, or the letter \'a\' for all. Note you cannot run individual trees as \'a\' yet.".format(x=analysis_type, y=target_type))

def single_tree_on_tree(target):
    """ Computes a single tree's values. Needs "t","t", "tree id". 

    """
    A = _t.Tree(cur, pcur, queries, target)
    Bios = A.compute_biomasses()
    Details = A.is_detail(XFACTOR)
    Areas = A.is_unusual_area(XFACTOR)

    basic_name = target + "_basic.csv"

    A.only_output_attributes(Bios, Details, Areas, datafile = basic_name, mode = 'wt')

def single_tree_qc(target):
    """ Computes a single tree's checks for qc. Needs "q","t", "tree id". 
    """

    A = _t.Tree(cur, pcur, queries, target)
    Checks = A.check_trees()

    checks_name = target + "_checks.csv"

    A.only_output_checks(Checks, checkfile = checks_name, mode = 'wt')


def stand_on_tree(target):
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

def stand_on_tree_qc(target):
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

def stand_on_stand(target):
    """ Computes the biomass for a single stand.
    """
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

def study_on_stands(target):
    """ Computes all the stands in a certain study code (biomass)
    """
    cur.execute(queries['execution']['list_of_stands']).format(studyid=target)

def stand_on_stand_qc(target):
    """ Checks tree populations at the stand scale (no output function written yet!)
    """
    Q = _s.QC(each_stand.lower())


if __name__=="__main__":
    #######
    # Basic inputs are here, used to run all the things
    #######

    analysis_type = sys.argv[1] 
    target_type = sys.argv[2]
    target = sys.argv[3]

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    _, cur = DATABASE_CONNECTION.sql_connect()
    _, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries
    XFACTOR = poptree_basis.Capture()

    choose_operation(analysis_type, target_type, target)