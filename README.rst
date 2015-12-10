********************************************
TPS: Tree, Plot, Stand - Biomass Aggregation
********************************************

TPS is a set of Python 3 modules for the aggregation of trees, plots, and stands from the USFS reference stands data maintained by the Corvallis Forest Science Lab.


.. contents::
    :local:
    :depth: 2
    :backlinks: none


=============
Main Modules
=============

* ``tps_Tree`` <- individual trees, to be computed ID by ID, and perform checks on individuals, ID by ID
* ``tps_Stand`` <- stands, plots on stands, trees on stands, for larger-scale computations
* ``tps_NPP`` <- net primary productivity for plots and stands
* ``tps_cli`` <- command line interface
* ``tps_Sample`` <- tests - queries to 'ncna' that should always work
* SQL queries and configs in yaml files for interoperability!
* lots of docs!

============
Installation
============

Set up Python 3 on your computer, and then run the darn thing!
Best to start with ``tps_Sample``, which will run a series of test trees and stands on a known dataset (that it will access from the server to test your connection) and output the results. To run it do:

.. code-block:: bash

    $ python3 tps_Sample.py

Assuming this goes well, please read the docs! The docs are in index.html, currently in the ``_build/`` folder. You'll be running the remainder of your analyses out of the command line interface (`tps_cli.py`) for now, but there are a lot of options.

If you have an issue with the code, please submit it using github and github only. Issues submitted via email or other methods will not be addressed. To get a fixed copy of the program, you'll need to install github and get your own clone of the repository, and keep it up to date with this master. Fox is not responsible for helping you maintain your local copy of the repository.

-------------------
Development version
-------------------

The **latest development version** can be installed directly from GitHub. Use this repository. Note that when Fox leaves, maintenance will be sporadic at best. Issues and pull requests will be addressed when possible, with pull requests receiving far more attention (as it shows you made an attempt to fix your own problems first :) ).

===============================
Documentation in the Literature
===============================

The biomass computations began with computations by Gody and Lutz. These were later passed on to Becky, Rob, and myself. There are two main sources, BIOPAK and dendrometer regressions. Dendrometer regressions are from volume, and use the TV009 or TP072 databases available from the FSDB. The TP072 database references the `BIOPAK <http://andrewsforest.oregonstate.edu/data/tools/software/biopak.cfm?topnav=149>`_ software. Metadata and data from TV009 is `here <http://andrewsforest.oregonstate.edu/data/abstract.cfm?dbcode=TV009>`_.

For computation of height (where needed), the `Garman <http://andrewsforest.oregonstate.edu/pubs/pdf/pub1445.pdf>`_  et al.(1995) methods were used, and height was computed as ``Ht_m = 1.37 + (b0*(1-exp(b1*DBH_cm))**b2)``. Height computations are largely internal to the `biomass_basis.py` module.

If you are at Oregon State, you can also access the equations in the shared ``T-drive`` under ``GROUPS > FSDB > TP001 > biomass_programs`` to see the original documentation from Gody.

----------------
Equation Listing
----------------

Six different "forms" of biomass equation are used depending on source of data and tree species. The following shows the syntax for the math for every species of tree. When height is needed, the subsequent table shows the height calculation. Components are ``BAT`` (total aboveground biomass, Mg ), ``VSW`` (volume of the stemwood,  m\ :sup:`3` ), ``HT`` (height, m), ``VAE`` (volume aboveground entire tree, m\ :sup:`3`) and ``dbh`` (diameter at breast height, cm). When volume is the product, a wood density (``woodden``) value in g / m\ :sup:`3` (see reference) is used to convert to biomass.

