#!/usr/bin/python3
# -*- coding: utf-8 -*-

import poptree_basis
import math
import biomass_basis
import bisect
import csv
import tps_Stand


def plot_wrap_compute_NPP(Bios_plot, type):
    """ To compute NPP by Plot, this function wraps around the Stand method, so that the years for the plot are specific.

    **INPUTS**
    
    :Bios_plot: biomasses by plot need this wrapper
    :type: species or aggregate, used internally

    **RETURNS**

    :NPP_output_plot: NPP at the plot scale
    """
    new_plots = {}
    NPP_output_plot = {}

    if type == 'species':

        for each_year in Bios_plot.keys():

            for each_species in Bios_plot[each_year].keys():

                available_plots = list(Bios_plot[each_year][each_species].keys())

                for each_plot in available_plots:
                    
                    if each_plot not in new_plots:
                        new_plots[each_plot] = {each_year: {each_species: Bios_plot[each_year][each_species][each_plot]}}
                    elif each_plot in new_plots:
                        if each_year not in new_plots[each_plot]:
                            new_plots[each_plot][each_year] = {each_species: Bios_plot[each_year][each_species][each_plot]}
                        elif each_year in new_plots[each_plot]:
                            if each_species not in new_plots[each_plot][each_year]:
                                new_plots[each_plot][each_year][each_species] = Bios_plot[each_year][each_species][each_plot]
                            elif each_species in new_plots[each_plot][each_year]:
                                print("an error occurred re-writing the plots for NPP analysis, check plot wrap compute")
        for each_plot in new_plots.keys():

            new_bios = new_plots[each_plot]
            npp_plot = compute_NPP(each_plot, new_bios, 'species', 'plot')

            if each_plot not in NPP_output_plot:
                NPP_output_plot.update({each_plot:npp_plot})
            else:
                print("plot already listed for species method, try again?")


    elif type == 'agg':

        for each_plot in Bios_plot.keys():
            new_bios = Bios_plot[each_plot]
            npp_plot_agg = compute_NPP(each_plot, new_bios, 'agg', 'plot')

            if each_plot not in NPP_output_plot:
                NPP_output_plot.update({each_plot: npp_plot_agg})
            else: 
                print("the aggregate biomass by plot is not working")
        
    return NPP_output_plot

def compute_NPP(Stand, Bios, type, breakdown_type):
    """ Computes NPP from either a Biomasses data structure or a Biomasses_agg data structure. The Biomasses data structure is species-specific, while the Biomasses_agg data structure is a sum of all the species.

    **INPUTS**

    :Stand: a tps_Stand generated Stand which has the metadata needed for the output
    :Bios: a Biomasses or Biomasses_agg data structure
    :type: either `species` or `agg`
    :breakdown_type: either `stand` or `plot`

    **RETURNS**

    :NPP_output: NPP at the stand or plot scale
    """

    if breakdown_type != 'plot':

        # make sure stand id is in lower case, even if it's for a real stand
        Stand.standid = Stand.standid.lower()

    elif breakdown_type == 'plot':
        pass

    NPP_output = {}

    ordered_years = sorted(Bios.keys())

    for index, each_year in enumerate(ordered_years):

        # skip year 1, since it's year begin, and your index - 1 will hold it
        if index == 0:
            continue

        else:
            year_begin = ordered_years[index-1]
            year_end = each_year
            
            duration = year_end - year_begin

            if type == "species":
                
                # get the species that are shared between the first year and the second, those that appear in the second, and those that appear in the first

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

                    
                        # the npp is the change in live biomass (inclusive of ingrowth) plus the mortality from the previous period
                        npp = (delta_live_bio + Bios[year_begin][each_species]['total_dead_bio'])/duration

                        npp_j = (delta_live_jenkins + Bios[year_begin][each_species]['total_dead_jenkins'])/duration

                        if each_year not in NPP_output:
                            NPP_output[each_year] = {each_species: {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp, 'npp_j_yr': npp_j}}
                        
                        elif each_year in NPP_output:
                            if each_species not in NPP_output[each_year]:
                                NPP_output[each_year][each_species] = {'year_begin': year_begin, 'year_end': year_end, 'delta_live_bio': delta_live_bio, 'delta_live_jenkins' : delta_live_jenkins, 'delta_live_volume' : delta_live_volume, 'delta_live_basal' : delta_live_basal, 'delta_live_tph' : delta_live_tph, 'npp_yr' : npp, 'npp_j_yr': npp_j}
                            
                            elif each_species in NPP_output[each_year]:
                                print("this species has already been included for this year, please debug")
                                import pdb; pdb.set_trace()

                else:
                    pass

                # for species which are introduced in the second remeasurement - there is no loss, whatever bio is there in this new period is the bio delta because it came in over the last measurement
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
                                print("this species has already been included for this year, please debug")
                                import pdb; pdb.set_trace()

                else:
                    pass

                # if a species is present in the first remeasurement but then goes away
                # the only time this might happen is like if it died
                if disappear_species != []:

                    for each_species in disappear_species:

                        # if the species disappears entirely, these numbers should be pretty negative
                        delta_live_bio = 0.0 - Bios[year_begin][each_species]['total_live_bio']
                        delta_live_jenkins = 0.0 - Bios[year_begin][each_species]['total_live_jenkins']
                        delta_live_volume = 0.0 - Bios[year_begin][each_species]['total_live_volume']
                        delta_live_basal = 0.0 - Bios[year_begin][each_species]['total_live_basal']
                        delta_live_tph = 0.0 - Bios[year_begin][each_species]['total_live_trees']

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

            # if computing the aggregate
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


    return NPP_output


