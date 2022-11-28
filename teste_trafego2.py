import glob
import os
import sys
import time
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

        
        



if __name__ == '__main__':
    
    #Connect to the client and retrieve the world object
    client = carla.Client('localhost', 2000)
    world = client.get_world()
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
    max_vehicles = 50
    max_vehicles = min([max_vehicles, len(spawn_points)])
    vehicles = []

    # Take a random sample of the spawn points and spawn some vehicles
    for i, spawn_point in enumerate(random.sample(spawn_points, max_vehicles)):
        temp = world.try_spawn_actor(random.choice(blueprints), spawn_point)
        if temp is not None:
            vehicles.append(temp)

    for vehicle in vehicles:
        vehicle.set_autopilot(True)
        
        
        
    
    
    #tick world, if c is pressed, destroy all vehicles
    count = 0
    #run listener in parallel
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    try:
        while True:
            world.tick()
            count = (count+1)%20
            if count == 0: 
                if signal == 1:
                    signal = 0
                    for vehicle in vehicles:
                        vehicle.destroy()
                    settings.synchronous_mode = False
                    world.apply_settings(settings)
                    traffic_manager.set_synchronous_mode(False)
                        
            time.sleep(0.002)
    except KeyboardInterrupt:
        settings.synchronous_mode = False
        world.apply_settings(settings)
        traffic_manager.set_synchronous_mode(False)
        
        
    
    
        
        
    