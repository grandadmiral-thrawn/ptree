.. ptree documentation master file, created by
   sphinx-quickstart on Thu Sep 17 20:42:35 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the TPS documentation!
=================================

TPS (Tree, Plot, Stand) is a simple set of Python3 scripts for processing the "PSP Study" forest inventory data (contained in entity TP001) into necessary outputs. These output are number of trees per Hectare (TPHA), Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg and Mg/Ha ), Volume ( m\ :sup:`3` ), and Basal Area ( m\ :sup:`2` ) tree, plot, and stand level summaries. It is also set up to compute the delta Trees Per Hectare (TPH), delta Biomass ( Mg/Ha ), delta Jenkins Biomass ( Mg/Ha ), delta Basal Area ( m\ :sup:`2` ), delta Volume ( m\ :sup:`3` ) between re-measurement intervals and to solve for aboveground Net Primary Productivity ( NPP, Mg/Ha/yr ) using the "change in biomass plus mortality and plus ingrowth" technique pioneered by `Acker <http://and.lternet.edu/lter/pubs/pdf/pub2824.pdf>`_. Outputs are labelled as "composite" and contain both species-specific (labelled according to the `taxa <http://andrewsforest.oregonstate.edu/data/domains.cfm?domain=taxa%20%20%20%20&dbcode=Tp001&attid=7268&topnav=8>`_) and aggregate metrics for each remeasurement or the interval between them. When trees are measured as "additions" to an existing remeasurement, they are included in the prior remeasurement or establishment year; when they are labelled as "mortalities" they are included in the subsequent remeasurement or establishment year. Thus, recent "mortalities" data, such as on WS02, may not be included in any outputs other than individual tree, as it does not yet have a subsequent year of remeasurement to be passed to.

Documentation for TP001 is found `here <http://andrewsforest.oregonstate.edu/data/abstract.cfm?dbcode=Tp001>`_. The README.rst file for the program's `GitHub <https://github.com/dataRonin/ptree>`_ repository details installation, how to run the command line interface, and sources for additional information. The README file also also contains basic instructions for pull requests and issues.

**NOTE**: A brief description of the lamdba function namespace issue is `here <http://dataronin.github.io/posts/20151211_lambdas.html>`_. Please be advised that the dataronin.github.io page is not yet completed and this is currently the only valid content on the site.

Outputs from TPS go to:

* TP00106 - Stand Composite Biomass - By species and whole stand biomass ( Mg/Ha ), Jenkins Biomass ( Mg/Ha ), Basal Area ( m\ :sup:`2`/Ha ), Volume ( m\ :sup:`3`/Ha ), and trees per hectare for stands by species and in aggregate.
* TP00107 - Stand Composite NPP - By species and whole stand aboveground NPP ( NPP, Mg/Ha/yr ) and the change (delta) in Biomass ( Mg/Ha ), Jenkins Biomass ( Mg/Ha ), Basal Area ( m\ :sup:`2`/Ha ), Volume ( m\ :sup:`3`/Ha ) between remeasurement intervals.
* TP00108 - Plot Composite Biomass - By species and whole plot biomass ( Mg/Ha ), Jenkins Biomass ( Mg/Ha ), Basal Area ( m\ :sup:`2`/Ha ), Volume ( m\ :sup:`3`/Ha ), and trees per hectare for plots within stands by species and in aggregate.
* TP00109 - Plot Composite NPP - By species and whole plot aboveground NPP ( NPP, Mg/Ha/yr ) and the change (delta) in Biomass ( Mg/Ha ), Jenkins Biomass ( Mg/Ha ), Basal Area ( m\ :sup:`2`/Ha ), Volume ( m\ :sup:`3`/Ha ) between remeasurement intervals.
* TP00113 - Individual Tree Biomass - Each individual Tree (by treeid) biomass ( Mg/Ha ), Jenkins Biomass ( Mg/Ha ), Basal Area ( m\ :sup:`2`/Ha ), Volume ( m\ :sup:`3`/Ha ). The "component" calculated (volume of stem wood, total aboveground biomass, etc.) directly for each tree by the given equation is also included.

