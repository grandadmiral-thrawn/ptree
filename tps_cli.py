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

parser = argparse.ArgumentParser(description="""TPS computes the biomass, npp, volume, basal area, and trees per hectare for trees, plots, stands, and studies from the PSP studies.
    """)
parser.add_argument("action", help="`bio` for biomass, `npp` for npp, `qc` for qc, `dtx` for details")
parser.add_argument("scale", help="`stand` for stand-scale, `tree` for individual tree scale, `plot` for all plots at the stand-scale, `study` for all stands in one study")
parser.add_argument("analysis", help="`composite` for species/all species output at the stand scale, `tree` for individual trees at the chosen scale. If using the `tree` scale, you may also specify `checks` to run quality control")
parser.add_argument("number", help="List stands, plots, studies, treeids, etc. here, one after another, separated by only spaces. The keyword --all will trigger an analysis of all the units you wish to compute at the chosen scale for the chosen analysis and action", nargs=argparse.REMAINDER)

args = parser.parse_args()

#args.action, args.scale, args.analysis, args.number - arguements needed

### CREATE CONNECTION OBJECTS GLOBALLY HERE !! ###

DATABASE_CONNECTION = poptree_basis.YamlConn()
conn, cur = DATABASE_CONNECTION.sql_connect()
queries = DATABASE_CONNECTION.queries
XFACTOR = poptree_basis.Capture(cur, queries)

