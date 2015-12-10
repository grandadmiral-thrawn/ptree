#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'dataRonin'

import poptree_basis
import biomass_basis
import tps_Tree
import tps_Stand
import tps_NPP
import math
import csv
import sys
import argparse

### CREATE CONNECTION OBJECTS GLOBALLY HERE !! ###

DATABASE_CONNECTION = poptree_basis.YamlConn()
conn, cur = DATABASE_CONNECTION.sql_connect()
queries = DATABASE_CONNECTION.queries
XFACTOR = poptree_basis.Capture(cur, queries)

### get details about 1 tree if you are interested in it
num_args = len(sys.argv)

if num_args == 3 and sys.argv[1] == "dtx":

    special_tree = sys.argv[2]

    file_in = input("if you would like to save your tree details to a text file please type Y otherwise they will be printed to screen.")
    if file_in != 'Y':
        mode = "--screen"
    else:
        mode = "--file"

    A = tps_Tree.Tree(cur, queries, special_tree)
    A.get_additional_info(mode)
else:
    pass

### otherwise process a good set of trees

parser = argparse.ArgumentParser(description="""TPS computes the biomass, npp, volume, basal area, and trees per hectare for trees, plots, stands, and studies from the PSP studies.
    """)
parser.add_argument("action", help="`bio` for biomass, `npp` for npp, `qc` for qc, `dtx` for details")
parser.add_argument("scale", help="`stand` for stand-scale, `tree` for individual tree scale, `plot` for all plots at the stand-scale, `study` for all stands in one study")
parser.add_argument("analysis", help="`composite` for species/all species output at the stand scale, `tree` for individual trees at the chosen scale. If using the `tree` scale, you may also specify `checks` to run quality control")
parser.add_argument("number", help="List stands, plots, studies, treeids, etc. here, one after another, separated by only spaces. The keyword --all will trigger an analysis of all the units you wish to compute at the chosen scale for the chosen analysis and action", nargs=argparse.REMAINDER)

args = parser.parse_args()


#args.action, args.scale, args.analysis, args.number - arguements needed



