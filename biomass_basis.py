#!/usr/bin/python3
# -*- coding: utf-8 -*-

import math

def maxref(dbh, species):
    """ Check if given dbh (in cm) and given species is bigger than the maximum for that combination. The maximum was found from determining the top 1 percent of dbh's in cm for each species from all the historical data. This function operates behind the scenes on inputs from TP00102 (dbh's) and TP00101(species). It populates the .eqns attribute of the Tree or Stand classes so that the right equation or set of equations will be called.

    **INPUTS**

    :dbh: the tree's dbh, in cm
    :species: the tree's species, a four character code. If the database provides a longer code, it will be converted to a lowercase four letter code.

    **RETURNS**

    Either `"big"` or `"normal"` to trigger appropriate equation selection from the Stand or Tree's `.eqns` attribute.

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

        except Exception:

            return "normal"

def as_lnln(woodden, dbh, b1, b2, b3, j1, j2, *args):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3`, and wood density for a given dbh (in cm).

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm.

    This equation is taken from TV00908.

    The math form of this equation is: biomass = b1 * wood density * ( b2 * dbh ** b3 )
    The math form for Jenkins is jenkins' biomass = 0.001 * exp( j1 + j2 * ln(dbh))

    **INPUTS**

    :woodden: wood density,
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :args: the remainder of arguments passed to the function, which are not called in this case

    **RETURNS**

    A tuple like this : `(biomass, volume, jenkins biomass, wood density)` or zeros, if any of these cannot be computed.

    """
    try:
        biomass = round(b1*woodden*(b2*dbh**b3),11)
        volume = round(biomass/woodden,11)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,4))),11)
        return (biomass, volume, jbio, woodden)
    except ValueError:

        return (0., 0., 0., woodden)


def as_d2ht(woodden, dbh, b1, b2, b3, j1, j2, h1, h2, h3):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3`, `h1`, `h2`, and `h3` and wood density for a given dbh (in cm).

    Internally, a conversion to meters on dbh is performed to match the equation documentation specified for
    `TV00908 <http://andrewsforest.oregonstate.edu/lter/data/domains.cfm?domain=enum&dbcode=TV009&attid=1321&topnav=8>`_.

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm.

    The math form of this equation is: biomass = wood density * height * b1 * (0.01 * dbh)**2
    The math form for Jenkins is jenkins' biomass = 0.001 * exp( j1 + j2 * ln(dbh))


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

    **RETURNS**

    A tuple like this : `(biomass, volume, jenkins biomass, wood density)` or zeros, if any of these cannot be computed

    """
    try:
        height = 1.37+ h1*(1-math.exp(h2*dbh))**h3
        biomass =  round(woodden*(height*b1*(0.01*dbh)**2),11)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,4))),11)
        volume = round(biomass/woodden,11)
        return (biomass, volume, jbio, woodden)
    except ValueError:

        return (0., 0., 0., woodden)

def as_biopak(woodden, dbh, b1, b2, b3, j1, j2, *args):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3` and wood density for dbh, in cm.

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm.

    The BioPak method computes total aboveground biomass explicitly, rather than from volume. In most cases, the original output from the equations as specified in BioPak was in grams, and here it is converted into Megagrams.

    The math form for this equation is: biomass = 1.0 * 10**(-6) * exp( b1 + b2 * ln(dbh))
    The math form for Jenkins is jenkins' biomass = 0.001 * exp( j1 + j2 * ln(dbh))

    **INPUTS**

    :woodden: wood density,
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :args: the remainder of arguments passed to the function, which are not called in this case

    **RETURNS**

    A tuple like this : `(biomass, volume, jenkins biomass, wood density)` or zeros, if any of these cannot be computed.

    """
    try:
        biomass = round(1.*10**(-6)*math.exp(b1 + b2 * math.log(dbh)),11)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,4))),11)
        volume = round(biomass/woodden,11)
        return (biomass, volume, jbio, woodden)
    except ValueError:

        return (0., 0., 0., woodden)

def segi_biopak(woodden, dbh, b1, b2, b3, j1, j2, *args):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3` and wood density for dbh, in cm.

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm.

    The BioPak method computes total aboveground biomass explicitly, rather than from volume. In most cases, the original output from the equations as specified in BioPak was in grams, and here it is converted into Megagrams.

    The math form for this equation is: biomass = 1.0 * 10**(-6) * exp( b1 + b2 * ln(dbh))
    The math form for Jenkins is jenkins' biomass = 0.001 * exp( j1 + j2 * ln(dbh))

    **INPUTS**

    :woodden: wood density,
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :args: the remainder of arguments passed to the function, which are not called in this case

    **RETURNS**

    A tuple like this : `(biomass, volume, jenkins biomass, wood density)` or zeros, if any of these cannot be computed.

    """
    try:
        biomass = round(math.exp(b1 + b2 * math.log(dbh)),11)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,4))),11)
        volume = round(biomass/woodden,11)
        return (1000000*biomass, volume, jbio, woodden)
    except ValueError:

        return (0., 0., 0., woodden)

def as_chinq_biopak(woodden, dbh, b1, b2, b3, j1, j2, h1, h2, h3):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3`, `h1`, `h2`, `h3` and wood density for dbh, in cm.

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm.

    Unlike many other BioPak methods, the chinquapin functions usually need height. Height is calculated here. The height equations are also from BioPak.

    The math form for this equation is: biomass = wood density * height**b1 * b2 * dbh**b3
    The math form for Jenkins is jenkins' biomass = 0.001 * exp( j1 + j2 * ln(dbh))

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

    **RETURNS**

    A tuple like this : `(biomass, volume, jenkins biomass, wood density)` or zeros, if any of these cannot be computed.

    """
    try:
        height = 1.37 + h1*(1-math.exp(h2*dbh))**h3
        biomass =  round(woodden*height**b1*b2*(dbh)**b3,11)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,4))),11)
        volume = round(biomass/woodden,11)
        return (biomass, volume, jbio, woodden)
    except ValueError:

        return (0., 0., 0., woodden)

def mod_biopak(woodden, dbh, b1, b2, b3, j1, j2, h1, h2, h3):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3`, `h1`, `h2`, `h3` and wood density for dbh, in cm.

    THIS IS A VERY SPECIAL EQUATION JUST FOR ACMA!!!  It is based on what is in 654 in BioPak, entity 2. It is what is used by both Lutz and Gody.

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm.

    The math form for this equation is: biomass = wood density * b1 * dbh**b2 * height**b3
    The math form for Jenkins is jenkins' biomass = 0.001 * exp( j1 + j2 * ln(dbh))

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

    **RETURNS**

    A tuple like this : `(biomass, volume, jenkins biomass, wood density)` or zeros, if any of these cannot be computed.

    """
    try:
        height = 1.37 + h1*(1-math.exp(h2*dbh))**h3
        biomass = round(woodden*(b1*dbh**b2*height**b3),11)
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,4))),11)
        volume = round(biomass/woodden,11)
        return (biomass, volume, jbio, woodden)
    except ValueError:

        return (0., 0., 0., woodden)

