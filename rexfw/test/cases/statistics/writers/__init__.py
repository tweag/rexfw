'''
'''
import unittest
from rexfw.remasters import RESwapStats
from rexfw.samplers.rwmc import RWMCSampleStats
from rexfw.statistics import FilterableQuantityList
from rexfw.statistics.logged_quantities import SamplerStepsize
from rexfw.statistics.averages import REAcceptanceRateAverage
from rexfw.statistics.writers import AbstractStatisticsWriter
from rexfw.statistics.writers.http import (AbstractHTTPStatisticsWriter,
                                           REHTTPStatisticsWriter,
                                           MCMCHTTPStatisticsWriter)


class MockStatisticsWriter(AbstractStatisticsWriter):
    def __init__(self):
        super(MockStatisticsWriter, self).__init__('8-)')

    def write(self, step, elements):
        pass


class MockedAbstractHTTPStatisticsWriter(AbstractHTTPStatisticsWriter):
    _data_prefix = "prefix_"

    def _sort_quantities(self, quantities):
        return quantities

    def _sanitize_value(self, value):
        return value


def setup_test_writer(writer_class):
    # little demo of the quantity objects: in the following list, we have
    # a "normal" logged quantity, the stepsize. It has a fixed value and
    # its current value only depends on whatever it last was updated with.
    # The acceptance rate quantity object, on the other hand, is an
    # averaged logged quantity. It basically keeps a state of the current
    # average and updates that average, once a new acceptance / rejection
    # info comes in via the update() method.
    quantities = [SamplerStepsize('replica22', 'x'),
                  REAcceptanceRateAverage('replica3', 'replica2')]
    quantities = FilterableQuantityList(quantities)

    quantities[0].update(123, {'x': RWMCSampleStats(True, 1, 0.1)})
    quantities[1].update(123, RESwapStats(False, [0.0], [0.0]))
    # Now, current_value() of quantities[1] is 0.0
    quantities[1].update(124, RESwapStats(True, [0.0], [0.0]))
    # But now, it is 0.5. Magic, huh?

    return writer_class("doesntexist", ["myvar", "myothervar"], quantities)


class testAbstractHTTPStatisticsWriter(unittest.TestCase):

    def setUp(self):
        self._writer = setup_test_writer(MockedAbstractHTTPStatisticsWriter)        

    def testQuantitiesToJSONableDict(self):
        res1 = self._writer._quantities_to_JSONable_dict(
            'stepsize', [self._writer.quantities_to_write[0]])
        expected = {'stepsize': [0.1]}
        self.assertEqual(res1, expected)

        res2 = self._writer._quantities_to_JSONable_dict(
            'acceptance rate', [self._writer.quantities_to_write[1]])
        expected = {'acceptance rate': [0.5]}
        self.assertEqual(res2, expected)

    def testMakeDataDict(self):
        res1 = self._writer._make_data_dict(
            FilterableQuantityList(self._writer.quantities_to_write[:2]))
        expected = {'prefix_statistics':
                    {'stepsize': [0.1], 'acceptance rate': [0.5]}}
        self.assertEqual(res1, expected)

        res2 = self._writer._make_data_dict(
            FilterableQuantityList(self._writer.quantities_to_write[1:]))
        expected = {'prefix_statistics': {'acceptance rate': [0.5]}}
        self.assertEqual(res2, expected)

    def testAugmentWithMetadata(self):
        res = self._writer._augment_with_metadata({'somekey': 42}, 321)
        expected = {'mcmc_step': 321, 'somekey': 42}
        self.assertEqual(res, expected)


class testREHTTPStatisticsWriter(unittest.TestCase):
    def setUp(self):
        self._writer = setup_test_writer(REHTTPStatisticsWriter)

    def testSortQuantities(self):
        quants = self._writer.quantities_to_write
        res = self._writer._sort_quantities(quants)
        expected = [quants[1], quants[0]]
        self.assertEqual(res, expected)

    def testSanitizeValue(self):
        res1 = self._writer._sanitize_value(None)
        expected1 = 0.0
        self.assertEqual(res1, expected1)

        res2 = self._writer._sanitize_value(0.42)
        expected2 = 0.42
        self.assertEqual(res2, expected2)


class testMCMCHTTPStatisticsWriter(unittest.TestCase):
    def setUp(self):
        self._writer = setup_test_writer(MCMCHTTPStatisticsWriter)

    def testSortQuantities(self):
        quants = self._writer.quantities_to_write
        res = self._writer._sort_quantities(quants)
        expected = [quants[1], quants[0]]
        self.assertEqual(res, expected)

    def testSanitizeValue(self):
        res1 = self._writer._sanitize_value(None)
        expected1 = 0.0
        self.assertEqual(res1, expected1)

        res2 = self._writer._sanitize_value(0.42)
        expected2 = 0.42
        self.assertEqual(res2, expected2)
