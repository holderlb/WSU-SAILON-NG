import math
import numpy as np

from .cartpoleplusplus import CartPoleBulletEnv


class CartPolePPMock15(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        if self.difficulty == 'easy':
            self.force_mag = 50
        elif self.difficulty == 'medium':
            self.force_mag = 100
        elif self.difficulty == 'hard':
            self.force_mag = 150
        else:
            raise Exception('Invalid difficulty')

        return
