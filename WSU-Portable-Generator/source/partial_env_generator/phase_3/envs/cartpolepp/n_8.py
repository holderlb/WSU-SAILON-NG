import math
import numpy as np
import os.path

from .cartpoleplusplus import CartPoleBulletEnv


class CartPolePPNovel8(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        if self.difficulty == 'easy':
            self.block_rate = 3
        elif self.difficulty == 'medium':
            self.block_rate = 2
        elif self.difficulty == 'hard':
            self.block_rate = 1

        self.block_tick = 0

        return None

    def step(self, action):
        self.block_tick = self.block_tick + 1
        if self.block_tick >= self.block_rate:
            self.block_tick = 0
            self.spawn_block()

        state, reward, done, info = super().step(action)
        return state, reward, done, info

    def spawn_block(self):
        p = self._p

        # Load blocks in
        self.nb_blocks = self.nb_blocks + 1
        self.blocks.append(None)

        self.blocks[-1] = p.loadURDF(os.path.join(self.path, 'models', 'block.urdf'))

        # Set blocks to be bouncy
        p.changeDynamics(self.blocks[-1], -1, restitution=1.0, lateralFriction=0.0,
                         rollingFriction=0.0, spinningFriction=0.0)

        # Set block posistions
        min_dist = 1
        cart_pos, _ = p.getBasePositionAndOrientation(self.cartpole)
        cart_pos = np.asarray(cart_pos)

        pos = self.np_random.uniform(low=-4.0, high=4.0, size=(3,))
        pos[2] = pos[2] + 5.0
        while np.linalg.norm(cart_pos[0:2] - pos[0:2]) < min_dist:
            pos = self.np_random.uniform(low=-4.0, high=4.0, size=(3,))
            # Z is not centered at 0.0
            pos[2] = pos[2] + 5.0
        p.resetBasePositionAndOrientation(self.blocks[-1], pos, [0, 0, 1, 0])

        # Set block velocities
        vel = self.np_random.uniform(low=3.0, high=5.0, size=(3,))
        for ind, val in enumerate(vel):
            if self.np_random.random() < 0.5:
                vel[ind] = val * -1

        p.resetBaseVelocity(self.blocks[-1], vel, [0, 0, 0])

        return None