### BIOMASS > ###
if args.action.lower() == 'bio':

    ### BIOMASS > STAND ###
    if args.scale.lower() =='stand':

        ### BIOMASS > STAND > COMPOSITE ###
        if args.analysis.lower() == 'composite':

            # the first argument is all, so we get all the biomass on the stand
            if len(args.number) == 1 and args.number[0]=="--all":

                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

                # get all the stands, in this case from the database
                list_all_stands = []

                sql = cur.execute(queries['execution']['list_of_all_stands'])
                for row in cur:
                    list_all_stands.append(str(row[0]))

                # create a file with the first stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, list_all_stands[0].lower())
                BM, BTR, _ = A.compute_biomasses(XFACTOR)
                BMA = A.aggregate_biomasses(BM)
                A.write_stand_composite(BM, BMA, XFACTOR, 'all_stands_biomass_composite_output.csv', 'w')
                #print("Added " + A.standid + " to the output file.")
                del A
                del BM
                del BMA

                # for the rest of the stands, using the "--all" method, for biomass, append to that first opened file
                for each_stand in list_all_stands[1:]:
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                    BM, BTR, _ = A.compute_biomasses(XFACTOR)
                    BMA = A.aggregate_biomasses(BM)
                    A.write_stand_composite(BM, BMA, XFACTOR, 'all_stands_biomass_composite_output.csv', 'a')
                    #print("Added " + A.standid + " to the output file.")
                    del A
                    del BM
                    del BMA

            # if the first arguement is not all, no further arguements would be all, so we just check the number of inputs
            elif args.number[0] != "--all":

                # some number of stands which is more than 1
                if len(args.number) > 1:

                    list_of_stands = ", ".join(args.number)

                    # create the output file based on the first given stand
                    A = tps_Stand.Stand(cur, XFACTOR, queries, args.number[0])
                    BM, BTR, _ = A.compute_biomasses(XFACTOR)
                    BMA = A.aggregate_biomasses(BM)

                    cli_filename = 'selected_stands_biomass_composite_output.csv'
                    A.write_stand_composite(BM, BMA, XFACTOR, cli_filename, 'w')
                    print("wrote biomass on " + A.standid + " to " + cli_filename)
                    del A
                    del BM
                    del BMA

                    # get each stand from the given list
                    for each_stand in args.number[1:]:
                        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                        BM, BTR, _ = A.compute_biomasses(XFACTOR)
                        BMA = A.aggregate_biomasses(BM)
                        cli_filename = 'selected_stands_biomass_composite_output.csv'
                        A.write_stand_composite(BM, BMA, XFACTOR, cli_filename, 'a')
                        print("wrote biomass on " + A.standid + " to " + cli_filename)
                        del A
                        del BM
                        del BMA

                # if only one stand is given
                elif len(args.number) == 1:

                    list_of_stands = args.number[0]
                    # one stand uses default naming
                    A = tps_Stand.Stand(cur, XFACTOR, queries, list_of_stands)
                    BM, BTR, _ = A.compute_biomasses(XFACTOR)
                    BMA = A.aggregate_biomasses(BM)

                    A.write_stand_composite(BM, BMA, XFACTOR)
                    print("wrote biomass for " + A.standid + " to " + A.standid + "_stand_composite_output.csv")
                    del A
                    del BM
                    del BMA
                else:
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio stand composite --all")

                print("Computed : " + list_of_stands + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        ### BIOMASS > STAND > TREE ###
        elif args.analysis == 'tree':

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":

                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

                # get all the stands
                list_all_stands = []
                # create a file for all the trees
                cli_filename = "all_stand_indvtree_output.csv"

                sql = cur.execute(queries['execution']['list_of_all_stands'])
                for row in cur:
                    list_all_stands.append(str(row[0]))

                # create the file with the first stand, write, then delete
                A = tps_Stand.Stand(cur, XFACTOR, queries, list_all_stands[0].lower())
                A.write_individual_trees(cli_filename, 'w')
                del A

                # now iterate over all the rest of the stands, write the tree, and exit
                for each_stand in list_all_stands[1:]:
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                    A.write_individual_trees(cli_filename, 'a')
                    del A

            # if the first arguement is not all, no further arguements would be all, so we just get whatever arguements are there.
            elif args.number[0] != "--all":

                if len(args.number) > 1:

                    list_of_stands = ", ".join(args.number)

                    # create the output file based on the first given stand
                    A = tps_Stand.Stand(cur, XFACTOR, queries, args.number[0])

                    cli_filename = 'selected_stand_indvtree_output.csv'
                    A.write_individual_trees(cli_filename, 'w')
                    print("wrote biomass for individual trees on " + A.standid + " to " + cli_filename)
                    del A

                    # get each stand from the given list
                    for each_stand in args.number[1:]:
                        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                        cli_filename = 'selected_stand_indvtree_output.csv'
                        A.write_individual_trees(cli_filename, 'a')
                        print("wrote biomass for individual trees on " + A.standid + " to " + cli_filename)
                        del A

                elif len(args.number) == 1:

                    list_of_stands = args.number[0]
                    # one stand uses default naming
                    A = tps_Stand.Stand(cur, XFACTOR, queries, args.number[0])

                    # default naming convention will use that stand's name
                    A.write_individual_trees()
                    print("wrote biomass for " + A.standid + " to " + A.standid + "_stand_indvtree_output.csv")
                    del A

                else:
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio tree tre --all")
                print("computed : " + list_of_stands + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        elif args.analysis.lower() not in ['composite','tree']:
            print("Your input for the analysis arguement is not valid. Please follow your input of " + args.action + " and " + args.scale + " with either `composite` or `tree`")

    ### BIOMASS > TREE ###
    elif args.scale.lower() =='tree':

        ### BIOMASS > TREE > COMPOSITE, TREE ###
        if args.analysis.lower() == 'composite' or args.analysis.lower() == 'tree':

            # the first argument is all, so we do all the things
            if len(args.number) > 3:
                print("For individual trees, please only select up to 3 tree id numbers; otherwise, use the `tps_cli.py bio stand tree [list of items]` arguement")

            elif len(args.number) <=3 and len(args.number) > 1:
                list_of_units = ", ".join(args.number)
                print("computing the individual tree biomasses for : " + list_of_units)

                First_Tree = tps_Tree.Tree(cur, queries, args.number[0])
                Bios = First_Tree.compute_biomasses()


                try:
                    if len(args.number) == 2:
                        datafile = str(args.number[0]) + "_" + str(args.number[1]) + "_indvtree_output.csv"
                    elif len(args.number) ==3:
                        datafile = str(args.number[0]) + "_" + str(args.number[1]) + "_" + str(args.number[2]) + "_indvtree_output.csv"
                except Exception:
                    datafile = 'selected_indvtree_output.csv'

                First_Tree.only_output_attributes(Bios, datafile = datafile, mode='wt')
                print("computed biomass for " + args.number[0])
                del Bios

                for each_tree in args.number[1:]:
                    A = tps_Tree.Tree(cur, queries, each_tree)
                    Bios = A.compute_biomasses()

                    A.only_output_attributes(Bios, datafile = datafile, mode='a')

            elif len(args.number) == 1:

                try:
                    datafile = str(args.number[0]) + "_indvtree_output.csv"
                except Exception:
                    print("Cannot construct filename, using default of `selected_indvtree_ouput.csv`")
                    datafile = "selected_indvtree_output.csv"

                First_Tree = tps_Tree.Tree(cur, queries, args.number[0])
                Bios = First_Tree.compute_biomasses()
                First_Tree.only_output_attributes(Bios, datafile = datafile, mode='wt')
                print("computed biomass for " + args.number[0])

        ### BIOMASS > TREE > CHECKS ###
        elif args.analysis == 'checks':
            print("args.analysis is `checks`, which can also be called from the `qc argument.`")

            # the first argument is all, so we do all the things
            if len(args.number) > 3:
                print("For individual trees, please only select up to 3 tree id numbers; otherwise, use the `tps_cli.py qc stand tree [list of items]` arguement for faster results")

            elif len(args.number) <=3 and len(args.number) > 1:
                list_of_units = ", ".join(args.number)
                print("computing the individual tree biomasses for : " + list_of_units )

                First_Tree = tps_Tree.Tree(cur, queries, args.number[0])
                Checks = First_Tree.check_trees()
                First_Tree.only_output_checks(Checks, checkfile = 'selected_indvtree_checks.csv', mode='wt')
                print("checked biomass for " + args.number[0])
                del Checks

                for each_tree in args.number[1:]:
                    A = tps_Tree.Tree(cur, queries, each_tree)
                    Checks = A.check_trees()

                    A.only_output_checks(Checks, checkfile = 'selected_indvtree_checks.csv', mode='a')

            elif len(args.number) == 1:
                list_of_units = args.number[0]

                First_Tree = tps_Tree.Tree(cur, queries, args.number[0])
                Checks = First_Tree.check_trees()
                First_Tree.only_output_checks(Checks, checkfile = 'selected_indvtree_checks.csv', mode='wt')
                print("checked biomass for " + args.number[0])

        elif args.analysis.lower() not in ['composite','tree','checks']:

            print("Your input for the analysis arguement is not valid. Please follow your input of " + args.action + " and " + args.scale + " with either `composite`,`tree`, or `checks`")

    ### BIOMASS > PLOT ###
    elif args.scale.lower()=="plot":

        ### BIOMASS > PLOT > COMPOSITE ###
        if args.analysis.lower() == 'composite':

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

                # get all the units from the inputs that follow the last argument in.
                list_all_stands = []

                # name your output file locally
                cli_filename = "all_plot_composite_output.csv"

                sql = cur.execute(queries['execution']['list_of_all_stands'])
                for row in cur:
                    list_all_stands.append(str(row[0]))

                # create the file with the first stand, query all the plots on that stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, list_all_stands[0].lower())
                K = tps_Stand.Plot(A, XFACTOR, [])

                BM_plot = K.compute_biomasses_plot(XFACTOR)
                BMA_plot = K.aggregate_biomasses_plot(BM_plot)
                K.write_plot_composite(BM_plot, BMA_plot, XFACTOR, cli_filename, 'w')

                del A
                del K
                del BM_plot
                del BMA_plot

                # append the new plots to the existing file
                for each_stand in list_all_stands[1:]:
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                    K = tps_Stand.Plot(A, XFACTOR, [])
                    BM_plot = K.compute_biomasses_plot(XFACTOR)
                    BMA_plot = K.aggregate_biomasses_plot(BM_plot)
                    K.write_plot_composite(BM_plot, BMA_plot, XFACTOR, cli_filename, 'a')
                    del A
                    del K
                    del BMA_plot
                    del BM_plot

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)

                    # name your output file here
                    cli_filename = "selected_plot_composite_output.csv"

                    #get the stand names for all the plots
                    all_standids = [x[0:4] for x in args.number]

                    # identify unique standids
                    unique_ids = {k:None for k in all_standids}

                    # list of unique stand ids
                    uids = list(unique_ids.keys())

                    # first plots in the first stand
                    first_plots = [x for x in args.number if uids[0] in x]

                    # create the file with the first stand, query all the plots
                    A = tps_Stand.Stand(cur, XFACTOR, queries, uids[0].lower())
                    K = tps_Stand.Plot(A, XFACTOR, first_plots)

                    BM_plot = K.compute_biomasses_plot(XFACTOR)
                    BMA_plot = K.aggregate_biomasses_plot(BM_plot)

                    K.write_plot_composite(BM_plot, BMA_plot, XFACTOR, cli_filename, 'w')

                    del A
                    del K
                    del BM_plot
                    del BMA_plot

                    # iterate over the rest of the plots
                    for each_stand in uids[1:]:
                        new_plots = [x for x in args.number if each_stand in x]
                        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                        K = tps_Stand.Plot(A, XFACTOR, new_plots)
                        BM_plot = K.compute_biomasses_plot(XFACTOR)
                        BMA_plot = K.aggregate_biomasses_plot(BM_plot)
                        K.write_plot_composite(BM_plot, BMA_plot, XFACTOR, cli_filename, 'a')
                        del A
                        del K
                        del BMA_plot
                        del BM_plot
                        del new_plots

                elif len(args.number) == 1:


                    list_of_units = args.number[0]

                    print("Processing one plot: " + list_of_units)

                    cli_filename = args.number[0] + "_plot_composite_output.csv"

                    standid = args.number[0][0:4]

                    A = tps_Stand.Stand(cur, XFACTOR, queries, standid.lower())
                    K = tps_Stand.Plot(A, XFACTOR, [list_of_units])
                    BM_plot = K.compute_biomasses_plot(XFACTOR)


                    BMA_plot = K.aggregate_biomasses_plot(BM_plot)

                    K.write_plot_composite(BM_plot, BMA_plot, XFACTOR, cli_filename, 'w')
                else:
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio stand composite --all")
                print("Finished computation of plot scale biomass on " + list_of_units)

        ### BIOMASS > PLOT > TREE ###
        elif args.analysis != 'composite':
            print("Your input for the analysis arguement is not valid. Please follow your input of " + args.action + " and " + args.scale + " with `composite`. At the plot scale, individual tree computations are invalid.")

    ### BIOMASS > STUDY ###
    elif args.scale.lower() == "study":

        ### BIOMASS > STUDY > COMPOSITE ###
        if args.analysis.lower() == 'composite':

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

                cur.execute(queries['execution']['list_of_all_studies'])

                # get all the studies
                list_of_all_studies = []

                for row in cur:
                    list_of_all_studies.append(str(row[0]))

                first_study = list_of_all_studies[0]


                sql = queries['execution']['list_of_stands_in_studies'].format(studyid=first_study)

                cur.execute(sql)

                # a blank list for each stand on this study
                list_of_stands = []

                # extract the first stand and start a file
                for row in cur:
                    list_of_stands.append(str(row[0]))

                # create the file with the first stand on that first study
                A = tps_Stand.Stand(cur, XFACTOR, queries, list_of_stands[0].lower())
                BM, BTR, _ = A.compute_biomasses(XFACTOR)
                BMA = A.aggregate_biomasses(BM)
                A.write_stand_composite(BM, BMA, XFACTOR, 'all_studies_biomass_composite_output.csv', 'w')
                del A
                del BM
                del BMA

                for each_stand in list_of_stands[1:]:
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                    BM, BTR, _ = A.compute_biomasses(XFACTOR)
                    BMA = A.aggregate_biomasses(BM)
                    A.write_stand_composite(BM, BMA, XFACTOR, 'all_studies_biomass_composite_output.csv', 'a')
                    del A
                    del BM
                    del BMA

                for each_study in list_of_all_studies[1:]:

                    sql = queries['execution']['list_of_stands_in_studies'].format(studyid=each_study)
                    cur.execute(sql)

                    # a blank list for each stand on this study
                    list_of_stands = []

                    # extract the first stand and start a file
                    for row in cur:
                        list_of_stands.append(str(row[0]))

                    # get each stand from the list of stands and append output to the file
                    # for the -- all method
                    for each_stand in list_of_stands:
                        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                        BM, BTR, _ = A.compute_biomasses(XFACTOR)
                        BMA = A.aggregate_biomasses(BM)
                        A.write_stand_composite(BM, BMA, XFACTOR, 'all_studies_biomass_composite_output.csv', 'a')
                        del A
                        del BM
                        del BMA

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)

                    first_study = args.number[0]
                    sql = queries['execution']['list_of_stands_in_studies'].format(studyid=first_study)
                    cur.execute(sql)

                    # clears itself on each iteration
                    list_of_stands = []

                    # extract the first stand and start a file
                    for row in cur:
                        list_of_stands.append(str(row[0]))

                    # create the file with the first stand
                    A = tps_Stand.Stand(cur, XFACTOR, queries, list_of_stands[0].lower())
                    BM, BTR, _ = A.compute_biomasses(XFACTOR)
                    BMA = A.aggregate_biomasses(BM)
                    A.write_stand_composite(BM, BMA, XFACTOR, 'selected_studies_biomass_composite_output.csv', 'w')
                    del A
                    del BM
                    del BMA

                    for each_stand in list_of_stands[1:]:
                        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                        BM, BTR, _ = A.compute_biomasses(XFACTOR)
                        BMA = A.aggregate_biomasses(BM)
                        A.write_stand_composite(BM, BMA, XFACTOR, 'selected_studies_biomass_composite_output.csv', 'a')
                        del A
                        del BM
                        del BMA

                    for each_study in args.number[1:]:

                        sql = queries['execution']['list_of_stands_in_studies'].format(studyid=each_study)
                        cur.execute(sql)

                        # clears itself on each iteration
                        list_of_stands = []

                        # extract the first stand and start a file
                        for row in cur:
                            list_of_stands.append(str(row[0]))

                        # create the file with the first stand
                        A = tps_Stand.Stand(cur, XFACTOR, queries, list_of_stands[0].lower())
                        BM, BTR, _ = A.compute_biomasses(XFACTOR)
                        BMA = A.aggregate_biomasses(BM)
                        A.write_stand_composite(BM, BMA, XFACTOR, 'selected_studies_biomass_composite_output.csv', 'a')
                        del A
                        del BM
                        del BMA

                        # get each stand from the list of stands and append output to the file
                        # for the -- all method
                        for each_stand in list_of_stands[1:]:
                            print(each_stand)
                            A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                            BM, BTR, _ = A.compute_biomasses(XFACTOR)
                            BMA = A.aggregate_biomasses(BM)
                            A.write_stand_composite(BM, BMA, XFACTOR, 'selected_studies_biomass_composite_output.csv', 'a')
                            del A
                            del BM
                            del BMA

                elif len(args.number) == 1:
                    list_of_units = args.number[0]

                    sql = queries['execution']['list_of_stands_in_studies'].format(studyid=args.number[0])
                    cur.execute(sql)
                    # clears itself on each iteration
                    list_of_stands = []

                    # extract the first stand and start a file
                    for row in cur:
                        list_of_stands.append(str(row[0]))

                    # create the file with the first stand
                    A = tps_Stand.Stand(cur, XFACTOR, queries, list_of_stands[0].lower())
                    BM, BTR, _ = A.compute_biomasses(XFACTOR)
                    BMA = A.aggregate_biomasses(BM)
                    cli_filename = args.number[0] + '_biomass_composite_output.csv'
                    A.write_stand_composite(BM, BMA, XFACTOR, cli_filename, 'w')
                    del A
                    del BM
                    del BMA

                    # get each stand from the list of stands and append output to the file
                    # for the -- all method
                    for each_stand in list_of_stands[1:]:
                        print(each_stand)
                        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                        BM, BTR, _ = A.compute_biomasses(XFACTOR)
                        BMA = A.aggregate_biomasses(BM)
                        A.write_stand_composite(BM, BMA, XFACTOR, cli_filename, 'a')
                        del A
                        del BM
                        del BMA
            else:
                print("You must specify at least one study to compute, or use the --all tag at the end of your line, like : tps_cli.py bio study composite --all")

            print("computed : " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        ### BIOMASS > STUDY > TREE ###
        elif args.analysis == 'tree':
            print("args.analysis is tree")

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

                # get all the units from the inputs that follow the last argument in.
                list_all_stands = []

                cli_filename = "all_study_indvtree_output.csv"

                cur.execute(queries['execution']['list_of_all_studies'])

                # get all the studies
                list_of_all_studies = []

                for row in cur:
                    list_of_all_studies.append(str(row[0]))

                first_study = list_of_all_studies[0]

                sql = queries['execution']['list_of_stands_in_studies'].format(studyid=first_study)
                cur.execute(sql)
                list_of_stands = []

                # extract the first stand and start a file
                for row in cur:
                    list_of_stands.append(str(row[0]))

                # create the file with the first stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, list_of_stands[0].lower())

                # create the file with the first stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, list_of_stands[0].lower())
                A.write_individual_trees(cli_filename, 'w')
                del A

                for each_stand in list_of_stands[1:]:
                    # create the file with the first stand
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                    A.write_individual_trees(cli_filename, 'a')

                for each_study in list_of_all_studies[1:]:
                    sql = queries['execution']['list_of_stands_in_studies'].format(studyid=each_study)
                    cur.execute(sql)
                    list_of_stands = []

                    # extract the first stand and start a file
                    for row in cur:
                        list_of_stands.append(str(row[0]))

                    for each_stand in list_of_stands:
                        # create the file with the first stand
                        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                        A.write_individual_trees(cli_filename, 'a')
                        del A

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":

                if len(args.number) > 1:

                    list_of_units = ", ".join(args.number)

                    cli_filename = "selected_studies_indvtree_output.csv"

                    first_study = args.number[0]

                    sql = queries['execution']['list_of_stands_in_studies'].format(studyid=first_study)
                    cur.execute(sql)
                    list_of_stands = []

                    # extract the first stand and start a file
                    for row in cur:
                        list_of_stands.append(str(row[0]))

                    # create the file with the first stand
                    A = tps_Stand.Stand(cur, XFACTOR, queries, list_of_stands[0].lower())

                    # create the file with the first stand
                    A = tps_Stand.Stand(cur, XFACTOR, queries, list_of_stands[0].lower())
                    A.write_individual_trees(cli_filename, 'w')
                    del A

                    for each_stand in list_of_stands[1:]:
                        # create the file with the first stand
                        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                        A.write_individual_trees(cli_filename, 'a')

                    for each_study in args.number[1:]:
                        sql = queries['execution']['list_of_stands_in_studies'].format(studyid=each_study)
                        cur.execute(sql)
                        list_of_stands = []

                        # extract the first stand and start a file
                        for row in cur:
                            list_of_stands.append(str(row[0]))

                        for each_stand in list_of_stands:
                            # create the file with the first stand
                            A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                            A.write_individual_trees(cli_filename, 'a')
                            del A

                elif len(args.number) == 1:

                    list_of_units = args.number[0]

                    cli_filename = args.number[0] + "_study_indvtree_output.csv"

                    sql = queries['execution']['list_of_stands_in_studies'].format(studyid=args.number[0])

                    list_of_stands = []
                    cur.execute(sql)
                    for row in cur:
                        list_of_stands.append(str(row[0]))

                    first_stand = list_of_stands[0]
                    # one stand uses default naming
                    A = tps_Stand.Stand(cur, XFACTOR, queries, first_stand.lower())
                    A.write_individual_trees(cli_filename,'w')
                    del A

                    for each_stand in list_of_stands[1:]:
                        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                        A.write_individual_trees(cli_filename,'a')
                        del A

                else:
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio tree tree --all")
                print("computed : " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        elif args.analysis.lower() not in ['composite','tree']:
            print("Your input for the analysis arguement is not valid. Please follow your input of " + args.action + " and " + args.scale + " with either `composite` or `tree`")

    elif args.scale.lower() not in ["stand", "tree", "plot", "study"]:
        print("Your input for the scale arguement is not valid. Please follow your input of " + args.action + " with either `stand`, `tree`, `plot`, or `study`")

### NPP ###
if args.action.lower() == 'npp':

    ### NPP > STAND ###
    if args.scale.lower() =='stand':

        ### NPP > STAND > COMPOSITE ###
        if args.analysis.lower() == 'composite':

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

                cli_filename = "all_stand_composite_npp.csv"
                print(cli_filename)
                # get all the stands, in this case from the database
                list_all_stands = []

                sql = cur.execute(queries['execution']['list_of_all_stands'])
                for row in cur:
                    list_all_stands.append(str(row[0]))

                # create a file with the first stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, list_all_stands[0].lower())
                BM, _, _ = A.compute_biomasses(XFACTOR)
                BMA = A.aggregate_biomasses(BM)

                tps_NPP.write_NPP_composite_stand(A, BM, BMA, cli_filename, 'w')

                del A
                del BM
                del BMA

                for each_stand in list_all_stands[1:]:
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                    BM, _, _ = A.compute_biomasses(XFACTOR)
                    BMA = A.aggregate_biomasses(BM)

                    tps_NPP.write_NPP_composite_stand(A, BM, BMA, cli_filename, 'a')
                    del A
                    del BM
                    del BMA


            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)

                cli_filename = "selected_stand_npp_output.csv"

                # create a file with the first stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, args.number[0].lower())
                BM, _, _ = A.compute_biomasses(XFACTOR)
                BMA = A.aggregate_biomasses(BM)

                tps_NPP.write_NPP_composite_stand(A, BM, BMA, cli_filename, 'w')
                del A
                del BM
                del BMA

                for each_stand in args.number[1:]:
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                    BM, _, _ = A.compute_biomasses(XFACTOR)
                    BMA = A.aggregate_biomasses(BM)

                    tps_NPP.write_NPP_composite_stand(A, BM, BMA, cli_filename, 'a')
                    del A
                    del BM
                    del BMA

            elif len(args.number) == 1:
                list_of_units = args.number[0]

                cli_filename = args.number[0] + "_stand_npp_output.csv"
                # create a file with the first stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, args.number[0].lower())
                BM, _, _ = A.compute_biomasses(XFACTOR)
                BMA = A.aggregate_biomasses(BM)

                tps_NPP.write_NPP_composite_stand(A, BM, BMA, cli_filename, 'w')
                del A
                del BM
                del BMA

            else:
                print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio stand composite --all")
            print("computing :   NPP  at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        ### NPP > STAND > TREE ###
        elif args.analysis != 'composite':
            print(" You can not do NPP computations for individual trees.")

    ### NPP > TREE ###
    elif args.scale.lower() =='tree':
        print("You can not do NPP computations for individual trees")

    ### NPP > PLOT ###
    elif args.scale.lower()=="plot":

        ### NPP> PLOT > COMPOSITE ###
        if args.analysis.lower() == 'composite':

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

                cli_filename = "all_plot_composite_npp.csv"
                # get all the stands, in this case from the database
                list_all_stands = []

                sql = cur.execute(queries['execution']['list_of_all_stands'])
                for row in cur:
                    list_all_stands.append(str(row[0]))

                # create the file with the first stand, query all the plots on that stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, list_all_stands[0].lower())
                K = tps_Stand.Plot(A, XFACTOR, [])

                BM_plot = K.compute_biomasses_plot(XFACTOR)
                BMA_plot = K.aggregate_biomasses_plot(BM_plot)

                tps_NPP.write_NPP_composite_plot(A, BM_plot, BMA_plot, cli_filename, 'w')
                del A
                del BM_plot
                del BMA_plot

                for each_stand in list_all_stands[1:]:
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())
                    K = tps_Stand.Plot(A, XFACTOR, [])
                    BM_plot = K.compute_biomasses_plot(XFACTOR)
                    BMA_plot = K.aggregate_biomasses_plot(BM_plot)


                    tps_NPP.write_NPP_composite_plot(A, BM_plot, BMA_plot, cli_filename, 'a')
                    del A
                    del BM_plot
                    del BMA_plot


            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) >= 1:
                    list_of_units = ", ".join(args.number)
                    list_for_file = "_".join(args.number)

                cli_filename = list_for_file + "_plot_npp_output.csv"

                #get the stand names for all the plots
                all_standids = [x[0:4] for x in args.number]

                # identify unique standids
                unique_ids = {k: None for k in all_standids}

                # list of unique stand ids
                uids = sorted(list(unique_ids.keys()))

                # first plots in the first stand

                first_plots = [x for x in args.number if uids[0] in x]

                # create a file with the first stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, uids[0].lower())

                K = tps_Stand.Plot(A, XFACTOR, first_plots)

                BM_plot = K.compute_biomasses_plot(XFACTOR)
                BMA_plot = K.aggregate_biomasses_plot(BM_plot)

                tps_NPP.write_NPP_composite_plot(A, BM_plot, BMA_plot, cli_filename, 'w')
                del A
                del BM_plot
                del BMA_plot
                del K

                for index, each_stand in enumerate(uids[1:]):

                    new_plots = [x for x in args.number if uids[index] in x]
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand[0:4].lower())
                    K = tps_Stand.Plot(A, XFACTOR, [new_plots])

                    BM_plot = K.compute_biomasses_plot(XFACTOR)
                    BMA_plot = K.aggregate_biomasses_plot(BM_plot)

                    tps_NPP.write_NPP_composite_plot(A, BM_plot, BMA_plot, cli_filename, 'a')
                    del A
                    del BM_plot
                    del BMA_plot
                    del K

            elif len(args.number) == 1:
                list_of_units = args.number[0]

                cli_filename = args.number[0] + "_plot_npp_output.csv"
                # create a file with the first stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, args.number[0][0:4].lower())
                K = tps_Stand.Plot(A, XFACTOR, [args.number[0]])

                BM_plot = K.compute_biomasses_plot(XFACTOR)
                BMA_plot = K.aggregate_biomasses_plot(BM_plot)

                tps_NPP.write_NPP_composite_plot(A, BM_plot, BMA_plot, cli_filename, 'w')
                del A
                del BM_plot
                del BMA_plot
                del K

        ### NPP> PLOT > TREE (not composite) ###
        elif args.analysis != 'composite':
            print("You can only compute NPP for stands or plots. Please try the syntax `tps_cli.py npp plot composite [list of plots]`")

    ### NPP > STUDY ###
    elif args.scale.lower() not in ["stand", "plot"]:
        print("Please do NPP analyses on the scale of stands, plots, or --all")

        # ### NPP > STUDY > COMPOSITE ###
        # if args.analysis.lower() == 'composite':
        #     print("args.analysis is composite")

        #     # the first argument is all, so we do all the things
        #     if len(args.number) == 1 and args.number[0]=="--all":
        #         print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        #     # if the first arguement is not all, no further arguements would be all
        #     elif args.number[0] != "--all":
        #         if len(args.number) > 1:
        #             list_of_units = ", ".join(args.number)
        #         elif len(args.number) == 1:
        #             list_of_units = args.number
        #         else:
        #             print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio stand composite --all")
        #         print("computing : " + list_of_units + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        # ### NPP > STUDY > TREE (not composite) ###
        # elif args.analysis != 'composite':
        #     print("You can only compute NPP for stands, plots, and studies. Please try the syntax `tps_cli.py npp plot composite [list of study]")

    # elif args.scale.lower() not in ["stand", "tree", "plot", "study"]:
    #     print("Your input for the scale arguement is not valid. Please follow your input of " + args.action + " with either `stand`, `tree`, `plot`, or `study`")

