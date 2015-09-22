#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import biomass_basis
import bisect

class Stand(object):
    """Stands contain a list of plots by year, as well as summary of biomass, volume, 


    """
    def __init__(self, cur, pcur, Xfactor, queries, standid):
        self.standid = standid
        self.has_details = False
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
        self.check_details(Xfactor)

        self.select_eqns()

        self.get_all_trees()

        # checks if it is a mortality plot, and, if so, shifts the dbhs to the year they should be on for the death totals
        is_mort = self.check_mort()
        self.update_mort(is_mort)

    def check_details(self, Xfactor):
        """ If the stand is in the Xfactor list, we need to check for detail plots, otherwise, don't bother

        :Xfactor: is an DetailCapture() object created by poptree_basis. It does not need to be re-created for more stands.

        :Example:
        >>> Xfactor = poptree_basis.DetailCapture()
        """
        if self.standid.upper() in Xfactor.detail_reference.keys():
            self.has_details = True
        else:
            self.has_details = False

    def select_eqns(self):
        """ Get only the equations you need based on the species on that plot

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


                if form != 'as_compbio':
                    this_eqn = lambda x : biomass_basis.which_fx(form)(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                    self.eqns.update({str(row[1]):this_eqn})

                elif form == 'as_compbio':
                    this_eqn = lambda x: biomass_basis.which_fx('as_biopak')(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                    self.eqns.update({str(row[12]):this_eqn})

    def get_all_trees(self):
        """ Get the trees and sort them by year, plot, live or dead, and species
        """
        cur.execute(queries['stand']['query'].format(standid=self.standid))
        
        for row in cur:
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
                dbh = round(float(row[3]),3)
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

            if year not in self.od and status in ["6","9"]:
                self.od[year]={plotid:{'live':{}, 'dead':{species:[(tid, dbh, status, dbh_code)]}}}
            elif year not in self.od and status not in ["6","9"]:
                self.od[year]={plotid:{'live':{species:[(tid, dbh, status, dbh_code)]}, 'dead':{species:[(tid, dbh, status, dbh_code)]}}}

            elif year in self.od:
                if plotid not in self.od[year] and status in ["6","9"]:
                    self.od[year][plotid] ={'live':{}, 'dead':{species:[(tid, dbh, status, dbh_code)]}}
                elif plotid not in self.od[year] and status not in ["6","9"]:
                    self.od[year][plotid] ={'live':{species:[(tid, dbh, status, dbh_code)]}, 'dead':{}}
                elif plotid in self.od[year]:
                    if status in ["6","9"] and species not in self.od[year][plotid]['dead']:
                        self.od[year][plotid]['dead']={species:[(tid, dbh, status, dbh_code)]}
                    elif status not in ["6","9"] and species not in self.od[year][plotid]['live']:
                        self.od[year][plotid]['live']={species:[(tid, dbh, status, dbh_code)]}
                    elif status not in ["6","9"] and species in self.od[year][plotid]['live']:
                        self.od[year][plotid]['live'][species].append((tid, dbh, status, dbh_code))
                    elif status in ["6","9"] and species in self.od[year][plotid]['dead']:
                        self.od[year][plotid]['dead'][species].append((tid, dbh, status, dbh_code))


    def check_mort(self):
        """ Check if the year is a mortality year, and if so, bisect it into the subsequent live year
        """
        list_all_years_possible_mortality = [year for year in self.od.keys() for x in self.od[year].keys() if self.od[year][x]['live'] =={}] 

        if list_all_years_possible_mortality == []:
            self.shifted = self.od
            return False
        else:
            mortality_years_comp = {year:None for year in list_all_years_possible_mortality}
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
            list_live_years = [x for x in sorted(self.od.keys()) if x not in self.mortality_years]

            self.shifted = {x:self.od[x] for x in list_live_years}
            
            for each_year in self.mortality_years:
                current_data = self.od[each_year]
                
                index = bisect.bisect_right(list_live_years, each_year)
                update_year = list_live_years[index]

                if update_year not in self.shifted.keys():
                    self.shifted[update_year] = current_data
                elif update_year in self.shifted.keys():
                    for each_plot in current_data.keys():
                        if each_plot not in self.shifted[update_year].keys():
                            self.shifted[update_year][each_plot] = current_data[each_plot]
                        elif each_plot in self.shifted[update_year].keys():
                            if self.shifted[update_year][each_plot]['dead'] =={}:
                                self.shifted[update_year][each_plot]['dead'].update(current_data[each_plot]['dead'])
                            elif self.shifted[update_year][each_plot]['dead'] != {}:
                                for each_species in current_data[each_plot]['dead'].keys():
                                    if each_species not in self.shifted[update_year][each_plot]['dead'].keys():
                                        self.shifted[update_year][each_plot]['dead'][each_species] = current_data[each_plot]['dead'][each_species]
                                    elif each_species in self.shifted[update_year][each_plot]['dead'].keys():
                                        self.shifted[update_year][each_plot]['dead'][each_species].append(current_data[each_plot]['dead'][each_species])


    def prepare_if_detail(self, Xfactor, given_year):
        """ Find the years that are detail plots, if there are any

        :Xfactor: a DetailCapture object containing the detail plots
        :given_year: a year for which biomass should be computed
        """
        if self.has_details == False:
            return False
        elif given_year not in Xfactor.detail_reference[self.standid.upper()].keys():
            return False
        elif given_year in Xfactor.detail_reference[self.standid.upper()].keys():
            expand_with = Xfactor.expansion[self.standid.upper()][given_year]
            expand_on = Xfactor.detail_reference[self.standid.upper()][given_year]['T_plots']
        return expand_with, expand_on


    def compute_biomasses(self):
        """ Compute the biomass using the same methods as for individual trees, but now for stands
        """
        pass

if __name__ == "__main__":

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    pconn, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries

    
    # creates lookups for expansion factors
    Xfactor = poptree_basis.DetailCapture()

    A = Stand(cur, pcur, Xfactor, queries, 'AV06')


    
    import pdb; pdb.set_trace();

    B = Stand(cur, pcur, Xfactor, queries, 'WI01')