'''
Requests replicas can send to :class:`.ExchangeMaster` or other :class:`.Replica` objects
'''

from collections import namedtuple


GetStateAndNegativeLogProbRequest = namedtuple('GetStateAndNegativeLogProbRequest', 'sender')
StoreStateNegativeLogProbRequest = namedtuple('StoreStateNegativeLogProbRequest', 'sender state negative_log_prob')
DoNothingRequest = namedtuple('DoNothingRequest', 'sender')
