# Functions to generate distance matrix, instances, scenarios, from multiple data sources provided by DP
# Notebook reference for implementation --> DP_instances_defaulttour_update.ipynb
#                                           DP_analytics_district_complete_dm_update.ipynb



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
import datetime
import subprocess


# path for the 'Data' folder provided by DP, adjust path if needed
# global vars

dir_loc = '/content/drive/Shareddrives/Private Unlimited Drive #1/DDS/Analytics Project/AOP_DP_Analytics/Data'

path = '/content/drive/Shareddrives/Private Unlimited Drive #1/DDS/Analytics Project/AOP_DP_Analytics/'


# 1
# get start and end node for a district

def start_end_points(region_name, district):

    # get start and end node
    district_path = dir_loc + '/Instances/' + region_name + '/Districts/' + district + '.dat'
    rows_needed = [1]
    file_district = pd.read_csv(district_path, sep='\t', skiprows = lambda x : x not in rows_needed,
                                names=('dum_0', 'start_point', 'end_point', 'dum_1', 'dum_2', 'dum_3', 'dum_4', 'dum_5', 'dum_6')
                                )
    start_point = file_district['start_point'][0]
    end_point = file_district['end_point'][0]

    points = [start_point, end_point]

    return points

# 2
# generate original distance matrix and mapping for districts

def ori_generate_distance_matrix_map(region_name, save_loc):
      i = 1

      dir_region = save_loc + '/' + region_name + '_original'
      print(dir_region)
      if not os.path.exists(dir_region):
        os.mkdir(dir_region)
        print('dir_region doesnt exist')

      # dir_region_ori = dir_region + '/original'
      # print(dir_region_ori)
      # if not os.path.exists(dir_region):
      #   os.mkdir(dir_region)
      #   print('dir_ori doesnt exist')

      ori_dm_map_dict_region = {}
      # get distance file and dataframes
      distance_path = dir_loc + '/Instances/' + region_name + '/distances/'
      for filename in os.listdir(distance_path):
        ori_dm_map_dict_district = {}
        district_name = re.sub('.dat', '', filename)
        district_name = re.sub('distances_', '', district_name)

        district_distance = pd.read_csv(distance_path + filename,
                                    names=['pp_1', 'pp_2', 'dist']
                                    )
      
        distance_matrix_df = district_distance.pivot(index = 'pp_1', columns = 'pp_2', values = 'dist')

        # generate and revise start and end nodes
        points = start_end_points(region_name = region_name, district = district_name)
        distance_matrix_df[points[0]][points[1]] = 0
        distance_matrix_df[points[1]][points[0]] = 0
        ori_dm_map_dict_district['start_end_points'] = points


        # distance matrix
        distance_matrix_array = distance_matrix_df.to_numpy()
        distance_matrix_array = distance_matrix_array.tolist()
        ori_dm_map_dict_district['dm'] = distance_matrix_array
        pickle.dump(distance_matrix_array, open(dir_region + '/dm_' + "%s.p"%district_name, "wb"))

        # node mapping
        map_val = list(range(0, len(distance_matrix_df)))
        nodes = distance_matrix_df.index.values.tolist()
        mapping = dict(zip(map_val, nodes))
        ori_dm_map_dict_district['map'] = mapping
        pickle.dump(mapping, open(dir_region + '/map_' + "%s.p"%(district_name), "wb"))

        ori_dm_map_dict_region[district_name] = ori_dm_map_dict_district
        print(i, ':', district_name, ':', len(distance_matrix_array))
        i = i+1

      return ori_dm_map_dict_region

# 3
# create dataframes for a region everyday

