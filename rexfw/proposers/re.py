'''
Proposer classes which propose states for RE, RENS, ... swaps
'''

from rexfw.proposers import AbstractProposer, GeneralTrajectory


class REProposer(AbstractProposer):

    def propose(self, local_replica, partner_state, partner_negative_log_prob,
                params):

        work =   local_replica.get_negative_log_prob(partner_state) \
               - partner_negative_log_prob

        return GeneralTrajectory([partner_state, partner_state], work=work)
