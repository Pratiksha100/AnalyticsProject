import lk_util
from lk_heuristic.utils.solver_funcs import solve
import pandas as pd
import numpy as np
import os
import time
start_time = time.time()

# tsp_filename = "./tsp_input_files/test.tsp"
# output_filename = "./solutions/solution_test.tsp"
tsp_filename = "test.tsp"
output_filename = "solution_test.tsp"

def create_dist_mat_from_atsp(path_of_file):
    # specify the path to the .atsp file
    file_path = path_of_file
    print(file_path)


    # initialize variables
    n_nodes = None
    dist_matrix = []

    # open and read the file
    with open(file_path) as f:
        for line in f:
            # extract the number of nodes
            if "DIMENSION" in line:
                n_nodes = int(line.split(":")[1].strip())
            # extract the distance matrix
            elif "EDGE_WEIGHT_SECTION" in line:
                while True:
                    line = f.readline()
                    if "EOF" in line:
                        break
                    dist_matrix.append(list(map(int, line.split())))
            # continue reading until end of file
            elif "EOF" in line:
                break


    #resizing the distance matrix to a square matrix
    list_of_lists = dist_matrix

    flat_list = []
    for sublist in list_of_lists:
        for item in sublist:
            flat_list.append(item)


    # Example 1D list
    lst = flat_list

    # Calculate the size of the square matrix
    n = len(lst)
    size = int(np.sqrt(n))

    # Reshape the 1D list into a 2D numpy array with the desired shape
    arr = np.reshape(lst, (size, size))

    # Print the resulting array
    dist_mat = np.array(arr)

    print("No of cities : "  , n_nodes)
    print(dist_mat.shape)
    return dist_mat

# instances_path = os.path.join(os.getcwd() , "LKH-Heuristic\\ALL_atsp")
# instances_path = 'LKH/LKH-Heuristic/ALL_atsp'
# instances_files = os.listdir(instances_path)
# instances_files2 = [os.path.join(instances_path , i) for i in instances_files if i.endswith(".atsp")]
# dir = instances_files2[len(instances_files2)-2]
distances = create_dist_mat_from_atsp('LKH/LKH-Heuristic/ALL_atsp/br18.atsp')

# distances = [[0,5,2],[4,0,1],[8,3,0]]

distances_converted = lk_util.make_symmetric(distances)
lk_util.distances_to_tsplib_file(distances_converted, tsp_filename)
solve(tsp_file=tsp_filename, solution_method="lk2_improve", runs=20, file_name=output_filename)
# backtracking = (5,5), reduction_level = 4, reduction_cycle = 4, tour_type = "cycle",
# file_name = "C:/temp/test_solution.tsp", logging_level = 20)

# get solution sequence
solutionSequence = []
# read in file
with open(output_filename, "r+") as f:

    # read all tsp file lines
    tsp_lines = f.readlines()

    # loop through each tsp line
    for line in tsp_lines:
        # check if line is not last end-of-file line
        if line.strip() != "EOF":
            # split the line using space separator
            stop = line.replace("\n", "").split()
            if len(stop) == 1 and stop[0].strip() != 'NODE_COORD_SECTION':
                solutionSequence.append(int(stop[0]))

n = len(distances)

if solutionSequence[0] == solutionSequence[1] - n:
    tour = solutionSequence
else:
    tour = [solutionSequence[0]]
    cnt = 2*n - 1
    while cnt != 0:
        tour.append(solutionSequence[cnt])
        cnt -= 1

# final_tour = []
# for i in tour[::2]:
#     final_tour.append(i)

final_tour  = [x for x in tour if x < n]

print(solutionSequence)
print(tour)
print(final_tour)

def final_cost(final_tour):
    final_tour.append(final_tour[0])
    print("########################### ", final_tour)
    Total_distance_covered = 0
    for i in range(len(final_tour) -1):
        Total_distance_covered = Total_distance_covered + distances[final_tour[i]][final_tour[i+1]]
    return Total_distance_covered

print(final_cost(final_tour))


print("--- %s seconds ---" % (time.time() - start_time))