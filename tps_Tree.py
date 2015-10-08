#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import csv
import biomass_basis


class Tree(object):
    """ A Tree object contains the required metrics and functions to compute Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg/Ha ), Volume ( m\ :sup:`3` ) , and Basal Area ( m\ :sup:`2` ) for any one tree. Tree objects also create a check file for data quality. 

    Tree objects are independent of the years; that is, each Tree object contains all the years of that tree's existance.

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
    >>> A.state = [[1942, 16.0, '1', 'G'], [1945, 17.9, '1','G']]
    >>> A.eqns = {'normal' : lambda x :<function 039459x342>}
    >>> A.woodden = 0.44

    .. note: Tree.state contains [year, dbh, status, dbh_code]. Although status is an integer, it is recorded as a string here because it is descriptive. '1' is OK, '2' is Ingrowth, '3' is merged or fused, '6' is dead, and '9' is missing. See : `Tree Status Codes <http://andrewsforest.oregonstate.edu/data/domains.cfm?domain=enum&dbcode=Tp001&attid=7291&topnav=8/>`_ . DBH Codes are also all displayed as strings, although some are integers. Description here : `Tree DBH Codes <http://andrewsforest.oregonstate.edu/data/domains.cfm?domain=enum&dbcode=Tp001&attid=7287&topnav=8/>`_

    .. warning: A.cur must be created in an external variable

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
        self.woodden = 0.0
        self.filename_data = ""
        self.filename_checks = ""
        self.filename_data_2 = ""

        self.get_a_tree()

    def get_a_tree(self):
        """ Retrieves a single tree and assign its species, standid, and plot; create a list of lists describing that tree for each remeasurement in its life. Gathers the equations the tree needs to have its biomass computed. 

        **INTERNAL VARIABLES**
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
                self.studyid = str(row[8]).strip().upper()
                self.standid = str(row[9]).strip().upper()
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
                self.eqns.update({str(row[1]).rstrip().lower():this_eqn})

                #print(biomass_basis.which_fx(form))

            elif form == 'as_compbio':
                this_eqn = lambda x: biomass_basis.which_fx('as_biopak')(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                self.eqns.update({str(row[12].rstrip().lower()):this_eqn})

    def compute_biomasses(self):
        """ Compute biomass, volume, Jenkins' biomass and wood density from equations

        If a tree is in it's death year, the dbh from the previous measurement is used.

        .. Example:

        >>> A = Tree(cur, pcur, queries, 'NCNA000100014')
        >>> A.state
        >>> [[1979, 47.5, '1', 'G'], [1981, None, '6', 'M']]
        >>> A.compute_biomasses()
        >>> [(1.2639, 2.8725, 1.14323, 0.44), (1.2639, 2.8725, 1.14323, 0.44), [0.002, 0.002]]

        .. note: Biomass and Jenkins' biomass are in Mg.
        
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
                list_of_biomasses = [biomass_basis.as_compbio(x, self.eqns) for (_,x,_,_) in self.state]
                list_of_basal = [round(0.00007854*float(x)*float(x),6) for (_,x,_,_) in self.state]
                
                return list_of_biomasses, list_of_basal
            
            else:
                try:
                    list_of_biomasses = [self.eqns['normal'](x) for (_,x,_,_) in self.state]
                    list_of_basal = [round(0.00007854*float(x)*float(x),6) for (_,x,_,_) in self.state]
                    
                    return list_of_biomasses, list_of_basal
                
                except Exception:
                    
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

    def is_detail(self, XFACTOR):
        """ Returns the Capture.expansion object as a dictionary specific for this tree.  

        If the plot is a detail plot and the tree has a dbh which is less than 15 but greater than the minimum dbh listed, then a factor other than 1.0 will be returned.

        
        **INTERNAL VARIABLES**

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
        """ Performance checks on tree 'state'

        **Rules**

        * A tree should not have more than one death 
        * A tree should not die and then re-appear
        * A tree should not go missing and then re-appear
        * A tree should not grow more than 10 percent per year between re-measurements unless it is smaller than 8.0 cm on the first of those measurements (because scaling)
        * A tree should not decrease in size by more than 10 percent per year between re-measurements
        * this method shouldn't be called in the case where there is only one state

        **INTERNAL VARIABLES**

        :intervals: are the string representation of the intervals between two measurements
        :statuses: strings containing pairs of statuses that follow one another in time
        :dbh_degrade: strings containing pairs of dbh_codes that follow one another in time

        **RETURNED VARIABLES**
        :tc: a dictionary of 'tree checks', referenced by the string containing the interval between two measurements
            
        * Houdini trees: "9" then something not "9"
        * Lazarus trees: "6" then something not "9"
        * Double-death: more than 1 "6"
        * Degrade: changes from dbh code of "G" (good) or "V" (verified) to "M" (missing) or "U" (unmeasured)
        * ShrinkX : mean percentage shrink per year if mean percentage shrink > 10 %
        * GrowthX : mean percentage growth per year if mean percentage growth > 10 %

        .. note : if a tree does not fail the checks, it gets a "none" returned.

        .. note : the output of the checks are the the "Checks" file, which can be renamed.
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
            
            except Exception:
                
                # when the last DBH is None we need to reset it to the second to last dbh, but keep the correct year
                all_dbh_except_end = [(year,dbh) for (year,dbh,_,_) in self.state[1:-1]]
                penultimate_dbh = (self.state[-1][0],self.state[-2][1])
                all_dbh_except_end.append(penultimate_dbh)
                
                percent_change_dbh_forward = [round(((two[1] - one[1])/(two[0]-one[0]))/one[1], 2)*100 for (one,two) in zip([(year,dbh) for (year,dbh,_,_) in self.state[:-1]], all_dbh_except_end)]

            tc = {x:{'deathx':"None", 'lazarus': "None", 'houdini':"None", 'growthx':"None", 'shrinkx':"None", 'degradex':"None"} for x in intervals}

            indices_double_dead = [intervals[index] for index,value in enumerate(statuses) if value =="6,6"]
            indices_lazarus = [intervals[index] for index,value in enumerate(statuses) if value in ["6,1","6,2","6,3"]]
            indices_houdini = [intervals[index] for index,value in enumerate(statuses) if value in ["9,1","9,2","9,3"]]
            indices_growthx = [(intervals[index],value) for index,value in enumerate(percent_change_dbh_forward) if value >= 30.0]
            indices_shrinkx = [(intervals[index],value) for index,value in enumerate(percent_change_dbh_forward) if value <=-30.0]
            indices_degrade = [intervals[index] for index,value in enumerate(dbh_degrade) if value in ["G,M","G,U","V,M","V,U"]]
            

            {tc[x].update({'deathx':True}) for x in indices_double_dead}
            {tc[x].update({'lazarus':True}) for x in indices_lazarus}
            {tc[x].update({'houdini':True}) for x in indices_houdini}
            {tc[x].update({'growthx': round(value, 2)}) for (x,value) in indices_growthx}
            {tc[x].update({'shrinkx': round(value, 2)}) for (x,value) in indices_shrinkx}
            {tc[x].update({'degradex': True}) for x in indices_degrade}
            
            return tc

    def output_tree(self, Bios, Details, Checks, Areas, file0 = 'basic_tree_output.csv', file1 = 'check_tree_output.csv', file2 = 'perhectare_tree_output.csv', mode = 'wt'):
        """ Writes 3 csv files, one containing the tree measurements for the individual trees, the second containing the checks about status, and the last containing a "per hectare" version. If filenames are given as arguements, these can be used, otherwise, default filenames will be assigned.

        :Bios: computed biomasses, Jenkins' biomasses, basal areas, volumes etc. from :compute_biomass():
        :Details: expansion factors for the specific tree in question - includes whether or not a detail plot as well as the DBH of the tree
        :Checks: reference dictionary from :check_trees():
        :Areas: reference dictionary from :is_unusual_area():
        :args: the names of csv files for output. The first arguement will be for the data, the second will be for the checks, the third will be for the per hectare version. If no files are specified, default file names of `basic_tree_output.csv`, `check_tree_output.csv`, and `perhectare_tree_output.csv` will be used
        """
        
        # Writes the single tree output, not on a per hectare basis
        self.filename_data = file0
        
        with open(self.filename_data, mode) as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)

            # if the file is in append mode, do not write headers
            if mode != 'a':

                headers = ['DBCODE', 'ENTITY', 'STUDYID', 'STANDID', 'TREEID', 'SPECIES', 'PROXY_USED', 'WOOD_DENSITY_G_CM3', 'YEAR', 'DBH_CM', 'TREE_STATUS', 'DBH_CODE', 'BASAL_AREA_M2', 'VOLUME_M3', 'BIOMASS_MG', 'JENKINS_MG', 'EXPANSION_FACTOR_HA']
                writer.writerow(headers)
            else:
                pass

            for index, each_state in enumerate(self.state):

                # expansion factor revised is m2 that are in a hectare divsided by the m2 which are in that plot
                expansion_factor_revised = 10000./Areas[each_state[0]]


                new_row = ['TP001', '12', self.studyid, self.standid.upper(), self.tid.upper(), self.species.upper(), self.proxy.upper(), self.woodden, each_state[0], each_state[1], each_state[2], each_state[3], round(Bios[1][index],6), round(Bios[0][index][1],4), round(Bios[0][index][0],4), round(Bios[0][index][2],4), round(expansion_factor_revised,4)]

                writer.writerow(new_row)


        # Writes the single tree output, on a per hectare basis
        self.filename_data_2 = file2

        with open(self.filename_data_2, mode) as writefile3:
            writer3 = csv.writer(writefile3, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)
            
            # if the file is in append mode, do not write headers
            if mode != 'a':
                headers = ['DBCODE', 'ENTITY', 'STUDYID', 'STANDID', 'TREEID', 'SPECIES', 'PROXY_USED', 'WOOD_DENSITY_G_CM3', 'YEAR', 'DBH_CM', 'TREE_STATUS', 'DBH_CODE', 'BASAL_AREA_M2_HA', 'VOLUME_M3_HA', 'BIOMASS_MG_HA', 'JENKINS_MG_HA']
                writer3.writerow(headers)
                
            else:
                pass


            for index, each_state in enumerate(self.state):

                try:
                    new_row = ['TP001', '13', self.studyid, self.standid.upper(), self.tid.upper(), self.species.upper(), self.proxy.upper(), self.woodden, each_state[0], each_state[1], each_state[2], each_state[3], round((Bios[1][index]/Areas[each_state[0]])*10000,6), round((Bios[0][index][1]/Areas[each_state[0]])*10000,4), round((Bios[0][index][0]/Areas[each_state[0]])*10000,4), round((Bios[0][index][2]/Areas[each_state[0]])*10000,4)]
                    
                    writer3.writerow(new_row)

                except KeyError:
                    if self.state[-1][1] == None and each_state == self.state[-1]:
                        self.state[-1][1] = self.state[-2][1]
                        new_row = ['TP001', '13', self.studyid, self.standid.upper(), self.tid.upper(), self.species.upper(), self.proxy.upper(), self.woodden, each_state[0], each_state[1], each_state[2], each_state[3], round((Bios[1][index]/Areas[each_state[0]])*10000,6), round((Bios[0][index][1]/Areas[each_state[0]])*10000,4), round((Bios[0][index][0]/Areas[each_state[0]])*10000,4), round((Bios[0][index][2]/Areas[each_state[0]])*10000,4)]
                        writer3.writerow(new_row)

                    else:
                        import pdb; pdb.set_trace()
                

        # writes the checks output, if it can be written, otherwise, returns a file containing only "NA" because the checks are Not Applicable. This would happen if there was only one remeasurement
        if Checks != False:
            self.filename_checks = file1

            with open(self.filename_checks, mode) as writefile2:
                writer2 = csv.writer(writefile2, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)
                
                # if the file is in append mode, do not write headers
                if mode != 'a':    
                    headers = ['TREEID', 'SPECIES', 'INTERVAL','SHRINK_X_FLAGGED','GROWTH_X_FLAGGED','DOUBLE_DEATH_FLAG','LAZARUS_FLAG','HOUDINI_FLAG','DEGRADE_FLAG']
                    writer2.writerow(headers)
                else:
                    pass

                for each_interval in sorted(Checks.keys()):
                    new_row = [self.tid.upper(), self.species.upper(), each_interval, Checks[each_interval]['shrinkx'], Checks[each_interval]['growthx'], Checks[each_interval]['deathx'], Checks[each_interval]['lazarus'], Checks[each_interval]['houdini'], Checks[each_interval]['degradex']]

                    writer2.writerow(new_row)
        
        else:

            self.filename_checks = file1

            with open(self.filename_checks, mode) as writefile2:
                writer2 = csv.writer(writefile2, delimiter = ",", quoting = csv.QUOTE_NONNUMERIC)
                # when only one measurement has been taken
                new_row = [self.tid.upper(), "NA", "NA", "NA", "NA", "NA", "NA", "NA"]
                writer2.writerow(new_row)


if __name__ == "__main__":

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    pconn, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries

    #import pdb; pdb.set_trace()

    # creates lookups for expansion factors
    XFACTOR = poptree_basis.Capture()
    
    # creates the Biomasses/Basal Areas and the Detail plot expansions
    # A = Tree(cur, pcur, queries, 'TO11000200005')
    # A = Tree(cur, pcur, queries, 'CH09000100002')
    
    # Bios = A.compute_biomasses()
    # Details = A.is_detail(XFACTOR)
    # Checks = A.check_trees()
    # Areas = A.is_unusual_area(XFACTOR)
    
    # A.output_tree(Bios, Details, Checks, Areas, mode='wt')
    # print("end!")

    # # a list of test trees to work through:
    sample_trees = ["OL03000100013", "OL03000100014", "CH42000100004", "CH42000100004","CH42000100005", "CH42000100138", "WS02010200001", "WS02010200002", "WS02010200003", "WS02010200004", "WS02010200005", "WS02010200007", "WS02010200006", "WS02010200008", "WS02010200009", "WS02010200010", "CFMF000100027", "FRA3000100001", "FRA3000100002", "FRA3000100003", "FRA3000100004", "FRA3000100005", "FRA3000100006", "FRA3000100007", "FRA3000100008", "FRA3000100009", "FRA3000100010", "FRA3000100011", "FRA3000100012", "FRA3000100013", "FRA3000100014", "FRA3000100015", "FRA3000100016", "FRA3000100017", "FRA3000100018", "FRA3000100019", "AX15000100001", "AX15000100002", "AX15000100003", "AX15000100004", "AX15000100005", "AX15000100006", "AX15000100007", "AX15000100008", "AX15000100009", "AX15000100010", "PIJE000100001", "PIJE000100002", "PIJE000100003", "PIJE000100004", "PIJE000100005", "PIJE000100006", "PIJE000100007", "PIJE000100008", "PIJE000100009", "PIJE000100010", "FRA3000100020", "NCNA000100014", "NCNA003100232", "NCNA002800010", "NCNA001800216", "NCNA002100017", "NCNA001800137", "NCNA001200063", "NCNA000400081", "NCNA000900065", "NCNA000400100", "NCNA004000089", "NCNA004400132", "NCNA004400056", "NCNA003700002", "NCNA003900028", "NCNA004000057", "NCNA003700019", "NCNA003900055", "NCNA003500196", "NCNA003800069", "HS02000700010", "HS02000700011", "HS02000700012", "HS02000700013", "HS02000700014", "HS02000800001", "HS02000800002", "HS02000800003", "HS02000800004", "HS02000800005", "HS02000800006", "HS02000800007", "HS02001300016", "HS02001300017", "HS02001300018", "HS02001300019", "HS02001300020", "HS02001300021", "HS02001300022", "HS02001400001", "CH11000100001", "CH11000100002", "CH11000100003", "CH11000100004", "CH11000100005", "CH11000100006", "CH11000100007", "CH11000100008", "CH11000100009", "CH11000100010", "CFMF000100001", "CFMF000100002", "CFMF000100003", "CFMF000100004", "CFMF000100005", "CFMF000100006", "CFMF000100007", "CFMF000100008", "CFMF000100009", "CFMF000100010", "BPNF000100001", "BPNF000100002"," BPNF000100003", "BPNF000100004", "BPNF000100005", "BPNF000100006", "BPNF000100007", "BPNF000100008", "BPNF000100009", "BPNF000100010", "AB08000100001", "AB08000100002", "AB08000100003", "AB08000100004", "AB08000100005", "AB08000100006", "AB08000100007", "AB08000100008", "AB08000100009", "AB08000100010", "MH02000100016", "MH02000100134", "MH02000100247", "MH02000100367", "MH02000100452", "MH02000100525", "MH02000100135", "MH02000100136", "MH02000100137", "MH02000100138", "RS33000100001", "RS33000100002", "RS33000100003", "RS33000100004", "RS33000100005", "RS33000100006", "RS33000100007", "RS33000100008", "RS33000100009", "RS33000100010", "SUCR000100001", "SUCR000100002", "SUCR000100003", "SUCR000100004", "SUCR000100005", "SUCR000100006", "SUCR000100007", "SUCR000100008", "SUCR000100009", "SUCR000100010", "SN02000100001", "SN02000100002", "SN02000100003", "SN02000100004", "SN02000100005", "SN02000100006", "SN02000100007", "SN02000100008", "SN02000100009", "SN02000100010", "AB08000100007", "AB08000100008", "AB08000100009", "AB08000100010", "AB08000100011", "UCRS000100001", "UCRS000100002", "UCRS000100003", "UCRS000100004", "UCRS000100005", "UCRS000100006", "UCRS000100007", "UCRS000100008", "UCRS000100009", "UCRS000100010", "MH02000100016", "MH02000100134", "MH02000100247", "MH02000100367", "MH02000100452", "MH02000100525", "MH02000100135", "MH02000100136", "MH02000100137", "MH02000100138", "CH12000400121", "CH12000400120", "CH12000400119", "CH12000400118", "CH12000400117", "CH12000400116", "CH12000400115", "CH12000400114", "CH12000400113", "CH12000400112", "WS09001600045", "WS09001600044", "WS09001600043", "WS09001600042", "WS09001600041", "WS09001600040", "WS09001600039", "WS09001600038", "WS09001600037", "WS09001600036"]

    # create output with the first tree:
    First_Tree = Tree(cur, pcur, queries, sample_trees[0])
    Bios = First_Tree.compute_biomasses()
    Details = First_Tree.is_detail(XFACTOR)
    Checks = First_Tree.check_trees()
    Areas = First_Tree.is_unusual_area(XFACTOR)

    First_Tree.output_tree(Bios, Details, Checks, Areas, file0 = "10082015_basic.csv", file1 = "10082015_checks.csv", file2 = "10082015_hectare.csv", mode='wt')

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
        A.output_tree(Bios, Details, Checks, Areas, file0 = "10082015_basic.csv", file1 = "10082015_checks.csv", file2 = "10082015_hectare.csv", mode='a')

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