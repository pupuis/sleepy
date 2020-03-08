
from sleepy.tagging.model import Navigator
from sleepy.tagging.model.event import EventTypeNotSupported, PointEvent, IntervalEvent
from sleepy.processing.algorithms import Massimi
from sleepy.processing.options import OptionView
from sleepy.processing.engine import Engine
from sleepy.processing import exceptions
from PyQt5.QtWidgets import QVBoxLayout, QGroupBox, QCheckBox, QComboBox
from PyQt5.QtWidgets import QStackedWidget
import numpy as np
import pdb

class FileProcessor:
    def __init__(self, applicationSettings):

        self.engine = Engine()

        self.algorithms = [Massimi(self.engine), Massimi(self.engine)]

        self.currentAlgorithm = None

        self.applicationSettings = applicationSettings

        self.labels = None
        self.dataSet = None

    @property
    def optionView(self):

        try:
            return self._optionView
        except AttributeError:

            self._optionView = OptionView(self)

            return self._optionView

    @property
    def options(self):
        return self.optionView.options

    def onAlgorithmSelection(self, index):

        if index == 0:

            self.currentAlgorithm = None

        else:

            self.currentAlgorithm = self.algorithms[index - 1]

            return self.currentAlgorithm.options

    def run(self, algorithm, dataSet):
        """Public API to execute an algorithm on a data-set. Is also used
        internally. The method calls its internal engine to provide a run-time
        environment for the algorithm.

        :param algorithm: Algorithm object that implements the method
        compute that receives a vector and a sampling rate and computes a list
        of either 2D-intervals or points.

        :param dataSet: Data-set object that provides the properties channelData,
        samplingRate and epochs.
        """

        return self.engine.run(
            algorithm,
            dataSet
        )

    def getLabels(self, dataSet):

        if self.currentAlgorithm:

            return self.run(self.currentAlgorithm, dataSet)

        else:

            return dataSet.labels

    def computeLabels(self, dataSet):
        """Computes the labels based on the dataset and buffers dataset and
        computed labels. This needs to be called before computeNavigator.
        """

        self.dataSet = dataSet

        self.labels = self.getLabels(dataSet)

    def computeNavigator(self):
        """Computes a navigator instance from the buffered dataset and computed
        labels in computeLabels
        """

        self.checkComputeLabelsCalled()

        changesMade = self.updateLabels(self.labels)

        events = self.convertLabelsToEvents()

        self.navigator = Navigator(events, changesMade)

        return self.navigator

    def checkComputeLabelsCalled(self):

        if self.labels is None or self.dataSet is None:
            raise exceptions.ComputeLabelsNotCalled

    def updateLabels(self, labels):

        changesMade = self.resultDiffers(labels)

        self.dataSet.labels = labels

        if changesMade:
            self.dataSet.removeCheckpoint()

        return changesMade

    def showNumberOfLabels(self):

        self.checkComputeLabelsCalled()

        self.optionView.showNumberOfLabels(len(self.labels))

    def resultDiffers(self, result):

        if result.shape == self.dataSet.labels.shape:

            return not (result.tolist() == self.dataSet.labels.tolist())

        return True

    def convertLabelsToEvents(self):

        events = []

        for labelIndex in range(self.dataSet.numberOfLabels):

            dataSource = self.dataSet.getDataSourceFor(labelIndex)

            tag = self.dataSet.tags[labelIndex]

            event = self.deriveEvent(labelIndex, dataSource)

            if tag > 0:
                event.switchTag()

            events.append(event)

        return events

    def deriveEvent(self, labelIndex, dataSource):

        label = self.dataSet.labels[labelIndex]

        # Currently unclear, how to solve this other than by checking shapes
        if isinstance(label, np.int32):

            return PointEvent(label, dataSource, self.applicationSettings)

        elif label.shape == (2,):

            return IntervalEvent(*label, dataSource, self.applicationSettings)

        else:

            raise EventTypeNotSupported
