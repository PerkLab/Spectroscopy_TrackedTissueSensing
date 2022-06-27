import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy, math
from slicer.util import getNode, getNodes
from slicer import modules, app


class LumpNavEval(ScriptedLoadableModule):

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LumpNav Eval" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Christina Yan (Queen's University, Perk Lab)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = "Put something here"
    self.parent.contributors = ["Christina Yan (Perk Lab)."] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This module evaluates lumpectomy data.
    """
    self.parent.acknowledgementText = ""


#
# LumpNavEvalWidget
#

class LumpNavEvalWidget(ScriptedLoadableModuleWidget):

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # button setup
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Setup Data for Evaluation"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    # Set Transforms Button
    self.applyButton = qt.QPushButton("Set-up Scene")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = True
    parametersFormLayout.addRow(self.applyButton)
    self.layout.addStretch(1)

    # Run logic when button is pressed
    self.applyButton.connect('clicked(bool)', self.onApplyButton)

    self.angleDescriptionLabel = qt.QLabel("Calculate angles between needle and coronal plane.")
    parametersFormLayout.addRow(self.angleDescriptionLabel)
    self.layout.addStretch(1)

    self.angleButton = qt.QPushButton("Calculate Angle")
    self.angleButton.toolTip = "Calculating angle."
    self.angleButton.enabled = True

    self.angleLabel = qt.QLabel()
    self.angleLabel.toolTip = "Displaying angle."
    self.angleLabel.enabled = True
    self.angleLabel.setAlignment(0x0002) # 0002 is right alignment

    parametersFormLayout.setSpacing(15) # vertical spacing between buttons/rows
    parametersFormLayout.addRow(self.angleButton, self.angleLabel)
    
    self.cosAngleButton = qt.QPushButton("Calculate Angle Cosine")
    self.cosAngleButton.toolTip = "Calculating cosine."
    self.cosAngleButton.enabled = True

    self.cosAngleLabel = qt.QLabel()
    self.cosAngleLabel.toolTip = "Displaying cosine."
    self.cosAngleLabel.enabled = True
    self.cosAngleLabel.setAlignment(0x0002) # 0002 is right alignment

    parametersFormLayout.setSpacing(15) # vertical spacing between buttons/rows
    parametersFormLayout.addRow(self.cosAngleButton, self.cosAngleLabel)

    self.angleButton.connect('clicked(bool)', self.onAngleButton)
    self.cosAngleButton.connect('clicked(bool)', self.onCosAngleButton)

  def onApplyButton(self):
    logic = LumpNavEvalLogic()
    logic.setTransforms()

  def onAngleButton(self):
    logic = LumpNavEvalLogic()
    logic.calculateNeedleToCoronalAngle()
    self.angleLabel.setText(str(logic.angleDegrees) + "   Degrees")
    
  def onCosAngleButton(self):
    logic = LumpNavEvalLogic()
    logic.calculateCosineNeedleToCoronalAngle()    
    self.cosAngleLabel.setText(str(logic.angleCosine))
  
  def cleanup(self):
    pass

  def onSelect(self):
    pass

#
# LumpNavEvalLogic
#

class LumpNavEvalLogic(ScriptedLoadableModuleLogic):

  def __init__(self):
    self.layoutManager = app.layoutManager()
    self.angleDegrees = -99
    self.angleRadians = -99
    self.angleCosine = -99
    
  def getAngleDegrees(self):
    return self.angleDegrees
    
  def setTransforms(self): #Run the actual algorithm
    logging.info('Setting up data for evaluation')

    # Get all nodes of models and transforms
    trackerToReferenceNode = getNode('*TrackerToReference-TrackerToReference')
    probeToTrackerNode = getNode('*ProbeToTracker')
    needleToTrackerNode = getNode('*NeedleToTracker')
    imageToTransducerNode = getNode('*ImageToTransducer')
    imageNode = getNode('*Image')

    referenceToRasNode = getNode('ReferenceToRas')
    transducerToProbeNode = getNode('TransducerToProbe')
    tumorModelNode = getNode('TumorModel')
    needleModelToNeedleTipNode = getNode('NeedleModelToNeedleTip')
    needleTipToNeedleNode = getNode('NeedleTipToNeedle')

    # Create needle model
    needleModelNode = modules.createmodels.logic().CreateNeedle(80,1.0,2.5,0)
    needleModelNode.GetDisplayNode().SetColor(0, 1, 1)
    needleModelNode.SetName("NeedleModel")
    needleModelNode.GetDisplayNode().SliceIntersectionVisibilityOn()

    # Set image to RAS hierarchy
    imageNode.SetAndObserveTransformNodeID(imageToTransducerNode.GetID())
    imageToTransducerNode.SetAndObserveTransformNodeID(transducerToProbeNode.GetID())
    transducerToProbeNode.SetAndObserveTransformNodeID(probeToTrackerNode.GetID())
    probeToTrackerNode.SetAndObserveTransformNodeID(trackerToReferenceNode.GetID())
    trackerToReferenceNode.SetAndObserveTransformNodeID(referenceToRasNode.GetID())

    # Set needle and tumor to RAS hierarchy
    needleModelToNeedleTipNode.SetAndObserveTransformNodeID(needleTipToNeedleNode.GetID())
    needleModelNode.SetAndObserveTransformNodeID(needleModelToNeedleTipNode.GetID())
    needleToTrackerNode.SetAndObserveTransformNodeID(trackerToReferenceNode.GetID())
    needleTipToNeedleNode.SetAndObserveTransformNodeID(needleToTrackerNode.GetID())
    tumorModelNode.SetAndObserveTransformNodeID(needleToTrackerNode.GetID())

    needleModelNode.GetDisplayNode().SetColor(0,1,1)
    needleModelNode.GetDisplayNode().SetSliceIntersectionVisibility(1)

    tumorModelNode.GetDisplayNode().SetColor(0,1,0)
    tumorModelNode.GetDisplayNode().SetOpacity(0.5)
    tumorModelNode.GetDisplayNode().SetSliceIntersectionVisibility(1)    
    
    # Center 3D view
    layoutManager = app.layoutManager()
    threeDWidget = layoutManager.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()

    self.showUltrasound(imageNode)
    logging.info('Set up complete, data ready for evaluation')
    return True

  def showUltrasound(self, volumeNode):
    resliceLogic = modules.volumereslicedriver.logic()
    if resliceLogic == None:
      logging.error("Volume reslice driver module not found! Install SlicerIGT extension.")
      return

    redNode = getNode('vtkMRMLSliceNodeRed')
    resliceLogic.SetDriverForSlice(volumeNode.GetID(),redNode)
    resliceLogic.SetModeForSlice(6,redNode) # Transverse mode
    resliceLogic.SetFlipForSlice(False,redNode)
    resliceLogic.SetRotationForSlice(180, redNode)

    redSliceLogic = self.layoutManager.sliceWidget('Red').sliceLogic()
    redSliceLogic.GetSliceCompositeNode().SetBackgroundVolumeID(volumeNode.GetID())
    redSliceLogic.FitSliceToAll()

    # Show red slice in 3D viewer
    sliceWidget = app.layoutManager().sliceWidget('Red')
    sliceLogic = sliceWidget.sliceLogic()
    sliceNode = sliceLogic.GetSliceNode()
    sliceNode.SetSliceVisible(True)

  def calculateAngle(self, directionVector, planeVector): #generic angle calculation between any 2 vectors, creates 2 default ones for 90 degrees if input vectors are none
    logging.info('Calculating angle')
    if directionVector is None: # create vectors if they dont exist
      directionVector = numpy.array([0,0,1,0])
    if planeVector is None:
      planeVector = numpy.array([0,1,0,0])

    self.angleRadians = vtk.vtkMath.AngleBetweenVectors(planeVector[0:3], directionVector[0:3])
    self.angleDegrees = round(vtk.vtkMath.DegreesFromRadians(self.angleRadians), 2)
    logging.info('Calculation complete')


  def calculateNeedleToCoronalAngle(self): #calculates angle between needle and coronal plane
    needleModelToNeedleTipNode = getNode('NeedleModelToNeedleTip')
    needleToRas = vtk.vtkMatrix4x4()
    needleModelToNeedleTipNode.GetMatrixTransformToWorld(needleToRas)
    directionVector = numpy.dot(self.arrayFromVtkMatrix(needleToRas), numpy.array([0,0,1,0]))
    coronalPlane = numpy.array([0,1,0,0])
    self.calculateAngle(directionVector, coronalPlane)
  
  def calculateCosineNeedleToCoronalAngle(self):
    self.calculateNeedleToCoronalAngle()
    self.angleCosine = numpy.cos(self.angleRadians) # argument to cos function needs to be in radians
    

  def arrayFromVtkMatrix(self, vtkMatrix):
    npArray = numpy.zeros((4,4))
    for row in range(4):
      for column in range(4):
          npArray[row][column] = vtkMatrix.GetElement(row,column)
    return npArray

class LumpNavEvalTest(ScriptedLoadableModuleTest):

  def setUp(self):
    pass

  def runTest(self):
    self.setUp()
    self.test_LumpNavEval_AngleCalcTest()

  def test_LumpNavEval_AngleCalcTest(self):
    logic = LumpNavEvalLogic()

    self.delayDisplay("Starting the test")
    #zero degrees
    directionVector1 = numpy.array([0,1,0,0])
    planeVector1 = numpy.array([0,1,0,0])
    logic.calculateAngle(directionVector1, planeVector1)
    if logic.getAngleDegrees() == 0.0:
      print "0 Degrees: Test Passed."
    else:
      print "0 Degrees: Test Failed."
      
    