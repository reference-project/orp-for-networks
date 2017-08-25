**********************************************************************************
Optimal Restoration Programs for Transportation Networks using Simulated Annealing
**********************************************************************************

:Date: August 2017
:Authors: Jürgen Hackl
:Contact: hackl.j@gmx.at
:Web site: http://github.com/hackl/orp-for-networks
:Documentation: http://hackl.github.io/orp-for-networks/
:Copyright: This document has been placed in the public domain.
:License: This program is released under the GNU General Public Licence.
:Version: 0.0.2


Note
----

   If you have any problems, found bugs in the code or have feature request
   comments or questions, please feel free to send a mail to `Jürgen Hackl`_.


.. _`Jürgen Hackl`: hackl.j@gmx.at



Abstract
========

Extreme events, such as earthquakes, floods, and landslides, may disrupt the service provided by transportation networks on a vast scale, as their occurrence is likely to cause multiple objects to fail simultaneously. The restoration program following an extreme event should restore service as much, and as fast, as possible. The estimation of risk due to natural hazards must take into consideration the resilience of the network which requires estimating the restoration program as accurate as possible. In this paper, a mathematical model and a simulated annealing algorithm are formulated to determine near-optimal restoration programs following the occurrence of hazard events. The objective function of the model is to minimize the costs, taking into consideration the direct costs of executing the physical interventions, and the indirect costs that are being incurred due to the inadequate service being provided by the network. The constraints of the model are annual and total budget constraints, annual and total resource constraints, and the specification of the number and type of interventions to be executed within a given time period. The model and algorithm are demonstrated by using them to determine the near-optimal restoration program for an example road network in Switzerland following the occurrence of an extreme flood event. The strengths and weaknesses of the model and algorithm are discussed, and an outlook for future work is given.

Note
----

   A proper documentation will be provide as soon I find some time to spare


Data
====

Due to data restriction only a dummy network is provided

Usage
=====

To run the optimization please use ::

  $ python3 main.py
