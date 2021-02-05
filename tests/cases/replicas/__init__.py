'''
'''

import unittest
import numpy as np
from collections import deque

from rexfw import Parcel
from rexfw.remasters import ExchangeMaster
from rexfw.slgenerators import ExchangeParams
from rexfw.proposers.params import REProposerParams
from rexfw.replicas import Replica
from ..communicators.test_communicators import MockCommunicator
from ..communicators.test_communicators import DoNothingRequestReceivingMockCommunicator
from ..statistics import MockStatistics, MockREStatistics
from ..proposers.test_proposers import MockProposer
from ..statistics import MockStatistics, MockREStatistics
from ..proposers import MockProposer

from resaas.common.storage import SimulationStorage, LocalStorageBackend


class MockStorageBackend:
    data = {}

    def write(self, data, file_name, data_type):
        self.data[file_name] = data

    def read(self, file_name, data_type):
        return self.data[file_name]


class MockPDF(object):

    def log_prob(self, x):

        return x

class MockReplica(Replica):

    def __init__(self, comm):

        storage = SimulationStorage('', sim_path='/test',
                                    storage_backend=MockStorageBackend())
        super(MockReplica, self).__init__('replica1', 4, MockPDF(),
                                          MockSampler, {'testparam': 4}, 
                                          {'mock_proposer1': MockProposer()},
                                          storage, comm)

        self._request_processing_table.update(TestRequest='self._process_test_request({})')
        self.test_request_processed = 0

    def _process_test_request(self, request):

        self.test_request_processed += 1

        
class ProposeMockReplica(MockReplica):

    def __init__(self, comm):

        super(ProposeMockReplica, self).__init__(comm)

        self.works_heats_sent = False
        self._buffered_partner_state = 34
        self._buffered_partner_negative_log_prob = 66
        self._buffered_proposal = 44

    def _calculate_proposal(self, request):

        from rexfw.proposers import GeneralTrajectory
        
        return GeneralTrajectory([0, 4], 23, 42)

    def _send_works_heats(self, proposal):

        self.works_heats_sent = True
    

class CalculateProposalMockReplica(MockReplica):

    def __init__(self, comm):

        super(CalculateProposalMockReplica, self).__init__(comm)

        self._buffered_partner_state = 34
        self._buffered_partner_negative_log_prob = 66
        self.pick_proposer_called = 0

    def _pick_proposer(self, params):

        self.pick_proposer_called += 1
        return 'mock_proposer1'

    def get_negative_log_prob(self, state):

        return 42

    
class SetupSamplerMockReplica(Replica):

    def __init__(self):

        self.sampler_class = MockSampler
        self.pdf = MockPDF()
        self._state = 5
        self.sampler_params = {'testparam': 4}


class MockSampler(object):

    def __init__(self, pdf, state, testparam):

        self.pdf = pdf
        self.state = state
        self.testparam = testparam
        self.last_sampled = None
        self.sampler_stats = None

    def sample(self):

        self.last_sampled = self.state ** 2
        
        return self.last_sampled

    @property
    def last_draw_stats(self):

        return 'nope'


