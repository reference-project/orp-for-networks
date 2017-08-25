#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
# =============================================================================
# File      : util.py 
# Creation  : 26 Feb 2016
# Time-stamp: <Fre 2016-07-22 14:18 juergen>
#
# Copyright (c) 2016 Jürgen Hackl <hackl@ibi.baug.ethz.ch>
#               http://www.ibi.ethz.ch
# $Id$ 
#
# Description : Util
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
import collections
import copy
import numpy as np


def merge_dicts(dict_args):
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def sort_dic(d):
    l = []
    for k,v in d.items():
        l.append('_'.join(k.split("_")[:-1])+'_')
    c=collections.Counter(l)
    x = [i for i in c if c[i]>1]
    t = []
    for j in x:
        e = []
        for i in range(1,c[j]+1):
            e.append(j+str(i))
        t.append(e)

    return(t)

def get_edge_attribute(graph,edge,attribute):
    try:
        return graph[edge[0]][edge[1]][attribute]
    except: 
        return None

def set_edge_attribute(graph,edge,attribute,value):
    graph[edge[0]][edge[1]][attribute] = value
    pass

def remove_duplicates(seq):
    """removes duplicates from a list"""
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def get_small_indices(list,x):
    """return indices of the x smallest values of a list """
    max_value = max(list)
    l = copy.copy(list)
    idx_list = []
    for i in range(x):
        idx = l.index(min(l))
        idx_list.append(idx)
        l[idx] = l[idx] + max_value + 1
    return idx_list

def get_resources_array(resources_matrix,duration,resources):
    """return array which can be assignd to a restoration task"""
    resources_array = None
    for j in range(resources_matrix.shape[1]):
        if np.sum(resources_matrix,axis=0)[j] >= resources:
            i_idx = []
            for i in range(resources_matrix.shape[0]):
                if resources_matrix[i,j] == 1:
                    i_idx.append(i)

            i_ok = []
            for idx in i_idx:
                if np.sum(resources_matrix[idx,j:j+duration]) >= duration:
                    i_ok.append(idx)

            if len(i_ok) >= resources:
                i_ok.sort()
                resources_array = (i_ok[0:resources],j)
                break
    return resources_array



# =============================================================================
# eof
#
# Local Variables: 
# mode: python
# End: 

 
