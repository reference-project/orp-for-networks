#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
# =============================================================================
# Time-stamp: <Fre 2017-08-25 14:07 juergen>
# File      : main.py 
# Creation  : 11 Mar 2016
#
# Copyright (c) 2016 Jürgen Hackl <hackl@ibi.baug.ethz.ch>
#               http://www.ibi.ethz.ch
# $Id$ 
#
# Description : main file
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
import random
import ast
import timeit

from pytras.initialize import *
from simanneal import Annealer
from joblib import Parallel, delayed
from util import *

from damagemodel import DamageModel
from restorationmodel import RestorationModel

## Traffic Assignment with Frank Wolf algorithm ##
# from pytras.fw import TrafficAssignment

## Traffic Assignment with Method of Successive Averages algorithm ##
from pytras.msa import TrafficAssignment


class Engine(object):
    """ Simulation engine
    """

    def __init__(self,output_directory = './'):
        self.capacity_losses = {'Bridge':{0:0, 1:.5, 2:1, 3:1},'Road':{0:0, 1:.7, 2:1, 3:1},'Tunnel':{0:0}}

        # TODO: Load data from csv file
        self.restoration_types = [0,1,2]

        self.restoration_constraint = False
        self.output_directory = output_directory

    def initialize_network(self):
        self.road_graph = read_shp('./data/roads.shp')
        self.od_graph = create_od_graph('./data/centroids.shp')
        self.con_edges = read_shp('./data/connections.shp')
        self.od_matrix = np.genfromtxt('./data/od.csv', delimiter=',')

        self.graph = create_network_graph(self.road_graph,self.od_graph,self.con_edges)
        pass

    def initialize_damage(self):
        self.damage = DamageModel(self.graph,self.capacity_losses)
        self.damage.run()
        self.graph_damaged = self.damage.get_graph()
        self.damage_dict = self.damage.get_damage_dict(directed=False)
        #self.damage_dict = self.damage.get_damage_dict(directed=True)
        pass

    def run_restoration_model(self,sequence=None):
        self.restoration = RestorationModel(self.graph_damaged)
        self.restoration.run(sequence)
        self.restoration_graphs = self.restoration.get_restoration_graphs()
        self.restoration_times = self.restoration.get_restoration_times()
        self.restoration_costs = self.restoration.get_restoration_costs()
        pass

    def run_traffic_model(self,graph,od_graph):
        # set up traffic model
        self.traffic = TrafficAssignment(graph,od_graph,self.od_matrix)
        # run traffic simulation
        self.traffic.run()
        t_k = sum(self.traffic.get_traveltime())
        flow = sum(self.traffic.get_flow())
        hours = sum(self.traffic.get_car_hours())
        distances = sum(self.traffic.get_car_distances())
        lost_trips = sum(self.traffic.get_lost_trips().values())
        return t_k, flow, hours, distances, lost_trips

    def initialize_state(self):
        init_edges = list(self.damage_dict.keys())
        random.shuffle(init_edges)

        init_state = []

        for edge in init_edges:
            if self.restoration_constraint:
                init_state.append((edge,0))
            else:
                init_state.append((edge,random.choice(self.restoration_types)))
        return init_state

    def load_state(self,filename):
        with open(filename, 'r') as f:
            state = ast.literal_eval(f.read())
        return state

    def load_damage(self,filename):
        with open(filename, 'r') as f:
            damaged = ast.literal_eval(f.read())
        return damaged

    def run(self):
        self.initialize_network()
        self.initialize_damage()
        init_state = self.initialize_state()

        no_damage = self.run_traffic_model(self.graph,self.od_graph)
        initial_damage= self.run_traffic_model(self.graph_damaged.copy(),self.od_graph.copy())

        damage = [no_damage,initial_damage]

        optimize = SimAnnealer(init_state,self.graph,self.od_graph,self.od_matrix,self.graph_damaged,damage,self.output_directory)

        optimize.copy_strategy = "slice"

        state, e = optimize.anneal()

        print("consequences: %i" % e)

        self.restoration_results = RestorationModel(self.graph_damaged)
        # (object,schedule time,needed time,#resources,intervention type, assignd resource)
        sequence_formated = self.restoration_results.format(state)

        with open(self.output_directory+'state.txt','w') as f:
            f.write(str(state))

        with open(self.output_directory+'state_formated.txt','w') as f:
            f.write(str(sequence_formated))
        pass

