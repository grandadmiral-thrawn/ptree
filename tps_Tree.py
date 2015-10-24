#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import csv
import biomass_basis


class Tree(object):
    """ A Tree object contains the required metrics and functions to compute Biomass ( Mg ), Jenkins Biomass ( Mg ), Volume ( m\ :sup:`3` ) , and Basal Area ( m\ :sup:`2` ) for any one tree. 

    Tree objects can also create a check file for individual tree history problems.

    Tree objects represent a tree as it is in TP00101; that is, each Tree object contains all the years of that tree's re-measurements, no matter its status. 

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

    .. note: Tree.state contains [year, dbh, status, dbh_code]. Although status is an integer, it is recorded as a string here because it is descriptive. '1' is OK, '2' is Ingrowth, '3' is merged or fused, '6' is dead, and '9' is missing. See : `Tree Status Codes <http://andrewsforest.oregonstate.edu/data/domains.cfm?domain=enum&dbcode=Tp001&attid=7291&topnav=8/>`_ . DBH Codes are also all displayed as strings, although some are integers. Description here : `Tree DBH Codes <http://andrewsforest.oregonstate.edu/data/domains.cfm?domain=enum&dbcode=Tp001&attid=7287&topnav=8/>`_

    .. warning: A.cur must be created in an external variable, or this will be very slow, because it will want to go to the database many times if you run more than one tree.

    """

    def __init__(self, cur, pcur, queries, tid):

        self.tid = str(tid).strip().lower()
        self.cur = cur
        self.pcur = pcur
        self.tree_query = queries['tree']['sql_1tree']
        self.eqn_query = queries['tree']['sql_1tree_eqn']
        self.species = ""
        self.studyid = ""
        self.standid = ""
        self.state =[]
        self.eqns = {}
        self.proxy = ""
        self.component = ""
        self.woodden = 0.0

        self.get_a_tree()

    def get_a_tree(self):
        """ Retrieves a single tree and assign its species, standid, and plot; create a list of lists describing that tree for each remeasurement in its life. Gathers the equations the tree needs to have its attributes computed. 

        **INTERNAL VARIABLES**

        :Tree.state: a list of lists containing the year, dbh, dbh_code, and status_code
        :Tree.eqns: a dictionary of eqns keyed by 'normal', 'big', or 'component' containing lambda functions to receive dbh inputs and compute Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), and wood density.
        :sql: sql query defined in 'qf_2.yaml'
        :sql_2: another sql query defined in 'qf_2.yaml'
        :form: equation 'form' such as as_lnln, as_compbio, etc.
        :proxy: if a tree does not have its own equation, a proxy equation is used from a similar species. This proxy species is needed in the output.
        """
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
        """ Compute biomass (Mg) , volume (m\ :sup:`3`), Jenkins' biomass (Mg) and wood density (g/cm\ :sup:`3`) from equations

        If a tree is in it's death year (i.e. has a status of '6'), the dbh from the previous live measurement is used.

        .. Example:

        >>> A = Tree(cur, pcur, queries, 'NCNA000100014')
        >>> A.state
        >>> [[1979, 47.5, '1', 'G'], [1981, None, '6', 'M']]
        >>> A.compute_biomasses()
        >>> [(1.2639, 2.8725, 1.14323, 0.44), (1.2639, 2.8725, 1.14323, 0.44), [0.002, 0.002]]

        .. note: Biomass and Jenkins' biomass are in Mg. Hectare division happens when the tree is written to file.
        
        **INTERNAL VARIABLES**

        :list_of_biomasses: a list of tuples generated by the biomass equations' returns
        :list_of_basal: a list of basal areas created by dbh*dbh*0.00007854
        :proxy_dbh: in years where the dbh is not extant because of mortality, the proxy dbh is used to compute the biomasses

        """

        # set these lists to empty at the top of the function so that even in the worst case, all that will be returned is empty lists
        list_of_biomasses = []
        list_of_basal = []

        try:
            list_of_biomasses = [self.eqns[biomass_basis.maxref(x, self.species)](x) for (_,x,_,_) in self.state]
            list_of_basal = [round(0.00007854*float(x)*float(x),6) for (_,x,_,_) in self.state]
            
            return list_of_biomasses, list_of_basal
        
        except Exception:
            
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
                                print("error in tps_Tree.py with dealing with biomasses where DBH is None?")
                                return list_of_biomasses, list_of_basal
                        except Exception:
                            print("still some kind of error in tree computation, treeid is " + self.tid + " please check databases for species and status")

    def is_detail(self, XFACTOR):
        """ Returns the expansion attribute from the Capture object as a dictionary specific for this tree.  

        First the stand is checked against the list of stands taht at some point in time contained a detail plot. If the stand is not in the list a default lookup of 1.0 is returned. Otherwise, a multiplier for detail plot is returned.

        If the plot is a detail plot and the tree has a dbh which is less than 15.0 cm but greater than the minimum dbh listed, then a factor other than 1.0 will be returned.

        **INTERNAL VARIABLES**

        :XFACTOR: is an instance of the Capture object, which tells us if a plot is a detail plot or not. 
        :standid: the stand of a tree object
        :plot: the plotid attribute of a tree object
        :dbh: the dbh attribute of a tree object
        :year: the year attribute of a tree object

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

        **INTERNAL VARIABLES**

        :XFACTOR: is an instance of the Capture object.
        :standid: the stand of a tree object
        :plot: the plotid attribute of a tree object
        :dbh: the dbh attribute of a tree object
        :year: the year attribute of a tree object

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

        **INTERNAL VARIABLES**

        :intervals: are the string representation of the intervals between two measurements
        :statuses: strings containing pairs of statuses that follow one another in time
        :dbh_degrade: strings containing pairs of dbh_codes that follow one another in time

        **RETURNS**

        :tc: a dictionary of 'tree checks', referenced by the string containing the interval between two measurements
            
        * Houdini trees: "9" then something not "9"
        * Lazarus trees: "6" then something not "9"
        * Double-death: more than 1 "6"
        * DegradeX: changes from dbh code of "G" (good) or "V" (verified) to "M" (missing) or "U" (unmeasured)
        * ShrinkX : mean percentage shrink per year if mean percentage shrink > 10 %
        * GrowthX : mean percentage growth per year if mean percentage growth > 10 %

        .. note : if a tree does not fail the checks, it gets a "none" returned.

        .. note : the output of the checks are the the "Checks" file, which can be renamed.
        """
        #print("computing on " + self.tid)
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

    def output_tree_agg(self, Bios, Checks, datafile = 'all_indv_tree_output.csv', checkfile = 'all_check_tree_output.csv', mode = 'wt'):
        """ Writes a csv files, for both the biomasses and the "checks". If filenames are given as arguements, these can be used, otherwise, default filenames will be assigned.

        .. note: THIS IS THE CURRENT PREFERRED METHOD. 

        **INPUT VARIABLES**

        :Bios: computed biomasses, Jenkins' biomasses, basal areas, volumes etc. from `compute_biomass()`
        :Checks: reference dictionary from `check_trees()`
        :datafile, checkfile: the names of csv files for output. The first arguement will be for the data, the second will be for the checks.
        :mode: `wt` for write one time, `a` for append.
        """

        # Writes a new "aggregate" output with both tree on per hectare basis and tree NOT per hectare.

        with open(datafile, mode) as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)
            
            # if the file is in append mode, do not write headers
            if mode != 'a':
                headers = ['DBCODE', 'ENTITY', 'TREEID', 'COMPONENT', 'YEAR', 'BASAL_AREA_M2', 'VOLUME_M3', 'BIOMASS_MG', 'JENKINS_MG', 'COMP_MG']
                writer.writerow(headers)
            
            else:
                pass

            for index, each_state in enumerate(self.state):

                try:

                    new_row = ['TP001', '13', self.tid.upper(), self.component, each_state[0], round(Bios[1][index],6), round(Bios[0][index][1],4), round(Bios[0][index][0],4),  round(Bios[0][index][2],4), 'None']
                    
                    writer.writerow(new_row)

                except KeyError:
                    # occurs sometimes if the final state and the second to final state are 9 and then 6 ... 
                    if self.state[-1][1] == None and each_state == self.state[-1]:
                        self.state[-1][1] = self.state[-2][1]


                        new_row = ['TP001', '13', self.tid.upper(), self.component, each_state[0],round(Bios[1][index],6), round(Bios[0][index][1],4), round(Bios[0][index][0],4), round(Bios[0][index][2],4), 'None']
                        
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

        .. note: THIS IS THE CURRENT PREFERRED, EASY METHOD. It only writes the attributes, rather than trying to write all the checks as well, which take longer.

        When the program is executed on the stand level, and this output is given (see example in `tps_Sample.py`) trees are sorted by tree id (ascending alphabetical order.)

        **INPUT VARIABLES**

        :Bios: computed biomasses, Jenkins' biomasses, basal areas, volumes etc. from :compute_biomass():
        :datafile: the name of the csv file to output to.
        :mode: `wt` for write one time, `a` for append.
        """

        # Writes a new "aggregate" output with both tree on per hectare basis and tree NOT per hectare.

        with open(datafile, mode) as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)

            # if the file is in append mode, do not write headers
            if mode != 'a':
            
                headers = ['DBCODE', 'ENTITY', 'TREEID', 'COMPONENT', 'YEAR', 'BASAL_AREA_M2', 'VOLUME_M3', 'BIOMASS_MG', 'JENKINS_MG', 'COMP_MG']
                writer.writerow(headers)
            
            else:
                pass

            for index, each_state in enumerate(self.state):

                try:

                    new_row = ['TP001', '13', self.tid.upper(), self.component, each_state[0], round(Bios[1][index],6), round(Bios[0][index][1],4), round(Bios[0][index][0],4),  round(Bios[0][index][2],4), 'None']
                    
                    writer.writerow(new_row)

                except KeyError:
                    # occurs sometimes if the final state and the second to final state are 9 and then 6 ... 
                    if self.state[-1][1] == None and each_state == self.state[-1]:
                        self.state[-1][1] = self.state[-2][1]


                        new_row = ['TP001', '13', self.tid.upper(), self.component, each_state[0],round(Bios[1][index],6), round(Bios[0][index][1],4), round(Bios[0][index][0],4), round(Bios[0][index][2],4), 'None']
                        
                        writer.writerow(new_row)

                    else:
                        print("an unexpected error has occured while trying to print individual tree output, please debug. check the inputs in tp00101 and the equations in tp00110")
                        import pdb; pdb.set_trace()


    def only_output_checks(self, Checks, checkfile = 'all_indv_tree_checks.csv', mode='wt'):
        """ A method to only write out the Checks when computed. Run separately from biomasses for faster results.

        **INPUT VARIABLES**

        :Checks: the results from running the checks routine
        :checkfile: the name of the file you wish to output to.
        :mode: `wt` for write one time, `a` for append.
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
    pconn, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries

    # creates lookups for expansion factors
    XFACTOR = poptree_basis.Capture()
    
    # creates the Biomasses/Basal Areas and the Detail plot expansions
    # A = Tree(cur, pcur, queries, 'TO11000200005')
    # A = Tree(cur, pcur, queries, 'CH09000100002')
    
    # Bios = A.compute_biomasses()
    # Checks = A.check_trees()
    

    # # a list of test trees to work through -- just a sample set you can use that has a lot of diversity if you are interested!

    #sample_trees = ["OL03000100013", "OL03000100014", "CH42000100004", "CH42000100004","CH42000100005", "CH42000100138", "WS02010200001", "WS02010200002", "WS02010200003", "WS02010200004", "WS02010200005", "WS02010200007", "WS02010200006", "WS02010200008", "WS02010200009", "WS02010200010", "CFMF000100027", "FRA3000100001", "FRA3000100002", "FRA3000100003", "FRA3000100004", "FRA3000100005", "FRA3000100006", "FRA3000100007", "FRA3000100008", "FRA3000100009", "FRA3000100010", "FRA3000100011", "FRA3000100012", "FRA3000100013", "FRA3000100014", "FRA3000100015", "FRA3000100016", "FRA3000100017", "FRA3000100018", "FRA3000100019", "AX15000100001", "AX15000100002", "AX15000100003", "AX15000100004", "AX15000100005", "AX15000100006", "AX15000100007", "AX15000100008", "AX15000100009", "AX15000100010", "PIJE000100001", "PIJE000100002", "PIJE000100003", "PIJE000100004", "PIJE000100005", "PIJE000100006", "PIJE000100007", "PIJE000100008", "PIJE000100009", "PIJE000100010", "FRA3000100020", "NCNA000100014", "NCNA003100232", "NCNA002800010", "NCNA001800216", "NCNA002100017", "NCNA001800137", "NCNA001200063", "NCNA000400081", "NCNA000900065", "NCNA000400100", "NCNA004000089", "NCNA004400132", "NCNA004400056", "NCNA003700002", "NCNA003900028", "NCNA004000057", "NCNA003700019", "NCNA003900055", "NCNA003500196", "NCNA003800069", "HS02000700010", "HS02000700011", "HS02000700012", "HS02000700013", "HS02000700014", "HS02000800001", "HS02000800002", "HS02000800003", "HS02000800004", "HS02000800005", "HS02000800006", "HS02000800007", "HS02001300016", "HS02001300017", "HS02001300018", "HS02001300019", "HS02001300020", "HS02001300021", "HS02001300022", "HS02001400001", "CH11000100001", "CH11000100002", "CH11000100003", "CH11000100004", "CH11000100005", "CH11000100006", "CH11000100007", "CH11000100008", "CH11000100009", "CH11000100010", "CFMF000100001", "CFMF000100002", "CFMF000100003", "CFMF000100004", "CFMF000100005", "CFMF000100006", "CFMF000100007", "CFMF000100008", "CFMF000100009", "CFMF000100010", "BPNF000100001", "BPNF000100002"," BPNF000100003", "BPNF000100004", "BPNF000100005", "BPNF000100006", "BPNF000100007", "BPNF000100008", "BPNF000100009", "BPNF000100010", "AB08000100001", "AB08000100002", "AB08000100003", "AB08000100004", "AB08000100005", "AB08000100006", "AB08000100007", "AB08000100008", "AB08000100009", "AB08000100010", "MH02000100016", "MH02000100134", "MH02000100247", "MH02000100367", "MH02000100452", "MH02000100525", "MH02000100135", "MH02000100136", "MH02000100137", "MH02000100138", "RS33000100001", "RS33000100002", "RS33000100003", "RS33000100004", "RS33000100005", "RS33000100006", "RS33000100007", "RS33000100008", "RS33000100009", "RS33000100010", "SUCR000100001", "SUCR000100002", "SUCR000100003", "SUCR000100004", "SUCR000100005", "SUCR000100006", "SUCR000100007", "SUCR000100008", "SUCR000100009", "SUCR000100010", "SN02000100001", "SN02000100002", "SN02000100003", "SN02000100004", "SN02000100005", "SN02000100006", "SN02000100007", "SN02000100008", "SN02000100009", "SN02000100010", "AB08000100007", "AB08000100008", "AB08000100009", "AB08000100010", "AB08000100011", "UCRS000100001", "UCRS000100002", "UCRS000100003", "UCRS000100004", "UCRS000100005", "UCRS000100006", "UCRS000100007", "UCRS000100008", "UCRS000100009", "UCRS000100010", "MH02000100016", "MH02000100134", "MH02000100247", "MH02000100367", "MH02000100452", "MH02000100525", "MH02000100135", "MH02000100136", "MH02000100137", "MH02000100138", "CH12000400121", "CH12000400120", "CH12000400119", "CH12000400118", "CH12000400117", "CH12000400116", "CH12000400115", "CH12000400114", "CH12000400113", "CH12000400112", "WS09001600045", "WS09001600044", "WS09001600043", "WS09001600042", "WS09001600041", "WS09001600040", "WS09001600039", "WS09001600038", "WS09001600037", "WS09001600036", 'RS17000100001', 'RS17000100002', 'RS17000100003', 'RS17000100004', 'RS17000100005', 'RS17000100006', 'RS17000100007', 'RS17000100008', 'RS17000100009', 'RS17000100010', 'RS17000100011', 'RS17000100012', 'RS17000100013', 'RS17000100014', 'RS17000100015', 'RS17000100016', 'RS17000100017', 'RS17000100018', 'RS17000100019', 'RS17000100020', 'RS17000100021', 'RS17000100022', 'RS17000100023', 'RS17000100024', 'RS17000100025', 'RS17000100026', 'RS17000100027', 'RS17000100028', 'RS17000100029', 'RS17000100030', 'RS17000100031', 'RS17000100032', 'RS17000100033', 'RS17000100034', 'RS17000100035', 'RS17000100036', 'RS17000100037', 'RS17000100038', 'RS17000100039', 'RS17000100040', 'RS17000100041', 'RS17000100042', 'RS17000100043', 'RS17000100044', 'RS17000100045', 'RS17000100046', 'RS17000100047', 'RS17000100048', 'RS17000100049', 'RS17000100050', 'RS17000100051', 'RS17000100052', 'RS17000100053', 'RS17000100054', 'RS17000100055', 'RS17000100056', 'RS17000100057', 'RS17000100058', 'RS17000100059', 'RS17000100060', 'RS17000100061', 'RS17000100062', 'RS17000100063', 'RS17000100064', 'RS17000100065', 'RS17000100066', 'RS17000100067', 'RS17000100068', 'RS17000100069', 'RS17000100070', 'RS17000100071', 'RS17000100072', 'RS17000100073', 'RS17000100074', 'RS17000100075', 'RS17000100076', 'RS17000100077', 'RS17000100078', 'RS17000100079', 'RS17000100080', 'RS17000100081', 'RS17000100082', 'RS17000100083', 'RS17000100084', 'RS17000100085', 'RS17000100086', 'RS17000100087', 'RS17000100088', 'RS17000100089', 'RS17000100090', 'RS17000100091', 'RS17000100092', 'RS17000100093', 'RS17000100094', 'RS17000100095', 'RS17000100096', 'RS17000100097', 'RS17000100098', 'RS17000100099', 'RS17000100100', 'RS17000100101', 'RS17000100102', 'RS17000100103', 'RS17000100104', 'RS17000100105', 'RS17000100106', 'RS17000100107', 'RS17000100108', 'RS17000100109', 'RS17000100110', 'RS17000100111', 'RS17000100112', 'RS17000100113', 'RS17000100114', 'RS17000100115', 'RS17000100116', 'RS17000100117', 'RS17000100118', 'RS17000100119', 'RS17000100120', 'RS17000100121', 'RS17000100122', 'RS17000100123', 'RS17000100124', 'RS17000100125', 'RS17000100126', 'RS17000100127', 'RS17000100128', 'RS17000100129', 'RS17000100130', 'RS17000100131', 'RS17000100132', 'RS17000100133', 'RS17000100134', 'RS17000100135', 'RS17000100136', 'RS17000100137', 'RS17000100138', 'RS17000100139', 'RS17000100140', 'RS17000100141', 'RS17000100142', 'RS17000100143', 'RS17000100144', 'RS17000100145', 'RS17000100146', 'RS17000100147', 'RS17000100148', 'RS17000100149', 'RS17000100150', 'RS17000100151', 'RS17000100152', 'RS17000100153', 'RS17000100154', 'RS17000100155', 'RS17000100156', 'RS17000100157', 'RS17000100158', 'RS17000100159', 'RS17000100160', 'SP06000100001', 'SP06000100002', 'SP06000100003', 'SP06000100004', 'SP06000100005', 'SP06000100006', 'SP06000100007', 'SP06000100008', 'SP06000100009', 'SP06000100010', 'SP06000100011', 'SP06000100012', 'SP06000100013', 'SP06000100014', 'SP06000100015', 'SP06000100016', 'SP06000100017', 'SP06000100018', 'SP06000100019', 'SP06000100020', 'SP06000100021', 'SP06000100022', 'SP06000100023', 'SP06000100024', 'SP06000100025', 'SP06000100026', 'SP06000100027', 'SP06000100028', 'SP06000100029', 'SP06000100030', 'SP06000100031', 'SP06000100032', 'SP06000100033', 'SP06000100034', 'SP06000100035', 'SP06000100036', 'SP06000100037', 'SP06000100038', 'SP06000100039', 'SP06000100040', 'SP06000100041', 'SP06000100042', 'SP06000100043', 'SP06000100044', 'SP06000100045', 'SP06000200001', 'SP06000200002', 'SP06000200003', 'SP06000200004', 'SP06000200005', 'SP06000200006', 'SP06000200007', 'SP06000200008', 'SP06000200009', 'SP06000200010', 'SP06000200011', 'SP06000200012', 'SP06000200013', 'SP06000200014', 'SP06000200015', 'SP06000200016', 'SP06000200017', 'SP06000200018', 'SP06000200019', 'SP06000200020', 'SP06000200021', 'SP06000200022', 'SP06000200023', 'SP06000200024', 'SP06000200025', 'SP06000200026', 'SP06000200027', 'SP06000200028', 'SP06000200029', 'SP06000200030', 'SP06000200031', 'SP06000200032', 'SP06000200033', 'SP06000200034', 'SP06000200035', 'SP06000200036', 'SP06000200037', 'SP06000200038', 'SP06000200039', 'SP06000200040', 'SP06000200041', 'SP06000200042', 'SP06000200043', 'SP06000200044', 'SP06000200045', 'SP06000200046', 'SP06000200047', 'SP06000200048', 'SP06000200049', 'SP06000200050', 'SP06000200051', 'SP06000200052', 'SP06000200053', 'SP06000200054', 'SP06000200055', 'SP06000200056', 'SP06000200057', 'SP06000200058', 'SP06000200059', 'SP06000200060', 'SP06000300001', 'SP06000300002', 'SP06000300003', 'SP06000300004', 'SP06000300005', 'SP06000300006', 'SP06000300007', 'SP06000300008', 'SP06000300009', 'SP06000300010', 'SP06000300011', 'SP06000300012', 'SP06000300013', 'SP06000300014', 'SP06000300015', 'SP06000300016', 'SP06000300017', 'SP06000300018', 'SP06000300019', 'SP06000300020', 'SP06000300021', 'SP06000300022', 'SP06000300023', 'SP06000300024', 'SP06000300025', 'SP06000300026', 'SP06000300027', 'SP06000300028', 'SP06000300029', 'SP06000300030', 'SP06000300031', 'SP06000300032', 'SP06000300033', 'SP06000300034', 'SP06000300035', 'SP06000300036', 'SP06000300037', 'SP06000300038', 'SP06000300039', 'SP06000300040', 'SP06000300041', 'SP06000300042', 'SP06000300043', 'SP06000300044', 'SP06000300045', 'SP06000300046', 'SP06000300047', 'SP06000300048', 'SP06000300049', 'SP06000300050', 'SP06000300051', 'SP06000300052', 'SP06000300053', 'SP06000300054', 'SP06000300055', 'SP06000300056', 'SP06000300057', 'SP06000300058', 'SP06000300059', 'SP06000300060', 'SP06000300061', 'SP06000300062', 'SP06000300063', 'SP06000300064', 'SP06000300065', 'SP06000300066', 'SP06000300067', 'SP06000300068', 'SP06000300069', 'SP06000300070', 'SP06000300071', 'SP06000300072', 'SP06000300073', 'SP06000300074', 'SP06000300075', 'SP06000300076', 'SP06000300077', 'SP06000300078', 'SP06000300079', 'SP06000300080', 'SP06000400001', 'SP06000400002', 'SP06000400003', 'SP06000400004', 'SP06000400005', 'SP06000400006', 'SP06000400007', 'SP06000400008', 'SP06000400009', 'SP06000400010', 'SP06000400011', 'SP06000400012', 'SP06000400013', 'SP06000400014', 'SP06000400015', 'SP06000400016', 'SP06000400017', 'SP06000400018', 'SP06000400019', 'SP06000400020', 'SP06000400021', 'SP06000400022', 'SP06000400023', 'SP06000400024', 'SP06000400025', 'SP06000400026', 'SP06000400027', 'SP06000400028', 'SP06000400029', 'SP06000400030', 'SP06000400031', 'SP06000400032', 'SP06000400033', 'SP06000400034', 'SP06000400035', 'SP06000400036', 'SP06000400037', 'SP06000400038', 'SP06000400039', 'SP06000400040', 'SP06000400041', 'SP06000400042']

    # a shorter query of trees by stand to work with:
    sample_trees = ["HGBK061000002", "HGBK061000003", 'SP06000400035', 'SP06000400036', 'SP06000400037']

    # create output with the first tree, to initiate the csv file.
    First_Tree = Tree(cur, pcur, queries, sample_trees[0])
    Bios = First_Tree.compute_biomasses()
    Checks = First_Tree.check_trees()

    First_Tree.output_tree_agg(Bios, Checks, datafile = "10232015_bio.csv", checkfile="10232015_checks.csv", mode = 'wt')

    # clear out the global variables by setting to empty arrays
    Bios = {}
    Checks = {}

    for each_tree in sample_trees[1:]:
        A = Tree(cur, pcur, queries, each_tree)
        Bios = A.compute_biomasses()
        Checks = A.check_trees()

        A.output_tree_agg(Bios, Checks, datafile= "10232015_bio.csv", checkfile="10232015_checks.csv", mode = 'a')

        # special cases:

        # WE NEED TO ACCOUNT FOR IF plot id is 11 and stand is CH11 it should be 01. We need to account for trees on FRD2/FRD1
        Bios = {}
        Checks = {}
    