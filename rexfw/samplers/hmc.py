'''
HMC sampler implementations
'''

from collections import namedtuple
from copy import deepcopy

import numpy as np

HMCSampleStats = namedtuple('HMCSampleStats', 'accepted stepsize')


class HMCSampler(object):

    def __init__(self, pdf, state, timestep, nsteps, timestep_adaption_limit=0,
                 adaption_uprate=1.05, adaption_downrate=0.95, variable_name='x'):
        """
        A Hamiltonian Monte Carlo implementation

        :param pdf: object representing the PDF this sampler is
                    supposed to sample from
        :type pdf: :class:`.AbstractBinfPDF`

        :param state: initial state
        :type state: :class:`.BinfState`

        :param timestep: integration step size for leap frog integrator
        :type timestep: float

        :param nsteps: number of integration steps for leap frog integrator
        :type nsteps: int

        :param timestep_adaption_limit: # of samples after which to stop
                                        automatically adapting the timestep
        :type timestep_adaption_limit: int

        :param adaption_uprate: factor with which to multiply current
                                time step in case of rejected move
        :type adaption_uprate: float

        :param adaption_downrate: factor with which to multiply current
                                  time step in case of accepted move
        :type adaption_downrate: float

        :param variable_name: name of the variable this sampler is
                              supposed to draw random samples from
        :type variable_name: str
        """
        self.pdf = pdf
        self.state = state
        self.timestep = timestep
        self.nsteps = nsteps
        self.timestep_adaption_limit = timestep_adaption_limit
        self.adaption_uprate = adaption_uprate
        self.adaption_downrate = adaption_downrate
        self.variable_name = variable_name
        self._last_move_accepted = 0
        self.n_accepted = 0
        self.counter = 0

    @property
    def acceptance_rate(self):
        if self.counter > 0:
            return self.n_accepted / float(self.counter)
        else:
            return 0.0

    @property
    def last_move_accepted(self):
        """
        Returns whether the last move has been accepted or not

        :returns: whether the last move has been accepted or not
        :rtype: bool
        """
        return self._last_move_accepted

    def _leapfrog(self, q, p, timestep, nsteps):
        """
        Performs leap frog integration of Hamiltonian dynamics guided
        by the gradient of the negative log-probability

        :param q: initial 'position'
        :type q: numpy.ndarray

        :param p: initial 'momentum'
        :type p: numpy.ndarray

        :param timestep: integration time step
        :type timestep: float

        :param nsteps: # of integration steps
        :type nsteps: int

        :returns: 'position' and 'momentum' at the end of the
                  approximated MD trajectory
        :rtype: (numpy.ndarray, numpy.ndarray)
        """

        gradient = lambda x: -self.pdf.log_prob_gradient(x)

        p -= 0.5 * timestep * gradient(q)

        for i in range(nsteps-1):
            q += p * timestep
            p -= timestep * gradient(q)

        q += p * timestep
        p -= 0.5 * timestep * gradient(q)

        return q, p

    def _copy_state(self, state):
        """
        Copies a state

        :param state: variable value to copy
        :type state: numpy.ndarray
        """
        return state.copy()
        return deepcopy(state)

    def sample(self):
        """
        Draws a random sample

        :returns: a sample
        :rtype: numpy.ndarray
        """
        V = lambda x: -self.pdf.log_prob(x)

        q = self.state.copy()
        p = np.random.normal(size=q.shape)

        E_before = V(q) + 0.5 * np.sum(p ** 2)
        q, p = self._leapfrog(q, p, self.timestep, self.nsteps)
        E_after = V(q) + 0.5 * np.sum(p ** 2)
        acc = np.log(np.random.uniform()) < -(E_after - E_before)

        self._last_move_accepted = acc
        self.counter += 1

        if self.counter < self.timestep_adaption_limit:
            self._adapt_timestep()

        if acc:
            self.state = q
            self.n_accepted += 1
            return self.state
        else:
            return self.state

    @property
    def last_draw_stats(self):
        """
        Returns information about the most recently performed move

        This is usually used by a replica exchange scheme to log
        sampling statistics.

        :returns: whether the last move has been accepted and the current
                  time step in the shape of a named tuple in a dictionary.
                  This contrived is needed for Gibbs sampling / replica
                  exchange statistics.
        :rtype: dict
        """
        return {self.variable_name: HMCSampleStats(self.last_move_accepted,
                                                   self.timestep)}

    def _adapt_timestep(self):
        """
        Increases / decreasese the leap frog time step depending on
        whether the last move has been rejected / accepted.
        """
        if self.last_move_accepted:
            self.timestep *= self.adaption_uprate
        else:
            self.timestep *= self.adaption_downrate



if __name__ == '__main__':
    class HO:
        def log_prob(self, x):
            return -0.5 * np.sum(x ** 2)

        def log_prob_gradient(self, x):
            return -x


    init_state = np.array([0.0, 1.0])
    s = HMCSampler(HO(), init_state, 0.5, 10)
    samples = np.array([s.sample() for _ in range(10000)])

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    from scipy.stats import norm
    for i, x in enumerate(init_state):
        ax.hist(samples[:,i], bins=40, alpha=0.5, density=True)
    xspace = np.linspace(-3, 3, 100)
    ax.plot(xspace, norm.pdf(xspace))
    plt.show()
