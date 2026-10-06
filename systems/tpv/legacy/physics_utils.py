import numpy as np
from TPVconfig import TPVconfig 


def wien_displacement(temp: float, constant: float = 2898e-6 ) ->float:

    return constant/temp
    

def radiant_exitance(temp: float, sigma: float = 5.670373e-8):
    return sigma * (temp**4)

def steradian_power(temp: float):
    M = radiant_exitance(temp)
    return M/np.pi

