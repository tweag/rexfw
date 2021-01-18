import sys
import yaml

import numpy as np
from mpi4py import MPI

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
output_folder = config['general_params']['output_path']

comm = MPICommunicator()

if rank == 0:

    ## the first process (rank 0) runs an ExchangeMaster, which sends out 
    ## commands / requests to the replica processes, such as "sample", 
    ## "propose exchange states", "accept proposal", etc.

    from rexfw.convenience import setup_default_re_master, create_directories

    create_directories(output_folder)
    ## sets up a default RE master object; should be sufficient for all practical purposes
    master = setup_default_re_master(n_replicas, output_folder, comm)
    master.run(**config['re_params'])
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
    
    pdf = Normal(sigma=float(rank))
    if config['general_params']['initial_states'] is None:
        init_state = np.random.normal(pdf.n_variables)
    else:
        init_states_path = output_folder
        init_states_path += config['general_params']['initial_states']
        init_stat = np.load(init_states_path)[rank - 1]

    ## all additional parameters for the sampler go in this dict
    replica = setup_default_replica(
        init_state, pdf, RWMCSampler, config['local_sampling_params'],
        output_folder, comm, rank)
    slave = Slave({replica.name: replica}, comm)

    ## starts infinite loop in slave to listen for messages
    slave.listen()
