import pickle
import pandas as pd

with open("vehicle_position.pickle","rb") as f:
    vehicles_position = pickle.load(f)

df = pd.DataFrame()

for i, position in enumerate(vehicles_position):
    veiculo_df = pd.DataFrame(position,columns=["x","y","z"])
    veiculo_df["veiculo"] = i
    veiculo_df["tempo"] = range(len(position))
    df = pd.concat([df,veiculo_df])

df.to_csv("vehicle_position.csv",index=False)