def write_NPP_composite_stand(Stand, BM, BMA, *args):
    """ Computes the Biomass for each species and for the stand as a whole together.

    **INPUTS**

    :BM: Biomasses, from ``tps_Stand``
    :BMA: Biomass Aggregate, from ``tps_Stand``
    :args: arguements of the filename and the mode (``w`` or ``a``) for write or append. Write the first plot or stand, append the rest!

    **RETURNS**

    A csv file containing the NPPS at the stand scale
    """
    npp_out = compute_NPP(Stand, BM, 'species', 'stand')
    npp_out_agg = compute_NPP(Stand, BMA, 'agg', 'stand')

    if args and args != []:
        filename_out = args[0]
        mode = args[1]
    else:
        filename_out = Stand.standid.lower() + "_stand_composite_NPP.csv"
        mode = 'w'

    

    with open(filename_out, mode) as writefile:
        writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)
        header = ['DBCODE','ENTITY', 'STANDID', 'YEAR_BEGIN', 'YEAR_END', 'SPECIES', 'DELTA_TPH_NHA','DELTA_BA_M2HA','DELTA_VOL_M3HA','DELTA_BIO_MGHA','DELTA_JENKBIO_MGHA', 'MEAN_ANNUAL_NPP_BIO', 'MEAN_ANNUAL_NPP_JENKBIO', 'NO_PLOTS']
        writer.writerow(header)

        for each_year in sorted(npp_out.keys()):

            num_plots = Stand.num_plots[each_year]

            try:
                # get the aggregate before getting the species
                new_row_1 = ['TP001','07', Stand.standid.upper(), npp_out_agg[each_year]['year_begin'], npp_out_agg[each_year]['year_end'], "ALL", int(npp_out_agg[each_year]['delta_live_tph']), round(npp_out_agg[each_year]['delta_live_basal']*10000,4), round(npp_out_agg[each_year]['delta_live_volume']*10000,4), round(npp_out_agg[each_year]['delta_live_bio']*10000,4), round(npp_out_agg[each_year]['delta_live_jenkins']*10000, 4), round(npp_out_agg[each_year]['npp_yr']*10000, 4), round(npp_out_agg[each_year]['npp_j_yr']*10000, 4), num_plots]

                writer.writerow(new_row_1)
            
            except Exception:
                import pdb; pdb.set_trace()

            for each_species in npp_out[each_year].keys():

                new_row =['TP001','07', Stand.standid.upper(), npp_out[each_year][each_species]['year_begin'], npp_out[each_year][each_species]['year_end'], each_species.upper(), int(npp_out[each_year][each_species]['delta_live_tph']), round(npp_out[each_year][each_species]['delta_live_basal']*10000,4), round(npp_out[each_year][each_species]['delta_live_volume']*10000,4), round(npp_out[each_year][each_species]['delta_live_bio']*10000,4), round(npp_out[each_year][each_species]['delta_live_jenkins']*10000, 4), round(npp_out[each_year][each_species]['npp_yr']*10000, 4), round(npp_out[each_year][each_species]['npp_j_yr']*10000, 4), num_plots]

                writer.writerow(new_row)
                

