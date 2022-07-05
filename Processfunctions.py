""" 

Processfunctions.py 

This library is supposed to contain all functions which alter / process the data. This includes normalization, subtracting baseline, data augmentations

"""

# Import all of the requried libraries
import numpy as np
import SimpleITK as sitk
import matplotlib.pyplot as plt
import pandas as pd
# import statistics
from statistics import mode,mean
from scipy import interpolate


# Normalize peak instensity to 1.0
def normalize(data):
    temp = data.copy()
    if len(temp) > 1000:
        temp = (temp - min(temp))
        temp = temp/max(temp)
    else:
        for i in range(len(temp)):
            temp[i] = (temp[i] - min(temp[i]))
            temp[i] = temp[i]/max(temp[i])
    return temp
 
def subtractBaseline(data,baseline):
    temp = data.copy()
    for i in range(len(temp)):
        temp[i] = temp[i]-baseline
    return temp