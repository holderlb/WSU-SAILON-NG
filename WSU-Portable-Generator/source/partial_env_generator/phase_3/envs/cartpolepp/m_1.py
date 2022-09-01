import math
import numpy as np

from .cartpoleplusplus import CartPoleBulletEnv


class CartPolePPMock1(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        return None

    # Used to generate the initial world state
    def reset_world(self):
        super().reset_world()

        p = self._p
        # Do Novelty Here
        p.changeDynamics(self.cartpole, 0, mass=10.0)
        '''
        if self.difficulty == 'easy':
            p.changeDynamics(self.cartpole, 0, mass=5.0)
        elif self.difficulty == 'medium':
            p.changeDynamics(self.cartpole, 0, mass=10.0)
        elif self.difficulty == 'hard':
            p.changeDynamics(self.cartpole, 0, mass=50.0)
        else:
            raise Exception('Invalid difficulty')
        '''
        return None