def generate_region_volume(region_name):
  # path of folder
  dir_region_instances = dir_loc + '/Instances/' + region_name
  dir_region_volume = dir_loc + '/Volumes/'
  # dir_region_districts = dir_region_instances + '/Districts'

  # load post_object-to-route_pos_id and post_point-to-post_object files 
  po_file = pd.read_csv(dir_region_instances + '/post_order_id_mapping.dat', sep='\t', names=('PostObjectId', 'RoutePosID'))
  pp_file = pd.read_csv(dir_region_instances + '/post_point_information.dat', sep='\t', names=('PostPointId', 'PostObjectId'))

  # pp_file adjustment by splitting list of post object ids
  pp_file['PostObjectId'] = pp_file['PostObjectId'].apply(literal_eval)
  pp_file = pp_file.explode('PostObjectId', ignore_index=True)

  # complete  post object list-district mapping
  region_district_df = generate_region_district(region_name = region_name)
  region_district_df.rename(columns = {'PostObjectID' : 'PostObjectId'}, inplace = True)

  # list of volume file paths
  day_names = []
  vol_path_list = []
  vol_day_map = {}
  day_map = {'mo' : 'Monday',
             'di' : 'Tuesday',
             'mi' : 'Wednesday',
             'do' : 'Thursday',
             'fr' : 'Friday',
             'sa' : 'Saturday'}

  for filename in os.listdir(dir_region_volume):
    vol_path_list.append(dir_region_volume + filename)
    day = filename[-6:-4]
    vol_day_map[filename] = day_map[day]

  # store dataframes of a region, map with post object id
  region_vol_day_dict = {}
  for vol_path in vol_path_list:
    vol_df = pd.read_csv(vol_path, sep = ';')
    vol_df.rename(columns = {'BRIEFE' : 'LETTERS',
                             'PAKETE' : 'PACKAGES',
                             'SONSTIGE' : 'OTHERS',
                             'ROUTEPOS_ID' : 'RoutePosID'},
                  inplace = True)
    
    # combining files to a complete table for a region
    vol_po_df = pd.merge(po_file, vol_df, on = 'RoutePosID', how = 'left')
    vol_po_df = pd.merge(pp_file, vol_po_df, on='PostObjectId', how='right')
    vol_po_df = pd.merge(region_district_df, vol_po_df, on='PostObjectId', how='right')

    # store dataframes in dict
    day_key = vol_day_map[vol_path[-18:]]
    region_vol_day_dict[day_key] = vol_po_df
    
  return region_vol_day_dict

# 4
def generate_region_district(region_name):
  district_path = dir_region_instances = dir_loc + '/Instances/' + region_name + '/Districts'
  region_districts_list = []

  for filename in os.listdir(district_path):
    file_var = re.sub('.dat', '', filename)
    file_district = pd.read_csv(district_path + '/' + filename, sep='\t', skiprows = [0,1],
                                names=('PostObjectID', 'dum_1', 'dum_2', 'dum_3', 'dum_4', 'dum_5')
                                # usecols = [0]
                                )
    file_district['district'] = file_var
    region_districts_list.append(file_district)

  region_districts_df = pd.concat(region_districts_list, ignore_index = True)
  region_districts_df.drop(['dum_1', 'dum_2', 'dum_3', 'dum_4', 'dum_5'], axis = 1, inplace = True)
  
  return region_districts_df

# 5
# generate instances

def generate_instances(region_vol_day, scenario_type, scenario_method, scenario_number, growth_factor):
  # df = region_vol_day.copy() #.copy() used to avoid recopying on the original dataframe
  df = region_vol_day

  sce_letters = 'scenario_' + str(scenario_number) + '_letter'
  sce_packages = 'scenario_' + str(scenario_number) + '_package'
  sce_others = 'scenario_' + str(scenario_number) + '_others'

  df[sce_letters] = df['LETTERS'].apply(lambda x :scenario_type(pos_delivery = x, method = scenario_method, rate_pct = growth_factor ))
  df[sce_packages] = df['PACKAGES'].apply(lambda x :scenario_type(pos_delivery = x, method = scenario_method, rate_pct = growth_factor))
  df[sce_others] = df['OTHERS'].apply(lambda x :scenario_type(pos_delivery = x, method = scenario_method, rate_pct = growth_factor))

  sce_all = 'scenario_' + str(scenario_number) + '_all'
  df[sce_all] = df[sce_letters] + df[sce_packages] + df[sce_others]

  return df