=========  ===========  =============================================================================
Species    Component    Biomass
=========  ===========  =============================================================================
``QUKE``   ``BAT``      ``math.exp(-4.49787 + 0.7225820*math.log(0.01*dbh) + 1.72264*math.log(HT)``
``ACMA``   ``VAE``      ``woodden*0.00007*dbh*2.2246200*HT**0.57561``
``CHNO``   ``VSW``      ``1.01600*woodden*(0.0001868*dbh**2.40240)``
``CHNO``   ``VSW``      ``1.02090*woodden*(0.0001076*dbh**2.56160)``
``ABAM``   ``VSW``      ``1.04720*woodden*(0.0001129*dbh**2.58670)``
``ABCO``   ``VSW``      ``1.03060*woodden*(0.0000932*dbh**2.62060)``
``ABCO``   ``VSW``      ``1.02560*woodden*(0.0000473*dbh**2.77270)``
``ABGR``   ``VSW``      ``1.02560*woodden*(0.0000473*dbh**2.77270)``
``ABLA2``  ``VSW``      ``1.01540*woodden*(0.0001896*dbh**2.38090)``
``ABMA``   ``VSW``      ``1.01440*woodden*(0.0000527*dbh**2.74780)``
``ABPR``   ``VSW``      ``1.01710*woodden*(0.0001227*dbh**2.58120)``
``PSME``   ``VSW``      ``1.03090*woodden*(0.0002146*dbh**2.43670)``
``PSME``   ``VSW``      ``1.02960*woodden*(0.0002286*dbh**2.42470)``
``PICO``   ``VSW``      ``1.02140*woodden*(0.0002840*dbh**2.33630)``
``PIEN``   ``VSW``      ``1.01400*woodden*(0.0001160*dbh**2.57180)``
``PIJE``   ``VSW``      ``1.01560*woodden*(0.0000158*dbh**2.95420)``
``PILA``   ``VSW``      ``1.02110*woodden*(0.0000557*dbh**2.70890)``
``PILA``   ``VSW``      ``1.02110*woodden*(0.0000557*dbh**2.70890)``
``PISI``   ``VSW``      ``1.02220*woodden*(0.0003460*dbh**2.33200)``
``PISI``   ``VSW``      ``1.02220*woodden*(0.0003460*dbh**2.33200)``
``TABR``   ``VSW``      ``1.05960*woodden*(0.0001189*dbh**2.59890)``
``THPL``   ``VSW``      ``1.01600*woodden*(0.0001860*dbh**2.40240)``
``TSHE``   ``VSW``      ``1.05960*woodden*(0.0001189*dbh**2.59890)``
``TSME``   ``VSW``      ``1.01920*woodden*(0.0000929*dbh**2.59150)``
``THPL``   ``VSW``      ``woodden*0.23080*(HT*(0.01*dbh)**2)``
``PIMO``   ``VSW``      ``woodden*0.36080*(HT*(0.01*dbh)**2)``
``PIPO``   ``VSW``      ``woodden*0.36080*(HT*(0.01*dbh)**2)``
``LIDE2``  ``VSW``      ``woodden*0.33250*(HT*(0.01*dbh)**2)``
``ABPR``   ``VSW``      ``woodden*0.27340*(HT*(0.01*dbh)**2)``
``ABMA``   ``VSW``      ``woodden*0.31020*(HT*(0.01*dbh)**2)``
``CADE3``  ``VSW``      ``woodden*0.33250*(HT*(0.01*dbh)**2)``
``CONU``   ``BAT``      ``1.*10**(-6)*math.exp(5.13118+2.1504600*math.log(dbh))``
``ALIN``   ``BAT``      ``1.*10**(-6)*math.exp(5.13118+2.1504600*math.log(dbh))``
``ALRU``   ``BAT``      ``1.*10**(-6)*math.exp(5.13118+2.1504600*math.log(dbh))``
``ALSI``   ``BAT``      ``1.*10**(-6)*math.exp(5.13118+2.1504600*math.log(dbh))``
``POTR``   ``BAT``      ``1.*10**(-6)*math.exp(5.13118+2.1504600*math.log(dbh))``
``POTR2``  ``BAT``      ``1.*10**(-6)*math.exp(5.13118+2.1504600*math.log(dbh))``
``PREM``   ``BAT``      ``1.*10**(-6)*math.exp(5.13118+2.1504600*math.log(dbh))``
``PRUNU``  ``BAT``      ``1.*10**(-6)*math.exp(5.13118+2.1504600*math.log(dbh))``
``ARME``   ``BAT``      ``1.*10**(-6)*math.exp(1.01532+0.0000380*math.log(dbh))``
``ACGL``   ``BAT``      ``1.*10**(-6)*math.exp(3.63400+2.7520000*math.log(dbh))``
``SASC``   ``BAT``      ``1.*10**(-6)*math.exp(3.45950+2.3891300*math.log(dbh))``
``SEGI``   ``BSW``      ``math.exp(-11.01740+2.5907000*math.log(dbh))``
``CACH``   ``VSW``      ``woodden*HT**0.77467*0.0000569*(dbh)**2.07202``
=========  ===========  =============================================================================

The tables below show the height equations used, by species, when necessary.


=========  ===========  =============================================================================
Species    Component    Height
=========  ===========  =============================================================================
``QUKE``   ``HT``       ``1.37 + 24.81869*(1-math.exp(-0.026937*dbh))**0.915991``
``ACMA``   ``HT``       ``1.37 + 30.41311*(1-math.exp(-0.034245*dbh))**0.682100``
``THPL``   ``HT``       ``1.37 + 56.91574*(1-math.exp(-0.012625*dbh))**0.935899``
``PIMO``   ``HT``       ``1.37 + 44.60542*(1-math.exp(-0.024401*dbh))**1.219469``
``PIPO``   ``HT``       ``1.37 + 44.60542*(1-math.exp(-0.024401*dbh))**1.219469``
``LIDE2``  ``HT``       ``1.37 + 39.82180*(1-math.exp(-0.027393*dbh))**1.403222``
``ABPR``   ``HT``       ``1.37 + 78.60353*(1-math.exp(-0.013330*dbh))**1.185140``
``ABMA``   ``HT``       ``1.37 + 9.05185*(1-math.exp(-0.016177*dbh))**1.152987``
``CACH``   ``HT``       ``1.37 + 40.66479*(1-math.exp(-0.017775*dbh))**0.873626``
=========  ===========  =============================================================================

-------------------------------
Programmatic Documentation Link
-------------------------------

Documentation for the `TPS` programs is located `here <http://htmlpreview.github.io/?https://github.com/dataRonin/ptree/blob/dev/_build/html/index.html>`_. Documentation is autogenerated by `sphinx autodoc <http://sphinx-doc.org/ext/autodoc.html>`_.

====================
Command Line Options
====================

The command line tool has a variety of options for your output. These have all been tested as of 11-06-2015. The command line options are set to organize your access to the data by the type of analysis, the scale of the analysis, the aggregation of the analysis, and finally specific targets for the analysis. Because there are some combinations of these that simply make no sense (``bio tree composite ncna00100001``, for example, could not run because there is no stand over which to aggregate by species one single tree), these options are blocked programmatically. Options that are allowed are as follows:

--------------------
Details About 1 Tree
--------------------

This command will get you details about 1 tree and either print them to the screen or to a file. Pretend the tree of your desire is ``ncna0001000001``

.. code-block:: bash

    $ python3 tps_cli.py dtx ncna000100001

The computer will ask if you would like to have a file, and if so to type ``Y``. If you type ``Y``, the output will go to a file named (in this case for ``ncna0001000001``) ``ncna000100001_tags_and_checks.csv``. If you don't type ``Y`` (you can even just press enter), you will see on your screen something like:

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

Your output will be in a file named ```all_stands_biomass_composite_output.csv```. It will be organized like ``DBCODE, ENTITY, STANDID, SPECIES, YEAR, PORTION, TPH_NHA, BA_M2HA, VOL_M3HA, BIO_MGHA, JENKBIO_MGHA``.

----------------------------------------------------------
Biomass at the Stand Scale for a set of one or more stands
----------------------------------------------------------

To compute the biomass at the stand scale for one or more stands, just add those stands to the end of the line ``tps_cli.py bio stand composite``. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. Here's how you could ask for ``ncna``, ``rs01``, ``srnf``, and ``wr01``.

.. code-block:: bash

    $ python3 tps_cli.py bio stand composite ncna rs01 srnf ws01

If you have more than one stand, your output will in a file named ``selected_stands_biomass_composite_output.csv``. It will be organized like ``DBCODE, ENTITY, STANDID, SPECIES, YEAR, PORTION, TPH_NHA, BA_M2HA, VOL_M3HA, BIO_MGHA, JENKBIO_MGHA``.

If you just have one stand, your output will be in a file named ``[name of whatever stand]_stand_composite_output.csv``. It will be organized like ``DBCODE, ENTITY, STANDID, SPECIES, YEAR, PORTION, TPH_NHA, BA_M2HA, VOL_M3HA, BIO_MGHA, JENKBIO_MGHA``.

---------------------------------------
Biomass at the Plot Scale for All Plots
---------------------------------------

To compute the biomass at the plot scale for all of the plots on all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py bio plot composite --all

Your output will be in a file named ``all_plots_biomass_composite_output.csv``. It will be organized like ``DBCODE, ENTITY, PLOTID, SPECIES, YEAR, PORTION, TPH_NHA, BA_M2HA, VOL_M3HA, BIO_MGHA, JENKBIO_MGHA``.

--------------------------------------------------------
Biomass at the Plot Scale for a set of one or more plots
--------------------------------------------------------

To compute the biomass at the plot scale for one or more plots, just add those plots to the end of the line `tps_cli.py bio plot composite`. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. You don't have to put them all from the same stand, either, or be organized about it. Here's how you could ask for ``ncna0001``, ``rs010001``, ``srnf0005``, and ``ncna0004``.

.. code-block:: bash

    $ python3 tps_cli.py bio plot composite ncna0001 rs010001 srnf0005 ncna0004

If you have more than one plot, your output will in a file named ``selected_plots_biomass_composite_output.csv``. It will be organized like ``DBCODE, ENTITY, PLOTID, SPECIES, YEAR, PORTION, TPH_NHA, BA_M2HA, VOL_M3HA, BIO_MGHA, JENKBIO_MGHA``.

If you just have one plot, your output will be in a file named ``[name of whatever plot]_plot_composite_output.csv``. It will be organized like ``DBCODE, ENTITY, PLOTID, SPECIES, YEAR, PORTION, TPH_NHA, BA_M2HA, VOL_M3HA, BIO_MGHA, JENKBIO_MGHA``.

------------------------------------------
Biomass at the Stand Scale for All Studies
------------------------------------------

To compute the biomass at the stand scale for all of the stands on all of the studies, use this command. Yes, this is exactly the same as the simpler ``tps_cli.py bio stand composite --all``, but if you are thinking in study mode, it might be helpful.

.. code-block:: bash

    $ python3 tps_cli.py bio study composite --all

Your output will be in a file named ``all_studies_biomass_composite_output.csv``. It will be organized like ``DBCODE, ENTITY, PLOTID, SPECIES, YEAR, PORTION, TPH_NHA, BA_M2HA, VOL_M3HA, BIO_MGHA, JENKBIO_MGHA``.

-----------------------------------------------------------
Biomass at the Stand Scale for a set of one or more studies
-----------------------------------------------------------

To compute the biomass at the study scale for one or more studies, just add those studies to the end of the line ``tps_cli.py bio study composite``. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. You don't have to put them all from the same stand, either, or be organized about it. Here's how you could ask for ``hsgy`` and ``alco``

.. code-block:: bash

    $ python3 tps_cli.py bio study composite hsgy alco

If you have more than one study, your output will in a file named ``selected_studies_biomass_composite_output.csv``. It will be organized like ``DBCODE, ENTITY, STUDYID, SPECIES, YEAR, PORTION, TPH_NHA, BA_M2HA, VOL_M3HA, BIO_MGHA, JENKBIO_MGHA``.

If you just have one study, your output will be in a file named ``[name of whatever study]_studies_composite_output.csv``. It will be organized like ``DBCODE, ENTITY, STUDYID, SPECIES, YEAR, PORTION, TPH_NHA, BA_M2HA, VOL_M3HA, BIO_MGHA, JENKBIO_MGHA``.


-------------------------------------------------------------------------------
Biomass at the Stand Scale for Individual Trees for a set of one or more stands
-------------------------------------------------------------------------------

**You cannot process individual tree biomasses at the scale of ``plot``. There does not exist code to do this. You get ``Stand`` and ``Tree`` but not ``plot``.**



To compute the biomass at the individual tree scale for one or more stands, just add those stands to the end of the line `tps_cli.py bio stand tree`. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. Here's how you could ask for `ncna`, `rs01`, `srnf`, and `wr01`.

.. code-block:: bash

    $ python3 tps_cli.py bio stand tree ncna rs01 srnf wr01

Your output will be in a file named ``selected_stands_indvtree_output.csv``. It will be organized like ``DBCODE, ENTITY, TREEID, COMPONENT, YEAR, BA_M2, VOL_M3, BIO_MG, JENKBIO_MG``.

If you just have one stand, your output will be in a file named ``[name of whatever stand]_stand_indvtree_output.csv``. It will be organized like ``DBCODE, ENTITY, TREEID, COMPONENT, YEAR, BA_M2, VOL_M3, BIO_MG, JENKBIO_MG``.

-----------------------------------------------------------
Biomass at the Plot Scale for Individual Trees on All Plots
-----------------------------------------------------------

To compute the biomass at the individual tree scale for all of the plots on all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py bio plot tree --all

Your output will be in a file named ``all_plots_indvtree_output.csv``. It will be organized like ``DBCODE, ENTITY, TREEID, COMPONENT, YEAR, BA_M2, VOL_M3, BIO_MG, JENKBIO_MG``.

-------------------------------------------------------------
Biomass at the Stand Scale for Individual Trees on All Stands
-------------------------------------------------------------

To compute the biomass at the individual tree scale for all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py bio stand tree --all

Your output will be in a file named ``all_stands_indvtree_output.csv``. It will be organized like ``DBCODE, ENTITY, TREEID, COMPONENT, YEAR, BA_M2, VOL_M3, BIO_MG, JENKBIO_MG``.

-----------------------------------------------
Biomass at the Tree Scale for Less Than 3 Trees
-----------------------------------------------

To compute the biomass at the individual tree scale for one or two trees, you can use the tree scale query. For example, to get ``ncna000100001`` and ``ta01000100001``

.. code-block:: bash

    $ python3 tps_cli.py bio tree tree ncna000100001 ta010001000001

Your output will be in a file named ``selected_trees_indvtree_output.csv``. It will be organized like ``DBCODE, ENTITY, TREEID, COMPONENT, YEAR, BA_M2, VOL_M3, BIO_MG, JENKBIO_MG``.

If you just have one tree, your output will be in a file named ``[name of whatever tree]_tree_indvtree_output.csv``. It will be organized like ``DBCODE, ENTITY, TREEID, COMPONENT, YEAR, BA_M2, VOL_M3, BIO_MG, JENKBIO_MG`.

-----------------------------------------------------
Status Checks at the Tree Scale for Less Than 3 Trees
-----------------------------------------------------

To check the status of the the biomass at the individual tree scale for one or two trees, you can use the tree scale query. This query will tell you whether or not your trees encountered a variety of non ideal conditions by generating a matrix of null or true values. The docs contain more descriptiosn of what these headers mean. But to work with the program, for example, to get ``ncna000100001`` and ``ta01000100001``

.. code-block:: bash

    $ python3 tps_cli.py bio tree checks ncna000100001 ta010001000001

Your output will be in a file named ``selected_trees_indvtree_checks.csv``. It will be organized like ``TREEID, SPECIES, INTERVAL, SHRINK_X_FLAGGED, GROWTH_X_FLAGGED, DOUBLE_DEATH_FLAG, LAZARUS_FLAG, HOUDINI_FLAG, DEGRADE_FLAG``.

IF A TREE ONLY HAS ONE REMEASUREMENT IT WILL NOT BE OUTPUT. THE STATUS CHECKS DEPEND ON A DIFFERENCE BETWEEN SUBSEQUENT REMEASUREMENTS. THE DEFINITIONS OF THE FLAGS ARE IN THE BUILD DOCUMENTATION.

If you just have one tree, your output will be in a file named ``[name of whatever tree]_tree_indvtree_checks.csv``. It will be organized like ``TREEID, SPECIES, INTERVAL, SHRINK_X_FLAGGED, GROWTH_X_FLAGGED, DOUBLE_DEATH_FLAG, LAZARUS_FLAG, HOUDINI_FLAG, DEGRADE_FLAG``.

-------------------------------------
NPP at the Stand Scale for All Stands
-------------------------------------

To compute the NPP at the stand scale for all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py npp stand composite --all

Your output will be in a file named ``all_stands_composite_npp.csv``. It will be organized like ``DBCODE, ENTITY, STANDID, YEAR_BEGIN, YEAR_END, SPECIES, DELTA_TPH_NHA, DELTA_BA_M2HA, DELTA_VOL_M3HA, DELTA_BIO_MGHA, DELTA_JENKBIO_MGHA, MEAN_ANNUAL_NPP_BIO, MEAN_ANNUAL_NPP_JENKBIO``.


------------------------------------------------------
NPP at the Stand Scale for a set of one or more stands
------------------------------------------------------

To compute the NPP at the stand scale for one or more stands, just add those stands to the end of the line ``tps_cli.py npp stand composite``. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. Here's how you could ask for ``ncna``, ``rs01``, ``srnf``, and ``wr01``.

.. code-block:: bash

    $ python3 tps_cli.py npp stand composite ncna rs01 srnf ws01

If you have more than one stand, your output will in a file named ``selected_stands_composite_npp.csv``. It will be organized like ``DBCODE, ENTITY, STANDID, YEAR_BEGIN, YEAR_END, SPECIES, DELTA_TPH_NHA, DELTA_BA_M2HA, DELTA_VOL_M3HA, DELTA_BIO_MGHA, DELTA_JENKBIO_MGHA, MEAN_ANNUAL_NPP_BIO, MEAN_ANNUAL_NPP_JENKBIO``.

If you just have one stand, your output will be in a file named ``[name of whatever stand]_stand_composite_npp.csv``. It will be organized like ``DBCODE, ENTITY, STANDID ,YEAR_BEGIN, YEAR_END, SPECIES, DELTA_TPH_NHA, DELTA_BA_M2HA, DELTA_VOL_M3HA, DELTA_BIO_MGHA, DELTA_JENKBIO_MGHA, MEAN_ANNUAL_NPP_BIO, MEAN_ANNUAL_NPP_JENKBIO``.

-----------------------------------
NPP at the Plot Scale for All Plots
-----------------------------------

To compute the NPP at the plot scale for all of the plots on all of the stands, use this command.

.. code-block:: bash

    $ python3 tps_cli.py npp plot composite --all

Your output will be in a file named ``all_plots_composite_npp.csv``. It will be organized like ``DBCODE, ENTITY, PLOTID, YEAR_BEGIN, YEAR_END, SPECIES, DELTA_TPH_NHA, DELTA_BA_M2HA, DELTA_VOL_M3HA, DELTA_BIO_MGHA, DELTA_JENKBIO_MGHA, MEAN_ANNUAL_NPP_BIO, MEAN_ANNUAL_NPP_JENKBIO``.

----------------------------------------------------
NPP at the Plot Scale for a set of one or more plots
----------------------------------------------------

To compute the NPP at the plot scale for one or more plots, just add those plots to the end of the line ``tps_cli.py npp plot composite``. You can add as many as you want! You don't need quotes, but you can put them. Don't put commas. Separate them with one space. You don't have to put them all from the same stand, either, or be organized about it. Here's how you could ask for ``ncna0001``, ``rs010001``, ``srnf0005``, and ``ncna0004``.

.. code-block:: bash

    $ python3 tps_cli.py npp plot composite ncna0001 rs010001 srnf0005 ncna0004

If you have more than one plot, your output will in a file named either ``plotname_plotname_plotname_plot_npp_output.csv``, or, if this cannot work, in ``selected_plots_composite_npp.csv``. It will be organized like ``DBCODE, ENTITY, PLOTID, YEAR_BEGIN, YEAR_END, SPECIES, DELTA_TPH_NHA, DELTA_BA_M2HA, DELTA_VOL_M3HA, DELTA_BIO_MGHA, DELTA_JENKBIO_MGHA, MEAN_ANNUAL_NPP_BIO, MEAN_ANNUAL_NPP_JENKBIO``.

If you just have one plot, your output will be in a file named ``[name of whatever plot]_plot_npp_output.csv``. It will be organized like ``DBCODE, ENTITY, PLOTID, YEAR_BEGIN, YEAR_END, SPECIES, DELTA_TPH_NHA, DELTA_BA_M2HA, DELTA_VOL_M3HA, DELTA_BIO_MGHA, DELTA_JENKBIO_MGHA, MEAN_ANNUAL_NPP_BIO, MEAN_ANNUAL_NPP_JENKBIO``.

--------------------------------------
NPP at the Stand Scale for All Studies
--------------------------------------

To compute the NPP at the plot scale for all of the plots on all of the studies, use this command. This is basically the same as what would happen if you were to just compute it for all stands.

.. code-block:: bash

    $ python3 tps_cli.py npp study composite --all

Your output will be in a file named ``all_plots_composite_npp.csv``. It will be organized like ``DBCODE, ENTITY, STANDID, YEAR_BEGIN, YEAR_END, SPECIES, DELTA_TPH_NHA, DELTA_BA_M2HA, DELTA_VOL_M3HA, DELTA_BIO_MGHA, DELTA_JENKBIO_MGHA, MEAN_ANNUAL_NPP_BIO, MEAN_ANNUAL_NPP_JENKBIO``.

