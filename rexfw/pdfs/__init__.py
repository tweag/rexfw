'''
Defines the interface for compatible PDFs:
all they need is a log_prob method which returns the
log-probability of a state
'''

from abc import abstractmethod

class AbstractPDF(object):

    @abstractmethod
    def log_prob(self, x):
        pass

    def bare_log_prob(self, x):
        # TODO: this is only to make the normal.py example script and possibly
        # tests happy
        return self.log_prob(x)