### QC ###
if args.action.lower() == 'qc':
    print("QC module is still being updated. Please try another option.")

    # ### QC > STAND ###
    # if args.scale.lower() =='stand':
    #     print("Stand scale QC is still being refined.. thanks for patience")

    #     # if args.analysis.lower() == 'composite':
    #     #     print("args.analysis is composite for quality control, doing population type analysis for trees at the stand scale- only 1 stand id at a time!")

    #     #     if len(args.number) > 1 or args.number[0] == "-all":
    #     #         print("You may not do QC on more than 1 stand at a time.")
    #     #     else:
    #     #         print("Doing QC on " + args.number[0])

    #     # elif args.analysis.lower() == 'tree':
    #     #     print("doing QC on biomasses at the tree scale for quality control, only can do 1 stand at a time!")

    #     #     if len(args.number) > 1 or args.number[0] == "-all":
    #     #         print("You may not do QC on more than 1 stand at a time.")
    #     #     else:
    #     #         print("Doing QC on " + args.number[0])

    #     # elif args.analysis.lower() not in ['composite', 'tree']:
    #     #     print("no QC method is defined for aggregate units outside of stands and trees, please try again with `tps_cli.py qc stand composite standid`")

    # ### QCV > STAND > COMPOSITE ###
    # elif args.scale.lower() == 'tree':
    #     print("doing single tree analysis for quality control, please specify the term tree twice here for clarity")

    #     # if the user tries to do a QC that isn't 'tree' there's not any other option here so jsut pretend they are doing tree
    #     if args.analysis.lower() not in 'tree':
    #         print("You have specified a mode of analysis that is not individual tree biomass (`composite`). We will analyze your arguement as a tree id, if we can.")
    #     else:
    #         pass

    #     if len(args.number) > 5 or args.number[0] == "--all":
    #         print("You may not do individual tree QC on more than 5 trees at a time.")
    #     elif len(args.number) == 1 and args.number[0] != "all":
    #         list_of_units = args.number[0]
    #         print("Processing QC for tree named " + list_of_units)

    #         A = tps_Tree.Tree()

    #     elif len(args.number) <= 5 and len(args.number >= 1) and args.number[0] != "--all":
    #         list_of_units = ", ".join(args.number)

    #         print("Processing QC for trees named " + list_of_units)
    #     else:
    #         print("Doing QC on " + args.number[0])

    # elif args.scale.lower() not in ['stand','tree']:
    #     print("There are only QC methods for stands and trees. Please try the method `tps_cli.py qc stand composite standid` or `tps_cli.py qc tree treeid`")



# if args.action.lower() not in ['bio', 'npp','qc','dtx']:
#     print("Your input for the action argument is not valid. Please type `bio`, `npp`, `qc` or `dtx`, without quotes, as in `tps_cli.py npp stand composite ncna`")