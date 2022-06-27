from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import math

#
# SegmentationExperimentInterface
#

class SegmentationExperimentInterface(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  
  def __init__(self, parent):
    parent.title = "Segmentation Experiment Interface"
    parent.categories = ["Segmentation"]
    parent.dependencies = []
    parent.contributors = ["Thomas Vaughan (Queen's)",
                           "Gabor Fichtinger (Queen's)"]
    parent.helpText = """
    This is an interface designed to help manage the experiment for contouring tumors using different methods.
    """
    parent.acknowledgementText = """
    This work is part of the Breast NaviKnife project within the Laboratory for Percutaneous Surgery, Queen's University, Kingston, Ontario. Thomas Vaughan is funded by an NSERC Postgraduate award. Gabor Fichtinger is funded as a Cancer Care Ontario (CCO) Chair.
    """ # replace with organization, grant and thanks.
    self.parent = parent

#
# SegmentationExperimentInterfaceWidget
#

class SegmentationExperimentInterfaceWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    
    # TODO: The following lines are strictly for debug purposes, should be removed when this module is done
    self.developerMode = True
    slicer.segmentationExperimentWidget = self
    
    self.logic = SegmentationExperimentInterfaceLogic()
    
    # parameters
    self.sliderSingleStepValue = 0.1
    self.sliderPageStepValue = 1.0
    self.rotationRateMinSeconds = 0.1
    self.rotationRateMaxSeconds = 5.0
    self.rotationRateDefaultSeconds = 0.5
    self.rotationMagnitudeMinDegrees = 1.0
    self.rotationMagnitudeMaxDegrees = 30.0
    self.rotationMagnitudeDefaultDegrees = 5.0
    
    # Collapsible buttons
    self.setupParametersCollapsibleButton = ctk.ctkCollapsibleButton()
    self.setupParametersCollapsibleButton.text = "Setup Parameters"
    self.layout.addWidget(self.setupParametersCollapsibleButton)
    # Layout within the collapsible button
    self.setupParametersFormLayout = qt.QFormLayout(self.setupParametersCollapsibleButton)
    
    # Input Slice combobox
    self.inputSliceLabel = qt.QLabel()
    self.inputSliceLabel.setText("Input Slice: ")
    self.inputSliceSelector = slicer.qMRMLNodeComboBox()
    self.inputSliceSelector.nodeTypes = ( ("vtkMRMLSliceNode"), "" )
    self.inputSliceSelector.noneEnabled = True
    self.inputSliceSelector.addEnabled = False
    self.inputSliceSelector.removeEnabled = False
    self.inputSliceSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSliceSelector.setToolTip("Pick the input slice for input points")
    self.setupParametersFormLayout.addRow(self.inputSliceLabel, self.inputSliceSelector)
    
    # Input Transform combobox
    self.inputTransformLabel = qt.QLabel()
    self.inputTransformLabel.setText("Input Transform: ")
    self.inputTransformSelector = slicer.qMRMLNodeComboBox()
    self.inputTransformSelector.nodeTypes = ( ("vtkMRMLTransformNode"), "" )
    self.inputTransformSelector.noneEnabled = True
    self.inputTransformSelector.addEnabled = False
    self.inputTransformSelector.removeEnabled = False
    self.inputTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.inputTransformSelector.setToolTip("Pick the transform that will alter the slices")
    self.setupParametersFormLayout.addRow(self.inputTransformLabel, self.inputTransformSelector)
    
    # Input Fiducials combobox
    self.inputMarkupFiducialsLabel = qt.QLabel()
    self.inputMarkupFiducialsLabel.setText("Input Markup Fiducials: ")
    self.inputMarkupFiducialsSelector = slicer.qMRMLNodeComboBox()
    self.inputMarkupFiducialsSelector.nodeTypes = ( ("vtkMRMLMarkupsFiducialNode"), "" )
    self.inputMarkupFiducialsSelector.noneEnabled = True
    self.inputMarkupFiducialsSelector.addEnabled = False
    self.inputMarkupFiducialsSelector.removeEnabled = False
    self.inputMarkupFiducialsSelector.setMRMLScene( slicer.mrmlScene )
    self.inputMarkupFiducialsSelector.setToolTip("Pick the fiducial list that will be used to generate the model")
    self.setupParametersFormLayout.addRow(self.inputMarkupFiducialsLabel, self.inputMarkupFiducialsSelector)
    
    # "Degrees of Freedom" Collapsible button
    #self.rotationAxisCollapsibleButton = ctk.ctkCollapsibleGroupBox()
    #self.rotationAxisCollapsibleButton.title = "Rotation Axis"
    #self.setupParametersFormLayout.addRow(self.rotationAxisCollapsibleButton)

    # Layout within the collapsible button
    #self.rotationAxisFormLayout = qt.QFormLayout(self.rotationAxisCollapsibleButton)
    
    # A series of radio buttons for changing the degrees of freedom
    #self.rotationAxisAPLabel = qt.QLabel(qt.Qt.Horizontal,None)
    #self.rotationAxisAPLabel.setText("AP")
    #self.rotationAxisAPRadioButton = qt.QRadioButton()
    #self.rotationAxisAPRadioButton.setToolTip("Rotate around the AP axis")
    #self.rotationAxisFormLayout.addRow(self.rotationAxisAPLabel,self.rotationAxisAPRadioButton)
    
    #self.rotationAxisLRLabel = qt.QLabel(qt.Qt.Horizontal,None)
    #self.rotationAxisLRLabel.setText("LR")
    #self.rotationAxisLRRadioButton = qt.QRadioButton()
    #self.rotationAxisLRRadioButton.setToolTip("Rotate around the LR axis")
    #self.rotationAxisFormLayout.addRow(self.rotationAxisLRLabel,self.rotationAxisLRRadioButton)
    
    #self.rotationAxisSILabel = qt.QLabel(qt.Qt.Horizontal,None)
    #self.rotationAxisSILabel.setText("SI")
    #self.rotationAxisSIRadioButton = qt.QRadioButton()
    #self.rotationAxisSIRadioButton.setToolTip("Rotate around the SI axis")
    #self.rotationAxisFormLayout.addRow(self.rotationAxisSILabel,self.rotationAxisSIRadioButton)
    
    # Rotation rate
    self.rotationRateLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.rotationRateLabel.setText("Rotation Rate: ")
    self.rotationRateSlider = slicer.qMRMLSliderWidget()
    self.rotationRateSlider.minimum = self.rotationRateMinSeconds
    self.rotationRateSlider.maximum = self.rotationRateMaxSeconds
    self.rotationRateSlider.value = self.rotationRateDefaultSeconds
    self.rotationRateSlider.singleStep = self.sliderSingleStepValue
    self.rotationRateSlider.pageStep = self.sliderPageStepValue
    self.rotationRateSlider.setToolTip("When in continuous mode, determine how often the rotation changes")
    self.setupParametersFormLayout.addRow(self.rotationRateLabel,self.rotationRateSlider)
    
    # Rotation magnitude
    self.rotationMagnitudeLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.rotationMagnitudeLabel.setText("Rotation Magnitude: ")
    self.rotationMagnitudeSlider = slicer.qMRMLSliderWidget()
    self.rotationMagnitudeSlider.minimum = self.rotationMagnitudeMinDegrees
    self.rotationMagnitudeSlider.maximum = self.rotationMagnitudeMaxDegrees
    self.rotationMagnitudeSlider.value = self.rotationMagnitudeDefaultDegrees
    self.rotationMagnitudeSlider.singleStep = self.sliderSingleStepValue
    self.rotationMagnitudeSlider.pageStep = self.sliderPageStepValue
    self.rotationMagnitudeSlider.setToolTip("When in continuous mode, determine how much the rotation changes")
    self.setupParametersFormLayout.addRow(self.rotationMagnitudeLabel,self.rotationMagnitudeSlider)
    
    # Collapsible buttons
    self.userControlsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.userControlsCollapsibleButton.text = "User Controls"
    self.layout.addWidget(self.userControlsCollapsibleButton)
    # Layout within the collapsible button
    self.userControlsFormLayout = qt.QFormLayout(self.userControlsCollapsibleButton)
    
    # Slice positioning
    self.continuousPlayButton = qt.QPushButton("Continuous Playback")
    self.continuousPlayButton.setCheckable(True)
    self.continuousPlayButton.setIcon(qt.QIcon(":/Icons/MarkupsUnselected.png"))
    self.setButtonStyle(self.continuousPlayButton)
    self.userControlsFormLayout.addRow(self.continuousPlayButton)
    
    self.snapshot1Button = qt.QPushButton("Snapshot 1")
    self.snapshot1Button.setIcon(qt.QIcon(":/Icons/MarkupsUnselected.png"))
    self.setButtonStyle(self.snapshot1Button)
    self.snapshot1Button.setEnabled(True)
    self.snapshot2Button = qt.QPushButton("Snapshot 2")
    self.snapshot2Button.setIcon(qt.QIcon(":/Icons/MarkupsUnselected.png"))
    self.setButtonStyle(self.snapshot2Button)
    self.snapshot2Button.setEnabled(True)
    hbox = qt.QHBoxLayout()
    hbox.addWidget(self.snapshot1Button)
    hbox.addWidget(self.snapshot2Button)
    self.userControlsFormLayout.addRow(hbox)
    
    # Placing fiducials
    self.toggleMarkups = qt.QPushButton("Mark points")
    self.toggleMarkups.setCheckable(True)
    self.toggleMarkups.setIcon(qt.QIcon(":/Icons/MarkupsMouseModePlace.png"))
    self.setButtonStyle(self.toggleMarkups)
    self.userControlsFormLayout.addRow(self.toggleMarkups)
    
    # Delete last/all fiducials
    self.deleteLastFiducialButton = qt.QPushButton("Delete last")
    self.deleteLastFiducialButton.setIcon(qt.QIcon(":/Icons/MarkupsDelete.png"))
    self.setButtonStyle(self.deleteLastFiducialButton)
    self.deleteLastFiducialButton.setEnabled(False)
    self.deleteAllFiducialsButton = qt.QPushButton("Delete all")
    self.deleteAllFiducialsButton.setIcon(qt.QIcon(":/Icons/MarkupsDeleteAllRows.png"))
    self.setButtonStyle(self.deleteAllFiducialsButton)
    self.deleteAllFiducialsButton.setEnabled(False)
    hbox = qt.QHBoxLayout()
    hbox.addWidget(self.deleteLastFiducialButton)
    hbox.addWidget(self.deleteAllFiducialsButton)
    self.userControlsFormLayout.addRow(hbox)
    
    # Done
    self.doneButton = qt.QPushButton("Done")
    self.doneButton.setCheckable(False)
    self.doneButton.setIcon(qt.QIcon(":/Icons/MarkupsUnselected.png"))
    self.setButtonStyle(self.doneButton)
    self.userControlsFormLayout.addRow(self.doneButton)
    
    # Output Model combobox
    self.outputModelLabel = qt.QLabel()
    self.outputModelLabel.setText("Output Model: ")
    self.outputModelSelector = slicer.qMRMLNodeComboBox()
    self.outputModelSelector.nodeTypes = ( ("vtkMRMLModelNode"), "" )
    self.outputModelSelector.noneEnabled = True
    self.outputModelSelector.addEnabled = True
    self.outputModelSelector.removeEnabled = False
    self.outputModelSelector.setMRMLScene( slicer.mrmlScene )
    self.outputModelSelector.setToolTip("Pick the output model")
    self.userControlsFormLayout.addRow(self.outputModelLabel, self.outputModelSelector)
    
    #Connections
    self.inputSliceSelector.connect('currentNodeChanged()', self.sendParametersToLogic)
    self.inputTransformSelector.connect('currentNodeChanged()', self.sendParametersToLogic)
    self.inputMarkupFiducialsSelector.connect('currentNodeChanged()', self.sendParametersToLogic)
    self.rotationRateSlider.connect('valueChanged()', self.sendParametersToLogic)
    self.rotationMagnitudeSlider.connect('valueChanged()', self.sendParametersToLogic)
    self.continuousPlayButton.connect('clicked()', self.onContinuousPlaybackButtonPressed)
    self.snapshot1Button.connect('clicked()', self.onSnapshot1ButtonPressed)
    self.snapshot2Button.connect('clicked()', self.onSnapshot2ButtonPressed)
    self.toggleMarkups.connect('clicked()', self.onToggleMarkupsButtonPressed)
    self.deleteLastFiducialButton.connect('clicked()', self.onDeleteLastFiducialButtonPressed)
    self.deleteAllFiducialsButton.connect('clicked()', self.onDeleteAllFiducialsButtonPressed)
    self.doneButton.connect('clicked()', self.onDoneButtonPressed)
    self.outputModelSelector.connect('clicked()', self.sendParametersToLogic)
    
    # Add vertical spacer
    self.layout.addStretch(1)
    
  def setButtonStyle(self, button, textScale = 1.0):
    style = """
    {0}         {{border-style: outset; border-width: 2px; border-radius: 10px; background-color: #C7DDF5; border-color: #9ACEFF; font-size: {1}pt; height: {2}px}}
    {0}:pressed  {{border-style: outset; border-width: 2px; border-radius: 10px; background-color: #9ACEFF; border-color: #9ACEFF; font-size: {1}pt; height: {2}px}}
    {0}:checked {{border-style: outset; border-width: 2px; border-radius: 10px; background-color: #669ACC; border-color: #9ACEFF; font-size: {1}pt; height: {2}px}}
    """.format(button.className(), 12*textScale, qt.QDesktopWidget().screenGeometry().height()*0.05)
    
    button.setStyleSheet(style)
    
  def onContinuousPlaybackButtonPressed(self):
    self.sendParametersToLogic()
    
  def onSnapshot1ButtonPressed(self):
    self.sendParametersToLogic()
    
  def onSnapshot2ButtonPressed(self):
    self.sendParametersToLogic()
    
  def onToggleMarkupsButtonPressed(self):
    self.sendParametersToLogic()
    
  def onDeleteLastFiducialButtonPressed(self):
    self.sendParametersToLogic()
  
  def onDeleteAllFiducialsButtonPressed(self):
    self.sendParametersToLogic()
    
  def onDoneButtonPressed(self):
    self.sendParametersToLogic()
    
  def sendParametersToLogic(self):
    logic.setInputMarkupsFiducialNode(self.inputMarkupsFiducialSelector.currentNode())
    logic.setInputSliceNode(self.inputSliceSelector.currentNode())
    logic.setTransformNode(self.inputTransformSelector.currentNode())
    logic.setRotationRate(self.rotationRateSlider.value)
    logic.setRotationMagnitude(self.rotationMagnitudeSlider.value)
    logic.setOutputModelNode(self.outputModelSelector.currentNode())

#
# SegmentationExperimentInterfaceLogic
#

class SegmentationExperimentInterfaceLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent = None):
    pass
    
  def setInputMarkupsFiducialNode(self, node):
    pass
    
  def setInputSliceNode(self, node):
    pass
    
  def setInputTransformNode(self, node):
    pass
    
  def setOutputModelNode(self, node):
    pass
    
  def setRotationRate(self):
    pass
  
  def setRotationMagnitude(self):
    pass
    
  def setRotationSnapshot1(self):
    pass
    
  def setRotationSnapshot2(self):
    pass
