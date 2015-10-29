#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import biomass_basis
import bisect
import csv

class Stand(object):
    """Stands contain several plots, grouped by year and species. Stand produce outputs of biomass ( Mg/ha ), volume (m\ :sup:`3`), Jenkins biomass ( Mg/ha ), TPH (number of trees/ ha), and basal area (m\ :sup:`2` / ha).

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
    def __init__(self, cur, XFACTOR, queries, standid):
        self.standid = standid
        self.cur = cur
        self.tree_list = queries['stand']['query']
        self.tree_list_m = queries['stand']['query_trees_m']
        self.species_list = queries['stand']['query_species']
        self.eqn_query = queries['tree']['sql_1tree_eqn']
        self.replacement_query = queries['stand']['query_replacements']
        self.eqns = {}
        self.od = {}
        self.woodden_dict ={}
        self.proxy_dict = {}
        self.decent_years = []
        self.missings= {}
        self.mortalities ={}
        self.mort_replacements = {}
        self.total_area_ref = {}
        self.additions = {}
        self.replacements = {}

        # get the total area for the stand - this dictionary is for the years when there is an actual inventory and not a mortality check
        self.get_total_area(XFACTOR)

        # get the appropriate equations, live trees, and dead trees for the stand
        self.select_eqns()

        # check if it is an addition; if is an addition, move to the subsequent year on that plot by creating self.replacements.
        self.check_additions_and_mort(XFACTOR)
        self.get_all_live_trees()
        self.get_all_dead_trees()

        # looks to the missing trees and matches their ids to live trees, assigns that dbh to the subsequent year.
        self.update_all_missing_trees()
        

    def select_eqns(self):
        """ Gets only the equations you need based on the species on that plot by querying the database for individual species that will be on this stand and makes an equation table.

        **INTERNAL VARIABLES**

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


                this_eqn = lambda x : biomass_basis.which_fx(form)(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                
                if each_species not in self.eqns:
                    self.eqns.update({each_species:{str(row[1]).rstrip().lower():this_eqn}})
                
                elif each_species in self.eqns:
                    # when there are 2 or more sizes
                    self.eqns[each_species].update({str(row[1]).rstrip().lower():this_eqn})

    
    def check_additions_and_mort(self, XFACTOR):
        """ Check if the stand may contain "additions". If so, replace the year with the subsequent year as long as it is not also additions or mortality. If additions or mortality is the final years in the data, we will not do those years. 

        **INTERNAL VARIABLES**
        :additions: stand additions are years that have live trees measured that were not measured in previous year's inventory. we allocate additions to the subsequent year's inventory. There's only about 15 plots this happens on. 
        :replacement: replaces the years of "additions" with the subsequent year that is not an additions.
        """

        if self.standid.lower() in XFACTOR.additions.keys():
            # store the additions for when you analyze
            self.additions = XFACTOR.additions[self.standid]
            
            # get the years in which there are additions
            additions_years = sorted(list(XFACTOR.additions[self.standid].keys()))

        else:
            pass

        if self.standid.lower() in XFACTOR.mortalities.keys():
            self.mortalities = XFACTOR.mortalities[self.standid]
            mortality_years = sorted(list(XFACTOR.mortalities[self.standid].keys()))
        else:
            pass

        if additions_years != [] or mortality_years != []:

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
                for each_year in mortality_years:
                    try:
                        index = bisect.bisect_right(self.decent_years, each_year)
                        replacement_year = self.decent_years[index]
                        plots_applied_to = XFACTOR.mortalities[self.standid][each_year]
                        self.mort_replacements.update({each_year:{'replacement_year': replacement_year, 'plots': plots_applied_to}})
                    
                    except Exception:
                        print("exception thrown while trying to list mortality years")
                        import pdb; pdb.set_trace()



    def get_total_area(self, XFACTOR):
        """ Get the total area for each year on that stand and create a reference table to be used when figuring out the per hectare output. The percent of area on the plot over the percent of the area of the stand is the proportion represented by that plot.

        **INPUTS**

        :XFACTOR: XFACTOR.total_areas has the areas by stand, like this: 

        :Example:

        >>> XFACTOR.total_areas['hr03']
        >>> {1984: 10000.0, 1985: 10000.0, 1986: 10000.0, 1988: 10000.0, 1989: 10000.0, 2000: 10000.0, 2007: 10000.0, 1978: 10000.0, 1995: 10000.0}
        """

        try:
            self.total_area_ref = XFACTOR.total_areas[self.standid]
        except Exception:
            self.total_area_ref = {None: 10000.0}

    def get_all_live_trees(self):
        """ Get the trees on that stand by querying FSDBDATA and sort them by year, plot, live or dead, and species. 

        Queries both the live trees and the dead trees in the live database who do not have a DBH given. The dead trees then come in and replace the live ones without the DBH's in get_all_dead_trees(). First get the live from self.tree_list. 

        .. Note: ingrowth is included in "live" (live statuses are all but "6" and "9"), but ingrowth is exclusive when status is "2"

        **INTERNAL VARIABLES**


        :self.query: "SELECT fsdbdata.dbo.tp00101.treeid, fsdbdata.dbo.tp00101.species, fsdbdata.dbo.tp00101.standid, fsdbdata.dbo.tp00101.plotid, fsdbdata.dbo.tp00102.dbh, fsdbdata.dbo.tp00102.tree_status, fsdbdata.dbo.tp00102.year, fsdbdata.dbo.tp00102.dbh_code, fsdbdata.dbo.tp00101.PSP_STUDYID FROM fsdbdata.dbo.tp00101 LEFT JOIN fsdbdata.dbo.tp00102 ON fsdbdata.dbo.tp00101.treeid = fsdbdata.dbo.tp00102.treeid WHERE fsdbdata.dbo.tp00101.standid like '{standid}' ORDER BY fsdbdata.dbo.tp00102.treeid ASC"

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
                    new_year = self.mort_replacements[year]['replacement_year']
                    year = new_year
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

        **INTERNAL VARIABLES**

        :self.tree_list_m: "SELECT fsdbdata.dbo.tp00101.treeid, fsdbdata.dbo.tp00101.species, fsdbdata.dbo.tp00101.standid, fsdbdata.dbo.tp00101.plotid, fsdbdata.dbo.tp00103.dbh_last, fsdbdata.dbo.tp00103.year FROM fsdbdata.dbo.tp00101 LEFT JOIN fsdbdata.dbo.tp00103 ON fsdbdata.dbo.tp00101.treeid = fsdbdata.dbo.tp00103.treeid WHERE fsdbdata.dbo.tp00101.standid like '{standid}' ORDER BY fsdbdata.dbo.tp00103.treeid ASC"
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
                    new_year = self.mort_replacements[year]['replacement_year']
                    year = new_year
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
        """ Get the missing trees from self.missing and try to match each to a tree in the main dictionary that is alive in the preceding year from self.decent_years, and then return a copy of that tree to the year it is missing, so we can compute its biomass.

        **INTERNAL VARIABLES**

        :replacement_year_index: the index in the list of valid years to get the year of replacement from. It needs to precede the missing year
        :replacement_year: the year whose data we use to replace the missing eyar

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
                                    # if it has been missing since the first year
                                    replacement_year = self.decent_years[0]
                                    replacement_tree_dbh = self.od[replacement_year][each_species][each_plot]['live'][each_treeid][0]
                                except Exception:
                                    print("cannot find a match for the missing tree: " + each_treeid + " -- check the fsdb!")
                                    import pdb; pdb.set_trace()

                        # this tree should have a dbh but also a status of '9' and 'M'
                        adjusted_replacement_tree_tuple = (replacement_tree_dbh, '9', 'M')

                        # update the main database with a replica of this tree for the missing one
                        self.od[each_year][each_species][each_plot]['live'].update({each_treeid: adjusted_replacement_tree_tuple})

                        
    def compute_biomasses(self, XFACTOR):
        """ Compute the biomass, volume, jenkins. Use for stands with alternate minimums, areas, or detail plots 

        First use the Capture object to tell if a fancy computation (i.e. get a special area, minimum, etc. needs to be performed.
            Load in the appropriate parameters for this computation. Separate "small" trees from "large" ones so that small ones can get the expansion factor. If they aren't on a detail plot, this number will just be "1".


        :XFACTOR: a Capture object containing the detail plots, minimum dbhs, etc.
        :XFACTOR.detail_reference: plots which are detail plots and when
        :XFACTOR.stands_with_unusual_mins: plots which have minimums that are not 15 and are not detail plots
        :XFACTOR.unusual_plot_areas: plots whose areas are not 625m

        **INTERNAL VARIABLES**

        Basically, this is the same as compute_normal_biomasses except the unique area of each plot and stand is referenced from a table rather than assumed to be 625 m\ :sup: 2.

        """

        Biomasses = {}
        BadTreeRef = {}
        
        all_years = sorted(self.od.keys())
        
        for index, each_year in enumerate(all_years):

            try:
                
                total_area = self.total_area_ref[each_year]
            
            except Exception:
                
                try:
                    # get most recent similar year
                    total_area = self.total_area_ref[all_years[index-1]]
                except Exception:
                    # get most recent year
                    total_area = self.total_area_ref[all_years[-1]]


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
                        Xw = XFACTOR.expansion[self.standid][each_year]
                        mindbh = XFACTOR.detail_reference[self.standid][each_year][each_plot]['min']
                        area = XFACTOR.detail_reference[self.standid][each_year][each_plot]['area']

                    # figure out the representative percentage of all the area of the stand that this plot represents in the given year
                    percent_area_of_total = area/total_area  
                    print("the area of the plot " + each_plot + " is " + str(area) + " and the total area is " + str(total_area))                  

                    large_dead_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] >= 15.0}
                    
                    small_dead_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}

                    large_live_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] >= 15.0}
                    
                    small_live_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}

                    large_ingrowth_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.od[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] >= 15.0}
                    
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
                    
                    # count the number of total dead, live, and ingrowth trees.
                    try:
                        total_dead_trees = (len(large_dead_trees) + len(small_dead_trees)*Xw)
                    except Exception:
                        total_dead_trees = 0.

                    try:
                        total_live_trees = (len(large_live_trees) + len(small_live_trees)*Xw)
                    except Exception:
                        total_live_trees = 0.

                    try:
                        total_ingrowth_trees = (len(large_ingrowth_trees) + len(small_ingrowth_trees)*Xw)
                    except Exception:
                        total_ingrowth_trees = 0.

                    # compute the totals
                    # total_live_bio = sum([large_live_trees[tree]['bio'][0]/area for tree in large_live_trees.keys()])*percent_area_of_total + sum([(small_live_trees[tree]['bio'][0]/area)*Xw for tree in small_live_trees.keys()])*percent_area_of_total
                    # total_ingrowth_bio = sum([large_ingrowth_trees[tree]['bio'][0]/area for tree in large_ingrowth_trees.keys()]) * percent_area_of_total + sum([(small_ingrowth_trees[tree]['bio'][0]/area)*Xw for tree in small_ingrowth_trees.keys()]) * percent_area_of_total
                    # total_dead_bio = sum([large_dead_trees[tree]['bio'][0]/area for tree in large_dead_trees.keys()]) * percent_area_of_total + sum([(small_dead_trees[tree]['bio'][0]/area)*Xw for tree in small_dead_trees.keys()]) * percent_area_of_total


                    total_live_bio = (sum([large_live_trees[tree]['bio'][0]/area for tree in large_live_trees.keys()]) + sum([(small_live_trees[tree]['bio'][0]/area)*Xw for tree in small_live_trees.keys()]))*percent_area_of_total
                    total_ingrowth_bio = (sum([large_ingrowth_trees[tree]['bio'][0]/area for tree in large_ingrowth_trees.keys()])+ sum([(small_ingrowth_trees[tree]['bio'][0]/area)*Xw for tree in small_ingrowth_trees.keys()]))* percent_area_of_total
                    total_dead_bio = (sum([large_dead_trees[tree]['bio'][0]/area for tree in large_dead_trees.keys()]) + sum([(small_dead_trees[tree]['bio'][0]/area)*Xw for tree in small_dead_trees.keys()]))* percent_area_of_total

                    
                    total_live_jenkins = (sum([large_live_trees[tree]['bio'][2]/area for tree in large_live_trees.keys()]) + sum([(small_live_trees[tree]['bio'][2]/area)*Xw for tree in small_live_trees.keys()])) * percent_area_of_total
                    total_ingrowth_jenkins = (sum([large_ingrowth_trees[tree]['bio'][2]/area for tree in large_ingrowth_trees.keys()])  + sum([(small_ingrowth_trees[tree]['bio'][2]/area)*Xw for tree in small_ingrowth_trees.keys()])) * percent_area_of_total
                    total_dead_jenkins = (sum([large_dead_trees[tree]['bio'][2]/area for tree in large_dead_trees.keys()]) + sum([(small_dead_trees[tree]['bio'][2]/area)*Xw for tree in small_dead_trees.keys()])) * percent_area_of_total

                    total_live_volume = (sum([large_live_trees[tree]['bio'][1]/area for tree in large_live_trees.keys()])  + sum([(small_live_trees[tree]['bio'][1]/area)*Xw for tree in small_live_trees.keys()])) * percent_area_of_total
                    total_ingrowth_volume = (sum([large_ingrowth_trees[tree]['bio'][1]/area for tree in large_ingrowth_trees.keys()]) + sum([(small_ingrowth_trees[tree]['bio'][1]/area)*Xw for tree in small_ingrowth_trees.keys()])) * percent_area_of_total
                    total_dead_volume = (sum([large_dead_trees[tree]['bio'][1]/area for tree in large_dead_trees.keys()]) + sum([(small_dead_trees[tree]['bio'][1]/area)*Xw for tree in small_dead_trees.keys()])) * percent_area_of_total

                    total_live_basal = (sum([large_live_trees[tree]['ba']/area for tree in large_live_trees.keys()]) + sum([(small_live_trees[tree]['ba']/area)*Xw for tree in small_live_trees.keys()])) * percent_area_of_total
                    total_ingrowth_basal = (sum([large_ingrowth_trees[tree]['ba']/area for tree in large_ingrowth_trees.keys()])+  sum([(small_ingrowth_trees[tree]['ba']/area)*Xw for tree in small_ingrowth_trees.keys()])) * percent_area_of_total
                    total_dead_basal = (sum([large_dead_trees[tree]['ba']/area for tree in large_dead_trees.keys()]) + sum([(small_dead_trees[tree]['ba']/area)*Xw for tree in small_dead_trees.keys()])) * percent_area_of_total


                    num_plots = 1
                    
                    # just take the wood density from one tree to have

                    try:
                        wooddensity = self.eqns[each_species][biomass_basis.maxref(16.0, each_species)](16.0)[3]
                        
                    except Exception:
                        print("stuck trying to compute wood density")
                        import pdb; pdb.set_trace()
                        # find the wood density by pretending that you need to compute a 25 cm tree
                        

                    # get a list of tree names for checking
                    living_trees = list(large_live_trees) + list(small_live_trees)
                    ingrowth_trees = list(large_ingrowth_trees) + list(small_ingrowth_trees)
                    dead_trees = list(large_dead_trees) + list(small_dead_trees)

                    if each_year not in Biomasses:
                        Biomasses[each_year] = {each_species : {'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'total_live_basal': total_live_basal, 'wooddensity': wooddensity, 'name_live': living_trees, 'name_mort': dead_trees, 'total_ingrowth_basal': total_ingrowth_basal, 'total_dead_basal': total_dead_basal,  'name_ingrowth': ingrowth_trees, 'num_plots': num_plots}}
                    

                    elif each_year in Biomasses:
                        # do not need to augment the wood density :) -> but do make sure it is in here
                        if each_species not in Biomasses[each_year]:
                            Biomasses[each_year][each_species]={'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'total_live_basal': total_live_basal, 'total_dead_basal': total_dead_basal, 'name_live': living_trees, 'total_ingrowth_basal': total_ingrowth_basal, 'wooddensity': wooddensity, 'name_mort': dead_trees,'name_ingrowth': ingrowth_trees, 'num_plots':num_plots}
                        
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
                            Biomasses[each_year][each_species]['wooddensity'] = wooddensity
                            Biomasses[each_year][each_species]['num_plots'] = num_plots
                        else:
                            pass
        
        return Biomasses, BadTreeRef

    def aggregate_biomasses(self, Biomasses):
        """ for each year in biomasses, add up all the trees from all the species, and output the stand summary over all the species as a nearly identical data structure. 

        For every one of the attributes in Biomasses for Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), sum the values for the whole stand. These values are already normalized into the per meters squared version. In the write out, we'll multiply it out to the HA level

        """
        Biomasses_Agg = {}

        for each_year in sorted(Biomasses.keys()):

            if each_year not in Biomasses_Agg:

                Biomasses_Agg[each_year]= {'total_live_trees': sum([Biomasses[each_year][x]['total_live_trees'] for x in Biomasses[each_year].keys()]), 'total_dead_trees': sum([Biomasses[each_year][x]['total_dead_trees'] for x in Biomasses[each_year].keys()]), 'total_ingrowth_trees': sum([Biomasses[each_year][x]['total_ingrowth_trees'] for x in Biomasses[each_year].keys()]), 'total_live_basal': sum([Biomasses[each_year][x]['total_live_basal'] for x in Biomasses[each_year].keys()]), 'total_dead_basal': sum([Biomasses[each_year][x]['total_dead_basal'] for x in Biomasses[each_year].keys()]), 'total_ingrowth_basal': sum([Biomasses[each_year][x]['total_ingrowth_basal'] for x in Biomasses[each_year].keys()]), 'total_live_bio': sum([Biomasses[each_year][x]['total_live_bio'] for x in Biomasses[each_year].keys()]), 'total_dead_bio': sum([Biomasses[each_year][x]['total_dead_bio'] for x in Biomasses[each_year].keys()]), 'total_ingrowth_bio': sum([Biomasses[each_year][x]['total_ingrowth_bio'] for x in Biomasses[each_year].keys()]), 'total_live_volume': sum([Biomasses[each_year][x]['total_live_volume'] for x in Biomasses[each_year].keys()]), 'total_dead_volume': sum([Biomasses[each_year][x]['total_dead_volume'] for x in Biomasses[each_year].keys()]), 'total_ingrowth_volume': sum([Biomasses[each_year][x]['total_ingrowth_volume'] for x in Biomasses[each_year].keys()]), 'total_live_jenkins': sum([Biomasses[each_year][x]['total_live_jenkins'] for x in Biomasses[each_year].keys()]), 'total_dead_jenkins': sum([Biomasses[each_year][x]['total_dead_jenkins'] for x in Biomasses[each_year].keys()]), 'total_ingrowth_jenkins': sum([Biomasses[each_year][x]['total_ingrowth_jenkins'] for x in Biomasses[each_year].keys()])}

            elif each_year in Biomasses_Agg:
                print("the year has already been included in aggregate biomass- what's up on line 869?")

        return Biomasses_Agg


    def write_stand_composite(self, Biomasses, Biomasses_Agg, XFACTOR):
        """ Generates an output file which combines the Trees Per Hectare (TPH), Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins' Biomass ( Mg ), Basal Area (m \ :sup:`2`) by species with a row of "all" containing the composite TPH, Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins' Biomass ( Mg ), and Basal Area (m \ :sup:`2`)

        **INPUTS**

        :Biomasses: data structure containing portions of biomass and other desired outputs, grouped by species
        :Biomasses_Agg: data structure containing the aggregate biomass over all the species.
        :XFACTOR: the reference object used for computing areas and such. You've already created it. No worries.

        **OUTPUTS**

        Writes a file named `standid + stand_composite_output.csv`
        """

        filename_out = self.standid + "_stand_composite_output.csv"
        with open(filename_out,'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            writer.writerow(['DBCODE','ENTITY','STANDID','SPECIES','YEAR','PORTION','TPH_NHA','BA_M2HA','VOL_M3HA','BIO_MGHA','JENKBIO_MGHA'])

            for each_year in sorted(Biomasses.keys()):

                for each_species in Biomasses[each_year]:

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row_1 = ['TP001', '07', self.standid.upper(), each_species, each_year,'INGROWTH', int(Biomasses[each_year][each_species]['total_ingrowth_trees']), round(Biomasses[each_year][each_species]['total_ingrowth_basal']*10000, 3), round(Biomasses[each_year][each_species]['total_ingrowth_volume']*10000,3), round(Biomasses[each_year][each_species]['total_ingrowth_bio']*10000,3), round(Biomasses[each_year][each_species]['total_ingrowth_jenkins']*10000,3)]
                    
                    #writer.writerow(new_row)

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row_2 = ['TP001', '07', self.standid.upper(), each_species, each_year,'LIVE', int(Biomasses[each_year][each_species]['total_live_trees']), round(Biomasses[each_year][each_species]['total_live_basal']*10000, 3), round(Biomasses[each_year][each_species]['total_live_volume']*10000,3), round(Biomasses[each_year][each_species]['total_live_bio']*10000,3), round(Biomasses[each_year][each_species]['total_live_jenkins']*10000,3)]
                 
                    #writer.writerow(new_row)

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row_3 = ['TP001', '07', self.standid.upper(), each_species, each_year,'MORT', int(Biomasses[each_year][each_species]['total_dead_trees']), round(Biomasses[each_year][each_species]['total_dead_basal']*10000, 3), round(Biomasses[each_year][each_species]['total_dead_volume']*10000,3), round(Biomasses[each_year][each_species]['total_dead_bio']*10000,3), round(Biomasses[each_year][each_species]['total_dead_jenkins']*10000,3)]

                    writer.writerow(new_row_1)
                    writer.writerow(new_row_2)
                    writer.writerow(new_row_3)


            for each_year in sorted(Biomasses_Agg.keys()):
                # remember to multiply by 10000 to go from m2 to hectare
                new_row4 = ['TP001', '07', self.standid.upper(), 'ALL', each_year,'INGROWTH', int(Biomasses_Agg[each_year]['total_ingrowth_trees']), round(Biomasses_Agg[each_year]['total_ingrowth_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_ingrowth_volume']*10000,3), round(Biomasses_Agg[each_year]['total_ingrowth_bio']*10000,3), round(Biomasses_Agg[each_year]['total_ingrowth_jenkins']*10000,3)]
                    

                new_row5 = ['TP001', '07', self.standid.upper(), 'ALL', each_year,'LIVE', int(Biomasses_Agg[each_year]['total_live_trees']), round(Biomasses_Agg[each_year]['total_live_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_live_volume']*10000,3), round(Biomasses_Agg[each_year]['total_live_bio']*10000,3), round(Biomasses_Agg[each_year]['total_live_jenkins']*10000,3)]

                # remember to multiply by 10000 to go from m2 to hectare

                new_row6 = ['TP001', '07', self.standid.upper(), 'ALL', each_year,'MORT', int(Biomasses_Agg[each_year]['total_dead_trees']), round(Biomasses_Agg[each_year]['total_dead_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_dead_volume']*10000,3), round(Biomasses_Agg[each_year]['total_dead_bio']*10000,3), round(Biomasses_Agg[each_year]['total_dead_jenkins']*10000,3)]
                writer.writerow(new_row4)
                writer.writerow(new_row5)
                writer.writerow(new_row6)


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


if __name__ == "__main__":

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    queries = DATABASE_CONNECTION.queries

    # creates lookups for expansion factors
    XFACTOR = poptree_basis.Capture(cur, queries)

    #### A set of test stands ####
    #test_stands = ['CFMF','AV06','WI01','NCNA', 'AG05', 'AB08', 'AX15', 'PP17', 'TO11', 'AV14', 'RS31', 'RS28', 'RS01', 'RS02', 'RS30', 'TB13', 'AR07', 'AM16', 'RS29', 'RS32', 'AE10', 'AV06', 'TO04']
    
    ### A shorter set of test stands ###
    test_stands = ["NCNA", "AX15", "WI01"]
    
    for each_stand in test_stands:

        each_stand=each_stand.lower()
        
        A = Stand(cur, XFACTOR, queries, each_stand)

        BM, BTR = A.compute_biomasses(XFACTOR)

        BMA = A.aggregate_biomasses(BM)

        import pdb; pdb.set_trace()

        A.write_stand_composite(BM, BMA, XFACTOR)

        print("computed static attributes for stand " + each_stand)

        # delete objects. This may not be necessary.
        del A
        del BM
        del BMA