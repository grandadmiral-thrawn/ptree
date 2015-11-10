********************************************
TPS: Tree, Plot, Stand - Biomass Aggregation
********************************************

TPS is a set of Python 3 modules for the aggregation of trees, plots, and stands from the USFS reference stands data maintained by the Corvallis Forest Science Lab.  


.. contents::
    :local:
    :depth: 1
    :backlinks: none


=============
Main Modules
=============

* tps_Tree <- individual trees, to be computed ID by ID, and perform checks on individuals, ID by ID
* tps_Stand <- stands, plots on stands, trees on stands, for larger-scale computations
* tps_NPP <- net primary productivity for plots and stands
* tps_cli <- command line interface
* tps_Sample <- tests - queries to 'ncna' that should always work
* SQL queries and configs in yaml files for interoperability!
* lots of docs!

============
Installation
============

Set up Python 3 on your computer, and then run the darn thing!
Best to start with tps_Sample, which will run a series of test trees and stands on a known dataset (that it will access from the server to test your connection) and output the results. To run it do:

.. code-block:: bash

    $ python3 tps_Sample.py

Assuming this goes well, please read the docs! The docs are in index.html, currently in the `_build/` folder. You'll be running the remainder of your analyses out of the command line interface for now, but there are a lot of options.

-------------------
Development version
-------------------

The **latest development version** can be installed directly from GitHub. Use this repository. Note that when Fox leaves, maintenance will be sporadic at best.

-------------------------------
Documentation in the Literature
-------------------------------

For computation of height (where needed), the `Garman et al.(1995)<http://andrewsforest.oregonstate.edu/pubs/pdf/pub1445.pdf>_` methods were used, and height was computed as `Ht_m = 1.37 + (b0*(1-exp(b1*DBH_cm))**b2)`


====================
Command Line Options
====================

The command line tool has a variety of options for your output pleasure. These have all been tested as of 11-06-2015 and work. 

--------------------
Details About 1 Tree
--------------------

This command will get you details about 1 tree and either print them to the screen or to a file. Pretend the tree of your desire is `ncna0001000001`

.. code-block:: bash

    $ python3 tps_cli.py dtx ncna000100001

The computer will ask if you would like to have a file, and if so to type `Y`. If you type `Y`, the output will go to a file named (in this case for `ncna0001000001`) `ncna000100001_tags_and_checks.csv`. If you don't type `Y` (you can even just press enter), you will see on your screen something like:

.. code-block:: bash


    Tree: ncna000100001
    Year: 1979
    Stand: NCNA
    Plot: ncna0001
    Study: HSGY
    DBH: 52.5
    Status: 1
    DBH Code: G
    Tag: 46
    Notes: 
    -------------------
    Tree: ncna000100001
    Year: 1984
    Stand: NCNA
    Plot: ncna0001
    Study: HSGY
    DBH: 53.3
    Status: 1
    DBH Code: G
    Tag: 46
    Notes: 
    -------------------
    Tree: ncna000100001
    Year: 1989
    Stand: NCNA
    Plot: ncna0001
    Study: HSGY
    DBH: 54.0
    Status: 1
    DBH Code: G
    Tag: 46
    Notes: 
    -------------------

But this will be for all the years of the tree, not just these first few.

-----------------------------------------
Biomass at the Stand Scale for All Stands
-----------------------------------------

To compute the biomass at the stand scale for all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py bio stand composite --all

Your output will be in a file named `all_stands_biomass_composite_output.csv`. It will be organized like `DBCODE`,`ENTITY`,`STANDID`,`SPECIES`,`YEAR`,`PORTION`,`TPH_NHA`,`BA_M2HA`,`VOL_M3HA`,`BIO_MGHA`,`JENKBIO_MGHA`.

----------------------------------------------------------
Biomass at the Stand Scale for a set of one or more stands
----------------------------------------------------------

To compute the biomass at the stand scale for one or more stands, just add those stands to the end of the line `tps_cli.py bio stand composite`. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. Here's how you could ask for `ncna`, `rs01`, `srnf`, and `wr01`.

.. code-block:: bash

    $ python3 tps_cli.py bio stand composite ncna rs01 srnf ws01