class testReplica(unittest.TestCase):

    def setUp(self):

        self._replica = MockReplica(MockCommunicator())

    def testSetupSampler(self):

        self._replica = SetupSamplerMockReplica()
        
        self._replica._setup_sampler()

        self.assertTrue(isinstance(self._replica._sampler, MockSampler))
        sampler = self._replica._sampler
        self.assertTrue(isinstance(sampler.pdf, MockPDF))
        self.assertEqual(sampler.state, self._replica.state)
        self.assertEqual(sampler.testparam, 4)

    def testStateGetter(self):
        ## TODO
        pass

    def testStateSetter(self):
        ## TODO
        pass

    def _checkParcel(self, obj, dest, sender=None):
        ## TODO: code duplication; similar code in other test cases
        from rexfw import Parcel

        if sender is None:
            sender = self._replica.name
        self.assertTrue(isinstance(obj, Parcel))
        self.assertEqual(obj.sender, sender)
        self.assertEqual(obj.receiver, dest)
    
    def testSendStateAndNegativeLogProb(self):

        from rexfw.replicas.requests import GetStateAndNegativeLogProbRequest
        
        sender = self._replica.name
        other = 'replica23'
        req = GetStateAndNegativeLogProbRequest(other)
        self._replica._send_state_and_negative_log_prob(req)

        last_sent, dest = self._replica._comm.sent.pop()
        self.assertEqual(dest, other)
        self._checkParcel(last_sent, other, sender)
        self.assertEqual(last_sent.data.sender, self._replica.name)
        self.assertEqual(last_sent.data.state, self._replica.state)
        self.assertEqual(last_sent.data.negative_log_prob, self._replica.negative_log_prob)

    def testSendGetStateAndNegativeLogProbRequest(self):

        from rexfw.remasters.requests import SendGetStateAndNegativeLogProbRequest
        from rexfw.replicas.requests import GetStateAndNegativeLogProbRequest
        
        other = 'replica123'
        req = SendGetStateAndNegativeLogProbRequest('remaster0', other)
        self._replica._send_get_state_and_negative_log_prob_request(req)

        last_sent, dest = self._replica._comm.sent.pop()
        self.assertEqual(dest, 'replica123')
        self._checkParcel(last_sent, other, self._replica.name)
        self.assertTrue(isinstance(last_sent.data, GetStateAndNegativeLogProbRequest))
        self.assertEqual(last_sent.data.sender, self._replica.name)

    def testStoreStateNegativeLogProb(self):

        from rexfw.replicas.requests import StoreStateNegativeLogProbRequest, DoNothingRequest

        other = 'replica234'
        req = StoreStateNegativeLogProbRequest(other, 2.5, 99)
        self._replica._store_state_negative_log_prob(req)

        self.assertEqual(self._replica._buffered_partner_state, 2.5)
        self.assertEqual(self._replica._buffered_partner_negative_log_prob, 99)
        last_sent, dest = self._replica._comm.sent.pop()
        self.assertEqual(dest, self._replica._current_master)
        self._checkParcel(last_sent, self._replica._current_master, self._replica.name)
        self.assertTrue(isinstance(last_sent.data, DoNothingRequest))
        self.assertEqual(last_sent.data.sender, self._replica.name)

    def testSample(self):

        old_state = self._replica.state
        self._replica._sample(None)
        
        self.assertEqual(self._replica._sampler.last_sampled, old_state ** 2)
        self.assertEqual(self._replica.samples[-1], old_state ** 2)
        self.assertEqual(self._replica.sampler_stats[-1][0], 0)
        self.assertEqual(self._replica.sampler_stats[-1][1], 'nope')
        self.assertEqual(self._replica._n_samples_drawn, 1)
        self.assertEqual(self._replica.energy_trace[-1], -old_state ** 2)

    def testSendStats(self):

        from rexfw.remasters.requests import SendStatsRequest
        
        self._replica.sampler_stats.append(123)
        self._replica._send_stats(SendStatsRequest('remaster23'))
        
        last_sent, dest = self._replica._comm.sent.pop()
        self.assertEqual(dest, 'remaster23')
        self._checkParcel(last_sent, 'remaster23', self._replica.name)
        self.assertTrue(isinstance(last_sent.data, list))
        self.assertEqual(last_sent.data[-1], 123)
        
    def testDumpSamples(self):

        import os
        import numpy as np
        from rexfw.remasters.requests import DumpSamplesRequest

        smin, smax = 3000, 4000
        offset = 2
        step = 2
        req = DumpSamplesRequest('remaster45', smin, smax, offset, step)
        buffered_samples = np.arange(1000)
        self._replica.samples = buffered_samples
        self._replica._dump_samples(req)

        output_folder = self._replica.storage.sim_path
        fname = '{}/samples/samples_{}_{}-{}.pickle'.format(
            output_folder, self._replica.name, smin + offset,
            smax + offset)
        backend = self._replica.storage._storage_backend
        self.assertTrue(fname in backend.data)
        dumped_samples = backend.data[fname]
        self.assertTrue(np.all(np.array(dumped_samples) == buffered_samples[::step]))
        self.assertEqual(len(self._replica.samples), 0)

    def testDumpEnergies(self):

        import os
        import numpy as np
        from rexfw.remasters.requests import DumpSamplesRequest

        smin, smax = 3000, 4000
        offset = 2
        step = 2
        req = DumpSamplesRequest('remaster45', smin, smax, offset, step)

        self._replica.energy_trace = [3]
        self._replica._dump_energies(req)

        output_folder = self._replica.storage.sim_path
        fname = '{}/energies/energies_{}_{}-{}.pickle'.format(
            output_folder, self._replica.name, smin + offset,
            smax + offset)
        backend = self._replica.storage._storage_backend
        energies = backend.data[fname]
        self.assertEqual(len(energies), 1)
        self.assertEqual(energies[0], 3)
        self.assertEqual(len(self._replica.energy_trace), 0)

    def testProcessRequest(self):

        from collections import namedtuple

        TestRequest = namedtuple('TestRequest', '')
        self._replica.process_request(TestRequest())

        self.assertEqual(self._replica.test_request_processed, 1)

    def testPropose(self):

        from rexfw.remasters import ProposeRequest
        from rexfw.slgenerators import ExchangeParams
        from rexfw.proposers.params import REProposerParams
        
        self._replica = ProposeMockReplica(MockCommunicator())

        req = ProposeRequest('remaster34', 'replica22', 
                             ExchangeParams(['mock_proposer1', 'mock_proposer2'],
                                            REProposerParams()))
        self._replica._propose(req)

        self.assertTrue(self._replica.works_heats_sent)
        self.assertEqual(self._replica._buffered_proposal, 4)

    def testSendWorksHeats(self):

        from rexfw.proposers import GeneralTrajectory

        proposal = GeneralTrajectory([0, 7], 4, 6)
        self._replica._send_works_heats(proposal)

        last_sent, dest = self._replica._comm.sent[-1]
        self.assertEqual(dest, self._replica._current_master)
        self._checkParcel(last_sent, self._replica._current_master, self._replica.name)
        self.assertEqual(last_sent.data, (4, 6))

    def testPickProposer(self):

        from rexfw.slgenerators import ExchangeParams
        
        params = ExchangeParams(['mock_proposer1', 'mock_proposer2'], None)
        proposer = self._replica._pick_proposer(params)

        self.assertEqual(proposer, list(self._replica.proposers.items())[0][0])

    def testCalculateProposal(self):

        from rexfw.remasters import ProposeRequest
        from rexfw.slgenerators import ExchangeParams
        from rexfw.proposers import GeneralTrajectory
        from rexfw.proposers.params import REProposerParams
        
        self._replica = CalculateProposalMockReplica(MockCommunicator())

        req = ProposeRequest('remaster34', 'replica22', 
                             ExchangeParams(['mock_proposer1', 'mock_proposer2'],
                                            REProposerParams()))
        result = self._replica._calculate_proposal(req)

        self.assertEqual(self._replica.pick_proposer_called, 1)
        self.assertEqual(self._replica.proposers['mock_proposer1'].partner_name, 'replica22')
        self.assertTrue(isinstance(result, GeneralTrajectory))
        self.assertEqual(result[:], [0, 1])
        self.assertEqual(result.heat, 0)
        self.assertEqual(result.work, 0)

    def _checkAcceptBufferedProposal(self, accepted):

        if accepted:
            self.assertEqual(self._replica.state, self._replica._buffered_proposal)
            self.assertEqual(self._replica.samples[-1], self._replica._buffered_proposal)
        else:
            self.assertEqual(self._replica.state, 4)
            self.assertEqual(self._replica.samples[-1], 4)
        last_sent, dest = self._replica._comm.sent.pop()
        self.assertEqual(dest, self._replica._current_master)
        self._checkParcel(last_sent, self._replica._current_master, self._replica.name)
        self.assertEqual(self._replica.energy_trace[-1], self._replica.energy)
        self.assertEqual(self._replica._n_samples_drawn, 1)
        
    def testAcceptBufferedProposal(self):

        from rexfw.remasters.requests import AcceptBufferedProposalRequest

        for accepted in (True, False):
            self._replica = ProposeMockReplica(MockCommunicator())
            req = AcceptBufferedProposalRequest(self._replica._current_master, accepted)
            self._replica._accept_buffered_proposal(req)
            self._checkAcceptBufferedProposal(accepted)

    def testNegativeLogProb(self):

        self._replica = CalculateProposalMockReplica(MockCommunicator())
        self.assertEqual(self._replica.negative_log_prob, 42)

    def testGetNegativeLogProb(self):

        self.assertEqual(self._replica.get_negative_log_prob(5), -5)
        self.assertEqual(self._replica.get_negative_log_prob(np.array([7]))[0], -7)
                
if __name__ == '__main__':

    unittest.main()
