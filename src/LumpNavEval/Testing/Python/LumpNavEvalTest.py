import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy, math
from slicer.util import getNode, getNodes
from slicer import modules, app

import LumpNavEval


#
# LumpNavEvalTest
#

class LumpNavEvalTest(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LumpNavEvalTest" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Testing.TestCases"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.
#
# LumpNavEvalTestWidget
#

class LumpNavEvalTestWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)


  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()


#
# LumpNavEvalTestLogic
#

class LumpNavEvalTestLogic(ScriptedLoadableModuleLogic): 
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    self.layoutManager = app.layoutManager()

  def run(self):
    logic = LumpNavEval.LumpNavEvalLogic()
    numpassed = 0

    self.delayDisplay("Starting the test")
    # zero degrees
    directionVector1 = numpy.array([0, 1, 0, 0])
    planeVector = numpy.array([0, 1, 0, 0])
    logic.calculateAngle(directionVector1, planeVector)
    angle0 = logic.getAngleDegrees()
    if angle0 == 0.0:
      print "0 Degrees: Test Passed."
      numpassed += 1
    else:
      print "0 Degrees: Test Failed."

    # 30 degrees
    directionVector2 = numpy.array([math.sqrt(3), 3,0,0])
    logic.calculateAngle(directionVector2, planeVector)
    angle30 =  logic.getAngleDegrees()
    if angle30 == 30.0:
      print "30 Degrees: Test Passed."
      numpassed += 1
    else:
      print "30 Degrees: Test Failed."

    # 45 degrees
    directionVector3 = numpy.array([1, 1, 0, 0])
    logic.calculateAngle(directionVector3, planeVector)
    angle45 =  logic.getAngleDegrees()
    if angle45 == 45.0:
      print "45 Degrees: Test Passed."
      numpassed += 1
    else:
      print "45 Degrees: Test Failed."

    # 60 degrees
    directionVector4 = numpy.array([math.sqrt(3) / 2.0, 0.5, 0, 0])
    logic.calculateAngle(directionVector4, planeVector)
    angle60 = logic.getAngleDegrees()
    if angle60 == 60.0:
      print "60 Degrees: Test Passed."
      numpassed += 1
    else:
      print "60 Degrees: Test Failed."

    # 90 degrees
    directionVector5 = numpy.array([1, 0, 0, 0])
    logic.calculateAngle(directionVector5, planeVector)
    angle90 =  logic.getAngleDegrees()
    if angle90 == 90.0:
      print "90 Degrees: Test Passed."
      numpassed += 1
    else:
      print "90 Degrees: Test Failed."

    # 135 degrees
    directionVector3 = numpy.array([1, -1, 0, 0])
    logic.calculateAngle(directionVector3, planeVector)
    angle135 =  logic.getAngleDegrees()
    if angle135 == 135.0:
      print "135 Degrees: Test Passed."
      numpassed += 1
    else:
      print "135 Degrees: Test Failed."

    # 180 degrees same as 0
    directionVector6 = numpy.array([0, -1, 0, 0])
    logic.calculateAngle(directionVector6, planeVector)
    angle180 =  logic.getAngleDegrees()
    if angle180 == 180.0:
      print "180 Degrees: Test Passed."
      numpassed += 1
    else:
      print "180 Degrees: Test Failed."

    return numpassed

class LumpNavEvalTestTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    pass

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_LumpNavEvalTest()

  def test_LumpNavEvalTest(self):
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
    logic = LumpNavEvalTestLogic()
    numpassed = logic.run()

    if numpassed == 7:
      self.delayDisplay("Tests Complete")
    else:
      rate = "Test Failed: " + str(numpassed) + "/7 Tests Passed."
      self.delayDisplay(rate)
      finalmsg = str(7-numpassed) + " Test Case(s)"
      raise LumpNavEvalTestException(finalmsg)

class LumpNavEvalTestException(Exception):
  pass