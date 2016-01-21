from nengo import Network as BaseNetwork
from nengo import Ensemble

from nengolib.stats import ScatteredHypersphere

_all__ = ['Network']


class Network(BaseNetwork):

    def __init__(self, *args, **kwargs):
        super(Network, self).__init__(*args, **kwargs)
        self.config[Ensemble].update({
            'encoders': ScatteredHypersphere(surface=True),
            'eval_points': ScatteredHypersphere(surface=False)})