If you have more than one stand, your output will in a file named `selected_stands_biomass_composite_output.csv`. It will be organized like `DBCODE`,`ENTITY`,`STANDID`,`SPECIES`,`YEAR`,`PORTION`,`TPH_NHA`,`BA_M2HA`,`VOL_M3HA`,`BIO_MGHA`,`JENKBIO_MGHA`.   

If you just have one stand, your output will be in a file named `[name of whatever stand]_stand_composite_output.csv`. It will be organized like `DBCODE`,`ENTITY`,`STANDID`,`SPECIES`,`YEAR`,`PORTION`,`TPH_NHA`,`BA_M2HA`,`VOL_M3HA`,`BIO_MGHA`,`JENKBIO_MGHA`.    

---------------------------------------
Biomass at the Plot Scale for All Plots
---------------------------------------

To compute the biomass at the plot scale for all of the plots on all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py bio plot composite --all

Your output will be in a file named `all_plots_biomass_composite_output.csv`. It will be organized like `DBCODE`,`ENTITY`,`PLOTID`,`SPECIES`,`YEAR`,`PORTION`,`TPH_NHA`,`BA_M2HA`,`VOL_M3HA`,`BIO_MGHA`,`JENKBIO_MGHA`.

--------------------------------------------------------
Biomass at the Plot Scale for a set of one or more plots
--------------------------------------------------------

To compute the biomass at the plot scale for one or more plots, just add those plots to the end of the line `tps_cli.py bio plot composite`. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. You don't have to put them all from the same stand, either, or be organized about it. Here's how you could ask for `ncna0001`, `rs010001`, `srnf0005`, and `ncna0004`.

.. code-block:: bash

    $ python3 tps_cli.py bio plot composite ncna0001 rs010001 srnf0005 ncna0004

If you have more than one plot, your output will in a file named `selected_plots_biomass_composite_output.csv`. It will be organized like `DBCODE`,`ENTITY`,`PLOTID`,`SPECIES`,`YEAR`,`PORTION`,`TPH_NHA`,`BA_M2HA`,`VOL_M3HA`,`BIO_MGHA`,`JENKBIO_MGHA`.   

If you just have one plot, your output will be in a file named `[name of whatever plot]_plot_composite_output.csv`. It will be organized like `DBCODE`,`ENTITY`,`PLOTID`,`SPECIES`,`YEAR`,`PORTION`,`TPH_NHA`,`BA_M2HA`,`VOL_M3HA`,`BIO_MGHA`,`JENKBIO_MGHA`.  

------------------------------------------
Biomass at the Stand Scale for All Studies
------------------------------------------

To compute the biomass at the stand scale for all of the stands on all of the studies, use this command. Yes, this is exactly the same as the simpler `tps_cli.py bio stand composite --all`, but if you are thinking in study mode, it might be helpful.

.. code-block:: bash

    $ python3 tps_cli.py bio study composite --all

Your output will be in a file named `all_studies_biomass_composite_output.csv`. It will be organized like `DBCODE`,`ENTITY`,`PLOTID`,`SPECIES`,`YEAR`,`PORTION`,`TPH_NHA`,`BA_M2HA`,`VOL_M3HA`,`BIO_MGHA`,`JENKBIO_MGHA`.

-----------------------------------------------------------
Biomass at the Stand Scale for a set of one or more studies
-----------------------------------------------------------

To compute the biomass at the study scale for one or more studies, just add those studies to the end of the line `tps_cli.py bio study composite`. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. You don't have to put them all from the same stand, either, or be organized about it. Here's how you could ask for `hsgy` and `alco`

.. code-block:: bash

    $ python3 tps_cli.py bio study composite hsgy alco

If you have more than one study, your output will in a file named `selected_studies_biomass_composite_output.csv`. It will be organized like `DBCODE`,`ENTITY`,`STUDYID`,`SPECIES`,`YEAR`,`PORTION`,`TPH_NHA`,`BA_M2HA`,`VOL_M3HA`,`BIO_MGHA`,`JENKBIO_MGHA`.   

If you just have one study, your output will be in a file named `[name of whatever study]_studies_composite_output.csv`. It will be organized like `DBCODE`,`ENTITY`,`STUDYID`,`SPECIES`,`YEAR`,`PORTION`,`TPH_NHA`,`BA_M2HA`,`VOL_M3HA`,`BIO_MGHA`,`JENKBIO_MGHA`.   