# 6
# generate real instances based on poisson

def random_poisson_instances(pos_delivery, method, rate_pct):
  rate = rate_pct/100
  rng = np.random.default_rng()
  poisson_dist = rng.poisson(lam = pos_delivery * (1 + rate), size = 52)

  if method == 'random':
    return random.choice(poisson_dist)
  if method == 'mode':
    return scipy.stats.mode(poisson_dist, keepdims = True)[0][0]
  else:
    return 'only options : [random, mode]'
  
# 7
# generate distance matrix and mapping for a scenario

def generate_distance_matrix_map(region_name, df_day_district, points, sce_col, district):
      scenario = sce_col

      col_use = ['PostPointId']
      col_use.append(scenario)
      df_day_district_scenario = df_day_district[col_use]
      
      # removing nodes with zero demand
      df_day_district_scenario_filtered = df_day_district_scenario[df_day_district_scenario[scenario] != 0]
      pp_id_day_district_scenario = df_day_district_scenario_filtered['PostPointId'].unique().tolist()
      
      # add start and end node if not in node list yet
      for point in points:
        if point not in pp_id_day_district_scenario:
          pp_id_day_district_scenario.append(point)

      # get distance file and dataframes
      distance_path = dir_loc + '/Instances/' + region_name + '/distances'
      district_distance = pd.read_csv(distance_path + '/distances_' + district + '.dat',
                                  names=['pp_1', 'pp_2', 'dist']
                                  )
      # remove unused postpoints
      district_distance_filtered = district_distance[(district_distance['pp_1'].isin(pp_id_day_district_scenario)) & (district_distance['pp_2'].isin(pp_id_day_district_scenario))]
      distance_matrix_df = district_distance_filtered.pivot(index = 'pp_1', columns = 'pp_2', values = 'dist')

      # generate and revise start and end nodes
      points = start_end_points(region_name = region_name, district = district)
      distance_matrix_df[points[0]][points[1]] = 0
      distance_matrix_df[points[1]][points[0]] = 0

      # distance matrix
      distance_matrix_array = distance_matrix_df.to_numpy()
      distance_matrix_array = distance_matrix_array.tolist()

      # node mapping
      map_val = list(range(0, len(distance_matrix_df)))
      nodes = distance_matrix_df.index.values.tolist()
      mapping = dict(zip(map_val, nodes))

      return distance_matrix_array, mapping

# 8
def create_dm_map(region, data, save_loc, rate):
  i = 1
  dir_region = save_loc + '/' + region
  if not os.path.exists(dir_region):
    os.mkdir(dir_region)


  # filter by day
  result_day = {}
  for day in data.keys():
    df_day = data[day]

    # filter by district
    result_district = {}
    for district in df_day['district'].value_counts().index.tolist():
      df_day_district = df_day[df_day['district'] == district]

      scenario_list = df_day_district.columns.tolist()[7:]

      # get start and end node
      points = start_end_points(region_name = region, district = district)
      
      # filter by scenario
      result_mail_demand = {}
      for scenario in scenario_list:
        # get volume
        scenario_volume = df_day_district[scenario].sum()

        # dir of mail
        mail_names = ['letter', 'package', 'others', 'all']
        for mail in mail_names:
          if mail in scenario:
            mail_current = mail

        # dir of demand
        demand_types = ['low', 'medium', 'high']
        for demand in demand_types:
          if demand in scenario:
            demand_current = demand

        # generate mapping and distance matrix
        distance_matrix, mapping = generate_distance_matrix_map(region_name = region, df_day_district = df_day_district,
                                                                points = points, sce_col = scenario, district = district)
        distance_matrix_name = 'dm_' + region + '_' + day + '_' + district + '_' + scenario + '_' + str(rate)
        mapping_name = 'map_' + region + '_' + day + '_' + district + '_' + scenario + '_' + str(rate)
        pickle.dump(distance_matrix, open(dir_region + '/' + "%s.p"%distance_matrix_name, "wb"))
        pickle.dump(mapping, open(dir_region + '/' + "%s.p"%mapping_name, "wb"))

        # log update
        # print(i, ':', distance_matrix_name, ':', distance_matrix.shape)
        print(i, ':', distance_matrix_name, ':', len(distance_matrix))
        i = i+1

        result_end = {}
        result_end['dm'] = distance_matrix
        result_end['map'] = mapping
        result_end['start_end_points'] = points
        result_end['volume'] = scenario_volume
        
        mail_demand = mail_current + '_' + demand_current
        result_mail_demand[mail_demand] = result_end
      result_district[district] = result_mail_demand
    result_day[day] = result_district

  return result_day

