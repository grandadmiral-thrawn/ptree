#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import biomass_basis

"""
tps.py contains the classes for Trees, Plots, and Stands.
DATABASE_CONNECTION is a global connection object which doesn''t need to get called with every single tree!
"""

class Tree(object):
    """ A Tree object contains the required metrics and functions to compute biomass, Jenkins' biomass, volume, and basal area for any one tree over any of the years of its remeasurement.

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

    .. note :: A.state contains [year, dbh, status, dbh_code]
    .. warning:: A.cur must be created in an external variable

    **METHODS**

    """

    def __init__(self, cur, pcur, queries, tid):

        self.tid = str(tid).strip().lower()
        self.cur = cur
        self.pcur = pcur
        self.tree_query = queries['tree']['sql_1tree']
        self.eqn_query = queries['tree']['sql_1tree_eqn']
        self.is_detail = queries['plot']['lite_plot_dtl']
        self.species = ""
        self.state = ()
        self.eqns = {}
        self.woodden = 0.0

        self.get_a_tree()

    def get_a_tree(self):
        """ get a single tree and all of its history
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
            try:
                h1 = round(float(str(row[3])),3)
            except:
                h1 = None
            try:
                h2 = round(float(str(row[4])),3)
            except:
                h2 = None
            try:
                h3 = round(float(str(row[5])),3)
            except:
                h3 = None
            try:
                b1 = round(float(str(row[6])),3)
            except:
                b1 = None
            try:
                b2 = round(float(str(row[7])),3)
            except:
                b2 = None
            try:
                b3 = round(float(str(row[8])),3)
            except:
                b3 = None
            try:
                j1 = round(float(str(row[9])),3)
            except:
                j1 = None
            try:
                j2 = round(float(str(row[10])),3)
            except:
                j2 = None


            if form != 'as_compbio':
                this_eqn = lambda x : biomass_basis.which_fx(form)(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                self.eqns.update({str(row[1]):this_eqn})

            elif form == 'as_compbio':
                this_eqn = lambda x: biomass_basis.which_fx('as_biopak')(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3)
                self.eqns.update({str(row[12]):this_eqn})

    def compute_biomasses(self):
        """ Compute biomass, volume, Jenkins' biomass and wood density from equations
        """
        try:
            list_of_biomasses = [self.eqns[biomass_basis.maxref(x, self.species)](x) for (_,x,_,_) in self.state]
        except Exception as e:
            try:
                list_of_biomasses = [self.eqns['normal'](x) for (_,x,_,_) in self.state]
            
            except Exception as e2:
                # if the final dbh is missing and the tree is dead or missing, take the final year from that missing value and give it the biomass, volume, and jenkins of the prior value
                if self.state[-1][1:3] == [None,'6'] or self.state[-1][1:3] == [None,'9']:
                    final_year = self.state[-1][0]
                    
                    list_of_biomasses = [self.eqns[biomass_basis.maxref(x, self.species)](x) for (_,x,_,_) in self.state[:-1]]
                    
                    final_biomasses = list_of_biomasses[-1]
                    list_of_biomasses.append(final_biomasses)

                else:
                    # new errors to debug
                    import pdb; pdb.set_trace()

        return list_of_biomasses

    def compute_basal_area(self):
        """ compute basal area from equations"""
        basal = [round(0.00007854*float(x),3) for (_,x,_,_) in self.state]
        return basal

    def is_detail(self, standid, plot, year):
        """ Returns true if the plot is a detail plot and the tree has a dbh which is less than 15 but greater than the minimum dbh listed. Otherwise, return false

        :standid: the stand of a tree object
        :plot: the plotid attribute of a tree object
        :dbh: the dbh attribute of a tree object
        :year: the year attribute of a tree object
        """
        self.pcur.execute(self.queries['plot']['lite_plot_dtl'].format(standid=self.standid, plot=self.plot, year=year))
        for row in self.pcur:
            if str(row[0]) == "T":
                return True
            else:
                return False

    def output_tree(self):
        ###

        #you are here!
        ###
        #[[x,y,z,c,b] for (x,y,z,c) in A.state for b in basal if z =='1']
        pass

if __name__ == "__main__":

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    pconn, pcur = DATABASE_CONNECTION.lite3_connect()
    queries = DATABASE_CONNECTION.queries
    A = Tree(cur, pcur, queries, 'NCNA000100014')
    h = A.compute_biomasses()
    print(h)
    print("end!")