def alder_biopak(woodden, dbh, b1, b2, b3, j1, j2, *args):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3` and wood density for dbh, in cm.

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm.

    `alder_biopak` computes VSW instead of biomass, but is otherwise the same.

    The math form for this equation is: biomass = 1.0 * 10**(-6) * exp( b1 + b2 * ln(dbh))*woodden
    The math form for Jenkins is jenkins' biomass = 0.001 * exp( j1 + j2 * ln(dbh))

    **INPUTS**

    :woodden: wood density,
    :dbh: cm diameter at breast height
    :b1: first biomass parameter
    :b2: second biomass parameter
    :b3: third biomass parameter
    :j1: first Jenkins parameter
    :j2: second Jenkins parameter
    :args: the remainder of arguments passed to the function, which are not called in this case

    **RETURNS**

    A tuple like this : `(biomass, volume, jenkins biomass, wood density)` or zeros, if any of these cannot be computed.

    """
    try:
        biomass = round(1.*10**(-6)*math.exp(b1 + b2 * math.log(dbh)),11)*woodden
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,4))),11)
        volume = round(biomass/woodden,11)
        return (biomass, volume, jbio, woodden)
    except ValueError:

        return (0., 0., 0., woodden)

def as_oak_biopak(woodden, dbh, b1, b2, b3, j1, j2, h1, h2, h3):
    """ Generates biomass equations based on inputs of `b1`, `b2`, `b3`, `h1`, `h2`, `h3`  and wood density for dbh, in cm.

    Generates Jenkin's biomass equations based on inputs of `j1` and `j2` for dbh, also in cm.

    Species in the Quercus (oak) family almost uniquely use this form in BioPak for doing the biomass computation.

    The math form for Jenkins is jenkins' biomass = 0.001 * exp( j1 + j2 * ln(dbh))

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

    **RETURNS**

    A tuple like this : `(biomass, volume, jenkins biomass, wood density)` or zeros, if any of these cannot be computed.

    """
    try:
        height = 1.37+h1*(1-math.exp(h2*dbh))**h3
        jbio = round(0.001*math.exp(j1 + j2*math.log(round(dbh,4))),11)
        biomass = round(math.exp(b1 + b2*math.log(0.01*dbh) + b3*math.log(height)),11)
        volume = round(biomass/woodden,11)
        return (biomass, volume, jbio, woodden)
    except ValueError:

        return (0., 0., 0., woodden)


def jenkins2014(dbh, j3, j4):
    """ Computes 2014 jenkins values for some species. If you add in new parameters, you might want this.

    The math form for Jenkins is jenkins' biomass = 0.001 * exp( j1 + j2 * ln(dbh))

    **INPUTS**

    :dbh: cm diameter at breast height
    :j3: first Jenkins2014 parameter
    :j4: second Jenkins2014 parameter

    **RETURNS**

    A tuple like this : `(biomass, volume, jenkins biomass, wood density)` or zeros, if any of these cannot be computed.

    """

    jbio2 = round(0.001*math.exp(j3 + j4*math.log(round(dbh,4))),11)

    return jbio2

def which_fx(function_string):
    """ Find the correct function for doing the Biomass ( Mg ), Jenkins Biomass ( Mg ), Volume ( m\ :sup:`3` ) , and Basal Area ( m\ :sup:`2` ) and wood density in the lookup table.
    The keys for the lookup table are the same as the FORM field in TP00110


    **INPUTS**

    :function_string: the string that is in the `form` attribute in TP00110, used to generate the above functions for computation.

    **RETURNS**

    This function will return a lambda to another function that is then assembled in tps_Tree or tps_Stand for the species at hand, and called with the dbhs there.
    """

    lookup = {'lnln': as_lnln,
    'oak_biopak': as_oak_biopak,
    'chinq_biopak': as_chinq_biopak,
    'biopak': as_biopak,
    'd2ht': as_d2ht,
    'mod_biopak': mod_biopak,
    'segi_biopak': segi_biopak,
    'alder_biopak': alder_biopak}

    return lookup[function_string]
