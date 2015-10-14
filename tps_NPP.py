#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import biomass_basis
import bisect
import csv
import tps_Stand

    

def compute_NPP(Stand, Bios, type):
    """ Computes NPP from either a Biomasses data structure or a Biomasses_agg data structure. The Biomasses data structure is species-specific, while the Biomasses_agg data structure is a sum of all the species.
    """
    NPP_output = {}

    ordered_years = sorted(Bios.keys())

    for index, each_year in enumerate(ordered_years):

        if index == 0:
            continue

        else:
            year_begin = ordered_years[index-1]
            year_end = each_year

            if type == "species":
                shared_species = [species for species in Bios[year_end].keys() if species in Bios[year_begin].keys()]
                new_species = [species for species in Bios[year_end].keys() if species not in Bios[year_begin].keys()]
                disappear_species = [species for species in Bios[year_begin].keys() if species not in Bios[year_end].keys()]

                duration = year_end - year_begin

                # for species which are shared between the two remeasurements:
                if shared_species != []:
                    
                    for each_species in shared_species:
                        
                        delta_live_bio = Bios[year_end][each_species]['total_live_bio'] - Bios[year_begin][each_species]['total_live_bio']
                        delta_live_jenkins = Bios[year_end][each_species]['total_live_jenkins'] - Bios[year_begin][each_species]['total_live_jenkins']
                        delta_live_volume = Bios[year_end][each_species]['total_live_volume'] - Bios[year_begin][each_species]['total_live_volume']
                        delta_live_basal = Bios[year_end][each_species]['total_live_basal'] - Bios[year_begin][each_species]['total_live_basal']
                        delta_live_tph = Bios[year_end][each_species]['total_live_trees'] - Bios[year_begin][each_species]['total_live_trees']

                        # the npp is the change in live biomass (inclusive of ingrowth) plus the mortality from the previous period
                        npp = (delta_live_bio + Bios[year_begin]['each_species']['total_dead_bio'])/duration

                        if each_year not in NPP_output:
                            NPP_output[each_year] = {each_species: {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp}}
                        elif each_year in NPP_output:
                            if each_species not in NPP_output[each_year]:
                                NPP_output[each_year][each_species] = {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp}
                            elif each_species in NPP_output[each_year]:
                                print("this species has already been included, please debug")
                                import pdb; pdb.set_trace()
                else:
                    pass

                # for species which are introduced in the second remeasurement
                if new_species != []:

                    for each_species in new_species:

                        delta_live_bio = Bios[year_end][each_species]['total_live_bio'] 
                        delta_live_jenkins = Bios[year_end][each_species]['total_live_jenkins'] 
                        delta_live_volume = Bios[year_end][each_species]['total_live_volume'] 
                        delta_live_basal = Bios[year_end][each_species]['total_live_basal'] 
                        delta_live_tph = Bios[year_end][each_species]['total_live_trees'] 

                        # since the species is new in the second measurement, there will not be any dead of it from the first measurement
                        npp = delta_live_bio/duration

                        if each_year not in NPP_output:
                            NPP_output[each_year] = {each_species: {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp}}
                        elif each_year in NPP_output:
                            if each_species not in NPP_output[each_year]:
                                NPP_output[each_year][each_species] = {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp}
                            elif each_species in NPP_output[each_year]:
                                print("this species has already been included, please debug")
                                import pdb; pdb.set_trace()

                else:
                    pass

                # if a species is present in the first remeasurement but then goes away
                if disappear_species != []:

                    for each_species in disappear_species:

                        delta


            elif type != "species":
                pass



def write_NPP_species(Stand, NPP, type):
    """ Writes NPP by species to a normalized data structure
    """

    if type == "species":
        filename_out = Stand.standid + "_stand_normalized_NPP.csv"
        header = ['DBCODE','ENTITY','STUDYID', 'STANDID', 'YEAR_BEGIN', 'YEAR_END', 'SPECIES', 'STATUS', 'DELTA_TPH','DELTA_BA_M2HA','DELTA_VOLM3_HA','DELTA_BIO_MGHA','DELTA_JBIO_MGHA', 'NPP_BIO', 'NPP_JBIO']
    elif type == "agg":
        filename_out = Stand.standid + "_stand_aggregate_NPP.csv"
        header = ['DBCODE','ENTITY','STUDYID', 'STANDID', 'YEAR_BEGIN', 'YEAR_END', 'STATUS', 'DELTA_TPH','DELTA_BA_M2HA','DELTA_VOLM3_HA','DELTA_BIO_MGHA','DELTA_JBIO_MGHA', 'NPP_BIO', 'NPP_JBIO']

        with open(filename_out,'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)


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
        
        A = tps_Stand.Stand(cur, pcur, XFACTOR, queries, each_stand)

        BM, BTR = A.compute_normal_biomasses(XFACTOR)
        
        if BM == {}:
            Biomasses, BadTreeSpec = A.compute_special_biomasses(XFACTOR)

            Biomasses_aggregate = A.aggregate_biomasses(Biomasses)

        else:

            BMA = A.aggregate_biomasses(BM)

        import pdb; pdb.set_trace()
        print("tonight")
        print("party")
        print("1999")