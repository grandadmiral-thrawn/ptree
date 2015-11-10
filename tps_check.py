import tps_Stand
import csv
import math
import poptree_basis
import biomass_basis

class QC(object):
    """ Conducts Stand level quality control if needed. Do not excute this with every run.

    Takes the list of trees who are on any one year of the stand and compare them to the prior year. Checks for the appearance and disappearance of individuals that cannot be attributed to death or a known status change. 

    """

    def __init__(self, target):
        """ Initializes the QC.

        **INPUT VARIABLES**
        
        :target: a stand or stands to QC. 

        **INTERNAL VARIABLES**

        :BM: biomasses on the target stand being processed
        :BTR: list of "bad trees" on the target stand being processsed.
        """

        self.target = target
        self.BM = {}
        self.BTR = {}

        self.parse_target()
        self.check_one_stand()
        self.population_check()

    def check_stand_members(self, BadTreeRef):
        """ Generates an output file containing ingrowth Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), and wood density, by species
        
        """
        filename_out = self.standid + "_stand_member_check.csv"
        
        with open(filename_out, 'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)
            
            writer.writerow(['standid','year', 'species', 'plot', 'treeid', 'state', 'issue'])

            for each_year in BadTreeRef:
                for each_species in BadTreeRef[each_year]:
                    for each_plot in BadTreeRef[each_year][each_species]:
                        if BadTreeRef[each_year][each_species][each_plot]['dead'] == []:
                            pass
                        else:
                            for each_tree in BadTreeRef[each_year][each_species][each_plot]['dead']:
                                writer.writerow([self.standid, each_year, each_species, each_plot, each_tree, 'dead', 'dbh is None'])

                        if BadTreeRef[each_year][each_species][each_plot]['live'] == []:
                            pass
                        else:
                            for each_tree in BadTreeRef[each_year][each_species][each_plot]['live']:
                                writer.writerow([self.standid, each_year, each_species, each_plot, each_tree, 'live', 'dbh is None'])

                        if BadTreeRef[each_year][each_species][each_plot]['ingrowth'] == []:
                            pass
                        else:
                            for each_tree in BadTreeRef[each_year][each_species][each_plot]['ingrowth']:
                                writer.writerow([self.standid, each_year, each_species, each_plot, each_tree, 'ingrowth', 'dbh is None'])


    def parse_target(self):
        """ Enable QC on either one or many stands. Fails if no stands are given.

        **RETURNS**

        False if not inputs. Function for many stands if more than one is given. Function for one stand if one is given.     
        """
        if self.target == []:
            return False

        elif isinstance(self.target, list):
            self.check_many_stand()

        elif isinstance(self.target, str):
            self.check_one_stand()
            self.population_check()

    def check_one_stand(self):
        """ Sets up the needed inputs, such as database connectors. Creates instance of Stand from `self.target`.
        """
        DATABASE_CONNECTION = poptree_basis.YamlConn()
        conn, cur = DATABASE_CONNECTION.sql_connect()
        pconn, pcur = DATABASE_CONNECTION.lite3_connect()
        queries = DATABASE_CONNECTION.queries
        XFACTOR = poptree_basis.Capture()

        A = Stand(cur, pcur, XFACTOR, queries, self.target)

        BM, BTR = A.compute_normal_biomasses(XFACTOR)
        
        if BM == {}:
            Biomasses, BadTreeSpec = A.compute_special_biomasses(XFACTOR)

            if BadTreeSpec == {}:
                pass
            else:
                A.check_stand_members(BadTreeSpec)
                

            self.BM = Biomasses
            self.BTR = BadTreeSpec


        else:
            A.check_stand_members(BTR)
            self.BM = BM
            self.BTR = BTR



def population_check(self):
        """ Gets the tree check data from each year and species.

        * Check if a tree dies in the first year, but is still present in the next year 
        * Check if a tree is alive in the first year, but is not present in the next year 
        * Check if a tree is ingrowth in the first year, but is not a live or dead tree in the next year
        """
        # find trees whose ID's are "lost" between remeasurements
        lost_trees = {}

        import pdb; pdb.set_trace()

        # create a "diff" function to filter items in one list which are not in the other (order matters: items in 1 not in 2)
        diff = lambda l1,l2: filter(lambda x: x not in l2, l1)

        valid_years = sorted(self.BM.keys())

        # get year 1
        first_year = list(valid_years)[0]
        first_species_list = list(self.BM[first_year].keys())

        # get next set of years
        for each_year in valid_years[1:]:

            # name the interval
            interval_name = str(first_year) + " - " + str(each_year)
            second_species_list = list(self.BM[each_year].keys())


            # if a species is present in the first year but not in the next, log it to the lost_trees list appropriately
            for each_species in first_species_list:
                if each_species not in second_species_list:

                    name_dead = self.BM[first_year][each_species]['name_dead']
                    name_live = self.BM[first_year][each_species]['name_live']
                    name_ingrowth = self.BM[first_year][each_species]['name_ingrowth']
                    name_live_2 = self.BM[each_year][each_species]['name_live']
                    name_dead_2 = self.BM[each_year][each_species]['name_dead']

                # check if some trees randomly appear - same check as the ingrowth tree lost check below, except can occur within a species which does not disappear
                elif each_species in second_species_list:
                    name_live_2 = self.BM[each_year][each_species]['name_live']
                    name_live = self.BM[first_year][each_species]['name_live']
                    name_ingrowth = self.BM[first_year][each_species]['name_ingrowth']

                    diff_live_l = diff(name_live_2, name_live)
                    if diff_live_l != []:
                        magical_trees = [each_tree for each_tree in diff_live_1 if each_tree not in name_ingrowth]
                        if magical_trees != []:
                            for each_tree in magical_trees:
                                if each_species not in lost_trees:
                                    lost_trees[each_species] = {interval_name: {'ingrowth_tree_lost' : [each_tree]}}
                                elif each_species in lost_trees:
                                    if interval_name not in lost_trees[each_species]:
                                        lost_trees[each_species][interval_name] = {'ingrowth_tree_lost': [each_tree]}
                                    elif interval_name in lost_trees[each_species]:
                                        lost_trees[each_species][interval_name]['ingrowth_tree_lost'].append(each_tree)
                                    else:
                                        pass

                    # if there are no dead trees in the first year but that species is going to disappear, record this
                    if name_dead == []:

                        for each_tree in name_dead: 
                            if each_species not in lost_trees:
                                lost_trees[each_species] = {interval_name : {'dead_tree_lost': [each_tree]}}
                            elif each_species in lost_trees:
                                if interval_name not in lost_trees[each_species]:
                                    lost_trees[interval_name][each_species]= {'dead_tree_lost': [each_tree]}
                                elif interval_name in lost_trees[interval_name][each_species]:
                                    lost_trees[interval_name][each_species]['dead_tree_lost'].append(each_tree)
                                else:
                                    pass

                    # if there are live trees in that year in that species, but the species will disappear in the next year, then there will be live trees lost
                    if name_live != []:

                        for each_tree in name_live:
                            if each_species not in lost_trees:
                                lost_trees[each_species] ={interval_name : {'live_tree_lost' : [each_tree]}}
                            elif each_species in lost_trees:
                                if interval_name not in lost_trees[each_species]:
                                    lost_trees[interval_name][each_speices] = {'live_tree_lost': [each_tree]}
                                elif interval_name in lost_trees[interval_name][each_species]:
                                    lost_trees[interval_name][each_species]['live_tree_lost'].append(each_tree)
                                else:
                                    pass

                    # if a tree comes in as ingrowth but it is not in the next years live or dead, it has been abandoned.
                    if name_ingrowth != []:
                        abandoned_trees = [each_tree for each_tree in name_ingrowth if each_tree not in name_live_2]
                    else:
                        pass

                        if abandoned_trees != []:
                            abandoned_trees_2 = [each_tree for each_tree in abandoned_trees if each_tree not in name_dead_2]
                        else:
                            pass

                            if abandoned_trees_2 != []:
                                for each_tree in abandoned_trees_2:
                                    if each_species not in lost_trees:
                                        lost_trees[each_species] ={interval_name : {'ingrowth_tree_abandoned' : [each_tree]}}
                                    elif each_species in lost_trees:
                                        if interval_name not in lost_trees[each_species]:
                                            lost_trees[interval_name][each_species] = {'ingrowth_tree_abandoned': [each_tree]}
                                        elif interval_name in lost_trees[interval_name][each_species]:
                                            lost_trees[interval_name][each_species]['ingrowth_tree_abandoned'].append(each_tree)
                                        else:
                                            pass


        print("lost some trees!")                                
        return lost_trees


    def check_many_stands(self):
        """ Sets up the needed inputs
        """
        DATABASE_CONNECTION = poptree_basis.YamlConn()
        conn, cur = DATABASE_CONNECTION.sql_connect()
        queries = DATABASE_CONNECTION.queries
        XFACTOR = poptree_basis.Capture()
