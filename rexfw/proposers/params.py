'''
Simple parameter objects holding information :class:`.AbstractProposer` objects
might need to calculate proposals
'''
from abc import abstractmethod


class AbstractProposerParams(object):
    @abstractmethod
    def reverse(self):
        '''
        Reverses certain parameters to reuse this object for both
        forward and reverse trajectories
        '''
        pass


class REProposerParams(AbstractProposerParams):
    def reverse(self):
        pass