# 9
def get_default_route(region, district_name):
    
    #Get directory path of district's assigned PostObjects
    district_po_path = os.path.join(path, 'Data', 'Instances', region, 'Districts', district_name + '.dat')

    #Get directory path of PostPoint-PostObject mapping for the region that district belongs to
    district_pp_po_mapping_path = os.path.join(path, 'Data', 'Instances', region, 'post_point_information' + '.dat')

    #Get directory path of distances between Post Points file fo the district
    district_pp_distances_path = os.path.join(path, 'Data', 'Instances', region, 'distances', 'distances_' + district_name + '.dat')

    #Generate the dataframe for the PostPoint distance combinations
    df_pp_district_distances = pd.read_csv(district_pp_distances_path, sep = ',', header = None, names = ['PostPoint1', 'PostPoint2','Distance'])


    #Generate the needed PostObjects dataframe in their assigned sequence. Also get start and end PostPoints as list
    df_district_po = pd.read_csv(district_po_path, sep = '\t', skiprows= 2, usecols=[0], header = None, names = ['PostObjectId'])

    df_start_end_pp = pd.read_csv(district_po_path, sep = '\t', skiprows= 1, nrows=1, usecols=[1,2], header = None, names = ['StartPostPoint','EndPostPoint'])


    #Get the needed PostPoint-PostObject dataframe for merging
    df_district_pp_po_mapping = pd.read_csv(district_pp_po_mapping_path, sep='\t', names=('PostPointId', 'PostObjectId'))
    df_district_pp_po_mapping['PostObjectId'] = df_district_pp_po_mapping['PostObjectId'].apply(literal_eval)
    df_district_pp_po_mapping = df_district_pp_po_mapping.explode('PostObjectId', ignore_index=True)

    #Create a dataframe of the PostPoint in Order Sequence by merging and preprocessing previous dataframes
    df_district_pp_sequence = merged_data = pd.merge(df_district_po, df_district_pp_po_mapping , on='PostObjectId', how = 'left').drop('PostObjectId', axis=1)

    #Save the value of the amount of PostObject ID Visited
    PO_touching_rate = len(df_district_pp_sequence)
    
    #get the values from start and end PostPoint separately
    start_point = df_start_end_pp.iloc[0,0]
    end_point = df_start_end_pp.iloc[0,1]

    #FUNCTION to Add start and end point on their respective initial and end position on the PostPoint dataframe. Check first if they exist on those positions.
    def add_start_end_point(point_1, point_2, df):
        #for start point
        if df.loc[0,'PostPointId'] == point_1:
            pass
        else: 
           new_row_start = pd.DataFrame([point_1], columns=df.columns)
           df = pd.concat([new_row_start, df], ignore_index=True) 
        #for end point
        if df.loc[len(df)-1,'PostPointId'] == point_2:
            pass
        else: 
            new_row_end = pd.DataFrame([point_2], columns=df.columns)
            df = pd.concat([df, new_row_end], ignore_index=True) 
        return df

    df_district_pp_sequence = add_start_end_point(point_1 = start_point, point_2= end_point, df = df_district_pp_sequence)

    
    #FUNCTION to delete all "consecutive" PostPointId numbers from the list and keep sequence
    #(PostObjectID on the same building being visited consecutively means just one visit to that PostPointID is needed on that trip)

    def delete_consecutive_duplicates(df, column_name):
        #Identify consecutive duplicates by calculating the difference
        differences = df[column_name].diff()

        # Keep the rows where the difference is non-zero
        df = df.loc[differences != 0]
        df = df.reset_index(drop=True)
        
        return df

    df_district_pp_sequence_filtered = delete_consecutive_duplicates(df = df_district_pp_sequence, column_name= 'PostPointId')

    #Save the value of the amount of PostPoint Trips
    PP_visit_rate = len(df_district_pp_sequence)

    #FUNTION to count number of duplicate PostPoints which are not consecutive
    #(if value > 1, PostPoints are visited and then returned in a non consecutive manner on current routing)
    #[Case is 1 if it is a tour when start and end point is the same, Case is 0 if is not a tour])

    def count_repeated_pp(df):
        df2 = df.groupby(['PostPointId'])['PostPointId'].count().to_frame()
        repeated = len(df2[df2['PostPointId']>1])
        return repeated

    repeated_pp_num = count_repeated_pp(df_district_pp_sequence_filtered)
    
    
    #Convert the default sequence to list
    district_pp_sequence_filtered = df_district_pp_sequence_filtered['PostPointId'].values.tolist()
    
    #FUNCTION to calculate total tour length
    def get_tour_length(sequence_list, distance_df):
        tour_length = 0 
        for i in range(len(sequence_list)-1):
            # Specify the specific values for column 1 and column 2
            value_column1 = sequence_list[i]
            value_column2 = sequence_list[i+1]

            # Filter the dataframe based on the specified values
            match_df = distance_df.loc[(distance_df['PostPoint1'] == value_column1) & (distance_df['PostPoint2'] == value_column2)]

            # Retrieve the value in distance column or give error if does not exist
            distance_pp = match_df['Distance'].values[0] if not match_df.empty else 'ERROR: No distance for PostPoint combination'
            tour_length += distance_pp
            
        return round(tour_length,2)

    district_tour_length = get_tour_length(district_pp_sequence_filtered, df_pp_district_distances)

    #Create a dictionary as a mapping of PostPoint to Index Position in list (In case is needed or can be useful)
    mapping_district = dict(zip([i for i in range(len(district_pp_sequence_filtered))] ,district_pp_sequence_filtered))
    
    
    return  district_pp_sequence_filtered, mapping_district, district_tour_length, repeated_pp_num

