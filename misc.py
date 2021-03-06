import numpy
from rexfw import Parcel
from rexfw.proposers import LMDRENSProposer, AMDRENSProposer, ParamInterpolationPDF, HMCStepRENSProposer
from rexfw.replicas import Replica
from csb.statistics.samplers import State


class GeneralTrajectory(list):

    def __init__(self, items, work=0.0, heat=0.0, delta_Epot=0.0, delta_Ekin=0.0):

        super(GeneralTrajectory, self).__init__(items)

        self.work = work
        self.heat = heat
        self.delta_Epot = delta_Epot
        self.delta_Ekin = delta_Ekin

        
class TrajDumpLMDRENSProposer(LMDRENSProposer):

    def propose(self, local_replica, partner_state, partner_energy, params):

        pdf = self._pdf_factory(local_replica, params)
        propagator = self._propagator_factory(pdf, params)

        ps_pos = partner_state.position
        traj = propagator.generate(State(ps_pos, numpy.random.normal(size=ps_pos.shape)), params.n_steps, True)
        traj.work = self._calculate_work(local_replica, partner_energy, traj)

        E_remote = partner_energy
        E_local = -local_replica.pdf.log_prob(traj.final.position)
        
        deltaE = (E_local - E_remote) + 0.5 * numpy.sum(traj.final.momentum ** 2) - 0.5 * numpy.sum(traj.initial.momentum ** 2)

        traj = GeneralTrajectory([traj.initial, traj[len(traj)/2], traj.final], 
                                 work=traj.work, heat=traj.heat,
                                 delta_Epot=E_local - E_remote, 
                                 delta_Ekin=.5*numpy.sum(traj.final.momentum**2)-.5*numpy.sum(traj.initial.momentum**2))

        return traj


class TrajDumpAMDRENSProposer(AMDRENSProposer):

    def propose(self, local_replica, partner_state, partner_energy, params):

        pdf = self._pdf_factory(local_replica, params)
        propagator = self._propagator_factory(pdf, params)

        ps_pos = partner_state.position
        traj = propagator.generate(State(ps_pos, numpy.random.normal(size=ps_pos.shape)), params.n_steps, True)
        traj.work = self._calculate_work(local_replica, partner_energy, traj)

        E_remote = partner_energy
        E_local = -local_replica.pdf.log_prob(traj.final.position)
        
        deltaE = (E_local - E_remote) + 0.5 * numpy.sum(traj.final.momentum ** 2) - 0.5 * numpy.sum(traj.initial.momentum ** 2)

        traj = GeneralTrajectory([traj.initial, traj[len(traj)/2], traj.final], 
                                 work=traj.work, heat=traj.heat,
                                 delta_Epot=E_local - E_remote, delta_Ekin=0.5 * numpy.sum(traj.final.momentum ** 2) - 0.5 * numpy.sum(traj.initial.momentum ** 2))

        return traj


class TrajDumpHMCStepRENSProposer(HMCStepRENSProposer):

    def propose(self, local_replica, partner_state, partner_energy, params):

        pdf = self._pdf_factory(local_replica, params)
        n_steps = params.n_steps
        propagator = self._propagator_factory(local_replica.pdf, params)

        ps_pos = partner_state.position
        traj = propagator.generate(State(ps_pos), return_trajectory=True)

        E_remote = partner_energy
        E_local = -local_replica.pdf.log_prob(traj.final.position)

        deltaE = (E_local - E_remote)
        
        traj = GeneralTrajectory([traj.initial, traj[len(traj)/2], traj.final], work=traj.work, heat=traj.heat, delta_Epot=deltaE)
        
        return traj        
    

class TrajDumpReplica(Replica):

    def _propose(self, request):

        partner_name = request.partner
        params = request.params
        proposer_params = params.proposer_params
        self._current_master = request.sender

        proposer = list(set(self.proposers.keys()).intersection(set(params.proposers)))[-1]
        self.proposers[proposer].partner_name = partner_name
        proposal = self.proposers[proposer].propose(self, 
                                                    self._buffered_partner_state,
                                                    self._buffered_partner_energy,
                                                    proposer_params)
        
        self._comm.send(Parcel(self.name, self._current_master, proposal), 
                        self._current_master)
        self._buffered_proposal = proposal[-1]
