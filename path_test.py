import glob
import os
import sys
import time
import math
import numpy as np
from distutils.spawn import spawn
from pynput import keyboard
import pickle
import pyautogui
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import random
import pickle
global signal
signal = 0
global spawnv
spawnv = 0
#listener to key c
def on_press(key):
    try:
        k = key.char # single-char keys
    except:
        k = key.name # other keys
    if k == 'c': # keys interested
        print('Key pressed: ' + k)
        #send signal
        global signal
        signal = 1
    if k == 'v':
        print('Key pressed: ' + k)
        global spawnv
        if spawnv == 0:
            spawnv = 1
        
if __name__ == '__main__':
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    #Connect to the client and retrieve the world object
    client = carla.Client('localhost', 2000)
    world = client.load_world('Town03', carla.MapLayer.Buildings | carla.MapLayer.ParkedVehicles)
    #Set up the simulation in synchronous mode
    settings = world.get_settings()
    settings.synchronous_mode = True # Enables synchronous mode
    settings.fixed_delta_seconds = 0.05
    world.apply_settings(settings)
    # Set up the TM in synchronous mode
    traffic_manager = client.get_trafficmanager()
    traffic_manager.set_synchronous_mode(True)
    traffic_manager.set_random_device_seed(0)
    random.seed(0)
    spectator = world.get_spectator()
    
    spawn_points = world.get_map().get_spawn_points()
    
    # Draw the spawn point locations as numbers in the map
    for i, spawn_point in enumerate(spawn_points):
        world.debug.draw_string(spawn_point.location, str(i), life_time=100000)
    #Select some models from the blueprint library
    spawn_points = world.get_map().get_spawn_points()
    models = ['dodge', 'audi', 'model3', 'mini', 'mustang', 'lincoln', 'prius', 'nissan', 'crown', 'impala']
    blueprints = []
    for vehicle in world.get_blueprint_library().filter('*vehicle*'):
        if any(model in vehicle.id for model in models):
            blueprints.append(vehicle)
    max_vehicles = 1
    max_vehicles = min([max_vehicles, len(spawn_points)])
    vehicles = []
    vehicle_positions = [[] for i in range(max_vehicles)]
    vehicle_velocities = [[] for i in range(max_vehicles)]
    path1_ind = [103,105,145,209,81,140,83,251,175,252]
    with open('path1.pkl', 'rb') as f:
        pathgerado = pickle.load(f)
    for i in range(len(pathgerado)):# initialize carla.Location method:__init__(self, x=0.0, y=0.0, z=0.0) as described in documentation
        pathgerado[i] = carla.Location(pathgerado[i][0], pathgerado[i][1], pathgerado[i][2])
    print(pathgerado)
    
    print([spawn_points[i].location for i in path1_ind])
    path1 = [spawn_points[i].location for i in path1_ind]
    spawnpoint = spawn_points[181]
    # Take a random sample of the spawn points and spawn some vehicles
    # for i, spawn_point in enumerate(random.sample(spawn_points, max_vehicles)):
    #     temp = world.try_spawn_actor(random.choice(blueprints), spawn_point)
    #     if temp is not None:
    #         vehicles.append(temp)
    
    try:
        while True:
            world.tick()
            if spawnv == 1:
                spawnv = -1
                temp = world.try_spawn_actor(random.choice(blueprints), spawnpoint)
                if temp is not None:
                    vehicles.append(temp)
                for vehicle in vehicles:
                    vehicle.set_autopilot(True)
                    traffic_manager.ignore_lights_percentage(vehicle, 100)
                    traffic_manager.update_vehicle_lights(vehicle, True)
                    traffic_manager.random_left_lanechange_percentage(vehicle, 0)
                    traffic_manager.random_right_lanechange_percentage(vehicle, 0)
                    traffic_manager.auto_lane_change(vehicle, True)
                    traffic_manager.set_path(vehicle, path1)
            if signal == 1:
                time.sleep(0.5)
                signal = 0
                camera = world.get_spectator().get_transform().location
                pathgerado.append((camera.x, camera.y, camera.z))
                print(pathgerado)
    except KeyboardInterrupt:
        # with open('path1.pkl', 'wb') as f:
        #     pickle.dump(pathgerado, f)
        pass
            
        
            
        