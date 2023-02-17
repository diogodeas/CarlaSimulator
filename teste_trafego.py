import glob
import os
import sys
import time
from distutils.spawn import spawn
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import random








if __name__ == '__main__':
    #Connect to the client and retrieve the world object
    client = carla.Client('localhost', 2000)
    world = client.get_world()
    tm = client.get_trafficmanager(8000)
    
    
    #Get the blueprint library and filter for vehicles
    vehicle_bps = world.get_blueprint_library().filter('*vehicle*')
    
    #Get the map's spawn points
    spawn_points = world.get_map().get_spawn_points()
    
    vehicle_list = []
    SpawnActor = carla.command.SpawnActor
    SetAutopilot = carla.command.SetAutopilot
    FutureActor = carla.command.FutureActor
    #Spawn x vehicles at random spawn points
    #For each spawn point, choose a random vehicle blueprint
    x = int(input("Quantos veículos spawnar?\n"))
    for i in range(x):
        vehicle = world.try_spawn_actor(random.choice(vehicle_bps), random.choice(spawn_points))
        vehicle_list.append(vehicle)
    print(vehicle_list)
    tm_port = tm.get_port()
    batch = []
    #configure autopilot and traffic manager
    for vehicle in vehicle_list:
        batch.append(SetAutopilot(vehicle, True, tm_port))
        client.apply_batch_sync(batch, True)
        
    