### BIOMASS > ###
if args.action.lower() == 'bio':
    print("args.action is bio")
    
    ### BIOMASS > STAND ###
    if args.scale.lower() =='stand':
        print("args.scale is stand")
        
        ### BIOMASS > STAND > COMPOSITE ###
        if args.analysis.lower() == 'composite':
            print("args.analysis is composite")

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

                list_all_units = []
                sql = cur.execute(queries['execution']['list_of_all_stands'])
                for row in cur:
                    list_all_units.append(str(row[0]))

                # create the file with the first stand
                A = tps_Stand.Stand(cur, XFACTOR, queries, list_of_units[0].lower())
                BM, BTR, _ = A.compute_biomasses(XFACTOR)

                BMA = A.aggregate_biomasses(BM)

                A.write_stand_composite(BM, BMA, XFACTOR, 'all_stands_biomass_composite_output.csv', 'w')
                    
                del A
                del BM
                del BMA

                # get each stand from the list of stands and append output to the file
                for each_stand in list_of_units[1:]:

                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())


                    BM, BTR, _ = A.compute_biomasses(XFACTOR)

                    BMA = A.aggregate_biomasses(BM)

                    A.write_stand_composite(BM, BMA, XFACTOR, 'all_stands_biomass_composite_output.csv', 'a')
                    
                    del A
                    del BM
                    del BMA
            # if the first arguement is not all, no further arguements would be all

            elif args.number[0] != "--all":

                # some number of stands which is more than 1
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)

                    # create the output file based on the first given stand
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())

                    BM, BTR, _ = A.compute_biomasses(XFACTOR)

                    BMA = A.aggregate_biomasses(BM)

                    A.write_stand_composite(BM, BMA, XFACTOR, 'selected_stands_biomass_composite_output.csv', 'w')
                    
                    del A
                    del BM
                    del BMA

                    # get each stand from the given list
                    for each_stand in list_of_units[1:]:
                        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())

                        BM, BTR, _ = A.compute_biomasses(XFACTOR)

                        BMA = A.aggregate_biomasses(BM)

                        A.write_stand_composite(BM, BMA, XFACTOR, 'selected_stands_biomass_composite_output.csv', 'a')
                        del A
                        del BM
                        del BMA

                elif len(args.number) == 1:
                    list_of_units = args.number

                    # one stand uses default naming
                    A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())

                    BM, BTR, _ = A.compute_biomasses(XFACTOR)

                    BMA = A.aggregate_biomasses(BM)

                    A.write_stand_composite(BM, BMA, XFACTOR)
                    
                    del A
                    del BM
                    del BMA
                else: 
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio stand composite --all")
                
                print("computing : " + list_of_units + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        ### BIOMASS > STAND > TREE ###
        elif args.analysis == 'tree':
            print("args.analysis is tree")

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)
                elif len(args.number) == 1:
                    list_of_units = args.number
                else: 
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio tree tre --all")
                print("computing : " + list_of_units + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())
        
        elif args.analysis.lower() not in ['composite','tree']:
            print("Your input for the analysis arguement is not valid. Please follow your input of " + args.action + " and " + args.scale + " with either `composite` or `tree`")

    ### BIOMASS > TREE ###
    elif args.scale.lower() =='tree':
        print("args.scale is tree")

        ### BIOMASS > TREE > COMPOSITE, TREE ###
        if args.analysis.lower() == 'composite' or args.analysis.lower() == 'tree':
            print("args.analysis is tree -- Both the composite biomass analysis and tree biomass anlaysis are the same at the individual tree scale. ")

            # the first argument is all, so we do all the things
            if len(args.number) > 3: 
                print("For individual trees, please only select up to 3 tree id numbers; otherwise, use the `tps_cli.py bio stand tree [list of items]` arguement")

            elif len(args.number) <=3 and len(args.number) > 1:
                list_of_units = ", ".join(args.number)
                print("computing the individual tree biomasses for : " + list_of_units )

            elif len(args.number) == 1:
                list_of_units = args.number[0]
                print("computing the individual tree biomass for : " + list_of_units)

        ### BIOMASS > TREE > CHECKS ###
        elif args.analysis == 'checks':
            print("args.analysis is `checks`, which can also be called from the `qc argument.`")

            # the first argument is all, so we do all the things
            if len(args.number) > 3: 
                print("For individual trees, please only select up to 3 tree id numbers; otherwise, use the `tps_cli.py qc stand tree [list of items]` arguement for faster results")

            elif len(args.number) <=3 and len(args.number) > 1:
                list_of_units = ", ".join(args.number)
                print("computing the individual tree checks for : " + list_of_units )

            elif len(args.number) == 1:
                list_of_units = args.number[0]
                print("computing the individual tree checks for : " + list_of_units)

        elif args.analysis.lower() not in ['composite','tree','checks']:
            print("Your input for the analysis arguement is not valid. Please follow your input of " + args.action + " and " + args.scale + " with either `composite`,`tree`, or `checks`")

    ### BIOMASS > PLOT ###
    elif args.scale.lower()=="plot":
        print("args.scale is plot")

        ### BIOMASS > PLOT > COMPOSITE ###
        if args.analysis.lower() == 'composite':
            print("args.analysis is composite")
                
            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)
                elif len(args.number) == 1:
                    list_of_units = args.number
                else: 
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio stand composite --all")
                print("computing : " + list_of_units + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        ### BIOMASS > PLOT > TREE ###
        elif args.analysis == 'tree':
            print("args.analysis is tree")

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)
                elif len(args.number) == 1:
                    list_of_units = args.number
                else: 
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio tree tre --all")
                print("computing : " + list_of_units + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())
        
        elif args.analysis.lower() not in ['composite','tree']:
            print("Your input for the analysis arguement is not valid. Please follow your input of " + args.action + " and " + args.scale + " with either `composite` or `tree`")
    
    ### BIOMASS > STUDY ###
    elif args.scale.lower() == "study":
        print("args.scale is study")

        ### BIOMASS > STUDY > COMPOSITE ###
        if args.analysis.lower() == 'composite':
            print("args.analysis is composite")
                
            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)
                elif len(args.number) == 1:
                    list_of_units = args.number
                else: 
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio stand composite --all")
                print("computing : " + list_of_units + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        ### BIOMASS > STUDY > TREE ###
        elif args.analysis == 'tree':
            print("args.analysis is tree")

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)
                elif len(args.number) == 1:
                    list_of_units = args.number
                else: 
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio tree tre --all")
                print("computing : " + list_of_units + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())
        
        elif args.analysis.lower() not in ['composite','tree']:
            print("Your input for the analysis arguement is not valid. Please follow your input of " + args.action + " and " + args.scale + " with either `composite` or `tree`")

    elif args.scale.lower() not in ["stand", "tree", "plot", "study"]:
        print("Your input for the scale arguement is not valid. Please follow your input of " + args.action + " with either `stand`, `tree`, `plot`, or `study`")

