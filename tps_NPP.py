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

    **INPUT VARIABLES**

    :Stand: a tps_Stand generated Stand which has the metadata needed for the output
    :Bios: a Biomasses or Biomasses_agg data structure
    :type: either `species` or `agg`
    """
    NPP_output = {}

    ordered_years = sorted(Bios.keys())

    

    for index, each_year in enumerate(ordered_years):

        if index == 0:
            continue

        else:
            year_begin = ordered_years[index-1]
            year_end = each_year
            duration = year_end - year_begin

            if type == "species":
                shared_species = [species for species in Bios[year_end].keys() if species in Bios[year_begin].keys()]
                new_species = [species for species in Bios[year_end].keys() if species not in Bios[year_begin].keys()]
                disappear_species = [species for species in Bios[year_begin].keys() if species not in Bios[year_end].keys()]

                # for species which are shared between the two remeasurements:
                if shared_species != []:
                    
                    for each_species in shared_species:
                        
                        delta_live_bio = Bios[year_end][each_species]['total_live_bio'] - Bios[year_begin][each_species]['total_live_bio']
                        delta_live_jenkins = Bios[year_end][each_species]['total_live_jenkins'] - Bios[year_begin][each_species]['total_live_jenkins']
                        delta_live_volume = Bios[year_end][each_species]['total_live_volume'] - Bios[year_begin][each_species]['total_live_volume']
                        delta_live_basal = Bios[year_end][each_species]['total_live_basal'] - Bios[year_begin][each_species]['total_live_basal']
                        delta_live_tph = Bios[year_end][each_species]['total_live_trees'] - Bios[year_begin][each_species]['total_live_trees']

                        # try:
                        #     print("started with " + str(Bios[year_begin][each_species]['total_live_trees']) + " and ended with " + str(Bios[year_end][each_species]['total_live_trees']) + "for a net of " + str(delta_live_tph))
                        # except Exception:
                        #     import pdb; pdb.set_trace()

                        # try:
                        #     print("started with " + str(Bios[year_begin][each_species]['total_live_bio']) + " and ended with " + str(Bios[year_end][each_species]['total_live_bio']) + "for a net of " + str(delta_live_bio))
                        # except Exception:
                        #     import pdb; pdb.set_trace()

                        # the npp is the change in live biomass (inclusive of ingrowth) plus the mortality from the previous period
                        npp = (delta_live_bio + Bios[year_begin][each_species]['total_dead_bio'])/duration

                        npp_j = (delta_live_jenkins + Bios[year_begin][each_species]['total_dead_jenkins'])/duration

                        if each_year not in NPP_output:
                            NPP_output[each_year] = {each_species: {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp, 'npp_j_yr': npp_j}}
                        elif each_year in NPP_output:
                            if each_species not in NPP_output[each_year]:
                                NPP_output[each_year][each_species] = {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp, 'npp_j_yr': npp_j}
                            elif each_species in NPP_output[each_year]:
                                print("this species has already been included, please debug")
                                import pdb; pdb.set_trace()
                else:
                    pass

                # for species which are introduced in the second remeasurement - there is no loss
                if new_species != []:

                    for each_species in new_species:

                        delta_live_bio = Bios[year_end][each_species]['total_live_bio'] 
                        delta_live_jenkins = Bios[year_end][each_species]['total_live_jenkins'] 
                        delta_live_volume = Bios[year_end][each_species]['total_live_volume'] 
                        delta_live_basal = Bios[year_end][each_species]['total_live_basal'] 
                        delta_live_tph = Bios[year_end][each_species]['total_live_trees'] 

                        # since the species is new in the second measurement, there will not be any dead of it from the first measurement
                        npp = delta_live_bio/duration
                        npp_j = delta_live_jenkins/duration

                        if each_year not in NPP_output:
                            NPP_output[each_year] = {each_species: {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp, 'npp_j_yr': npp_j}}
                        elif each_year in NPP_output:
                            if each_species not in NPP_output[each_year]:
                                NPP_output[each_year][each_species] = {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp, 'npp_j_yr': npp_j}
                            elif each_species in NPP_output[each_year]:
                                print("this species has already been included, please debug")
                                import pdb; pdb.set_trace()

                else:
                    pass

                # if a species is present in the first remeasurement but then goes away
                # the only time this might happen is like if it died
                if disappear_species != []:

                    for each_species in disappear_species:

                        delta_live_bio = 0.0
                        delta_live_jenkins = 0.0
                        delta_live_volume = 0.0
                        delta_live_basal = 0.0
                        delta_live_tph = 0.0

                        try:
                            npp_from_mort = Bios[year_begin]['each_species']['total_dead_bio']
                        except Exception: 
                            npp_from_mort = 0.0


                        try:
                            npp_from_mort_j = Bios[year_begin]['each_species']['total_dead_jenkins']
                        except Exception: 
                            npp_from_mort_j = 0.0

                        # the npp is the change in live biomass (inclusive of ingrowth) plus the mortality from the previous period
                        npp = (delta_live_bio + npp_from_mort)/duration

                        npp_j = (delta_live_jenkins + npp_from_mort_j)/duration

                        if each_year not in NPP_output:
                            NPP_output[each_year] = {each_species: {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp, 'npp_j_yr': npp_j}}
                        elif each_year in NPP_output:
                            if each_species not in NPP_output[each_year]:
                                NPP_output[each_year][each_species] = {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp, 'npp_j_yr': npp_j}
                            elif each_species in NPP_output[each_year]:
                                print("this species has already been included, please debug")
                                import pdb; pdb.set_trace()
                else:
                    pass


            elif type != "species":
                delta_live_bio = Bios[year_end]['total_live_bio'] - Bios[year_begin]['total_live_bio']
                delta_live_jenkins = Bios[year_end]['total_live_jenkins'] - Bios[year_begin]['total_live_jenkins']
                delta_live_volume = Bios[year_end]['total_live_volume'] - Bios[year_begin]['total_live_volume']
                delta_live_basal = Bios[year_end]['total_live_basal'] - Bios[year_begin]['total_live_basal']
                delta_live_tph = Bios[year_end]['total_live_trees'] - Bios[year_begin]['total_live_trees']

                # the npp is the change in live biomass (inclusive of ingrowth) plus the mortality from the previous period
                npp = (delta_live_bio + Bios[year_begin]['total_dead_bio'])/duration

                npp_j = (delta_live_jenkins + Bios[year_begin]['total_dead_jenkins']/duration)

                if each_year not in NPP_output:
                    NPP_output[each_year] = {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp, 'npp_j_yr' : npp_j}
                elif each_year in NPP_output:
                    print("the year is already in the NPP output for this stand, please debug")
                    import pdb; pdb.set_trace()

    import pdb; pdb.set_trace()
    return NPP_output


def write_NPP_species(Stand, NPP_output, type):
    """ Writes NPP by species to a normalized data structure
    """

    if type == "species":
        filename_out = Stand.standid + "_stand_normalized_NPP.csv"

        with open(filename_out, 'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)
            header = ['DBCODE','ENTITY','STUDYID', 'STANDID', 'YEAR_BEGIN', 'YEAR_END', 'SPECIES', 'DELTA_TPH','DELTA_BA_M2HA','DELTA_VOLM3_HA','DELTA_BIO_MGHA','DELTA_JBIO_MGHA', 'NPP_BIO', 'NPP_JENKINS']
            writer.writerow(header)
            for each_year in sorted(NPP_output.keys()):
                for each_species in NPP_output[each_year].keys():
                
                    new_row =['TP001','9', Stand.study_id.upper(), Stand.standid.upper(), NPP_output[each_year][each_species]['year_begin'], NPP_output[each_year][each_species]['year_end'], each_species.upper(), int(NPP_output[each_year][each_species]['delta_live_tph']), round(NPP_output[each_year][each_species]['delta_live_basal']*10000,3), round(NPP_output[each_year][each_species]['delta_live_volume']*10000,3), round(NPP_output[each_year][each_species]['delta_live_bio']*10000,3), round(NPP_output[each_year][each_species]['delta_live_jenkins']*10000, 3), round(NPP_output[each_year][each_species]['npp_yr']*10000, 3), round(NPP_output[each_year][each_species]['npp_j_yr']*10000, 3)]

                    writer.writerow(new_row)

    elif type == "agg":
        filename_out = Stand.standid + "_stand_aggregate_NPP.csv"

        with open(filename_out,'w') as writefile:
            writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)

            header = ['DBCODE','ENTITY','STUDYID', 'STANDID', 'YEAR_BEGIN', 'YEAR_END', 'DELTA_TPH','DELTA_BA_M2HA','DELTA_VOLM3_HA','DELTA_BIO_MGHA','DELTA_JBIO_MGHA', 'NPP_BIO', 'NPP_JENKINS']
            writer.writerow(header)

            for each_year in sorted(NPP_output.keys()):
                
                new_row =['TP001','9', Stand.study_id.upper(), Stand.standid.upper(), NPP_output[each_year]['year_begin'], NPP_output[each_year]['year_end'], int(NPP_output[each_year]['delta_live_tph']), round(NPP_output[each_year]['delta_live_basal'],3), round(NPP_output[each_year]['delta_live_volume'],3), round(NPP_output[each_year]['delta_live_bio'],3), round(NPP_output[each_year]['delta_live_jenkins'], 3), round(NPP_output[each_year]['npp_yr'], 3), round(NPP_output[each_year]['npp_j_yr'], 3)]

                writer.writerow(new_row)


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
    
    test_stands = ["AV06"]
    for each_stand in test_stands:
        
        A = tps_Stand.Stand(cur, pcur, XFACTOR, queries, each_stand)
        BM, BTR = A.compute_normal_biomasses(XFACTOR)
        
        #import pdb; pdb.set_trace()
        if BM == {}:

            Biomasses, BadTreeSpec = A.compute_special_biomasses(XFACTOR)
            NPP1 = compute_NPP(A, Biomasses, "species")
            write_NPP_species(A, NPP1, "species")
            
            Biomasses_aggregate = A.aggregate_biomasses(Biomasses)
            NPPA = compute_NPP(A, Biomasses_aggregate, "agg")
            write_NPP_species(A, NPPA, "agg")
        
        else:
            NPP1 = compute_NPP(A, BM, "species")
            write_NPP_species(A, NPP1, "species")
            BMA = A.aggregate_biomasses(BM)
            NPPA = compute_NPP(A, BMA, "agg")
            write_NPP_species(A, NPPA, "agg")

        
        print("tonight")
        print("party")
        print("1999")