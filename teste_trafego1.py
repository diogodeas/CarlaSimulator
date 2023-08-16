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
global auto_pilot
auto_pilot = 0
global kpress
kpress = 0
#listener to key c
def on_press(key):
    global kpress
    global kpressanterior
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
        kpress+=1
        kpress%=2
        if(kpress==1):
            kpressanterior=world.get_spectator().get_transform()
        if kpress == 0:
            print('Quarteirao: [',end='')
            xmin = min(kpressanterior.location.x,world.get_spectator().get_transform().location.x)
            xmax = max(kpressanterior.location.x,world.get_spectator().get_transform().location.x)
            ymin = min(kpressanterior.location.y,world.get_spectator().get_transform().location.y)
            ymax = max(kpressanterior.location.y,world.get_spectator().get_transform().location.y)
            print(xmin,',',xmax,',',ymin,',',ymax,']')
        print('Key pressed: ' + k)
        camera = world.get_spectator().get_transform()
        print(camera.location)
    if k == 'l':
        print('Key pressed: ' + k)
        signal = 2


def verifica_quarteirao(veiculo, quarteirao_coords):
    # Obtém a localização do veículo
    localizacao = veiculo.get_location()

    # Verifica se a localização do veículo está dentro das coordenadas do quarteirão
    if (localizacao.x >= quarteirao_coords[0] and localizacao.x <= quarteirao_coords[1]) and \
       (localizacao.y >= quarteirao_coords[2] and localizacao.y <= quarteirao_coords[3]):
        return True
    else:
        return False
        
def gerenciarFila(idQuart):
    global filaQuarteirao
    global BoolQuarteirao
    if len(filaQuarteirao[idQuart]) == 0:
        return
    for ivehicle in range(len(filaQuarteirao[idQuart])):
        if ivehicle != 0:
            filaQuarteirao[idQuart][ivehicle].set_autopilot(False)
            filaQuarteirao[idQuart][ivehicle].apply_control(carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0))
    if BoolQuarteirao[idQuart]==0:
        filaQuarteirao[idQuart][0].set_autopilot(True)
        BoolQuarteirao[idQuart] = 1
        
    



if __name__ == '__main__':
    
    #Connect to the client and retrieve the world object
    client = carla.Client('localhost', 2000)
    world = client.get_world()
    # world = client.load_world('Town03', carla.MapLayer.Buildings | carla.MapLayer.ParkedVehicles)
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
    max_vehicles = 80
    max_vehicles = min([max_vehicles, len(spawn_points)])
    vehicles = []
    vehicle_positions = [[] for i in range(max_vehicles)]
    vehicle_velocities = [[] for i in range(max_vehicles)]
    # Take a random sample of the spawn points and spawn some vehicles
    for i, spawn_point in enumerate(random.sample(spawn_points, max_vehicles)):
        temp = world.try_spawn_actor(random.choice(blueprints), spawn_point)
        if temp is not None:
            vehicles.append(temp)
        
             

    for vehicle in vehicles:
        vehicle.set_autopilot(True)
        traffic_manager.ignore_lights_percentage(vehicle, 100)
    #I'll give 2 values as input and assign them as min and max values for the spawn points
    
    xmin, xmax = sorted([-21.393253, 22.072824])
    ymin, ymax = sorted([-154.187500, -118.530777])
    global filaQuarteirao
    global BoolQuarteirao
    BoolQuarteirao = [0 for _ in range(100)]
    filaQuarteirao = [[] for _ in range(100)]
    # Define as coordenadas XYZ do quarteirão desejado
    quarteirao_coords = [[-63.775169372558594 , -25.274696350097656 , 0.8999748826026917 , 41.85736846923828 ]]  # Substitua pelos valores corretos

        
    #tick world, if c is pressed, destroy all vehicles
    count = -1
    #run listener in parallel
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    total_avg = 0
    count_avg = 0
    try:
        while True:
            world.tick()
            count = (count+1)%3
            
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

                if signal == 2:
                    signal = 0
                    if auto_pilot == 0:
                        for vehicle in vehicles:
                            vehicle.set_autopilot(False)
                            traffic_manager.ignore_lights_percentage(vehicle, 100)
                        auto_pilot = 1

                    else: 
                        for vehicle in vehicles:
                            vehicle.set_autopilot(True)
                            traffic_manager.ignore_lights_percentage(vehicle, 100)
                        auto_pilot = 0 




                for i, vehicle in enumerate(vehicles):
                    try:
                        location = vehicle.get_location()
                        velocity = vehicle.get_velocity()
                        vehicle_positions[i].append((location.x,location.y,location.z))
                        vehicle_velocities[i].append((velocity.x,velocity.y,velocity.z))
                    except Exception as e:
                        print(e)
                        continue
                        
                
                
                # Obtendo uma lista de todos os veículos dentro da área
                for vehicle in vehicles:
                    try:
                        location = vehicle.get_location()
                        for i in range(len(quarteirao_coords)):
                            if verifica_quarteirao(vehicle, quarteirao_coords[i]):
                                if vehicle not in filaQuarteirao[i]:
                                    filaQuarteirao[i].append(vehicle)
                            else:
                                if vehicle in filaQuarteirao[i]:
                                    filaQuarteirao[i].remove(vehicle)
                                    BoolQuarteirao[i] = 0
                    except Exception as e:
                        print(e)
                        for i in range(len(quarteirao_coords)):
                            if vehicle in filaQuarteirao[i]:
                                filaQuarteirao[i].remove(vehicle)
                        

                for i in range(len(quarteirao_coords)):
                    num_vehicles = len(filaQuarteirao[i])
                    gerenciarFila(i)

                total_velocity = 0
                for vehicle in vehicles:
                    try:
                        # Obtendo a velocidade do veículo
                        velocity = vehicle.get_velocity()

                        # Obtendo a velocidade escalar do veículo
                        speed_scalar = np.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)

                        # Adicionando a velocidade escalar ao total
                        total_velocity += speed_scalar
                    except Exception as e:
                        print(e)
                        continue

                # Calculando o fluxo médio
                num_vehicles =len(vehicles)
                if num_vehicles == 0:
                    average_speed = 0
                else:
                    average_speed = total_velocity / num_vehicles
                total_avg += average_speed
                count_avg += 1

                print("Velociade média até então é: ", total_avg/count_avg)
                

                # Imprimindo o fluxo na tela
                #print(f"Fluxo de tráfego na área: {flow} veículos por segundo")



            #print("Posições dos veículos:", vehicle_positions)
                        
            time.sleep(0.002)
    except KeyboardInterrupt:
        settings.synchronous_mode = False
        world.apply_settings(settings)
        traffic_manager.set_synchronous_mode(False)