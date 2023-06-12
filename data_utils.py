import pickle
import os

current_dir = os.getcwd() + ""


def get_data(instance_object= "", solver=""):
    if instance_object != "":
        all_unequal_instances_objects = pickle.load(open(current_dir + "\\Results\\all_unequal_instances_objects_Hannover.p", "rb"))
        return all_unequal_instances_objects
    if solver != "":
        all_complete_solver = pickle.load(open(current_dir + "\\Results\\all_complete_solver.p", "rb"))
        return all_complete_solver

print('data has been loaded successfully ')

# exec(open("data_utils.py").read())