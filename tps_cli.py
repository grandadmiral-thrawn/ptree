#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import biomass_basis
import tps_Tree
import tps_Stand
import math
import csv
import sys

analysis_type = sys.argv[1] 
target_type = sys.argv[2]
target = sys.argv[3]

# create the setup variables
DATABASE_CONNECTION = poptree_basis.YamlConn()
conn, cur = DATABASE_CONNECTION.sql_connect()
pconn, pcur = DATABASE_CONNECTION.lite3_connect()
queries = DATABASE_CONNECTION.queries
XFACTOR = poptree_basis.Capture()

if analysis_type == 't' and target_type == 't':

    A = Tree(cur, pcur, queries, target)
    Bios = A.compute_biomasses()
    Details = A.is_detail(XFACTOR)
    Checks = A.check_trees()
    Areas = A.is_unusual_area(XFACTOR)

    basic_name = target + "_basic.csv"
    checks_name = target + "_checks.csv"
    hectare_name = target + "_hectare.csv"

    A.output_tree(Bios, Details, Checks, Areas, file0 = basic_name , file1 = checks_name, file2 = hectare_name, mode='wt')

elif analysis_type == 't' and target_type == 's':

    sql = queries['stand']['cli_stand_tree'].format(standid=target)

    trees_on_stand = []
    cur.execute(sql)
    for row in cur:
        trees_on_stand.append(str(row[0]))

    # create output with the first tree:
    First_Tree = Tree(cur, pcur, queries, trees_on_stand[0])
    Bios = First_Tree.compute_biomasses()
    Details = First_Tree.is_detail(XFACTOR)
    Checks = First_Tree.check_trees()
    Areas = First_Tree.is_unusual_area(XFACTOR)

    basic_name = target + "_basic.csv"
    checks_name = target + "_checks.csv"
    hectare_name = target + "_hectare.csv"

    First_Tree.output_tree(Bios, Details, Checks, Areas, file0 = basic_name, file1 = checks_name, file2 = hectare_name, mode='wt')

    # clear out the global variables by setting to empty arrays
    Bios = {}
    Details = {}
    Checks = {}
    Areas = {}

    for each_tree in trees_on_stand[1:]:
        A = Tree(cur, pcur, queries, each_tree)
        Bios = A.compute_biomasses()
        Details = A.is_detail(XFACTOR)
        Checks = A.check_trees()
        Areas = A.is_unusual_area(XFACTOR)
        A.output_tree(Bios, Details, Checks, Areas, file0 = basic_name, file1 = checks_name, file2 = hectare_name, mode='a')

        # special cases:
        integer_plot = int(A.plotid[4:])

        if A.standid == 'ch11' and integer_plot == 11:
            A.plotid = 1

        if A.standid == 'frd2':
            print("there is no FRD2")
            continue

        if A.standid == 'frd1' and integer_plot == 2:
            print("we dont know the areas of plot 2 on frd1")
            continue 

        Bios = {}
        Details = {}
        Checks = {}
        Areas = {}

elif analysis_type == "s" and target_type == "s":

    