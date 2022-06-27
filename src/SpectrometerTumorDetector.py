import os
import unittest
import logging
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import xml.etree.ElementTree as ET

#
# SpectrometerTumorDetector
#

class SpectrometerTumorDetector(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Spectrometer tumor detector"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    parent.contributors = ["Andras Lasso (PerkLab, Queen's University)"]
    self.parent.helpText = """
    Mark points where a tracked spectrometer detects fluorescence.
    """
    parent.acknowledgementText = """
    """

#
# SpectrometerTumorDetectorWidget
#

class SpectrometerTumorDetectorWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.logic = SpectrometerTumorDetectorLogic()
    self.parameterNode = None
    self.parameterNodeObserver = None
    self.green = qt.QColor()
    self.green.setGreen(255)
    self.red = qt.QColor()
    self.red.setRed(255)

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Instantiate and connect widgets ...

    self.logic.setTumorProbabilityChangedCallback(self.setTumorProbability)
    self.logic.setTissueRecognitionCallback(self.setTissueRecognitionResult)

    self.detectionMethodsButtonGroup = qt.QButtonGroup()

    # Optical spectrometer parameters

    self.opticalSpectrometerCollapsibleButton = ctk.ctkCollapsibleButton()
    self.detectionMethodsButtonGroup.addButton(self.opticalSpectrometerCollapsibleButton)
    self.opticalSpectrometerCollapsibleButton.text = "Optical spectrometer"
    self.layout.addWidget(self.opticalSpectrometerCollapsibleButton)
    opticalSpectrometerFormLayout = qt.QFormLayout(self.opticalSpectrometerCollapsibleButton)

    # Input spectrum image selector
    self.spectrumImageSelector = slicer.qMRMLNodeComboBox()
    self.spectrumImageSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.spectrumImageSelector.selectNodeUponCreation = True
    self.spectrumImageSelector.addEnabled = False
    self.spectrumImageSelector.removeEnabled = False
    self.spectrumImageSelector.noneEnabled = False
    self.spectrumImageSelector.showHidden = False
    self.spectrumImageSelector.showChildNodeTypes = False
    self.spectrumImageSelector.setMRMLScene( slicer.mrmlScene )
    self.spectrumImageSelector.setToolTip( "Pick the spectrum image to visualize." )
    opticalSpectrometerFormLayout.addRow("Input spectrum image: ", self.spectrumImageSelector)

    # Tumor probability threshold value
    self.tumorProbabilityThresholdSliderWidget = ctk.ctkSliderWidget()
    self.tumorProbabilityThresholdSliderWidget.singleStep = 0.05
    self.tumorProbabilityThresholdSliderWidget.minimum = 0
    self.tumorProbabilityThresholdSliderWidget.maximum = 1
    self.tumorProbabilityThresholdSliderWidget.value = 0.5
    self.tumorProbabilityThresholdSliderWidget.setToolTip("If tumor probability is above this value then it will be marked as tumor")
    opticalSpectrometerFormLayout.addRow("Tumor probability threshold", self.tumorProbabilityThresholdSliderWidget)

    # Tumor probability value display
    self.tumorProbabilityLabel = qt.QLabel()
    self.tumorProbabilityLabel.setText( "Tumor probability: " )
    self.tumorProbabilityValue = qt.QLabel()
    self.tumorProbabilityValue.setText( "N/A" )
    opticalSpectrometerFormLayout.addRow(self.tumorProbabilityLabel, self.tumorProbabilityValue)

    self.tumorProbabilityPalette = qt.QPalette();
    self.tumorProbabilityPalette.setColor(qt.QPalette.Background, self.green)
    self.tumorProbabilityValue.setAutoFillBackground(True)
    self.tumorProbabilityValue.setPalette(self.tumorProbabilityPalette)

    # Mass spectrometer parameters

    self.massSpectrometerCollapsibleButton = ctk.ctkCollapsibleButton()
    self.detectionMethodsButtonGroup.addButton(self.massSpectrometerCollapsibleButton)
    self.massSpectrometerCollapsibleButton.text = "Mass spectrometer (iKnife)"
    self.layout.addWidget(self.massSpectrometerCollapsibleButton)
    massSpectrometerFormLayout = qt.QFormLayout(self.massSpectrometerCollapsibleButton)

    # OpenIGTLink connection for starting/stopping streaming
    self.massSpecConnectorSelector = slicer.qMRMLNodeComboBox()
    self.massSpecConnectorSelector.nodeTypes = ["vtkMRMLIGTLConnectorNode"]
    self.massSpecConnectorSelector.selectNodeUponCreation = True
    self.massSpecConnectorSelector.addEnabled = False
    self.massSpecConnectorSelector.removeEnabled = False
    self.massSpecConnectorSelector.noneEnabled = True
    self.massSpecConnectorSelector.showHidden = False
    self.massSpecConnectorSelector.showChildNodeTypes = False
    self.massSpecConnectorSelector.setMRMLScene( slicer.mrmlScene )
    self.massSpecConnectorSelector.setToolTip( "Pick the OpenIGTLink connector node that communicates with the iKnife Recognizer software for starting/stopping data streaming." )
    massSpectrometerFormLayout.addRow("OpenIGTLink connection: ", self.massSpecConnectorSelector)

    # OpenIGTLink connection for starting/stopping streaming
    self.tumorTissueClassIdTextEditWidget = qt.QLineEdit()
    self.tumorTissueClassIdTextEditWidget.setToolTip("This tissue class will be marked with red dots when detected.")
    massSpectrometerFormLayout.addRow("Tumor tissue class: ", self.tumorTissueClassIdTextEditWidget)

    # Recognized tissue class display
    self.recognizedTissueClassIdLabel = qt.QLabel()
    self.recognizedTissueClassIdLabel.setText("N/A")
    self.recognizedTissueClassIdPalette = qt.QPalette()
    self.recognizedTissueClassIdPalette.setColor(qt.QPalette.Background, self.green)
    self.recognizedTissueClassIdLabel.setAutoFillBackground(True)
    self.recognizedTissueClassIdLabel.setPalette(self.recognizedTissueClassIdPalette)
    massSpectrometerFormLayout.addRow("Recognized tissue class: ", self.recognizedTissueClassIdLabel)

    # Recognition probability value display
    self.recognitionConfidenceValue = qt.QLabel()
    self.recognitionConfidenceValue.setText( "N/A" )
    massSpectrometerFormLayout.addRow("Recognition confidence: ", self.recognitionConfidenceValue)

    # General parameters

    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    # Spectrometer probe tip position selector
    self.spectrometerProbeTipSelector = slicer.qMRMLNodeComboBox()
    self.spectrometerProbeTipSelector.nodeTypes = ["vtkMRMLTransformNode"]
    self.spectrometerProbeTipSelector.selectNodeUponCreation = True
    self.spectrometerProbeTipSelector.addEnabled = False
    self.spectrometerProbeTipSelector.removeEnabled = False
    self.spectrometerProbeTipSelector.noneEnabled = False
    self.spectrometerProbeTipSelector.showHidden = False
    self.spectrometerProbeTipSelector.showChildNodeTypes = True
    self.spectrometerProbeTipSelector.setMRMLScene( slicer.mrmlScene )
    self.spectrometerProbeTipSelector.setToolTip( "Pick the breach warning node to observe." )
    parametersFormLayout.addRow("Spectrometer tip position: ", self.spectrometerProbeTipSelector)

    # Select StylusToReference node by default (if it exists)
    defaultSpectrometerProbeTipNode = slicer.mrmlScene.GetFirstNodeByName("StylusToReference")
    if defaultSpectrometerProbeTipNode:
      self.spectrometerProbeTipSelector.setCurrentNode(defaultSpectrometerProbeTipNode)

    # Output model selector
    self.outputTumorPointsModelSelectorLabel = qt.QLabel()
    self.outputTumorPointsModelSelectorLabel.setText( "Output tumor points model: " )
    self.outputTumorPointsModelSelector = slicer.qMRMLNodeComboBox()
    self.outputTumorPointsModelSelector.nodeTypes = ["vtkMRMLModelNode"]
    self.outputTumorPointsModelSelector.noneEnabled = False
    self.outputTumorPointsModelSelector.addEnabled = True
    self.outputTumorPointsModelSelector.removeEnabled = True
    self.outputTumorPointsModelSelector.renameEnabled = True
    self.outputTumorPointsModelSelector.setMRMLScene( slicer.mrmlScene )
    self.outputTumorPointsModelSelector.baseName = "TumorModel"
    self.outputTumorPointsModelSelector.setToolTip( "A glyph is added to the model at each point tumor is detected" )
    parametersFormLayout.addRow(self.outputTumorPointsModelSelectorLabel, self.outputTumorPointsModelSelector)

    #
    # OpenIGTLink connector node selector
    #
    self.ligthFeedbackConnectorSelector = slicer.qMRMLNodeComboBox()
    self.ligthFeedbackConnectorSelector.nodeTypes = ["vtkMRMLIGTLConnectorNode"]
    self.ligthFeedbackConnectorSelector.selectNodeUponCreation = True
    self.ligthFeedbackConnectorSelector.addEnabled = False
    self.ligthFeedbackConnectorSelector.removeEnabled = False
    self.ligthFeedbackConnectorSelector.noneEnabled = True
    self.ligthFeedbackConnectorSelector.showHidden = False
    self.ligthFeedbackConnectorSelector.showChildNodeTypes = False
    self.ligthFeedbackConnectorSelector.setMRMLScene( slicer.mrmlScene )
    self.ligthFeedbackConnectorSelector.setToolTip( "Pick the OpenIGTLink connector node to send light control commands to. Optional, if set to None then no light feedback will be provided." )
    parametersFormLayout.addRow("Light feedback: ", self.ligthFeedbackConnectorSelector)

    # Checkbox to enable tumor detection (if off then nothing happens)
    self.enableTumorDetectionFlagCheckBox = qt.QCheckBox()
    self.enableTumorDetectionFlagCheckBox.checked = 0
    self.enableTumorDetectionFlagCheckBox.setToolTip("If checked, then tumor detection and marking is enabled.")
    parametersFormLayout.addRow("Enable tumor detection", self.enableTumorDetectionFlagCheckBox)

    # Checkbox to enable tumor marking (if off then detected tumor points are not added to the output model)
    self.enableTumorMarkingFlagCheckBox = qt.QCheckBox()
    self.enableTumorMarkingFlagCheckBox.checked = 0
    self.enableTumorMarkingFlagCheckBox.setToolTip("If checked, then detected tumor points are marked.")
    parametersFormLayout.addRow("Enable tumor marking", self.enableTumorMarkingFlagCheckBox)

    self.clearPointsButton = qt.QPushButton()
    self.clearPointsButton.text = "Clear points"
    self.clearPointsButton.setEnabled(True)
    parametersFormLayout.addRow(self.clearPointsButton)

    self.opticalSpectrometerCollapsibleButton.setChecked(True)

    # connections
    self.enableTumorDetectionFlagCheckBox.connect('stateChanged(int)', self.logic.setEnableTumorDetection)
    self.enableTumorMarkingFlagCheckBox.connect('stateChanged(int)', self.logic.setEnableTumorMarking)
    self.tumorProbabilityThresholdSliderWidget.connect('valueChanged(double)', self.logic.setTumorProbabilityThreshold)
    self.clearPointsButton.connect('clicked()', self.logic.clearPoints)

    self.opticalSpectrometerCollapsibleButton.connect('toggled(bool)', lambda toggle: self.onDetectionMethodChanged(self.opticalSpectrometerCollapsibleButton, toggle))
    self.massSpectrometerCollapsibleButton.connect('toggled(bool)', lambda toggle: self.onDetectionMethodChanged(self.massSpectrometerCollapsibleButton, toggle))

    self.spectrometerProbeTipSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.logic.setSpectrometerProbeTransformNode)
    self.ligthFeedbackConnectorSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.logic.setConnectorNode)
    self.massSpecConnectorSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.logic.setMassSpectrometerConnectorNode)
    self.spectrumImageSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.logic.setAndObserveSpectrumImageNode)
    self.outputTumorPointsModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.logic.setOutputTumorPointsModelNode)
    self.tumorTissueClassIdTextEditWidget.connect("textChanged(QString)", self.logic.setTumorTissueClassId)

    # Define list of widgets for updateGUIFromParameterNode, updateParameterNodeFromGUI, and addGUIObservers
    self.valueEditWidgets = {
      "TumorTissueClassId": self.tumorTissueClassIdTextEditWidget,
      "TumorProbabilityThreshold": self.tumorProbabilityThresholdSliderWidget,
      "EnableTumorDetection": self.enableTumorDetectionFlagCheckBox,
      "EnableTumorMarking": self.enableTumorMarkingFlagCheckBox }
    self.nodeSelectorWidgets = {
      "SpectrometerProbeTip": self.spectrometerProbeTipSelector,
      "Connector": self.ligthFeedbackConnectorSelector,
      "SpectrumImage": self.spectrumImageSelector,
      "MassSpectrometerConnector": self.massSpecConnectorSelector,
      "OutputTumorPointsModel": self.outputTumorPointsModelSelector }

    # Use singleton parameter node (it is created if does not exist yet)
    parameterNode = self.logic.getParameterNode()
    # Set parameter node (widget will observe it and also updates GUI)
    self.setAndObserveParameterNode(parameterNode)

    self.logic.setAndObserveSpectrumImageNode(self.spectrumImageSelector.currentNode())
    self.logic.setSpectrometerProbeTransformNode(self.spectrometerProbeTipSelector.currentNode())
    self.logic.setConnectorNode(self.ligthFeedbackConnectorSelector.currentNode())
    self.logic.setMassSpectrometerConnectorNode(self.massSpecConnectorSelector.currentNode())
    self.logic.setOutputTumorPointsModelNode(self.outputTumorPointsModelSelector.currentNode())
    self.logic.setEnableTumorDetection(self.enableTumorDetectionFlagCheckBox.checked)
    self.logic.setEnableTumorMarking(self.enableTumorMarkingFlagCheckBox.checked)
    self.logic.setTumorProbabilityThreshold(self.tumorProbabilityThresholdSliderWidget.value)
    self.logic.setDetectionMethod("OpticalSpectrometer" if self.opticalSpectrometerCollapsibleButton.checked else "MassSpectrometer")
    self.logic.setTumorTissueClassId(self.tumorTissueClassIdTextEditWidget.text)

    self.addGUIObservers()

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    self.removeGUIObservers()
    self.setAndObserveParameterNode(None)
    self.logic.setAndObserveSpectrumImageNode(None)

  def setAndObserveParameterNode(self, parameterNode):
    if parameterNode == self.parameterNode and self.parameterNodeObserver:
      # no change and node is already observed
      return
    # Remove observer to old parameter node
    if self.parameterNode and self.parameterNodeObserver:
      self.parameterNode.RemoveObserver(self.parameterNodeObserver)
      self.parameterNodeObserver = None
    # Set and observe new parameter node
    self.parameterNode = parameterNode
    if self.parameterNode:
      self.parameterNodeObserver = self.parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    # Update GUI
    self.updateGUIFromParameterNode()

  def updateGUIFromParameterNode(self, dummy=None, dummy2=None):
    parameterNode = self.parameterNode
    if not parameterNode:
      return
    for parameterName in self.valueEditWidgets:
      oldBlockSignalsState = self.valueEditWidgets[parameterName].blockSignals(True)
      widgetClassName = self.valueEditWidgets[parameterName].className()
      if widgetClassName=="QCheckBox":
        checked = (int(parameterNode.GetParameter(parameterName)) != 0)
        self.valueEditWidgets[parameterName].setChecked(checked)
      elif widgetClassName=="QSpinBox":
        self.valueEditWidgets[parameterName].setValue(float(parameterNode.GetParameter(parameterName)))
      elif widgetClassName=="ctkSliderWidget":
        self.valueEditWidgets[parameterName].setValue(float(parameterNode.GetParameter(parameterName)))
      elif widgetClassName=="QLineEdit":
        self.valueEditWidgets[parameterName].text = parameterNode.GetParameter(parameterName)
      else:
        raise Exception("Unexpected widget class: {0}".format(widgetClassName))
      self.valueEditWidgets[parameterName].blockSignals(oldBlockSignalsState)
    for parameterName in self.nodeSelectorWidgets:
      oldBlockSignalsState = self.nodeSelectorWidgets[parameterName].blockSignals(True)
      self.nodeSelectorWidgets[parameterName].setCurrentNodeID(parameterNode.GetNodeReferenceID(parameterName))
      self.nodeSelectorWidgets[parameterName].blockSignals(oldBlockSignalsState)

    detectionMethod = self.parameterNode.GetParameter("DetectionMethod")
