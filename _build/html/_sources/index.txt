.. ptree documentation master file, created by
   sphinx-quickstart on Thu Sep 17 20:42:35 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the TPS documentation!
=================================

TPS (Tree, Plot, Stand) is a simple set of Python3 scripts for processing the "PSP Study" forest inventory data (contained in entity TP001) into the required Trees per Hectare (TPH), Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg and Mg/Ha ), Volume ( m\ :sup:`3` ), and Basal Area ( m\ :sup:`2` ) tree and stand level summaries. It is also set up to compute the delta Trees Per Hectare (TPH), delta Biomass (Mg/Ha), delta Jenkins Biomass ( Mg and Mg/Ha ), delta Basal Area ( m\ :sup:`2` ), delta Volume ( m\ :sup:`3` ) between re-measurement intervals and to solve for Bole Net Primary Productivity (NPP, Mg/Ha/yr ) using the "change in biomass plus mortality and plus ingrowth" technique. It has the capacity to produce both species specific and aggregate metrics for each remeasurement or the interval between them.

Outputs from TPS go to:

* TP00107 - By species Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg and Mg/Ha ), Basal Area ( m\ :sup:`2` ), Volume ( m\ :sup:`3` ), and wood density for stands by species
* TP00108 - By species Bole NPP (NPP, Mg/Ha/yr ) and the change in Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg and Mg/Ha ), Basal Area ( m\ :sup:`2` ), Volume ( m\ :sup:`3` ) between intervals.
* TP00109 - Whole stand summary of Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg and Mg/Ha ), Basal Area ( m\ :sup:`2` ), Volume ( m\ :sup:`3` ), and wood density for stands by species
* TP00110 - Whole stand summary of Bole NPP (NPP, Mg/Ha/yr ) and the change in Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg and Mg/Ha ), Basal Area ( m\ :sup:`2` ), Volume ( m\ :sup:`3` ) between intervals.


TPS contains 3 core modules: ``tps_Tree`` (for individual trees), ``tps_Stand`` (for stands), and ``tps_NPP`` (for differences between stands over time). ``tps_CLI`` is a command line interface for using the appropriate module. Within each tps program, reliance on a core data structure is consistent. This structure is basically:

.. code-block:: python

    STAND ID : 
      {YEARS : 
        {SPECIES : 
          {PLOTS : 
            {[raw data]}
          }
        }
      } 

This structure helps to organize the inputs in such a way that they can be easily iterated across to summarize new outputs. This documentation has been auto-generated from these modules using the Sphinx Autodoc package. Documentation is also included from  two modules for parameterizing the computations, ``biomass_basis`` and ``poptree_basis``. ``biomass_basis`` contains the rules for parsing the biomass computation equations (found in table TP00111) and generating functions that take DBH and produce the outputs needed; ``poptree_basis`` contains the database connectors and a parameter object, ``Capture``, which contains the information about the stands, plots, and study protocols (detail plot or not, mortality survey or not, etc.) that is needed in the tps modules. When executing a script to process a number of trees or stands, the ``Capture`` object needs to only be created once, greatly reducing the amount of database queries that might otherwise occur. 


Contents:
=========

.. toctree::
   :maxdepth: 2

Database Connectors and Cached Settings:
----------------------------------------

``poptree_basis.py`` contains the classes and functions for connecting to the FSDBDATA database. To make this connection, one needs to also include a configuration file named specifically ``config_2.yaml`` in the base directory where ``poptree_basis`` is located. This file should look like this:

.. code-block:: python

    server: stewartia.forestry.oregonstate.edu:1433
    user: USERNAME
    password: PASSWORD
    database: FSDBDATA

    query_file: qf_2.yaml

    litedb: areas.db
    litetable: plotAreas

It is imperative that the `keys` on the left-side of the configuration file match the keys in the program. If TP00112 is not in place, I locally run a similar table in SQLite3, which is where the ``litedb`` parameter comes into play. 

Your SQL queries are in ``qf_2.yaml``. This file is included with this program, and should also be located in the base directory with ``poptree_basis``. You can re-configure or add queries there so that the changes propogate throughout the modules. This is done by creating an object called ``YamlConn`` with ``poptree_basis`` which is responsible for managing your connections and queries.

In the ``tps_CLI`` commands can be issued to gather a specific tree, stand, set of trees, etc. 

.. automodule:: poptree_basis
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

Biomass Equations:
------------------

``biomass_basis.py`` uses the information in TP00111 to compute the Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg and Mg/Ha ), Basal Area ( m\ :sup:`2` ), Volume ( m\ :sup:`3` ). Wood density is assigned by ``biomass_basis`` but no computation is involved apart from using it to switch between volume and biomass when needed.

.. automodule:: biomass_basis
    :members:
    :undoc-members:
    :inherited-members:
    :show-inheritance:

Individual Trees:
-----------------

``tps_Tree.py`` contains classes and functions for computing the attributes of individual trees. Each individual tree as defined in TP00101 is an instance of a class of ``Tree``. For example, ``NCNA000300005`` is one Tree. All the remeasurements taken on one individual tree are encapsulated into a single instance of Tree for that individual, and can be accessed using the property of ``Tree.state``. 

.. automodule:: tps_Tree
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

Stands:
-------
``tps_Stand.py`` contains classes and functions for computing the attributes on the stand scale. Each stand is defined as all the plots during a given re-measurement year. Stand attributes are computed on a per-hectare basis. Some stands contain ``detail plots`` with small trees representative of the stand as a whole.   

.. automodule:: tps_Stand
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

.. automodule:: tps_cli
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
