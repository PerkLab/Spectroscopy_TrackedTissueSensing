import logging
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import sklearn
import numpy as np
# This is a custom library which slicer doesnt recognize on startup
try: 
  from joblib import load
except:
  slicer.util.pip_install('joblib')
  pass

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
    self.ui.connectButton.connect('clicked(bool)', self.onConnectButtonClicked)
    self.ui.spectrumImageSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSpectrumImageChanged)
    self.ui.outputTableSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onOutputTableChanged)
    self.ui.modelFileSelector.connect('currentPathChanged(QString)', self.onModelFileSelectorChanged)
    self.ui.placeFiducialButton.connect('clicked(bool)', self.onPlaceFiducialButtonClicked)

    self.ui.enablePlottingButton.connect('clicked(bool)', self.setEnablePlotting)
    self.ui.scanButton.connect('clicked(bool)', self.onScanButtonClicked)
    self.ui.addControlPointButton.connect('clicked(bool)', self.onAddControlPointButtonClicked)
    self.ui.clearControlPointsButton.connect('clicked(bool)', self.onClearControlPointsButtonClicked)
    self.ui.clearLastPointButton.connect('clicked(bool)', self.onClearLastPointButtonClicked)
    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()

  # My functions

  def onConnectButtonClicked(self):
    '''
    This function creates the IGTL connection for the Spectrometer and the EMT 
    '''
    self.updateParameterNodeFromGUI()
    nodeList = slicer.util.getNodesByClass('vtkMRMLIGTLConnectorNode') 
    if nodeList == []: # if there are no nodes, create one for each device
      connectorNode_Spec = slicer.vtkMRMLIGTLConnectorNode()
      connectorNode_Spec.SetName('IGTLConnector_Spec')
      connectorNode_EMT = slicer.vtkMRMLIGTLConnectorNode()
      connectorNode_EMT.SetName('IGTLConnector_EMT')
      slicer.mrmlScene.AddNode(connectorNode_Spec)
      slicer.mrmlScene.AddNode(connectorNode_EMT)
      connectorNode_Spec.SetTypeClient('localhost', 18944)
      connectorNode_EMT.SetTypeClient('localhost', 18945)
      connectorNode_Spec.Start()
      connectorNode_EMT.Start()
      self.ui.connectButton.text = 'Disconnect'
    else:
      connectorNode_Spec = nodeList[0]
      connectorNode_EMT = nodeList[1]
      if connectorNode_Spec.GetState() == 0:
        connectorNode_Spec.Start()
        connectorNode_EMT.Start()
        self.ui.connectButton.text = 'Disconnect'
      else:
        connectorNode_Spec.Stop()
        connectorNode_EMT.Stop()
        self.ui.connectButton.text = 'Connect' 

  def onSpectrumImageChanged(self):
    self.updateParameterNodeFromGUI()

  def onOutputTableChanged(self):
    self.updateParameterNodeFromGUI()

  def onModelFileSelectorChanged(self):
    # Uparate the parameter node from the GUI
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
    self.setupLists()

    pointListGreen_World = slicer.mrmlScene.GetFirstNodeByName("pointListGreen_World")
    pointListRed_World = slicer.mrmlScene.GetFirstNodeByName("pointListRed_World")
    parameterNode = self.logic.getParameterNode()
    # lastPointClass = parameterNode.GetParameter('LastPointAdded')
    # if lastPointClass == self.logic.CLASS_LABEL_0:
    #   # remove the Nth control point
    #   pointListGreen_World.RemoveNthControlPoint(pointListGreen_World.GetNumberOfControlPoints()-1)
    # elif lastPointClass == self.logic.CLASS_LABEL_1:
    #   pointListRed_World.RemoveNthControlPoint(pointListRed_World.GetNumberOfControlPoints()-1)
    pass

  def onClearControlPointsButtonClicked(self):
    self.updateParameterNodeFromGUI()
    # Check to see if the lists exist, and if not create them
    self.logic.setupLists()
    pointListGreen_World = slicer.mrmlScene.GetFirstNodeByName("pointListGreen_World")
    pointListRed_World = slicer.mrmlScene.GetFirstNodeByName("pointListRed_World")
    pointListGreen_World.RemoveAllMarkups()
    pointListRed_World.RemoveAllMarkups()

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

    # Select default input nodes if nothing is selected yet to save a few clicks for the user
    if not self._parameterNode.GetNodeReference(self.logic.INPUT_VOLUME):
      firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
      if firstVolumeNode:
        self._parameterNode.SetNodeReferenceID(self.logic.INPUT_VOLUME, firstVolumeNode.GetID())

    # If no table selection exists, create one and select it
    if not self._parameterNode.GetNodeReference(self.logic.OUTPUT_TABLE):
      # if a table node is not selected, create a new one
      firstTableNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLTableNode")
      if not firstTableNode:
        firstTableNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLTableNode")
        firstTableNode.SetName('Table')
        slicer.mrmlScene.AddNode(firstTableNode)
      if firstTableNode:
        self._parameterNode.SetNodeReferenceID(self.logic.OUTPUT_TABLE, firstTableNode.GetID())

    # If no model path is selected, select the default one
    if not self._parameterNode.GetNodeReference(self.logic.MODEL_PATH):
      defaultModelPath = 'C:/OpticalSpectroscopy_TissueClassification/Models/KNN_WhiteVsBlue2.joblib' # Hardcoded path
      self._parameterNode.SetParameter(self.logic.MODEL_PATH, defaultModelPath)

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
    nodeList = slicer.util.getNodesByClass('vtkMRMLIGTLConnectorNode') 
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
  INPUT_VOLUME = "InputVolume"
  OUTPUT_TABLE = "OutputTable"
  CLASSIFICATION = "Classification"
  MODEL_PATH = "ModelPath"
  CLASS_LABEL_0 = "ClassLabel0"
  CLASS_LABEL_1 = "ClassLabel1"
  CLASS_LABEL_NONE = "WeakSignal"
  SCANNING_STATE = 'Scanning State'
  PLOTTING_STATE = 'Plotting State'
  DISTANCE_THRESHOLD = 2 # in mm

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)
    self.observerTags = [] # This is reset when the module is reloaded. But not all observers are removed.
    # ###
    slicer.mymodLog = self
    # path = "C:\OpticalSpectroscopy_TissueClassification\Models/"
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
      parameterNode.SetParameter(self.MODEL_PATH, 'C:/OpticalSpectroscopy_TissueClassification/Models/KNN_TestModel.joblib') # Hardcoded path
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
    pointListGreen_World = slicer.mrmlScene.GetFirstNodeByName("pointListGreen_World")
    pointList_EMT = slicer.mrmlScene.GetFirstNodeByName("pointList_EMT")

    # The the tip of the probe in world coordinates
    pos = [0,0,0]
    pointList_EMT.GetNthControlPointPositionWorld(0,pos)
    tip_World = pos
    pointListGreen_World.AddControlPoint(tip_World)
    pointListGreen_World.SetNthControlPointLabel(pointListRed_World.GetNumberOfControlPoints()-1, '')

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
    ln.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalPlotView)
    # ln.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
    self.removeObservers()  

  def startScanning(self):
    print('Scanning')
    pass

  def stopScanning(self):
    print('Stopping Scanning')
    pass

  def addControlPointToToolTip(self):
    # Get the required nodes
    pointListGreen_World = slicer.mrmlScene.GetFirstNodeByName("pointListGreen_World")
    pointListRed_World = slicer.mrmlScene.GetFirstNodeByName("pointListRed_World")
    pointList_EMT = slicer.mrmlScene.GetFirstNodeByName("pointList_EMT")

    # The the tip of the probe in world coordinates
    pos = [0,0,0]
    pointList_EMT.GetNthControlPointPositionWorld(0,pos)
    tip_World = pos
    '''
    # # Get the tip of the probe in the reference frame coordinates
    # ProbeTipToProbe = slicer.mrmlScene.GetFirstNodeByName("ProbeTiptoProbe")
    # ProbeToTracker = slicer.mrmlScene.GetFirstNodeByName("ProbeToTracker")
    # TrackerToReference = slicer.mrmlScene.GetFirstNodeByName("ReferenceToTracker (-)")
    # probeTip_ProbeTip = [0,0,0,0]
    # print("probeTip_ProbeTip: " + str(probeTip_ProbeTip))
    # probeTip_Probe = ProbeTipToProbe.GetMatrixTransformToParent().MultiplyPoint(probeTip_ProbeTip)
    # print("probeTip_Probe: " + str(probeTip_Probe))
    # probeTip_Tracker = ProbeToTracker.GetMatrixTransformToParent().MultiplyPoint(probeTip_Probe)
    # print("ProbeTip_Tracker: " + str(probeTip_Tracker))
    # probeTip_Reference = TrackerToReference.GetMatrixTransformToParent().MultiplyPoint(probeTip_Tracker)
    # print("ProbeTip_Reference: " + str(probeTip_Reference))
    # tip_World = probeTip_Reference[:-1]
    '''
    # Add control point at tip of probe based on classification
    parameterNode = self.getParameterNode()
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

  def onSpectrumImageNodeModified(self, observer, eventid):
    self.setupLists()
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
      pointListGreen_World = slicer.mrmlScene.GetFirstNodeByName("pointListGreen_World")
      pointListRed_World = slicer.mrmlScene.GetFirstNodeByName("pointListRed_World")
      # if the red and green point lists are both empty
      if pointListRed_World.GetNumberOfControlPoints() == 0 and pointListGreen_World.GetNumberOfControlPoints() == 0:
        self.addControlPointToToolTip()
        pass
      # Else check the distance beween the last control point and the tip of the probe
      else:
        # The the tip of the probe in world coordinates
        pos = [0,0,0]
        pointList_EMT = slicer.mrmlScene.GetFirstNodeByName("pointList_EMT")
        pointList_EMT.GetNthControlPointPositionWorld(0,pos)
        # # Transform the point from world to referenece coordinates
        # TrackerToReferenceNode = slicer.mrmlScene.GetFirstNodeByName("ReferenceToTracker (-)")
        # pos = TrackerToReferenceNode.GetMatrixTransformToParent().MultiplyPoint(pos)
        tip_World = pos
            
        # Get the last control point of green in world coordinates
        pos = [0,0,0]
        pointListGreen_World.GetNthControlPointPositionWorld(pointListGreen_World.GetNumberOfControlPoints()-1,pos)
        # # Transform the point from world to referenece coordinates
        # pos = TrackerToReferenceNode.GetMatrixTransformToParent().MultiplyPoint(pos)
        lastPointGreen_World = pos
        # Get the last control point of red in world coordinates
        pos = [0,0,0]
        pointListRed_World.GetNthControlPointPositionWorld(pointListRed_World.GetNumberOfControlPoints()-1,pos)
        # # Transform the point from world to referenece coordinates
        # pos = TrackerToReferenceNode.GetMatrixTransformToParent().MultiplyPoint(pos)
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
      # Check for the Green List
      if slicer.mrmlScene.GetFirstNodeByName('pointListGreen_World') == None:
        pointListGreen_World = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        pointListGreen_World.SetName('pointListGreen_World')
        pointListGreen_World.GetDisplayNode().SetSelectedColor(0,1,0) # Set colour to green

      # Check for the Red List
      if slicer.mrmlScene.GetFirstNodeByName('pointListRed_World') == None:
        pointListRed_World = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        pointListRed_World.SetName('pointListRed_World')
        pointListRed_World.GetDisplayNode().SetSelectedColor(1,0,0) # Set colour to red
      pointListRed_World = slicer.mrmlScene.GetFirstNodeByName('pointListRed_World')
      # Get the size of a control point
      # controlPointSize = pointListRed_World.GetMarkupsDisplayNode().GetGlyphScale()
      # Set the size of the control point
      # pointListRed_World.GetMarkupsDisplayNode().SetGlyphScale(2)
      # Set an absolute size for the control point

      # Check for the EMT list
      if slicer.mrmlScene.GetFirstNodeByName('pointList_EMT') == None:
        pointList_EMT = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        pointList_EMT.SetName('pointList_EMT')
        #add pointList_EMT to the EMT reference frame
      pointList_EMT = slicer.mrmlScene.GetFirstNodeByName("pointList_EMT")
      # pointList_EMT.SetAndObserveTransformNodeID(slicer.mrmlScene.GetFirstNodeByName('ProbeTiptoProbe').GetID())

      # if pointList_EMT is empty, add a point at the origin
      if pointList_EMT.GetNumberOfControlPoints() == 0:
        pointList_EMT.AddControlPoint(np.array([0, 0, 0]))
        pointList_EMT.SetNthControlPointLabel(0, "origin_Tip")
      pointList_EMT.SetNthControlPointLabel(0, "origin_Tip")
  
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

    # Get the image from the volume selector
    specIm = spectrumImageNode
    # Convert it to a displayable format
    specArray = slicer.util.arrayFromVolume(specIm)
    specArray = np.squeeze(specArray)
    specArray = np.transpose(specArray)

    # Save results to a new table node
    if slicer.util.getNodesByClass('vtkMRMLTableNode') == []:
      tableNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
    slicer.util.updateTableFromArray(tableNode,specArray,["Wavelength","Intensity"])

    return specArray
    
  def updateChart(self):
    #
    # Load in and classify the spectra using the model. This should be passed in as a parameter
    #
    # specPred, specLabel = self.classifySpectra(specArray[743:-1,:]) 
    parameterNode = self.getParameterNode()
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    tableNode = parameterNode.GetNodeReference(self.OUTPUT_TABLE)
    spectrumLabel = parameterNode.GetParameter(self.CLASSIFICATION)

    # Create plot
    if slicer.util.getNodesByClass('vtkMRMLPlotSeriesNode') == []:
      plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", spectrumImageNode.GetName() + " plot")
    plotSeriesNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLPlotSeriesNode") 
    plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
    plotSeriesNode.SetXColumnName("Wavelength")
    plotSeriesNode.SetYColumnName("Intensity")
    plotSeriesNode.SetPlotType(plotSeriesNode.PlotTypeScatter)
    plotSeriesNode.SetColor(0, 0.6, 1.0)

    # Create chart and add plot
    if slicer.util.getNodesByClass('vtkMRMLPlotChartNode') == []:
      plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode")
    plotChartNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLPlotChartNode") 
    plotChartNode.SetAndObservePlotSeriesNodeID(plotSeriesNode.GetID())
    plotChartNode.YAxisRangeAutoOn() # The axes can be set or automatic by toggling between on and off
    # plotChartNode.SetYAxisRange(0, 2)
    # plotChartNode.SetTitle('Spectrum')
    plotChartNode.SetTitle(str(spectrumLabel))
    plotChartNode.SetXAxisTitle('Wavelength [nm]')
    plotChartNode.SetYAxisTitle('Intensity')

    # Show plot in layout
    slicer.modules.plots.logic().ShowChartInLayout(plotChartNode)

  def classifySpectra(self,X_test):
    # Get the max value in X_test to see if we will classify or not
    max_value = np.amax(X_test[:,1])
    # # Subtract the baseline from the data
    # path = 'C:/OpticalSpectroscopy_TissueClassification/raw_data/'
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
