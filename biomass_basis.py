#!/usr/bin/python3
# -*- coding: utf-8 -*-

import math

def maxref(dbh, species):
    """ Check if given dbh and given species is bigger than the maximum for that combination. The max was found from determining the top 1 percent of dbh's for each species.

    **INPUTS**
    
    :dbh: the tree's dbh, in cm
    :species: the tree's species, a four character code. If the database provides a longer code, it will be converted to a lowercase four letter code.

    .. Example:

    >>> maxref(20.0, 'ABAM')
    >>> "normal"
    
    """
    if dbh == None or dbh == "None":
        return False
    
    else:
        maxlookup = {"abam" : 150.,
            "abco": 150.,
            "abgr": 112.,
            "abla": 108.,
            "abla2": 108.,
            "abma": 150.,
            "abpr": 150.,
            "acci": 14.,
            "acgl": 20.,
            "acma": 105.,
            "alin": 12.,
            "alru": 104.,
            "alsi": 8.,
            "arme": 50.,
            "cach": 53.,
            "cade": 150.,
            "cade3": 150.,
            "chno": 150.,
            "conu": 33.,
            "lide": 150.,
            "lide2": 150.,
            "mafu": 17.,
            "pico": 65.,
            "pien": 130.,
            "pije": 150.,
            "pila": 150.,
            "pimo": 140.,
            "pipo": 140.,
            "pisi": 150.,
            "potr": 36.,
            "potr2": 52.,
            "prem": 24.,
            "prunu": 32.,
            "psme": 150.,
            "quga": 28.,
            "quke": 60.,
            "rhpu": 30.,
            "sasc": 14.,
            "segi": 150.,
            "tabr": 80.,
            "thpl": 150.,
            "tsme": 140.,}
        try:
            if maxlookup[species.rstrip().lower()] <= float(dbh): 
                return "big"
            
            else:
                return "normal"

        except Exception as e5:
            
            return "normal"

def as_lnln(woodden, dbh, b1, b2, b3, j1, j2, *args):
    """ Generates biomass equations based on inputs of b1, b2, b3, and wood density for dbh, in cm. 

    Generates Jenkin's biomass equations based on inputs of j1 and j2 for dbh, also in cm. 

    **INPUTS**

    :woodden: wood density, 
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :args: the remainder of arguments passed to the function, which are not called in this case
    """
    try:
        biomass = round(b1*woodden*(b2*dbh**b3),7)
        volume = round(biomass/woodden,7)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,2))),7)
        return (biomass, volume, jbio, woodden)
    except ValueError as e1:
        
        return (0., 0., 0., woodden)


def as_d2ht(woodden, dbh, b1, b2, b3, j1, j2, h1, h2, h3):
    """ Generates biomass equations based on inputs of b1, b2, b3, h1, h2, and h3 and wood density for dbh, in cm.

    Generates Jenkin's biomass equations based on inputs of j1 and j2 for dbh, also in cm.

    **INPUTS**

    :woodden: wood density, 
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :h1: first height parameter
    :h2: second height parameter
    :h3: third height parameter
    """
    try:
        height = 1.37+ h1*(1-math.exp(h2*dbh))**h3
        biomass =  round(woodden*(height*b1*(0.01*dbh)**2),7)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,2))),7)
        volume = round(biomass/woodden,7)
        return (biomass, volume, jbio, woodden)
    except ValueError as e1:
        
        return (0., 0., 0., woodden)

def as_d2htcasc(woodden, dbh, b1, b2, b3, j1, j2, *args):
    """ Generates biomass equations based on inputs of b1, b2, b3 and wood density for dbh, in cm.

    Generates Jenkin's biomass equations based on inputs of j1 and j2 for dbh, also in cm. 

    **INPUTS**

    :woodden: wood density, 
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :args: the remainder of arguments passed to the function, which are not called in this case
    """
    try:
        biomass = round(b1*woodden*(b2*dbh**b3),7)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,2))),7)
        volume = round(biomass/woodden,7)
        return (biomass, volume, jbio, woodden)
    except ValueError as e1:
        
        return (0., 0., 0., woodden)


