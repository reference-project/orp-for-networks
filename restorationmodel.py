#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
# =============================================================================
# Time-stamp: <Fre 2017-08-25 14:30 juergen>
# File      : restorationmodel.py 
# Creation  : 11 Mar 2016
#
# Copyright (c) 2016 Jürgen Hackl <hackl@ibi.baug.ethz.ch>
#               http://www.ibi.ethz.ch
# $Id$ 
#
# Description : Restoration Model
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

from util import *
import random
import numpy as np

import copy
from itertools import groupby
from operator import itemgetter

class RestorationModel(object):
    """Restoration model for the network
    """

    def __init__(self, graph,filepath=None):
        self.filepath = filepath
        self.output_costs = []
        self.graph = graph
        self.damage_dict = {}

        self.interventions = np.loadtxt('./data/interventions.txt')
        self.interventions = self.interventions.reshape((2,2,3,6))

        self.working_hours = 8
        self.duration_subdivision = 2
        # working day / duration_subdivision
        # smallest time unit in relation to one working day

        self.max_available_resources = 3

        # TODO make this nicer
        self.resources_constrains = [[],[],[]]
        # self.resources_constrains = [[],[(0,7)],[(20,29)]]

        # TODO: Load data from csv file
        self.object_types = {'Bridge':0,'Road':1}
        self.object_width = {'A_Klass':10,'1_Klass':6,'2_Klass':4,'3_Klass':2.8,'Q_Klass':4}

    def damaged_objects(self):
        self.G = self.graph.copy()
        for edge in self.G.edges():
            if get_edge_attribute(self.G,edge,'damage') > 0:
                self.damage_dict[edge] = [get_edge_attribute(self.G,edge,'name'),get_edge_attribute(self.G,edge,'oneway')]
        pass

    def get_enhanced_sequence(self):
        graph = self.graph.copy()
        sequence = self.sequence

        # add additional information to sequence
        # (object,duration,resourses,intervention)
        sequence_list = []

        for values in sequence:
            edge = values[0]
            object = get_edge_attribute(self.graph,edge,'object')
            object_type = self.object_types[object]
            intervention_type = values[1]
            # TODO: add also a condition state 0 and remove -1
            condition_state = get_edge_attribute(self.graph,edge,'damage')-1
            intervention_duration_per_unit = self.interventions[object_type,condition_state,intervention_type,1]
            resources = int(self.interventions[object_type,condition_state,intervention_type,2])


            if object == 'Road':
                edge_lenght = get_edge_attribute(self.graph,edge,'length')
                edge_type = get_edge_attribute(self.graph,edge,'type')
                intervention_duration = max(int(np.round((edge_lenght*self.object_width[edge_type]*intervention_duration_per_unit / self.working_hours)*self.duration_subdivision)),1)

            else:
                intervention_duration = max(int(np.round((intervention_duration_per_unit / self.working_hours)*self.duration_subdivision)),1)

            sequence_list.append((edge,intervention_duration,resources,intervention_type))

        # calculate maximum time needed
        t_max = sum([value[1] for value in sequence_list])

        # matrix for the results
        sequence_matrix = [[None] * t_max for i in range(self.max_available_resources)]

        # initial resources matrix
        resources_matrix = np.ones((self.max_available_resources,t_max))

        # add constraints to the matrix
        for i in range(self.max_available_resources):
            for j in self.resources_constrains[i]:
                for k in range(j[0],j[1]+1):
                    resources_matrix[i,k] = 0

        # assign task to sequence considering constrains
        for task in sequence_list:
            resources_array = get_resources_array(resources_matrix,task[1],task[2])
            for i in resources_array[0]:
                j = resources_array[1]
                resources_matrix[i,j:j+task[1]] = 0
                for k in range(j,j+task[1]):
                    sequence_matrix[i][k] = task[0]

        # grupe list by tasks
        sequence_grouped = [[list(g) for k, g in groupby(l)] for l in sequence_matrix]

        # reduces list to label and duration
        sequence_reduced = []
        for i,k in enumerate(sequence_grouped):
            n = 0
            for j in k:
                n += len(j)
                sequence_reduced.append((j[0],n,i))

        # remove None values
        sequence_reduced = remove_duplicates([x for x in sequence_reduced if x[0] != None])

        # add information to sequence (object,schedule time,needed time,#resources,intervention type, assignd resource)
        sequence_enhanced = []
        for v in sequence_list:
            for w in sequence_reduced:
                if v[0] == w[0]:
                    sequence_enhanced.append((v[0],w[1],v[1],v[2],v[3],w[2]))

        # sort in decendent order
        sequence_enhanced.sort(key=itemgetter(1))

        # groupe interventions ending in the same period
        sequence_enhanced = [list(group) for key, group in groupby(sequence_enhanced, itemgetter(1))]

        return(sequence_enhanced)

    def repair(self):
        sequence = self.sequence_enhanced
        graph = self.graph.copy()
        graph_sequence = []
        cost_sequence = []
        schedule = []

        for tasks in sequence:
            graphs = []
            costs = []
            time = 0
            res = True
            for task in tasks:
                edge = task[0]
                time_scheduled = task[1] / self.duration_subdivision
                duration = task[2] / self.duration_subdivision
                resources_needed = task[3]
                intervention_type = task[4]
                assignd_resource = task[5]

                object = get_edge_attribute(self.graph,edge,'object')
                object_type = self.object_types[object]

                # TODO: add also a condition state 0 and remove -1
                condition_state = get_edge_attribute(self.graph,edge,'damage')-1
                oneway = get_edge_attribute(self.graph,edge,'oneway')

                recovery = self.interventions[object_type,condition_state,intervention_type,0]
                # duration
                # resources_needed
                fix_costs = self.interventions[object_type,condition_state,intervention_type,3]
                variable_costs_per_unit = self.interventions[object_type,condition_state,intervention_type,4]
                resources_costs_per_unit = self.interventions[object_type,condition_state,intervention_type,5]
                if object == 'Road':
                    edge_lenght = get_edge_attribute(self.graph,edge,'length')
                    edge_type = get_edge_attribute(self.graph,edge,'type')

                    variable_costs = variable_costs_per_unit * edge_lenght * self.object_width[edge_type]
                    resources_costs = resources_costs_per_unit * resources_needed * duration * self.working_hours

                else:
                    variable_costs = variable_costs_per_unit
                    resources_costs = resources_costs_per_unit * resources_needed * duration * self.working_hours

                self.output_costs.append([edge,fix_costs,variable_costs,resources_costs])

                capacity_i = get_edge_attribute(self.graph,edge,'capacity_i')
                capacity_d = get_edge_attribute(self.graph,edge,'capacity')
                capacity_n = np.round(capacity_d + (capacity_i - capacity_d) * recovery)

                set_edge_attribute(graph,edge,'capacity',capacity_n)

                if oneway == 0:
                    edge = (edge[1],edge[0])
                    capacity_i = get_edge_attribute(self.graph,edge,'capacity_i')
                    capacity_d = get_edge_attribute(self.graph,edge,'capacity')
                    capacity_n = np.round(capacity_d + (capacity_i - capacity_d) * recovery)

                    set_edge_attribute(graph,edge,'capacity',capacity_n)

                graphs.append(graph.copy())
                time = time_scheduled
                if resources_needed == 1:
                    costs.append((fix_costs,variable_costs,resources_costs))
                if resources_needed > 1 and res == True:
                    costs.append((fix_costs,variable_costs,resources_costs))
                    res = False

            graph_sequence.append(graphs[-1])
            C = []
            for i in range(3):
                C.append(sum(x[i] for x in costs))
            cost_sequence.append((C[0],C[1],C[2]))
            schedule.append(time)

        if self.filepath is not None:
            with open(self.filepath+'costs.txt','w') as f:
                f.write(str(self.output_costs))

        return schedule, cost_sequence, graph_sequence

    def format(self,sequence):
        self.sequence = sequence
        return self.get_enhanced_sequence()

    def run(self,sequence=None):
        if sequence==None:
            # TODO: fix this if statement
            self.damaged_objects()
            self.sequence = self.random_sequence()
        else:
            self.sequence = sequence
            self.sequence_enhanced = self.get_enhanced_sequence()

            self.times, self.costs, self.graphs = self.repair()
        pass

    def get_restoration_graphs(self):
        return self.graphs

    def get_restoration_times(self):
        return self.times

    def get_restoration_costs(self):
        return self.costs

    def get_damage_dict(self):
        return self.damage_dict

    def random_sequence(self):
        sequence = list(self.damage_dict.keys())
        random.shuffle(sequence)
        return sequence


# =============================================================================
# eof
#
# Local Variables: 
# mode: python
# mode: linum
# End: 

 
