import numpy

import theano
from theano import tensor

from blocks.algorithms import GradientDescent, Scale
from blocks.bricks import MLP, Tanh, Identity
from blocks.bricks.cost import SquaredError
from blocks.graph import ComputationGraph
from blocks.initialization import IsotropicGaussian, Constant
from blocks.model import Model
from fuel.datasets import IterableDataset
from fuel.schemes import ConstantScheme
from fuel.transformers import Batch
from blocks.extensions import FinishAfter, Timing, Printing
from blocks.extensions.saveload import Checkpoint
from blocks.extensions.monitoring import (TrainingDataMonitoring,
                                          DataStreamMonitoring)
from blocks.main_loop import MainLoop

floatX = theano.config.floatX


def get_data_stream(iterable):
    """Returns a 'fuel.Batch' datastream of
    [x~input~numbers, y~targets~roots], with each iteration returning a
    batch of 20 training examples
    """
    numbers = numpy.asarray(iterable, dtype=floatX)
    dataset = IterableDataset(
        {'numbers': numbers, 'roots': numpy.sqrt(numbers)})
    return Batch(dataset.get_example_stream(), ConstantScheme(20))


def main(save_to, num_batches):
    mlp = MLP([Tanh(), Identity()], [1, 10, 1],
              weights_init=IsotropicGaussian(0.01),
              biases_init=Constant(0), seed=1)
    mlp.initialize()
    x = tensor.vector('numbers')
    y = tensor.vector('roots')
    cost = SquaredError().apply(y[:, None], mlp.apply(x[:, None]))
    cost.name = "cost"

    main_loop = MainLoop(
        GradientDescent(
            cost=cost, parameters=ComputationGraph(cost).parameters,
            step_rule=Scale(learning_rate=0.001)),
        get_data_stream(range(100)),
        model=Model(cost),
        extensions=[
            Timing(),
            FinishAfter(after_n_batches=num_batches),
#            DataStreamMonitoring(
#                [cost], get_data_stream(range(100, 200)),
#                prefix="test"),
#            TrainingDataMonitoring([cost], after_epoch=True),
            Checkpoint(save_to),
            Printing()])
    main_loop.run()
    return main_loop
