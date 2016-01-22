from csb.statistics.samplers import State
from csb.statistics.samplers.mc.singlechain import RWMCSampler
from csb.statistics.samplers.mc.multichain import ThermostattedMDRENS, AlternatingAdjacentSwapScheme, ThermostattedMDRENSSwapParameterInfo
import matplotlib.pyplot as plt
import numpy
from rexfw.test.pdfs import MyNormal

std_devs = 1.0 / numpy.sqrt(numpy.array([7., 5., 3., 1.]))[0:4]
init = State(numpy.array([1.0]))
pdfs = [MyNormal(sigma=std_dev) for std_dev in std_devs]
samplers = [RWMCSampler(pdf, State(numpy.array([2.0 + 0.0*i+0.0*1])), 0.7) for i, pdf in enumerate(pdfs)]
timesteps = [0.3, 0.5, 0.7][0:3]
im_steps = 15
    
from rexfw.proposers import InterpolatingPDF
from collections import namedtuple
P = namedtuple('P', 'n_steps timestep pdf_params')
ipdfs = [InterpolatingPDF(MyNormal(), 
                          P(float(im_steps), 1.0, 
                            {'sigma': (std_devs[i], std_devs[i+1])})) 
         for i in range(len(pdfs) - 1)]

rens_gradients = [lambda x, l, i=i: ipdfs[i].gradient(x, l*1.0 * float(im_steps)) 
                  for i, pdf in enumerate(ipdfs)]

params = [ThermostattedMDRENSSwapParameterInfo(samplers[i], samplers[i+1], timesteps[i], im_steps,
                                               rens_gradients[i])
          for i in range(len(std_devs) - 1)]

algorithm = ThermostattedMDRENS(samplers, params)

swapper = AlternatingAdjacentSwapScheme(algorithm)
nsamples = 2*15000

samples = []

for i in range(nsamples):
    # print i
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