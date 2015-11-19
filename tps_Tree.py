#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import csv
import biomass_basis


class Tree(object):
    """ A Tree object contains the required metrics and functions to compute Biomass ( Mg ), Jenkins Biomass ( Mg ), Volume ( m\ :sup:`3` ) , and Basal Area ( m\ :sup:`2` ) for any one tree. 

    Tree objects can also create a check file for individual tree history problems, although this is not automatically output.

    Tree objects represent a tree as it is in TP00101; that is, each Tree object contains all the years of that tree's re-measurements, no matter its status. If a tree is dead, it's dbh is taken from the last known not-dead measurement. If a tree is missing, it's dbh is taken from the last-known not missing measurement.

    A Tree will also detail which of it's components it calculates: most softwoods get initially the volume of stemwood and convert to biomass, and most hardwoods get initially the total aboveground biomass, and convert to volume. Jenkins equations always get the total aboveground biomass.

    .. Example:

    >>> import tps
    >>> import poptree_basis
    >>> import biomass_basis
    >>> A = Tree(cur, 'NCNA001800216')
    >>> A.tid = 'ncna001800216'
    >>> A.cur = <pymssql.cursor>
    >>> A.tree_query= "SELECT <columns> from ..."
    >>> A.eqn_query = "SELECT <columns> from ..."
    >>> A.species = "TSHE"
    >>> A.state = [(1942, 16.0, '1', 'G'), (1945, 17.9, '1','G')]
    >>> A.eqns = {'normal' : lambda x :<function 039459x342>}
    >>> A.woodden = 0.44

    **INPUTS**

    :cur: a pymssql cursor, created by YamlConn.
    :queries: queries, taken from `qf_2.yml`, also created by YamlConn
    :tid: a 15-character tree id, whose format is roughly `plotid` + `tree number`

    **RETURNS**

    An instance of the Tree object, which holds the tree in all its years and all that is needed to process it. This method is great for introspecting one specific tree, but is pretty slow for anything more than 1 tree (two trees is okay, also).

    .. note:: `Tree.state` contains `[year, dbh, status, dbh_code]`. Although status is an integer, it is recorded as a string here because it is descriptive. `1` is OK, `2` is Ingrowth, `3` is merged or fused, `6` is Dead, and `9` is Missing. See : `Tree Status Codes <http://andrewsforest.oregonstate.edu/data/domains.cfm?domain=enum&dbcode=Tp001&attid=7291&topnav=8/>`_ . DBH Codes are also all displayed as strings, although some are integers. See : `Tree DBH Codes <http://andrewsforest.oregonstate.edu/data/domains.cfm?domain=enum&dbcode=Tp001&attid=7287&topnav=8/>`_.

    .. warning:: `Tree.cur` must be created in an external variable, or this will be very slow, because the program will want to go to the database many times if you run more than one tree.

    """

    def __init__(self, cur, queries, tid):

        self.tid = str(tid).strip().lower()
        self.cur = cur
        self.tree_query = queries['tree']['sql_1tree']
        self.eqn_query = queries['tree']['sql_1tree_eqn']
        self.additional_info=queries['tree']['tag_and_notes']
        self.species = ""
        self.studyid = ""
        self.standid = ""
        self.state =[]
        self.eqns = {}
        self.proxy = ""
        self.component = ""
        self.woodden = 0.0
        self.additional = {}

        self.get_a_tree()

    def get_a_tree(self):
        """ Retrieves a single tree and assign its species, standid, and plot; create a list of lists describing that tree for each remeasurement in its life. Gathers the equations the tree needs to have its attributes computed. 

        **INPUTS**

        No explicit inputs are needed

        **RETURNS**

        Populates the Tree object with the data for that specific tree, generating these parameters:

        :Tree.state: a list of lists containing the year, dbh, dbh_code, and status_code
        :Tree.eqns: a dictionary of eqns keyed by 'normal', 'big', or 'component' containing lambda functions to receive dbh inputs and compute Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), and wood density.
        :sql: sql query defined in 'qf_2.yaml'
        :form: equation 'form' such as lnln, d2ht, etc.
        :proxy: if a tree does not have its own equation, a proxy equation is used from a similar species. For example, `prunu` uses `alru` as both are small hardwoods.
        """

        # the case of the tree id doesn't matter, since the sql statement just looks for a 'like'
        sql = self.tree_query.format(tid=self.tid)

        self.cur.execute(sql)

        for index, row in enumerate(self.cur):
            if index == 0:
                self.species = str(row[1]).strip().lower()
                self.standid = str(row[2]).strip().lower()
                self.plotid = str(row[3]).strip().lower()
                self.studyid = str(row[8]).strip().upper()
                self.standid = str(row[9]).strip().upper()
            else:
                pass

            # append to state to Tree.state, to create a list of tuples with : ( year, dbh, status, dbh_code )
            # on connection, when a tree has a missing DBH (dead?) a None will be passed. Later it will be populated with the mortality DBH, if it truely is dead.
            try:
                self.state.append( [int(str(row[6])), round(float(str(row[4])),3), str(row[5]), str(row[7])] )
            except Exception:
                self.state.append( [int(str(row[6])), None, str(row[5]), str(row[7])] )

        # get the equation for that tree
        sql_2 = self.eqn_query.format(species=self.species)

        # note : f = lambda x : biomass_basis.which_fx('as_d2htcasc')(0.5, x, 5, 6, 7, 2, 3)
        self.cur.execute(sql_2)

        for row in self.cur:
            # identify the form of the equation -- as long as its not comp bio we just extract it -- if it's comp bio we need to get each reference. in some cases the equation might cross the 'big' barrier so we need to index it by this

            form = str(row[2]).rstrip().lower()
            
            try:
                woodden = round(float(str(row[11])),3)
            except:
                woodden = None

            self.woodden = woodden

            try:
                proxy = str(row[12]).strip().lower()
            except Exception:
                proxy = "None"

            self.proxy = proxy

            try:
                component = str(row[13]).strip().lower()
            except Exception:
                component = "None"

            self.component = component

            try:
                h1 = round(float(str(row[3])),6)
            except:
                h1 = None
            try:
                h2 = round(float(str(row[4])),6)
            except:
                h2 = None
            try:
                h3 = round(float(str(row[5])),6)
            except:
                h3 = None
            try:
                b1 = round(float(str(row[6])),6)
            except:
                b1 = None
            try:
                b2 = round(float(str(row[7])),6)
            except:
                b2 = None
            try:
                b3 = round(float(str(row[8])),6)
            except:
                b3 = None
            try:
                j1 = round(float(str(row[9])),6)
            except:
                j1 = None
            try:
                j2 = round(float(str(row[10])),6)
            except:
                j2 = None

            if self.species == "acci":
                print("ACCI tree found, number " + self.tid + ", do not compute!")
                continue

            else:
            
                this_eqn = lambda x : biomass_basis.which_fx(form)(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                self.eqns.update({str(row[1]).rstrip().lower():this_eqn})

    def compute_biomasses(self):
        """ Compute biomass ( Mg ) , volume ( m\ :sup:`3` ), Jenkins' biomass ( Mg ) and wood density ( g/cm\ :sup:`3` ) from equations

        If a tree is in it's death year (i.e. has a status of '6'), the dbh from the previous live measurement is used.

        .. Example:

        >>> A = Tree(cur, pcur, queries, 'NCNA000100014')
        >>> A.state
        >>> [[1979, 47.5, '1', 'G'], [1981, None, '6', 'M']]
        >>> A.compute_biomasses()
        >>> [(1.2639, 2.8725, 1.14323, 0.44), (1.2639, 2.8725, 1.14323, 0.44), [0.002, 0.002]]

        If a tree is missing (i.e. it has a status of '9'), it is assumed to be alive, with the last known live tree dbh.

        **INPUTS**

        No explicit inputs are needed

        **RETURNS**

        Populates the Tree object with the biomasses and basal area for that specific tree, using these parameters:

        :list_of_biomasses: a list of tuples generated by the biomass equations' returns
        :list_of_basal: a list of basal areas created by ``dbh * dbh * 0.00007854``

        .. note: Biomass and Jenkins' biomass are in Mg for individual trees computed in this way. Hectare division happens when the tree is written to file.

        """

        # set these lists to empty at the top of the function so that even in the worst case, all that will be returned is empty lists
        list_of_biomasses = []
        list_of_basal = []

        try:
            list_of_biomasses = [self.eqns[biomass_basis.maxref(x, self.species)](x) for (_,x,_,_) in self.state]
            list_of_basal = [round(0.00007854*float(x)*float(x),6) for (_,x,_,_) in self.state]
            
            return list_of_biomasses, list_of_basal
        
        except Exception:
            
            # warn if the tree is an acci, and skip it.
            if self.species == "acci":
                print("acci found, do not compute! please remove from database tree: " + self.tid)
                list_of_biomasses = []
                list_of_basal = []

                return list_of_biomasses, list_of_basal
            
            else:
                try:
                    list_of_biomasses = [self.eqns['normal'](x) for (_,x,_,_) in self.state]
                    list_of_basal = [round(0.00007854*float(x)*float(x),6) for (_,x,_,_) in self.state]
                    
                    return list_of_biomasses, list_of_basal
                
                except Exception:
                    
                    try:
                        # in the cases where there is a 1 and then a 9... and then a 1 again... 
                        for index, each_state in enumerate(self.state):
                            if self.state[index][1:3] == [None,'9']:
                                if index - 1 > 0:
                                    self.state[index][1] = self.state[index-1][1]
                                elif index-1 <= 0:
                                    self.state[index][1] = 0.0
                                else:
                                    pass
                        
                        list_of_biomasses = [self.eqns['normal'](x) for (_,x,_,_) in self.state]
                        list_of_basal = [round(0.00007854*float(x)*float(x),6) for (_,x,_,_) in self.state]

                        return list_of_biomasses, list_of_basal
                    
                    except Exception:

                        try:
                            # if the final dbh is missing and the tree is dead or missing, take the final year from that missing value and give it the biomass, volume, and jenkins of the prior value
                            if self.state[-1][1:3] == [None,'6'] or self.state[-1][1:3] == [None,'9']:
                                
                                final_year = self.state[-1][0]
                                proxy_dbh = self.state[-2][1]
                                
                                list_of_biomasses = [self.eqns[biomass_basis.maxref(x, self.species)](x) for (_,x,_,_) in self.state[:-1]]

                                list_of_basal = [round(0.00007854*float(x)*float(x),6) for (_,x,_,_) in self.state[:-1]]
                                
                                final_biomasses = list_of_biomasses[-1]
                                final_basal = list_of_basal[-1]

                                list_of_biomasses.append(final_biomasses)
                                list_of_basal.append(final_basal)

                                # set the final dbh to be the dbh from the one before that
                                self.state[-1][1] = proxy_dbh

                                return list_of_biomasses, list_of_basal
                            
                            else:
                                # new errors to debug
                                print("error in tps_Tree.py in compute_biomass function with dealing with biomasses where dbh is None. please CTRL+F for this error and fix")
                                return list_of_biomasses, list_of_basal
                        
                        except Exception:
                            print("still some kind of error in tree biomass computation, treeid is " + self.tid + ": please check databases for species and status. Please CTRL+F for this error. Exiting.")

    def is_detail(self, XFACTOR):
        """ Returns the expansion attribute from the Capture object as a dictionary specific for this tree.  

        First the stand is checked against the list of stands taht at some point in time contained a detail plot. If the stand is not in the list a default lookup of 1.0 is returned. Otherwise, a multiplier for detail plot is returned.

        If the plot is a detail plot and the tree has a dbh which is less than 15.0 cm but greater than the minimum dbh listed, then a factor other than 1.0 will be returned.

        **INPUTS**

        :XFACTOR: an instance of Capture, which is used here to map year and plot id onto the area of the plot and the minimum dbh. Detail plots get `expanded` if they have small trees to a greater proportion of the stand's area.

        **RETURNS**

        :expansion_dict: a dictionary by year containing the expansion factor that should be applied. If the year is not present, there is a 1.0 applied.
        """
        expansion_dict = {year:1.0 for (year,_,_,_) in self.state}

        # if the plot is not a detail plot in any year, all expansion factors are 1.
        if self.standid not in XFACTOR.detail_reference.keys():
            return expansion_dict
            
        else:
            # if there are no years that the tree has a dbh of < 15., then all expansion factors are 1
            small_tree_search = [(year,dbh) for (year,dbh,_,_) in self.state if dbh != None and dbh < 15.]

            if small_tree_search == []:
                return expansion_dict
            
            else:
                expansion_dict = {}
                
                # test that the year is a detail plot year and that the tree exceeds the minimum, and get the expansion factor
                integer_plot = int(self.plotid[4:])

                for (each_year, each_dbh) in small_tree_search:
                    
                    if integer_plot in XFACTOR.detail_reference[self.standid][each_year].keys() and XFACTOR.detail_reference[self.standid][each_year][integer_plot]['min'] <= each_dbh:
                        
                        expansion_factor = XFACTOR.expansion[self.standid][each_year]

                    else:
                        expansion_factor = 1.0

                    expansion_dict.update({each_year:expansion_factor})

                return expansion_dict

    def is_unusual_area(self, XFACTOR):
        """ Returns the uplot_areas attribute from the Capture object as a dictionary specific for this tree.  

        If the plot is listed in the unique areas reference, that reference will be returned for the year, otherwise, the default 625 m\ :sup:`2` is returned

        **INPUTS**

        :XFACTOR: an instance of Capture, which is used here to map year and plot id onto the area of the plot. If the plot has a non-standard area (i.e. it is not 625 m\ :sup:`2`), this value is returned.

        **RETURNS**

        :area_dict: the area of the plot that the tree is on, defaults to 625. if not specified.
        """
        area_dict = {year: 625. for (year,dbh,_,_) in self.state if dbh != None}

        if self.standid.lower() not in XFACTOR.uplot_areas.keys():
            return area_dict

        else:

            integer_plot = int(self.plotid[4:])
            yearlist = [year for (year,dbh,_,_) in self.state if dbh != None]
            
            for each_year in yearlist:

                try:
                    area = XFACTOR.uplot_areas[self.standid.lower()][each_year][integer_plot]
                    area_dict.update({each_year:area})
                
                except Exception:
                    # if that year doesn't have a weird area, pass over it, since the area will default to 625 m
                    pass

            return area_dict

    def check_trees(self):
        """ Performs checks on tree ``state`` (i.e. ``Tree.state``). These checks test whether or not logical sequences of tree status are being followed. For example, a tree cannot die twice. See rules:

        **RULES:**

        * A tree should not have more than one death (``double-death``)
        * A tree should not die and then re-appear (``lazarus``)
        * A tree should not go missing and then re-appear (``houdini``)
        * A tree should not grow more than 10 percent per year between re-measurements unless it is smaller than 8.0 cm on the first of those measurements (``growthx``)
        * A tree should not decrease in size by more than 10 percent per year between re-measurements (``shrinkx``)
        * We should be told if a tree's dbh code changes from G or V to any inferior dbh code (1,2,3,4,8,9,M or U) - see `DBH CODES <http://andrewsforest.oregonstate.edu/data/domains.cfm?domain=enum&dbcode=Tp001&attid=7287&topnav=8>`_ (``degradex``)
        * This method shouldn't be called in the case where there is only one state

        The internal function of check_trees uses a few non-standard parameters, including:

        :intervals: are the string representation of the intervals between two measurements
        :statuses: strings containing pairs of statuses that follow one another in time
        :dbh_degrade: strings containing pairs of dbh codes that follow one another in time

        **INPUTS**

        No explicit inputs are needed.

        **RETURNS**

        :tc: a dictionary of 'tree checks', referenced by the string containing the interval between two measurements
            
        * Houdini trees : "9" then something not "9"
        * Lazarus trees : "6" then something not "9"
        * Double-death: more than 1 "6"
        * DegradeX : changes from dbh code of "G" (good) or "V" (verified) to "M" (missing) or "U" (unmeasured)
        * ShrinkX : mean percentage shrink per year if mean percentage shrink more than 10 percent
        * GrowthX : mean percentage growth per year if mean percentage growth more than 10 percent 

        .. note:: if a tree does not fail the checks, it gets a "none" returned.

        .. note:: the output of the checks are the the "Checks" file, which can be renamed.

        .. note:: check_trees() is timely to run, and therefore is not automatically called by the program.
        """
        
        if len(self.state) <=1:
            return False
        
        else:

            intervals = [str(one) +"-" + str(two) for (one,two) in zip([year for (year,_,_,_) in self.state[:-1]],[year for (year,_,_,_) in self.state[1:]])]
            statuses = [str(one) +"," + str(two) for (one,two) in zip([status for (_,_,status,_) in self.state[:-1]],[status for (_,_,status,_) in self.state[1:]])]
            dbh_degrade = [str(one) +"," + str(two) for (one,two) in zip([status for (_,_,_,status) in self.state[:-1]],[status for (_,_,_,status) in self.state[1:]])]
            
            # the change in dbh between two intervals, measured in change in dbh/year
            try:
                percent_change_dbh_forward = [round(((two[1] - one[1])/(two[0]-one[0]))/one[1], 2)*100 for (one,two) in zip([(year,dbh) for (year,dbh,_,_) in self.state[:-1]],[(year,dbh) for (year,dbh,_,_) in self.state[1:]])]
                #print("assessing on " + self.tid)
            except Exception:
                
                # when the last DBH is None we need to reset it to the second to last dbh, but keep the correct year
                all_dbh_except_end = [(year,dbh) for (year,dbh,_,_) in self.state[1:-1]]
                penultimate_dbh = (self.state[-1][0],self.state[-2][1])
                all_dbh_except_end.append(penultimate_dbh)
                
                try:
                    percent_change_dbh_forward = [round(((two[1] - one[1])/(two[0]-one[0]))/one[1], 2)*100 for (one,two) in zip([(year,dbh) for (year,dbh,_,_) in self.state[:-1]], all_dbh_except_end)]
                except Exception: 
                    # if there are more instances of early death then just continue and tc "should" fill in nones... this is what happens if more than 1 missing dbh
                    pass

            # default dictionary
            tc = {x:{'deathx':"None", 'lazarus': "None", 'houdini':"None", 'growthx':"None", 'shrinkx':"None", 'degradex':"None"} for x in intervals}

            indices_double_dead = [intervals[index] for index,value in enumerate(statuses) if value =="6,6"]
            indices_lazarus = [intervals[index] for index,value in enumerate(statuses) if value in ["6,1","6,2","6,3"]]
            indices_houdini = [intervals[index] for index,value in enumerate(statuses) if value in ["9,1","9,2","9,3"]]
            try:
                indices_growthx = [(intervals[index],value) for index,value in enumerate(percent_change_dbh_forward) if value >= 30.0]
            except Exception:
                indices_growthx = []
            try:
                indices_shrinkx = [(intervals[index],value) for index,value in enumerate(percent_change_dbh_forward) if value <=-30.0]
            except Exception:
                indices_shrinkx = []

            indices_degrade = [intervals[index] for index,value in enumerate(dbh_degrade) if value in ["G,M","G,U","V,M","V,U"]]
            

            {tc[x].update({'deathx':True}) for x in indices_double_dead}
            {tc[x].update({'lazarus':True}) for x in indices_lazarus}
            {tc[x].update({'houdini':True}) for x in indices_houdini}
            {tc[x].update({'growthx': round(value, 2)}) for (x,value) in indices_growthx}
            {tc[x].update({'shrinkx': round(value, 2)}) for (x,value) in indices_shrinkx}
            {tc[x].update({'degradex': True}) for x in indices_degrade}
            
            return tc

    def get_additional_info(self, mode="--screen"):
        """ Gets the tag and check-notes from the database for the tree and outputs it to the screen
        
        **INPUTS**

        :mode: either `--screen` (default) or `--csv` (specified). If `--csv` the outputs will have their own csv file.

        **RETURNS**

        Either a csv file is saved or a screen of information is presented. For details, see the documentation for ``tps_cli.py``, which is where this function is generally called.
        """

        sql = self.additional_info.format(treeid=self.tid)

        self.cur.execute(sql)

        for row in self.cur:
            if int(row[0]) not in self.additional.keys():
                self.additional[int(row[0])] = {'tag': str(row[1]), 'notes': str(row[2])}
            elif int(row[0]) in self.additional.keys():
                pass

        state_years = [self.state[i][0] for i,_ in enumerate(self.state)]
        state_dbhs = [self.state[i][1] for i,_ in enumerate(self.state)]
        state_status = [self.state[i][2] for i,_ in enumerate(self.state)]
        state_dbhcode = [self.state[i][3] for i,_ in enumerate(self.state)]
        
        temporary_reference = {}

        found_years = sorted(list(self.additional.keys()))

        # get the additional information and make sure it maps to found years
        for index, each_year in enumerate(state_years):
            if each_year not in temporary_reference:
                if each_year not in found_years:
                    continue
                elif each_year in found_years:
                    if each_year not in temporary_reference:
                        temporary_reference[each_year] = {'dbh': state_dbhs[index], 'status': state_status[index], 'dbhcode': state_dbhcode[index]}
                    elif each_year in temporary_reference:
                        pass


        if mode == '--screen':

            for each_year in found_years:
                print("Tree: " + str(self.tid))
                print("Year: " + str(each_year))
                print("Stand: " + str(self.standid))
                print("Plot: " + str(self.plotid))
                print("Study: " + str(self.studyid))
                print("DBH: " + str(temporary_reference[each_year]['dbh']))
                print("Status: " + temporary_reference[each_year]['status'])
                print("DBH Code: " + temporary_reference[each_year]['dbhcode'])
                print("Tag: " + str(self.additional[each_year]['tag']))
                print("Notes: " + str(self.additional[each_year]['notes']).rstrip())
                print("-------------------")

        elif mode == '--file':

            filename = self.tid + "_tag_and_notes.csv"

            with open(filename, mode) as writefile:
                writer = csv.writer(writefile, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)

                writer.writerow(['TREEID','YEAR','STAND','PLOT','STUDY','DBH','STATUS','DBHCODE','TAG','NOTES'])
                for each_year in found_years:
                    new_row = [self.treeid, str(each_year), str(self.standid), str(self.plotid), str(self.study), temporary_reference[each_year]['dbh'], temporary_reference[each_year]['status'], temporary_reference[each_year]['dbhcode'], str(self.additional[each_year]['tag']), str(self.additional[each_year]['notes'])]
                    writer.writerow(new_row)

    def output_tree_agg(self, Bios, Checks, datafile = 'all_indv_tree_output.csv', checkfile = 'all_check_tree_output.csv', mode = 'wt'):
        """ Writes a csv files, for both the biomasses and the "checks". If filenames are given as arguements, these can be used, otherwise, default filenames will be assigned.

        .. note:: This method is really slow if doing more than just a few trees. 

        **INPUTS**

        :Bios: computed biomasses, Jenkins' biomasses, basal areas, volumes etc. from `compute_biomass()`
        :Checks: reference dictionary from `check_trees()`
        :datafile, checkfile: the names of csv files for output. The first arguement will be for the data, the second will be for the checks.
        :mode: `wt` for write one time, `a` for append.

        **RETURNS**

        A file containing individual trees, aggregated by stand or plot. It is really slow to run this function. Save it for very peculiar trees and use ``tps_cli.py``
        """

        # Writes a new "aggregate" output with both tree on per hectare basis and tree NOT per hectare.

        with open(datafile, mode) as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)
            
            # if the file is in append mode, do not write headers
            if mode != 'a':
                headers = ['DBCODE', 'ENTITY', 'TREEID', 'COMPONENT', 'YEAR', 'BA_M2', 'VOL_M3', 'BIO_MG', 'JENKBIO_MG']
                writer.writerow(headers)
            
            else:
                pass

            for index, each_state in enumerate(self.state):

                try:

                    new_row = ['TP001', '13', self.tid.upper(), self.component, each_state[0], round(Bios[1][index],6), round(Bios[0][index][1],4), round(Bios[0][index][0],4),  round(Bios[0][index][2],4)]
                    
                    writer.writerow(new_row)

                except KeyError:
                    # occurs sometimes if the final state and the second to final state are 9 and then 6 ... 
                    if self.state[-1][1] == None and each_state == self.state[-1]:
                        self.state[-1][1] = self.state[-2][1]


                        new_row = ['TP001', '13', self.tid.upper(), self.component, each_state[0],round(Bios[1][index],6), round(Bios[0][index][1],4), round(Bios[0][index][0],4), round(Bios[0][index][2],4)]
                        
                        writer.writerow(new_row)

                    else:
                        print("an unexpected error has occured while trying to print individual tree output, please debug. check the inputs in tp00101 and the equations in tp00110")
                        import pdb; pdb.set_trace()


        # writes the checks output, if it can be written, otherwise, just goes on.
        if Checks != False:

            with open(checkfile, mode) as writefile:
                writer = csv.writer(writefile, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)
                
                # if the file is in append mode, do not write headers
                if mode != 'a':    
                    headers = ['TREEID', 'SPECIES', 'INTERVAL','SHRINK_X_FLAGGED','GROWTH_X_FLAGGED','DOUBLE_DEATH_FLAG','LAZARUS_FLAG','HOUDINI_FLAG','DEGRADE_FLAG']
                    writer.writerow(headers)
                else:
                    pass

                for each_interval in sorted(Checks.keys()):
                    new_row = [self.tid.upper(), self.species.upper(), each_interval, Checks[each_interval]['shrinkx'], Checks[each_interval]['growthx'], Checks[each_interval]['deathx'], Checks[each_interval]['lazarus'], Checks[each_interval]['houdini'], Checks[each_interval]['degradex']]

                    writer.writerow(new_row)
        
        else:

            print("Could not write checks for " + self.tid + " - only one state exists :)")


    def only_output_attributes(self, Bios, datafile = 'all_indv_tree_output.csv', mode='wt'):
        """ Writes a csv file, containing both the tree measurements for the individual trees. Can accept a filename as arguement. Does not do checks.

        .. note:: This method is slow if doing more than just a few trees. It only writes the attributes, rather than trying to write all the checks as well, which take longer.

        When the program is executed on the stand level, and this output is given (see example in `tps_Sample.py`) trees are sorted by tree id (ascending alphabetical order.)

        **INPUTS**

        :Bios: computed biomasses, Jenkins' biomasses, basal areas, volumes etc. from :compute_biomass():
        :datafile: the name of the csv file to output to.
        :mode: `wt` for write one time, `a` for append.

        **RETURNS**

        A file containing only biomass information about a tree or set of 3 or fewer trees.
        """

        # Writes a new "aggregate" output with both tree on per hectare basis and tree NOT per hectare.

        with open(datafile, mode) as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)

            # if the file is in append mode, do not write headers
            if mode != 'a':
            
                headers = ['DBCODE', 'ENTITY', 'TREEID', 'COMPONENT', 'YEAR', 'BASAL_AREA_M2', 'VOLUME_M3', 'BIOMASS_MG', 'JENKINS_MG']
                writer.writerow(headers)
            
            else:
                pass

            for index, each_state in enumerate(self.state):

                try:

                    new_row = ['TP001', '11', self.tid.upper(), self.component, each_state[0], round(Bios[1][index],6), round(Bios[0][index][1],4), round(Bios[0][index][0],4),  round(Bios[0][index][2],4)]
                    
                    writer.writerow(new_row)

                except KeyError:
                    # occurs sometimes if the final state and the second to final state are 9 and then 6 ... 
                    if self.state[-1][1] == None and each_state == self.state[-1]:
                        self.state[-1][1] = self.state[-2][1]


                        new_row = ['TP001', '11', self.tid.upper(), self.component, each_state[0],round(Bios[1][index],6), round(Bios[0][index][1],4), round(Bios[0][index][0],4), round(Bios[0][index][2],4)]
                        
                        writer.writerow(new_row)

                    else:
                        print("an unexpected error has occured while trying to print individual tree output, please debug. check the inputs in tp00101 and the equations in tp00110")
                        import pdb; pdb.set_trace()


    def only_output_checks(self, Checks, checkfile = 'all_indv_tree_checks.csv', mode='wt'):
        """ A method to only write out the Checks when computed. Run separately from biomasses for faster results.

        **INPUTS**

        :Checks: the results from running the checks routine
        :checkfile: the name of the file you wish to output to.
        :mode: `wt` for write one time, `a` for append.

        **RETURNS**

        A file containing true or false for the tree checks from `check_trees`
        """
        # writes the checks output, if it can be written, otherwise, returns a file containing only "NA" because the checks are Not Applicable. This would happen if there was only one remeasurement
        if Checks != False:

            with open(checkfile, mode) as writefile:
                writer = csv.writer(writefile, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)
                
                # if the file is in append mode, do not write headers
                if mode != 'a':    
                    headers = ['TREEID', 'SPECIES', 'INTERVAL','SHRINK_X_FLAGGED','GROWTH_X_FLAGGED','DOUBLE_DEATH_FLAG','LAZARUS_FLAG','HOUDINI_FLAG','DEGRADE_FLAG']
                    writer.writerow(headers)
                else:
                    pass

                for each_interval in sorted(Checks.keys()):
                    new_row = [self.tid.upper(), self.species.upper(), each_interval, Checks[each_interval]['shrinkx'], Checks[each_interval]['growthx'], Checks[each_interval]['deathx'], Checks[each_interval]['lazarus'], Checks[each_interval]['houdini'], Checks[each_interval]['degradex']]

                    writer.writerow(new_row)
        
        else:

            print("could not perform checks for " + self.tid + " only one remeasurement has been taken :)")


if __name__ == "__main__":

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    queries = DATABASE_CONNECTION.queries

    # creates lookups for expansion factors, areas, etc. stores locally.
    XFACTOR = poptree_basis.Capture(cur, queries)
    

    # a shorter query of trees by stand to work with:
    sample_trees = ["HGBK061000002"]

    # create output with the first tree, to initiate the csv file.
    First_Tree = Tree(cur, queries, sample_trees[0])
    Bios = First_Tree.compute_biomasses()
    Checks = First_Tree.check_trees()

    First_Tree.output_tree_agg(Bios, Checks, datafile = "individual_tree_bio.csv", checkfile="individual_tree_checks.csv", mode = 'wt')

    First_Tree.get_additional_info(mode="--screen")
    # clear out the global variables by setting to empty arrays
    Bios = {}
    Checks = {}

    for each_tree in sample_trees[1:]:
        A = Tree(cur, queries, each_tree)
        Bios = A.compute_biomasses()
        Checks = A.check_trees()

        A.output_tree_agg(Bios, Checks, datafile= "individual_tree_bio.csv", checkfile="individual_tree_checks.csv", mode = 'a')

        Bios = {}
        Checks = {}
    