import pickle
import numpy as np
import pandas as pd

with open("vehicle_position.pickle","rb") as f:
    vehicles_position = pickle.load(f)

with open("vehicle_velocity.pickle","rb") as f:
    vehicles_velocities = pickle.load(f)
    
df = pd.DataFrame()

for i, (position, velocity) in enumerate(zip(vehicles_position, vehicles_velocities)):
    veiculo_df = pd.DataFrame(position,columns=["P.x","P.y","P.z"])
    veiculo_df["V.x"] = pd.Series([v[0] for v in velocity])
    veiculo_df["V.y"] = pd.Series([v[1] for v in velocity])
    veiculo_df["V.z"] = pd.Series([v[2] for v in velocity])
    veiculo_df["V.Escalar"] = np.sqrt(veiculo_df["V.x"]**2+veiculo_df["V.y"]**2+veiculo_df["V.z"]**2)
    veiculo_df["veiculo"] = i
    veiculo_df["tempo"] = range(len(position))
    df = pd.concat([df,veiculo_df])


df.to_csv("vehicle_position.csv",index=False)
