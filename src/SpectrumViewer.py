import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import numpy as np

#
# SpectrumViewer
#

class SpectrumViewer(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SpectrumViewer" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    parent.contributors = ["Andras Lasso (Queen's University, PERK Lab)"] 
    self.parent.helpText = """
    Show a spectrum curve in real-time from a spectrum image received through OpenIGTLink. First line of the spectrum image contains wavelength, second line of the image contains intensities.
    """
    parent.acknowledgementText = """
    """

#
# SpectrumViewerWidget
#

class SpectrumViewerWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """  
  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    # VTKObservationMixin.__init__(self)
    slicer.mymod = self 
  
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Instantiate and connect widgets ...

    self.logic = SpectrumViewerLogic()
    
    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.spectrumImageSelector = slicer.qMRMLNodeComboBox()
    self.spectrumImageSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.spectrumImageSelector.selectNodeUponCreation = True
    self.spectrumImageSelector.addEnabled = False
    self.spectrumImageSelector.removeEnabled = False
    self.spectrumImageSelector.noneEnabled = False
    self.spectrumImageSelector.showHidden = False
    self.spectrumImageSelector.showChildNodeTypes = False
    self.spectrumImageSelector.setMRMLScene( slicer.mrmlScene )
    self.spectrumImageSelector.setToolTip( "Pick the spectrum image to visualize." )
    parametersFormLayout.addRow("Input spectrum image: ", self.spectrumImageSelector)
   
    #
    # output array selector
    #
    self.outputArraySelector = slicer.qMRMLNodeComboBox()
    self.outputArraySelector.nodeTypes = ( ("vtkMRMLTableNode"), "" ) # https://slicer.readthedocs.io/en/latest/developer_guide/mrml_overview.html
    self.outputArraySelector.addEnabled = True
    self.outputArraySelector.removeEnabled = True
    self.outputArraySelector.noneEnabled = False 
    self.outputArraySelector.showHidden = False
    self.outputArraySelector.showChildNodeTypes = False
    self.outputArraySelector.setMRMLScene( slicer.mrmlScene )
    self.outputArraySelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output spectrum Table: ", self.outputArraySelector)
   
    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enablePlottingCheckBox = qt.QCheckBox()
    self.enablePlottingCheckBox.checked = 0
    self.enablePlottingCheckBox.setToolTip("If checked, then the spectrum plot will be updated in real-time")
    parametersFormLayout.addRow("Enable plotting", self.enablePlottingCheckBox)

    # connections
    self.enablePlottingCheckBox.connect('stateChanged(int)', self.setEnablePlotting)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass
    
  def setEnablePlotting(self, enable):
    if enable:
      self.logic.startPlotting(self.spectrumImageSelector.currentNode(), self.outputArraySelector.currentNode())
    else:
      self.logic.stopPlotting()

#
# SpectrumViewerLogic
#

class SpectrumViewerLogic(ScriptedLoadableModuleLogic):
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
    
    self.chartNodeID = None
    self.spectrumImageNode = None
    self.observerTags = []
    self.outputArrayNode = None
    self.resolution = 100
    slicer.mymodLog = self
    self.plotChartNode = None 

  def addObservers(self):
    if self.spectrumImageNode:
      print("Add observer to {0}".format(self.spectrumImageNode.GetName()))
      self.observerTags.append([self.spectrumImageNode, self.spectrumImageNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onSpectrumImageNodeModified)])

  def removeObservers(self):
    print("Remove observers")
    for nodeTagPair in self.observerTags:
      nodeTagPair[0].RemoveObserver(nodeTagPair[1])

  def startPlotting(self, spectrumImageNode, outputArrayNode):
    # Change the layout to one that has a chart.  This created the ChartView
    ln = slicer.util.getNode(pattern='vtkMRMLLayoutNode*')
    # ln.SetViewArrangement(24)

    self.removeObservers()
    self.spectrumImageNode=spectrumImageNode
    self.outputArrayNode=outputArrayNode    

    # Start the updates
    self.addObservers()
    self.onSpectrumImageNodeModified(0,0)

  def stopPlotting(self):
    self.removeObservers()
  
  def onSpectrumImageNodeModified(self, observer, eventid):
  
    if not self.spectrumImageNode or not self.outputArrayNode:
      return
      
    self.updateOutputArray()
    #self.updateChart()




  def updateOutputArray(self):
    # Get the created table node
    tableNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLTableNode')

    numberOfPoints = self.spectrumImageNode.GetImageData().GetDimensions()[0]
    numberOfRows = self.spectrumImageNode.GetImageData().GetDimensions()[1]
    if numberOfRows!=2:
      logging.error("Spectrum image is expected to have exactly 2 rows, got {0}".format(numberOfRows))
      return

    I = slicer.util.getNode('Image_Image') # Update this to grab it from selector
    A = slicer.util.arrayFromVolume(I)
    A = np.squeeze(A)
    A = np.transpose(A)
    # histogram = np.histogram(A, bins=100)

    # Save results to a new table node
    if self.plotChartNode is None:
      tableNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
    #slicer.util.updateTableFromArray(tableNode,histogram)
    slicer.util.updateTableFromArray(tableNode,A)
    tableNode.GetTable().GetColumn(0).SetName("Wavelength")
    tableNode.GetTable().GetColumn(1).SetName("Intensity")

    # Create plot
    # 
    if self.plotChartNode is None:
      # plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", I.GetName() + " histogram")
      plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", I.GetName() + " plot")
      print ('here')
    plotSeriesNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLPlotSeriesNode") 
    plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
    plotSeriesNode.SetXColumnName("Wavelength")
    plotSeriesNode.SetYColumnName("Intensity")
    plotSeriesNode.SetPlotType(plotSeriesNode.PlotTypeScatter) # This is where to switch it to Scatter
    plotSeriesNode.SetColor(0, 0.6, 1.0)

    # Create chart and add plot
    # Stop it from creating a plot on every loop
    if self.plotChartNode is None:
      plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode")
    plotChartNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLPlotChartNode") 
    plotChartNode.SetAndObservePlotSeriesNodeID(plotSeriesNode.GetID()) # look for set and observe
    plotChartNode.YAxisRangeAutoOff()
    plotChartNode.SetYAxisRange(0, 1)
    self.plotChartNode = plotChartNode   
    # Show plot in layout
    slicer.modules.plots.logic().ShowChartInLayout(plotChartNode)




  """ def updateOutputArray2(self):
   
    numberOfPoints = self.spectrumImageNode.GetImageData().GetDimensions()[0]
    numberOfRows = self.spectrumImageNode.GetImageData().GetDimensions()[1]
    if numberOfRows!=2:
      logging.error("Spectrum image is expected to have exactly 2 rows, got {0}".format(numberOfRows))
      return

    # Create arrays of data  
    # a = self.outputArrayNode.GetArray()
    # a.SetNumberOfTuples(self.resolution)

    #This part appears to be filtering the data and preping it for display. Not sure its purpose
    for row in range(numberOfRows):
      lineSource=vtk.vtkLineSource()
      lineSource.SetPoint1(0,row,0)
      lineSource.SetPoint2(numberOfPoints-1,row,0)
      lineSource.SetResolution(self.resolution-1)
      probeFilter=vtk.vtkProbeFilter()
      probeFilter.SetInputConnection(lineSource.GetOutputPort())
      if vtk.VTK_MAJOR_VERSION <= 5:
        probeFilter.SetSource(self.spectrumImageNode.GetImageData())
      else:
        probeFilter.SetSourceData(self.spectrumImageNode.GetImageData())
      probeFilter.Update()
      self.probedPoints=probeFilter.GetOutput()
      self.probedPointScalars= self.probedPoints.GetPointData().GetScalars()
      # for i in xrange(self.resolution):
        # a.SetComponent(i, row, probedPointScalars.GetTuple(i)[0])

    # for i in xrange(self.resolution):
      # a.SetComponent(i, 2, 0)
    self.probedPoints.GetPointData().GetScalars().Modified() """

  # This function is used to create and update the chart node 
  def updateChart(self):
    
    # Get the first PlotChart node
    pcn = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLPlotChartNode')
    
    # If we already created a chart node and it still exists then reuse that node
    cn = None
    # If there is one then reuse it
    if self.chartNodeID: # this is None upon initialization
      cn = slicer.mrmlScene.GetNodeByID(pcn.GetID())
      print('in 1')
      name = self.spectrumImageNode.GetName()
      print(name)
      # print(self.outputArrayNode.GetTable())
      # I then want to populate the chart using the data from the table
      """ ChA_ChartNode = slicer.util.plot(np.array([0,0,0,0,0,0,0]), 0)

      layoutManager = slicer.app.layoutManager()
      layoutWithPlot = slicer.modules.plots.logic().GetLayoutWithPlot(layoutManager.layout)
      layoutManager.setLayout(layoutWithPlot)
      plotWidget = layoutManager.plotWidget(0)
      plotViewNode = plotWidget.mrmlPlotViewNode()
      plotViewNode.SetPlotChartNodeID(ChA_ChartNode.GetID()) """

    # If there isnt one then create one
    if not cn:
      print('in 2')
      cn = slicer.mrmlScene.AddNode(slicer.vtkMRMLPlotChartNode())
      self.chartNodeID = cn.GetID()
      # This is broken
      # Configure properties of the Chart - GetPlotDataNodeReferenceRole() in doc shows list of attribute to change
      """ cn.SetProperty('default', 'title', 'Spectrum')
      cn.SetProperty('default', 'xAxisLabel', 'Wavelength (nm)')
      cn.SetProperty('default', 'yAxisLabel', 'Intensity') """

    # Now I need to get the chart to pop up
    

    # ******************************************************************************************
""" def updateChart2(self):
    # Get the first ChartView node
    cvn = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLPlotChartNode') #************
    # cvn = slicer.util.getNode(pattern='vtkMRMLPlotChartNode*')

    # If we already created a chart node and it is still exists then reuse that
    cn = None
    if self.chartNodeID:
      cn = slicer.mrmlScene.GetNodeByID(cvn.GetID())
      # cn = slicer.mrmlScene.GetNodeByID(cvn.GetChartNodeID()) # GetChartNodeID is depreciated
    if not cn:
      cn = slicer.mrmlScene.AddNode(slicer.vtkMRMLPlotChartNode()) # ***************
      self.chartNodeID = cn.GetID()
      # Configure properties of the Chart
      cn.SetProperty('default', 'title', 'Spectrum')
      cn.SetProperty('default', 'xAxisLabel', 'Wavelength (nm)')
      cn.SetProperty('default', 'yAxisLabel', 'Intensity')  
    
    name = self.spectrumImageNode.GetName()

    # ** This is no longer an array, now it is a table
    cn.AddArray(name, self.outputArrayNode.GetID())
    
    # Set the chart to display
    cvn.SetChartNodeID(cn.GetID())
    cvn.Modified() """

 
class SpectrumViewerTest(ScriptedLoadableModuleTest):
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
    self.test_SpectrumViewer1()

  def test_SpectrumViewer1(self):
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

    self.delayDisplay('Test passed! (No testing was actually performed)')