-----------------------------------------------------------------------------
Biomass at the Plot Scale for Individual Trees for a set of one or more plots
-----------------------------------------------------------------------------

To compute the biomass at the individual scale for one or more plots, just add those plots to the end of the line `tps_cli.py bio plot composite`. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. You don't have to put them all from the same stand, either, or be organized about it. Here's how you could ask for `ncna0001`, `rs010001`, `srnf0005`, and `ncna0004`.

.. code-block:: bash

    $ python3 tps_cli.py bio plot tree ncna0001 rs010001 srnf0005 ncna0004

Your output will be in a file named `selected_plots_indvtree_output.csv`. It will be organized like `DBCODE`, `ENTITY`, `TREEID`, `COMPONENT`, `YEAR`, `BA_M2`, `VOL_M3`, `BIO_MG`, `JENKBIO_MG`.


If you just have one plot, your output will be in a file named `[name of whatever plot]_plot_indvtree_output.csv`. It will be organized like `DBCODE`, `ENTITY`, `TREEID`, `COMPONENT`, `YEAR`, `BA_M2`, `VOL_M3`, `BIO_MG`, `JENKBIO_MG`.

-------------------------------------------------------------------------------
Biomass at the Stand Scale for Individual Trees for a set of one or more stands
-------------------------------------------------------------------------------

To compute the biomass at the individual tree scale for one or more stands, just add those stands to the end of the line `tps_cli.py bio stand tree`. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. Here's how you could ask for `ncna`, `rs01`, `srnf`, and `wr01`.

.. code-block:: bash

    $ python3 tps_cli.py bio stand tree ncna rs01 srnf wr01

Your output will be in a file named `selected_stands_indvtree_output.csv`. It will be organized like `DBCODE`, `ENTITY`, `TREEID`, `COMPONENT`, `YEAR`, `BA_M2`, `VOL_M3`, `BIO_MG`, `JENKBIO_MG`.

If you just have one stand, your output will be in a file named `[name of whatever stand]_stand_indvtree_output.csv`. It will be organized like `DBCODE`, `ENTITY`, `TREEID`, `COMPONENT`, `YEAR`, `BA_M2`, `VOL_M3`, `BIO_MG`, `JENKBIO_MG`.

-----------------------------------------------------------
Biomass at the Plot Scale for Individual Trees on All Plots
-----------------------------------------------------------

To compute the biomass at the individual tree scale for all of the plots on all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py bio plot tree --all

Your output will be in a file named `all_plots_indvtree_output.csv`. It will be organized like `DBCODE`, `ENTITY`, `TREEID`, `COMPONENT`, `YEAR`, `BA_M2`, `VOL_M3`, `BIO_MG`, `JENKBIO_MG`.

-------------------------------------------------------------
Biomass at the Stand Scale for Individual Trees on All Stands
-------------------------------------------------------------

To compute the biomass at the individual tree scale for all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py bio stand tree --all

Your output will be in a file named `all_stands_indvtree_output.csv`. It will be organized like `DBCODE`, `ENTITY`, `TREEID`, `COMPONENT`, `YEAR`, `BA_M2`, `VOL_M3`, `BIO_MG`, `JENKBIO_MG`.

-----------------------------------------------
Biomass at the Tree Scale for Less Than 3 Trees
-----------------------------------------------

To compute the biomass at the individual tree scale for one or two trees, you can use the tree scale query. For example, to get `ncna000100001` and `ta01000100001`

.. code-block:: bash

    $ python3 tps_cli.py bio tree tree ncna000100001 ta010001000001

Your output will be in a file named `selected_trees_indvtree_output.csv`. It will be organized like `DBCODE`, `ENTITY`, `TREEID`, `COMPONENT`, `YEAR`, `BA_M2`, `VOL_M3`, `BIO_MG`, `JENKBIO_MG`.

If you just have one tree, your output will be in a file named `[name of whatever tree]_tree_indvtree_output.csv`. It will be organized like `DBCODE`, `ENTITY`, `TREEID`, `COMPONENT`, `YEAR`, `BA_M2`, `VOL_M3`, `BIO_MG`, `JENKBIO_MG`.