#    oldBlockSignalsStateOptical = self.opticalSpectrometerCollapsibleButton.blockSignals(True)
#    oldBlockSignalsStateMass = self.massSpectrometerCollapsibleButton.blockSignals(True)
    if detectionMethod == "OpticalSpectrometer":
      self.opticalSpectrometerCollapsibleButton.setChecked(True)
    else:
      self.massSpectrometerCollapsibleButton.setChecked(True)
#    self.opticalSpectrometerCollapsibleButton.blockSignals(oldBlockSignalsStateOptical)
#    self.massSpectrometerCollapsibleButton.blockSignals(oldBlockSignalsStateMass)

  def updateParameterNodeFromGUI(self):
    parameterNode = self.parameterNode
    oldModifiedState = parameterNode.StartModify()
    for parameterName in self.valueEditWidgets:
      widgetClassName = self.valueEditWidgets[parameterName].className()
      if widgetClassName=="QCheckBox":
        if self.valueEditWidgets[parameterName].checked:
          parameterNode.SetParameter(parameterName, "1")
        else:
          parameterNode.SetParameter(parameterName, "0")
      elif widgetClassName=="QSpinBox":
        parameterNode.SetParameter(parameterName, str(self.valueEditWidgets[parameterName].value))
      elif widgetClassName=="ctkSliderWidget":
        parameterNode.SetParameter(parameterName, str(self.valueEditWidgets[parameterName].value))
      elif widgetClassName=="QLineEdit":
        parameterNode.SetParameter(parameterName, str(self.valueEditWidgets[parameterName].text))
      else:
        raise Exception("Unexpected widget class: {0}".format(widgetClassName))
    for parameterName in self.nodeSelectorWidgets:
      parameterNode.SetNodeReferenceID(parameterName, self.nodeSelectorWidgets[parameterName].currentNodeID)
    parameterNode.EndModify(oldModifiedState)

  def onDetectionMethodChanged(self, collapsibleButton, toggle):
    if not toggle:
      return
    detectionMethod = "OpticalSpectrometer" if collapsibleButton == self.opticalSpectrometerCollapsibleButton else "MassSpectrometer"
    self.logic.setDetectionMethod(detectionMethod)
    self.parameterNode.SetParameter("DetectionMethod", detectionMethod)

  def addGUIObservers(self):
    for parameterName in self.valueEditWidgets:
      widgetClassName = self.valueEditWidgets[parameterName].className()
      if widgetClassName=="QSpinBox":
        self.valueEditWidgets[parameterName].connect("valueChanged(int)", self.updateParameterNodeFromGUI)
      elif widgetClassName=="QCheckBox":
        self.valueEditWidgets[parameterName].connect("clicked()", self.updateParameterNodeFromGUI)
    for parameterName in self.nodeSelectorWidgets:
      self.nodeSelectorWidgets[parameterName].connect("currentNodeIDChanged(QString)", self.updateParameterNodeFromGUI)

  def removeGUIObservers(self):
    for parameterName in self.valueEditWidgets:
      widgetClassName = self.valueEditWidgets[parameterName].className()
      if widgetClassName=="QSpinBox":
        self.valueEditWidgets[parameterName].disconnect("valueChanged(int)", self.updateParameterNodeFromGUI)
      elif widgetClassName=="QCheckBox":
        self.valueEditWidgets[parameterName].disconnect("clicked()", self.updateParameterNodeFromGUI)
    for parameterName in self.nodeSelectorWidgets:
      self.nodeSelectorWidgets[parameterName].disconnect("currentNodeIDChanged(QString)", self.updateParameterNodeFromGUI)

  def setTumorProbability(self, probability):
    self.tumorProbabilityValue.setText( "{0:.2f}".format(probability) )
    if probability>self.tumorProbabilityThresholdSliderWidget.value:
      self.tumorProbabilityPalette.setColor(qt.QPalette.Background, self.red)
    else:
      self.tumorProbabilityPalette.setColor(qt.QPalette.Background, self.green)
    self.tumorProbabilityValue.setPalette(self.tumorProbabilityPalette)

  def setTissueRecognitionResult(self, tissueClassId, recognitionConfidenceStr, colorNameStr):
    self.recognizedTissueClassIdLabel.setText(tissueClassId)
    self.recognitionConfidenceValue.setText(recognitionConfidenceStr)
    if colorNameStr.lower() == 'red':
      self.recognizedTissueClassIdPalette.setColor(qt.QPalette.Background, self.red)
    else:
      self.recognizedTissueClassIdPalette.setColor(qt.QPalette.Background, self.green)
    self.recognizedTissueClassIdLabel.setPalette(self.recognizedTissueClassIdPalette)