def write_NPP_composite_plot(Plot, BM_plot, BMA_plot, *args):
    """ Computes the Biomass for each species and for the stand as a whole together.

    **INPUTS**

    :BM_plot: Biomasses, from ``tps_Stand``
    :BMA_plot: Biomass Aggregate, from ``tps_Stand``
    :args: arguements of the filename and the mode (``w`` or ``a``) for write or append. Write the first plot or stand, append the rest!

    **RETURNS**

    A csv file containing the NPPS at the plot scale
    """
    npp_out = plot_wrap_compute_NPP(BM_plot, 'species')
    npp_out_agg = plot_wrap_compute_NPP(BMA_plot, 'agg')

    if args and args != []:
        filename_out = args[0]
        mode = args[1]
    else:
        filename_out = Plot.Stand.standid.lower() + "_plot_composite_NPP.csv"
        mode = 'w'

    

    with open(filename_out, mode) as writefile:
        writer = csv.writer(writefile, delimiter = ",", quoting=csv.QUOTE_NONNUMERIC)
        header = ['DBCODE','ENTITY', 'PLOTID', 'YEAR_BEGIN', 'YEAR_END', 'SPECIES', 'DELTA_TPH_NHA','DELTA_BA_M2HA','DELTA_VOL_M3HA','DELTA_BIO_MGHA','DELTA_JENKBIO_MGHA', 'MEAN_ANNUAL_NPP_BIO', 'MEAN_ANNUAL_NPP_JENKBIO']
        
        writer.writerow(header)

        for each_plot in sorted(npp_out_agg.keys()):

            for each_year in npp_out_agg[each_plot]:

                try:
                    # get the aggregate before getting the species
                    new_row_1 = ['TP001','09', each_plot.upper(), npp_out_agg[each_plot][each_year]['year_begin'], npp_out_agg[each_plot][each_year]['year_end'], "ALL", int(npp_out_agg[each_plot][each_year]['delta_live_tph']), round(npp_out_agg[each_plot][each_year]['delta_live_basal']*10000,4), round(npp_out_agg[each_plot][each_year]['delta_live_volume']*10000,4), round(npp_out_agg[each_plot][each_year]['delta_live_bio']*10000,4), round(npp_out_agg[each_plot][each_year]['delta_live_jenkins']*10000, 4), round(npp_out_agg[each_plot][each_year]['npp_yr']*10000, 4), round(npp_out_agg[each_plot][each_year]['npp_j_yr']*10000, 4)]

                    writer.writerow(new_row_1)
            
                except Exception:
                    import pdb; pdb.set_trace()

                # the years should be the same but go over the species one anger another here
                for each_species in npp_out[each_plot][each_year].keys():

                    new_row =['TP001','07', each_plot.upper(), npp_out[each_plot][each_year][each_species]['year_begin'], npp_out[each_plot][each_year][each_species]['year_end'], each_species.upper(), int(npp_out[each_plot][each_year][each_species]['delta_live_tph']), round(npp_out[each_plot][each_year][each_species]['delta_live_basal']*10000,4), round(npp_out[each_plot][each_year][each_species]['delta_live_volume']*10000,4), round(npp_out[each_plot][each_year][each_species]['delta_live_bio']*10000,4), round(npp_out[each_plot][each_year][each_species]['delta_live_jenkins']*10000, 4), round(npp_out[each_plot][each_year][each_species]['npp_yr']*10000, 4), round(npp_out[each_plot][each_year][each_species]['npp_j_yr']*10000, 4)]

                    writer.writerow(new_row)



if __name__ == "__main__":

    DATABASE_CONNECTION = poptree_basis.YamlConn()
    conn, cur = DATABASE_CONNECTION.sql_connect()
    queries = DATABASE_CONNECTION.queries

    # creates lookups for expansion factors
    XFACTOR = poptree_basis.Capture(cur, queries)

    #A = Stand(cur, pcur, XFACTOR, queries, 'CFMF')
    #import pdb; pdb.set_trace()
    #test_stands = ['CFMF','AV06','WI01','NCNA', 'AG05', 'AB08', 'AX15', 'PP17', 'TO11', 'AV14', 'RS31', 'RS28', 'RS01', 'RS02', 'RS30', 'TB13', 'AR07', 'AM16', 'RS29', 'RS32', 'AE10', 'AV06', 'TO04']
    
    test_stands = ['RS01', 'RS02', 'RS30', 'TB13', 'AR07', 'AM16', 'RS29', 'RS32', 'AE10', 'AV06', 'TO04']
    
    for each_stand in test_stands:
        
        A = tps_Stand.Stand(cur, XFACTOR, queries, each_stand.lower())

        K = tps_Stand.Plot(A, XFACTOR, [])
        BM, BTR, ROB= A.compute_biomasses(XFACTOR)

        BM_plot = K.compute_biomasses_plot(XFACTOR)
    
        #NPP1 = compute_NPP(A, BM, "species", "stand")
        BMA = A.aggregate_biomasses(BM)

        #A.write_stand_composite(BM, BMA, XFACTOR)
        

        BMA_plot = K.aggregate_biomasses_plot(BM_plot)
        #NPP2 = compute_NPP(A, BMA, "agg", "stand")

        #K.write_plot_composite(BM_plot, BMA_plot, XFACTOR)

        #NPP3 = plot_wrap_compute_NPP(BM_plot, "species")
        #NPP4 = plot_wrap_compute_NPP(BMA_plot, "agg")

        write_NPP_composite_stand(A, BM, BMA)
        write_NPP_composite_plot(K, BM_plot, BMA_plot)
           