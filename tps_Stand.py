#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import biomass_basis
import bisect
import csv

class Stand(object):
    """Stands contain several plots, grouped by year and species. Stand produce outputs of biomass, volume, jenkins, trees/ha, and basal areas per hectare. Also, a number of checks are performed.

    1. "Tree in remeasurement not in master" - a tree id appears in one measurement not in the former
    2. "Tree in master not remeasured" - a tree id disappears from one measurement to the next

    .. Example:

    >>> A = Stand(cur, pcur, XFACTOR, queries, 'NCNA')
    >>> A.cur = <pymssql.Cursor object at 0x1007a4648>
    >>> A.pcur = <sqlite3.Cursor object at 0x10078cce0>
    >>> A.tree_list = "SELECT fsdbdata.dbo.tp00101.treeid, fsdbdata.dbo.tp00101.species..."
    >>> A.species_list = ""SELECT DISTINCT(fsdbdata.dbo.tp00101.species) from ..."
    >>> A.eqn_query = "SELECT SPECIES, EQNSET, FORM, H1, H2, H3, B1 ..."
    >>> A.eqns = {'abam': {'normal': <function Stand.select_eqns.<locals>.<lambda> at 0x1007d9730>}..."
    >>> A.od[1985]['abam'][4]['dead']
    >>> [('av06000400017', None, '6', '1985')]

    .. Note: shifted keys are the years with live trees; mortality only years are merged into these.

    >>> A.od.keys()
    >>> dict_keys([1985, 1987, 1988, 2007, 1993, 1978, 1981, 1998, 1983])
    >>> A.shifted.keys()
    >>> dict_keys([1993, 1978, 1988, 1998, 2007])
    >>> A.mortality_years
    >>> [1981, 1983, 1985, 1987]
 
    """
    def __init__(self, cur, pcur, XFACTOR, queries, standid):
        self.standid = standid
        self.cur = cur
        self.pcur = pcur
        self.tree_list = queries['stand']['query_trees']
        self.species_list = queries['stand']['query_species']
        self.eqn_query = queries['tree']['sql_1tree_eqn']
        self.eqns = {}
        self.od = {}
        self.shifted = {}
        self.mortality_years = []

        # check that the stand contains detail plots
        self.select_eqns()
        self.get_all_trees(queries)

        # checks if it is a mortality plot, and, if so, shifts the dbhs to the year they should be on for the death totals
        is_mort = self.check_mort()
        self.update_mort(is_mort)

    def select_eqns(self):
        """ Gets only the equations you need based on the species on that plot by querying the database for individual species that will be on this stand and makes an equation table.


        """
        list_species = []
        
        self.cur.execute(self.species_list.format(standid = self.standid))

        for row in self.cur:
            list_species.append(str(row[0]).strip().lower())

        for each_species in list_species:
            sql2 = self.eqn_query.format(species=each_species)
            
            self.cur.execute(sql2)

            for row in self.cur:

                form = str(row[2]).strip().lower()
                
                try:
                    woodden = round(float(str(row[11])), 3)
                except:
                    woodden = None

                self.woodden = woodden
                try:
                    h1 = round(float(str(row[3])), 6)
                except:
                    h1 = None
                try:
                    h2 = round(float(str(row[4])), 6)
                except:
                    h2 = None
                try:
                    h3 = round(float(str(row[5])), 6)
                except:
                    h3 = None
                try:
                    b1 = round(float(str(row[6])), 6)
                except:
                    b1 = None
                try:
                    b2 = round(float(str(row[7])), 6)
                except:
                    b2 = None
                try:
                    b3 = round(float(str(row[8])), 6)
                except:
                    b3 = None
                try:
                    j1 = round(float(str(row[9])), 6)
                except:
                    j1 = None
                try:
                    j2 = round(float(str(row[10])), 6)
                except:
                    j2 = None


                if form != 'as_compbio':
                    this_eqn = lambda x : biomass_basis.which_fx(form)(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                    
                    if each_species not in self.eqns:
                        self.eqns.update({each_species:{str(row[1]).rstrip().lower():this_eqn}})
                    
                    elif each_species in self.eqns:
                        # when there are 2 or more sizes
                        self.eqns[each_species].update({str(row[1]).rstrip().lower():this_eqn})

                # only for "ACCI"
                elif form == 'as_compbio':
                    this_eqn = lambda x: biomass_basis.which_fx('as_biopak')(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                    if each_species not in self.eqns:
                        self.eqns.update({each_species: {str(row[12]).rstrip().lower():this_eqn}})
                    elif each_species in self.eqns:
                        self.eqns[each_species].update({str(row[12]).rstrip().lower():this_eqn})
                    

    def get_all_trees(self, queries):
        """ Get the trees on that stand by querying FSDBDATA and sort them by year, plot, live or dead, and species.

        .. Note: ingrowth is included in "live" (live statuses are all but "6" and "9"), but ingrowth is exclusive when status is "2"

        """
        self.cur.execute(queries['stand']['query'].format(standid=self.standid))
        
        for row in self.cur:
            try:
                year = int(row[6])
            except Exception:
                year = None

            try:
                plotid = int(str(row[3][4:]))
            except Exception:
                plotid = None

            try:
                species = str(row[1]).strip().lower()
            except Exception:
                species = None

            try:
                dbh = round(float(row[4]), 3)
            except Exception:
                dbh = None

            try:
                status = str(row[5]).strip()
            except Exception:
                status = None

            try:
                tid = str(row[0]).strip().lower()
            except Exception:
                tid = "None"

            try:
                dbh_code = str(row[6]).strip()
            except Exception:
                dbh_code = None

            if year not in self.od and status in ["6", "9"]:
                self.od[year]={species:{plotid: {'live': [], 'ingrowth': [], 'dead': [(tid, dbh, status, dbh_code)]}}}
            
            elif year not in self.od and status not in ["6","9"]:
                self.od[year]={species: {plotid: {'live': [(tid, dbh, status, dbh_code)], 'ingrowth': [], 'dead': []}}}

                if status == "2":
                    self.od[year][species][plotid]['ingrowth'].append((tid, dbh, status, dbh_code))
                else:
                    pass

            elif year in self.od:

                if species not in self.od[year] and status in ["6", "9"]:
                    self.od[year][species] ={plotid: {'live': [], 'ingrowth': [], 'dead': [(tid, dbh, status, dbh_code)]}}
                    
                elif species not in self.od[year] and status not in ["6","9"]: 
                    self.od[year][species] ={plotid: {'live': [(tid, dbh, status, dbh_code)], 'ingrowth': [], 'dead': []}}

                    if status == "2":
                        self.od[year][species][plotid]['ingrowth'].append((tid, dbh, status, dbh_code))
                    else:
                        pass

                elif species in self.od[year]:
                    
                    if status in ["6", "9"] and plotid not in self.od[year][species]:
                        self.od[year][species][plotid] = {'dead': [(tid, dbh, status, dbh_code)], 'live': [], 'ingrowth': []}
                    
                    elif status not in ["6", "9"] and plotid not in self.od[year][species]:
                        self.od[year][species][plotid] = {'live': [(tid, dbh, status, dbh_code)], 'dead': [], 'ingrowth': []}
                        
                        if status == "2":
                            self.od[year][species][plotid]['ingrowth'].append((tid, dbh, status, dbh_code))
                        else:
                            pass

                    elif status not in ["6", "9"] and plotid in self.od[year][species]:
                        
                        self.od[year][species][plotid]['live'].append((tid, dbh, status, dbh_code))
                        
                        if status == "2":
                            self.od[year][species][plotid]['ingrowth'].append((tid, dbh, status, dbh_code))
                        else:
                            pass

                    elif status in ["6", "9"] and plotid in self.od[year][species][plotid]['dead']:
                        self.od[year][species][plotid]['dead'].append((tid, dbh, status, dbh_code))


    def check_mort(self):
        """ Checks if the year is a mortality year, and if so, bisect it into the subsequent live year.

        Populates self.mortality_years if there are any mortality years. Also sets self.shifted to the output dictionary if there are no mortality years.
        """
        # a year is a mortality year if there is no live biomass in that year for all species on a plot. include species because maybe useful for species
        list_all_years_possible_mortality = []
        
        for each_year in self.od.keys():

            possible_species = []
            for each_species in self.od[each_year].keys():

                list_of_plots_where_no_live = [x for x in self.od[each_year][each_species].keys() if self.od[each_year][each_species][x]['live'] == []]

                if list_of_plots_where_no_live == []:
                    self.shifted = self.od
                    return False

                elif list_of_plots_where_no_live == list(self.od[each_year][each_species].keys()):
                    possible_species.append(each_species)

            if possible_species != self.od[each_year].keys():
                self.shifted = self.od
                return False

            else:
                list_all_years_possible_mortality.append(each_year)


        #list_all_years_possible_mortality = [year for year in self.od.keys() for species in self.od[year].keys() for plot in self.od[year][species].keys() if self.od[year][species][plot]['live'] ==[]]

        import pdb; pdb.set_trace()

        if list_all_years_possible_mortality == []:
            self.shifted = self.od
            return False
        
        else:
            # use the dictionary comprehension method to uniqueify the list! :)
            mortality_years_comp = {year: None for year in list_all_years_possible_mortality}
            self.mortality_years = sorted(mortality_years_comp.keys())
            return True


    def update_mort(self, is_mort):
        """ Returns a new dbh dictionary for the stand based on whether or not a year is a mortality year. If it is not a mortality year, the dictionary is the same as the original. If it is a mortality year, the dead trees are shifted to the subsequent year.

        The bisect right function determines the windowing years from a given list around a given input year. 

        :list_of_live_years: a list of years when checks were performed that were not mortality only
        :dead_year: the year of the mortality check to be aggregated to a selection from list_of_live_years
        :is_mort: Boolean value of whether or not we should update mortality. If it was not a mortality year, we shifted the original output into the shifted dictionary using check_mort, without changing a value!
        """
        if is_mort != True:
            pass
        
        else:
            # in this list, all the years which are NOT mortality years, no matter what
            list_live_years = [x for x in sorted(self.od.keys()) if x not in self.mortality_years]


            
            self.shifted = {x: self.od[x] for x in list_live_years}
            
            for each_year in self.mortality_years:
                current_data = self.od[each_year]

                if each_year not in list_live_years:
                    index = bisect.bisect_right(list_live_years, each_year)
                    update_year = list_live_years[index]
                else:
                    update_year = each_year
                
                # if the new mortality year isn't listed, add it in
                if update_year not in self.shifted.keys():
                    self.shifted[update_year] = current_data
                
                elif update_year in self.shifted.keys():
                    for each_species in current_data.keys():
                        if each_species not in self.shifted[update_year].keys():
                            self.shifted[update_year][each_species] = current_data[each_species]
                        elif each_species in self.shifted[update_year].keys():
                            for each_plot in current_data[each_species].keys():
                                if each_plot not in self.shifted[update_year][each_species].keys():
                                    self.shifted[update_year][each_species][each_plot] = current_data[each_species][each_plot]
                                elif each_plot in self.shifted[update_year][each_species].keys():
                                    self.shifted[update_year][each_species][each_plot]['dead'].append(current_data[each_species][each_plot]['dead'])


    def compute_normal_biomasses(self, XFACTOR):
        """ Compute the biomass, volume, jenkins. Use for "normal" stands.

        First use XFACTOR to tell if a fancy computation needs to be performed.

        :XFACTOR: a Capture object containing the detail plots, minimum dbhs, etc.
        :XFACTOR.detail_reference: plots which are detail plots and when
        :XFACTOR.stands_with_unusual_mins: plots which have minimums that are not 15 and are not detail plots
        :XFACTOR.unusual_plot_areas: plots whose areas are not 625 m

        **INTERNAL VARIABLES**

        :Biomasses: The output dictionary which will ultimately contain the biomass, Jenkins' biomass, volume, etc. for the stand. 

        """

        Biomasses = {}
        
        # if the stand id is one that should not be treated as a "normal" stand, return the empty dictionary
        if self.standid in XFACTOR.detail_reference.keys() or self.standid in XFACTOR.uplot_areas.keys() or self.standid in XFACTOR.umins_reference.keys():
            return Biomasses

        else:
            all_years = sorted(self.shifted.keys())
            
            for each_year in all_years:
                for each_species in self.shifted[each_year].keys():
                    for each_plot in self.shifted[each_year][each_species].keys():

                        # dead trees first
                        if each_species == "acci":
                            
                            dead_trees = {value[0]: {'bio': biomass_basis.as_compbio(value[1], self.eqns['acci']), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['dead']) if value[1] >= 15.0 and value[1] != None}
                        else:

                            dead_trees = {value[0]: {'bio': self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['dead']) if value[1] != None and value[1] >= 15.0}

                        bad_dead_trees = {value[0]: {'dbh': value[1], 'status': value[2], 'year':each_year, 'plot':each_plot} for index, value in enumerate(self.shifted[each_year][each_species][each_plot]['dead']) if value[1] == None}    

                        # create a cache for the live trees for that year - remember this is in ascending order :)
                        cached_live_trees = {}
                        cached_ingrowth_trees = {}

                        if each_species == "acci":
                            live_trees = {value[0]:{'bio' : biomass_basis.as_compbio(value[1], self.eqns['acci']), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['live']) if value[1]!= None and value[1] >= 15.0}
                            
                        else:

                            live_trees = {value[0]:{'bio' : self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['live']) if value[1]!= None and value[1] >= 15.0}


                        bad_live_trees = {value[0]: {'dbh': value[1], 'status': value[2], 'year': each_year, 'plot':each_plot } for index, value in enumerate(self.shifted[each_year][each_species][each_plot]['live']) if value[1] == None}

                        if each_species == "acci":

                            ingrowth_trees = {value[0]: {'bio': biomass_basis.as_compbio(value[1], self.eqns['acci']), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['ingrowth']) if value[1]!= None and value[1] >= 15.0}

                        else:

                            ingrowth_trees = {value[0]: {'bio': self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['ingrowth']) if value[1]!= None and value[1] >= 15.0}

                        bad_ingrowth_trees = {value[0]:{'tree': value[1] ,'status':value[2], 'year':each_year, 'plot':each_plot} for index, value in enumerate(self.shifted[each_year][each_species][each_plot]['ingrowth']) if value[1] == None}

                        # set the cached live trees lookup to live trees and the cached ingrowth trees lookup to ingrowth trees
                        cached_live_trees = live_trees
                        cached_ingrowth_trees = ingrowth_trees

                        # if for some reason there are dead trees without a dbh, find them from the previous measurements live trees                        
                        if bad_dead_trees == {}:
                            pass

                        elif bad_dead_trees != {}:
                            if cached_live_trees != {} or cached_ingrowth_trees != {}:

                                tids_bad_dead_trees = bad_dead_trees.keys()
                                new_dead_trees = {x:cached_live_trees[x] for x in cached_live_trees.keys() if cached_live_trees.get(x) != None}
                                new_dead_trees.update({x:cached_ingrowth_trees[x] for x in cached_ingrowth_trees.keys() if cached_ingrowth_trees.get(x) != None})
                                dead_trees.update(new_dead_trees)
                            else:
                                bad_dead_trees.update(bad_dead_trees)
                        else:
                            pass

                        ## All these are "normal" so we know there is not any multiplying to do and we can divide the area by 625 to get the per Mg/m2 values
                        total_live_bio = round(sum([live_trees[tree]['bio'][0] for tree in live_trees.keys()])/625., 3)
                        total_ingrowth_bio = round(sum([ingrowth_trees[tree]['bio'][0] for tree in ingrowth_trees.keys()])/625., 3)
                        total_dead_bio = round(sum([dead_trees[tree]['bio'][0] for tree in dead_trees.keys()])/625., 3)

                        total_live_jenkins = round(sum([live_trees[tree]['bio'][2] for tree in live_trees.keys()])/625., 3)
                        total_ingrowth_jenkins = round(sum([ingrowth_trees[tree]['bio'][2] for tree in ingrowth_trees.keys()])/625., 3)
                        total_dead_jenkins = round(sum([dead_trees[tree]['bio'][2] for tree in dead_trees.keys()])/625., 3)

                        total_live_volume = sum([live_trees[tree]['bio'][1] for tree in live_trees.keys()])/625.
                        total_ingrowth_volume = sum([ingrowth_trees[tree]['bio'][1] for tree in ingrowth_trees.keys()])/625.
                        total_dead_volume = sum([dead_trees[tree]['bio'][1] for tree in dead_trees.keys()])/625.

                        total_live_basal = sum([live_trees[tree]['ba'] for tree in live_trees.keys()])/625.
                        total_ingrowth_basal = sum([ingrowth_trees[tree]['ba'] for tree in ingrowth_trees.keys()])/625.
                        total_dead_basal = sum([dead_trees[tree]['ba'] for tree in dead_trees.keys()])/625.

                        total_live_trees = len(live_trees.keys())/625.
                        total_ingrowth_trees = len(ingrowth_trees.keys())/625.
                        total_dead_trees = len(dead_trees.keys())/625.

                        # just take the wood density from a fake tree at a fake dbh one time.
                        try:
                            wooddensity = self.eqns[each_species][biomass_basis.maxref(25.0, each_species)](25.0)[3]
                        except Exception:
                            if each_species == "acci":
                                wooddensity = 0.44
                            else:
                                # a default value 
                                wooddensity = 0.5

                        # get a list of tree names for checking
                        living_trees = list(live_trees.keys())
                        ingrowth_trees = list(ingrowth_trees.keys())
                        dead_trees = list(dead_trees.keys())

                        if each_year not in Biomasses:
                            Biomasses[each_year] = {each_species : {'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'wooddensity': wooddensity, 'total_live_basal': total_live_basal, 'total_dead_basal': total_dead_basal, 'name_live': living_trees, 'total_ingrowth_basal': total_ingrowth_basal, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'name_live': living_trees, 'name_dead': dead_trees, 'name_ingrowth': ingrowth_trees}}
                        
                        elif each_year in Biomasses:
                            # do not need to augment the wood density :)
                            if each_species not in Biomasses[each_year]:
                                Biomasses[each_year][each_species]={'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_basal': total_live_basal, 'total_dead_basal': total_dead_basal, 'name_live': living_trees, 'total_ingrowth_basal': total_ingrowth_basal,'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'name_live':living_trees, 'name_dead': dead_trees, 'wooddensity': wooddensity, 'name_ingrowth': ingrowth_trees}
                            # don't need to augment the wood density - one time is enough!
                            elif each_species in Biomasses[each_year]:
                                
                                Biomasses[each_year][each_species]['total_live_bio'] += total_live_bio
                                Biomasses[each_year][each_species]['total_dead_bio'] += total_dead_bio
                                Biomasses[each_year][each_species]['total_ingrowth_bio'] += total_ingrowth_bio
                                Biomasses[each_year][each_species]['total_live_jenkins'] +=total_live_jenkins
                                Biomasses[each_year][each_species]['total_ingrowth_jenkins'] += total_ingrowth_jenkins
                                Biomasses[each_year][each_species]['total_dead_jenkins'] += total_dead_jenkins
                                Biomasses[each_year][each_species]['total_live_volume'] += total_live_volume
                                Biomasses[each_year][each_species]['total_dead_volume'] += total_dead_volume
                                Biomasses[each_year][each_species]['total_ingrowth_volume'] += total_ingrowth_volume
                                Biomasses[each_year][each_species]['total_live_trees'] += total_live_trees
                                Biomasses[each_year][each_species]['total_dead_trees'] += total_dead_trees 
                                Biomasses[each_year][each_species]['total_ingrowth_trees'] += total_ingrowth_trees
                                Biomasses[each_year][each_species]['name_live'].append(living_trees)
                                Biomasses[each_year][each_species]['name_dead'].append(dead_trees)
                                Biomasses[each_year][each_species]['name_ingrowth'].append(ingrowth_trees)

                            else:
                                pass

        print(Biomasses)
        return Biomasses

    def compute_special_biomasses(self, XFACTOR):
        """ Compute the biomass, volume, jenkins. Use for stands with alternate minimums, areas, or detail plots 

        First use the Capture object to tell if a fancy computation (i.e. get a special area, minimum, etc. needs to be performed.
            Load in the appropriate parameters for this computation. Separate "small" trees from "large" ones so that small ones can get the expansion factor. If they aren't on a detail plot, this number will just be "1".


        :XFACTOR: a Capture object containing the detail plots, minimum dbhs, etc.
        :XFACTOR.detail_reference: plots which are detail plots and when
        :XFACTOR.stands_with_unusual_mins: plots which have minimums that are not 15 and are not detail plots
        :XFACTOR.unusual_plot_areas: plots whose areas are not 625m
        """

        Biomasses = {}
        
        all_years = sorted(self.shifted.keys())
        
        for each_year in all_years:
            for each_species in self.shifted[each_year].keys():
                
                if each_species == 'pimo':
                    #import pdb; pdb.set_trace()
                    continue
                else:
                    pass
                for each_plot in self.shifted[each_year][each_species].keys():

                    # try to find the plot in the unusual mins reference
                    try:
                        mindbh = XFACTOR.umins_reference[self.standid][each_year][each_species][each_plot]
                    except KeyError as exc:
                        mindbh = 15.0

                    # try to find the plot in the unusual areas reference
                    try:
                        area = XFACTOR.uplot_areas[self.standid][each_year][each_species][each_plot]
                    except KeyError as exc:
                        area = 625.
                    
                    # test if the plot is a detail plot
                    if self.standid not in XFACTOR.detail_reference.keys():
                        Xw = 1.0
                    else:
                        Xw = XFACTOR.expansion[self.standid][each_year]
                        mindbh = XFACTOR.detail_reference[self.standid][each_year][each_plot]['min']

                        area = XFACTOR.detail_reference[self.standid][each_year][each_plot]['area']

                    # compute the dead trees first, if the dbh is not None
                    try: 
                        dead_trees_large = {value[0]: {'bio': self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['dead']) if value[1] != None and value[1] >= 15.0}

                        dead_trees_small = {value[0]: {'bio': self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['dead']) if value[1] != None and value[1] >= mindbh and value[1] < 15.0}

                        bad_dead_trees = {value[0]: {'dbh': value[1], 'status': value[2], 'year':each_year, 'plot':each_plot} for index, value in enumerate(self.shifted[each_year][each_species][each_plot]['dead']) if value[1] == None}

                    except Exception:
                        try: 
                            flat_list = [item for sublist in self.shifted[each_year][each_species][each_plot]['dead'] for item in sublist]
                            
                            dead_trees_large = {value[0]: {'bio': self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(flat_list) if value[1] != None and value[1] >= 15.0}
                            
                            dead_trees_small = {value[0]: {'bio': self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(flat_list) if value[1] != None and value[1] >= mindbh and value[1]<15.0}

                            bad_dead_trees = {value[0]: {'dbh': value[1], 'status': value[2], 'year':each_year, 'plot':each_plot} for index, value in enumerate(flat_list) if value[1] == None}

                        except Exception:
                            flat_list = [item for sublist in self.shifted[each_year][each_species][each_plot]['dead'] for item in sublist]
                            print(self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]) for index,value in enumerate(flat_list) if value[1] != None)

                    # create a cache for the live trees for that year - remember this is in ascending order :)
                    cached_live_trees_large = {}
                    cached_live_trees_small = {}

                    cached_ingrowth_trees_large = {}
                    cached_ingrowth_trees_small = {}

                    live_trees_large = {value[0]:{'bio' : self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['live']) if value[1]!= None and value[1] >= 15.0}
                    live_trees_small = {value[0]:{'bio' : self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['live']) if value[1]!= None and value[1] >= mindbh and value[1] < 15.0}

                    bad_live_trees = {value[0]: {'dbh': value[1], 'status': value[2], 'year': each_year, 'plot':each_plot } for index, value in enumerate(self.shifted[each_year][each_species][each_plot]['live']) if value[1] == None}

                    ingrowth_trees_large = {value[0]: {'bio': self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['ingrowth']) if value[1] != None and value[1] >= 15.0}
                    ingrowth_trees_small = {value[0]: {'bio': self.eqns[each_species][biomass_basis.maxref(value[1], each_species)](value[1]), 'ba': round(0.00007854*float(value[1]),3)} for index,value in enumerate(self.shifted[each_year][each_species][each_plot]['ingrowth']) if value[1] != None and value[1] >= mindbh and value[1] < 15.0}

                    bad_ingrowth_trees = {value[0]:{'tree': value[1] ,'status':value[2], 'year':each_year, 'plot':each_plot} for index, value in enumerate(self.shifted[each_year][each_species][each_plot]['ingrowth']) if value[1] == None}

                    # set the cached live trees lookup to live trees and the cached ingrowth trees lookup to ingrowth trees
                    cached_live_trees_large = live_trees_large
                    cached_live_trees_small = live_trees_small
                    cached_ingrowth_trees_small = ingrowth_trees_large
                    cached_ingrowth_trees_small = ingrowth_trees_small

                    # if for some reason there are dead trees without a dbh, find them from the previous measurements live trees or ingrowth trees                        
                    if bad_dead_trees == {}:
                        pass

                    elif bad_dead_trees != {}:
                        if cached_live_trees_large != {} or cached_ingrowth_trees_large != {} or cached_live_trees_small !={} or cached_ingrowth_trees_small != {}:

                            new_dead_trees_large = {}
                            new_dead_trees_small = {}
                            tids_bad_dead_trees = bad_dead_trees.keys()
                            new_dead_trees_large = {x:cached_live_trees_large[x] for x in cached_live_trees_large.keys() if cached_live_trees_large.get(x) != None}
                            new_dead_trees_large.update({x:cached_ingrowth_trees_large[x] for x in cached_ingrowth_trees_large.keys() if cached_ingrowth_trees_large.get(x) != None})
                            new_dead_trees_small.update({x:cached_ingrowth_trees_small[x] for x in cached_ingrowth_trees_small.keys() if cached_ingrowth_trees_small.get(x) != None})
                            new_dead_trees_small.update({x:cached_live_trees_small[x] for x in cached_live_trees_small.keys() if cached_live_trees_small.get(x) != None})
                            dead_trees_large.update(new_dead_trees_large)
                            dead_trees_small.update(new_dead_trees_small)
                        else:
                            print(bad_dead_trees)
                    else:
                        pass

                    ## All these are "normal" so we know there is not any multiplying to do and we can divide the area by 625 to get the per Mg/m2 values
                    total_live_bio = sum([live_trees_large[tree]['bio'][0] for tree in live_trees_large.keys()])/area + sum([live_trees_small[tree]['bio'][0]*Xw for tree in live_trees_small.keys()])/area
                    total_ingrowth_bio = sum([ingrowth_trees_large[tree]['bio'][0] for tree in ingrowth_trees_large.keys()])/area + sum([ingrowth_trees_small[tree]['bio'][0] * Xw for tree in ingrowth_trees_small.keys()])/area
                    total_dead_bio = sum([dead_trees_large[tree]['bio'][0] for tree in dead_trees_large.keys()])/area + sum([dead_trees_small[tree]['bio'][0]*Xw for tree in dead_trees_small.keys()])/area

                    total_live_jenkins = sum([live_trees_large[tree]['bio'][2] for tree in live_trees_large.keys()])/area + sum([live_trees_small[tree]['bio'][2] * Xw for tree in live_trees_small.keys()])/area
                    total_ingrowth_jenkins = sum([ingrowth_trees_large[tree]['bio'][2] for tree in ingrowth_trees_large.keys()])/area +  sum([ingrowth_trees_small[tree]['bio'][2] * Xw for tree in ingrowth_trees_small.keys()])/area
                    total_dead_jenkins = sum([dead_trees_large[tree]['bio'][2] for tree in dead_trees_large.keys()])/area + sum([dead_trees_small[tree]['bio'][2] * Xw for tree in dead_trees_small.keys()])/area

                    total_live_volume = sum([live_trees_large[tree]['bio'][1] for tree in live_trees_large.keys()])/area + sum([live_trees_small[tree]['bio'][1] * Xw for tree in live_trees_small.keys()])/area
                    total_ingrowth_volume = sum([ingrowth_trees_large[tree]['bio'][1] for tree in ingrowth_trees_large.keys()])/area + sum([ingrowth_trees_small[tree]['bio'][1] * Xw for tree in ingrowth_trees_small.keys()])/area
                    total_dead_volume = sum([dead_trees_large[tree]['bio'][1] for tree in dead_trees_large.keys()])/area + sum([dead_trees_small[tree]['bio'][1] * Xw for tree in dead_trees_small.keys()])/area

                    total_live_trees = len(live_trees_large.keys())/area+ len(live_trees_small.keys())*Xw/area
                    total_ingrowth_trees = len(ingrowth_trees_large.keys())/area + len(ingrowth_trees_small.keys())*Xw/area
                    total_dead_trees = len(dead_trees_large.keys())/area + len(dead_trees_small.keys())*Xw/area

                    total_live_basal = sum([live_trees_large[tree]['ba'] for tree in live_trees_large.keys()])/area + sum([live_trees_small[tree]['ba'] * Xw for tree in live_trees_small.keys()])/area
                    total_ingrowth_basal = sum([ingrowth_trees_large[tree]['ba'] for tree in ingrowth_trees_large.keys()])/area +  sum([ingrowth_trees_small[tree]['ba'] * Xw for tree in ingrowth_trees_small.keys()])/area
                    total_dead_basal = sum([dead_trees_large[tree]['ba'] for tree in dead_trees_large.keys()])/area + sum([dead_trees_small[tree]['ba']* Xw for tree in dead_trees_small.keys()])/area

                    
                    # just take the wood density from one tree to have
                    try:
                        wooddensity = self.eqns[each_species][biomass_basis.maxref(25.0, each_species)](25.0)[3]
                    
                    except Exception:
                        # find the wood density by pretending that you need to compute a 25 cm tree
                        if each_species == "acci":
                            wooddensity = 0.44
                        else:
                            wooddensity = 0.5
                        

                    # get a list of tree names for checking
                    living_trees = list(live_trees_large) + list(live_trees_small)
                    ingrowth_trees = list(ingrowth_trees_large) + list(ingrowth_trees_small)
                    dead_trees = list(dead_trees_large) + list(dead_trees_small)

                    if each_year not in Biomasses:
                        Biomasses[each_year] = {each_species : {'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'total_live_basal': total_live_basal, 'wooddensity': wooddensity, 'name_live': living_trees, 'name_mort': dead_trees, 'total_ingrowth_basal': total_ingrowth_basal, 'total_dead_basal': total_dead_basal,  'name_ingrowth': ingrowth_trees}}
                    

                    elif each_year in Biomasses:
                        # do not need to augment the wood density :) -> but do make sure it is in here
                        if each_species not in Biomasses[each_year]:
                            Biomasses[each_year][each_species]={'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'total_live_basal': total_live_basal, 'total_dead_basal': total_dead_basal, 'name_live': living_trees, 'total_ingrowth_basal': total_ingrowth_basal, 'wooddensity': wooddensity, 'name_mort': dead_trees,'name_ingrowth': ingrowth_trees}
                        
                        # don't need to augment the wood density - one time is enough!
                        elif each_species in Biomasses[each_year]:
                            Biomasses[each_year][each_species]['total_live_bio'] += total_live_bio
                            Biomasses[each_year][each_species]['total_dead_bio'] += total_dead_bio
                            Biomasses[each_year][each_species]['total_ingrowth_bio'] += total_ingrowth_bio
                            Biomasses[each_year][each_species]['total_live_jenkins'] +=total_live_jenkins
                            Biomasses[each_year][each_species]['total_ingrowth_jenkins'] += total_ingrowth_jenkins
                            Biomasses[each_year][each_species]['total_dead_jenkins'] += total_dead_jenkins
                            Biomasses[each_year][each_species]['total_live_volume'] += total_live_volume
                            Biomasses[each_year][each_species]['total_dead_volume'] += total_dead_volume
                            Biomasses[each_year][each_species]['total_ingrowth_volume'] += total_ingrowth_volume
                            Biomasses[each_year][each_species]['total_live_trees'] += total_live_trees
                            Biomasses[each_year][each_species]['total_dead_trees'] += total_dead_trees 
                            Biomasses[each_year][each_species]['total_ingrowth_trees'] += total_ingrowth_trees
                            Biomasses[each_year][each_species]['name_live'].append(living_trees)
                            Biomasses[each_year][each_species]['name_mort'].append(dead_trees)
                            Biomasses[each_year][each_species]['name_ingrowth'].append(ingrowth_trees)
                            Biomasses[each_year][each_species]['total_live_basal']+=total_live_basal
                            Biomasses[each_year][each_species]['total_dead_basal']+=total_dead_basal
                            Biomasses[each_year][each_species]['total_ingrowth_basal']+=total_ingrowth_basal
                            Biomasses[each_year][each_species]['wooddensity'] = wooddensity
                        else:
                            pass

        return Biomasses

    def write_stand_live(self, Biomasses):

        filename_out = self.standid + "_stand_live_output.csv"
        with open(filename_out,'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            writer.writerow(['year','species','total_live_bio','total_live_jenkins','total_live_volume','total_live_trees','total_live_basal','wooddensity'])

            for each_year in Biomasses:
                for each_species in Biomasses[each_year]:
                  
                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row = [each_year, each_species, round(Biomasses[each_year][each_species]['total_live_bio']*10000,3), round(Biomasses[each_year][each_species]['total_live_jenkins']*10000,3), round(Biomasses[each_year][each_species]['total_live_volume']*10000,3), int(Biomasses[each_year][each_species]['total_live_trees']*10000), round(Biomasses[each_year][each_species]['total_live_basal']*10000,3), Biomasses[each_year][each_species]['wooddensity']]
                    
                    writer.writerow(new_row)

    def write_stand_dead(self, Biomasses):
        filename_out = self.standid + "_stand_dead_output.csv"
        with open(filename_out,'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            writer.writerow(['year','species','total_dead_bio','total_dead_jenkins','total_dead_volume','total_dead_trees','total_dead_basal','wooddensity'])

            for each_year in Biomasses:
                for each_species in Biomasses[each_year]:
                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row = [each_year, each_species, round(Biomasses[each_year][each_species]['total_dead_bio']*10000,3), round(Biomasses[each_year][each_species]['total_dead_jenkins']*10000,3), round(Biomasses[each_year][each_species]['total_dead_volume']*10000,3), int(Biomasses[each_year][each_species]['total_dead_trees']*10000), round(Biomasses[each_year][each_species]['total_dead_basal']*10000,3), Biomasses[each_year][each_species]['wooddensity']]
                    
                    writer.writerow(new_row)

    def write_stand_ingrowth(self, Biomasses):
        filename_out = self.standid + "_stand_ingrowth_output.csv"
        with open(filename_out,'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            writer.writerow(['year','species','total_ingrowth_bio','total_ingrowth_jenkins','total_ingrowth_volume','total_ingrowth_trees','total_ingrowth_basal','wooddensity'])

            for each_year in Biomasses:
                for each_species in Biomasses[each_year]:
                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row = [each_year, each_species, round(Biomasses[each_year][each_species]['total_ingrowth_bio']*10000,3), round(Biomasses[each_year][each_species]['total_ingrowth_jenkins']*10000,3), round(Biomasses[each_year][each_species]['total_ingrowth_volume']*10000,3), int(Biomasses[each_year][each_species]['total_ingrowth_trees']*10000), round(Biomasses[each_year][each_species]['total_ingrowth_basal']*10000,3), Biomasses[each_year][each_species]['wooddensity']]
                    
                    writer.writerow(new_row)


if __name__ == "__main__":

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    pconn, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries

    # creates lookups for expansion factors
    XFACTOR = poptree_basis.Capture()

    #A = Stand(cur, pcur, XFACTOR, queries, 'CFMF')
    #import pdb; pdb.set_trace()
    test_stands = ['CFMF','AV06','WI01','NCNA']
    
    for each_stand in test_stands:
        
        A = Stand(cur, pcur, XFACTOR, queries, each_stand)
        
        BM = A.compute_normal_biomasses(XFACTOR)
        
        
        if BM == {}:
            Biomasses = A.compute_special_biomasses(XFACTOR)
            A.write_stand_live(Biomasses)
            A.write_stand_dead(Biomasses)
            A.write_stand_ingrowth(Biomasses)
            del Biomasses
    
        else: 
            A.write_stand_live(BM)
            A.write_stand_dead(BM)
            A.write_stand_ingrowth(BM)
        del BM    
        del A
        
        

    