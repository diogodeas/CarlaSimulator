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
    world = client.load_world('Town03', carla.MapLayer.Buildings | carla.MapLayer.ParkedVehicles)
    