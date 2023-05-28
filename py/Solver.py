# Functions to run solver, produce outputs, adjust route, similarity analysis
# Notebook reference for implementation --> DP_analytics_pipeline_gOR_update.ipynb


import os
import pandas as pd
import numpy as np
import re
import collections
import pickle
from ast import literal_eval
import random
import scipy
import math
# from concorde_class import Concorde
import datetime
import subprocess
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2


# 1
# arrange sequence of tour

def arrange_tour(solver_tour, start_end_points):

    #Get the start and end point of the specific district of the instance
    start_PP, end_PP = start_end_points 
    arranged_tour = 0

    #FUNCTION TO REARRANGE THE LIST WITH CASE OF SAME START AND END POSTPOINT
    def rearrange_list(numbers, specific_value):
        # Find the index of the specific value in the list
        index = numbers.index(specific_value)
        
        # Check if the chosen element is repeated twice consecutively
        if numbers[index] == numbers[index + 1]:
            # Split the list into two parts based on the index
            part1 = numbers[:index]
            part2 = numbers[index + 1:]
            
            # Rearrange the list by concatenating the parts and adding the specific value at the beginning and end
            rearranged_list = part2 + part1 + [specific_value]
        else:
            # Split the list into two parts based on the index
            part1 = numbers[:index]
            part2 = numbers[index:]
            
            # Rearrange the list by concatenating the parts in reverse order
            rearranged_list = part2 + part1
        
        return rearranged_list
    
    
    #FUNCTION TO REARRANGE THE LIST WITH CASE OF DIFFERENT START AND END POSTPOINT
    def rearrange_circular_tour(tour, start_point, end_point):
    # Find the index of the start point in the tour list
        start_index = tour.index(start_point)
            
        # Find the index of the end point in the tour list
        end_index = tour.index(end_point)
                
        # Check if the start and end points are already at the first and last positions
        if start_index == 0 and end_index == len(tour) - 1:
            return tour
                
        # Split the tour list into two parts based on the start and end indices
        if start_index < end_index:
            part1 = tour[0:start_index + 1]
            part1.reverse()

            part2 = tour[start_index + 1:]
            part2.reverse()
                
        else:
            part1 = tour[start_index:] + tour[:end_index+1]
            part2 = tour[end_index+1:start_index]
                
        # Rearrange the tour list by concatenating the parts
        rearranged_tour = part1 + part2
        
        return rearranged_tour
    


    #Case of start and end point equal
    if start_PP == end_PP:
        #If the start and end point are already in correct positions return list as it is                                                                              
        if start_PP == solver_tour[0] and end_PP == solver_tour[len(solver_tour)-1]:                    
            arranged_tour = solver_tour
        else: 
            #Check if start or end point (doesn't matter they have the same value) appears less than two times on the list
            if list.count(solver_tour, start_PP) < 2:
                #If if is not repeated. Check if at least start_point is in first_position.                                                   
                if start_PP == solver_tour[0]: 
                    #If start_point is in first position just append end point at the end of list.                                                         
                    arranged_tour = solver_tour + [end_PP]
                else: 
                    #Rearrange the tour first with start_PP at the beginning of the list before appending end_PP
                    arranged_tour = rearrange_list(solver_tour, start_PP)
                    arranged_tour = arranged_tour + [end_PP]               
            else: 
                #Rearrange the tour in the correct order
                arranged_tour = rearrange_list(solver_tour, start_PP)
    #Case of start and end point different
    else:
       arranged_tour = rearrange_circular_tour(tour = solver_tour, start_point = start_PP, end_point = end_PP)
    
    return arranged_tour

# 2
#FUNCTION TO GET SUBSET OF A COMPLETE TOUR AND ITS LENGTH KEEPING SEQUENCE BASED ON INSTANCES VOLUMES

#INPUTS:    Complete Tour (DP or Concord), Complete Tour info (DP or Concord), 
#           Distance Matrix for the instance (generated from instance generation function), Mapping of PostPoints Needed (Dictionary obtained from instance generation function)
#OUTPUTS:   Tour Sequence Fixed, Tour Length, Difference between New Tour and Complete Tour



