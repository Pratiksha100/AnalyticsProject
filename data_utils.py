import pickle
import os

current_dir = os.getcwd() + ""


all_unequal_instances_objects = pickle.load(open(current_dir + "\\Results\\all_unequal_instances_objects_Hannover.p", "rb"))
all_complete_solver = pickle.load(open(current_dir + "\\Results\\all_complete_solver.p", "rb"))
print('data has been loaded successfully ')