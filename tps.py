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
    """ 
    ex. A = Tree(cur, 'NCNA001800216')
    A.tid = 'ncna001800216'
    A.cur = <pymssql.cursor>
    A.tree_query= "SELECT <columns> from ..."
    A.eqn_query = "SELECT <columns> from ..."
    A.species = "TSHE"
    A.state = [[1942, 16.0, '1', 'G'], [1945, 17.9, '1','G']]
    A.eqns = {'normal' : lambda x :<function 039459x342>}
    A.woodden = 0.44
    states are the [year, dbh, status, dbh_code]

    """
 
    def __init__(self, cur, tid):

        self.tid = str(tid).strip().lower()
        self.cur = cur
        self.tree_query = DATABASE_CONNECTION.queries['tree']['sql_1tree']
        self.eqn_query = DATABASE_CONNECTION.queries['tree']['sql_1tree_eqn']
        self.species = "" 
        self.state = []
        self.eqns = {}
        self.woodden = 0.0

        self.get_a_tree()

    def get_a_tree(self):
        """ get a single tree and all of its history"""
        sql = self.tree_query.format(tid=self.tid)
        
        cur.execute(sql)
        
        for index,row in enumerate(cur):
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
        cur.execute(sql_2)

        for row in cur:
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
            """ compute biomass from equations : bio, vol, jenkins, woodden"""
            list_of_biomasses = [self.eqns[biomass_basis.maxref(x, self.species)](x) for (_,x,_,_) in self.state]
        
        def compute_basal_area(self):
            """ compute basal area from equations"""
            basal = [round(0.00007854*float(x),3) for (_,x,_,_) in self.state]
            return basal
            
        def output_tree(self):
            ###

            #you are here!
            ###
            #[[x,y,z,c,b] for (x,y,z,c) in A.state for b in basal if z =='1']
            pass

if __name__ == "__main__":
    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    # lite3db for eqns and plots -- these will be removed when we go to the main database --
    pconn, pcur = DATABASE_CONNECTION.lite3_connect('plots')
