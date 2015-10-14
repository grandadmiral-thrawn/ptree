#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import biomass_basis
import bisect
import csv

class Stand(object):
    """Stands contain several plots, grouped by year and species. Stand produce outputs of biomass, volume, jenkins, trees/ha, and basal areas per hectare.

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
        self.tree_list = queries['stand']['query']
        self.tree_list_m = queries['stand']['query_trees_m']
        self.species_list = queries['stand']['query_species']
        self.eqn_query = queries['tree']['sql_1tree_eqn']
        self.total_area_query = queries['stand']['query_total_plot']
        self.study_id = ""
        self.woodden_dict = {}
        self.proxy_dict = {}
        self.eqns = {}
        self.od = {}
        self.shifted = {}
        self.mortality_years = []
        self.total_area_ref = {}
        self.additions = []
        self.replacement = ""

        # get the total area for the stand - this dictionary is for the years when there is an actual inventory and not a mortality check
        self.get_total_area()

        # get the appropriate equations, live trees, and dead trees for the stand
        self.select_eqns()

        # check that the year is not an "additions" year.
        self.check_additions(XFACTOR)
        self.get_all_live_trees()
        self.get_all_dead_trees()

        # checks if it is a mortality plot, and, if so, shifts the dbhs to the year they should be on for the death totals
        is_mort = self.check_mort()
        self.update_mort(is_mort)
        

    def select_eqns(self):
        """ Gets only the equations you need based on the species on that plot by querying the database for individual species that will be on this stand and makes an equation table.

        **INTERNAL VARIABLES**
        :list_species: a list of the species on that stand in any year, used to query the database for distinct species
        :self.woodden_dict: a dictionary of wood densities by species
        :self.proxy_dict: a dictionary of equation proxies, by species
        :self.eqns: a dictionary of eqns keyed by 'normal', 'big', or 'component' containing lambda functions to receive dbh inputs and compute Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), and wood density.
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
    
    def check_additions(self, XFACTOR):
        """ Check if the stand may contain "additions". If so, populate the additions attribute of yourself and do not include trees from those years
        """

        if self.standid.lower() in XFACTOR.additions.keys():
            if isinstance(XFACTOR.additions[self.standid.lower()], int):
                self.additions.append(XFACTOR.additions[self.standid.lower()])
                self.replacement = XFACTOR.replacements[self.standid.lower()]
            else:
              self.additions = XFACTOR.additions[self.standid.lower()]
              self.replacement = XFACTOR.replacements[self.standid.lower()]

        else:
            self.additions = []


    def get_total_area(self):
        """ Get the total area for each year on that stand and create a reference table to be used when figuring out the per hectare output

        **INTERNAL PARAMETERS**
        :self.total_area_query: "SELECT year, sum(area_m2_corr) from plotAreas where standid like '{standid}' group by year"

        """

        self.pcur.execute(self.total_area_query.format(standid=self.standid))

        for row in self.pcur:

            try: 
                year = int(row[0])
            except Exception:
                year = None

            try:
                area_sum = round(float(row[1]),3)
            except Exception:
                # if it breaks for some reason, assume the sum of all areas is 10000m2
                area_sum = 10000.

            if year not in self.total_area_ref:
                self.total_area_ref[year] = area_sum
            elif year in self.total_area_ref:
                pass

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
                dbh_code = str(row[7]).strip()
            except Exception:
                dbh_code = None

            try:
                study_id = str(row[8]).strip()
            except Exception:
                study_id = "None"

            if self.study_id == "":
                self.study_id = study_id
            else:
                pass

            if year in self.additions:
                year = self.replacement
            else:

                if year not in self.od and status in ["6", "9"]:
                    self.od[year]={species:{plotid: {'live': {}, 'ingrowth': {}, 'dead': {tid: (dbh, status, dbh_code)}}}}
                
                elif year not in self.od and status not in ["6", "9"]:
                    self.od[year]={species: {plotid: {'live': {tid: (dbh, status, dbh_code)}, 'ingrowth': {}, 'dead': {}}}}

                    if status == "2":
                        self.od[year][species][plotid]['ingrowth'].update({tid: (dbh, status, dbh_code)})
                    else:
                        pass

                elif year in self.od:

                    if species not in self.od[year] and status in ["6", "9"]:
                        self.od[year][species] ={plotid: {'live': {}, 'ingrowth': {}, 'dead': {tid: (dbh, status, dbh_code)}}}
                        
                    elif species not in self.od[year] and status not in ["6","9"]: 
                        self.od[year][species] ={plotid: {'live': {tid: (dbh, status, dbh_code)}, 'ingrowth': {}, 'dead': {}}}

                        if status == "2":
                            self.od[year][species][plotid]['ingrowth'].update({tid: (dbh, status, dbh_code)})
                        else:
                            pass

                    elif species in self.od[year]:
                        
                        if status in ["6", "9"] and plotid not in self.od[year][species]:
                            self.od[year][species][plotid] = {'dead': {tid: (dbh, status, dbh_code)}, 'live': {}, 'ingrowth': {}}
                        
                        elif status not in ["6", "9"] and plotid not in self.od[year][species]:
                            self.od[year][species][plotid] = {'live': {tid: (dbh, status, dbh_code)}, 'dead': {}, 'ingrowth': {}}
                            
                            if status == "2":
                                self.od[year][species][plotid]['ingrowth'].update({tid: (dbh, status, dbh_code)})
                            else:
                                pass

                        elif status not in ["6", "9"] and plotid in self.od[year][species]:
                            
                            self.od[year][species][plotid]['live'].update({tid: (dbh, status, dbh_code)})
                            
                            if status == "2":
                                self.od[year][species][plotid]['ingrowth'].update({tid: (dbh, status, dbh_code)})
                            else:
                                pass

                        elif status in ["6", "9"] and plotid in self.od[year][species][plotid]['dead']:
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

            # all status are 6
            status = "6"

            try:
                tid = str(row[0]).strip().lower()
            except Exception:
                tid = "None"

            dbh_code = "M"

            if year in self.additions:
                year = self.replacement
            else:


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
                        

    def check_mort(self):
        """ Checks if the year is a mortality year. 

        Populates self.mortality_years if there are any mortality years. Also sets self.shifted to the output dictionary if there are no mortality years.
        """
        # a year is a mortality year if there is no live biomass in that year for all species on a plot. include species because maybe useful for species
        list_all_years_possible_mortality = []
        
        for each_year in self.od.keys():

            if each_year not in self.total_area_ref.keys() and each_year < 2010:
                list_all_years_possible_mortality.append(each_year)
            else:
                pass

        # if there are no mortality years, return a false, and self.shifted for that year is the exact same as the actual values
        if list_all_years_possible_mortality == []:
            self.shifted = self.od
            return False
        
        else:
            # the mortality years attribute is set for the list of mortality years, and sorted. A true return triggers update mort function
            self.mortality_years = sorted(list_all_years_possible_mortality)
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
                mort_data = self.od[each_year]

                # if the mortality year is not in the live year list, then the mortality belongs to the inventory to its "right"
                if each_year not in list_live_years:
                    index = bisect.bisect_right(list_live_years, each_year)
                    try:
                        update_year = list_live_years[index]
                    except Exception:
                        import pdb; pdb.set_trace()
                else:
                    update_year = each_year
                
                # if the new mortality year isn't listed in the "shifted" data which was generated from the existing data in "od" add it in; this might happen if the mort was the very last inventory to happen
                if update_year not in self.shifted.keys():
                    self.shifted[update_year] = mort_data
                
                elif update_year in self.shifted.keys():
                    for each_species in mort_data.keys():
                        if each_species not in self.shifted[update_year].keys():
                            self.shifted[update_year][each_species] = mort_data[each_species]

                        elif each_species in self.shifted[update_year].keys():
                            for each_plot in mort_data[each_species].keys():
                                if each_plot not in self.shifted[update_year][each_species].keys():
                                    self.shifted[update_year][each_species][each_plot] = mort_data[each_species][each_plot]

                                elif each_plot in self.shifted[update_year][each_species].keys():
                                    try:
                                        self.shifted[update_year][each_species][each_plot]['dead'].update(mort_data[each_species][each_plot]['dead'])
                                    except Exception:
                            
                                        import pdb; pdb.set_trace()


    def compute_normal_biomasses(self, XFACTOR):
        """ Compute the biomass, volume, jenkins. Use for "normal" stands.

        First use XFACTOR to tell if a fancy computation needs to be performed.

        :XFACTOR: a Capture object containing the detail plots, minimum dbhs, etc.
        :XFACTOR.detail_reference: plots which are detail plots and when
        :XFACTOR.stands_with_unusual_mins: plots which have minimums that are not 15 and are not detail plots
        :XFACTOR.unusual_plot_areas: plots whose areas are not 625 m

        **INTERNAL VARIABLES**

        :Biomasses: The output dictionary which will ultimately contain the biomass, Jenkins' biomass, volume, etc. for the stand. 
        
        .. Example: Compute the number of trees per hectare represented by this one 'PSME' from 1984.

        >>> A.shifted[1984].keys()
        >>> dict_keys(['alru', 'psme', 'pisi', 'thpl', 'tshe'])
        >>> A.shifted[1984]['psme']
        >>> {44: {'ingrowth': [], 'live': [('ncna004400023', 109.7, '1', '1984')], 'dead': []}}
        
        >>> 10000*(1/625)
        >>> 16.0

        """

        Biomasses = {}
        BadTreeRef = {}

        p_list = {}

        # if the stand id is one that should not be treated as a "normal" stand, return the empty dictionary, which is a signal that we should process using the special processing
        if self.standid in XFACTOR.detail_reference.keys() or self.standid in XFACTOR.uplot_areas.keys() or self.standid in XFACTOR.umins_reference.keys():
            
            return Biomasses, BadTreeRef

        else:
            all_years = sorted(self.shifted.keys())

            for index, each_year in enumerate(all_years):

                try:
                    # get the total area
                    total_area = self.total_area_ref[each_year]
                
                except KeyError:
                    # if the area is missing, then take the most recent one to it
                    list_areas = [x for x in sorted(list(self.total_area_ref.keys())) if x <=each_year]
                    total_area = self.total_area_ref[list_areas[-1]]


                for each_species in self.shifted[each_year].keys():
                    num_plots = len(self.shifted[each_year][each_species].keys())

                    for each_plot in self.shifted[each_year][each_species].keys():


                        #print("processing now .... (delete me later) ..." + str(each_year) + " | species " + str(each_species) + " | on plot " + str(each_plot))
                        
                        # figure out the representative percentage of all the area of the stand that this plot represents in the given year
                        percent_area_of_total = 625./total_area

                        # compute the dead trees first
                        if each_species == "acci": 

                            large_dead_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['dead'].items() if v[0] >= 15.0 and v[0] != None}
                            small_dead_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']),'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['dead'].items() if v[0] < 15.0 and v[0] != None}

                            large_live_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']),'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['live'].items() if v[0] >= 15.0 and v[0] != None}
                            small_live_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']),'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['live'].items() if v[0] < 15.0 and v[0] != None}

                            large_ingrowth_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']),'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['ingrowth'].items() if v[0] >= 15.0 and v[0] != None}
                            small_ingrowth_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']),'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['ingrowth'].items() if v[0] < 15.0 and v[0] != None}

                        elif each_species != "acci":
                            
                            
                            large_dead_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] >= 15.0}
                            small_dead_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] < 15.0}

                            large_live_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] >= 15.0}
                            small_live_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] < 15.0}

                            large_ingrowth_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] >= 15.0}
                            small_ingrowth_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] < 15.0}
                            
                        bad_dead_trees = [k for k in self.shifted[each_year][each_species][each_plot]['dead'].keys() if self.shifted[each_year][each_species][each_plot]['dead'][k] == None]
                        bad_live_trees = [k for k in self.shifted[each_year][each_species][each_plot]['live'].keys() if self.shifted[each_year][each_species][each_plot]['live'][k] == None]
                        bad_ingrowth_trees = [k for k in self.shifted[each_year][each_species][each_plot]['ingrowth'].keys() if self.shifted[each_year][each_species][each_plot]['ingrowth'][k] == None]
                        
                    
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

                        # dead trees of the "right size", and inclusive of the "small size" - do not divide by m2 yet here
                        try:
                            total_dead_trees = len(large_dead_trees)
                        except Exception:
                            total_dead_trees = 0.
                        try:
                            total_dead_trees_inclusive = (len(large_dead_trees) + len(small_dead_trees))
                        except Exception:
                            total_dead_trees_inclusive = 0.

                        # live trees of the "right size", and inclusive of the "small size"- do not divide by m2 yet here
                        try:
                            total_live_trees = len(large_live_trees)
                        except Exception:
                            total_live_trees = 0.
                        try:
                            total_live_trees_inclusive = (len(large_live_trees) + len(small_live_trees)) 
                        except Exception:
                            total_live_trees_inclusive = 0.

                        # ingrowth trees of the "right size", and inclusive of the "small size"- do not divide by m2 yet here
                        try:
                            total_ingrowth_trees = len(large_ingrowth_trees)
                        except Exception:
                            total_ingrowth_trees = 0.
                        try:
                            total_ingrowth_trees_inclusive = (len(large_ingrowth_trees) + len(small_ingrowth_trees))
                        except Exception:
                            total_ingrowth_trees_inclusive = 0.

                        #print("completed gathering for " + str(each_year) + ", " + str(each_species) + ", " + str(each_plot))

                        ## All these are "normal" so we know there is not any multiplying to do and we can divide the area by 625 to get the per Mg/m2 values for the species on that plot, that year. Multiply result by the percentage area of the total area that plot represents for that stand that year.

                        # the live trees, dead trees, and ingrowth trees counts have already been determined.
                        total_live_bio = round(sum([large_live_trees[tree]['bio'][0]/625. for tree in large_live_trees.keys()])*percent_area_of_total, 10)
                        total_ingrowth_bio = round(sum([large_ingrowth_trees[tree]['bio'][0]/625. for tree in large_ingrowth_trees.keys()])*percent_area_of_total, 10)
                        total_dead_bio = round(sum([large_dead_trees[tree]['bio'][0]/625. for tree in large_dead_trees.keys()])*percent_area_of_total, 10)

                        total_live_bio_inclusive = round(sum([large_live_trees[tree]['bio'][0]/625. for tree in large_live_trees.keys()])*percent_area_of_total + sum([small_live_trees[tree]['bio'][0]/625. for tree in small_live_trees.keys()])*percent_area_of_total, 10)
                        total_ingrowth_bio_inclusive = round(sum([large_ingrowth_trees[tree]['bio'][0]/625. for tree in large_ingrowth_trees.keys()])*percent_area_of_total + sum([small_ingrowth_trees[tree]['bio'][0]/625. for tree in small_ingrowth_trees.keys()])*percent_area_of_total, 10)
                        total_dead_bio_inclusive = round(sum([large_dead_trees[tree]['bio'][0]/625. for tree in large_dead_trees.keys()])*percent_area_of_total + sum([small_dead_trees[tree]['bio'][0]/625. for tree in small_dead_trees.keys()])*percent_area_of_total, 10)

                        total_live_jenkins = round(sum([large_live_trees[tree]['bio'][2]/625. for tree in large_live_trees.keys()])*percent_area_of_total, 10)
                        total_ingrowth_jenkins = round(sum([large_ingrowth_trees[tree]['bio'][2]/625. for tree in large_ingrowth_trees.keys()])*percent_area_of_total, 10)
                        total_dead_jenkins = round(sum([large_dead_trees[tree]['bio'][2]/625. for tree in large_dead_trees.keys()])*percent_area_of_total, 10)

                        total_live_jenkins_inclusive= round(sum([large_live_trees[tree]['bio'][2]/625. for tree in large_live_trees.keys()])*percent_area_of_total + sum([small_live_trees[tree]['bio'][2]/625. for tree in small_live_trees.keys()])*percent_area_of_total, 10)
                        total_ingrowth_jenkins_inclusive = round(sum([large_ingrowth_trees[tree]['bio'][2]/625. for tree in large_ingrowth_trees.keys()])*percent_area_of_total + sum([small_ingrowth_trees[tree]['bio'][2]/625. for tree in small_ingrowth_trees.keys()])*percent_area_of_total, 10)
                        total_dead_jenkins_inclusive = round(sum([large_dead_trees[tree]['bio'][2]/625. for tree in large_dead_trees.keys()])*percent_area_of_total + sum([small_dead_trees[tree]['bio'][2]/625. for tree in small_dead_trees.keys()])*percent_area_of_total, 10)

                        total_live_volume = round(sum([large_live_trees[tree]['bio'][1]/625. for tree in large_live_trees.keys()])*percent_area_of_total, 10)
                        total_ingrowth_volume = round(sum([large_ingrowth_trees[tree]['bio'][1]/625. for tree in large_ingrowth_trees.keys()])*percent_area_of_total, 10)
                        total_dead_volume = round(sum([large_dead_trees[tree]['bio'][1]/625. for tree in large_dead_trees.keys()])*percent_area_of_total, 10)

                        total_live_basal = round(sum([large_live_trees[tree]['ba']/625. for tree in large_live_trees.keys()])*percent_area_of_total, 10)
                        total_ingrowth_basal = round(sum([large_ingrowth_trees[tree]['ba']/625. for tree in large_ingrowth_trees.keys()])*percent_area_of_total, 10)
                        total_dead_basal = round(sum([large_dead_trees[tree]['ba']/625. for tree in large_dead_trees.keys()])*percent_area_of_total, 10)

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
                        living_trees = list(large_live_trees.keys())
                        living_trees_small = list(small_live_trees.keys())
                        ingrowth_trees = list(large_ingrowth_trees.keys())
                        ingrowth_trees_small = list(small_ingrowth_trees.keys())
                        dead_trees = list(large_dead_trees.keys())
                        dead_trees_small = list(small_dead_trees.keys())

                        # add the year to plot list if not there
                        if each_year not in Biomasses:
                            Biomasses[each_year] = {each_species : {'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'wooddensity': wooddensity, 'total_live_basal': total_live_basal, 'total_dead_basal': total_dead_basal, 'name_live': living_trees, 'total_ingrowth_basal': total_ingrowth_basal, 'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'name_live': living_trees, 'name_dead': dead_trees, 'name_ingrowth': ingrowth_trees, 'total_live_bio_inclusive': total_live_bio_inclusive, 'total_dead_bio_inclusive' : total_dead_bio_inclusive, 'total_ingrowth_bio_inclusive' : total_ingrowth_bio_inclusive, 'total_live_jenkins_inclusive' : total_live_jenkins_inclusive, 'total_dead_jenkins_inclusive' : total_dead_jenkins_inclusive, 'total_ingrowth_jenkins_inclusive': total_ingrowth_jenkins_inclusive, 'num_plots': num_plots}}
                        

                        elif each_year in Biomasses:
                            # do not need to augment the wood density :)
                            if each_species not in Biomasses[each_year]:
                                Biomasses[each_year][each_species] = {'total_live_bio': total_live_bio, 'total_dead_bio' : total_dead_bio, 'total_ingrowth_bio': total_ingrowth_bio, 'total_live_jenkins': total_live_jenkins, 'total_ingrowth_jenkins': total_ingrowth_jenkins, 'total_dead_jenkins' : total_dead_jenkins, 'total_live_volume' : total_live_volume, 'total_dead_volume' : total_dead_volume, 'total_ingrowth_volume': total_ingrowth_volume, 'total_live_basal': total_live_basal, 'total_dead_basal': total_dead_basal, 'name_live': living_trees, 'total_ingrowth_basal': total_ingrowth_basal,'total_live_trees': total_live_trees, 'total_dead_trees': total_dead_trees, 'total_ingrowth_trees': total_ingrowth_trees, 'name_live': living_trees, 'name_dead': dead_trees, 'wooddensity': wooddensity, 'name_ingrowth': ingrowth_trees, 'total_live_bio_inclusive': total_live_bio_inclusive, 'total_dead_bio_inclusive' : total_dead_bio_inclusive, 'total_ingrowth_bio_inclusive' : total_ingrowth_bio_inclusive, 'total_live_jenkins_inclusive' : total_live_jenkins_inclusive, 'total_dead_jenkins_inclusive' : total_dead_jenkins_inclusive, 'total_ingrowth_jenkins_inclusive': total_ingrowth_jenkins_inclusive, 'num_plots': num_plots}
                            
                            # all the plots can be added together for that species and year, no need to keep separate - area division has already happened for all except for the number of trees
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
                                
                                # count of all the live trees/ dead trees / ingrowth trees
                                Biomasses[each_year][each_species]['total_live_trees'] += total_live_trees
                                Biomasses[each_year][each_species]['total_dead_trees'] += total_dead_trees 
                                Biomasses[each_year][each_species]['total_ingrowth_trees'] += total_ingrowth_trees
                                
                                # names of all the live trees / dead trees / ingrowth trees
                                Biomasses[each_year][each_species]['name_live'] += living_trees
                                Biomasses[each_year][each_species]['name_dead'] += dead_trees
                                Biomasses[each_year][each_species]['name_ingrowth'] += ingrowth_trees

                                Biomasses[each_year][each_species]['num_plots'] = num_plots

                            else:
                                pass


        print("completed all normal biomass on " + str(self.standid))       
        return Biomasses, BadTreeRef

    def compute_special_biomasses(self, XFACTOR):
        """ Compute the biomass, volume, jenkins. Use for stands with alternate minimums, areas, or detail plots 

        First use the Capture object to tell if a fancy computation (i.e. get a special area, minimum, etc. needs to be performed.
            Load in the appropriate parameters for this computation. Separate "small" trees from "large" ones so that small ones can get the expansion factor. If they aren't on a detail plot, this number will just be "1".


        :XFACTOR: a Capture object containing the detail plots, minimum dbhs, etc.
        :XFACTOR.detail_reference: plots which are detail plots and when
        :XFACTOR.stands_with_unusual_mins: plots which have minimums that are not 15 and are not detail plots
        :XFACTOR.unusual_plot_areas: plots whose areas are not 625m

        ** Internal Variables **

        """

        Biomasses = {}
        BadTreeRef = {}
        
        all_years = sorted(self.shifted.keys())
        
        for each_year in all_years:
            total_area = self.total_area_ref[each_year]

            for each_species in self.shifted[each_year].keys():
                
                if each_species == 'pimo':
                    #print("found a pimo on {stand}".format(stand=self.standid))
                    continue

                else:
                    pass

                num_plots = len(self.shifted[each_year][each_species].keys())
                
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

                    # figure out the representative percentage of all the area of the stand that this plot represents in the given year
                    percent_area_of_total = area/total_area

                    # compute the dead trees first, if the dbh is not None - this is just for one plot!
                    if each_species == "acci":

                        large_dead_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['dead'].items() if v[0] >= 15.0 and v[0] != None}
                        small_dead_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']),'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['dead'].items() if v[0] < 15.0 and v[0] > mindbh and v[0] != None}

                        large_live_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']),'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['live'].items() if v[0] >= 15.0 and v[0] != None}
                        small_live_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']),'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['live'].items() if v[0] < 15.0 and v[0] > mindbh and v[0] != None}

                        large_ingrowth_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']),'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['ingrowth'].items() if v[0] >= 15.0 and v[0] != None}
                        small_ingrowth_trees = {k: {'bio': biomass_basis.as_compbio(v[0], self.eqns['acci']),'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k, v in self.shifted[each_year][each_species][each_plot]['ingrowth'].items() if v[0] < 15.0 and v[0] > mindbh and v[0] != None}
                
                    elif each_species != "acci":

                        large_dead_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] >= 15.0}
                        small_dead_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['dead'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}

                        large_live_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] >= 15.0}
                        small_live_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['live'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}

                        large_ingrowth_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] >= 15.0}
                        small_ingrowth_trees = {k: {'bio': self.eqns[each_species][biomass_basis.maxref(v[0], each_species)](v[0]), 'ba': round(0.00007854*float(v[0])*float(v[0]),4)} for k,v in self.shifted[each_year][each_species][each_plot]['ingrowth'].items() if v[0] != None and v[0] < 15.0 and v[0] > mindbh}
                    
                    bad_dead_trees = [k for k in self.shifted[each_year][each_species][each_plot]['dead'].keys() if self.shifted[each_year][each_species][each_plot]['dead'][k] == None]
                    bad_live_trees = [k for k in self.shifted[each_year][each_species][each_plot]['live'].keys() if self.shifted[each_year][each_species][each_plot]['live'][k] == None]
                    bad_ingrowth_trees = [k for k in self.shifted[each_year][each_species][each_plot]['ingrowth'].keys() if self.shifted[each_year][each_species][each_plot]['ingrowth'][k] == None]

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
                    total_live_bio = sum([large_live_trees[tree]['bio'][0]/area for tree in large_live_trees.keys()])*percent_area_of_total + sum([(small_live_trees[tree]['bio'][0]/area)*Xw for tree in small_live_trees.keys()])*percent_area_of_total
                    total_ingrowth_bio = sum([large_ingrowth_trees[tree]['bio'][0]/area for tree in large_ingrowth_trees.keys()]) * percent_area_of_total + sum([(small_ingrowth_trees[tree]['bio'][0]/area)*Xw for tree in small_ingrowth_trees.keys()]) * percent_area_of_total
                    total_dead_bio = sum([large_dead_trees[tree]['bio'][0]/area for tree in large_dead_trees.keys()]) * percent_area_of_total + sum([(small_dead_trees[tree]['bio'][0]/area)*Xw for tree in small_dead_trees.keys()]) * percent_area_of_total
                    
                    total_live_jenkins = sum([large_live_trees[tree]['bio'][2]/area for tree in large_live_trees.keys()]) * percent_area_of_total + sum([(small_live_trees[tree]['bio'][2]/area)*Xw for tree in small_live_trees.keys()]) * percent_area_of_total
                    total_ingrowth_jenkins = sum([large_ingrowth_trees[tree]['bio'][2]/area for tree in large_ingrowth_trees.keys()]) * percent_area_of_total + sum([(small_ingrowth_trees[tree]['bio'][2]/area)*Xw for tree in small_ingrowth_trees.keys()]) * percent_area_of_total
                    total_dead_jenkins = sum([large_dead_trees[tree]['bio'][2]/area for tree in large_dead_trees.keys()]) * percent_area_of_total + sum([(small_dead_trees[tree]['bio'][2]/area)*Xw for tree in small_dead_trees.keys()]) * percent_area_of_total

                    total_live_volume = sum([large_live_trees[tree]['bio'][1]/area for tree in large_live_trees.keys()]) * percent_area_of_total + sum([(small_live_trees[tree]['bio'][1]/area)*Xw for tree in small_live_trees.keys()]) * percent_area_of_total
                    total_ingrowth_volume = sum([large_ingrowth_trees[tree]['bio'][1]/area for tree in large_ingrowth_trees.keys()]) * percent_area_of_total + sum([(small_ingrowth_trees[tree]['bio'][1]/area)*Xw for tree in small_ingrowth_trees.keys()]) * percent_area_of_total
                    total_dead_volume = sum([large_dead_trees[tree]['bio'][1]/area for tree in large_dead_trees.keys()]) * percent_area_of_total+ sum([(small_dead_trees[tree]['bio'][1]/area)*Xw for tree in small_dead_trees.keys()]) * percent_area_of_total

                    total_live_basal = sum([large_live_trees[tree]['ba']/area for tree in large_live_trees.keys()]) * percent_area_of_total + sum([(live_trees_small[tree]['ba']/area)*Xw for tree in live_trees_small.keys()]) * percent_area_of_total
                    total_ingrowth_basal = sum([large_ingrowth_trees[tree]['ba']/area for tree in large_ingrowth_trees.keys()])* percent_area_of_total +  sum([(small_ingrowth_trees[tree]['ba']/area)*Xw for tree in small_ingrowth_trees.keys()]) * percent_area_of_total
                    total_dead_basal = sum([large_dead_trees[tree]['ba'] for tree in large_dead_trees.keys()])/area + sum([(small_dead_trees[tree]['ba']/area)*Xw for tree in small_dead_trees.keys()]) * percent_area_of_total

                    
                    # just take the wood density from one tree to have

                    try:
                        wooddensity = self.eqns[each_species][biomass_basis.maxref(25.0, each_species)](25.0)[3]
                        
                    except Exception:
                        import pdb; pdb.set_trace()
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


    def write_stand_live(self, Biomasses):
        """ Generates an output file containing ingrowth Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), and wood density, by species
        
        """
        filename_out = self.standid + "_stand_live_output.csv"

        with open(filename_out,'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            writer.writerow(['studyid','standid', 'year','species','total_live_bio_mg_ha','total_live_jenkins_mg_ha','total_live_volume_m3_ha','total_live_num_trees_ha','total_live_basal_m2_ha','wooddensity_g_cm3'])

            for each_year in Biomasses:
                for each_species in Biomasses[each_year]:
                  
                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row = [self.study_id.upper(), self.standid.upper(), each_year, each_species, round(Biomasses[each_year][each_species]['total_live_bio']*10000,3), round(Biomasses[each_year][each_species]['total_live_jenkins']*10000,3), round(Biomasses[each_year][each_species]['total_live_volume']*10000,3), int(Biomasses[each_year][each_species]['total_live_trees']), round(Biomasses[each_year][each_species]['total_live_basal']*10000,3), Biomasses[each_year][each_species]['wooddensity']]
                    
                    writer.writerow(new_row)

    def write_stand_dead(self, Biomasses):
        """ Generates an output file containing dead Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), and wood density, by species
        
        """
        filename_out = self.standid + "_stand_dead_output.csv"
        with open(filename_out,'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            writer.writerow(['studyid', 'standid','year','species','total_dead_bio_mg_ha','total_dead_jenkins_mg_ha','total_dead_volume_m3_ha','total_dead_num_trees_ha','total_dead_basal_m2_ha','wooddensity_g_cm3'])

            for each_year in Biomasses:
                for each_species in Biomasses[each_year]:
                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row = [self.studyid.upper(), self.standid.upper(), each_year, each_species, round(Biomasses[each_year][each_species]['total_dead_bio']*10000,3), round(Biomasses[each_year][each_species]['total_dead_jenkins']*10000,3), round(Biomasses[each_year][each_species]['total_dead_volume']*10000,3), int(Biomasses[each_year][each_species]['total_dead_trees']), round(Biomasses[each_year][each_species]['total_dead_basal']*10000, 3), Biomasses[each_year][each_species]['wooddensity']]
                    
                    writer.writerow(new_row)

    def write_stands_ingrowth(self, Biomasses):
        """ Generates an output file for stands which does NOT break the live, dead, and ingrowth Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins' Biomass ( Mg ), and wood density, by species, into separate files

        """

        filename_out = self.standid + "_stand_all_output.csv"

        with open(filename_out, 'w') as writefile:

            writer.writerow(['study_id','stand_id','year','species','total_ingrowth_bio_mg_ha','total_ingrowth_jenkins_mg_ha','total_ingrowth_volume_m3_ha','total_ingrowth_num_trees_ha','total_ingrowth_basal_m2_ha','wooddensity_g_cm3'])

            for each_year in Biomasses:
                for each_species in Biomasses[each_year]:
                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row = [self.study_id.upper(), self.standid.upper(), each_year, each_species, round(Biomasses[each_year][each_species]['total_ingrowth_bio']*10000,3), round(Biomasses[each_year][each_species]['total_ingrowth_jenkins']*10000,3), round(Biomasses[each_year][each_species]['total_ingrowth_volume']*10000,3), int(Biomasses[each_year][each_species]['total_ingrowth_trees']), round(Biomasses[each_year][each_species]['total_ingrowth_basal']*10000, 3), Biomasses[each_year][each_species]['wooddensity']]
                    
                    writer.writerow(new_row)

    def write_stand_normalized(self, Biomasses):
        """ Generates an output file containing ingrowth Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins' Biomass ( Mg ), and wood density, by species
        """
        filename_out = self.standid + "_stand_normalized_output.csv"
        with open(filename_out,'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            writer.writerow(['DBCODE','ENTITY','STUDYID', 'STANDID', 'SPECIES', 'YEAR', 'STATUS','TPH','BA_M2HA','VOLM3_HA','BIO_MGHA','JBIO_MGHA','WOODDEN','NPLOTS_SPECIES'])

            for each_year in sorted(Biomasses.keys()):
                for each_species in Biomasses[each_year]:
                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row = ['TP001', '08', self.study_id.upper(), self.standid.upper(), each_species, each_year,'INGROWTH', int(Biomasses[each_year][each_species]['total_ingrowth_trees']), round(Biomasses[each_year][each_species]['total_ingrowth_basal']*10000, 3), round(Biomasses[each_year][each_species]['total_ingrowth_volume']*10000,3), round(Biomasses[each_year][each_species]['total_ingrowth_bio']*10000,3), round(Biomasses[each_year][each_species]['total_ingrowth_jenkins']*10000,3), Biomasses[each_year][each_species]['wooddensity'], Biomasses[each_year][each_species]['num_plots']]
                    
                    writer.writerow(new_row)

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row = ['TP001', '08', self.study_id.upper(), self.standid.upper(), each_species, each_year,'LIVE', int(Biomasses[each_year][each_species]['total_live_trees']), round(Biomasses[each_year][each_species]['total_live_basal']*10000, 3), round(Biomasses[each_year][each_species]['total_live_volume']*10000,3), round(Biomasses[each_year][each_species]['total_live_bio']*10000,3), round(Biomasses[each_year][each_species]['total_live_jenkins']*10000,3), Biomasses[each_year][each_species]['wooddensity'], Biomasses[each_year][each_species]['num_plots']]
                 
                    writer.writerow(new_row)

                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row = ['TP001', '08', self.study_id.upper(), self.standid.upper(), each_species, each_year,'MORT', int(Biomasses[each_year][each_species]['total_dead_trees']), round(Biomasses[each_year][each_species]['total_dead_basal']*10000, 3), round(Biomasses[each_year][each_species]['total_dead_volume']*10000,3), round(Biomasses[each_year][each_species]['total_dead_bio']*10000,3), round(Biomasses[each_year][each_species]['total_dead_jenkins']*10000,3), Biomasses[each_year][each_species]['wooddensity'], Biomasses[each_year][each_species]['num_plots']]

                    writer.writerow(new_row)

    def write_stand_normalized_aggregate(self, Biomasses_Agg, XFACTOR):
        """ Generates an output file containing ingrowth Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins' Biomass ( Mg ), and wood density, not by species but for the whole stand.

        Uses the Capture object to tell the total number of plots on that stand during that year

        """
        filename_out = self.standid + "_stand_aggregate_output.csv"
        
        with open(filename_out,'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            writer.writerow(['DBCODE','ENTITY','STUDYID', 'STANDID', 'YEAR', 'STATUS','TPH','BA_M2HA','VOLM3_HA','BIO_MGHA','JBIO_MGHA', 'NUM_PLOTS_STAND'])

            #print(sorted(Biomasses_Agg.keys()))

            for each_year in sorted(Biomasses_Agg.keys()):

                try:
                    # remember to multiply by 10000 to go from m2 to hectare
                    new_row1 = ['TP001', '08', self.study_id.upper(), self.standid.upper(), each_year,'INGROWTH', int(Biomasses_Agg[each_year]['total_ingrowth_trees']), round(Biomasses_Agg[each_year]['total_ingrowth_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_ingrowth_volume']*10000,3), round(Biomasses_Agg[each_year]['total_ingrowth_bio']*10000,3), round(Biomasses_Agg[each_year]['total_ingrowth_jenkins']*10000,3), XFACTOR.num_plots[self.standid.lower()][each_year]]
                except Exception:
                    try:
                        new_row1 = ['TP001', '08', self.study_id.upper(), self.standid.upper(), each_year,'INGROWTH', int(Biomasses_Agg[each_year]['total_ingrowth_trees']), round(Biomasses_Agg[each_year]['total_ingrowth_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_ingrowth_volume']*10000,3), round(Biomasses_Agg[each_year]['total_ingrowth_bio']*10000,3), round(Biomasses_Agg[each_year]['total_ingrowth_jenkins']*10000,3), None]
                        print("temp plot table does not include " + self.standid + "in " + str(each_year))
                    except Exception:
                        import pdb; pdb.set_trace()

                # remember to multiply by 10000 to go from m2 to hectare
                try:
                    new_row2 = ['TP001', '08', self.study_id.upper(), self.standid.upper(), each_year,'LIVE', int(Biomasses_Agg[each_year]['total_live_trees']), round(Biomasses_Agg[each_year]['total_live_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_live_volume']*10000,3), round(Biomasses_Agg[each_year]['total_live_bio']*10000,3), round(Biomasses_Agg[each_year]['total_live_jenkins']*10000,3), XFACTOR.num_plots[self.standid.lower()][each_year]]
                except Exception:
                    try:
                        new_row2 = ['TP001', '08', self.study_id.upper(), self.standid.upper(), each_year,'LIVE', int(Biomasses_Agg[each_year]['total_live_trees']), round(Biomasses_Agg[each_year]['total_live_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_live_volume']*10000,3), round(Biomasses_Agg[each_year]['total_live_bio']*10000,3), round(Biomasses_Agg[each_year]['total_live_jenkins']*10000,3), None]
                    except Exception:
                        import pdb; pdb.set_trace()

                # remember to multiply by 10000 to go from m2 to hectare
                try:
                    new_row3 = ['TP001', '08', self.study_id.upper(), self.standid.upper(), each_year,'MORT', int(Biomasses_Agg[each_year]['total_dead_trees']), round(Biomasses_Agg[each_year]['total_dead_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_dead_volume']*10000,3), round(Biomasses_Agg[each_year]['total_dead_bio']*10000,3), round(Biomasses_Agg[each_year]['total_dead_jenkins']*10000,3), XFACTOR.num_plots[self.standid.lower()][each_year]]
                except Exception:
                    try:
                        new_row3 = ['TP001', '08', self.study_id.upper(), self.standid.upper(), each_year,'MORT', int(Biomasses_Agg[each_year]['total_dead_trees']), round(Biomasses_Agg[each_year]['total_dead_basal']*10000, 3), round(Biomasses_Agg[each_year]['total_dead_volume']*10000,3), round(Biomasses_Agg[each_year]['total_dead_bio']*10000,3), round(Biomasses_Agg[each_year]['total_dead_jenkins']*10000,3), None]
                    except Exception:
                        import pdb; pdb.set_trace()

                writer.writerow(new_row1)
                writer.writerow(new_row2)
                writer.writerow(new_row3)



    def check_stand_members(self, BadTreeRef):
        """ Generates an output file containing ingrowth Biomass ( Mg ), Volume (m\ :sup:`3`), Jenkins'' Biomass ( Mg ), and wood density, by species
        
        """
        filename_out = self.standid + "_stand_member_check.csv"
        with open(filename_out, 'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)
            
            writer.writerow(['studyid','standid','year', 'species', 'plot', 'treeid', 'state', 'issue'])

            for each_year in BadTreeRef:
                for each_species in BadTreeRef[each_year]:
                    for each_plot in BadTreeRef[each_year][each_species]:
                        if BadTreeRef[each_year][each_species][each_plot]['dead'] == []:
                            pass
                        else:
                            for each_tree in BadTreeRef[each_year][each_species][each_plot]['dead']:
                                writer.writerow([self.study_id.upper,each_year, each_species, each_plot, each_tree, 'dead', 'dbh is None'])

                        if BadTreeRef[each_year][each_species][each_plot]['live'] == []:
                            pass
                        else:
                            for each_tree in BadTreeRef[each_year][each_species][each_plot]['live']:
                                writer.writerow([each_year, each_species, each_plot, each_tree, 'live', 'dbh is None'])

                        if BadTreeRef[each_year][each_species][each_plot]['ingrowth'] == []:
                            pass
                        else:
                            for each_tree in BadTreeRef[each_year][each_species][each_plot]['ingrowth']:
                                writer.writerow([each_year, each_species, each_plot, each_tree, 'ingrowth', 'dbh is None'])

class QC(object):
    """ Conducts Stand level quality control if needed

    """

    def __init__(self, target):
        """ Initializes the QC
        """

        self.target = target
        self.BM = {}
        self.BTR = {}

        self.parse_target()


    def parse_target(self):
        """ Decides to do one or many stands. Fails if no stands are given.
        """
        if self.target == []:
            return False

        elif isinstance(self.target, list):
            self.check_many_stand()

        elif isinstance(self.target, str):
            self.check_one_stand()
            self.population_check()

    def check_one_stand(self):
        """ Sets up the needed inputs
        """
        DATABASE_CONNECTION = poptree_basis.YamlConn()
        conn, cur = DATABASE_CONNECTION.sql_connect()
        pconn, pcur = DATABASE_CONNECTION.lite3_connect()
        queries = DATABASE_CONNECTION.queries
        XFACTOR = poptree_basis.Capture()

        A = Stand(cur, pcur, XFACTOR, queries, self.target)

        BM, BTR = A.compute_normal_biomasses(XFACTOR)
        
        # if the stands are not normal, compute them in the special way
        if BM == {}:
            BM, BTR = A.compute_special_biomasses(XFACTOR)

    def population_check(self):
        """ Gets the tree check data from each year and species.

        * Check if a tree dies in the first year, but is still present in the next year 
        * Check if a tree is alive in the first year, but is not present in the next year 
        * Check if a tree is ingrowth in the first year, but is not a live or dead tree in the next year
        """
        # find trees whose ID's are "lost" between remeasurements
        lost_trees = {}

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
            second_species_list = self.BM[each_year].keys()

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

    def check_many_stands(self):
        """ Sets up the needed inputs
        """
        DATABASE_CONNECTION = poptree_basis.YamlConn()
        conn, cur = DATABASE_CONNECTION.sql_connect()
        pconn, pcur = DATABASE_CONNECTION.lite3_connect()
        queries = DATABASE_CONNECTION.queries
        XFACTOR = poptree_basis.Capture()


if __name__ == "__main__":

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    pconn, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries

    # creates lookups for expansion factors
    XFACTOR = poptree_basis.Capture()

    #A = Stand(cur, pcur, XFACTOR, queries, 'CFMF')
    #import pdb; pdb.set_trace()
    #test_stands = ['CFMF','AV06','WI01','NCNA', 'AG05', 'AB08', 'AX15', 'PP17', 'TO11', 'AV14', 'RS31', 'RS28', 'RS01', 'RS02', 'RS30', 'TB13', 'AR07', 'AM16', 'RS29', 'RS32', 'AE10', 'AV06', 'TO04']
    
    test_stands = ["NCNA"]
    for each_stand in test_stands:
        
        A = Stand(cur, pcur, XFACTOR, queries, each_stand)

        BM, BTR = A.compute_normal_biomasses(XFACTOR)
        
        if BM == {}:
            Biomasses, BadTreeSpec = A.compute_special_biomasses(XFACTOR)
            A.write_stand_normalized(Biomasses)

            Biomasses_aggregate = A.aggregate_biomasses(Biomasses)
            A.write_stand_normalized_aggregate(Biomasses_aggregate, XFACTOR)
            #A.write_stand_live(Biomasses)
            #A.write_stand_dead(Biomasses)
            #A.write_stand_ingrowth(Biomasses)

            if BadTreeSpec == {}:
                pass
            else:
                A.check_stand_members(BadTreeSpec)
            del Biomasses, BadTreeSpec

    
        else:
            A.write_stand_normalized(BM) 
            BMA = A.aggregate_biomasses(BM)
            A.write_stand_normalized_aggregate(BMA, XFACTOR)
            #A.write_stand_live(BM)
            #A.write_stand_dead(BM)
            #A.write_stand_ingrowth(BM)

            if BTR == {}:
                pass
            else:
                A.check_stand_members(BTR)
        del BM, BTR
        


