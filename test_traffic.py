#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
# =============================================================================
# Time-stamp: <Fre 2017-08-25 13:45 juergen>
# File      : test_traffic.py 
# Creation  : 08 Oct 2015
#
# Copyright (c) 2015 Jürgen Hackl <hackl@ibi.baug.ethz.ch>
#               http://www.ibi.ethz.ch
# $Id$ 
#
# Description : Test Traffic Simulation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 
# =============================================================================

import networkx as nx
import numpy as np
from pytras.initialize import *

## Traffic Assignment with Frank Wolf algorithm ##
# from pytras.fw import TrafficAssignment

## Traffic Assignment with Method of Successive Averages algorithm ##
from pytras.msa import TrafficAssignment

import timeit

if __name__ == '__main__':
    print('***** start *****')
    start = timeit.default_timer()

    ### Initialization of the graphs ###

    # road graph
    road_graph = read_shp('./data/roads.shp')

    # od graph (without external od matrix)
    od_graph = create_od_graph('./data/centroids.shp')

    # load connections from od nodes to road network
    con_edges = read_shp('./data/connections.shp')

    # create network for traffic model
    graph = create_network_graph(road_graph,od_graph,con_edges)

    ## Traffic Model ##

    # load given od matix
    od_matrix = np.genfromtxt('./data/od.csv', delimiter=',')

    ### REMARK ###
    # Final flow results has to be multiplied wit 0.46
    # for a hourly analysis and with 10.9 for a daily analysis !!!

    start_run = timeit.default_timer()
    # set up traffic model
    traffic = TrafficAssignment(graph,od_graph,od_matrix)

    # run traffic simulation
    traffic.run()

    # # get the new graph of roads
    # graph_result = traffic.get_graph()
    end_run = timeit.default_timer()
    # # traffic.print_results()

    # ### writing output to shp ###
    # #save_shp(graph_result,'./results/test')
    # # create mapping from od nodes to points in the plan
    # mapping = {node:od_graph.node[node]['coordinates'] for node in od_graph.nodes()}

    # # rename od nodes to local point coordinates
    # graph_result = nx.relabel_nodes(graph_result,mapping,copy=False)

    # # write output file
    # write_shp(graph_result,'./results/','traffic_test')

    print(sum(traffic.get_traveltime()))
    print(sum(traffic.get_flow()))
    print(sum(traffic.get_car_hours()))
    print(sum(traffic.get_car_distances()))
    stop = timeit.default_timer()
    print('run time: ' + str(end_run - start_run))
    print('total time: ' + str(stop - start))
    print('****** end ******')






# =============================================================================
# eof
#
# Local Variables: 
# mode: python
# mode: linum
# End: 
