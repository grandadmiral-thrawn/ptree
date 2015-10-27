********************************************
TPS: Tree, Plot, Stand - Biomass Aggregation
********************************************

TPS is a set of Python 3 modules for the aggregation of trees, plots, and stands from the USFS reference stands data maintained by the Corvallis Forest Science Lab.  


.. contents::
    :local:
    :depth: 1
    :backlinks: none


=============
Main Features
=============

* tps_Tree <- individual trees
* tps_Plot <- plots on stands
* tps_Stand <- stands
* tps_NPP <- net primary productivity for plots and stands
* tps_CLI <- command line interface
* tps_Sample <- tests
* SQL queries and configs in yaml files for interoperability!
* lots of docs!

============
Installation
============

Set up Python 3 on your computer, and then run the darn thing!
Best to start with tps_Sample, which will run a series of test trees, plots, and stands on a known dataset (that it will access from the server to test your connection) and output the results. To run it do:

.. code-block:: bash

    $ python3 tps_Sample.py

Assuming this goes well, please read the docs! You'll be running the remainder of your analyses out of the command line interface for now, but there are a lot of options.

-------------------
Development version
-------------------

The **latest development version** can be installed directly from GitHub. Use this repository. Note that when Fox changes contracts, maintenance will be sporadic at best.

==============
Output Options
==============

.. note: This section is in progress right now.


By default, outputs for a computational analysis will be stored in ``target`` + ``_basic.csv`` and outputs for a check analysis will be stored in ``target`` + ``_checks.csv``. ``target`` in these cases refers to the object you are analyzing. 

You can control the ``target`` to be a tree, stand, plot, or study.:

=================   =====================================================
``ncna000100005``   Only addresses the tree NCNA000100005.
``ncna``            Addresses all trees on stand NCNA or NCNA the stand as a whole.
``hsgy``            Addresses all stands in the HSGY study.
``[ncna, ch11]`     Addresses all trees on stand NCNA and on stand CH11 or the stands NCNA and CH11 as wholes.
=================   =====================================================


More about CLI.

==========  ==================
Character   Stands for
==========  ==================
``t``       tree.
``s``       stand.
``w``       stand by tree.
``p``       study.
``q``       quality control.
``a``       all.
``n``       net primary productivity
==========  ==================