def get_delta(t_0,t_1):
    delta = [t_1[i]-t_0[i] for i in range(len(t_0))]
    return delta

class SimAnnealer(Annealer):

    def __init__(self, state,graph,od_graph,od_matrix,graph_damaged,damage,fdir):
        self.graph = graph
        self.od_graph = od_graph
        self.od_matrix = od_matrix
        self.graph_damaged = graph_damaged
        self.no_damage = damage[0]
        self.initial_damage = damage[1]
        self.fdir = fdir

        # Model parameters for indirect costs
        self.mu = np.array([0.94,0.06])
        self.xi = np.array([23.02,130.96])
        self.F_w = np.array([6.7,33])/100
        self.nu = 1.88
        self.rho = np.array([14.39,32.54])/100
        self.upsilon = 83.27 * 8
        self.day_factor = 9

        with open(self.fdir+'energy.txt','w') as f:
                f.write('Energy')

        self.restoration_types = [0,1,2]
        super(SimAnnealer, self).__init__(state,fdir=self.fdir)  # important!

    def move(self):
        """Swaps two object in the restoration schedual."""
        a = random.randint(0, len(self.state) - 1)
        b = random.randint(0, len(self.state) - 1)
        self.state[a], self.state[b] = self.state[b], self.state[a]

        # change type of restoration for one state
        c = random.choice(self.restoration_types)
        self.state[a] = (self.state[a][0],c)

    def energy(self):
        """Calculates the costs of the restoration."""
        e = 0

        restoration = RestorationModel(self.graph_damaged)
        restoration.run(self.state)
        restoration_graphs = restoration.get_restoration_graphs()
        restoration_times = restoration.get_restoration_times()
        restoration_costs = restoration.get_restoration_costs()

        damaged = []
        damaged.append(get_delta(self.no_damage,self.initial_damage))

        sim_results = Parallel(n_jobs=4)(delayed(parallel_model)(graph,self.od_graph,self.od_matrix) for graph in restoration_graphs[:-1])
        for values in sim_results:
            damaged.append(get_delta(self.no_damage,values))

        for idx,values in enumerate(damaged):
            dt = restoration_times[idx] if idx == 0 else restoration_times[idx]-restoration_times[idx-1]
            e += sum(restoration_costs[idx]) + dt * (self.day_factor * values[2] * np.sum(self.mu*self.xi)  + values[3] * np.sum(self.mu * (self.nu * self.F_w + self.rho)) + values[4] * self.upsilon)
        with open(self.fdir+'energy.csv','a') as f:
            f.write('\n'+str(e))

        return e


def parallel_model(graph,od_graph,od_matrix):
    g = graph.copy()
    od_g = od_graph.copy()
    traffic = TrafficAssignment(g,od_g,od_matrix)
    traffic.run()
    t_k = sum(traffic.get_traveltime())
    flow = sum(traffic.get_flow())
    hours = sum(traffic.get_car_hours())
    distances = sum(traffic.get_car_distances())
    lost_trips = sum(traffic.get_lost_trips().values())
    return t_k, flow, hours, distances, lost_trips

if __name__ == '__main__':
    print('***** start *****')
    start = timeit.default_timer()
    model = Engine('./results/')
    model.run()
    stop = timeit.default_timer()
    print('time: ' + str(stop - start))
    print('****** end ******')

# =============================================================================
# eof
#
# Local Variables: 
# mode: python
# mode: linum
# End: 

 
