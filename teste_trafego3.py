import glob
import os
import sys
import time
import math
import numpy as np
from distutils.spawn import spawn
from pynput import keyboard

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
    if k == 'g':
        print('Key pressed: ' + k)
        camera = world.get_spectator().get_transform()
        print(camera.location)



        
        



if __name__ == '__main__':
    
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

    # Set a seed so behaviour can be repeated if necessary
    traffic_manager.set_random_device_seed(0)
    random.seed(0)

    # We will also set up the spectator so we can see what we do
    spectator = world.get_spectator()
    
    spawn_points = world.get_map().get_spawn_points()
    
    # Draw the spawn point locations as numbers in the map
    for i, spawn_point in enumerate(spawn_points):
        world.debug.draw_string(spawn_point.location, str(i), life_time=10)
    #Select some models from the blueprint library
    models = ['dodge', 'audi', 'model3', 'mini', 'mustang', 'lincoln', 'prius', 'nissan', 'crown', 'impala']
    blueprints = []
    for vehicle in world.get_blueprint_library().filter('*vehicle*'):
        if any(model in vehicle.id for model in models):
            blueprints.append(vehicle)

    # Set a max number of vehicles and prepare a list for those we spawn
    max_vehicles = 150
    max_vehicles = min([max_vehicles, len(spawn_points)])
    vehicles = []
    vehicle_positions = [[] for i in range(max_vehicles)]
    vehicle_velocities = [[] for i in range(max_vehicles)]

    # Route 1
    spawn_point_1 =  spawn_points[32]
    # Create route 1 from the chosen spawn points
    route_1_indices = [129, 28, 124, 33, 97, 119, 58, 154, 147]
    route_1 = []
    for ind in route_1_indices:
        route_1.append(spawn_points[ind].location)

    # Route 2
    spawn_point_2 =  spawn_points[149]
    # Create route 2 from the chosen spawn points
    route_2_indices = [21, 76, 38, 34, 90, 3]
    route_2 = []
    for ind in route_2_indices:
        route_2.append(spawn_points[ind].location)

    # Now let's print them in the map so we can see our routes
    world.debug.draw_string(spawn_point_1.location, 'Spawn point 1', life_time=30, color=carla.Color(255,0,0))
    world.debug.draw_string(spawn_point_2.location, 'Spawn point 2', life_time=30, color=carla.Color(0,0,255))

    for ind in route_1_indices:
        spawn_points[ind].location
        world.debug.draw_string(spawn_points[ind].location, str(ind), life_time=60, color=carla.Color(255,0,0))

    for ind in route_2_indices:
        spawn_points[ind].location
        world.debug.draw_string(spawn_points[ind].location, str(ind), life_time=60, color=carla.Color(0,0,255))


    # # Run the simulation so we can inspect the results with the spectator
    # while True:
    #     world.tick()

    # Set delay to create gap between spawn times
    spawn_delay = 20
    counter = spawn_delay

    # Alternate between spawn points
    alt = False
    count = -1

    spawn_points = world.get_map().get_spawn_points()
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    try:
        while True:
            world.tick()
            count = (count+1)%20
            n_vehicles = len(world.get_actors().filter('*vehicle*'))
            vehicle_bp = random.choice(blueprints)

            # Spawn vehicle only after delay
            if counter == spawn_delay and n_vehicles < max_vehicles:
                # Alternate spawn points
                if alt:
                    vehicle = world.try_spawn_actor(vehicle_bp, spawn_point_1)
                    if vehicle is not None:
                        vehicles.append(vehicle)
                
                else:
                    vehicle = world.try_spawn_actor(vehicle_bp, spawn_point_2)
                    if vehicle is not None:
                        vehicles.append(vehicle)

                if vehicle: # IF vehicle is succesfully spawned
                    vehicle.set_autopilot(True) # Give TM control over vehicle

                    # Set parameters of TM vehicle control, we don't want lane changes
                    traffic_manager.update_vehicle_lights(vehicle, True)
                    traffic_manager.random_left_lanechange_percentage(vehicle, 0)
                    traffic_manager.random_right_lanechange_percentage(vehicle, 0)
                    traffic_manager.auto_lane_change(vehicle, False)

                    # Alternate between routes
                    if alt:
                        traffic_manager.set_path(vehicle, route_1)
                        alt = False
                    else:
                        traffic_manager.set_path(vehicle, route_2)
                        alt = True

                    vehicle = None

                counter -= 1
            elif counter > 0:
                counter -= 1
            elif counter == 0:
                counter = spawn_delay
            
            if count == 0: 
                if signal == 1:
                    signal = 0
                    with open('vehicle_position.pickle', 'wb') as f:
                        pickle.dump(vehicle_positions, f)
                        f.close()
                    with open('vehicle_velocity.pickle', 'wb') as f:
                        pickle.dump(vehicle_velocities, f)
                        f.close()
                    for vehicle in vehicles:
                        vehicle.destroy()
                    settings.synchronous_mode = False
                    world.apply_settings(settings)
                    traffic_manager.set_synchronous_mode(False)

                for i, vehicle in enumerate(vehicles):
                    location = vehicle.get_location()
                    velocity = vehicle.get_velocity()
                    vehicle_positions[i].append((location.x,location.y,location.z))
                    vehicle_velocities[i].append((velocity.x,velocity.y,velocity.z))
                
                x_min = -50
                x_max = 60
                y_min = 200
                y_max = 210

                # Obtendo uma lista de todos os veículos dentro da área
                vehicle_list = []
                for vehicle in world.get_actors().filter('vehicle.*'):
                    location = vehicle.get_location()
                    if x_min <= location.x <= x_max and y_min <= location.y <= y_max:
                        vehicle_list.append(vehicle)

                num_vehicles = len(vehicle_list)
                total_velocity = 0
                for vehicle in vehicle_list:
                    # Obtendo a velocidade do veículo
                    velocity = vehicle.get_velocity()

                    # Obtendo a velocidade escalar do veículo
                    speed_scalar = np.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)

                    # Adicionando a velocidade escalar ao total
                    total_velocity += speed_scalar

                # Calculando o fluxo médio
                if num_vehicles == 0:
                    average_speed = 0;
                else:
                    average_speed = total_velocity / num_vehicles
                flow = math.floor(average_speed * num_vehicles)

                # Imprimindo o fluxo na tela
                #print(f"Fluxo de tráfego na área: {flow} veículos por segundo")



            #print("Posições dos veículos:", vehicle_positions)
                        
            time.sleep(0.002)
    except KeyboardInterrupt:
        settings.synchronous_mode = False
        world.apply_settings(settings)
        traffic_manager.set_synchronous_mode(False)