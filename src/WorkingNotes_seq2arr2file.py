import numpy as np
# import pip
# pip.main(['install','pandas'])
import pandas as pd


# This code is used to access a sequence from slicer and convert it to a numpy array to later export
seqNode  = slicer.mrmlScene.GetFirstNodeByName('Sequence')
# The sequence contains n data nodes, in this first case 44 of them
arr_list = []
for idx in range(seqNode.GetNumberOfDataNodes()): # 0 to 43
    volumeNode = seqNode.GetNthDataNode(idx)
    specArray = slicer.util.arrayFromVolume(volumeNode)
    specArray = np.squeeze(specArray)
    specArray = np.transpose(specArray)
    arr_list.append(specArray)
# convert the list to array format    
output = np.array(arr_list)
#add a column for the label (0 for table 1 for cork)

#save the array to the file
#fileName = 'testFile'
#pd.DataFrame(output).to_csv(fileName + '.csv')
#np.save(fileName, output)