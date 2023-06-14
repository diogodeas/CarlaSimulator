#!/usr/bin/env python

# Copyright (c) 2021 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""Example script to generate traffic in the simulation"""

import glob
import os
import sys
import time

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
from carla import Location
from carla import VehicleLightState as vls

import argparse
import logging
from numpy import random
import math

def calcular_distancia(loc1, loc2):
    dx = loc2.x - loc1.x
    dy = loc2.y - loc1.y
    dz = loc2.z - loc1.z
    distancia = math.sqrt(dx**2 + dy**2 + dz**2)
    return distancia

def get_actor_blueprints(world, filter, generation):
    bps = world.get_blueprint_library().filter(filter)

    if generation.lower() == "all":
        return bps

    # If the filter returns only one bp, we assume that this one needed
    # and therefore, we ignore the generation
    if len(bps) == 1:
        return bps

    try:
        int_generation = int(generation)
        # Check if generation is in available generations
        if int_generation in [1, 2]:
            bps = [x for x in bps if int(x.get_attribute('generation')) == int_generation]
            return bps
        else:
            print("   Warning! Actor Generation is not valid. No actor will be spawned.")
            return []
    except:
        print("   Warning! Actor Generation is not valid. No actor will be spawned.")
        return []

def main():
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-n', '--number-of-vehicles',
        metavar='N',
        default=20,
        type=int,
        help='Number of vehicles (default: 30)')
    argparser.add_argument(
        '-w', '--number-of-walkers',
        metavar='W',
        default=10,
        type=int,
        help='Number of walkers (default: 10)')
    argparser.add_argument(
        '--safe',
        action='store_true',
        help='Avoid spawning vehicles prone to accidents')
    argparser.add_argument(
        '--filterv',
        metavar='PATTERN',
        default='vehicle.*',
        help='Filter vehicle model (default: "vehicle.*")')
    argparser.add_argument(
        '--generationv',
        metavar='G',
        default='All',
        help='restrict to certain vehicle generation (values: "1","2","All" - default: "All")')
    argparser.add_argument(
        '--filterw',
        metavar='PATTERN',
        default='walker.pedestrian.*',
        help='Filter pedestrian type (default: "walker.pedestrian.*")')
    argparser.add_argument(
        '--generationw',
        metavar='G',
        default='2',
        help='restrict to certain pedestrian generation (values: "1","2","All" - default: "2")')
    argparser.add_argument(
        '--tm-port',
        metavar='P',
        default=8000,
        type=int,
        help='Port to communicate with TM (default: 8000)')
    argparser.add_argument(
        '--asynch',
        action='store_true',
        help='Activate asynchronous mode execution')
    argparser.add_argument(
        '--hybrid',
        action='store_true',
        help='Activate hybrid mode for Traffic Manager')
    argparser.add_argument(
        '-s', '--seed',
        metavar='S',
        type=int,
        help='Set random device seed and deterministic mode for Traffic Manager')
    argparser.add_argument(
        '--seedw',
        metavar='S',
        default=0,
        type=int,
        help='Set the seed for pedestrians module')
    argparser.add_argument(
        '--car-lights-on',
        action='store_true',
        default=False,
        help='Enable automatic car light management')
    argparser.add_argument(
        '--hero',
        action='store_true',
        default=False,
        help='Set one of the vehicles as hero')
    argparser.add_argument(
        '--respawn',
        action='store_true',
        default=False,
        help='Automatically respawn dormant vehicles (only in large maps)')
    argparser.add_argument(
        '--no-rendering',
        action='store_true',
        default=False,
        help='Activate no rendering mode')
    argparser.add_argument(
        '-f', '--recorder_filename',
        metavar='F',
        default="D:/COMPET/WindowsNoEditor/PythonAPI/CarlaSimulator/test1.rec",
        help='recorder filename (test1.rec)')
    argparser.add_argument(
        '-a', '--show_all',
        action='store_true',
        help='show detailed info about all frames content')
    argparser.add_argument(
        '-sa', '--save_to_file',
        metavar='S',
        help='save result to file (specify name and extension)')
    args = argparser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    

    vehicles_list = []
    walkers_list = []
    all_id = []
    client = carla.Client(args.host, args.port)
    client.set_timeout(1000.0)
    synchronous_master = False
    random.seed(args.seed if args.seed is not None else int(time.time()))
    client.start_recorder('recording.log')

    try:
        world = client.get_world()

        traffic_manager = client.get_trafficmanager(args.tm_port)
        traffic_manager.set_global_distance_to_leading_vehicle(2.5)
        if args.respawn:
            traffic_manager.set_respawn_dormant_vehicles(True)
        if args.hybrid:
            traffic_manager.set_hybrid_physics_mode(True)
            traffic_manager.set_hybrid_physics_radius(70.0)
        if args.seed is not None:
            traffic_manager.set_random_device_seed(args.seed)

        settings = world.get_settings()
        if not args.asynch:
            traffic_manager.set_synchronous_mode(True)
            if not settings.synchronous_mode:
                synchronous_master = True
                settings.synchronous_mode = True
                settings.fixed_delta_seconds = 0.05
            else:
                synchronous_master = False
        else:
            print("You are currently in asynchronous mode. If this is a traffic simulation, \
            you could experience some issues. If it's not working correctly, switch to synchronous \
            mode by using traffic_manager.set_synchronous_mode(True)")

        if args.no_rendering:
            settings.no_rendering_mode = True
        world.apply_settings(settings)

        blueprints = get_actor_blueprints(world, args.filterv, args.generationv)
        blueprintsWalkers = get_actor_blueprints(world, args.filterw, args.generationw)

        if args.safe:
            blueprints = [x for x in blueprints if x.get_attribute('base_type') == 'car']

        blueprints = sorted(blueprints, key=lambda bp: bp.id)

        spawn_points = world.get_map().get_spawn_points()
        number_of_spawn_points = len(spawn_points)

        if args.number_of_vehicles < number_of_spawn_points:
            random.shuffle(spawn_points)
        elif args.number_of_vehicles > number_of_spawn_points:
            msg = 'requested %d vehicles, but could only find %d spawn points'
            logging.warning(msg, args.number_of_vehicles, number_of_spawn_points)
            args.number_of_vehicles = number_of_spawn_points

        # @todo cannot import these directly.
        SpawnActor = carla.command.SpawnActor
        SetAutopilot = carla.command.SetAutopilot
        FutureActor = carla.command.FutureActor

        # --------------
        # Spawn vehicles
        # --------------
        batch = []
        hero = args.hero
        for n, transform in enumerate(spawn_points):
            if n >= args.number_of_vehicles:
                break
            blueprint = random.choice(blueprints)
            if blueprint.has_attribute('color'):
                color = random.choice(blueprint.get_attribute('color').recommended_values)
                blueprint.set_attribute('color', color)
            if blueprint.has_attribute('driver_id'):
                driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
                blueprint.set_attribute('driver_id', driver_id)
            if hero:
                blueprint.set_attribute('role_name', 'hero')
                hero = False
            else:
                blueprint.set_attribute('role_name', 'autopilot')

            # spawn the cars and set their autopilot and light state all together
            batch.append(SpawnActor(blueprint, transform)
                .then(SetAutopilot(FutureActor, True, traffic_manager.get_port())))

        for response in client.apply_batch_sync(batch, synchronous_master):
            if response.error:
                logging.error(response.error)
            else:
                vehicles_list.append(response.actor_id)
        all_vehicle_actors = world.get_actors(vehicles_list)
        # Set automatic vehicle lights update if specified
        if args.car_lights_on:            
            for actor in all_vehicle_actors:
                traffic_manager.update_vehicle_lights(actor, True)
        traffic_lights = []

        all_actors = world.get_actors()
        for actor in all_actors:
            if actor.type_id == 'traffic.traffic_light':
                traffic_lights.append(actor)
        area_central = world.get_spectator().get_transform()
        print(area_central)
        area_raio = 50.0  # Raio da área (distância máxima permitida)
        semaforos_na_area = []
        for traffic_light in traffic_lights:
            traffic_light_position = traffic_light.get_location()  
            distancia = calcular_distancia(traffic_light_position, area_central.location)
            # Verificar se a distância está dentro do raio da área
            if distancia <= area_raio:
                semaforos_na_area.append(traffic_light)
            #print("Traffic Light - Position:", traffic_light_position)
            #print("Traffic Light - State:", traffic_light_state)
        for semaforo_vehicle in semaforos_na_area:
            print("Semaforo na area:", semaforo_vehicle)
                        
            # Obtém o estado atual do semáforo
            state = semaforo_vehicle.get_state()

            # Obtém a duração do estado verde
            green_duration =  carla.TrafficLight.get_green_time(semaforo_vehicle)

            # Obtém a duração do estado amarelo
            yellow_duration = carla.TrafficLight.get_yellow_time(semaforo_vehicle)

            # Obtém a duração do estado vermelho
            red_duration = carla.TrafficLight.get_red_time(semaforo_vehicle)

            light_number_on_group = carla.TrafficLight.get_pole_index(semaforo_vehicle)
            vehicle_stop_points = carla.TrafficLight.get_stop_waypoints(semaforo_vehicle)
            stop_points = []
            for vehicle_stop_point in vehicle_stop_points:
                waypoint = vehicle_stop_point.transform.location
                stop_points.append(waypoint)
            semaforo_vehicle.set_state(carla.TrafficLightState.Green)
            if(light_number_on_group == 0):
                semaforo_vehicle.set_state(carla.TrafficLightState.Red)
            
            #print("Duração do estado verde:", green_duration)
            #print("Duração do estado amarelo:", yellow_duration)
            #print("Duração do estado vermelho:", red_duration)
            #print("Grupo pertencente:", group_of_ligths)
            #print("Numero dentro do grupo:", light_number_on_group)
            #for stop_point in stop_points:
            #    print("ponto de parada do veiculo:", stop_point)
        
        # -------------
        # Spawn Walkers
        # -------------
        # some settings
        percentagePedestriansRunning = 0.0      # how many pedestrians will run
        percentagePedestriansCrossing = 0.0     # how many pedestrians will walk through the road
        if args.seedw:
            world.set_pedestrians_seed(args.seedw)
            random.seed(args.seedw)
        # 1. take all the random locations to spawn
        spawn_points = []
        for i in range(args.number_of_walkers):
            spawn_point = carla.Transform()
            loc = world.get_random_location_from_navigation()
            if (loc != None):
                spawn_point.location = loc
                spawn_points.append(spawn_point)
        # 2. we spawn the walker object
        batch = []
        walker_speed = []
        for spawn_point in spawn_points:
            walker_bp = random.choice(blueprintsWalkers)
            # set as not invincible
            if walker_bp.has_attribute('is_invincible'):
                walker_bp.set_attribute('is_invincible', 'false')
            # set the max speed
            if walker_bp.has_attribute('speed'):
                if (random.random() > percentagePedestriansRunning):
                    # walking
                    walker_speed.append(walker_bp.get_attribute('speed').recommended_values[1])
                else:
                    # running
                    walker_speed.append(walker_bp.get_attribute('speed').recommended_values[2])
            else:
                print("Walker has no speed")
                walker_speed.append(0.0)
            batch.append(SpawnActor(walker_bp, spawn_point))
        results = client.apply_batch_sync(batch, True)
        walker_speed2 = []
        for i in range(len(results)):
            if results[i].error:
                logging.error(results[i].error)
            else:
                walkers_list.append({"id": results[i].actor_id})
                walker_speed2.append(walker_speed[i])
        walker_speed = walker_speed2
        # 3. we spawn the walker controller
        batch = []
        walker_controller_bp = world.get_blueprint_library().find('controller.ai.walker')
        for i in range(len(walkers_list)):
            batch.append(SpawnActor(walker_controller_bp, carla.Transform(), walkers_list[i]["id"]))
        results = client.apply_batch_sync(batch, True)
        for i in range(len(results)):
            if results[i].error:
                logging.error(results[i].error)
            else:
                walkers_list[i]["con"] = results[i].actor_id
        # 4. we put together the walkers and controllers id to get the objects from their id
        for i in range(len(walkers_list)):
            all_id.append(walkers_list[i]["con"])
            all_id.append(walkers_list[i]["id"])
        all_actors = world.get_actors(all_id)

        # wait for a tick to ensure client receives the last transform of the walkers we have just created
        if args.asynch or not synchronous_master:
            world.wait_for_tick()
            
        else:
            world.tick()

        # 5. initialize each controller and set target to walk to (list is [controler, actor, controller, actor ...])
        # set how many pedestrians can cross the road
        world.set_pedestrians_cross_factor(percentagePedestriansCrossing)
        for i in range(0, len(all_id), 2):
            # start walker
            all_actors[i].start()
            # set walk to random point
            all_actors[i].go_to_location(world.get_random_location_from_navigation())
            # max speed
            all_actors[i].set_max_speed(float(walker_speed[int(i/2)]))
        print('spawned %d vehicles and %d walkers, press Ctrl+C to exit.' % (len(vehicles_list), len(walkers_list)))

        # Example of how to use Traffic Manager parameters
        traffic_manager.global_percentage_speed_difference(30.0)
        if args.save_to_file:
            doc = open(args.save_to_file, "w+")
            doc.write(client.show_recorder_file_info(args.recorder_filename, args.show_all))
            doc.close()
        else:
            print(client.show_recorder_file_info(args.recorder_filename, args.show_all))
        green_time = 10.0
        for semaforo in semaforos_na_area:
            semaforo.set_state(carla.TrafficLightState.Red)
        
        while True:
            world.tick()
            # Obter a lista de veículos no mundo
            vehicles = world.get_actors().filter('vehicle.*')    
            # Verificar se há veículos próximos ao semáforo
            vehicle_nearby = False

            
            for vehicle in vehicles:
                if vehicle.is_at_traffic_light():
                    semaforo_vehicle = carla.Vehicle.get_traffic_light(vehicle)  
                    semaforo_valido = False          
                    #print(semaforo_vehicle)
                    for semaforo in semaforos_na_area:
                        if semaforo_vehicle.id == semaforo.id:
                            print(semaforo_vehicle)
                            semaforo_valido = True
                    if semaforo_valido:
                        ha_semaforo_verde = False
                        for semaforo in semaforos_na_area:
                            if semaforo.id != semaforo_vehicle.id:
                                # Alternar todos os outros sinal vermelho
                                if semaforo.get_state() == carla.TrafficLightState.Green:
                                    ha_semaforo_verde = True  
                        #print(ha_semaforo_verde)
                        if not ha_semaforo_verde:                  
                            green_time += 5.0  # Aumentar o tempo de sinal verde                    
                            semaforo_vehicle.set_green_time(green_time)
                            semaforo_vehicle.set_state(carla.TrafficLightState.Green)
                            for semaforo in semaforos_na_area:
                            # Alternar todos os outros sinal vermelho
                                semaforo.set_state(carla.TrafficLightState.Red)
                               
                
                    

                
                


    finally:

        if not args.asynch and synchronous_master:
            settings = world.get_settings()
            settings.synchronous_mode = False
            settings.no_rendering_mode = False
            settings.fixed_delta_seconds = None
            world.apply_settings(settings)

        print('\ndestroying %d vehicles' % len(vehicles_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])

        # stop walker controllers (list is [controller, actor, controller, actor ...])
        for i in range(0, len(all_id), 2):
            all_actors[i].stop()

        print('\ndestroying %d walkers' % len(walkers_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in all_id])

        time.sleep(0.5)

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')