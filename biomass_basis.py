#!/usr/bin/python3
# -*- coding: utf-8 -*-

import math

def maxref(dbh, species):
    """ check if an instance of dbh and species is bigger than the max. the max was found from the upper 1 percent ( I think!) per tree"""
    if dbh == None or dbh == "None":
        return False
    else:
        maxlookup = {"ABAM": 150.,
            "ABCO": 150.,
            "ABGR": 112.,
            "ABLA": 108.,
            "ABLA2": 108.,
            "ABMA": 150.,
            "ABPR": 150.,
            "ACCI": 14.,
            "ACGL": 20.,
            "ACMA": 105.,
            "ALIN": 12.,
            "ALRU": 104.,
            "ALSI": 8.,
            "ARME": 50.,
            "CACH": 53.,
            "CADE": 150.,
            "CADE3": 150.,
            "CHNO": 150.,
            "CONU": 33.,
            "LIDE": 150.,
            "LIDE2": 150.,
            "MAFU": 17.,
            "PICO": 65.,
            "PIEN": 130.,
            "PIJE": 150.,
            "PILA": 150.,
            "PIMO": 140.,
            "PIPO": 140.,
            "PISI": 150.,
            "POTR": 36.,
            "POTR2": 52.,
            "PREM": 24.,
            "PRUNU": 32.,
            "PSME": 150.,
            "QUGA": 28.,
            "QUKE": 60.,
            "RHPU": 30.,
            "SASC": 14.,
            "SEGI": 150.,
            "TABR": 80.,
            "THPL": 150.,
            "TSME": 140.,}
        if maxlookup[species.upper()] <= float(dbh):
            return "big"
        else:
            return "normal"

def as_lnln(woodden, x, b1, b2, b3, j1, j2, *args):
    """ shapes a biomass equation based on inputs of b1, b2, b3, and wood density onto variable x which is for the dbh"""
    try:
        biomass = round(b1*woodden*(b2*x**b3),4)
        volume = round(biomass/woodden,4)
        jbio = round(0.001*math.exp(j1+j2*math.log(round(x,2))),5)
        return (biomass, volume, jbio, woodden)
    except ValueError:
        return (0., 0., 0., woodden)


def as_d2ht(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3):
    """ shapes a biomass equation based on inputs of h1, h2, h3, and b1 and wood density onto the variable x which is for the dbh"""
    try:
        height = 1.37+ h1*(1-math.exp(h2*x))**h3
        biomass =  round(woodden*(height*b1*(0.01*x)**2),4)
        jbio = round(0.001*math.exp(j1+j2*math.log(round(x,2))),5)
        volume = round(biomass/woodden,4)
        return (biomass, volume, jbio, woodden)
    except ValueError:
        return (0., 0., 0., woodden)

def as_d2htcasc(woodden, x, b1, b2, b3, j1, j2, *args):
    """ shapes a biomass equation based on inputs of b1, b2, b3, and wood density onto the variable x which is for the dbh. cascades variety does not need height or the adjustment by m2"""
    try:
        biomass = round(b1*woodden*(b2*x**b3),4)
        jbio = round(0.001*math.exp(j1+j2*math.log(round(x,2))),5)
        volume = round(biomass/woodden,4)
        return (biomass, volume, jbio, woodden)
    except ValueError:
        return (0., 0., 0., woodden)


def as_biopak(woodden, x, b1, b2, b3, j1, j2, *args):
    """ shapes a biomass equation based on inputs of b1, b2 and wood density onto the variable x which is for the dbh. does not use height or wood density directly"""
    try:
        jbio = round(0.001*math.exp(j1+ j2*math.log(round(x,2))),5)
        biomass = round(1.*10**(-6)*math.exp(b1 + b2 * math.log(x)),4)
        volume = round(biomass/woodden,4)
        return (biomass, volume, jbio, woodden)
    except ValueError:
        return (0., 0., 0., woodden)

def as_chinq_biopak(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3):
    """ shapes a biomass equation based on inputs of h1, h2, h3, b1, b2, and b3, plus wood density onto the variable x which is for the dbh. uses pretty much all the inputs directly and calculates volume. chinquapin. """
    try:
        height = 1.37 + h1*(1-math.exp(h2*x))**h3
        biomass =  round(woodden*height**b1*b2*(x)**b3,4)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(x,2))),5)
        volume = round(biomass/woodden,4)
        return (biomass, volume, jbio, woodden)
    except ValueError:
        return (0., 0., 0., woodden)

def as_oak_biopak(woodden, x, b1, b2, b3, j1, j2, h1, h2, h3):
    """ shapes a biomass equation based on inputs of h1, h2, h3, b1, b2, and b3, plus wood density onto the variable x which is for the dbh. uses pretty much all the inputs directly and calculates volume. things in quercus family. """
    try:
        height = 1.37+h1*(1-math.exp(h2*x))**h3
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(x,2))),4)
        biomass = round(math.exp(b1 + b2*math.log(0.01*x) + b3*math.log(height)),4)
        volume = round(biomass/woodden,4)
        return (biomass, volume, jbio, woodden)
    except ValueError:
        return (0., 0., 0., woodden)

def as_compbio(x, parameter_rows):
    """ shapes a biomass equation based on the inputs of b1, b2, and wood density onto the variable x which is the dbh. adds the components from each row in the table it needs. only works with a few trees."""
    try:
        biomass = 0.
        volume = 0.

        for index, each_parameter_set in enumerate(parameter_rows):
            if index == 0:
                jbio = round(0.001*math.exp(j1+j2*math.log(round(x,2))),5)
            else:
                pass

            bio_1, vol_1,_,_ = as_biopak(b1, b2, woodden, x)
            biomass += bio_1
            volume += vol_1
        return (biomass, volume, jbio, woodden)
    except ValueError:
        return (0.,0.,0.,woodden)

def which_fx(function_string):
    """ find the correct function for doing the biomass in the lookup table"""

    lookup = {'as_lnln': as_lnln,
    'as_compbio': as_compbio,
    'as_oak_biopak': as_oak_biopak,
    'as_chinq_biopak': as_chinq_biopak,
    'as_biopak': as_biopak,
    'as_d2htcasc': as_d2htcasc,
    'as_d2ht': as_d2ht}

    return lookup[function_string]
