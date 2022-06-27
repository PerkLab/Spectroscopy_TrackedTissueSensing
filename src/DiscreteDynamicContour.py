from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import math

#
# DiscreteDynamicContour
#

class DiscreteDynamicContour(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  
  def __init__(self, parent):
    parent.title = "Discrete Dynamic Contour"
    parent.categories = ["Segmentation"]
    parent.dependencies = []
    parent.contributors = ["Thomas Vaughan (Queen's)",
                           "Gabor Fichtinger (Queen's)"]
    parent.helpText = """
    This is an implementation of Discrete Dynamic Contour, as described by Ladak et al. (2000) "Prostate boundary segmentation from 2D ultrasound images"
    """
    parent.acknowledgementText = """
    This work is part of the Breast NaviKnife project within the Laboratory for Percutaneous Surgery, Queen's University, Kingston, Ontario. Thomas Vaughan is funded by an NSERC Postgraduate award. Gabor Fichtinger is funded as a Cancer Care Ontario (CCO) Chair.
    """ # replace with organization, grant and thanks.
    self.parent = parent

#
# DiscreteDynamicContourWidget
#

class DiscreteDynamicContourWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    
    # TODO: The following lines are strictly for debug purposes, should be removed when this module is done
    self.developerMode = True
    slicer.lswidget = self
    
    self.logic = DiscreteDynamicContourLogic()

    # Parameters
    self.sigmaDefaultPixels = 20
    self.sigmaMinPixels     = 0
    self.sigmaMaxPixels     = 100
    self.wIntDefault        = 0.3
    self.wIntMin            = 0.0
    self.wIntMax            = 1.0
    self.wImgDefault        = 1.0
    self.wImgMin            = 0.0
    self.wImgMax            = 1.0
    self.wDamDefault        = -0.5
    self.wDamMin            = -1.0
    self.wDamMax            = 1.0
    self.maxDeformCyclesDefault = 100
    self.maxDeformCyclesMin     = 1
    self.maxDeformCyclesMax     = 500
    
    self.sliderSingleStepValue = 0.1
    self.sliderPageStepValue   = 1
    
    self.allIOFieldsSelected = 0
    self.initializeButtonState = 0
    self.editButtonState = 0
    self.deformButtonState = 0
    
    # Collapsible buttons
    self.ioCollapsibleButton = ctk.ctkCollapsibleButton()
    self.ioCollapsibleButton.text = "Input/Output"
    self.layout.addWidget(self.ioCollapsibleButton)

    # Layout within the collapsible button
    self.ioFormLayout = qt.QFormLayout(self.ioCollapsibleButton)
    
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
    self.ioFormLayout.addRow(self.inputSliceLabel, self.inputSliceSelector)
    
    # Input Volume combobox
    self.inputVolumeLabel = qt.QLabel()
    self.inputVolumeLabel.setText("Input Volume: ")
    self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
    self.inputVolumeSelector.nodeTypes = ( ("vtkMRMLVolumeNode"), "" )
    self.inputVolumeSelector.noneEnabled = True
    self.inputVolumeSelector.addEnabled = False
    self.inputVolumeSelector.removeEnabled = False
    self.inputVolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.inputVolumeSelector.setToolTip("Pick the input ultrasound volume (containing the tumor/prostate)")
    self.ioFormLayout.addRow(self.inputVolumeLabel, self.inputVolumeSelector)
    
    # Output Volume combobox
    self.outputModelLabel = qt.QLabel()
    self.outputModelLabel.setText("Output Model: ")
    self.outputModelSelector = slicer.qMRMLNodeComboBox()
    self.outputModelSelector.nodeTypes = ( ("vtkMRMLModelNode"), "" )
    self.outputModelSelector.noneEnabled = True
    self.outputModelSelector.addEnabled = False
    self.outputModelSelector.removeEnabled = False
    self.outputModelSelector.setMRMLScene( slicer.mrmlScene )
    self.outputModelSelector.setToolTip("Pick the output label map (outlining the tumor/prostate)")
    self.ioFormLayout.addRow(self.outputModelLabel, self.outputModelSelector)
    
    # "Parameters" Collapsible
    self.parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    self.parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(self.parametersCollapsibleButton)

    # Layout within the collapsible button
    self.parametersFormLayout = qt.QFormLayout(self.parametersCollapsibleButton)
    
    # sigma
    self.sigmaLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.sigmaLabel.setText("Sigma: ")
    self.sigmaSlider = slicer.qMRMLSliderWidget()
    self.sigmaSlider.minimum = self.sigmaMinPixels
    self.sigmaSlider.maximum = self.sigmaMaxPixels
    self.sigmaSlider.value = self.sigmaDefaultPixels
    self.sigmaSlider.singleStep = self.sliderSingleStepValue
    self.sigmaSlider.pageStep = self.sliderPageStepValue
    self.sigmaSlider.setToolTip("TODO: Add tooltip - what does this parameter do?")
    self.parametersFormLayout.addRow(self.sigmaLabel,self.sigmaSlider)
    
    self.wIntLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.wIntLabel.setText("Internal weight: ")
    self.wIntSlider = slicer.qMRMLSliderWidget()
    self.wIntSlider.minimum = self.wIntMin
    self.wIntSlider.maximum = self.wIntMax
    self.wIntSlider.value = self.wIntDefault
    self.wIntSlider.singleStep = self.sliderSingleStepValue
    self.wIntSlider.pageStep = self.sliderPageStepValue
    self.wIntSlider.setToolTip("TODO: Add tooltip - what does this parameter do?")
    self.parametersFormLayout.addRow(self.wIntLabel,self.wIntSlider)
    
    self.wImgLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.wImgLabel.setText("Image weight: ")
    self.wImgSlider = slicer.qMRMLSliderWidget()
    self.wImgSlider.minimum = self.wImgMin
    self.wImgSlider.maximum = self.wImgMax
    self.wImgSlider.value = self.wImgDefault
    self.wImgSlider.singleStep = self.sliderSingleStepValue
    self.wImgSlider.pageStep = self.sliderPageStepValue
    self.wImgSlider.setToolTip("TODO: Add tooltip - what does this parameter do?")
    self.parametersFormLayout.addRow(self.wImgLabel,self.wImgSlider)
    
    self.wDamLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.wDamLabel.setText("Dampening weight: ")
    self.wDamSlider = slicer.qMRMLSliderWidget()
    self.wDamSlider.minimum = self.wDamMin
    self.wDamSlider.maximum = self.wDamMax
    self.wDamSlider.value = self.wDamDefault
    self.wDamSlider.singleStep = self.sliderSingleStepValue
    self.wDamSlider.pageStep = self.sliderPageStepValue
    self.wDamSlider.setToolTip("TODO: Add tooltip - what does this parameter do?")
    self.parametersFormLayout.addRow(self.wDamLabel,self.wDamSlider)
    
    self.maxDeformCyclesLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.maxDeformCyclesLabel.setText("maxDeformCycles: ")
    self.maxDeformCyclesSlider = slicer.qMRMLSliderWidget()
    self.maxDeformCyclesSlider.minimum = self.maxDeformCyclesMin
    self.maxDeformCyclesSlider.maximum = self.maxDeformCyclesMax
    self.maxDeformCyclesSlider.value = self.maxDeformCyclesDefault
    self.maxDeformCyclesSlider.singleStep = self.sliderSingleStepValue
    self.maxDeformCyclesSlider.pageStep = self.sliderPageStepValue
    self.maxDeformCyclesSlider.setToolTip("TODO: Add tooltip - what does this parameter do?")
    self.parametersFormLayout.addRow(self.maxDeformCyclesLabel,self.maxDeformCyclesSlider)
    
    # "Process Control" Collapsible
    self.processControlCollapsibleButton = ctk.ctkCollapsibleButton()
    self.processControlCollapsibleButton.text = "Process Control"
    self.layout.addWidget(self.processControlCollapsibleButton)

    # Layout within the collapsible button
    self.processControlFormLayout = qt.QFormLayout(self.processControlCollapsibleButton)
    
    # Initialization
    self.initializeButton = qt.QPushButton()
    self.initializeButton.setToolTip("Select 4 points (top, left, bottom, right) to be the initial contour")
    self.initializeButton.setText("Initialize")
    self.initializeButton.setCheckable(True)
    self.processControlFormLayout.addRow(self.initializeButton)
    
    # Deformation
    self.deformButton = qt.QPushButton()
    self.deformButton.setToolTip("Enter the deformation cycle.")
    self.deformButton.setText("Deform")
    self.processControlFormLayout.addRow(self.deformButton)
    
    # Edit
    self.editButton = qt.QPushButton()
    self.editButton.setToolTip("Enter edit mode, drag and clamp contour points.")
    self.editButton.setText("Edit")
    self.processControlFormLayout.addRow(self.editButton)
    
    # Change slice
    self.nextSliceButton = qt.QPushButton()
    self.nextSliceButton.setToolTip("Go to the next slice.")
    self.nextSliceButton.setText("Next Slice")
    self.prevSliceButton = qt.QPushButton()
    self.prevSliceButton.setToolTip("Go to the previous slice.")
    self.prevSliceButton.setText("Previous Slice")
    self.processControlFormLayout.addRow(self.prevSliceButton,self.nextSliceButton)

    # Switch direction
    self.directionButton = qt.QPushButton()
    self.directionButton.setToolTip("Change the direction of the image sweep.")
    self.directionButton.setText("Switch Direction")
    self.processControlFormLayout.addRow(self.directionButton)
    
    # Change slice
    self.abortButton = qt.QPushButton()
    self.abortButton.setToolTip("Abort this process.")
    self.abortButton.setText("Abort")
    self.doneButton = qt.QPushButton()
    self.doneButton.setToolTip("Complete this process.")
    self.doneButton.setText("Done")
    self.processControlFormLayout.addRow(self.abortButton,self.doneButton)
    
    #Connections
    self.initializeButton.connect('clicked(bool)', self.initializeButtonClicked)
    self.deformButton.connect('clicked()',self.deformButtonClicked)
    #self.cameraViewAngleSlider.connect('valueChanged(double)', self.logic.SetCameraViewAngleDeg)
    
    # Add vertical spacer
    self.layout.addStretch(1)

  def initializeButtonClicked(self, pushed):
    logging.debug('initializeButtonClicked()')
    if pushed:
      self.logic.inputSliceNode = self.inputSliceSelector.currentNode()
      self.logic.inputVolumeNode = self.inputVolumeSelector.currentNode()
      self.logic.initializeBegin()
    else:
      self.logic.initializeEnd()
      
  def deformButtonClicked(self):
    logging.debug('deformButtonClicked()')
    self.logic.deformContour()
#
# DiscreteDynamicContourLogic
#

class DiscreteDynamicContourLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  # TODO: Create slice model, vtkMRMLModelNode with visible slice intersections
  
  def __init__(self, parent = None):
    self.currentFiducialsNode = None
    self.previousFiducialsNode = None
    self.deformPreviewModelNode = None
    self.inputSliceNode = None
    self.inputVolumeNode = None
    self.outputModelNode = None
    self.outputVolumeNode = None
    self.dimX = 0
    self.dimY = 1
    self.dimZ = 2
    self.clamps = []
    self.samplingFrequencyMm = 4 # 20 pixels * 0.2 mm/pixel, as per [Ladak2000]
    self.epsilon = 0.001
    self.gaussianCharacteristicWidthPx = 5 # As per [Ladak2000]
    self.SliceCornerToSliceTransform = None
    self.gradientImage = None
    
  def initializeBegin(self):
    logging.debug('initializeBegin()')
    # activate placement mode
    self.setupCurrentFiducialsNode()
    self.setupPreviousFiducialsNode()
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
    selectionNode.SetActivePlaceNodeID(self.currentFiducialsNode.GetID())
    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    interactionNode.SetPlaceModePersistence(True)
    interactionNode.SetCurrentInteractionMode(interactionNode.Place)
    
  def initializeEnd(self):
    logging.debug('initializeEnd()')
    # deactivate placement mode
    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    interactionNode.SetCurrentInteractionMode(interactionNode.ViewTransform)
    self.setFiducialClamping()
    self.resampleFiducials()
    
  def resampleFiducials(self):
    logging.debug('resampleFiducials()')
    if not self.currentFiducialsNode:
      logging.error('Error in DiscreteDynamicContour::resampleFiducials - no fiducial list provided. Aborting.')
      return
    if (self.currentFiducialsNode.GetNumberOfFiducials() < 4):
      logging.error('Error in DiscreteDynamicContour::resampleFiducials - not enough fiducials provided. Aborting.')
      return
    
    sliceToRASMatrix = self.inputSliceNode.GetSliceToRAS()
    sliceToRASTransform = vtk.vtkTransform()
    sliceToRASTransform.SetMatrix(sliceToRASMatrix)
    RASToSliceTransform = sliceToRASTransform.GetInverse()
    
    inputCoordsRASMm = self.inputRASMmFromFiducialList(self.currentFiducialsNode)
    inputCoordsSliceMm = []
    for i in range(0, len(inputCoordsRASMm)):
      inputPointSliceMm = [0,0,0]
      RASToSliceTransform.TransformPoint(inputCoordsRASMm[i],inputPointSliceMm)
      inputCoordsSliceMm.append(inputPointSliceMm)
      
    # TODO: Add some kind of check to make sure z dimension is always 0 for input points...?
      
    segmentVectorsSliceMm = self.computeSegmentVectorsFromCoordinateList(inputCoordsSliceMm)
    segmentLengthsMm = self.computeSegmentLengthsFromSegmentVectors(segmentVectorsSliceMm)
      
    # This code actually resamples. TODO: Tidy this up a bit...
    outputCoordsSliceMm = [] # this is the output - will keep adding to it
    outputClamps = []
    iEndLast = -1 # This is the first clamped point, and the end of the last cycle
    iStart = 0
    iEnd = 0
    for i in range( 0, len(inputCoordsSliceMm) ):
      if self.clamps[i] == True:
        if iEndLast == -1: #Haven't assigned this yet
          iEndLast = i
          iStart = i
        else:
          iEnd = i
          outputCoordsToAddSliceMm = self.resampleFiducialsBetween(inputCoordsSliceMm,iStart,iEnd)
          for j in range(0,len(outputCoordsToAddSliceMm)):
            outputCoordsSliceMm.append(outputCoordsToAddSliceMm[j])
            if (j == 0): # First point is always a clamped point.
              outputClamps.append(True)
            else: # others are simply interpolated, should not be clamped
              outputClamps.append(False)
          iStart = i
    
    outputCoordsToAddSliceMm = self.resampleFiducialsBetween(inputCoordsSliceMm,iStart,iEndLast)  # the last cycle won't be caught within the loop
    for j in range(0,len(outputCoordsToAddSliceMm)):
      outputCoordsSliceMm.append(outputCoordsToAddSliceMm[j])
      if (j == 0): # First point is always a clamped point.
        outputClamps.append(True)
      else: # others are simply interpolated, should not be clamped
        outputClamps.append(False)
    
    outputCoordsRASMm = []
    for i in range(0, len(outputCoordsSliceMm)):
      outputPointRASMm = [0,0,0]
      sliceToRASTransform.TransformPoint(outputCoordsSliceMm[i],outputPointRASMm)
      outputCoordsRASMm.append(outputPointRASMm)
      
    self.outputRASMmToFiducialList(self.currentFiducialsNode, outputCoordsRASMm)
    self.outputRASMmToFiducialList(self.previousFiducialsNode, outputCoordsRASMm)
    self.clamps = outputClamps
    
  # TODO: This function is very messy. Look for a cleaner way to implement.
  def resampleFiducialsBetween( self, inputCoordsSliceMm, iStart, iEnd ):
    logging.debug('resampleFiducialsBetween()')
    # Outputs a new set of vertices to replace all fiducials from iStart to iEnd-1
    # Requires the full set of inputCoords because of the Hermite spline interpolation
    if (self.samplingFrequencyMm <= 0):
      logging.error('Error in DiscreteDynamicContour::resampleFiducialsBetween - sampling frequency is zero or less. Returning empty list.')
      return []
    if (iEnd <= iStart):
      logging.warning('Warning in DiscreteDynamicContour::resampleFiducialsBetween - iStart is greater than or equal to iEnd. Consider checking the code for errors.')
    while (iEnd <= iStart): # TODO: Should I output a warning? Hm.
      iEnd = iEnd + len(inputCoordsSliceMm)
    segmentVectorsSliceMm = self.computeSegmentVectorsFromCoordinateList(inputCoordsSliceMm)
    segmentLengthsMm = self.computeSegmentLengthsFromSegmentVectors(segmentVectorsSliceMm)
    sumSegmentLengthsMm = 0
    for i in range(iStart,iEnd):
      sumSegmentLengthsMm = sumSegmentLengthsMm + segmentLengthsMm[(i%len(segmentLengthsMm))]
    if (sumSegmentLengthsMm <= 0):
      logging.error('Error in DiscreteDynamicContour::resampleFiducialsBetween - sum of segment length is zero. This is caused either by duplicate vertices or a coding error. Returning empty list.')
      return []
    numberToSample = math.ceil(sumSegmentLengthsMm / self.samplingFrequencyMm)
    resamplingDistanceMm = sumSegmentLengthsMm / numberToSample
    remainingDistanceUntilIEndMm = sumSegmentLengthsMm
    iCurrent = iStart
    remainingDistanceUntilSegmentEndMm = segmentLengthsMm[iCurrent]
    remainingDistanceUntilSampleMm = resamplingDistanceMm
    outputCoordsSliceMm = [] # Output variable, keep adding to it
    outputCoordsSliceMm.append(inputCoordsSliceMm[iCurrent])
    while remainingDistanceUntilIEndMm > self.epsilon: # Avoiding errors arising from imprecision is critical here
      if remainingDistanceUntilSegmentEndMm < remainingDistanceUntilSampleMm:
        # Update the remaining distances
        remainingDistanceUntilIEndMm = remainingDistanceUntilIEndMm - remainingDistanceUntilSegmentEndMm
        remainingDistanceUntilSampleMm = remainingDistanceUntilSampleMm - remainingDistanceUntilSegmentEndMm
        remainingDistanceUntilSegmentEndMm = 0
        # Update to the next segment
        iCurrent = (iCurrent + 1)%len(segmentLengthsMm)
        remainingDistanceUntilSegmentEndMm = segmentLengthsMm[iCurrent]
      else:
        # Update the remaining distances
        remainingDistanceUntilIEndMm = remainingDistanceUntilIEndMm - remainingDistanceUntilSampleMm
        remainingDistanceUntilSegmentEndMm = remainingDistanceUntilSegmentEndMm - remainingDistanceUntilSampleMm
        remainingDistanceUntilSampleMm = 0
        # Sample
        if (remainingDistanceUntilIEndMm > self.epsilon): # haven't reached end yet 
          inputPointIMinus1SliceMm = inputCoordsSliceMm[(iCurrent-1+len(inputCoordsSliceMm))%len(inputCoordsSliceMm)]
          inputPointISliceMm       = inputCoordsSliceMm[iCurrent]
          inputPointIPlus1SliceMm  = inputCoordsSliceMm[(iCurrent+1)%len(inputCoordsSliceMm)]
          inputPointIPlus2SliceMm  = inputCoordsSliceMm[(iCurrent+2)%len(inputCoordsSliceMm)]
          splineParameters  = self.calculateSplineParameters(inputPointIMinus1SliceMm,inputPointISliceMm,inputPointIPlus1SliceMm,inputPointIPlus2SliceMm)
          distanceFromSegmentStart = segmentLengthsMm[iCurrent] - remainingDistanceUntilSegmentEndMm
          sParameter = distanceFromSegmentStart / segmentLengthsMm[iCurrent]
          zCoordinateSliceMm = 0
          outputPointSliceMm = self.hermiteInterpolationXY(splineParameters, sParameter, zCoordinateSliceMm)
          outputCoordsSliceMm.append(outputPointSliceMm)
        # reset the remaining distance until sample
        remainingDistanceUntilSampleMm = resamplingDistanceMm
    return outputCoordsSliceMm
    
  def computeSegmentVectorsFromCoordinateList(self, inputCoordsMm):
    print('computeSegmentVectorsFromCoordinateList()')
    segmentVectorsMm = []
    for i in range( 0, len(inputCoordsMm) ):
      inputPointIMm = inputCoordsMm[i]
      inputPointIPlus1Mm = inputCoordsMm[(i+1)%len(inputCoordsMm)]
      segmentVectorMm = [0,0,0] # initial values soon to be changed
      for dim in range(0,3):
        segmentVectorMm[dim] = inputPointIPlus1Mm[dim] - inputPointIMm[dim]
      segmentVectorsMm.append(segmentVectorMm)
    return segmentVectorsMm

  def computeSegmentLengthsFromSegmentVectors(self,segmentVectorsMm):
    print('computeSegmentLengthsFromSegmentVectors()')
    segmentLengthsMm = []
    for i in range(0, len(segmentVectorsMm)):
      segmentSumOfSquaredMmComponents = 0
      segmentVectorMm = segmentVectorsMm[i]
      for dim in range(0,3):
        segmentSumOfSquaredMmComponents = segmentSumOfSquaredMmComponents + segmentVectorMm[dim] * segmentVectorMm[dim]
      segmentLengthMm = segmentSumOfSquaredMmComponents**0.5 #sqrt
      segmentLengthsMm.append(segmentLengthMm)
    return segmentLengthsMm
    
  def updateFiducialClamping(self):
    # At the end of each deform cycle, two identical fiducial lists are created.
    # The "current" one can be modified by the user, while the "previous" one cannot
    # If any element of the "current" list is different from the "previous", then
    # that point has been manipulated by the user and should be clamped in place.
    logging.debug('updateFiducialClamping()')
    if not self.currentFiducialsNode:
      logging.error('Error in DiscreteDynamicContour::updateFiducialClamping - no current fiducial node has been set internally. Will not update clamps.')
      return
    if not self.previousFiducialsNode:
      logging.error('Error in DiscreteDynamicContour::updateFiducialClamping - no previous fiducial node has been set internally. Will not update clamps.')
      return
    inputCoordsCurrentRASMm = self.inputRASMmFromFiducialList(self.currentFiducialsNode)
    inputCoordsPreviousRASMm = self.inputRASMmFromFiducialList(self.previousFiducialsNode)
    if (len(inputCoordsPreviousRASMm) != len(inputCoordsCurrentRASMm)):
      logging.error('Error in DiscreteDynamicContour::updateFiducialClamping - Previous list and current list are not the same. Will not update clamps.')
      return
    inputCoordsListLength = len(inputCoordsCurrentRASMm)
    if (len(self.clamps) != inputCoordsListLength):
      logging.error('Error in DiscreteDynamicContour::updateFiducialClamping - Clamp list length is not the same as input coordinate list length. Will not update clamps.')
      return
    for i in range(0,inputCoordsListLength):
      inputCoordCurrentRASMm = inputCoordsCurrentRASMm[i]
      inputCoordPreviousRASMm = inputCoordsPreviousRASMm[i]
      same = True
      for dim in range(0,3): #TODO: Look for a nice, built-in way of doing array comparisons
        if (inputCoordCurrentRASMm[dim] != inputCoordPreviousRASMm[dim]):
          same = False
          break
      if (same == False):
        self.clamps[i] = True
  
  def resetFiducialClamping(self):
    # Resets all clamp values to False
    logging.debug('resetFiducialClamping()')
    self.clamps = []
    numberOfFiducials = self.currentFiducialsNode.GetNumberOfFiducials()
    for i in range (0, numberOfFiducials):
      self.clamps.append(False)
  
  def setFiducialClamping(self):
    # Sets all clamp values to True
    logging.debug('setFiducialClamping()')
    self.clamps = []
    numberOfFiducials = self.currentFiducialsNode.GetNumberOfFiducials()
    for i in range (0, numberOfFiducials):
      self.clamps.append(True)
    
  def hermiteInterpolationXY(self, splineParameters, s, zCoordinateSliceMm):
    logging.debug('hermiteInterpolationXY()')
    a0 = splineParameters[0]
    a1 = splineParameters[1]
    a2 = splineParameters[2]
    a3 = splineParameters[3]
    xCoordinateSliceMm = a3*(s**3)+a2*(s**2)+a1*s+a0
    b0 = splineParameters[4]
    b1 = splineParameters[5]
    b2 = splineParameters[6]
    b3 = splineParameters[7]
    yCoordinateSliceMm = b3*(s**3)+b2*(s**2)+b1*s+b0
    interpolatedPointSliceMm = [xCoordinateSliceMm, yCoordinateSliceMm, zCoordinateSliceMm]
    return interpolatedPointSliceMm
    
  def inputRASMmFromFiducialList(self, fiducialNode):
    logging.debug('inputFromFiducialList()')
    # return a 2D list of points
    # index as inputCoords[pointID][dimension]
    if not fiducialNode:
      logging.error('Error in DiscreteDynamicContour::inputFromFiducialList - Fiducial list set to None. Returning empty list.')
      return []
    fiducialListLength = fiducialNode.GetNumberOfFiducials()
    inputCoordsRASMm = [] # return value, append points to this list
    for i in range(0,fiducialListLength):
      inputPointRASMm = [0,0,0]
      fiducialNode.GetNthFiducialPosition(i,inputPointRASMm)
      inputCoordsRASMm.append(inputPointRASMm)
    return inputCoordsRASMm
    
  def outputRASMmToFiducialList(self, fiducialNode, outputCoordsRASMm):
    logging.debug('outputToFiducialList()')
    if not fiducialNode:
      logging.error('Error in DiscreteDynamicContour::outputToFiducialList - Fiducial list set to None. No action done.')
      return
    # write outputCoords[pointID][dimension] to the current fiducial list
    outputNumberOfFiducials = len(outputCoordsRASMm)
    fiducialNode.RemoveAllMarkups()
    for i in range(0,outputNumberOfFiducials):
      fiducialNode.AddFiducial(outputCoordsRASMm[i][0],outputCoordsRASMm[i][1],outputCoordsRASMm[i][2])
    
  def calculateSplineParameters(self, pointIMinus1, pointI, pointIPlus1, pointIPlus2):
    logging.debug('calculateSplineParameters()')
    #TODO: Check to make sure these are all vectors with dimension 3
    # return a vector containing (in this order):
    # [a0, a1, a2, a3, b0, b1, b2, b3]
    # This is a Hermitan spline as per Ladak et al. 2000
    x0 = pointI[self.dimX]
    x1 = pointIPlus1[self.dimX]
    x0prime = self.calculateDerivative(pointIMinus1,pointIPlus1,self.dimX)
    x1prime = self.calculateDerivative(pointI,pointIPlus2,self.dimX)
    y0 = pointI[self.dimY]
    y1 = pointIPlus1[self.dimY]
    y0prime = self.calculateDerivative(pointIMinus1,pointIPlus1,self.dimY)
    y1prime = self.calculateDerivative(pointI,pointIPlus2,self.dimY)
    a0 = x0
    a1 = x0prime
    a2 = 3 * (x1-x0) - x1prime - 2 * x0prime
    a3 = 2 * (x0-x1) + x0prime + x1prime
    b0 = y0
    b1 = y0prime
    b2 = 3 * (y1-y0) - y1prime - 2 * y0prime
    b3 = 2 * (y0-y1) + y0prime + y1prime
    parameters = [a0, a1, a2, a3, b0, b1, b2, b3]
    return parameters
    
  def calculateDerivative(self, previousPoint, nextPoint, dim):
    logging.debug('calculateDerivative()')
    #TODO: Check to make sure these are all vectors with dimension 3
    derivative = (nextPoint[dim] - previousPoint[dim])
    return derivative
    
  def setupPreviousFiducialsNode(self):
    logging.debug('setupPreviousFiducialsNode()')
    nameString = 'DDC_PreviousFiducials'
    self.previousFiducialsNode = slicer.util.getNode(nameString)
    if not self.previousFiducialsNode:
      self.previousFiducialsNode=slicer.vtkMRMLMarkupsFiducialNode()
      self.previousFiducialsNode.SetName(nameString)
      slicer.mrmlScene.AddNode(self.previousFiducialsNode)
  
  def setupCurrentFiducialsNode(self):
    logging.debug('setupCurrentFiducialsNode()')
    nameString = 'DDC_CurrentFiducials'
    self.currentFiducialsNode = slicer.util.getNode(nameString)
    if not self.currentFiducialsNode:
      self.currentFiducialsNode=slicer.vtkMRMLMarkupsFiducialNode()
      self.currentFiducialsNode.SetName(nameString)
      slicer.mrmlScene.AddNode(self.currentFiducialsNode)
  
  def setupDeformPreviewModelNode(self):
    logging.debug('setupDeformPreviewModelNode()')
    nameString = 'DDC_DeformPreviewModel'
    self.deformPreviewModelNode = slicer.util.getNode(nameString)
    if not self.deformPreviewModelNode:
      self.deformPreviewModelNode=slicer.vtkMRMLModelNode()
      self.deformPreviewModelNode.SetName(nameString)
      slicer.mrmlScene.AddNode(self.deformPreviewModelNode)
      
  def setupOutputVolumeNode(self):
    logging.debug('setupOutputVolumeNode()')
    nameString = 'DDC_OutputScalarVolume'
    self.outputVolumeNode = slicer.util.getNode(nameString)
    if not self.outputVolumeNode:
      self.outputVolumeNode=slicer.vtkMRMLScalarVolumeNode()
      self.outputVolumeNode.SetName(nameString)
      slicer.mrmlScene.AddNode(self.outputVolumeNode)

  def deformContour(self):
    # TODO: Move the contour toward the tumor boundary. Do this by calculating the gradient on a convoluted slice
    sliceCornerImage = self.getImageFromSlice()
    
    gaussianSmooth = vtk.vtkImageGaussianSmooth()
    gaussianSmooth.SetStandardDeviations(self.gaussianCharacteristicWidthPx,self.gaussianCharacteristicWidthPx,0)
    gaussianSmooth.SetInputData(sliceCornerImage)
    gaussianSmooth.Update()
    
    numDimensions = 2 #2d image
    gradientMagnitudeFilter = vtk.vtkImageGradientMagnitude()
    gradientMagnitudeFilter.SetDimensionality(numDimensions)
    gradientMagnitudeFilter.SetInputData(gaussianSmooth.GetOutput())
    gradientMagnitudeFilter.Update()
    
    energyImage = gradientMagnitudeFilter.GetOutput()
    
    gradientFilter = vtk.vtkImageGradient()
    gradientFilter.SetInputData(energyImage)
    gradientFilter.SetDimensionality(numDimensions)
    gradientFilter.Update()
    
    self.gradientImage = gradientFilter.GetOutput()
    
    self.setupOutputVolumeNode()
    self.outputVolumeNode.SetAndObserveImageData(self.gradientImage)
    self.outputVolumeNode.SetIJKToRASMatrix(self.getSliceCornerToRAS())
    
    writer = vtk.vtkMetaImageWriter()
    writer.SetInputData(self.gradientImage)
    writer.SetFileName('C:/Users/vaughan/devel/SlicerIGT-Source/trunk/LumpNav/data/ThomasSandbox/gradientImage.mha')
    writer.Write()
    
    #self.updateFiducialClamping()
    #self.resampleFiducials()
  
  def getImageFromSlice(self):
    logging.debug('getImageFromSlice()')
    
    SliceCenterToIJKMatrix = self.getSliceCenterToIJKMatrix()
    inputImage = self.inputVolumeNode.GetImageData()
    
    backgroundColor = 0
    
    reslice = vtk.vtkImageReslice()
    reslice.SetInputData(inputImage)
    reslice.SetResliceAxes(SliceCenterToIJKMatrix)
    reslice.SetBackgroundColor(backgroundColor,backgroundColor,backgroundColor,1)
    reslice.SetInterpolationModeToLinear()
    reslice.SetOutputDimensionality(2)
    reslice.SetOutputSpacing(0.2,0.2,0.2)
    reslice.Update()
    
    sliceCenterImage = reslice.GetOutput()
    self.updateSliceCornerToSliceCenterTransform(sliceCenterImage)
    sliceCornerImage = self.transformSliceCenterToSliceCorner(sliceCenterImage)
    
    return sliceCornerImage
    
  def updateSliceCornerToSliceCenterTransform(self,sliceCenterImage):
    SliceCornerToSliceCenterTransform = vtk.vtkTransform()
    SliceCornerToSliceCenterTransform.Identity()
    SliceCornerToSliceCenterTransform.Translate(sliceCenterImage.GetOrigin())
    SliceCornerToSliceCenterTransform.Scale(sliceCenterImage.GetSpacing())
    self.SliceCornerToSliceCenterTransform = SliceCornerToSliceCenterTransform
    
  def transformSliceCenterToSliceCorner(self,sliceCenterImage):
    sliceCenterImage.SetOrigin(0,0,0)
    sliceCenterImage.SetSpacing(1,1,1)
    return sliceCenterImage
    
  def getSliceCornerToRAS(self):
    SliceCenterToRASTransform = vtk.vtkTransform()
    SliceCenterToRASMatrix = self.inputSliceNode.GetSliceToRAS()
    SliceCenterToRASTransform.SetMatrix(SliceCenterToRASMatrix)
    
    SliceCornerToSliceCenterTransform = self.SliceCornerToSliceCenterTransform
    
    SliceCornerToRASTransform = vtk.vtkTransform()
    SliceCornerToRASTransform.Identity()
    SliceCornerToRASTransform.PreMultiply()
    SliceCornerToRASTransform.Concatenate(SliceCenterToRASTransform)
    SliceCornerToRASTransform.Concatenate(SliceCornerToSliceCenterTransform)
    
    SliceCornerToRASMatrix = SliceCornerToRASTransform.GetMatrix()
    
    return SliceCornerToRASMatrix

  def getSliceCenterToIJKMatrix(self):   
    RASToIJKTransform = vtk.vtkTransform()
    IJKToRASMatrix = vtk.vtkMatrix4x4()
    self.inputVolumeNode.GetIJKToRASMatrix(IJKToRASMatrix)
    RASToIJKMatrix = vtk.vtkMatrix4x4()
    vtk.vtkMatrix4x4.Invert(IJKToRASMatrix,RASToIJKMatrix)
    RASToIJKTransform.SetMatrix(RASToIJKMatrix)
    
    SliceCenterToRASTransform = vtk.vtkTransform()
    SliceCenterToRASMatrix = self.inputSliceNode.GetSliceToRAS()
    SliceCenterToRASTransform.SetMatrix(SliceCenterToRASMatrix)
    
    SliceCenterToIJKTransform = vtk.vtkTransform()
    SliceCenterToIJKTransform.Identity()
    SliceCenterToIJKTransform.PreMultiply()
    SliceCenterToIJKTransform.Concatenate(RASToIJKTransform)
    SliceCenterToIJKTransform.Concatenate(SliceCenterToRASTransform)
    
    SliceCenterToIJKMatrix = SliceCenterToIJKTransform.GetMatrix()
    
    return SliceCenterToIJKMatrix
    
  def getIJKToSliceCenterMatrix(self):
    IJKToSliceCenterMatrix = vtk.vtkMatrix4x4()
    SliceCenterToIJKMatrix = self.getSliceCenterToIJKMatrix()
    vtk.vtkMatrix4x4.Invert(SliceCenterToIJKMatrix,IJKToSliceCenterMatrix)
    return IJKToSliceCenterMatrix

  #TODO: Add units to all variable names everywhere...
  
  # Good classes to know about:
  # vtkSplineFilter
  # vtkImageGaussianSmooth
  # vtkGradientFilter
  # vtkImageData