# 10
#FUNCTION to get the list of all districts on a specific region by looping existing entries in the folder
def get_district_list(region):
    districts_list = []
    districts_name_path = os.path.join(path, 'Data', 'Instances', region, 'Districts')
    for filename in os.listdir(districts_name_path):
        districts_list.append(filename[:-4])
    return districts_list

# 11
#FUNCTION to generate all default route information for an entire region
def get_region_all_default_routes(region_chosen, path_save):

  dir_region = os.path.join(path_save, region_chosen + '_Default_Routes')
  # print(dir_region)
  if not os.path.exists(dir_region):
    os.mkdir(dir_region)

  district_list = get_district_list(region = region_chosen)

  default_route_regions = {}

  for district in district_list:
    district_route_info = {}
    route_list, district_mapping, total_length, repetitions = get_default_route(region = region_chosen, district_name = district)
    #save default route sequence list as pickle file
    pickle.dump(route_list, open(os.path.join(dir_region, district + '_default_route.p'), 'wb'))
    district_route_info['default_route'] = route_list
    district_route_info['mapping'] = district_mapping
    district_route_info['route_cost'] = total_length
    default_route_regions[district] = district_route_info
      
    #save data regarding total length of tour, repeating nodes, and mapping info on .txt file
    file = open(os.path.join(dir_region, district + 'default_route_info.txt'),'w')
    file.write('Total tour length in seconds: \n{}\n'.format(total_length))
    file.write('Total tour length in hours: \n{}\n'.format(round(total_length/3600,1)))
    file.write('Number of PostPoint visited more than once: \n{}\n'.format(repetitions))
    file.write('Mapping: \n{}\n'.format(district_mapping))

    file.close()
  return default_route_regions

