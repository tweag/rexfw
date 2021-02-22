'''
A Metropolis-Hastings sampler as an example for the sampler interface
'''

import numpy as np
from collections import namedtuple

from rexfw.samplers import AbstractSampler


RWMCSampleStats = namedtuple('RWMCSampleStats', 'accepted total stepsize neg_log_prob')


class RWMCSampler(AbstractSampler):

    def __init__(self, pdf, state, stepsize, timestep_adaption_limit=0,
                 adaption_uprate=1.05, adaption_downrate=0.95,
                 variable_name='x'):

        super(RWMCSampler, self).__init__(pdf, state, variable_name)

        self.stepsize = stepsize
        self.timestep_adaption_limit = timestep_adaption_limit
        self.adaption_uprate = adaption_uprate
        self.adaption_downrate = adaption_downrate
        self._last_move_accepted = False
        self._n_moves = 0

    @property
    def last_draw_stats(self):

        return {self.variable_name: RWMCSampleStats(
            self._last_move_accepted, self._n_moves, self.stepsize,
            -self.pdf.log_prob(self.state))}

    def _adapt_stepsize(self):
        if self._last_move_accepted:
            self.stepsize *= self.adaption_uprate
        else:
            self.stepsize *= self.adaption_downrate

    def sample(self):

        E_old = -self.pdf.log_prob(self.state)
        proposal = self.state + np.random.uniform(
            low=-self.stepsize, high=self.stepsize, size=len(self.state))
        E_new = -self.pdf.log_prob(proposal)

        accepted = np.log(np.random.random()) < -(E_new - E_old)

        if accepted:
            self.state = proposal
            self._last_move_accepted = True
        else:
            self._last_move_accepted = False

        if self._n_moves < self.timestep_adaption_limit:
            self._adapt_stepsize()

        self._n_moves += 1

        return self.state
