from array import array
from calendar import SATURDAY
import logging
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import sklearn
import numpy as np
import os
try: 
  from joblib import load
except:
  slicer.util.pip_install('joblib')
  pass

try:
  import sklearn
except:
  slicer.util.pip_install('sklearn')
  pass

# This is a custom library which slicer doesnt recognize on startup
try:
  import Processfunctions as process
except:
  pass
# import IOfunctions as IO

# try:
#     import pyigtl
# except:
#     slicer.util.pip_install('pyigtl')
#     import pyigtl


#
# BroadbandSpecModule
#

class BroadbandSpecModule(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "BroadbandSpecModule"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Broadband"]
    self.parent.dependencies = []
    parent.contributors = ["David Morton (Queen's University, PERK Lab)"] 
    self.parent.helpText = """
    Module can display spectrum curve in real-time from a spectrum image received through OpenIGTLink. 
    First line of the spectrum image contains wavelength, 
    second line of the image contains intensities.
    Module also recieves 3D tracking data and plots the 3D position of each spectrum obtained.
    """
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
    """

#
# BroadbandSpecModuleWidget
#

class BroadbandSpecModuleWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False
    slicer.mymod = self # Used to access nodes in the python interactor

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/BroadbandSpecModule.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = BroadbandSpecModuleLogic()

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).

    # Setup
    self.ui.connectButton.connect('clicked(bool)', self.onConnectButtonClicked)
    self.ui.spectrumImageSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSpectrumImageChanged)
    self.ui.outputTableSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onOutputTableChanged)
    self.ui.modelFileSelector.connect('currentPathChanged(QString)', self.onModelFileSelectorChanged)
    self.ui.placeFiducialButton.connect('clicked(bool)', self.onPlaceFiducialButtonClicked)
    self.ui.enablePlottingButton.connect('clicked(bool)', self.setEnablePlotting)
    # Inference
    self.ui.scanButton.connect('clicked(bool)', self.onScanButtonClicked)
    self.ui.addControlPointButton.connect('clicked(bool)', self.onAddControlPointButtonClicked)
    self.ui.clearControlPointsButton.connect('clicked(bool)', self.onClearControlPointsButtonClicked)
    self.ui.clearLastPointButton.connect('clicked(bool)', self.onClearLastPointButtonClicked)
    # Data Collection
    self.ui.dataClassSelector.connect('currentIndexChanged(int)', self.onDataClassSelectorChanged)
    self.ui.saveLocationSelector.connect('currentPathChanged(QString)', self.onSaveLocationSelectorChanged)
    # add the options cancer and normal to the data class selector
    self.ui.dataClassSelector.addItem("Cancer")
    self.ui.dataClassSelector.addItem("Normal")
    self.ui.samplingDurationSlider.connect('valueChanged(double)', self.onSamplingDurationChanged)
    self.ui.samplingRateSlider.connect('valueChanged(double)', self.onSamplingRateChanged)
    self.ui.collectSampleButton.connect('clicked(bool)', self.onCollectSampleButtonClicked)
    self.ui.continuousCollectionButton.connect('clicked(bool)', self.onContinuousCollectionButtonClicked)
    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()

  # My functions
  def onContinuousCollectionButtonClicked(self):
    # if the button is checked, start collecting data
    if self.ui.continuousCollectionButton.isChecked():
      self.ui.continuousCollectionButton.setText("Stop Collection")
      self.logic.startDataCollection()
    # if the button is not checked, stop collecting data
    else:
      self.ui.continuousCollectionButton.setText("Start Continuous Collection")
      self.logic.stopDataCollection()

  def onDataClassSelectorChanged(self):
    self.updateParameterNodeFromGUI()
    parameterNode = self.logic.getParameterNode()
    dataClass = self.ui.dataClassSelector.currentText
    parameterNode.SetParameter(self.logic.DATA_CLASS, dataClass)

  def onSamplingDurationChanged(self):
    self.updateParameterNodeFromGUI()
    parameterNode = self.logic.getParameterNode()
    # sampleDuration = self.ui.sampleDurationSelector.currentText
    sampleDuration = self.ui.samplingDurationSlider.value
    parameterNode.SetParameter(self.logic.SAMPLING_DURATION, str(sampleDuration))

  def onSamplingRateChanged(self):
    self.updateParameterNodeFromGUI()
    parameterNode = self.logic.getParameterNode()
    # sampleRate = self.ui.samplePerSecondSelector.currentText
    sampleRate = self.ui.samplingRateSlider.value
    print("sample rate is: ", sampleRate)
    parameterNode.SetParameter(self.logic.SAMPLING_RATE, str(sampleRate))

  def onCollectSampleButtonClicked(self):
    self.updateParameterNodeFromGUI()
    self.logic.recordSample()

  def onConnectButtonClicked(self):
    '''
    This function creates the IGTL connection for the Spectrometer and the EMT 
    '''
    self.updateParameterNodeFromGUI()
    # Get parameter node
    parameterNode = self.logic.getParameterNode()
    # Get the connector node from the parameter node
    connectorNode = parameterNode.GetNodeReference(self.logic.CONNECTOR)
    # if the a connector node does not exist, create one
    if connectorNode == None:
      print('No connector node found, creating one')
      # Create a connector node
      connectorNode = slicer.vtkMRMLIGTLConnectorNode()
      # print(connectorNode)
      print(connectorNode.GetID())
      # Set the connector node name
      connectorNode.SetName('IGTLConnector_SpecEMT')
      # Add the connector node to the scene
      slicer.mrmlScene.AddNode(connectorNode) 
      connectorNode.SetTypeClient('localhost', 18944)
      connectorNode.Start()
      self.ui.connectButton.text = 'Disconnect'
      # Save the node ID to the parameter node
      parameterNode.SetNodeReferenceID(self.logic.CONNECTOR, connectorNode.GetID())
      print(connectorNode.GetID())
    # if connector node exists, update the text on the button
    else:
      if connectorNode.GetState() == 0:
        connectorNode.Start()
        print('Connector node started')
        self.ui.connectButton.text = 'Disconnect'
      else:
        connectorNode.Stop()
        print('Connector node stopped')
        self.ui.connectButton.text = 'Connect'

  def onSaveLocationSelectorChanged(self):
      self.updateParameterNodeFromGUI()
      # get path from the selector
      path = self.ui.saveLocationSelector.currentPath
      # get parameter node
      parameterNode = self.logic.getParameterNode()
      # set the path in the parameter node
      parameterNode.SetParameter(self.logic.SAVE_LOCATION, path)

  def onSpectrumImageChanged(self):
    self.updateParameterNodeFromGUI()

  def onOutputTableChanged(self):
    self.updateParameterNodeFromGUI()

  def onModelFileSelectorChanged(self):
    # Update the parameter node from the GUI
    self.updateParameterNodeFromGUI()
    # get the file from the modelFileSelector
    modelPath = self.ui.modelFileSelector.currentPath
    # update the parameter node with the new model path
    parameterNode = self.logic.getParameterNode()
    parameterNode.SetParameter(self.logic.MODEL_PATH, modelPath)
    print('Loading in model from path:', modelPath)
    if not (modelPath == ''): 
      self.logic.model = load(modelPath)

  def onPlaceFiducialButtonClicked(self):
    self.updateParameterNodeFromGUI()
    self.logic.placeFiducial()

  def setEnablePlotting(self, enable):
    self.updateParameterNodeFromGUI()
    if enable:
      # change the button text to 'Disable Plotting'
      self.ui.enablePlottingButton.text = 'Disable Plotting'
      self.logic.startPlotting()
    else:
      # change the button text to 'Enable Plotting'
      self.ui.enablePlottingButton.text = 'Enable Plotting'
      self.logic.stopPlotting()

  def onClearLastPointButtonClicked(self):
    self.updateParameterNodeFromGUI()
    # Check to see if the lists exist, and if not create them
    self.logic.setupLists()
    print("This button is not currently implemented")
    pass

  def onClearControlPointsButtonClicked(self):
    self.updateParameterNodeFromGUI()
    self.logic.clearControlPoints()

  def onAddControlPointButtonClicked(self):
    self.updateParameterNodeFromGUI()
    # Check to see if the lists exist, and if not create them
    self.logic.setupLists()
    self.logic.addControlPointToToolTip()

  def onScanButtonClicked(self, checked):
    self.updateParameterNodeFromGUI()
    if checked:
      self.logic.startScanning()
    else:
      self.logic.stopScanning()
    self.ui.scanButton.text = 'Scanning' if checked else 'Start Scanning'

  # Predefined functions
  
  def setParameterNode(self, inputParameterNode):
    """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    if self._parameterNode is not None:
      self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def initializeParameterNode(self):
    """
    Ensure parameter node exists and observed.
    """
    # Parameter node stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.
    self.setParameterNode(self.logic.getParameterNode())

    # Ensure the required lists are created and reference in the parameter node
    self.logic.setupLists()

    # Select default input nodes if nothing is selected yet to save a few clicks for the user
    if not self._parameterNode.GetNodeReference(self.logic.INPUT_VOLUME):
      firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode") # ***
      if firstVolumeNode:
        self._parameterNode.SetNodeReferenceID(self.logic.INPUT_VOLUME, firstVolumeNode.GetID())

    # If the output table does not exist, create one and select it
    if self._parameterNode.GetNodeReference(self.logic.OUTPUT_TABLE) is None:
      # a table node is not selected, create a new one
        firstTableNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLTableNode")
        firstTableNode.SetName('Table')
        slicer.mrmlScene.AddNode(firstTableNode)
        self._parameterNode.SetNodeReferenceID(self.logic.OUTPUT_TABLE, firstTableNode.GetID())

    # If no model path is selected, select the default one
    if self._parameterNode.GetNodeReference(self.logic.MODEL_PATH) is None:
      self._parameterNode.SetParameter(self.logic.MODEL_PATH, self.logic.DEFAULT_MODEL_PATH)

    # Add a default save location if none exists
    if self._parameterNode.GetNodeReference(self.logic.SAVE_LOCATION) is None:
      self._parameterNode.SetParameter(self.logic.SAVE_LOCATION, self.logic.DEFAULT_SAVE_LOCATION)

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    # It doesn't update if the paramater node is empty or is already updating the GUI
    if self._parameterNode is None or self._updatingGUIFromParameterNode: 
      return

    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True

    # Update node selectors
    self.ui.spectrumImageSelector.setCurrentNode(self._parameterNode.GetNodeReference(self.logic.INPUT_VOLUME))
    self.ui.outputTableSelector.setCurrentNode(self._parameterNode.GetNodeReference(self.logic.OUTPUT_TABLE))

    # Update buttons state
    nodeList = slicer.util.getNodesByClass('vtkMRMLIGTLConnectorNode') # ***
    if nodeList == []:
      pass
    else:
      connectorNode = nodeList[0]
      if connectorNode.GetState() == 0:
        self.ui.connectButton.text = 'Connect'
      else:
        self.ui.connectButton.text = 'Disconnect' 

    # Update the model path to be the last selection
    if self.ui.modelFileSelector.currentPath == '':
      # set the current path to whatever is stored in the parameter node
      self.ui.modelFileSelector.currentPath = self._parameterNode.GetParameter(self.logic.MODEL_PATH)

    # Update the save location to be the last selection
    if self.ui.saveLocationSelector.currentPath == '':
      # set the current path to whatever is stored in the parameter node
      self.ui.saveLocationSelector.currentPath = self._parameterNode.GetParameter(self.logic.SAVE_LOCATION)
  
    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    # Update Widget ParameterNode
    self._parameterNode.SetNodeReferenceID(self.logic.INPUT_VOLUME, self.ui.spectrumImageSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID(self.logic.OUTPUT_TABLE, self.ui.outputTableSelector.currentNodeID)
    
    # print('In updateParameterNodeFromGUI')
    parameterNode = self.logic.getParameterNode() # The parameter node is already linked to the GUI
    # update parameter node with the state of start scanning button
    parameterNode.SetParameter(self.logic.SCANNING_STATE, str(self.ui.scanButton.isChecked()))
    # update parameter node with the state of enable plotting button
    parameterNode.SetParameter(self.logic.PLOTTING_STATE, str(self.ui.enablePlottingButton.isChecked()))
    # update parameter node with the current path of the file selector
    parameterNode.SetParameter(self.logic.MODEL_PATH, self.ui.modelFileSelector.currentPath)
    # update parameter node with the current sampling duration and samplling rate
    parameterNode.SetParameter(self.logic.SAMPLING_DURATION, str(self.ui.samplingDurationSlider.value))
    parameterNode.SetParameter(self.logic.SAMPLING_RATE, str(self.ui.samplingRateSlider.value))

    self._parameterNode.EndModify(wasModified)
 
  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.logic.removeObservers()
  
  def enter(self):
    """
    Called each time the user opens this module.
    """
    # Make sure parameter node exists and observed
    self.initializeParameterNode()

  def exit(self):
    """
    Called each time the user opens a different module.
    """
    # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    # Parameter node will be reset, do not use it anymore
    self.setParameterNode(None)

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    # If this module is shown while the scene is closed then recreate a new parameter node immediately
    if self.parent.isEntered:
      self.initializeParameterNode()


#
# BroadbandSpecModuleLogic
#

class BroadbandSpecModuleLogic(ScriptedLoadableModuleLogic,VTKObservationMixin): # added the mixin class
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  # NAMES
  INPUT_VOLUME = "InputVolume"
  OUTPUT_TABLE = "OutputTable"
  MODEL_PATH = "ModelPath"
  CLASSIFICATION = "Classification"
  CLASS_LABEL_0 = "ClassLabel0"
  CLASS_LABEL_1 = "ClassLabel1"
  CLASS_LABEL_NONE = "WeakSignal"
  SCANNING_STATE = 'Scanning State'
  PLOTTING_STATE = 'Plotting State'
  CLICK_COUNT = 'Click Count'
  SAMPLING_DURATION = "Sample Duration"
  SAMPLING_RATE = "Sample Rate"
  DATA_CLASS = "Data Class"
  SAVE_LOCATION = 'Save Location'

  # ROLES
  POINTLIST_GREEN_WORLD = 'pointList_Green_World'
  POINTLIST_RED_WORLD = 'pointList_Red_World'
  POINTLIST_EMT = 'pointList_EMT'
  CONNECTOR = 'Connector'
  SAMPLE_SEQUENCE = 'SampleSequence'
  SAMPLE_SEQ_BROWSER = 'SampleSequenceBrowser'
  OUTPUT_SERIES = "OutputSeries"
  OUTPUT_CHART = "OutputChart"

  # Constants
  DISTANCE_THRESHOLD = 2 # in mm
  DEFAULT_SAVE_LOCATION = os.path.join('C:\Spectroscopy_TrackedTissueSensing\data', 'Nov2022_skinTestData')
  DEFAULT_MODEL_PATH = os.path.join('C:\Spectroscopy_TrackedTissueSensing\TrainedModels', 'KNN_WhiteVsBlue2.joblib')

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)
    self.observerTags = [] # This is reset when the module is reloaded. But not all observers are removed.
    # ###
    slicer.mymodLog = self
    # path = "C:\Spectroscopy_TrackedTissueSensing\Models/"
    # filename = "KNN_TestModel.joblib" 
    # filename = "KNN_BlueVsWhite.joblib" 
    # filename = "KNN_CardboardVsTeaBox.joblib" 
    # self.model = load(path + filename)
    self.model = None

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    if not parameterNode.GetParameter(self.CLASSIFICATION):
      parameterNode.SetParameter(self.CLASSIFICATION, '')
    # if the self.model path is not set, grab it from the ctkPathLineEdit widget
    if parameterNode.GetParameter(self.MODEL_PATH) == '':
      parameterNode.SetParameter(self.MODEL_PATH, 'C:/Spectroscopy_TrackedTissueSensing/TrainedModels/KNN_PorkVsBeefTest.joblib') # Hardcoded path
    # print("Model path1: " + parameterNode.GetParameter(self.MODEL_PATH))
    # print(self.model)
    if self.model == None:
      # parameterNode = self.getParameterNode()
      modelPath = parameterNode.GetParameter(self.MODEL_PATH)
      # print("Model path2: " + parameterNode.GetParameter(self.MODEL_PATH))
      self.model = load(modelPath)

    if not parameterNode.GetParameter("Threshold"):
      parameterNode.SetParameter("Threshold", "100.0")
    if not parameterNode.GetParameter("Invert"):
      parameterNode.SetParameter("Invert", "false")

  def process(self, inputVolume, outputTable, imageThreshold, invert=False, showResult=True):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputTable: thresholding result
    :param imageThreshold: values above/below this threshold will be set to 0
    :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    :param showResult: show output volume in slice viewers
    """

    if not inputVolume or not outputTable:
      raise ValueError("Input or output volume is invalid")

    import time
    startTime = time.time()
    logging.info('Processing started')

    # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
    cliParams = {
      self.INPUT_VOLUME: inputVolume.GetID(),
      self.OUTPUT_TABLE: outputTable.GetID(),
      'ThresholdValue' : imageThreshold,
      'ThresholdType' : 'Above' if invert else 'Below'
      }
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
    # We don't need the CLI module node anymore, remove it to not clutter the scene with it
    slicer.mrmlScene.RemoveNode(cliNode)

    stopTime = time.time()
    logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')

  def addObservers(self):
    parameterNode = self.getParameterNode()
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    if spectrumImageNode:
      # print("Add observer to {0}".format(spectrumImageNode.GetName()))
      self.observerTags.append([spectrumImageNode, spectrumImageNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onSpectrumImageNodeModified)])

  def removeObservers(self):
    for nodeTagPair in self.observerTags:
      nodeTagPair[0].RemoveObserver(nodeTagPair[1])

  def placeFiducial(self):
    """
    Place a fiducial at the tool tip.
    """
    parameterNode = self.getParameterNode()
    pointListGreen_World = parameterNode.GetNodeReference(self.POINTLIST_GREEN_WORLD)
    pointList_EMT = parameterNode.GetNodeReference(self.POINTLIST_EMT)
    # The the tip of the probe in world coordinates
    pos = [0,0,0]
    pointList_EMT.GetNthControlPointPositionWorld(0,pos)
    tip_World = pos
    pointListGreen_World.AddControlPoint(tip_World)
    pointListGreen_World.SetNthControlPointLabel(pointListGreen_World.GetNumberOfControlPoints()-1, '')

  def clearControlPoints(self):
    """
    Clear all control points from the point lists.
    """
    # Check to see if the lists exist, and if not create them
    self.setupLists()
    parameterNode = self.getParameterNode()
    # *** this should be done from parameter node
    pointListGreen_World = parameterNode.GetNodeReference(self.POINTLIST_GREEN_WORLD)
    pointListRed_World = parameterNode.GetNodeReference(self.POINTLIST_RED_WORLD)
    pointListGreen_World.RemoveAllMarkups()
    pointListRed_World.RemoveAllMarkups()

  def startPlotting(self):
    print("Start plotting")
    # Change the layout to one that has a chart.
    ln = slicer.util.getNode(pattern='vtkMRMLLayoutNode*')
    ln.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalPlotView)
    # Make sure there aren't already observers
    self.removeObservers()  
    # Start the updates
    self.addObservers()
    self.onSpectrumImageNodeModified(0,0)

  def stopPlotting(self):
    print("Stopped plotting")
    # Set layout to conventional widescreen
    ln = slicer.util.getNode(pattern='vtkMRMLLayoutNode*')
    # ln.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalPlotView)
    # ln.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
    # set view to conventional
    ln.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalView)
    self.removeObservers()  

  def startScanning(self):
    print('Scanning')
    pass

  def stopScanning(self):
    print('Stopping Scanning')
    pass

  def recordSample(self):
    '''
    This function will record an N second sample of spectral data, it then calls saveSample to save the data to a csv file.

    NOTE:
    There is a browser and a sequence
    SetPlayback
    SetRecordingActive  
    The goal is to create a a sequencec of spectra using the sequence browser over 1 section and then save it to a csv
    self = slicer.mymodLog
    parameterNode = self.getParameterNode()
    seqBrowserNode.RemoveAllProxyNodes()
    image.EndModify(0) # when the second seq is created I think it modifys the first and then the second is ended. When things stop modifying call this. 
    '''
    # Load in the parameters
    parameterNode = self.getParameterNode()
    sampleDuration = parameterNode.GetParameter(self.SAMPLING_DURATION)
    sampleFrequency = parameterNode.GetParameter(self.SAMPLING_RATE)
    image_imageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    browserNode = parameterNode.GetNodeReference(self.SAMPLE_SEQ_BROWSER)
    # Print Collecting sample and the data collection parameters
    print('Collecting sample')
    print('Sample duration: ' + sampleDuration)
    print('Sample frequency: ' + sampleFrequency)
    if browserNode == None:
      browserNode = slicer.vtkMRMLSequenceBrowserNode()
      slicer.mrmlScene.AddNode(browserNode)
      browserNode.SetName("SampleSequenceBrowser")
      parameterNode.SetNodeReferenceID(self.SAMPLE_SEQ_BROWSER, browserNode.GetID())
    # Check to see if our sequence node exists yet
    if parameterNode.GetNodeReferenceID(self.SAMPLE_SEQUENCE) is None:
      sequenceLogic = slicer.modules.sequences.logic()
      sequenceNode = sequenceLogic.AddSynchronizedNode(None, image_imageNode, browserNode) # Check doc on AddSynchronizedNode to see if there is another way.
      parameterNode.SetNodeReferenceID(self.SAMPLE_SEQUENCE, sequenceNode.GetID())
    sequenceNode = parameterNode.GetNodeReference(self.SAMPLE_SEQUENCE)
    # Clear the sequence node of previous data
    sequenceNode.RemoveAllDataNodes()
    # Initalize the sequence node parameters
    browserNode.SetRecording(sequenceNode, True)
    browserNode.SetPlayback(sequenceNode, True)
    browserNode.SetPlaybackRateFps(float(sampleFrequency))
    # Start the recording
    browserNode.SetRecordingActive(True)
    timer = qt.QTimer()
    # NOTE: singleShot will proceed with the next lines of code before the timer is done
    # Call a singleShot to stop the recording after the sample duration
    timer.singleShot(float(sampleDuration)*1000, lambda: browserNode.SetRecordingActive(False))
    # Save the sample slightly after the recording is stopped
    timer.singleShot(float(sampleDuration)*1000+50, lambda: self.saveSample())

  def startDataCollection(self):
    # Load in the parameters
    parameterNode = self.getParameterNode()
    sampleFrequency = parameterNode.GetParameter(self.SAMPLING_RATE)
    image_imageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    browserNode = parameterNode.GetNodeReference(self.SAMPLE_SEQ_BROWSER)
    # Print Collecting sample and the data collection parameters
    print('Starting Collection')
    print('Sample frequency: ' + sampleFrequency)
    if browserNode == None:
      browserNode = slicer.vtkMRMLSequenceBrowserNode()
      slicer.mrmlScene.AddNode(browserNode)
      browserNode.SetName("SampleSequenceBrowser")
      parameterNode.SetNodeReferenceID(self.SAMPLE_SEQ_BROWSER, browserNode.GetID())
    # Check to see if our sequence node exists yet
    if parameterNode.GetNodeReferenceID(self.SAMPLE_SEQUENCE) is None:
      sequenceLogic = slicer.modules.sequences.logic()
      sequenceNode = sequenceLogic.AddSynchronizedNode(None, image_imageNode, browserNode) # Check doc on AddSynchronizedNode to see if there is another way.
      parameterNode.SetNodeReferenceID(self.SAMPLE_SEQUENCE, sequenceNode.GetID())
    sequenceNode = parameterNode.GetNodeReference(self.SAMPLE_SEQUENCE)
    # Clear the sequence node of previous data
    sequenceNode.RemoveAllDataNodes()
    # Initalize the sequence node parameters
    browserNode.SetRecording(sequenceNode, True)
    browserNode.SetPlayback(sequenceNode, True)
    browserNode.SetPlaybackRateFps(float(sampleFrequency))
    # Start the recording
    browserNode.SetRecordingActive(True)
    pass

  def stopDataCollection(self):
    print('Stopping Collection')
    # Load in the parameters
    parameterNode = self.getParameterNode()
    browserNode = parameterNode.GetNodeReference(self.SAMPLE_SEQ_BROWSER)
    # Stop the recording
    browserNode.SetRecordingActive(False)
    # Save the sample to csv
    self.saveSample()
    pass

  def saveSample(self):
    '''
    Saves the data stored in the SampleSequenceBrowse to a single csv file
    '''
    # get parameters
    parameterNode = self.getParameterNode()
    dataLabel = parameterNode.GetParameter(self.DATA_CLASS)
    sampleDuration = parameterNode.GetParameter(self.SAMPLING_DURATION)
    # Stop the timer
    browserNode = parameterNode.GetNodeReference(self.SAMPLE_SEQ_BROWSER)
    # browserNode.SetRecordingActive(False)
    print("Recording stopped")
    # Get the sequence node
    sequenceNode = parameterNode.GetNodeReference(self.SAMPLE_SEQUENCE)
    # Save the sequence to a csv
    savePath = parameterNode.GetParameter(self.SAVE_LOCATION)
    savePath = os.path.join(savePath, dataLabel)
    # Loop through the sequence
    sequenceLength = sequenceNode.GetNumberOfDataNodes()

    # Check to see if any data has been recorded
    if sequenceLength == 0:
      print("No data to save")
      return

    print(sequenceLength)
    # Format the empty array
    # Get the length of a spectrum
    spectrumArray = slicer.util.arrayFromVolume(sequenceNode.GetNthDataNode(0))
    SpectrumLength = spectrumArray.shape[2]
    # Create the 2D array
    spectrumArray2D = np.zeros((sequenceLength + 1, SpectrumLength + 1))
    # Fill the 2D array
    # create a time vector using the sampleDuration
    timeVector = np.linspace(0, float(sampleDuration), sequenceLength)
    # concatenate the time vector to the spectrum array
    spectrumArray2D[1:,0] = timeVector
    # print shape of the array
    print(spectrumArray2D.shape)
    for i in range(sequenceLength):
      # Get a spectrum as an array
      spectrumArray = np.squeeze(slicer.util.arrayFromVolume(sequenceNode.GetNthDataNode(i)))
      spectrumArray2D[i+1,1:] = spectrumArray[1,:]
    # Save the array to a csv
    clickCount = parameterNode.GetParameter(self.CLICK_COUNT)
    # np.savetxt(savePath + clickCount + '.csv', spectrumArray2D[1:,:], delimiter=",")
    np.savetxt(savePath + '.csv', spectrumArray2D[1:,:], delimiter=",")

  def addControlPointToToolTip(self):
    # Get the required nodes
    parameterNode = self.getParameterNode()
    pointListGreen_World = parameterNode.GetNodeReference(self.POINTLIST_GREEN_WORLD)
    pointListRed_World = parameterNode.GetNodeReference(self.POINTLIST_RED_WORLD)
    pointList_EMT = parameterNode.GetNodeReference(self.POINTLIST_EMT)

    # The the tip of the probe in world coordinates
    pos = [0,0,0]
    pointList_EMT.GetNthControlPointPositionWorld(0,pos)
    tip_World = pos
    # print("Tip World: ", tip_World)
    # Add control point at tip of probe based on classification
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    # Convert image to volume 
    specArray = slicer.util.arrayFromVolume(spectrumImageNode)
    specArray = np.squeeze(specArray)
    specArray = np.transpose(specArray)
    self.classifySpectra(specArray[743:-1,:]) # Magic Number ** Also this is very slow to compute
    spectrumLabel = parameterNode.GetParameter(self.CLASSIFICATION)

    if spectrumLabel == self.CLASS_LABEL_0:
      pointListGreen_World.AddControlPoint(tip_World)
      # set label of the control point to ''
      pointListGreen_World.SetNthControlPointLabel(pointListGreen_World.GetNumberOfControlPoints()-1, '')
      # parameterNode.SetParameter('LastPointAdded', self.logic.CLASS_LABEL_0)
    elif spectrumLabel == self.CLASS_LABEL_1:
      pointListRed_World.AddControlPoint(tip_World)
      pointListRed_World.SetNthControlPointLabel(pointListRed_World.GetNumberOfControlPoints()-1, '')
      # parameterNode.SetParameter('LastPointAdded', self.logic.CLASS_LABEL_1)
    pass

  def onSpectrumImageNodeModified(self, observer, eventid):
    self.setupLists()
    # print("Spectrum Image Node Modified")
    parameterNode = self.getParameterNode()
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    outputTableNode = parameterNode.GetNodeReference(self.OUTPUT_TABLE)
    
    if not spectrumImageNode or not outputTableNode:
      return

    # If the enable plotting button is checked
    if parameterNode.GetParameter(self.PLOTTING_STATE) == "True":
      spectrumArray = self.updateOutputTable()
      self.classifySpectra(spectrumArray[743:-1,:]) # Magic Number **
      self.updateChart()
      pass

    # If the enable scanning button is checked
    if parameterNode.GetParameter(self.SCANNING_STATE) == "True":
      pointListGreen_World = parameterNode.GetNodeReference(self.POINTLIST_GREEN_WORLD)
      pointListRed_World = parameterNode.GetNodeReference(self.POINTLIST_RED_WORLD)
      # if the red and green point lists are both empty
      if pointListRed_World.GetNumberOfControlPoints() == 0 and pointListGreen_World.GetNumberOfControlPoints() == 0:
        self.addControlPointToToolTip()
        pass
      # Else check the distance beween the last control point and the tip of the probe
      else:
        # The the tip of the probe in world coordinates
        pos = [0,0,0]
        pointList_EMT = parameterNode.GetNodeReference(self.POINTLIST_EMT)
        pointList_EMT.GetNthControlPointPositionWorld(0,pos)
        tip_World = pos
            
        # Get the last control point of green in world coordinates
        pos = [0,0,0]
        pointListGreen_World.GetNthControlPointPositionWorld(pointListGreen_World.GetNumberOfControlPoints()-1,pos)
        lastPointGreen_World = pos
        # Get the last control point of red in world coordinates
        pos = [0,0,0]
        pointListRed_World.GetNthControlPointPositionWorld(pointListRed_World.GetNumberOfControlPoints()-1,pos)
        lastPointRed_World = pos

        # Get the distance between the tip and the last control point
        distanceRed = np.linalg.norm(np.subtract(tip_World, lastPointGreen_World))
        distanceGreen = np.linalg.norm(np.subtract(tip_World, lastPointRed_World))
        # If both distances are greater than the threshold, add a new control point
        self.Distance_Threshold = 1
        # print("Distance Red: {0}".format(distanceRed))
        if distanceRed > self.DISTANCE_THRESHOLD and distanceGreen > self.DISTANCE_THRESHOLD:
          self.addControlPointToToolTip()
          pass
 
  def setupLists(self):
      '''
      This function is used to create the point lists if they're not present.
      '''
      # get the parameter node
      parameterNode = self.getParameterNode()

      # Check to see if role pointListGreen_World is present
      if parameterNode.GetNodeReference(self.POINTLIST_GREEN_WORLD) == None:
        # Create a point list for the green points in world coordinates
        pointListGreen_World = slicer.vtkMRMLMarkupsFiducialNode()
        pointListGreen_World.SetName("pointListGreen_World")
        slicer.mrmlScene.AddNode(pointListGreen_World)
        # Set the color of the points to green
        pointListGreen_World.GetDisplayNode().SetSelectedColor(0,1,0)
        # Set the role of the point list
        parameterNode.SetNodeReferenceID(self.POINTLIST_GREEN_WORLD, pointListGreen_World.GetID())

      # Check to see if role pointListRed_World is present
      if parameterNode.GetNodeReference(self.POINTLIST_RED_WORLD) == None:
        # Create a point list for the red points in world coordinates
        pointListRed_World = slicer.vtkMRMLMarkupsFiducialNode()
        pointListRed_World.SetName("pointListRed_World")
        slicer.mrmlScene.AddNode(pointListRed_World)
        # Set the color of the points to red
        pointListRed_World.GetDisplayNode().SetSelectedColor(1,0,0)
        # Set the role of the point list
        parameterNode.SetNodeReferenceID(self.POINTLIST_RED_WORLD, pointListRed_World.GetID())

      # Check to see if role pointList_EMT is present
      if parameterNode.GetNodeReference(self.POINTLIST_EMT) == None:
        # Create a point list for the endoscope tip in reference coordinates
        pointList_EMT = slicer.vtkMRMLMarkupsFiducialNode()
        pointList_EMT.SetName("pointList_EMT")
        slicer.mrmlScene.AddNode(pointList_EMT)
        # Set the role of the point list
        parameterNode.SetNodeReferenceID(self.POINTLIST_EMT, pointList_EMT.GetID())

      # If the point list for EMT is empty, add a point to the origin
      pointList_EMT = parameterNode.GetNodeReference(self.POINTLIST_EMT)
      if pointList_EMT.GetNumberOfControlPoints() == 0:
        pointList_EMT.AddControlPoint(np.array([0, 0, 0]))
        pointList_EMT.SetNthControlPointLabel(0, "origin_Tip")
      # move pointList_EMT to the ProbeTiptoProbe transform
      pass
  
  def updateOutputTable(self):
    # Get the table created by the selector
    parameterNode = self.getParameterNode()
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    tableNode = parameterNode.GetNodeReference(self.OUTPUT_TABLE)

    # Throw an error if the image has improper dimensions
    numberOfPoints = spectrumImageNode.GetImageData().GetDimensions()[0]
    numberOfRows = spectrumImageNode.GetImageData().GetDimensions()[1]
    if numberOfRows!=2:
      logging.error("Spectrum image is expected to have exactly 2 rows, got {0}".format(numberOfRows))
      return

    # Convert image to a displayable format
    specArray = slicer.util.arrayFromVolume(spectrumImageNode)
    specArray = np.squeeze(specArray)
    specArray = np.transpose(specArray)

    # Save results to a new table node
    if tableNode is None:
      tableNode = slicer.vtkMRMLTableNode()
      slicer.mrmlScene.AddNode(tableNode)
      # Name the table
      tableNode.SetName("OutputTable")
      parameterNode.SetNodeReferenceID(self.OUTPUT_TABLE, tableNode.GetID())
    # if slicer.util.getNodesByClass('vtkMRMLTableNode') == []: # ***
    #   tableNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
    slicer.util.updateTableFromArray(tableNode,specArray,["Wavelength","Intensity"])

    return specArray # *** Instead of returning the array, should I just save it to the parameter node?
    
  def updateChart(self):
    ''' Update the display chart using the the given spectra and classification '''
    # specPred, specLabel = self.classifySpectra(specArray[743:-1,:]) 
    parameterNode = self.getParameterNode()
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    tableNode = parameterNode.GetNodeReference(self.OUTPUT_TABLE)
    spectrumLabel = parameterNode.GetParameter(self.CLASSIFICATION)

    # Create PlotSeriesNode for the spectra
    plotSeriesNode = parameterNode.GetNodeReference(self.OUTPUT_SERIES)
    # If the plotSeriesNode does not exists then create it, set the role and set default properties
    if plotSeriesNode == None:
      plotSeriesNode = slicer.vtkMRMLPlotSeriesNode()
      slicer.mrmlScene.AddNode(plotSeriesNode)
      #plotSeriesNode.SetName(spectrumImageNode.GetName() + " plot")
      plotSeriesNode.SetName("Measured Spectrum")
      parameterNode.SetNodeReferenceID(self.OUTPUT_SERIES, plotSeriesNode.GetID())
      plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
      plotSeriesNode.SetXColumnName("Wavelength")
      plotSeriesNode.SetYColumnName("Intensity")
      plotSeriesNode.SetPlotType(plotSeriesNode.PlotTypeScatter)
      plotSeriesNode.SetColor(0, 0.6, 1.0)

    #Create PlotChartNode for the spectra
    plotChartNode = parameterNode.GetNodeReference(self.OUTPUT_CHART)
    # Create chart and add plot
    if plotChartNode == None:
      plotChartNode = slicer.vtkMRMLPlotChartNode()
      slicer.mrmlScene.AddNode(plotChartNode)
      parameterNode.SetNodeReferenceID(self.OUTPUT_CHART, plotChartNode.GetID())

      plotChartNode.SetAndObservePlotSeriesNodeID(plotSeriesNode.GetID())
      plotChartNode.YAxisRangeAutoOn() # The axes can be set or automatic by toggling between on and off
      # plotChartNode.SetYAxisRange(0, 2)
      plotChartNode.SetXAxisTitle('Wavelength [nm]')
      plotChartNode.SetYAxisTitle('Intensity')  
    plotChartNode.SetTitle(str(spectrumLabel)+" detected")
    # Show plot in layout
    slicer.modules.plots.logic().ShowChartInLayout(plotChartNode)

  def classifySpectra(self,X_test):
    # Get the max value in X_test to see if we will classify or not
    max_value = np.amax(X_test[:,1])
    # # Subtract the baseline from the data
    # path = 'C:/Spectroscopy_TrackedTissueSensing/raw_data/'
    # file_name = 'white_baseline.csv'
    # baseline_pap = IO.loadSpectrum(path, file_name, 'Wavelength', start_index=774)
    # baseline = baseline_pap[:-1,:]
    # baseline = process.normalize(baseline)[:,1] 
    
    # X_test = process.normalize(X_test)
    # X_test[:,1] = X_test[:,1] - baseline

    X_test = process.normalize(X_test)
    X_test = X_test[:,1].reshape(1,-1)
    predicted = self.model.predict(X_test)
    # To ensure a strong, unsaturated signal
    if max_value < 0.1 or max_value > 9.95:
      label = self.CLASS_LABEL_NONE
    elif predicted[0] == 0:
      label = self.CLASS_LABEL_0
    elif predicted[0] == 1:
      label = self.CLASS_LABEL_1
    # Save the prediction to the parameter node
    parameterNode = self.getParameterNode()
    parameterNode.SetParameter(self.CLASSIFICATION, label)
    return predicted, label
  

#
# BroadbandSpecModuleTest
#

class BroadbandSpecModuleTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_BroadbandSpecModule1()

  def test_BroadbandSpecModule1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    registerSampleData()
    inputVolume = SampleData.downloadSample('BroadbandSpecModule1')
    self.delayDisplay('Loaded test data set')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 695)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    threshold = 100

    # Test the module logic

    logic = BroadbandSpecModuleLogic()

    # Test algorithm with non-inverted threshold
    logic.process(inputVolume, outputVolume, threshold, True)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], threshold)

    # Test algorithm with inverted threshold
    logic.process(inputVolume, outputVolume, threshold, False)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], inputScalarRange[1])

    self.delayDisplay('Test passed')
