from csb.statistics.samplers import State
from csb.statistics.samplers.mc.singlechain import RWMCSampler
from csb.statistics.samplers.mc.multichain import HMCStepRENS, AlternatingAdjacentSwapScheme, HMCStepRENSSwapParameterInfo
import matplotlib.pyplot as plt
import numpy
from rexfw.test.pdfs import MyNormal

std_devs = 1.0 / numpy.sqrt(numpy.array([7., 5., 3., 1.]))
pdfs = [MyNormal(sigma=std_dev) for std_dev in std_devs]
samplers = [RWMCSampler(pdf, State(numpy.array([float(i) + 1])), 0.7) for i, pdf in enumerate(pdfs)]
timesteps = [0.3, 0.5, 0.7]

im_steps = 5
    
from rexfw.proposers import ParamInterpolationPDF
from collections import namedtuple
P = namedtuple('P', 'n_steps timestep pdf_params')
ipdfs = [ParamInterpolationPDF(MyNormal(), 
                               P(float(im_steps), 1.0, 
                               {'sigma': (std_devs[i], std_devs[i+1])})) 
         for i in range(len(pdfs) - 1)]
# rens_gradients = [lambda x, l, i=i: ipdfs[i].gradient(x, l*1.0 * float(im_steps)) 
#                   for i, pdf in enumerate(ipdfs)]

rens_gradients = [lambda x, l, i=i: l * pdfs[i+1].gradient(x) + (1.0 - l) * pdfs[i].gradient(x) 
                  for i in range(len(pdfs) - 1)]

params = [HMCStepRENSSwapParameterInfo(samplers[i], samplers[i+1], timesteps[i], 1, 1,
                                       rens_gradients[i], im_steps)
          for i in range(len(std_devs) - 1)]

from fastcode import FastHMCStepRENS
algorithm = FastHMCStepRENS(samplers, params)

swapper = AlternatingAdjacentSwapScheme(algorithm)

nsamples = 5#15000

samples = []

for i in range(nsamples):
    if i % 100 == 0 and i > 0:
        print "################ HMC step #"+str(i)+" #####################"
        print "MC acceptance rates:", ["%.2f" % x.acceptance_rate for x in samplers]
        print "RENS acceptance rates:", ["%.2f" % x for x in algorithm.acceptance_rates]
        print 

    if i % 5 == 0:
        swapper.swap_all()
    else:
        algorithm.sample()

    samples.append(algorithm.state)