-----------------------------------------------------
Status Checks at the Tree Scale for Less Than 3 Trees
-----------------------------------------------------

To check the status of the the biomass at the individual tree scale for one or two trees, you can use the tree scale query. This query will tell you whether or not your trees encountered a variety of non ideal conditions by generating a matrix of null or true values. The docs contain more descriptiosn of what these headers mean. But to work with the program, for example, to get `ncna000100001` and `ta01000100001`

.. code-block:: bash

    $ python3 tps_cli.py bio tree checks ncna000100001 ta010001000001

Your output will be in a file named `selected_trees_indvtree_checks.csv`. It will be organized like `TREEID`, `SPECIES`, `INTERVAL`,`SHRINK_X_FLAGGED`,`GROWTH_X_FLAGGED`,`DOUBLE_DEATH_FLAG`,`LAZARUS_FLAG`,`HOUDINI_FLAG`,`DEGRADE_FLAG`.

If you just have one tree, your output will be in a file named `[name of whatever tree]_tree_indvtree_checks.csv`. It will be organized like `TREEID`, `SPECIES`, `INTERVAL`,`SHRINK_X_FLAGGED`,`GROWTH_X_FLAGGED`,`DOUBLE_DEATH_FLAG`,`LAZARUS_FLAG`,`HOUDINI_FLAG`,`DEGRADE_FLAG``.

-------------------------------------
NPP at the Stand Scale for All Stands
-------------------------------------

To compute the NPP at the stand scale for all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py npp stand composite --all

Your output will be in a file named `all_stands_composite_npp.csv`. It will be organized like `DBCODE`,`ENTITY`, `STANDID`, `YEAR_BEGIN`, `YEAR_END`, `SPECIES`, `DELTA_TPH_NHA`,`DELTA_BA_M2HA`,`DELTA_VOL_M3HA`,`DELTA_BIO_MGHA`,`DELTA_JENKBIO_MGHA`, `MEAN_ANNUAL_NPP_BIO`, `MEAN_ANNUAL_NPP_JENKBIO`.


------------------------------------------------------
NPP at the Stand Scale for a set of one or more stands
------------------------------------------------------

To compute the biomass at the stand scale for one or more stands, just add those stands to the end of the line `tps_cli.py npp stand composite`. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. Here's how you could ask for `ncna`, `rs01`, `srnf`, and `wr01`.

.. code-block:: bash

    $ python3 tps_cli.py npp stand composite ncna rs01 srnf ws01

If you have more than one stand, your output will in a file named `selected_stands_composite_npp.csv`. It will be organized like `DBCODE`,`ENTITY`, `STANDID`, `YEAR_BEGIN`, `YEAR_END`, `SPECIES`, `DELTA_TPH_NHA`,`DELTA_BA_M2HA`,`DELTA_VOL_M3HA`,`DELTA_BIO_MGHA`,`DELTA_JENKBIO_MGHA`, `MEAN_ANNUAL_NPP_BIO`, `MEAN_ANNUAL_NPP_JENKBIO`.

If you just have one stand, your output will be in a file named `[name of whatever stand]_stand_composite_npp.csv`. It will be organized like `DBCODE`,`ENTITY`, `STANDID`, `YEAR_BEGIN`, `YEAR_END`, `SPECIES`, `DELTA_TPH_NHA`,`DELTA_BA_M2HA`,`DELTA_VOL_M3HA`,`DELTA_BIO_MGHA`,`DELTA_JENKBIO_MGHA`, `MEAN_ANNUAL_NPP_BIO`, `MEAN_ANNUAL_NPP_JENKBIO`.

-----------------------------------
NPP at the Plot Scale for All Plots
-----------------------------------

To compute the biomass at the plot scale for all of the plots on all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py npp plot composite --all

Your output will be in a file named `all_plots_composite_npp.csv`. It will be organized like `DBCODE`,`ENTITY`, `PLOTID`, `YEAR_BEGIN`, `YEAR_END`, `SPECIES`, `DELTA_TPH_NHA`,`DELTA_BA_M2HA`,`DELTA_VOL_M3HA`,`DELTA_BIO_MGHA`,`DELTA_JENKBIO_MGHA`, `MEAN_ANNUAL_NPP_BIO`, `MEAN_ANNUAL_NPP_JENKBIO`.

----------------------------------------------------
NPP at the Plot Scale for a set of one or more plots
----------------------------------------------------

To compute the NPP at the plot scale for one or more plots, just add those plots to the end of the line `tps_cli.py npp plot composite`. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. You don't have to put them all from the same stand, either, or be organized about it. Here's how you could ask for `ncna0001`, `rs010001`, `srnf0005`, and `ncna0004`.

.. code-block:: bash

    $ python3 tps_cli.py npp plot composite ncna0001 rs010001 srnf0005 ncna0004

If you have more than one plot, your output will in a file named `selected_plots_composite_npp.csv`. It will be organized like `DBCODE`,`ENTITY`, `PLOTID`, `YEAR_BEGIN`, `YEAR_END`, `SPECIES`, `DELTA_TPH_NHA`,`DELTA_BA_M2HA`,`DELTA_VOL_M3HA`,`DELTA_BIO_MGHA`,`DELTA_JENKBIO_MGHA`, `MEAN_ANNUAL_NPP_BIO`, `MEAN_ANNUAL_NPP_JENKBIO`.

If you just have one plot, your output will be in a file named `[name of whatever plot]_plot_npp_output.csv`. It will be organized like `DBCODE`,`ENTITY`, `PLOTID`, `YEAR_BEGIN`, `YEAR_END`, `SPECIES`, `DELTA_TPH_NHA`,`DELTA_BA_M2HA`,`DELTA_VOL_M3HA`,`DELTA_BIO_MGHA`,`DELTA_JENKBIO_MGHA`, `MEAN_ANNUAL_NPP_BIO`, `MEAN_ANNUAL_NPP_JENKBIO`.

--------------------------------------
NPP at the Stand Scale for All Studies
--------------------------------------

To compute the NPP at the plot scale for all of the plots on all of the studies, use this command. This is basically the same as what would happen if you were to just compute it for all stands.

.. code-block:: bash

    $ python3 tps_cli.py npp study composite --all

Your output will be in a file named `all_plots_composite_npp.csv`. It will be organized like `DBCODE`,`ENTITY`, `STANDID`, `YEAR_BEGIN`, `YEAR_END`, `SPECIES`, `DELTA_TPH_NHA`,`DELTA_BA_M2HA`,`DELTA_VOL_M3HA`,`DELTA_BIO_MGHA`,`DELTA_JENKBIO_MGHA`, `MEAN_ANNUAL_NPP_BIO`, `MEAN_ANNUAL_NPP_JENKBIO`.

-------------------------------------------------------
NPP at the Stand Scale for a set of one or more studies
-------------------------------------------------------

To compute the NPP at the stand scale for one or more studies, just add those studies to the end of the line `tps_cli.py npp study composite`. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. There are not so many studies out there, and be careful that you make the names accurate. Again, this is just a luxury function for looking at studies instead of stands or plots.

.. code-block:: bash

    $ python3 tps_cli.py npp study composite alco hsgy

If you have more than one plot, your output will in a file named `selected_studies_composite_npp.csv`. It will be organized like `DBCODE`,`ENTITY`, `STANDID`, `YEAR_BEGIN`, `YEAR_END`, `SPECIES`, `DELTA_TPH_NHA`,`DELTA_BA_M2HA`,`DELTA_VOL_M3HA`,`DELTA_BIO_MGHA`,`DELTA_JENKBIO_MGHA`, `MEAN_ANNUAL_NPP_BIO`, `MEAN_ANNUAL_NPP_JENKBIO`.

If you just have one plot, your output will be in a file named `[name of whatever study]_npp_output.csv`. It will be organized like `DBCODE`,`ENTITY`, `STANDID`, `YEAR_BEGIN`, `YEAR_END`, `SPECIES`, `DELTA_TPH_NHA`,`DELTA_BA_M2HA`,`DELTA_VOL_M3HA`,`DELTA_BIO_MGHA`,`DELTA_JENKBIO_MGHA`, `MEAN_ANNUAL_NPP_BIO`, `MEAN_ANNUAL_NPP_JENKBIO`.



