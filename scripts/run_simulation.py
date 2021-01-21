import sys
import os

import yaml

import numpy as np
from mpi4py import MPI

sys.path.append(os.getenv('RESAAS_COMMON_PATH', '/home/simeon/projects/resaas/common/resaas/'))

from common.util import storage_factory

## communicators are classes which serve as an interface between, say, MPI and the rexfw code
## other communicators could use, e.g., the Python multiprocessing module to
## communicate between the master and the replicas
from rexfw.communicators.mpi import MPICommunicator

mpicomm = MPI.COMM_WORLD
rank = mpicomm.Get_rank()
size = mpicomm.Get_size()

n_replicas = size - 1

config_file = sys.argv[1]
with open(config_file) as ipf:
    config = yaml.load(ipf.read())
env = sys.argv[2]

## this is where all simulation output (samples, statistics files, etc.) are stored
basename = config['general']['basename']
output_folder = config['general']['output_path']
pstorage, sstorage = storage_factory(basename + output_folder)
os.makedirs(basename + output_folder + 'statistics/', exist_ok=True)
os.makedirs(basename + output_folder + 'works/', exist_ok=True)
os.makedirs(basename + output_folder + 'heats/', exist_ok=True)


comm = MPICommunicator()

if rank == 0:

    ## the first process (rank 0) runs an ExchangeMaster, which sends out 
    ## commands / requests to the replica processes, such as "sample", 
    ## "propose exchange states", "accept proposal", etc.

    from rexfw.convenience import setup_default_re_master, create_directories

    create_directories(output_folder)
    ## sets up a default RE master object; should be sufficient for all practical purposes
    master = setup_default_re_master(n_replicas, basename + output_folder, comm)
    master.run(config['general']['n_iterations'],
               config['re']['swap_interval'],
               config['re']['status_interval'],
               config['re']['dump_interval'])
    ## send kill request to break from infinite message receiving loop in replicas
    master.terminate_replicas()

else:

    ## every process with rank > 0 runs a replica, which does single-chain
    ## sampling and proposes exchange states

    from rexfw.convenience import setup_default_replica
    ## the slaves are relicts; originally I thought them to pass on
    ## messages from communicators to proposers / replicas, but now
    ## the replicas take care of everything themselves
    from rexfw.slaves import Slave
    ## a simple Metropolis-Hastings sampler...
    from rexfw.samplers.rwmc import RWMCSampler
    ## ... to sample from a normal distribution
    from rexfw.pdfs.normal import Normal

    os.chdir(output_folder)
    schedule = pstorage.read('schedule.pickle')
    pdf = Normal(sigma=1 / schedule['beta'][rank - 1] ** 2)
    pdf.n_variables = 1
    if config['general']['initial_states'] is None:
        init_state = np.random.normal(pdf.n_variables)
    else:
        init_states_path = output_folder
        init_states_path += config['general']['initial_states']
        init_stat = np.load(init_states_path)[rank - 1]

    ## all additional parameters for the sampler go in this dict
    
    if timesteps_path := config['local_sampling']['timesteps'] is not None:
        from pickle import load
        with open(timesteps_path, 'rb') as ipf:
            timestep = load(ipf)[rank - 1]
    else:
        timestep = 0.5
    sampler_params = {'stepsize': timestep}
    replica = setup_default_replica(
        init_state, pdf, RWMCSampler, sampler_params,
        pstorage, comm, rank)
    slave = Slave({replica.name: replica}, comm)

    ## starts infinite loop in slave to listen for messages
    slave.listen()