### NPP ###
if args.action.lower() == 'npp':
    print("args.action is npp")
    ### NPP > STAND ###
    if args.scale.lower() =='stand':
        print("args.scale is stand")
        
        ### NPP > STAND > COMPOSITE ###
        if args.analysis.lower() == 'composite':
            print("args.analysis is composite")

            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)
                elif len(args.number) == 1:
                    list_of_units = args.number
                else: 
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio stand composite --all")
                print("computing : " + list_of_units + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        ### NPP > STAND > TREE ###
        elif args.analysis != 'composite':
            print(" You can not do NPP computations for individual trees.")

    ### NPP > TREE ###
    elif args.scale.lower() =='tree':
        print("You can not do NPP computations for individual trees")

    ### NPP > PLOT ###
    elif args.scale.lower()=="plot":
        print("args.scale is plot")

        ### NPP> PLOT > COMPOSITE ###
        if args.analysis.lower() == 'composite':
            print("args.analysis is composite")
                
            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)
                elif len(args.number) == 1:
                    list_of_units = args.number
                else: 
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio stand composite --all")
                print("computing : " + list_of_units + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        ### NPP> PLOT > TREE (not composite) ###
        elif args.analysis != 'composite':
            print("You can only compute NPP for stands, plots, and studies. Please try the syntax `tps_cli.py npp plot composite [list of plots]`")
    
    ### NPP > STUDY ###
    elif args.scale.lower() == "study":
        print("args.scale is study")

        ### NPP > STUDY > COMPOSITE ###
        if args.analysis.lower() == 'composite':
            print("args.analysis is composite")
                
            # the first argument is all, so we do all the things
            if len(args.number) == 1 and args.number[0]=="--all":
                print("computing ALL " + args.scale.lower() + "s with the " + args.analysis.lower() + " analysis for " + args.action.lower())

            # if the first arguement is not all, no further arguements would be all
            elif args.number[0] != "--all":
                if len(args.number) > 1:
                    list_of_units = ", ".join(args.number)
                elif len(args.number) == 1:
                    list_of_units = args.number
                else: 
                    print("You must specify at least one unit to compute, or use the --all tag at the end of your line, like : tps_cli.py bio stand composite --all")
                print("computing : " + list_of_units + " at the scale of " + args.scale.lower() + " with the " + args.analysis.lower() + " analysis for " + args.action.lower())

        ### BIOMASS > STUDY > TREE (not composite) ###
        elif args.analysis != 'composite':
            print("You can only compute NPP for stands, plots, and studies. Please try the syntax `tps_cli.py npp plot composite [list of study]")

    elif args.scale.lower() not in ["stand", "tree", "plot", "study"]:
        print("Your input for the scale arguement is not valid. Please follow your input of " + args.action + " with either `stand`, `tree`, `plot`, or `study`")
### QC ###
if args.action.lower() == 'qc':
    print("args.action is qc")

    ### QC > STAND ###
    if args.scale.lower() =='stand':
        print("doing QC on biomasses ast the stand scale")
        
        if args.analysis.lower() == 'composite':
            print("args.analysis is composite for quality control, doing population type analysis for trees at the stand scale- only 1 stand id at a time!")

            if len(args.number) > 1 or args.number[0] == "-all":
                print("You may not do QC on more than 1 stand at a time.")
            else:
                print("Doing QC on " + args.number[0])

        elif args.analysis.lower() == 'tree':
            print("doing QC on biomasses at the tree scale for quality control, only can do 1 stand at a time!")

            if len(args.number) > 1 or args.number[0] == "-all":
                print("You may not do QC on more than 1 stand at a time.")
            else:
                print("Doing QC on " + args.number[0])
    
        elif args.analysis.lower() not in ['composite', 'tree']:
            print("no QC method is defined for aggregate units outside of stands and trees, please try again with `tps_cli.py qc stand composite standid`")

    ### QCV > STAND > COMPOSITE ###
    elif args.scale.lower() == 'tree':
        print("doing single tree analysis for quality control")

        # if the user tries to do a QC that isn't 'tree' there's not any other option here so jsut pretend they are doing tree
        if args.analysis.lower() not in 'tree':
            print("You have specified a mode of analysis that is not individual tree biomass (`composite`). We will analyze your arguement as a tree id, if we can.")
        else:
            pass

        if len(args.number) > 5 or args.number[0] == "-all":
            print("You may not do individual tree QC on more than 5 trees at a time.")
        elif len(args.number) == 1 and args.number[0] != "all":
            list_of_units = args.number[0]
            print("Processing QC for tree named " + list_of_units)
        elif len(args.number) <= 5 and len(args.number >= 1) and args.number[0] != "-all":
            list_of_units = ", ".join(args.number)
            print("Processing QC for trees named " + list_of_units) 
        else:
            print("Doing QC on " + args.number[0])

    elif args.scale.lower() not in ['stand','tree']:
        print("There are only QC methods for stands and trees. Please try the method `tps_cli.py qc stand composite standid` or `tps_cli.py qc tree treeid`")

### DTX ###
if args.action.lower() == 'dtx':
    print("args.action is dtx")

    if args.scale.lower() != 'tree':
        print('You should specify that your detail is for a tree, like `tps_cli.py dtx tree`. We will try to match you a tree, but it may not work.')
    else:
        pass

    if args.analysis.lower() != 'tree':
        pass

    if len(args.number) > 1:
        print("We can only detail query one tree at a time right now")

    elif len(args.number) == 1 and args.number[0] != "--all":
        print("getting details for " + args.number[0])

    else:
        print("That is not a valid tree id to request for details.")

if args.action.lower() not in ['bio', 'npp','qc','dtx']:
    print("Your input for the action argument is not valid. Please type `bio`, `npp`, `qc` or `dtx`, without quotes, as in `tps_cli.py npp stand composite ncna`")