#
# SpectrometerTumorDetectorLogic
#

class SpectrometerTumorDetectorLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)

    self.isSingletonParameterNode = True

    self.detectionMethod = "OpticalSpectrometer"

    self.spectrometerProbeTransformNode = None
    self.connectorNode = None
    self.spectrumImageNode = None
    self.outputTumorPointsModelNode = None
    self.tumorProbabilityChangedCallback = None

    self.massSpectrometerConnectorNode = None
    self.tissueTypeNode = None
    self.tissueRecognitionResultCallback = None
    self.tissueRecognitionStreamingStarted = False
    self.tumorTissueClassId = ""

    self.defaultCommandTimeoutSec = 30
    # Create commands
    self.cmdStartRecognitionDataStreaming  = slicer.mrmlScene.GetFirstNodeByName("CMD_1")
    if self.cmdStartRecognitionDataStreaming is None:
      self.cmdStartRecognitionDataStreaming = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTextNode", "CMD_1")
    self.cmdStartRecognitionDataStreaming.SetText("<Command Name=\"StartTissueRecognitionDataStreaming\"/>")
    self.cmdStartRecognitionDataStreamingTimer = qt.QTimer()
    self.cmdStartRecognitionDataStreamingTimer.setInterval(self.defaultCommandTimeoutSec*1000)
    self.cmdStartRecognitionDataStreamingTimer.timeout.connect(self.onStartTissueRecognitionDataStreamingCommandResponseReceived)

    self.ackStartRecognitionDataStreaming  = slicer.mrmlScene.GetFirstNodeByName("ACK_1")
    if self.ackStartRecognitionDataStreaming is None:
      self.ackStartRecognitionDataStreaming = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTextNode", "ACK_1")
    self.ackStartRecognitionDataStreaming.AddObserver(vtk.vtkCommand.ModifiedEvent,
      self.onStartTissueRecognitionDataStreamingCommandResponseReceived)

    self.cmdStopRecognitionDataStreaming  = slicer.mrmlScene.GetFirstNodeByName("CMD_2")
    if self.cmdStopRecognitionDataStreaming is None:
      self.cmdStopRecognitionDataStreaming = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTextNode", "CMD_2")
    self.cmdStopRecognitionDataStreaming.SetText("<Command Name=\"StopTissueRecognitionDataStreaming\"/>")
    self.cmdStopRecognitionDataStreamingTimer = qt.QTimer()
    self.cmdStopRecognitionDataStreamingTimer.setInterval(self.defaultCommandTimeoutSec*1000)
    self.cmdStopRecognitionDataStreamingTimer.timeout.connect(self.onStopTissueRecognitionDataStreamingCommandResponseReceived)

    self.ackStopRecognitionDataStreaming  = slicer.mrmlScene.GetFirstNodeByName("ACK_2")
    if self.ackStopRecognitionDataStreaming is None:
      self.ackStopRecognitionDataStreaming = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTextNode", "ACK_2")
    self.ackStopRecognitionDataStreaming.AddObserver(vtk.vtkCommand.ModifiedEvent,
      self.onStopTissueRecognitionDataStreamingCommandResponseReceived)

    self.observerTags = []

    self.enableTumorDetection = False
    self.tumorProbabilityThreshold = 0.5
    self.enableTumorMarking = False

    self.previousProbeTipPosition_Model = [0,0,0]
    self.minimumSamplingDistance = 5

    # Set up tumor marker
    self.markedPoints = vtk.vtkPoints()
    self.markedPointsPolydata = vtk.vtkPolyData()
    self.markedPointsPolydata.SetPoints(self.markedPoints)
    glyph = vtk.vtkPolyData()
    #cubeSource = vtk.vtkCubeSource()
    #cubeSource.SetXLength(self.minimumSamplingDistance)
    #cubeSource.SetYLength(self.minimumSamplingDistance)
    #cubeSource.SetZLength(self.minimumSamplingDistance)
    sphereSource = vtk.vtkSphereSource()
    sphereSource.SetRadius(self.minimumSamplingDistance/2)
    self.markedPointsGlyph3d = vtk.vtkGlyph3D()
    #self.markedPointsGlyph3d.SetSourceConnection(cubeSource.GetOutputPort())
    self.markedPointsGlyph3d.SetSourceConnection(sphereSource.GetOutputPort())
    self.markedPointsGlyph3d.SetInputData(self.markedPointsPolydata)
    self.markedPointsGlyph3d.Update()

    # Create command object for sending light setting command
    self.lightSetCommand = slicer.vtkSlicerPlusOpenIGTLinkCommand()
    self.lightSetCommand.SetCommandName('SendText')
    # We use the same Arduino device for the tumor detector feedback as for BreachWarningLight
    self.lightSetCommand.SetCommandAttribute('DeviceId','BreachWarningLight')
    self.lightSetCommand.SetCommandTimeoutSec(1.0)
    logging.debug("Add observer to lightSetCommand")
    self.lightSetCommandObserverTag = self.lightSetCommand.AddObserver(self.lightSetCommand.CommandCompletedEvent, self.onLightSetCommandCompleted)
    # If the last light set command is still in progress then we set the new command text
    # in this variable. When the command is completed then we send the command
    self.queuedLightSetCommandText = None

  def __del__(self):
    # Clean up observations
    self.removeObservers()
    logging.debug("Remove observer from lightSetCommand")
    self.lightSetCommand.RemoveObserver(self.lightSetCommandObserverTag)
    # Clean up commands
    self.cmdStartRecognitionDataStreaming.RemoveObservers(slicer.vtkSlicerPlusOpenIGTLinkCommand.CommandCompletedEvent)
    self.cmdStopRecognitionDataStreaming.RemoveObservers(slicer.vtkSlicerPlusOpenIGTLinkCommand.CommandCompletedEvent)

  def createParameterNode(self):
    # Set default parameters
    node = ScriptedLoadableModuleLogic.createParameterNode(self)
    node.SetName(slicer.mrmlScene.GetUniqueNameByString(self.moduleName))
    node.SetParameter("TumorProbabilityThreshold", "0.5")
    node.SetParameter("EnableTumorDetection", "0")
    node.SetParameter("EnableTumorMarking", "0")
    node.SetParameter("TumorTissueClassId", "Goose")
    node.SetParameter("DetectionMethod", "OpticalSpectrometer")
    return node

  def addObservers(self):
    if self.detectionMethod == "OpticalSpectrometer":
      if self.spectrumImageNode:
        logging.debug("Add observer to {0}".format(self.spectrumImageNode.GetName()))
        self.observerTags.append([self.spectrumImageNode, self.spectrumImageNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onSpectrumImageNodeModified)])
    else:
      self.tissueTypeNode = slicer.mrmlScene.GetFirstNode("TissueType", "vtkMRMLTextNode")
      if not self.tissueTypeNode:
        self.tissueTypeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTextNode", "TissueType")
      logging.debug("Add observer to {0}".format(self.tissueTypeNode.GetName()))
      self.observerTags.append([self.tissueTypeNode, self.tissueTypeNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onTissueTypeNodeModified)])
      if self.massSpectrometerConnectorNode:
        self.massSpectrometerConnectorNode.RegisterOutgoingMRMLNode(self.cmdStartRecognitionDataStreaming)
        self.massSpectrometerConnectorNode.PushNode(self.cmdStartRecognitionDataStreaming)
        self.ackStartRecognitionDataStreaming.SetText("")
        self.cmdStartRecognitionDataStreamingTimer.start()

  def removeObservers(self):
    logging.debug("Remove observers")

    for nodeTagPair in self.observerTags:
      nodeTagPair[0].RemoveObserver(nodeTagPair[1])

    if self.tissueRecognitionStreamingStarted:
      if self.massSpectrometerConnectorNode:
        self.massSpectrometerConnectorNode.RegisterOutgoingMRMLNode(self.cmdStopRecognitionDataStreaming)
        self.massSpectrometerConnectorNode.PushNode(self.cmdStopRecognitionDataStreaming)
        self.ackStopRecognitionDataStreaming.SetText("")
        self.cmdStopRecognitionDataStreamingTimer.start()

  def setTumorTissueClassId(self, tumorTissueClassId):
    self.tumorTissueClassId = tumorTissueClassId

  def setAndObserveSpectrumImageNode(self, spectrumImageNode):
    if spectrumImageNode == self.spectrumImageNode and self.observerTags:
      return
    self.removeObservers()
    self.spectrumImageNode = spectrumImageNode
    if self.enableTumorDetection:
      self.addObservers()
    self.onSpectrumImageNodeModified(0,0)

  def setEnableTumorMarking(self, enable):
   self.enableTumorMarking = enable

  def setEnableTumorDetection(self, enable):
    self.removeObservers()
    self.enableTumorDetection = enable
    if self.enableTumorDetection:
      self.addObservers()
    else:
      # Disable light
      self.queueLightSetCommand('000000')

  def setDetectionMethod(self, detectionMethod):
    self.removeObservers()
    self.detectionMethod = detectionMethod
    self.addObservers()

  def setSpectrometerProbeTransformNode(self, spectrometerProbeTransformNode):
    self.spectrometerProbeTransformNode = spectrometerProbeTransformNode

  def setConnectorNode(self, connectorNode):
    self.connectorNode = connectorNode
    if not self.connectorNode is None:
      self.connectorNode.SetOutgoingMessageHeaderVersionMaximum(1)

  def setMassSpectrometerConnectorNode(self, massSpectrometerConnectorNode):
    self.massSpectrometerConnectorNode = massSpectrometerConnectorNode
    if not self.massSpectrometerConnectorNode is None:
      self.massSpectrometerConnectorNode.SetOutgoingMessageHeaderVersionMaximum(1)

  def setOutputTumorPointsModelNode(self, outputTumorPointsModelNode):
    if self.outputTumorPointsModelNode == outputTumorPointsModelNode:
      return

    if self.outputTumorPointsModelNode:
      self.outputTumorPointsModelNode.SetPolyDataConnection(None)

    self.outputTumorPointsModelNode = outputTumorPointsModelNode

    if self.outputTumorPointsModelNode:
      # Create model display node if does not exist yet
      if not self.outputTumorPointsModelNode.GetDisplayNode():
        modelDisplay = slicer.vtkMRMLModelDisplayNode()
        modelDisplay.SetEdgeVisibility(False)
        modelDisplay.SetColor(1,0,0)
        slicer.mrmlScene.AddNode(modelDisplay)
        self.outputTumorPointsModelNode.SetAndObserveDisplayNodeID(modelDisplay.GetID())
      # Set up glyph filter
      self.outputTumorPointsModelNode.SetPolyDataConnection(self.markedPointsGlyph3d.GetOutputPort())

  def setTumorProbabilityThreshold(self, tumorProbabilityThreshold):
    self.tumorProbabilityThreshold = tumorProbabilityThreshold

  def setTumorProbabilityChangedCallback(self, tumorProbabilityChangedCallback):
    self.tumorProbabilityChangedCallback = tumorProbabilityChangedCallback

  def setTissueRecognitionCallback(self, tissueRecognitionResultCallback):
    self.tissueRecognitionResultCallback = tissueRecognitionResultCallback

  def setTumorProbabilityThreshold(self, tumorProbabilityThreshold):
    self.tumorProbabilityThreshold = tumorProbabilityThreshold
    self.onSpectrumImageNodeModified(0,0)

  def getMeanIntensity(self, pixels, sensorIndexStart, sensorIndexEnd, numberOfSamples):
    sensorIndexStepSize = (sensorIndexEnd-sensorIndexStart)/(numberOfSamples-1)
    sensorIndex = sensorIndexStart
    pixelSum = 0
    for sampleIndex in range(numberOfSamples):
      pixelSum = pixelSum + pixels.GetScalarComponentAsDouble(int(sensorIndex), 1, 0, 0)
      sensorIndex = sensorIndex + sensorIndexStepSize
    return pixelSum/numberOfSamples

  def computeTumorProbabilitySvm(self):
    if not self.spectrumImageNode:
      logging.error("No spectrum image is available")
      return 0
    pixels = self.spectrumImageNode.GetImageData()
    # These values were obtained from MATLAB after training a Support Vector Machine (SVM) using svmtrain().
    indices = [ 744, 860, 975, 1090, 1203, 1316, 1428, 1539, 1650, 1760, 1869, 1978, 2086, 2194, 2301, 2407, 2513, 2619, 2724, 2829, 2933, 3037 ]
    weights = [ -35.8542, -23.5847, 1.3148, 2.0409, 2.6045, 1.3813, 11.0868, 6.0270, 2.2969, -110.6294, -143.2754, 55.1955, 82.8242, 94.3075, 21.9733, 24.7663, 27.2706, -24.4474, -14.3193, -3.3020, -7.1302, 32.1520 ]
    bias = 1.3146
    # This value is a parameter, determined empirically. Should be negative.
    scale = -10
    # apply SVM
    probability = self.getProbabilityFromSvm(pixels,indices,weights,bias,scale)
    return probability

  def getProbabilityFromSvm(self, pixels, indices, weights, bias, scale):
    # have to computed a weighted sum of pixel values, and incorporate the bias
    sumWeightedValues = bias
    for i in range(len(indices)):
      weightedValue = (pixels.GetScalarComponentAsDouble(indices[i], 1, 0, 0) * weights[i])
      sumWeightedValues = (sumWeightedValues + weightedValue)
    # Determine class based on the sign of the sum. 0 = first class = background, and 1 = second class = tumor was used.
    # According to MATLAB documentation, the sign is positive for weights belonging to the first group (background)
    # so if the sign is negative, then it belongs to the second (tumor) group. Scale should thus be signed accordingly.
    probability = sumWeightedValues*scale
    if probability<0:
      probability=0
    if probability>1:
      probability=1
    return probability

  def computeTumorProbabilityPeakRegions(self):
    if not self.spectrumImageNode:
      return 0
    pixels = self.spectrumImageNode.GetImageData()

    # excitation: 380-410nm (900-1030)
    # background: 430-480nm and 800-900nm (indices: 1115-1350, 2730-3150)
    # fluorescence: 560-650nm (1700-2100)
    #   Note: Thomas Vaughan observes fluorescence starting around 550 nm (index 1650)

    #excitationIntensity = self.getMeanIntensity(pixels, 900, 1030, 10)
    excitationIntensity = self.getMeanIntensity(pixels, 960, 990, 10)
    excitationScalingFactor = 0.25
    #fluorescenceIntensity = self.getMeanIntensity(pixels, 1700, 2100, 10)
    fluorescenceIntensity = self.getMeanIntensity(pixels, 1650, 1700, 10)
    bkgIntensity = (self.getMeanIntensity(pixels, 1115, 1350, 10)+self.getMeanIntensity(pixels, 2730, 3150, 10))/2

    probability = (fluorescenceIntensity-bkgIntensity)/(excitationIntensity*excitationScalingFactor)

    #logging.info("Excitation = {0}   Background = {1}    Fluorescence = {2}    Tumor probability: {3}".format(excitationIntensity, bkgIntensity, fluorescenceIntensity, probability))

    excitationLowerThreshold = 0.005
    if excitationIntensity<excitationLowerThreshold or excitationIntensity<3*bkgIntensity:
      # no excitation signal detected
     return 0.01

    if probability<0:
      probability=0
    if probability>1:
      probability=1

    return probability

  def onSpectrumImageNodeModified(self, observer, eventid):
    #tumorProbability = self.computeTumorProbabilityPeakRegions()
    tumorProbability = self.computeTumorProbabilitySvm()

    if self.tumorProbabilityChangedCallback:
      self.tumorProbabilityChangedCallback(tumorProbability)

    #logging.info("Tumor probability: {0}, threshold: {1}".format(tumorProbability, self.tumorProbabilityThreshold))

    if self.enableTumorMarking and tumorProbability>self.tumorProbabilityThreshold:
      #logging.info("Add tumor marker")
      self.AddTumorMarker()

    if self.connectorNode:
      # Command text is 6 characters:
      #  1-3: 3 intensities (LED, [unused], sound), each between 0 and 9
      #  4-6: 3-digit number light is on for the specified time (in msec) and then off for the same length of time
      lightSetCommandText = "000000"
      if tumorProbability>self.tumorProbabilityThreshold:
        #volume = (tumorProbability-self.tumorProbabilityThreshold)*10
        #if volume<0: volume=0
        #if volume>9: volume=9
        #lightSetCommandText = "90"+str(volume)+"000" # modulated light and volume, solid

        #freq = 50+(1-(tumorProbability-self.tumorProbabilityThreshold))*100
        #if freq<50: freq=50
        #if freq>500: freq=500
        #lightSetCommandText = "909"+'{0:03d}'.format(freq) # max light and volume

        lightSetCommandText = "909000" # max light and volume, solid
      # print the command on the console - just for testing
      # logging.info('Light pattern: '+lightSetCommandText)
      # Send the output data to the serial input of the arduino
      self.queueLightSetCommand(lightSetCommandText)

  def onTissueTypeNodeModified(self, observer, eventid):
    tissueRecognitionResult = self.tissueTypeNode.GetText()
    if (tissueRecognitionResult is None) or (not tissueRecognitionResult.startswith("<")):
      # not a valid tissue recognition result - ignore it
      return

    responseElement = vtk.vtkXMLUtilities.ReadElementFromString(tissueRecognitionResult)
    tissueClassId = responseElement.GetAttribute("TissueClassId")
    recognitionConfidenceStr = responseElement.GetAttribute("Confidence")

    isTumorClass = (self.tumorTissueClassId == tissueClassId)

    if self.tissueRecognitionResultCallback:
      self.tissueRecognitionResultCallback(tissueClassId, recognitionConfidenceStr, "red" if isTumorClass else "green")

    if self.enableTumorMarking and isTumorClass:
      #logging.info("Add tumor marker")
      self.AddTumorMarker()

  def AddTumorMarker(self):
    if not self.spectrometerProbeTransformNode or not self.outputTumorPointsModelNode:
      return

    # Get the tumor point position in the model's coordinate system
    tumorModelTransform = None
    tumorModelTransformId = self.outputTumorPointsModelNode.GetTransformNodeID()
    if tumorModelTransformId:
      tumorModelTransform = slicer.mrmlScene.GetNodeByID(tumorModelTransformId)

    probeTipToModelTransformMatrix = vtk.vtkMatrix4x4()
    if tumorModelTransform:
      self.spectrometerProbeTransformNode.GetMatrixTransformToNode(tumorModelTransform, probeTipToModelTransformMatrix)
    else:
      self.spectrometerProbeTransformNode.GetMatrixTransformToWorld(probeTipToModelTransformMatrix)

    probeTipPosition_Model = [probeTipToModelTransformMatrix.GetElement(0,3), probeTipToModelTransformMatrix.GetElement(1,3), probeTipToModelTransformMatrix.GetElement(2,3)]

    # return if did not move enough compared to the previous sampling position
    if vtk.vtkMath.Distance2BetweenPoints(self.previousProbeTipPosition_Model, probeTipPosition_Model) < self.minimumSamplingDistance*self.minimumSamplingDistance:
      return

    self.markedPoints.InsertNextPoint(probeTipPosition_Model)
    self.markedPoints.Modified()
    self.markedPointsGlyph3d.Modified()

  def clearPoints(self):
    self.markedPoints.Reset()
    self.markedPoints.Modified()
    self.markedPointsGlyph3d.Modified()

  def queueLightSetCommand(self, lightSetCommandText):
    if not self.connectorNode:
      # connector node is not selected, no need for sending light set command
      return
    if self.lightSetCommand.IsSucceeded() and self.lightSetCommand.GetCommandAttribute('Text') == lightSetCommandText:
      # The command has been already sent successfully, no need to resend
      return
    if self.lightSetCommand.IsInProgress():
      # The previous command is still in progress anymore, so we have to wait until it is completed
      self.queuedLightSetCommandText = lightSetCommandText
      return
    # Ready to send a new setting
    self.lightSetCommand.SetCommandAttribute('Text', lightSetCommandText)
    slicer.modules.openigtlinkremote.logic().SendCommand(self.lightSetCommand, self.connectorNode.GetID())

  def onLightSetCommandCompleted(self, observer, eventid):
    # If there was a queued command that we could not execute because a command was already in progress
    # then send it now
    if self.queuedLightSetCommandText:
      text=self.queuedLightSetCommandText
      self.queuedLightSetCommandText = None
      self.queueLightSetCommand(text)

  def printCommandResponse(self, command, q):
    statusText = "Command {0} [{1}]: {2}\n".format(command.GetCommandName(), command.GetID(), command.StatusToString(command.GetStatus()))
    if command.GetResponseMessage():
      statusText = statusText + command.GetResponseMessage()
    elif command.GetResponseText():
      statusText = statusText + command.GetResponseText()
    logging.info(statusText)

  def onStartTissueRecognitionDataStreamingCommandResponseReceived(self, command=None, q=None):
    self.cmdStartRecognitionDataStreamingTimer.stop()
    status = "FAIL"
    if  self.ackStartRecognitionDataStreaming.GetText() != "":
      commandResponse = ET.fromstring(self.ackStartRecognitionDataStreaming.GetText())
      status = commandResponse.attrib["status"]
    if status != "SUCCESS":
      if self.tissueRecognitionResultCallback:
        self.tissueRecognitionResultCallback("Failed to start data streaming", "N/A", "red")
      return

    self.tissueRecognitionResultCallback("Started data streaming", "N/A", "green")
    self.tissueRecognitionStreamingStarted = True

  def onStopTissueRecognitionDataStreamingCommandResponseReceived(self, command=None, q=None):
    self.cmdStopRecognitionDataStreamingTimer.stop()
    status = "FAIL"
    if  self.ackStopRecognitionDataStreaming.GetText() != "":
      commandResponse = ET.fromstring(self.ackStopRecognitionDataStreaming.GetText())
      status = commandResponse.attrib["status"]
    if status != "SUCCESS":
      if self.tissueRecognitionResultCallback:
        self.tissueRecognitionResultCallback("Failed to stop data streaming", "N/A", "red")
      return

    self.tissueRecognitionResultCallback("Stopped data streaming", "N/A", "green")
    self.tissueRecognitionStreamingStarted = False


class SpectrometerTumorDetectorTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SpectrometerTumorDetector1()

  def test_SpectrometerTumorDetector1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay('Test passed!')
