#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import csv
import biomass_basis

"""
tps_Tree.py contains the class Tree, which describes an individual tree (not on a per hectare basis!)

In the __main__ section of this function, a few examples of how to call this script are presented. Note that the objects created by poptree_basis and biomass_basis are global, and do not need to be created with every single tree. 

* DATABASE_CONNECTION is a global connection object.
* XFACTOR is a global reference object for the "unusual plots".

Form:
* The word 'dbh' in TPS is always lowercase.
* Inputs can be in uppercase or lowercase, but in general lowercase is preferred, and functions process lowercase, with all right-spacing stripped.
"""

class Tree( object ):
    """ A Tree object contains the required metrics and functions to compute Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg/Ha ), Volume ( m\ :sup:`3` ) , and Basal Area ( m\ :sup:`2` ) for any one tree. Tree objects also create a check file for data quality. 

    Tree objects are independent of the years; that is, each Tree object contains all the years of that tree's existance.

    :Example:
    >>> import tps
    >>> import poptree_basis
    >>> import biomass_basis
    >>> A = Tree(cur, 'NCNA001800216')
    >>> A.tid = 'ncna001800216'
    >>> A.cur = <pymssql.cursor>
    >>> A.tree_query= "SELECT <columns> from ..."
    >>> A.eqn_query = "SELECT <columns> from ..."
    >>> A.species = "TSHE"
    >>> A.state = [[1942, 16.0, '1', 'G'], [1945, 17.9, '1','G']]
    >>> A.eqns = {'normal' : lambda x :<function 039459x342>}
    >>> A.woodden = 0.44

    .. note: Tree.state contains [year, dbh, status, dbh_code]. Although status is an integer, it is recorded as a string here because it is descriptive. '1' is OK, '2' is Ingrowth, '3' is merged or fused, '6' is dead, and '9' is missing. See : `Tree Status Codes <http://andrewsforest.oregonstate.edu/data/domains.cfm?domain=enum&dbcode=Tp001&attid=7291&topnav=8/>`_ . DBH Codes are also all displayed as strings, although some are integers. Description here : `Tree DBH Codes <http://andrewsforest.oregonstate.edu/data/domains.cfm?domain=enum&dbcode=Tp001&attid=7287&topnav=8/>`_

    .. warning: A.cur must be created in an external variable

    **METHODS**

    """

    def __init__(self, cur, pcur, queries, tid):

        self.tid = str(tid).strip().lower()
        self.cur = cur
        self.pcur = pcur
        self.tree_query = queries['tree']['sql_1tree']
        self.eqn_query = queries['tree']['sql_1tree_eqn']
        self.species = ""
        self.state =[]
        self.eqns = {}
        self.woodden = 0.0
        self.filename_data = ""
        self.filename_checks = ""
        self.filename_data_2 = ""

        self.get_a_tree()

    def get_a_tree(self):
        """ Retrieves a single tree and assign its species, standid, and plot; create a list of lists describing that tree for each remeasurement in its life. Gathers the equations the tree needs to have its biomass computed. 

        **PROPERTIES**
        :Tree.state: a list of lists containing the year, dbh, dbh_code, and status_code
        :Tree.eqns: a dictionary of eqns keyed by 'normal', 'big', or 'component' containing lambda functions to receive dbh inputs and compute Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), and wood density.
        """
        sql = self.tree_query.format(tid=self.tid)

        self.cur.execute(sql)

        for index,row in enumerate(self.cur):
            if index == 0:
                self.species = str(row[1]).strip().lower()
                self.standid = str(row[2]).strip().lower()
                self.plotid = str(row[3]).strip().lower()
            else:
                pass

            # append to state to ( year, dbh, status, dbh_code )
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
            form = str(row[2]).strip().lower()
            try:
                woodden = round(float(str(row[11])),3)
            except:
                woodden = None

            self.woodden = woodden
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

            # for the computation of ACCI, exclusively...
            if form != 'as_compbio':
                this_eqn = lambda x : biomass_basis.which_fx(form)(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                self.eqns.update({str(row[1]):this_eqn})

            elif form == 'as_compbio':
                this_eqn = lambda x: biomass_basis.which_fx('as_biopak')(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                self.eqns.update({str(row[12].rstrip().lower()):this_eqn})

    def compute_biomasses(self):
        """ Compute biomass, volume, Jenkins' biomass and wood density from equations

        If a tree is in it's death year, the dbh from the previous measurement is used.

        :Example:
        >>> A = Tree(cur, pcur, queries, 'NCNA000100014')
        >>> A.state
        >>> [[1979, 47.5, '1', 'G'], [1981, None, '6', 'M']]
        >>> A.compute_biomasses()
        >>> [(1.2639, 2.8725, 1.14323, 0.44), (1.2639, 2.8725, 1.14323, 0.44), [0.002, 0.002]]

        .. note: Biomass and Jenkins' biomass are in Mg.
        """

        # set these lists to empty at the top of the function so that even in the worst case, all that will be returned is empty lists
        list_of_biomasses = []
        list_of_basal = []

        try:
            list_of_biomasses = [self.eqns[biomass_basis.maxref(x, self.species)](x) for (_,x,_,_) in self.state]
            list_of_basal = [round(0.00007854*float(x),3) for (_,x,_,_) in self.state]
            
            return list_of_biomasses, list_of_basal
        
        except Exception as e6:
            
            if self.species == "acci":
                list_of_biomasses = [biomass_basis.as_compbio(x, self.eqns) for (_,x,_,_) in self.state]
                list_of_basal = [round(0.00007854*float(x),3) for (_,x,_,_) in self.state]
                
                return list_of_biomasses, list_of_basal
            
            else:
                try:
                    list_of_biomasses = [self.eqns['normal'](x) for (_,x,_,_) in self.state]
                    list_of_basal = [round(0.00007854*float(x),3) for (_,x,_,_) in self.state]
                    
                    return list_of_biomasses, list_of_basal
                
                except Exception as e2:
                    
                    # if the final dbh is missing and the tree is dead or missing, take the final year from that missing value and give it the biomass, volume, and jenkins of the prior value
                    if self.state[-1][1:3] == [None,'6'] or self.state[-1][1:3] == [None,'9']:
                        
                        final_year = self.state[-1][0]
                        
                        list_of_biomasses = [self.eqns[biomass_basis.maxref(x, self.species)](x) for (_,x,_,_) in self.state[:-1]]

                        list_of_basal = [round(0.00007854*float(x),3) for (_,x,_,_) in self.state[:-1]]
                        
                        final_biomasses = list_of_biomasses[-1]
                        final_basal = list_of_basal[-1]
                        list_of_biomasses.append(final_biomasses)
                        list_of_basal.append(final_basal)

                        return list_of_biomasses, list_of_basal
                    
                    else:
                        # new errors to debug
                        print("error in tps_Tree.py with dealing with biomasses where DBH is None?")
                        return list_of_biomasses, list_of_basal

    def is_detail(self, XFACTOR):
        """ Returns the Capture.expansion object as a dictionary specific for this tree.  

        If the plot is a detail plot and the tree has a dbh which is less than 15 but greater than the minimum dbh listed, then a factor other than 1.0 will be returned.

        :XFACTOR: is an instance of the Capture object, used for reference here.
        :standid: the stand of a tree object
        :plot: the plotid attribute of a tree object
        :dbh: the dbh attribute of a tree object
        :year: the year attribute of a tree object
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
        """ Returns the Capture.uplot_areas object as a dictionary specific for this tree.  

        If the plot is listed in the unique areas reference, that reference will be returned for the year, otherwise, the default 625 is returned

        :XFACTOR: is an instance of the Capture object, used for reference here.
        :standid: the stand of a tree object
        :plot: the plotid attribute of a tree object
        :dbh: the dbh attribute of a tree object
        :year: the year attribute of a tree object
        """
        area_dict = {year:625. for (year,dbh,_,_) in self.state if dbh != None}

        if self.standid not in XFACTOR.uplot_areas.keys():
            return area_dict

        else:

            integer_plot = int(self.plotid[4:])
            yearlist = [year for (year,dbh,_,_) in self.state if dbh != None]
            for each_year in yearlist:
                try:
                    area = XFACTOR.uplot_areas[self.standid][each_year][integer_plot]
                    area_dict.update({year:area})
                except Exception:
                    # if that year doesn't have a weird area, pass over it, since the area will default to 625 m
                    pass

                return area_dict

    def check_trees(self):
        """ Performance checks on tree 'state'

        * A tree should not have more than one death
        * A tree should not die and then re-appear
        * A tree should not go missing and then re-appear
        * A tree should not grow more than 10 percent per year between re-measurements unless it is smaller than 8.0 cm on the first of those measurements (because scaling)
        * A tree should not decrease in size by more than 10 percent per year between re-measurements
        * this method shouldn't be called in the case where there is only one state

        :intervals: are the string representation of the intervals between two measurements
        :tc: a dictionary of 'tree checks', referenced by the string containing the interval between two measurements
        """

        if len(self.state) <=1:
            return False
        
        else:

            intervals = [str(one) +"-" + str(two) for (one,two) in zip([year for (year,_,_,_) in self.state[:-1]],[year for (year,_,_,_) in self.state[1:]])]
            statuses = [str(one) +"," + str(two) for (one,two) in zip([status for (_,_,status,_) in self.state[:-1]],[status for (_,_,status,_) in self.state[1:]])]
            dbh_degrade = [str(one) +"," + str(two) for (one,two) in zip([status for (_,_,_,status) in self.state[:-1]],[status for (_,_,_,status) in self.state[1:]])]
            
            # the change in dbh between two intervals, measured in change in dbh/year
            try:
                percent_change_dbh_forward = [round((two[1] - one[1])/(two[0]-one[0]),2)*100 for (one,two) in zip([(year,dbh) for (year,dbh,_,_) in self.state[:-1]],[(year,dbh) for (year,dbh,_,_) in self.state[1:]])]
            
            except Exception as e7:
                
                # when the last DBH is None we need to reset it to the second to last dbh, but keep the correct year
                all_dbh_except_end = [(year,dbh) for (year,dbh,_,_) in self.state[1:-1]]
                penultimate_dbh = (self.state[-1][0],self.state[-2][1])
                all_dbh_except_end.append(penultimate_dbh)
                
                percent_change_dbh_forward = [round((two[1] - one[1])/(two[0]-one[0]),2)*100 for (one,two) in zip([(year,dbh) for (year,dbh,_,_) in self.state[:-1]], all_dbh_except_end)]

            tc = {x:{'deathx':"None", 'lazarus': "None", 'houdini':"None", 'growthx':"None", 'shrinkx':"None", 'degradex':"None"} for x in intervals}

            indices_double_dead = [intervals[index] for index,value in enumerate(statuses) if value =="6,6"]
            indices_lazarus = [intervals[index] for index,value in enumerate(statuses) if value in ["6,1","6,2","6,3"]]
            indices_houdini = [intervals[index] for index,value in enumerate(statuses) if value in ["9,1","9,2","9,3"]]
            indices_growthx = [(intervals[index],value) for index,value in enumerate(percent_change_dbh_forward) if value >= 10.0]
            indices_shrinkx = [(intervals[index],value) for index,value in enumerate(percent_change_dbh_forward) if value <=-10.0]
            indices_degrade = [intervals[index] for index,value in enumerate(dbh_degrade) if value in ["G,M","G,U","V,M","V,U"]]
            

            {tc[x].update({'deathx':True}) for x in indices_double_dead}
            {tc[x].update({'lazarus':True}) for x in indices_lazarus}
            {tc[x].update({'houdini':True}) for x in indices_houdini}
            {tc[x].update({'growthx': round(value, 2)}) for (x,value) in indices_growthx}
            {tc[x].update({'shrinkx': round(value, 2)}) for (x,value) in indices_shrinkx}
            {tc[x].update({'degradex': True}) for x in indices_degrade}
            
            print(tc)
            return tc

    def output_tree(self, Bios, Details, Checks, Areas, *args, mode='wt'):
        """ Writes 3 csv files, one containing the tree measurements for the individual trees, the second containing the checks about status, and the last containing a "per hectare" version. If filenames are given as arguements, these can be used, otherwise, default filenames will be assigned.


        :Bios: computed biomasses, Jenkins' biomasses, basal areas, volumes etc. from :compute_biomass():
        :Details: expansion factors if the plot is a detail plot or not 
        :Checks: reference dictionary from :check_trees():
        :args: the names of csv files for output. The first arguement will be for the data, the second will be for the checks, the third will be for the per hectare version.
        """
        

        # Writes the single tree output, not on a per hectare basis
        if args and args[0] != None:
            self.filename_data = args[0]
        else:
            self.filename_data = 'basic_tree_output.csv'

        with open(self.filename_data, mode) as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)

            # if the file is in append mode, do not write headers
            if mode != 'a':
                headers = ['DBCODE', 'ENTITY', 'TREEID', 'YEAR', 'DBH', 'TREE_STATUS', 'DBH_CODE','BIOMASS', 'JENKINS', 'VOLUME', 'BASAL_AREA_M2','WOODDENSITY','EXPANSION_FACTOR']
                writer.writerow(headers)
                headers2 = ['', '', '', 'CM', '', '', 'MG','MG','M3','M2','','']
                writer.writerow(headers2)
            else:
                pass

            for index, each_state in enumerate(self.state):

                new_row = [self.tid.upper(), each_state[0], each_state[1], each_state[2], each_state[3], Bios[0][index][0], Bios[0][index][2], Bios[0][index][1], Bios[1][index], Bios[0][index][3], Details[each_state[0]]]

                writer.writerow(new_row)


        # Writes the single tree output, on a per hectare basis
        if args and args[2] != None:
            self.filename_data_2 = args[2]
        else:
            self.filename_data_2 = 'perhectare_tree_output.csv'

        with open(self.filename_data_2, mode) as writefile3:
            writer3 = csv.writer(writefile3, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)
            
            # if the file is in append mode, do not write headers
            if mode != 'a':
                headers = ['DBCODE', 'ENTITY', 'TREEID', 'YEAR', 'DBH', 'TREE_STATUS', 'DBH_CODE','BIOMASS', 'JENKINS', 'VOLUME', 'BASAL_AREA_M2','WOODDENSITY','EXPANSION_FACTOR']
                writer3.writerow(headers)
                headers2 = ['', '', '', 'CM', '', '', 'MG/HA','MG/HA','M3/HA','M2/HA','','']
                writer3.writerow(headers2)
            else:
                pass

            for index, each_state in enumerate(self.state):

                try:
                    # the (biomass * the expansion factor)/ (the plot area in m2) * 10000 m2/ha
                    new_row = [self.tid.upper(), each_state[0], each_state[1], each_state[2], each_state[3], round(((Bios[0][index][0]*Details[each_state[0]])/Areas[each_state[0]])*10000, 3), round(((Bios[0][index][2]*Details[each_state[0]])/Areas[each_state[0]])*10000, 3), round(((Bios[0][index][1]*Details[each_state[0]])/Areas[each_state[0]])*10000, 3), round(((Bios[1][index]*Details[each_state[0]])/Areas[each_state[0]])*10000, 3), Bios[0][index][3], Details[each_state[0]]]
                    writer3.writerow(new_row)

                except KeyError:
                    if self.state[-1][1] == None and each_state == self.state[-1]:
                        new_row = [self.tid.upper(), self.state[-2][0], each_state[1], each_state[2], each_state[3], round(((Bios[0][index][0]*Details[self.state[-2][0]])/Areas[self.state[-2][0]])*10000, 3), round(((Bios[0][index][2]*Details[self.state[-2][0]])/Areas[self.state[-2][0]])*10000, 3), round(((Bios[0][index][1]*Details[self.state[-2][0]])/Areas[self.state[-2][0]])*10000, 3), round(((Bios[1][index]*Details[each_state[0]])/Areas[self.state[-2][0]])*10000, 3), Bios[0][index][3], Details[self.state[-2][0]]]
                        writer3.writerow(new_row)

                    else:
                        import pdb; pdb.set_trace()
                

        # writes the checks output, if it can be written, otherwise, returns a file containing only "NA" because the checks are Not Applicable. This would happen if there was only one remeasurement
        if Checks != False:
            if args and args[1] != None:
                self.filename_checks = args[1]
            else:
                self.filename_checks = 'check_tree_output.csv'

            with open(self.filename_checks, mode) as writefile2:
                writer2 = csv.writer(writefile2, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)
                
                # if the file is in append mode, do not write headers
                if mode != 'a':    
                    headers = ['TREEID','INTERVAL','SHRINK_X_FLAGGED','GROWTH_X_FLAGGED','DOUBLE_DEATH_FLAG','LAZARUS_FLAG','HOUDINI_FLAG','DEGRADE_FLAG']
                    writer2.writerow(headers)
                else:
                    pass

                for each_interval in sorted(Checks.keys()):
                    new_row = [self.tid.upper(), each_interval, Checks[each_interval]['shrinkx'], Checks[each_interval]['growthx'], Checks[each_interval]['deathx'], Checks[each_interval]['lazarus'], Checks[each_interval]['houdini'], Checks[each_interval]['degradex']]

                    writer2.writerow(new_row)

            print("finished printing csvs for data and checks!")
        
        else:
            # when only one measurement has been taken
            new_row = [self.tid.upper(), "NA", "NA", "NA", "NA", "NA", "NA", "NA"]
            writer2.writerow(new_row)
            
            print("only one re-measurement, checks could not be performed")


if __name__ == "__main__":

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    pconn, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries

    # creates lookups for expansion factors
    XFACTOR = poptree_basis.Capture()
    
    # creates the Biomasses/Basal Areas and the Detail plot expansions
    # A = Tree(cur, pcur, queries, 'TO11000200005')
    # A = Tree(cur, pcur, queries, 'CFMF000100027')
    
    # Bios = A.compute_biomasses()
    # Details = A.is_detail(XFACTOR)
    # Checks = A.check_trees()
    # Areas = A.is_unusual_area(XFACTOR)
    
    # A.output_tree(Bios, Details, Checks, Areas, mode='a')
    # print("end!")


    # a list of test trees to work through:
    sample_trees = ["OL03000100013", "OL03000100013", "OL03000100013", "OL03000100013", "OL03000100014", "OL03000100014", "OL03000100014", "OL03000100014", "OL03000100014", "OL03000100014", "CH42000100004", "CH42000100004", "CH42000100004", "CH42000100005","CH42000100005", "CH42000100005", "CH42000100005", "CH42000100005", "CH42000100138", "CH42000100138", "WS02010200001", "WS02010200002", "WS02010200003", "WS02010200004", "WS02010200005", "WS02010200007", "WS02010200006", "WS02010200008", "WS02010200009", "WS02010200010", "CFMF000100027"]

    # create output with the first tree:
    First_Tree = Tree(cur, pcur, queries, sample_trees[0])
    Bios = First_Tree.compute_biomasses()
    Details = First_Tree.is_detail(XFACTOR)
    Checks = First_Tree.check_trees()
    Areas = First_Tree.is_unusual_area(XFACTOR)
    First_Tree.output_tree(Bios, Details, Checks, Areas, mode='wt')
    print("have completed a tree")

    # clear out the global variables by setting to empty arrays
    Bios = {}
    Details = {}
    Checks = {}
    Areas = {}

    for each_tree in sample_trees[1:]:
        A = Tree(cur, pcur, queries, each_tree)
        Bios = A.compute_biomasses()
        Details = A.is_detail(XFACTOR)
        Checks = A.check_trees()
        Areas = A.is_unusual_area(XFACTOR)
        A.output_tree(Bios, Details, Checks, Areas, mode='a')

        Bios = {}
        Details = {}
        Checks = {}
        Areas = {}