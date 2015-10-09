#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import biomass_basis
import tps_Tree
import tps_Stand
import math
import csv
import sys


class ArgCapture():
    """ Captures the command line arguements to run the tool.

    :analysis_type: can be "t" for tree, "s" for stand, "q" for quality control.
    :target_type: under tree mode, can be "t" for tree or "s" for stand. under stand mode, can be "s" for stand or "p" for study or "a" for all. under quality mode, can be "s" for stand or "p" for study or "a" for all.
    :target: under tree mode, can be a tree id or stand id. under stand mode, can be a stand id or a study id or another "a" for all. under quality mode, can be a stand id, a study id, or "a" again for all.

    If all three inputs are not specified, the program will not run the cli.

    """
    def __init__(self):

        self.analysis_type = sys.argv[1] 
        self.target_type = sys.argv[2]
        self.target = sys.argv[3]
        self.DATABASE_CONNECTION = poptree_basis.YamlConn()
        self.conn, self.cur = DATABASE_CONNECTION.sql_connect()
        self.pconn, self.pcur = DATABASE_CONNECTION.lite3_connect()
        self.queries = DATABASE_CONNECTION.queries
        self.XFACTOR = poptree_basis.Capture()


    def choose_operation(self):
        """ Selects which analyses to run based on inputs...
        """
        if self.analysis_type == 't' and self.target_type == 't':
            self.single_tree_on_tree()

        elif self.analysis_type == 't' and target_type == 's':
            self.stand_on_tree()

        elif self.analysis_type == 's' and target_type == 's':
            self.single_stand_on_stand()

        elif self.analysis_type == 's' and target_type == 'p':
            self.study_on_stand()

        elif self.analysis_type == 's' and target_type == 'a':
            self.all_stand_on_stand()

        elif self.analysis_type == 'q' and target_type == 's':
            self.stand_qc()

        elif self.analysis_type == 'q' and target_type == 'a':
            self.all_stand_qc()

        else:
            print("You have input invalid parameters. Your first input was {x} -- is that in \'t\', \'s\', or \'q\'? \n Your next input was {y} -- is that in \'s\', \'p\', or \'a\'? Your final input must be a treeid, standid, studyid, or the letter \'a\' for all. Note you cannot run individual trees as \'a\' yet.".format(x=self.analysis_type, y=self.target_type))

    def single_tree_on_tree(self):
        """ Computes a single tree's values (see the docs on tps_Tree for more info.)
        """

        A = Tree(self.cur, self.pcur, self.queries, self.target)
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

        