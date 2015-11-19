#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import biomass_basis
import bisect
import csv
import os

class Stand(object):
    """Stands contain several plots, grouped by year and species. Stand produce outputs of biomass ( Mg/ha ), volume (m\ :sup:`3`), Jenkins biomass ( Mg/ha ), TPH (number of trees/ ha), and basal area (m\ :sup:`2` / ha).

    .. Example:

    >>> A = Stand(cur, pcur, XFACTOR, queries, 'NCNA')
    >>> A.cur = <pymssql.Cursor object at 0x1007a4648>
    >>> A.tree_list = "SELECT fsdbdata.dbo.tp00101.treeid, fsdbdata.dbo.tp00101.species..."
    >>> A.species_list = ""SELECT DISTINCT(fsdbdata.dbo.tp00101.species) from ..."
    >>> A.eqn_query = "SELECT SPECIES, EQNSET, FORM, H1, H2, H3, B1 ..."
    >>> A.eqns = {'abam': {'normal': <function Stand.select_eqns.<locals>.<lambda> at 0x1007d9730>}..."
    >>> A.od[1985]['abam'][4]['dead']
    >>> [('av06000400017', None, '6', '1985')]
    >>> A.od.keys()
    >>> dict_keys([1985, 1987, 1988, 2007, 1993, 1978, 1981, 1998, 1983])

    **INPUTS**

    :cur: the pymssql cursor object created by YamlConn
    :XFACTOR: instance of the Capture object for parameterization (see ``poptree_basis.py``)
    :queries: queries from ``qf_2.yaml``, created by YamlConn
    :standid: 4 character stand id, in lowercase.

    **RETURNS**

    An instance of the Stand object, which is used to do all plot, stand, and study level computations as well as output individual trees.

    .. note:: Stands have mortalities, additions, and replacements dictionaries for both of these within themselves. These are very helpful for checking errors in the study set-up.
 
    """
    def __init__(self, cur, XFACTOR, queries, standid):
        self.standid = standid
        self.cur = cur
        self.tree_list = queries['stand']['query']
        self.tree_list_m = queries['stand']['query_trees_m']
        self.species_list = queries['stand']['query_species']
        self.eqn_query = queries['tree']['sql_1tree_eqn']
        self.replacement_query = queries['stand']['query_replacements']
        self.numplot_query = queries['plot']['query_plot']
        self.eqns = {}
        self.od = {}
        self.woodden_dict ={}
        self.proxy_dict = {}
        self.component_dict = {}
        self.decent_years = []
        self.missings= {}
        self.mortalities ={}
        self.mort_replacements = {}
        self.total_area_ref = {}
        self.additions = {}
        self.replacements = {}
        self.num_plots = {}

        # get the total area for the stand - this dictionary is for the years when there is an actual inventory and not a mortality check
        self.get_total_area(XFACTOR)

        # get the appropriate equations, live trees, and dead trees for the stand
        self.select_eqns()

        # count the number of plots
        self.create_num_plots()

        # check if it is an addition; if is an addition, move to the subsequent year on that plot by creating self.replacements.
        self.check_additions_and_mort(XFACTOR)
        self.get_all_live_trees()
        self.get_all_dead_trees()

        # looks to the missing trees and matches their ids to live trees, assigns that dbh to the subsequent year.
        self.update_all_missing_trees()
        

    def create_num_plots(self):
        """ Creates a number of plots count for each stand and year. Uses a special query to the database to do this. Currently we use this for the stand composite output only.

        **INPUTS**

        No explicit inputs are needed.

        **RETURNS**

        :Capture.num_plots: the number of plots for that stand and year. Serves no purpose in computation and is only used to generated the required outputs. 
        """

        np = {}
        sql = self.numplot_query.format(standid = self.standid)
        self.cur.execute(sql)

        for row in self.cur:
            try: 
                year = int(row[0])
            except Exception:
                year = None

            try:
                plotid = str(row[1]).rstrip().lower()
            except Exception:
                plotid = "None"

            
            if year not in np:
                np[year] = [plotid]
            elif year in np:
                np[year].append(plotid)

        self.num_plots = {year:len(np[year]) for year in np.keys()}

    def select_eqns(self):
        """ Gets only the equations you need based on the species on that plot by querying the database for individual species that will be on this stand and makes an equation table.

        This is designed to limit the calls to the database and the amount of conditionals in the program. All trees on the stand are 'grouped' by species and then each group is mapped by the appropriate equation. Only the equations needed are used.

        **INPUTS**

        No explicit inputs are needed; this function is called automatically upon Stand creation.
        
        **RETURNS**

        Populates some of the Stands attributes:

        :list_species: a list of the species on that stand in any year, used to query the database for distinct species
        :self.woodden_dict: a dictionary of wood densities by species
        :self.proxy_dict: a dictionary of equation proxies, by species
        :self.eqns: a dictionary of eqns keyed by 'normal', 'big', or 'component' containing lambda functions to receive dbh (in cm) inputs and compute Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins' Biomass ( Mg ), and wood density.

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

                if each_species not in self.woodden_dict:
                    self.woodden_dict[each_species] = woodden
                else:
                    pass

                try:
                    proxy = str(row[12]).strip().lower()
                except Exception:
                    proxy = "None"

                if each_species not in self.proxy_dict:
                    self.proxy_dict[each_species] = proxy
                else:
                    pass


                try:
                    component = str(row[13]).strip().lower()
                except Exception:
                    component = "None"

                if each_species not in self.component_dict:
                    self.component_dict[each_species] = component
                else:
                    pass

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

                if each_species != "segi":
                    this_eqn = lambda x : biomass_basis.which_fx(form)(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                elif each_species == "segi":
                    this_eqn = lambda x : biomass_basis.which_fx('segi_biopak')(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)

                if each_species not in self.eqns:
                    self.eqns.update({each_species:{str(row[1]).rstrip().lower():this_eqn}})
                
                elif each_species in self.eqns:
                    # when there are 2 or more sizes
                    self.eqns[each_species].update({str(row[1]).rstrip().lower():this_eqn})

    
    def check_additions_and_mort(self, XFACTOR):
        """ Check if the stand may contain "additions". If so, replace the year with the subsequent year as long as it is not also additions or mortality. If additions or mortality is the final years in the data, we will not do those years. 

        For example, if addition happens in 1981 and last good remeasurement was in 1978, trees get 1978 if alive.

        Also, check if the stand contains "mortalities". If so, replace the year with the previous year as long as it is not also additions or mortality. If this is the final year in the data, do not do this year.

        For example, if mortality happens in 2004 and last remeasurement was 2010, trees roll to 2010 if dead. DBH is carried over from previous measurment.

        **INPUTS**

        :XFACTOR: passed inherently, uses its additions and mortalities attributes to determine the shifting of the years to fit the data.

        **RETURNS**

        Fixes additions and mortalities by replacing their years with a proxy year in remeasurements.

        """

        if self.standid.lower() in XFACTOR.additions.keys():
            # store the additions for when you analyze
            self.additions = XFACTOR.additions[self.standid]
            
            # get the years in which there are additions
            additions_years = sorted(list(XFACTOR.additions[self.standid].keys()))

        else:
            additions_years = []

        if self.standid.lower() in XFACTOR.mortalities.keys():
            # store mortalities 
            self.mortalities = XFACTOR.mortalities[self.standid]
            mortality_years = sorted(list(XFACTOR.mortalities[self.standid].keys()))
        else:
            mortality_years = []


        # execute a search for all good years from sql (years of E or R)
        self.cur.execute(self.replacement_query.format(standid=self.standid))

        # the years returned from the sql are not the additions or mort years (just r years)
        decent_years = []
        
        for row in self.cur:
            decent_years.append(int(row[0]))

        self.decent_years = sorted(decent_years)

        # each additions year is replaced by a correct year from the table and the replacements table is updated. 
        if additions_years != []:
            for each_year in additions_years:
                
                try:
                    if each_year not in self.decent_years:
                        # bisect left marks the left token in case you are checking for a value already in the list so subtract 1.
                        index = bisect.bisect_left(self.decent_years, each_year)-1
                    elif each_year in self.decent_years:
                        index = bisect.bisect_left(self.decent_years, each_year)
                    
                    replacement_year = self.decent_years[index]
                    plots_applied_to = XFACTOR.additions[self.standid][each_year]
                    self.replacements.update({each_year:{'replacement_year': replacement_year, 'plots': plots_applied_to}})
                
                except Exception:
                    print("exception thrown while trying to list replacement years")
                    import pdb; pdb.set_trace()
        else:
            pass

        # each mortality year is replaced by a correct year from the table and the mort_replacements plots are given
        if mortality_years != []:

            # if all the mortality years happen AFTER the last year of remeasurements, then purge the system of self.mortalities and also purge mortality_years
            if sorted(mortality_years)[0] > self.decent_years[-1]:
                self.mortalities = {}
                mortality_years = []
            
            for each_year in mortality_years:
                try:
                    index = bisect.bisect_right(self.decent_years, each_year)
                    replacement_year = self.decent_years[index]
                    plots_applied_to = XFACTOR.mortalities[self.standid][each_year]
                    self.mort_replacements.update({each_year:{'replacement_year': replacement_year, 'plots': plots_applied_to}})
                
                except Exception:
                    if each_year > self.decent_years[-1]:
                        pass
                    #import pdb; pdb.set_trace()


    def get_total_area(self, XFACTOR):
        """ Get the total area for each year on that stand and create a reference table to be used when figuring out the per hectare output. The percent of area on the plot over the percent of the area of the stand is the proportion represented by that plot.

        .. Example:

        >>> XFACTOR.total_areas['hr03']
        >>> {1984: 10000.0, 1985: 10000.0, 1986: 10000.0, 1988: 10000.0, 1989: 10000.0, 2000: 10000.0, 2007: 10000.0}

        **INPUTS**

        :XFACTOR: An instance of the Capture object used here to know the area of the stand.

        **RETURNS**

        The area of the stand, as a float. If not, 0.

        """

        try:
            self.total_area_ref = XFACTOR.total_areas[self.standid]
        except Exception:
            self.total_area_ref = {None: 10000.0}

    def get_all_live_trees(self):
        """ Get the trees on that stand by querying FSDBDATA and sort them by year, plot, live or dead, and species. 

        Queries both the live trees and the dead trees in the live database who do not have a DBH given. The dead trees then come in and replace the live ones without the DBH's in get_all_dead_trees(). First get the live from self.tree_list. 

        
        **INPUTS**

        No explicit inputs are needed.

        **RETURNS**

        This function gathers all the live trees from FSDBDATA.dbo.TP00102.

        .. note:: ingrowth is included in "live" (live statuses are all but "6" and "9"), but ingrowth is exclusive when status is "2"

        """
        self.cur.execute(self.tree_list.format(standid=self.standid))
        
        for row in self.cur:
            try:
                year = int(row[6])
            except Exception:
                year = None

            try:
                plotid = str(row[3]).rstrip().lower()
            except Exception:
                plotid = "None"

            try:
                species = str(row[1]).strip().lower()
                if species == "acci":
                    continue
                else:
                    pass
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
                dbh_code = str(row[7]).strip()
            except Exception:
                dbh_code = None


            # if the additions are not blank... 
            if self.additions != {}:
                
                # if the tree is in an additions year, roll it back to where it belongs
                if year in self.additions.keys() and plotid in self.additions[year]:
                    new_year = self.replacements[year]['replacement_year']
                    year = new_year
                else:
                    pass
            else:
                pass

            # if the tree is dead we need to get its dbh from elsewhere
            if self.mortalities != {} and status == "6":

                # if the tree is dead and is in a mortality year, go ahead and roll it forward.
                if year in self.mortalities.keys() and plotid in self.mortalities[year]:
                    try:
                        new_year = self.mort_replacements[year]['replacement_year']
                        year = new_year
                    except Exception:
                        #print("the mortality check in " + str(year) + " follows the last remeasurement, and has not yet been included in the data")
                        pass
                else:
                    pass

            # if the tree is missing we'll add it to the missing table. Then, after we've loaded in all the regular trees, we'll update the live table with a replicate of the last tree that was not missing with the same id, but in this new year.
            if status in ["9"]:

                if year not in self.missings:
                    self.missings[year] = {species:{plotid:[tid]}}
                elif year in self.missings:
                    if species not in self.missings[year]:
                        self.missings[year][species] = {plotid:[tid]}
                    elif species in self.missings[year]:
                        if plotid not in self.missings[year][species]:
                            self.missings[year][species][plotid] = [tid]
                        elif plotid in self.missings[year][species]:
                            self.missings[year][species][plotid].append(tid)
            else:
                pass

            if year not in self.od and status in ["6"]:

                self.od[year]={species:{plotid: {'live': {}, 'ingrowth': {}, 'dead': {tid: (dbh, status, dbh_code)}}}}
            
            elif year not in self.od and status not in ["6"]:
                self.od[year]={species: {plotid: {'live': {tid: (dbh, status, dbh_code)}, 'ingrowth': {}, 'dead': {}}}}

                if status == "2":
                    self.od[year][species][plotid]['ingrowth'].update({tid: (dbh, status, dbh_code)})
                else:
                    pass

            elif year in self.od:

                if species not in self.od[year] and status in ["6"]:
                    self.od[year][species] ={plotid: {'live': {}, 'ingrowth': {}, 'dead': {tid: (dbh, status, dbh_code)}}}
                    
                elif species not in self.od[year] and status not in ["6"]: 
                    self.od[year][species] ={plotid: {'live': {tid: (dbh, status, dbh_code)}, 'ingrowth': {}, 'dead': {}}}

                    if status == "2":
                        self.od[year][species][plotid]['ingrowth'].update({tid: (dbh, status, dbh_code)})
                    else:
                        pass

                elif species in self.od[year]:
                    
                    if status in ["6"] and plotid not in self.od[year][species]:
                        self.od[year][species][plotid] = {'dead': {tid: (dbh, status, dbh_code)}, 'live': {}, 'ingrowth': {}}
                    
                    elif status not in ["6"] and plotid not in self.od[year][species]:
                        self.od[year][species][plotid] = {'live': {tid: (dbh, status, dbh_code)}, 'dead': {}, 'ingrowth': {}}
                        
                        if status == "2":
                            self.od[year][species][plotid]['ingrowth'].update({tid: (dbh, status, dbh_code)})
                        else:
                            pass

                    elif status not in ["6"] and plotid in self.od[year][species]:
                        
                        self.od[year][species][plotid]['live'].update({tid: (dbh, status, dbh_code)})
                        
                        if status == "2":
                            self.od[year][species][plotid]['ingrowth'].update({tid: (dbh, status, dbh_code)})
                        else:
                            pass

                    elif status in ["6"] and plotid in self.od[year][species][plotid]['dead']:
                        self.od[year][species][plotid]['dead'].update({tid: (dbh, status, dbh_code)})


    def get_all_dead_trees(self):
        """ Gets all the dead trees from TP00103. Updates self.od, which was made in get_all_live_trees().

        **INPUTS**

        No explicit inputs are needed.

        **RETURNS**

        Gathers all the dead trees and data from FSDBDATA.dbo.TP00103.
        """

        self.cur.execute(self.tree_list_m.format(standid=self.standid))
        
        for row in self.cur:
            try:
                year = int(row[5])
            except Exception:
                if str(row[5]) == "None":
                    continue

            try:
                plotid = str(row[3]).rstrip().lower()
            except Exception:
                plotid = "None"

            try:
                species = str(row[1]).strip().lower()
            except Exception:
                species = None

            try:
                dbh = round(float(row[4]), 3)
            except Exception:
                dbh = None
                import pdb; pdb.set_trace()

            # all status are 6
            status = "6"

            try:
                tid = str(row[0]).strip().lower()
            except Exception:
                tid = "None"

            dbh_code = "M"

            if self.mortalities != {}:

                # if the tree is in a mortality year, go ahead and roll it forward to the next real inventory
                if year in self.mortalities.keys() and plotid in self.mortalities[year]:

                    try:
                        new_year = self.mort_replacements[year]['replacement_year']
                        year = new_year
                    except Exception:
                        pass
                else:
                    pass


            if year not in self.od:
                self.od[year] = {species: {plotid: {'live': {}, 'ingrowth': {}, 'dead': {tid: (dbh, status, dbh_code)}}}}

            elif year in self.od:
                if species not in self.od[year]:
                    self.od[year][species] ={plotid: {'live': {}, 'ingrowth': {}, 'dead': {tid: ( dbh, status, dbh_code)}}}

                elif species in self.od[year]:
                    if plotid not in self.od[year][species]:
                        self.od[year][species][plotid] = {'dead': {tid: (dbh, status, dbh_code)}, 'live': {}, 'ingrowth': {}}
                
                    elif plotid in self.od[year][species]:   
                        self.od[year][species][plotid]['dead'].update({tid: (dbh, status, dbh_code)})

    def update_all_missing_trees(self):
        """ Get the missing trees from self.missing and try to match each to a tree in the main dictionary that is alive in the preceding year from self.decent_years, and then return a copy of that tree to the year it is missing, so we can compute its biomass. Trees were assigned here when pulled in from live. Because all trees are there now, we can roll the dbh from the appropriate last good measurement into this new year. The assumption is that all trees not known dead are considered alive.

        **INPUTS**

        No explicit inputs are needed.

        **RETURNS**

        This function updates the missing trees so that they are viewed as alive and with a dbh. It is actually fairly hard to manage as many trees have been missing for a good long time. If a tree ID can't be found, check it through ``tps_Tree`` and if it has many `9` status, you'll want to modify this script to help you catch those statuses and replace them.

        """

        for each_year in self.missings:

            replacement_year_index = bisect.bisect_left(self.decent_years, each_year) - 1
            replacement_year = self.decent_years[replacement_year_index]

            for each_species in self.missings[each_year].keys():
                for each_plot in self.missings[each_year][each_species].keys():

                    for each_treeid in self.missings[each_year][each_species][each_plot]:

                        try:
                            replacement_tree_dbh = self.od[replacement_year][each_species][each_plot]['live'][each_treeid][0]
                        except Exception:
                            try:
                                # if it has been missing for more than 1 year
                                replacement_year = self.decent_years[replacement_year_index-1]
                                replacement_tree_dbh = self.od[replacement_year][each_species][each_plot]['live'][each_treeid][0]
                            except Exception:
                                try:
                                    # one more year back
                                    replacement_year_index = bisect.bisect_left(self.decent_years, each_year) - 2
                                    replacement_year = self.decent_years[replacement_year_index]
                                    replacement_tree_dbh = self.od[replacement_year][each_species][each_plot]['live'][each_treeid][0]
                                except Exception:
                                    try:
                                        replacement_year_index = bisect.bisect_left(self.decent_years, each_year) - 3
                                        replacement_year = self.decent_years[replacement_year_index]
                                        replacement_tree_dbh = self.od[replacement_year][each_species][each_plot]['live'][each_treeid][0]
                                    except Exception:
                                        try:
                                            replacement_year_index = bisect.bisect_left(self.decent_years, each_year) - 4
                                            replacement_year = self.decent_years[replacement_year_index]
                                            replacement_tree_dbh = self.od[replacement_year][each_species][each_plot]['live'][each_treeid][0]
                                        except Exception:
                                            print("cannot find a match for the missing tree: " + each_treeid + " -- tested up to four intervals preceding " + each_year + "check the fsdb!")
                                            continue

                        # this tree should have a dbh but also a status of '9' and 'M'
                        adjusted_replacement_tree_tuple = (replacement_tree_dbh, '9', 'M')

                        # update the main database with a replica of this tree for the missing one
                        self.od[each_year][each_species][each_plot]['live'].update({each_treeid: adjusted_replacement_tree_tuple})

                        
    def compute_biomasses(self, XFACTOR):
        """ Compute the number of trees per Hectare (TPHA), Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg and Mg/Ha ), Volume ( m\ :sup:`3` ), and Basal Area ( m\ :sup:`2` ); can be used for stands with weird minimums, detail plots, or areas that are not 625 m. If a match to one of the unusual attributes of XFACTOR is not found, it is assumed the minimum is 15.0, the plot is not detail, and the area is 625. Most plots match on at least one category, though.

        This function uses the Capture object to tell if a fancy computation (i.e. get a special area, minimum, etc. needs to be performed.
            Load in the appropriate parameters for this computation. Separate "small" trees from "large" ones so that small ones can get the expansion factor. If they aren't on a detail plot, this number will just be "1".)

        **INPUTS**

        :XFACTOR: a Capture object containing the detail plots, minimum dbhs, etc.
        
        **RETURNS**
        
        :Biomasses: a species-separated, stand-scale composite of biomasses that are needed for the final output.
        """

        Biomasses = {}
        BadTreeRef = {}
        Rob_Biomasses = {}
        
        try:
            all_years = sorted(self.od.keys())
        except Exception:
            all_years = sorted([x for x in self.od.keys() if x != None])
        
        for index, each_year in enumerate(all_years):

            try:
                num_plots = self.num_plots[each_year]
            except Exception: 
                num_plots = 16.0

            try:
                
                total_area = self.total_area_ref[each_year]
            
            except Exception:
                
                try:
                    # get most recent similar year
                    total_area = self.total_area_ref[all_years[index-1]]
                
                except Exception:
                    try:
                        # get most recent year
                        total_area = self.total_area_ref[all_years[-1]]
                    except Exception:
                        try:
                            # get the first year
                            total_area = self.total_area_ref[all_years[0]]
                        except Exception:
                            
                            print("total area could not be found, defaulting to 10000m")
                            total_area = 10000.


            for each_species in self.od[each_year].keys():
                
                for each_plot in self.od[each_year][each_species].keys():

                    # try to find the plot in the unusual mins reference
                    try:
                        mindbh = XFACTOR.umins_reference[self.standid][each_year][each_plot]
                    except KeyError as exc:
                        mindbh = 15.0

                    # try to find the plot in the unusual areas reference
                    try:
                        area = XFACTOR.uplot_areas[self.standid][each_plot][each_year]
                    except KeyError as exc:
                        area = 625.

                    # test if the plot is a detail plot
                    if self.standid not in XFACTOR.detail_reference.keys():
                        Xw = 1.0
                    
                    else:
                        try:
                            Xw = XFACTOR.expansion[self.standid][each_year]
                        except Exception:
                            Xw = 1.0
                        try:
                            mindbh = XFACTOR.detail_reference[self.standid][each_year][each_plot]['min']
                        except Exception:
                            mindbh = 5.0
                        try:
                            area = XFACTOR.detail_reference[self.standid][each_year][each_plot]['area']
                        except Exception:
                            area = 625.

                    # figure out the representative percentage of all the area of the stand that this plot represents in the given year

                    # if the area is 0. and the total_area is 0.
                    if area == 0. and total_area == 0.:
                        area = 10000.
                        total_area = 10000.

                        print("area for " + each_plot + " in the database for " + str(each_year) + " is 0")
                        print("area for " + self.standid + " in the database for " + str(each_year) + " is 0")
                    
                    # if the area is 0. but the total area isn't 0.
                    elif area == 0. and total_area != 0.:
                        area = 625.
                        print("area for " + each_plot + " in the database for " + str(each_year) + " is 0")
                    
                    # if the total_area is 0. but the area is not 0.
                    elif total_area == 0. and area != 0.:
                        total_area = 10000.
                        print("area for " + self.standid + " in the database for " + str(each_year) + " is 0")

                    try:
                        percent_area_of_total = area/total_area  
                    
                    except ZeroDivisionError:
                        print("area for " + self.standid + " in the database for " + str(each_year) + " is 0")
                        total_area = 10000. 
                        percent_area_of_total = area/total_area

                    if total_area == None:
                        print("area for " + self.standid + " in the database for " + str(each_year) + " is null")
                        total_area = 10000.
                        percent_area_of_total = area/total_area
                    else:
                        pass                

                    try:
                        large_dead_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] >= 15.0}
                    except Exception:
                        large_dead_trees = {k: {'bio': self.eqns[each_species]['normal'](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] >= 15.0}

                    small_dead_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}

                    try:
                        large_live_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] >= 15.0}
                    except Exception:
                        large_live_trees = {k: {'bio': self.eqns[each_species]['normal'](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] >= 15.0}

                    small_live_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}

                    try:
                        large_ingrowth_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] >= 15.0}
                    except Exception:
                        large_ingrowth_trees = {k: {'bio': self.eqns[each_species]['normal'](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] >= 15.0}
                    
                    small_ingrowth_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}
                    
                    bad_dead_trees = [k for k in self.od[each_year][each_species][each_plot]['dead'].keys() if self.od[each_year][each_species][each_plot]['dead'][k] == None]
                    
                    bad_live_trees = [k for k in self.od[each_year][each_species][each_plot]['live'].keys() if self.od[each_year][each_species][each_plot]['live'][k] == None]
                    
                    bad_ingrowth_trees = [k for k in self.od[each_year][each_species][each_plot]['ingrowth'].keys() if self.od[each_year][each_species][each_plot]['ingrowth'][k] == None]

                    # write the "bad trees" to a reference
                    if bad_dead_trees == [] and bad_live_trees == [] and bad_ingrowth_trees ==[]:
                        pass
                    else: 
                        if each_year not in BadTreeRef:
                            BadTreeRef[each_year] = {each_species:{each_plot: {'dead': bad_dead_trees, 'live': bad_live_trees, 'ingrowth': bad_ingrowth_trees}}}
                        elif each_year in BadTreeRef:
                            if each_species not in BadTreeRef[each_year]:
                                BadTreeRef[each_year][each_species] = {each_plot:{'dead': bad_dead_trees, 'live': bad_live_trees, 'ingrowth': bad_ingrowth_trees}}
                            elif each_species in BadTreeRef[each_year]:
                                if each_plot not in BadTreeRef[each_year][each_species]:
                                    BadTreeRef[each_year][each_species][each_plot] = {'dead': bad_dead_trees, 'live': bad_live_trees, 'ingrowth': bad_ingrowth_trees}
                                elif each_plot in BadTreeRef[each_year][each_species]:
                                    BadTreeRef[each_year][each_species][each_plot]['dead'] += bad_dead_trees
                                    BadTreeRef[each_year][each_species][each_plot]['live'] += bad_live_trees
                                    BadTreeRef[each_year][each_species][each_plot]['ingrowth'] += bad_ingrowth_trees
                    
                    # count the number of total dead, live, and ingrowth trees. Divide by area to get the number of trees per unit area
                    try:
                        total_dead_trees = (len(large_dead_trees)/area + len(small_dead_trees)*Xw/area)*percent_area_of_total
                    except Exception:
                        total_dead_trees = 0.

                    try:
                        total_live_trees = (len(large_live_trees)/area + len(small_live_trees)*Xw/area)*percent_area_of_total
                    except Exception:
                        total_live_trees = 0.

                    try:
                        total_ingrowth_trees = (len(large_ingrowth_trees)/area + len(small_ingrowth_trees)/area*Xw)*percent_area_of_total
                    except Exception:
                        total_ingrowth_trees = 0.

                    # compute the total "rob trees" which are only those > 15 cm
                    # count the number of total dead, live, and ingrowth trees.
                    try:
                        rob_total_dead_trees = len(large_dead_trees)/area 
                    except Exception:
                        rob_total_dead_trees = 0.

                    try:
                        rob_total_live_trees = len(large_live_trees)/area
                    except Exception:
                        rob_total_live_trees = 0.

                    try:
                        rob_total_ingrowth_trees = len(large_ingrowth_trees)/area
                    except Exception:
                        rob_total_ingrowth_trees = 0.


                    # compute the totals at the stand level, divide by area to get the area for each of the plots, multiply by the percent area of the total
                    total_live_bio = (sum([large_live_trees[tree]['bio'][0]/area for tree in large_live_trees.keys()]) + sum([(small_live_trees[tree]['bio'][0]/area)*Xw for tree in small_live_trees.keys()]))*percent_area_of_total
                    total_ingrowth_bio = (sum([large_ingrowth_trees[tree]['bio'][0]/area for tree in large_ingrowth_trees.keys()])+ sum([(small_ingrowth_trees[tree]['bio'][0]/area)*Xw for tree in small_ingrowth_trees.keys()]))* percent_area_of_total
                    total_dead_bio = (sum([large_dead_trees[tree]['bio'][0]/area for tree in large_dead_trees.keys()]) + sum([(small_dead_trees[tree]['bio'][0]/area)*Xw for tree in small_dead_trees.keys()]))* percent_area_of_total

                    rob_total_live_bio = (sum([large_live_trees[tree]['bio'][0]/area for tree in large_live_trees.keys()]))*percent_area_of_total
                    rob_total_ingrowth_bio = (sum([large_ingrowth_trees[tree]['bio'][0]/area for tree in large_ingrowth_trees.keys()]))*percent_area_of_total
                    rob_total_dead_bio = (sum([large_dead_trees[tree]['bio'][0]/area for tree in large_dead_trees.keys()]))*percent_area_of_total

                    
                    total_live_jenkins = (sum([large_live_trees[tree]['bio'][2]/area for tree in large_live_trees.keys()]) + sum([(small_live_trees[tree]['bio'][2]/area)*Xw for tree in small_live_trees.keys()])) * percent_area_of_total
                    total_ingrowth_jenkins = (sum([large_ingrowth_trees[tree]['bio'][2]/area for tree in large_ingrowth_trees.keys()])  + sum([(small_ingrowth_trees[tree]['bio'][2]/area)*Xw for tree in small_ingrowth_trees.keys()])) * percent_area_of_total
                    total_dead_jenkins = (sum([large_dead_trees[tree]['bio'][2]/area for tree in large_dead_trees.keys()]) + sum([(small_dead_trees[tree]['bio'][2]/area)*Xw for tree in small_dead_trees.keys()])) * percent_area_of_total

                    rob_total_live_jenkins = (sum([large_live_trees[tree]['bio'][2]/area for tree in large_live_trees.keys()]))*percent_area_of_total
                    rob_total_ingrowth_jenkins = (sum([large_ingrowth_trees[tree]['bio'][2]/area for tree in large_ingrowth_trees.keys()]))*percent_area_of_total
                    rob_total_dead_jenkins = (sum([large_dead_trees[tree]['bio'][2]/area for tree in large_dead_trees.keys()]))*percent_area_of_total

                    total_live_volume = (sum([large_live_trees[tree]['bio'][1]/area for tree in large_live_trees.keys()])  + sum([(small_live_trees[tree]['bio'][1]/area)*Xw for tree in small_live_trees.keys()])) * percent_area_of_total
                    total_ingrowth_volume = (sum([large_ingrowth_trees[tree]['bio'][1]/area for tree in large_ingrowth_trees.keys()]) + sum([(small_ingrowth_trees[tree]['bio'][1]/area)*Xw for tree in small_ingrowth_trees.keys()])) * percent_area_of_total
                    total_dead_volume = (sum([large_dead_trees[tree]['bio'][1]/area for tree in large_dead_trees.keys()]) + sum([(small_dead_trees[tree]['bio'][1]/area)*Xw for tree in small_dead_trees.keys()])) * percent_area_of_total

                    rob_total_live_volume = (sum([large_live_trees[tree]['bio'][1]/area for tree in large_live_trees.keys()]))*percent_area_of_total
                    rob_total_ingrowth_volume = (sum([large_ingrowth_trees[tree]['bio'][1]/area for tree in large_ingrowth_trees.keys()]))*percent_area_of_total
                    rob_total_dead_volume = (sum([large_dead_trees[tree]['bio'][1]/area for tree in large_dead_trees.keys()]))*percent_area_of_total

                    total_live_basal = (sum([large_live_trees[tree]['ba']/area for tree in large_live_trees.keys()]) + sum([(small_live_trees[tree]['ba']/area)*Xw for tree in small_live_trees.keys()])) * percent_area_of_total
                    total_ingrowth_basal = (sum([large_ingrowth_trees[tree]['ba']/area for tree in large_ingrowth_trees.keys()])+  sum([(small_ingrowth_trees[tree]['ba']/area)*Xw for tree in small_ingrowth_trees.keys()])) * percent_area_of_total
                    total_dead_basal = (sum([large_dead_trees[tree]['ba']/area for tree in large_dead_trees.keys()]) + sum([(small_dead_trees[tree]['ba']/area)*Xw for tree in small_dead_trees.keys()])) * percent_area_of_total

                    rob_total_live_basal = (sum([large_live_trees[tree]['ba']/area for tree in large_live_trees.keys()]))*percent_area_of_total
                    rob_total_ingrowth_basal = (sum([large_ingrowth_trees[tree]['ba']/area for tree in large_ingrowth_trees.keys()]))*percent_area_of_total
                    rob_total_dead_basal = (sum([large_dead_trees[tree]['ba']/area for tree in large_dead_trees.keys()]))*percent_area_of_total
                        

                    # get a list of tree names for checking
                    living_trees = list(large_live_trees) + list(small_live_trees)
                    ingrowth_trees = list(large_ingrowth_trees) + list(small_ingrowth_trees)
                    dead_trees = list(large_dead_trees) + list(small_dead_trees)

                    if each_year not in Biomasses:
                        Biomasses[each_year] = {each_species : {'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'total_live_basal': total_live_basal, 'name_live': living_trees, 'name_mort': dead_trees, 'total_ingrowth_basal': total_ingrowth_basal, 'total_dead_basal': total_dead_basal,  'name_ingrowth': ingrowth_trees, 'num_plots': num_plots}}
                    

                    elif each_year in Biomasses:
                        # do not need to augment the wood density :) -> but do make sure it is in here
                        if each_species not in Biomasses[each_year]:
                            Biomasses[each_year][each_species]={'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'total_live_basal': total_live_basal, 'total_dead_basal': total_dead_basal, 'name_live': living_trees, 'total_ingrowth_basal': total_ingrowth_basal, 'name_mort': dead_trees,'name_ingrowth': ingrowth_trees, 'num_plots':num_plots}
                        
                        # don't need to augment the wood density - one time is enough! - this is adding in each of the plots, which are already on area basis
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
                            Biomasses[each_year][each_species]['name_live'] += living_trees
                            Biomasses[each_year][each_species]['name_mort'] += dead_trees
                            Biomasses[each_year][each_species]['name_ingrowth'] += ingrowth_trees
                            Biomasses[each_year][each_species]['total_live_basal']+=total_live_basal
                            Biomasses[each_year][each_species]['total_dead_basal']+=total_dead_basal
                            Biomasses[each_year][each_species]['total_ingrowth_basal']+=total_ingrowth_basal
                            Biomasses[each_year][each_species]['num_plots'] = num_plots
                        else:
                            pass


                    # do the same for rob bio
                    if each_year not in Rob_Biomasses:
                        Rob_Biomasses[each_year] = {each_species : {'total_live_bio': rob_total_live_bio, 'total_dead_bio' : rob_total_dead_bio, 'total_ingrowth_bio': rob_total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': rob_total_ingrowth_jenkins, 'total_dead_jenkins' : rob_total_dead_jenkins, 'total_live_volume' : rob_total_live_volume, 'total_dead_volume' : rob_total_dead_volume, 'total_ingrowth_volume': rob_total_ingrowth_volume, 'total_live_trees': rob_total_live_trees, 'total_dead_trees': rob_total_dead_trees, 'total_ingrowth_trees': rob_total_ingrowth_trees, 'total_live_basal': rob_total_live_basal, 'total_ingrowth_basal': rob_total_ingrowth_basal, 'total_dead_basal': rob_total_dead_basal, 'num_plots': num_plots}}
                    

                    elif each_year in Rob_Biomasses:
                        # do not need to augment the wood density :) -> but do make sure it is in here
                        if each_species not in Rob_Biomasses[each_year]:
                            Rob_Biomasses[each_year][each_species]={'total_live_bio': rob_total_live_bio, 'total_dead_bio' : rob_total_dead_bio, 'total_ingrowth_bio': rob_total_ingrowth_bio, 'total_live_jenkins': rob_total_live_jenkins, 'total_ingrowth_jenkins': rob_total_ingrowth_jenkins, 'total_dead_jenkins' : rob_total_dead_jenkins, 'total_live_volume' : rob_total_live_volume, 'total_dead_volume' : rob_total_dead_volume, 'total_ingrowth_volume': rob_total_ingrowth_volume, 'total_live_trees': rob_total_live_trees, 'total_dead_trees': rob_total_dead_trees, 'total_ingrowth_trees': rob_total_ingrowth_trees, 'total_live_basal':rob_total_live_basal, 'total_dead_basal': rob_total_dead_basal,  'total_ingrowth_basal': rob_total_ingrowth_basal, 'num_plots':num_plots}
                        
                        # don't need to augment the wood density - one time is enough! - this is adding in each of the plots, which are already on area basis
                        elif each_species in Rob_Biomasses[each_year]:
                            Rob_Biomasses[each_year][each_species]['total_live_bio'] += rob_total_live_bio
                            Rob_Biomasses[each_year][each_species]['total_dead_bio'] += rob_total_dead_bio
                            Rob_Biomasses[each_year][each_species]['total_ingrowth_bio'] += rob_total_ingrowth_bio
                            Rob_Biomasses[each_year][each_species]['total_live_jenkins'] +=rob_total_live_jenkins
                            Rob_Biomasses[each_year][each_species]['total_ingrowth_jenkins'] += rob_total_ingrowth_jenkins
                            Rob_Biomasses[each_year][each_species]['total_dead_jenkins'] += rob_total_dead_jenkins
                            Rob_Biomasses[each_year][each_species]['total_live_volume'] += rob_total_live_volume
                            Rob_Biomasses[each_year][each_species]['total_dead_volume'] += rob_total_dead_volume
                            Rob_Biomasses[each_year][each_species]['total_ingrowth_volume'] += rob_total_ingrowth_volume
                            Rob_Biomasses[each_year][each_species]['total_live_trees'] += rob_total_live_trees
                            Rob_Biomasses[each_year][each_species]['total_dead_trees'] += rob_total_dead_trees 
                            Rob_Biomasses[each_year][each_species]['total_ingrowth_trees'] += rob_total_ingrowth_trees
                            Rob_Biomasses[each_year][each_species]['total_live_basal']+=rob_total_live_basal
                            Rob_Biomasses[each_year][each_species]['total_dead_basal']+=rob_total_dead_basal
                            Rob_Biomasses[each_year][each_species]['total_ingrowth_basal']+=rob_total_ingrowth_basal
                            Rob_Biomasses[each_year][each_species]['num_plots'] = num_plots
                        else:
                            pass
        
        return Biomasses, BadTreeRef, Rob_Biomasses

    def aggregate_biomasses(self, Biomasses):
        """ For each year in biomasses, add up all the trees from all the species, and output the stand summary over all the species as a nearly identical data structure. 

        For every one of the attributes in Biomasses for Trees Per Hectare (TPHA), Biomass ( Mg ), Basal Area (m\ :sup:`2`),  Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), sum the values for the whole stand. These values are already normalized into the per meters squared version. When writing occurs, the aggregate is expanded to the hectare.

        **INPUTS**

        :Biomasses: the biomasses by species for a whole stand, separated into `live`, `dead`, and `ingrowth`.

        **RETURNS**

        :Biomasses_agg: the `all` biomass for the aggregate of all species on that stand in that year.

        """
        Biomasses_Agg = {}

        for each_year in sorted(Biomasses.keys()):

            if each_year not in Biomasses_Agg:

                Biomasses_Agg[each_year]= {'total_live_trees': sum([Biomasses[each_year][x]['total_live_trees'] for x in Biomasses[each_year].keys()]), 'total_dead_trees': sum([Biomasses[each_year][x]['total_dead_trees'] for x in Biomasses[each_year].keys()]), 'total_ingrowth_trees': sum([Biomasses[each_year][x]['total_ingrowth_trees'] for x in Biomasses[each_year].keys()]), 'total_live_basal': sum([Biomasses[each_year][x]['total_live_basal'] for x in Biomasses[each_year].keys()]), 'total_dead_basal': sum([Biomasses[each_year][x]['total_dead_basal'] for x in Biomasses[each_year].keys()]), 'total_ingrowth_basal': sum([Biomasses[each_year][x]['total_ingrowth_basal'] for x in Biomasses[each_year].keys()]), 'total_live_bio': sum([Biomasses[each_year][x]['total_live_bio'] for x in Biomasses[each_year].keys()]), 'total_dead_bio': sum([Biomasses[each_year][x]['total_dead_bio'] for x in Biomasses[each_year].keys()]), 'total_ingrowth_bio': sum([Biomasses[each_year][x]['total_ingrowth_bio'] for x in Biomasses[each_year].keys()]), 'total_live_volume': sum([Biomasses[each_year][x]['total_live_volume'] for x in Biomasses[each_year].keys()]), 'total_dead_volume': sum([Biomasses[each_year][x]['total_dead_volume'] for x in Biomasses[each_year].keys()]), 'total_ingrowth_volume': sum([Biomasses[each_year][x]['total_ingrowth_volume'] for x in Biomasses[each_year].keys()]), 'total_live_jenkins': sum([Biomasses[each_year][x]['total_live_jenkins'] for x in Biomasses[each_year].keys()]), 'total_dead_jenkins': sum([Biomasses[each_year][x]['total_dead_jenkins'] for x in Biomasses[each_year].keys()]), 'total_ingrowth_jenkins': sum([Biomasses[each_year][x]['total_ingrowth_jenkins'] for x in Biomasses[each_year].keys()])}

            elif each_year in Biomasses_Agg:
                print("the year has already been included in aggregate biomass- what's up on line 869?")

        return Biomasses_Agg

    def write_stand_rob(self, RobBiomass, XFACTOR, *args):
        """ quick little method that ignores all the detail plot (trees < 15.)

        .. note:: This is NOT a permanent script. It is here to help look at detail plots. It should not be considered final.
        """

        if args and args != []:
            filename_out = args[0]
            mode = args[1]
        else:
            dirout = "sample_output"
            filename_out = self.standid + "_stand_rob_output.csv"
            os.path.join(dirout, filename_out)
            mode = 'w'
            
        with open(filename_out,mode) as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            writer.writerow(['DBCODE','ENTITY','STANDID','SPECIES','YEAR','PORTION','TPH_NHA','BA_M2HA','VOL_M3HA','BIO_MGHA','JENKBIO_MGHA', 'NO_PLOTS'])

            for each_year in sorted(RobBiomass.keys()):

                num_plots = self.num_plots[each_year]

                for each_species in RobBiomass[each_year]:

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row_1 = ['TP001', '06', self.standid.upper(), each_species.upper(), each_year,'INGROWTH', math.ceil(RobBiomass[each_year][each_species]['total_ingrowth_trees']*10000), round(RobBiomass[each_year][each_species]['total_ingrowth_basal']*10000, 3), round(RobBiomass[each_year][each_species]['total_ingrowth_volume']*10000,3), round(RobBiomass[each_year][each_species]['total_ingrowth_bio']*10000,3), round(RobBiomass[each_year][each_species]['total_ingrowth_jenkins']*10000,3), num_plots]
                    
                    #writer.writerow(new_row)

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row_2 = ['TP001', '06', self.standid.upper(), each_species.upper(), each_year,'LIVE', math.ceil(RobBiomass[each_year][each_species]['total_live_trees']*10000), round(RobBiomass[each_year][each_species]['total_live_basal']*10000, 3), round(RobBiomass[each_year][each_species]['total_live_volume']*10000,3), round(RobBiomass[each_year][each_species]['total_live_bio']*10000,3), round(RobBiomass[each_year][each_species]['total_live_jenkins']*10000,3), num_plots]
                 
                    #writer.writerow(new_row)

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row_3 = ['TP001', '06', self.standid.upper(), each_species.upper(), each_year,'MORT', math.ceil(RobBiomass[each_year][each_species]['total_dead_trees']*10000), round(RobBiomass[each_year][each_species]['total_dead_basal']*10000, 3), round(RobBiomass[each_year][each_species]['total_dead_volume']*10000,3), round(RobBiomass[each_year][each_species]['total_dead_bio']*10000,3), round(RobBiomass[each_year][each_species]['total_dead_jenkins']*10000,3), num_plots]

                    writer.writerow(new_row_1)
                    writer.writerow(new_row_2)
                    writer.writerow(new_row_3)

    def write_stand_composite(self, Biomasses, Biomasses_Agg, XFACTOR, *args):
        """ Generates an output file which combines the Trees Per Hectare (TPH), Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins' Biomass ( Mg ), Basal Area (m \ :sup:`2`) by species with a row of "all" containing the composite TPH, Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins' Biomass ( Mg ), and Basal Area (m \ :sup:`2`)

        **INPUTS**

        :Biomasses: data structure containing portions of biomass and other desired outputs, grouped by species
        :Biomasses_Agg: data structure containing the aggregate biomass over all the species.
        :XFACTOR: the reference object used for computing areas and such. You've already created it. No worries.
        :args: two arguements, a csv filename and a mode of write or append

        If the mode is ``w`` for write, this will always over-write previous stands. If it is ``a`` for append, this will add to the last file. When doing many stands I suggest doing ``w`` for the first one and ``a`` for the rest. Understand though that if the program freezes up or you need to stop, if you start using ``a`` again, you will just append to the file you already made.  ``tps_cli`` handles this for you.

        **RETURNS**

        Writes a file named `standid + stand_composite_output.csv`. If you are running through ``tps_cli`` there is also an option of returning an ``all`` version
        """

        if args and args != []:
            filename_out = args[0]
            mode = args[1]
        else:

            dirout = "sample_output"
            filename_out = self.standid + "_stand_composite_output.csv"
            os.path.join(dirout, filename_out)
            mode = 'w'
        
        with open(filename_out,mode) as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            if mode == 'w':
                writer.writerow(['DBCODE','ENTITY','STANDID','SPECIES','YEAR','PORTION','TPH_NHA','BA_M2HA','VOL_M3HA','BIO_MGHA','JENKBIO_MGHA', 'NO_PLOTS'])
            else:
                pass

            for each_year in sorted(Biomasses.keys()):

                try:
                    num_plots = self.num_plots[each_year]
                except KeyError:
                    print("There are no activity years in TP00112 that correspond with the remeasurement of " + self.standid + " in " + str(each_year))
                    continue


                for each_species in Biomasses[each_year]:

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row_1 = ['TP001', '06', self.standid.upper(), each_species.upper(), each_year,'INGROWTH', math.ceil(Biomasses[each_year][each_species]['total_ingrowth_trees']*10000), round(Biomasses[each_year][each_species]['total_ingrowth_basal']*10000, 3), round(Biomasses[each_year][each_species]['total_ingrowth_volume']*10000,3), round(Biomasses[each_year][each_species]['total_ingrowth_bio']*10000,3), round(Biomasses[each_year][each_species]['total_ingrowth_jenkins']*10000,3), num_plots]
                    
                    #writer.writerow(new_row)

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row_2 = ['TP001', '06', self.standid.upper(), each_species.upper(), each_year,'LIVE', math.ceil(Biomasses[each_year][each_species]['total_live_trees']*10000), round(Biomasses[each_year][each_species]['total_live_basal']*10000, 3), round(Biomasses[each_year][each_species]['total_live_volume']*10000,3), round(Biomasses[each_year][each_species]['total_live_bio']*10000,3), round(Biomasses[each_year][each_species]['total_live_jenkins']*10000,3), num_plots]
                 
                    #writer.writerow(new_row)

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row_3 = ['TP001', '06', self.standid.upper(), each_species.upper(), each_year,'MORTALITY', math.ceil(Biomasses[each_year][each_species]['total_dead_trees']*10000), round(Biomasses[each_year][each_species]['total_dead_basal']*10000, 3), round(Biomasses[each_year][each_species]['total_dead_volume']*10000,3), round(Biomasses[each_year][each_species]['total_dead_bio']*10000,3), round(Biomasses[each_year][each_species]['total_dead_jenkins']*10000,3), num_plots]

                    writer.writerow(new_row_1)
                    writer.writerow(new_row_2)
                    writer.writerow(new_row_3)


            for each_year in sorted(Biomasses_Agg.keys()):

                # continue through a num_plots error because you may already have a value for num_plots that will suffice and the year may be mis-assigned
                try:
                    num_plots = self.num_plots[each_year]
                except KeyError:
                    print("There are no activity years in TP00112 that correspond with the remeasurement of " + self.standid + " in " + str(each_year))
                    continue

                # remember to multiply by 10000 to go from m2 to hectare
                new_row4 = ['TP001', '06', self.standid.upper(), 'ALL', each_year,'INGROWTH', math.ceil(Biomasses_Agg[each_year]['total_ingrowth_trees']*10000), round(Biomasses_Agg[each_year]['total_ingrowth_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_ingrowth_volume']*10000,3), round(Biomasses_Agg[each_year]['total_ingrowth_bio']*10000,3), round(Biomasses_Agg[each_year]['total_ingrowth_jenkins']*10000,3), num_plots]
                    

                new_row5 = ['TP001', '06', self.standid.upper(), 'ALL', each_year,'LIVE', math.ceil(Biomasses_Agg[each_year]['total_live_trees']*10000), round(Biomasses_Agg[each_year]['total_live_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_live_volume']*10000,3), round(Biomasses_Agg[each_year]['total_live_bio']*10000,3), round(Biomasses_Agg[each_year]['total_live_jenkins']*10000,3), num_plots]

                # remember to multiply by 10000 to go from m2 to hectare

                new_row6 = ['TP001', '06', self.standid.upper(), 'ALL', each_year,'MORTALITY', math.ceil(Biomasses_Agg[each_year]['total_dead_trees']*10000), round(Biomasses_Agg[each_year]['total_dead_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_dead_volume']*10000,3), round(Biomasses_Agg[each_year]['total_dead_bio']*10000,3), round(Biomasses_Agg[each_year]['total_dead_jenkins']*10000,3), num_plots]
                writer.writerow(new_row4)
                writer.writerow(new_row5)
                writer.writerow(new_row6)

    def write_individual_trees(self, *args):
        """ Writes a csv file, containing the tree measurements for the individual trees on the stand. File contains only the measurement attributes from the composite file; it does not contain "trees per hectare" because only one tree.

        **INPUTS**

        :args: is two command line args indicating the filename for output and the mode, either write or append

        When the first tree is run, we want to write the file. However, then we want to append because re-opening and writing would destroy the first one. The ``tps_cli`` interface handles this for you!

        **RETURNS**

        A csv file containing all the individual trees, or sets of csv files by aggregation level. This function is managed in ``tps_cli``.

        .. note: this method is faster than using `tps_Tree`. However, `tps_Tree` provides more detailed information. 
        """

        if args and args != []:
            filename_out = args[0]
            mode = args[1]
        else:

            dirout = "sample_output"
            filename_out = self.standid + "_stand_indvtree_output.csv"
            os.path.join(dirout, filename_out)
            mode = 'w'

        with open(filename_out, mode) as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            if mode == 'w':
                headers = ['DBCODE', 'ENTITY', 'TREEID', 'COMPONENT', 'YEAR', 'BA_M2', 'VOL_M3', 'BIO_MG', 'JENKBIO_MG']
                writer.writerow(headers)
            else: 
                pass


            for each_year in sorted([x for x in self.od.keys() if x != None]):

                for each_species in self.od[each_year].keys():

                    my_component = self.component_dict[each_species]
                    for each_plot in self.od[each_year][each_species].keys():

                        try:
                            live_trees= {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4), 'status': v[1]} for k,v in self.od[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] >= 5.0}
                        except Exception:
                            live_trees= {k: {'bio': self.eqns[each_species]['normal'](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4), 'status': v[1]} for k,v in self.od[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] >= 5.0}

                        try:
                            dead_trees= {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4), 'status': v[1]} for k,v in self.od[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] >= 5.0}
                        except Exception:
                            dead_trees= {k: {'bio': self.eqns[each_species]['normal'](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4), 'status': v[1]} for k,v in self.od[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] >= 5.0}

                        for each_tree in live_trees.keys():
                            writer.writerow(['TP001', '11', each_tree.upper(), my_component.upper(), each_year, live_trees[each_tree]['ba'], round(live_trees[each_tree]['bio'][1],4), live_trees[each_tree]['bio'][0], live_trees[each_tree]['bio'][2]])

                        for each_tree in dead_trees.keys():
                            writer.writerow(['TP001', '11', each_tree.upper(), my_component.upper(), each_year, dead_trees[each_tree]['ba'], round(dead_trees[each_tree]['bio'][1],4), dead_trees[each_tree]['bio'][0], dead_trees[each_tree]['bio'][2]])


class Plot(Stand):
    """ Most of the functions of plot are actually the same as stand, so why re-write the class?

    Plots contain a Stand from which they are extracted, and a plot list enumerating what plots are to be analyzed. Otherwise, all of the methods and outputs are virtually identical to that in Stand, but scaled down.

    :self.plotlist: is a list of plots for analysis. i.e. you could specify 3 plots of 40 total plots (like [ncna0001, ncna0002, ncna0003], 1 plot of 40 (like ncna0001), or no plots of 40 (**in this case, ALL the plots get computed**). 

    .. Warning: 
    You must always pass in an empty string for plotlist if you don't specify plots.

    .. code-block:: python

    >>> A = tps_Stand.Stand(cur, XFACTOR, queries, 'ncna')
    >>> K = tps_Stand.Plot(A, XFACTOR, [])
    """

    def __init__(self, Stand, XFACTOR, plotlist):
        self.Stand = Stand
        self.plotlist = plotlist


    def compute_biomasses_plot(self, XFACTOR):
        """ Compute the biomass ( Mg/ha ), volume (m\ :sup:`3`), Jenkins biomass ( Mg/ha ), TPH (number of trees/ ha), and basal area (m\ :sup:`2` / ha). Use at the plot scale, so no expansion factors are needed here. 

        **INPUTS**

        :XFACTOR: An instance of the Capture object used for parameterization.

        **RETURNS**

        :Biomasses: Biomasses by plot, separated into special groups such as `live`, `dead`, and `ingrowth` as well as into `biomass`, `basal`, `volume`, `Jenkins' biomass`, and `trees per hectare.`
        """

        # if the plotlist is in uppercase make lower case
        if self.plotlist != []:
            temporary_plotlist = [x[i].lower() for i,x in enumerate(self.plotlist)]
            self.plotlist = temporary_plotlist
            
        Biomasses = {}
        
        all_years = sorted([x for x in self.Stand.od.keys() if x != None])
        
        for index, each_year in enumerate(all_years):

            for each_species in self.Stand.od[each_year].keys():

                for each_plot in self.Stand.od[each_year][each_species].keys():

                    # so you can specify a plot or set of plots if you want - if it's empty we do all the plots, if not, we skip that plot we already have
                    if self.plotlist !=[] and each_plot.lower() not in self.plotlist:
                        continue
                    else:
                        pass

                    if self.Stand.standid not in XFACTOR.uplot_areas.keys():
                        total_area = 625.
                    
                    elif each_plot not in XFACTOR.uplot_areas[self.Stand.standid]:
                        total_area = 625.

                    else:
                        try:
                            total_area = XFACTOR.uplot_areas[self.Stand.standid][each_plot][each_year]
                        except Exception:
                            try:
                                total_area = XFACTOR.uplot_areas[self.Stand.standid][each_plot][all_years[index-1]]
                            except Exception:
                                print("exception thrown trying to get the plot area for " + each_plot + " in " + str(each_year))

                    # try to find the plot in the unusual mins reference
                    try:
                        mindbh = XFACTOR.umins_reference[self.Stand.standid][each_year][each_plot]
                    except KeyError as exc:
                        mindbh = 15.0

                    # try to find the plot in the unusual areas reference
                    try:
                        area = XFACTOR.uplot_areas[self.Stand.standid][each_plot][each_year]
                    except KeyError as exc:
                        area = 625.

                  
                    try:
                        large_dead_trees = {k: {'bio': self.Stand.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.Stand.od[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] >= 15.0}
                    except Exception:
                        large_dead_trees = {k: {'bio': self.Stand.eqns[each_species]['normal'](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.Stand.od[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] >= 15.0}
                    
                    small_dead_trees = {k: {'bio': self.Stand.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.Stand.od[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}

                    try:
                        large_live_trees = {k: {'bio': self.Stand.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.Stand.od[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] >= 15.0}
                    except Exception:
                        large_live_trees = {k: {'bio': self.Stand.eqns[each_species]['normal'](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.Stand.od[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] >= 15.0}
                    
                    small_live_trees = {k: {'bio': self.Stand.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.Stand.od[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}

                    try:
                        large_ingrowth_trees = {k: {'bio': self.Stand.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.Stand.od[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] >= 15.0}
                    except Exception:
                        large_ingrowth_trees = {k: {'bio': self.Stand.eqns[each_species]['normal'](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.Stand.od[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] >= 15.0}
                    
                    small_ingrowth_trees = {k: {'bio': self.Stand.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.Stand.od[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}
                    
                    
                    # count the number of total dead, live, and ingrowth trees by the plot
                    try:
                        total_dead_trees = (len(large_dead_trees)/total_area + len(small_dead_trees)/total_area)
                    except Exception:
                        total_dead_trees = 0.

                    try:
                        total_live_trees = (len(large_live_trees)/total_area + len(small_live_trees)/total_area)
                    except Exception:
                        total_live_trees = 0.

                    try:
                        total_ingrowth_trees = (len(large_ingrowth_trees)/total_area + len(small_ingrowth_trees)/total_area)
                    except Exception:
                        total_ingrowth_trees = 0.

                    # compute the totals

                    try:
                        total_live_bio = sum([large_live_trees[tree]['bio'][0]/total_area for tree in large_live_trees.keys()]) + sum([small_live_trees[tree]['bio'][0]/total_area for tree in small_live_trees.keys()])
                    except Exception:
                        import pdb; pdb.set_trace()
                    total_ingrowth_bio = sum([large_ingrowth_trees[tree]['bio'][0]/total_area for tree in large_ingrowth_trees.keys()])+ sum([small_ingrowth_trees[tree]['bio'][0]/total_area for tree in small_ingrowth_trees.keys()])
                    total_dead_bio = sum([large_dead_trees[tree]['bio'][0]/total_area for tree in large_dead_trees.keys()]) + sum([small_dead_trees[tree]['bio'][0]/total_area for tree in small_dead_trees.keys()])

                    total_live_jenkins = sum([large_live_trees[tree]['bio'][2]/total_area for tree in large_live_trees.keys()]) + sum([small_live_trees[tree]['bio'][2]/total_area for tree in small_live_trees.keys()])
                    total_ingrowth_jenkins = sum([large_ingrowth_trees[tree]['bio'][2]/total_area for tree in large_ingrowth_trees.keys()])  + sum([small_ingrowth_trees[tree]['bio'][2]/total_area for tree in small_ingrowth_trees.keys()])
                    total_dead_jenkins = sum([large_dead_trees[tree]['bio'][2]/total_area for tree in large_dead_trees.keys()]) + sum([small_dead_trees[tree]['bio'][2]/total_area for tree in small_dead_trees.keys()])

                    total_live_volume = sum([large_live_trees[tree]['bio'][1]/total_area for tree in large_live_trees.keys()])  + sum([small_live_trees[tree]['bio'][1]/total_area for tree in small_live_trees.keys()])
                    total_ingrowth_volume = sum([large_ingrowth_trees[tree]['bio'][1]/total_area for tree in large_ingrowth_trees.keys()]) + sum([small_ingrowth_trees[tree]['bio'][1]/total_area for tree in small_ingrowth_trees.keys()])
                    total_dead_volume = sum([large_dead_trees[tree]['bio'][1]/total_area for tree in large_dead_trees.keys()]) + sum([small_dead_trees[tree]['bio'][1]/total_area for tree in small_dead_trees.keys()])

                    total_live_basal = sum([large_live_trees[tree]['ba']/total_area for tree in large_live_trees.keys()]) + sum([small_live_trees[tree]['ba']/total_area for tree in small_live_trees.keys()])
                    total_ingrowth_basal = sum([large_ingrowth_trees[tree]['ba']/total_area for tree in large_ingrowth_trees.keys()])+  sum([small_ingrowth_trees[tree]['ba']/total_area for tree in small_ingrowth_trees.keys()])
                    total_dead_basal = sum([large_dead_trees[tree]['ba']/total_area for tree in large_dead_trees.keys()]) + sum([small_dead_trees[tree]['ba']/total_area for tree in small_dead_trees.keys()])


                    if each_year not in Biomasses:
                        Biomasses[each_year] = {each_species : {each_plot : {'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'total_live_basal': total_live_basal,'total_ingrowth_basal': total_ingrowth_basal, 'total_dead_basal': total_dead_basal}}}
                    

                    elif each_year in Biomasses:
                        
                        if each_species not in Biomasses[each_year]:
                            Biomasses[each_year][each_species]= {each_plot : {'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'total_live_basal': total_live_basal, 'total_dead_basal': total_dead_basal, 'total_ingrowth_basal': total_ingrowth_basal}}
                        
                        # don't need to augment the wood density - one time is enough! - this is adding in each of the plots, which are already on area basis
                        elif each_species in Biomasses[each_year]:
                            if each_plot not in Biomasses[each_year][each_species]:
                                Biomasses[each_year][each_species][each_plot] = {'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'total_live_basal': total_live_basal, 'total_dead_basal': total_dead_basal, 'total_ingrowth_basal': total_ingrowth_basal}
                            elif each_plot in Biomasses[each_year][each_species]:
                                print("error, you have already processed " + each_plot)
                        else:
                            pass
        
        return Biomasses

    def aggregate_biomasses_plot(self, Biomasses):
        """ for each year in biomasses, add up all the trees from all the species, and output the plot summary over all the species as a nearly identical data structure. 

        For every one of the attributes in Biomasses for Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), sum the values for the whole stand. These values are already normalized into the per meters squared version. In the write out, we'll multiply it out to the HA level

        **INPUTS**

        :Biomasses: the species aggregated results from the plot scale analyses of biomass

        **RETURNS**

        :Biomasses_Agg: The biomasses by plot, but now aggregated over all the species on that plot.
        """
        Biomasses_Agg = {}

        for each_year in sorted(Biomasses.keys()):

            for each_species in Biomasses[each_year].keys():

                for each_plot in Biomasses[each_year][each_species].keys():
                    
                    if each_plot not in Biomasses_Agg:

                        Biomasses_Agg[each_plot] = { each_year: {
                        'total_live_trees': Biomasses[each_year][each_species][each_plot]['total_live_trees'],
                        'total_dead_trees': Biomasses[each_year][each_species][each_plot]['total_dead_trees'],
                        'total_ingrowth_trees': Biomasses[each_year][each_species][each_plot]['total_ingrowth_trees'],
                        'total_live_basal': Biomasses[each_year][each_species][each_plot]['total_live_basal'],
                        'total_dead_basal': Biomasses[each_year][each_species][each_plot]['total_dead_basal'],
                        'total_ingrowth_basal': Biomasses[each_year][each_species][each_plot]['total_ingrowth_basal'],
                        'total_live_bio': Biomasses[each_year][each_species][each_plot]['total_live_bio'],
                        'total_dead_bio': Biomasses[each_year][each_species][each_plot]['total_dead_bio'],
                        'total_ingrowth_bio': Biomasses[each_year][each_species][each_plot]['total_ingrowth_bio'],
                        'total_live_volume': Biomasses[each_year][each_species][each_plot]['total_live_volume'],
                        'total_dead_volume': Biomasses[each_year][each_species][each_plot]['total_dead_volume'],
                        'total_ingrowth_volume': Biomasses[each_year][each_species][each_plot]['total_ingrowth_volume'],
                        'total_live_jenkins': Biomasses[each_year][each_species][each_plot]['total_live_jenkins'],
                        'total_dead_jenkins': Biomasses[each_year][each_species][each_plot]['total_dead_jenkins'],
                        'total_ingrowth_jenkins': Biomasses[each_year][each_species][each_plot]['total_ingrowth_jenkins']}}

                    elif each_plot in Biomasses_Agg:
                        
                        if each_year not in Biomasses_Agg[each_plot]:
                            Biomasses_Agg[each_plot][each_year] = {'total_live_trees': Biomasses[each_year][each_species][each_plot]['total_live_trees'],'total_dead_trees': Biomasses[each_year][each_species][each_plot]['total_dead_trees'], 'total_ingrowth_trees': Biomasses[each_year][each_species][each_plot]['total_ingrowth_trees'], 'total_live_basal': Biomasses[each_year][each_species][each_plot]['total_live_basal'], 'total_dead_basal': Biomasses[each_year][each_species][each_plot]['total_dead_basal'], 'total_ingrowth_basal': Biomasses[each_year][each_species][each_plot]['total_ingrowth_basal'], 'total_live_bio': Biomasses[each_year][each_species][each_plot]['total_live_bio'], 'total_dead_bio': Biomasses[each_year][each_species][each_plot]['total_dead_bio'], 'total_ingrowth_bio': Biomasses[each_year][each_species][each_plot]['total_ingrowth_bio'], 'total_live_volume': Biomasses[each_year][each_species][each_plot]['total_live_volume'], 'total_dead_volume': Biomasses[each_year][each_species][each_plot]['total_dead_volume'], 'total_ingrowth_volume': Biomasses[each_year][each_species][each_plot]['total_ingrowth_volume'], 'total_live_jenkins': Biomasses[each_year][each_species][each_plot]['total_live_jenkins'], 'total_dead_jenkins': Biomasses[each_year][each_species][each_plot]['total_dead_jenkins'], 'total_ingrowth_jenkins': Biomasses[each_year][each_species][each_plot]['total_ingrowth_jenkins']}
                        
                        # if you already have that year and plot, just add whatever the heck species it is.
                        elif each_year in Biomasses_Agg[each_plot]:
                            Biomasses_Agg[each_plot][each_year]['total_live_trees'] += Biomasses[each_year][each_species][each_plot]['total_live_trees']
                            Biomasses_Agg[each_plot][each_year]['total_dead_trees'] += Biomasses[each_year][each_species][each_plot]['total_dead_trees']
                            Biomasses_Agg[each_plot][each_year]['total_ingrowth_trees'] += Biomasses[each_year][each_species][each_plot]['total_ingrowth_trees']
                            Biomasses_Agg[each_plot][each_year]['total_live_basal'] += Biomasses[each_year][each_species][each_plot]['total_live_basal']
                            Biomasses_Agg[each_plot][each_year]['total_dead_basal'] += Biomasses[each_year][each_species][each_plot]['total_dead_basal']
                            Biomasses_Agg[each_plot][each_year]['total_ingrowth_basal'] += Biomasses[each_year][each_species][each_plot]['total_ingrowth_basal']
                            Biomasses_Agg[each_plot][each_year]['total_live_bio'] += Biomasses[each_year][each_species][each_plot]['total_live_bio']
                            Biomasses_Agg[each_plot][each_year]['total_dead_bio'] += Biomasses[each_year][each_species][each_plot]['total_dead_bio']
                            Biomasses_Agg[each_plot][each_year]['total_ingrowth_bio'] += Biomasses[each_year][each_species][each_plot]['total_ingrowth_bio']
                            Biomasses_Agg[each_plot][each_year]['total_live_volume'] += Biomasses[each_year][each_species][each_plot]['total_live_volume']
                            Biomasses_Agg[each_plot][each_year]['total_dead_volume'] += Biomasses[each_year][each_species][each_plot]['total_dead_volume']
                            Biomasses_Agg[each_plot][each_year]['total_ingrowth_volume'] += Biomasses[each_year][each_species][each_plot]['total_ingrowth_volume']
                            Biomasses_Agg[each_plot][each_year]['total_live_jenkins'] += Biomasses[each_year][each_species][each_plot]['total_live_jenkins']
                            Biomasses_Agg[each_plot][each_year]['total_dead_jenkins'] += Biomasses[each_year][each_species][each_plot]['total_dead_jenkins']
                            Biomasses_Agg[each_plot][each_year]['total_ingrowth_jenkins'] += Biomasses[each_year][each_species][each_plot]['total_ingrowth_jenkins']

        return Biomasses_Agg


    def write_plot_composite(self, Biomasses, Biomasses_Agg, XFACTOR, *args):
        """ Generates an output file which combines the Trees Per Hectare (TPH), Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins' Biomass ( Mg ), Basal Area (m \ :sup:`2`) by species with a row of "all" containing the composite TPH, Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins' Biomass ( Mg ), and Basal Area (m \ :sup:`2`)

        **INPUTS**

        :Biomasses: data structure containing portions of biomass and other desired outputs, grouped by species
        :Biomasses_Agg: data structure containing the aggregate biomass over all the species.
        :XFACTOR: the reference object used for computing areas and such. You've already created it. No worries.

        **RETURNS**

        Writes a file named `standid + stand_composite_output.csv`

        If an additional argument is specified, this is the generic output file to write to for the `--all` command line method
        """

        try:
            detail_reference = XFACTOR.detail_reference[self.standid]
        except Exception:
            detail_reference = None

        if args and args != []:
            filename_out = args[0]
            mode = args[1]
        else:

            dirout = "sample_output"
            filename_out = self.Stand.standid + "_plot_composite_output.csv"
            os.path.join(dirout, filename_out)
            mode = 'w'
        
        with open(filename_out, mode) as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            if mode == 'w':
                writer.writerow(['DBCODE','ENTITY','PLOTID','SPECIES','YEAR','PORTION','TPH_NHA','BA_M2HA','VOL_M3HA','BIO_MGHA','JENKBIO_MGHA'])
            else:
                pass

            for each_year in sorted(Biomasses.keys()):
                    # try:
                    #     detail_reference
                for each_species in Biomasses[each_year]:

                    for each_plot in Biomasses[each_year][each_species]:
                        # remember to multiply by 10000 to go from m2 to hectare
                        new_row_1 = ['TP001', '08', each_plot.upper(), each_species.upper(), each_year,'INGROWTH', math.ceil(Biomasses[each_year][each_species][each_plot]['total_ingrowth_trees']*10000), round(Biomasses[each_year][each_species][each_plot]['total_ingrowth_basal']*10000, 3), round(Biomasses[each_year][each_species][each_plot]['total_ingrowth_volume']*10000,3), round(Biomasses[each_year][each_species][each_plot]['total_ingrowth_bio']*10000,3), round(Biomasses[each_year][each_species][each_plot]['total_ingrowth_jenkins']*10000,3)]
                        
                    #writer.writerow(new_row)

                        # remember to multiply by 10000 to go from m2 to hectare
                        new_row_2 = ['TP001', '08', each_plot.upper(), each_species.upper(), each_year,'LIVE', math.ceil(Biomasses[each_year][each_species][each_plot]['total_live_trees']*10000), round(Biomasses[each_year][each_species][each_plot]['total_live_basal']*10000, 3), round(Biomasses[each_year][each_species][each_plot]['total_live_volume']*10000,3), round(Biomasses[each_year][each_species][each_plot]['total_live_bio']*10000,3), round(Biomasses[each_year][each_species][each_plot]['total_live_jenkins']*10000,3)]
                     
                        #writer.writerow(new_row)

                        # remember to multiply by 10000 to go from m2 to hectare
                        new_row_3 = ['TP001', '08', each_plot.upper(), each_species.upper(), each_year,'MORTALITY', math.ceil(Biomasses[each_year][each_species][each_plot]['total_dead_trees']*10000), round(Biomasses[each_year][each_species][each_plot]['total_dead_basal']*10000, 3), round(Biomasses[each_year][each_species][each_plot]['total_dead_volume']*10000,3), round(Biomasses[each_year][each_species][each_plot]['total_dead_bio']*10000,3), round(Biomasses[each_year][each_species][each_plot]['total_dead_jenkins']*10000,3)]

                        writer.writerow(new_row_1)
                        writer.writerow(new_row_2)
                        writer.writerow(new_row_3)


            for each_plot in sorted(Biomasses_Agg.keys()):

                for each_year in sorted(Biomasses_Agg[each_plot].keys()):
                
                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row4 = ['TP001', '08', each_plot.upper(), 'ALL', each_year,'INGROWTH', math.ceil(Biomasses_Agg[each_plot][each_year]['total_ingrowth_trees']*10000), round(Biomasses_Agg[each_plot][each_year]['total_ingrowth_basal']*10000, 3), round(Biomasses_Agg[each_plot][each_year]['total_ingrowth_volume']*10000,3), round(Biomasses_Agg[each_plot][each_year]['total_ingrowth_bio']*10000,3), round(Biomasses_Agg[each_plot][each_year]['total_ingrowth_jenkins']*10000,3)]
                        

                    new_row5 = ['TP001', '08', each_plot.upper(), 'ALL', each_year,'LIVE', math.ceil(Biomasses_Agg[each_plot][each_year]['total_live_trees']*10000), round(Biomasses_Agg[each_plot][each_year]['total_live_basal']*10000, 3), round(Biomasses_Agg[each_plot][each_year]['total_live_volume']*10000,3), round(Biomasses_Agg[each_plot][each_year]['total_live_bio']*10000,3), round(Biomasses_Agg[each_plot][each_year]['total_live_jenkins']*10000,3)]

                    # remember to multiply by 10000 to go from m2 to hectare

                    new_row6 = ['TP001', '08', each_plot.upper(), 'ALL', each_year,'MORTALITY', math.ceil(Biomasses_Agg[each_plot][each_year]['total_dead_trees']*10000), round(Biomasses_Agg[each_plot][each_year]['total_dead_basal']*10000, 3), round(Biomasses_Agg[each_plot][each_year]['total_dead_volume']*10000,3), round(Biomasses_Agg[each_plot][each_year]['total_dead_bio']*10000,3), round(Biomasses_Agg[each_plot][each_year]['total_dead_jenkins']*10000,3)]
                    writer.writerow(new_row4)
                    writer.writerow(new_row5)
                    writer.writerow(new_row6)



    

if __name__ == "__main__":

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    queries = DATABASE_CONNECTION.queries

    # creates lookups for expansion factors
    # remember, to introspect the class you can use >>> XFACTOR.__dict__.keys()
    # dict_keys(['expansion', 'additions', 'total_areas', 'num_plots', 'detail_reference', 'cur', 'mortalities', 'uplot_areas', 'umins_reference', 'queries'])

    XFACTOR = poptree_basis.Capture(cur, queries)

    #### A set of test stands ####
    test_stands = ['RS01', 'RS02', 'RS30', 'TB13', 'AR07', 'AM16', 'RS29', 'RS32', 'AE10', 'AV06', 'TO04']
    
    ### A shorter set of test stands ###
    #test_stands = ["CH06"]

    test_stands = ['rs01']
    
    for each_stand in test_stands:

        each_stand=each_stand.lower()
        
        A = Stand(cur, XFACTOR, queries, each_stand)

        import pdb; pdb.set_trace()
        BM, BTR, ROB = A.compute_biomasses(XFACTOR)

        A.write_stand_rob(ROB, XFACTOR)

        BMA = A.aggregate_biomasses(BM)

        # testing a single plot or two
        K = Plot(A, XFACTOR, [])

        BM_plot = K.compute_biomasses_plot(XFACTOR)
        
        BMA_plot = K.aggregate_biomasses_plot(BM_plot)
        
        A.write_stand_composite(BM, BMA, XFACTOR)

        K.write_plot_composite(BM_plot, BMA_plot, XFACTOR)

        A.write_individual_trees()

        # delete objects. This may not be necessary.
        del A
        del BM
        del BMA
        del K
        del BM_plot
        del BMA_plot