def new_tour_sequence_fixed(complete_tour, dm_instance, mapping_pp_needed):
    #get the list of only the Postpoint needed for the specific instance
    list_pp_needed = list(mapping_pp_needed.values())

    #Keep from complete_tour only the needed PostPoints according to the list of PostPoints needed mantaining sequence
    tour_seq_fixed = [x for x in complete_tour if x in list_pp_needed]

    #Generate a dataframe from the distance matrix with the correct row-column combination based on PostPoints required
    df_dm_instance = pd.DataFrame(dm_instance)
    df_dm_instance = (df_dm_instance.rename(columns= mapping_pp_needed)).rename(index = mapping_pp_needed)

    #FUNCTION to compute length of new tour (Adapting using logic of function already created for default_route calculation: get_tour_length())
    
    def get_seq_tour_length(sequence_list, distance_df):
        tour_length = 0 
        for i in range(len(sequence_list)-1):
            # Specify the specific values for row and column in the dataframe
            PostPoint_predecesor = sequence_list[i]
            PostPoint_succesor = sequence_list[i+1]

            # Get the distance value needed based on the Post Point combination or raise error
            try:
                distance_value = distance_df[PostPoint_predecesor][PostPoint_succesor]
            except: 
                print('ERROR: No distance for PostPoint combination')

            # Aggreate sum value until end of loop to compute total tour length
            tour_length += distance_value
            
        return round(tour_length,2)
    
    #Calculate tour length of new tour which skips PostPoints
    tour_seq_fixed_length = get_seq_tour_length(tour_seq_fixed, df_dm_instance)
    

    return tour_seq_fixed, tour_seq_fixed_length

# 3
# route similarity

def find_similarity_route(Tour1, Tour2):
    predecessors1 = {Tour1[i]: Tour1[i-1] for i in range(1, len(Tour1))}
    predecessors2 = {Tour2[i]: Tour2[i-1] for i in range(1, len(Tour2))}
    num_changed_predecessors = 0

    for node, pred2 in predecessors2.items():
        pred1 = predecessors1[node]
        if pred1 != pred2:
            num_changed_predecessors += 1
    percent_change = num_changed_predecessors / (len(Tour1)-1) * 100
    sim_pct = 100 - percent_change

    return num_changed_predecessors, sim_pct

# 4
# heuristic google OR algo

# !pip install ortools

class TSP:
    def __init__(self, distance_matrix):
        #read distance matrix --> list
        self.dist_mat = distance_matrix
        self.dist_mat = self.round_up(self.dist_mat)
        # Create data model
        self.data = self.create_data_model()
        # Create routing index manager
        self.manager = pywrapcp.RoutingIndexManager(len(self.data['distance_matrix']),
                                            self.data['num_vehicles'], self.data['depot'])
        # Create Routing Model
        self.routing = pywrapcp.RoutingModel(self.manager)
        # Define cost of each arc
        self.transit_callback_index = self.routing.RegisterTransitCallback(self.distance_callback)
        self.routing.SetArcCostEvaluatorOfAllVehicles(self.transit_callback_index)
    
    def round_up(self , lst):
        '''
        input : list of lists having non integral values
        output : list of lists having integral values.
        Function to round up numbers and return as integers
        '''
        rounded_lst = []
        for inner_lst in lst:
            rounded_inner_lst = []
            for num in inner_lst:
                rounded_num = int(round(num))
                rounded_inner_lst.append(rounded_num)
            rounded_lst.append(rounded_inner_lst)
        return rounded_lst        


    def create_data_model(self):
        # Stores the data for the problem
        data = {}
        data['distance_matrix'] = self.dist_mat 
        data['num_vehicles'] = 1
        data['depot'] = 0
        return data

    def distance_callback(self, from_index, to_index):
        # Returns the distance between the two nodes
        from_node = self.manager.IndexToNode(from_index)
        to_node = self.manager.IndexToNode(to_index)
        return self.data['distance_matrix'][from_node][to_node]

    def solve(self):
        # Setting first solution heuristic
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        # Solve the problem
        solution = self.routing.SolveWithParameters(search_parameters)
        if solution:
            # Get the route as an array
            route = []
            index = self.routing.Start(0)
            while not self.routing.IsEnd(index):
                node = self.manager.IndexToNode(index)
                route.append(node)
                index = solution.Value(self.routing.NextVar(index))
            # Get the objective value
            obj_value = solution.ObjectiveValue()
            # route = self.map_nodes(route)
            return route, obj_value

# 5
def map_actual_route(route, mapping):
  tour_mapped = [mapping[a] for a in route]
  return tour_mapped

# 6
# pyconcorde prerequisites and function

# %pip install git+https://github.com/jvkersch/pyconcorde

# # install tweak file
# %cp '/content/drive/Shareddrives/Private Unlimited Drive #1/DDS/Analytics Project/Concorde/concorde_class.py' '/content'
# %cp '/content/drive/Shareddrives/Private Unlimited Drive #1/DDS/Analytics Project/Concorde/test.py' '/content'
# %cp '/content/drive/Shareddrives/Private Unlimited Drive #1/DDS/Analytics Project/Concorde/concorde_to_replace/tsp.py' '/usr/local/lib/python3.10/dist-packages/concorde'
# %cp '/content/drive/Shareddrives/Private Unlimited Drive #1/DDS/Analytics Project/Concorde/concorde_to_replace/util.py' '/usr/local/lib/python3.10/dist-packages/concorde'

# exact solution with concord

# def concord_solver(distance_matrix, mapping):
#   concorde = Concorde()
#   concorde_sol = concorde.run_ProbATSP(distance_matrix)
#   tour_mapped = [mapping[a] for a in concorde.route]

#   return tour_mapped, concorde.optimal_value