def as_biopak(woodden, dbh, b1, b2, b3, j1, j2, *args):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3` and wood density for dbh, in cm.

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm. 

    The BioPak method computes Biomass explicitly, rather than from volume. In most cases, the original output was in grams, but in this case, it is converted into Megagrams.

    **INPUTS**

    :woodden: wood density, 
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :args: the remainder of arguments passed to the function, which are not called in this case
    """
    try:
        biomass = round(1.*10**(-6)*math.exp(b1 + b2 * math.log(dbh)),7)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,2))),7)
        volume = round(biomass/woodden,7)
        return (biomass, volume, jbio, woodden)
    except ValueError as e1:
        
        return (0., 0., 0., woodden)

def as_chinq_biopak(woodden, dbh, b1, b2, b3, j1, j2, h1, h2, h3):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3`, `h1`, `h2`, `h3` and wood density for dbh, in cm.

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm. 

    Unlike many other BioPak methods, the chinquapin functions usually need height. 

    **INPUTS**

    :woodden: wood density, 
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :h1: first height parameter
    :h2: second height parameter
    :h3: third height parameter
    """
    try:
        height = 1.37 + h1*(1-math.exp(h2*dbh))**h3
        biomass =  round(woodden*height**b1*b2*(dbh)**b3,7)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,2))),7)
        volume = round(biomass/woodden,7)
        return (biomass, volume, jbio, woodden)
    except ValueError as e1:
        
        return (0., 0., 0., woodden)

def as_oak_biopak(woodden, dbh, b1, b2, b3, j1, j2, h1, h2, h3):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3`, `h1`, `h2`, `h3`  and wood density for dbh, in cm.

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm. 

    Species in the Quercus (oak) family almost uniquely use this form in BioPak for doing the dbh.

    **INPUTS**

    :woodden: wood density, 
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :h1: first height parameter
    :h2: second height parameter
    :h3: third height parameter
    """
    try:
        height = 1.37+h1*(1-math.exp(h2*dbh))**h3
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,2))),7)
        biomass = round(math.exp(b1 + b2*math.log(0.01*dbh) + b3*math.log(height)),7)
        volume = round(biomass/woodden,7)
        return (biomass, volume, jbio, woodden)
    except ValueError as e1:
        
        return (0., 0., 0., woodden)

def as_compbio(dbh, component_dict):
    """ Generates biomass equations based on inputs of dbh and the parameter "rows" for ACCI. 

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm.

    The function of `compbio` and how it is called programmatically is vastly different from all other functions. 
    This system was made originally not to have a storage of equations but to operate efficiently for any species, and because of this, component biomass needs to temporarily store its equations within the function caller and pass that whole reference structure to the Tree or Stand using it.

    **INPUTS**

    :woodden: wood density, 
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :h1: first height parameter
    :h2: second height parameter
    :h3: third height parameter
    """
    try:
        biomass = 0.
        volume = 0.

        for index, each_component in enumerate(list(component_dict.keys())):
            # compute biomass and volume - jenkin's is not needed for each component!
            bio_1, vol_1, jbio, woodden = component_dict[each_component](dbh)
            biomass += bio_1
            volume += vol_1
        return (biomass, volume, jbio, woodden)
    
    except ValueError as e1:
        
        return (0.,0.,0.,woodden)

def jenkins2014(dbh, j3, j4):
    """ Computes 2014 jenkins values for some species. Just here for testing.

    ** INPUTS **
    :dbh: cm diameter at breast height
    :j3: first Jenkins2014 parameter
    :j4: second Jenkins2014 parameter
    """

    jbio2 = round(0.001*math.exp(j3 + j4*math.log(round(dbh,2))),7)

    return jbio2

def which_fx(function_string):
    """ Find the correct function for doing the biomass, volume, Jenkins, and wood density in the lookup table.
    The keys for the lookup table are the same as the FORM field in TP00111.

    **INTERNAL VARIABLES**

    :as_lnln: function call for the lnln form 
    :as_compbio: function call for the component-biomass form
    :as_oak_biopak: function call for the oak biomass form
    :as_biopak: function call for the biopak form
    :as_d2htcasc: function call for the d2ht, Cascades-variety, form
    :as_d2ht: function call for the d2ht form

    **RETURNS**

    This function will return a lambda to another function that is then assembled in tps_Tree or tps_Stand for the species at hand, and called with the dbhs there.

    .. warning: requires pymssql
    """

    lookup = {'as_lnln': as_lnln,
    'as_compbio': as_compbio,
    'as_oak_biopak': as_oak_biopak,
    'as_chinq_biopak': as_chinq_biopak,
    'as_biopak': as_biopak,
    'as_d2htcasc': as_d2htcasc,
    'as_d2ht': as_d2ht}

    return lookup[function_string]
