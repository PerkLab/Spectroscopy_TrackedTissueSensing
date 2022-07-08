import numpy as np
# import pip
# pip.main(['install','pandas'])
import pandas as pd

folder = '../new_data/'
# Select the label and append it to the end of the 
label = 0
name = 'cork'
# This code is used to access a sequence from slicer and convert it to a numpy array to later export
seqNode  = slicer.mrmlScene.GetFirstNodeByName('Sequence')
# The sequence contains n data nodes
folder = 'C:/OpticalSpectroscopy_TissueClassification/new_data/testFolder/'
for idx in range(seqNode.GetNumberOfDataNodes()):
    volumeNode = seqNode.GetNthDataNode(idx)
    specArray = slicer.util.arrayFromVolume(volumeNode)
    specArray = np.squeeze(specArray)
    specArray = np.transpose(specArray)
    np.savetxt(folder + name + str(idx) + '.csv', specArray, delimiter=',')