TPS contains 3 core modules: ``tps_Tree`` (for individual trees- all years of the tree's history are shown at once), ``tps_Stand`` (for stands and plots), and ``tps_NPP`` (for differences between stands over time). ``tps_cli`` is a command line interface for using the appropriate module.  Within each ``tps`` program, reliance on a core data structure is consistent. This structure is basically:

.. code-block:: python

    STAND ID :
      {YEARS :
        {SPECIES :
          {PLOTS :
            {[raw data]}
          }
        }
      }



This structure helps to organize the inputs in such a way that they can be easily iterated across to summarize new outputs. Beyond this description, this documentation has been auto-generated from these modules using the Sphinx Autodoc package. Documentation is also included for two modules for parameterizing the computations, ``biomass_basis`` and ``poptree_basis``. ``biomass_basis`` contains the rules for parsing the biomass computation equations (found in table TP00110) and generating functions that take DBH and produce the outputs needed; ``poptree_basis`` contains the database connectors and a parameter object, ``Capture``, which contains the information about the stands, plots, and study protocols (detail plot or not, mortality survey or not, etc.) that is needed in the tps modules. When executing a script to process a number of trees or stands, the ``Capture`` object needs to only be created once, greatly reducing the amount of database queries that might otherwise occur.

.. note:: For the equation form of each of the processing equations, see the ``biomass_basis`` section below.

.. note:: All treeid's, plots, and stands are specified programmatically in lowercase and as strings. Output to a file place them in uppercase. In debugging, checking the case to lowercase will be useful. The proper way to do this in Python is to append ``.lower()`` to the end of any string you suspect might be coming in as an uppercase.

---------------------------
A note for future MUNA work
---------------------------

Note that for the future processing of a site like MUNA or MUN2, you could re-use some of the connection information discussed below and the equation getters and Stand formation. However, you'd want to write a specialfunction to condense the biomass over the species specific areas. See the documentation below for the Stand function ``compute_biomass`` as an example to start from.

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


It is imperative that the `keys` on the left-side of the configuration file match the keys in the `pymssql` driver so that the connection will work. I.e. you must call the server as `server` and the password as `password`, not as `s` and `pw` or some other nonsense.

SQL queries are in ``qf_2.yaml``. This file is included with this program, and should also be located in the base directory with ``poptree_basis``. You can re-configure or add queries there so that the changes propogate throughout the modules. This is done by creating an object called ``YamlConn()`` with ``poptree_basis`` which is responsible for managing your connections and queries. If you want to try out a query, you can use ``YamlConn()`` to generate a cursor to the database, like so:

.. code-block:: python

    _, cur = YamlConn().sql_connect()
    sql= "select top 1 * from fsdbdata.dbo.tp00101"
    cur.execute(sql)
    print([row for row in sql])


In the command line interface, ``tps_cli``, commands can be issued to gather a specific tree, stand, set of trees, etc. See documentation in the ``README.rst`` file on `GitHub <https://github.com/dataRonin/ptree>`_.

.. automodule:: poptree_basis
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

Biomass Equations:
------------------

``biomass_basis.py`` uses the information in TP00110 to compute the Biomass ( Mg and Mg/Ha ), Jenkins Biomass ( Mg and Mg/Ha ), Basal Area ( m\ :sup:`2` ), Volume ( m\ :sup:`3` ). Jenkins' biomass is from Jenkins' 2003 `paper <http://www.fs.fed.us/ne/durham/4104/papers/Heathbiomass_eqns.pdf>`_. (Wood density is assigned by ``biomass_basis`` but no computation is involved apart from using it to switch between volume and biomass when needed. Proxy forms and components computed are also pulled from the database in this module.

.. automodule:: biomass_basis
    :members:
    :undoc-members:
    :inherited-members:
    :show-inheritance:

Individual Trees:
-----------------

``tps_Tree.py`` contains classes and functions for computing the attributes of individual trees. Each individual tree as defined in TP00101 is an instance of a class of ``Tree``. For example, ``NCNA000300005`` is one Tree, even if it alive for 5 remeasurements. All the remeasurements taken on one individual tree are encapsulated into a single instance of Tree for that individual, and can be accessed using the property of ``Tree.state``. If desired, checks on the state of a tree are generated. These are accessed through the QC portion of the interface. The equations used on the tree are foind in ``Tree.eqns``. They are in ``lambda`` form; to access them, you'll need to specify a dbh.

.. automodule:: tps_Tree
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

Stands:
-------
``tps_Stand.py`` contains classes and functions for computing the static attributes on the stand and plot scale. Each stand is defined as all the plots during a given re-measurement year. Both plot and stand attributes are computed on a per-hectare basis. Some stands contain ``detail plots`` with small trees representative of the stand as a whole. Plots sometimes have additional ``meaning`` we want to know beyond that of the stand. In all cases, we compute plot ``on the way`` to getting stand, so it's easy for us to include it in the output as well. Additions on stands are rolled to the prior remeasurement. Mortalities on stands are rolled to the next remeasurement. DBH's from the last known good DBH are assigned to `mort-ed` or missing trees. Stands can also be used for computing the individual trees they contain. When a set of individual trees are computed at the stand scale, the individuals on additions plots are rolled back in time to the previous remeasurement and those on mortality plots are rolled forward in time to the next remeasurement. Any mortality measurements that happen after the final re-measurement will not be included.

.. note:: Sometimes on missing trees, the time that has passed since last known good measurement and now can be in excess of 20 years. Since a tree is not considered dead until it is morted, these trees may affect your output unexpectedly.

.. automodule:: tps_Stand
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

NPP:
----
``tps_NPP.py`` contains classes and functions for computing the dynamic attributes on the stand and plot scale. Each stand is defined as all the plots during a given re-measurement year. Deltas are defined as the difference between remeasurement years, where mortalities are moved "up" to subsequent remeasurements and additions are moved "down" to early remeasurements. Both plot and stand attributes are computed on a per-hectare basis. NPP is computed on an annual basis. The rest of the details regarding the static stand and plot attributes apply to the dynamic attributes as well. There is no such thing as NPP on individual trees. Trying to run that from the command line interface will result in error.

.. automodule:: tps_NPP
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

SAMPLE:
-------

``tps_Sample.py`` is a set of sample data you can test the program on. Run at the command line like:

.. code-block:: bash

    $ python3 tps_Sample.py

See ``README.rst`` for more details.

CLI:
----

``tps_cli.py`` is the command line interface. Please see ``README.rst`` for how to use this interface.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
