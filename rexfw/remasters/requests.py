'''
Requests :class:`.ExchangeMaster` objects can send to :class:`.Replica` objects
'''

from collections import namedtuple


SampleRequest = namedtuple('SampleRequest', 'sender')
DieRequest = namedtuple('DieRequest', 'sender')
ProposeRequest = namedtuple('ProposeRequest', 'sender partner params')
AcceptBufferedProposalRequest = namedtuple('AcceptBufferedProposalRequest', 'sender accept')
GetStateAndNegativeLogProbRequest = namedtuple('GetStateAndNegativeLogProbRequest', 'sender partner')
SendGetStateAndNegativeLogProbRequest = namedtuple('SendGetStateAndNegativeLogProbRequest', 'sender partner')
DumpSamplesRequest = namedtuple('DumpSamplesRequest', 'sender s_min s_max offset dump_step')
SendStatsRequest = namedtuple('SendStatsRequest', 'sender')
