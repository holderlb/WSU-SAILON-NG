import math
import numpy as np
import os.path
import random

from .cartpoleplusplus import CartPoleBulletEnv


class CartPolePPMock8(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        if self.difficulty == 'easy':
            self.block_rate = 50
        elif self.difficulty == 'medium':
            self.block_rate = 15
        elif self.difficulty == 'hard':
            self.block_rate = 7

        self.block_tick = 0

        self.directions = []

        return None

    def step(self, action):
        self.block_tick = self.block_tick + 1
        if self.block_tick >= self.block_rate:
            self.block_tick = 0
            self.spawn_block()

        state, reward, done, info = super().step(action)
        self.directions.append([state['cart']['x_velocity'], state['cart']['y_velocity']])
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
        min_dist = 0.75
        max_attempts = 100
        attempt = 0

        pos = self.get_pos()
        pos[2] = 1.0
        while self.too_close(min_dist, pos) or self.is_out(pos):
            attempt = attempt + 1
            if attempt > max_attempts:
                p.removeBody(self.blocks[-1])
                self.nb_blocks = self.nb_blocks - 1
                del self.blocks[-1]
                return None
            pos = self.get_pos()
            # Z is not centered at 0.0
            pos[2] = 1.0
        p.resetBasePositionAndOrientation(self.blocks[-1], pos, [0, 0, 1, 0])

        return None

    # Use last directions to figure out where to spawn next
    def get_pos(self):
        p = self._p

        # Get cart position
        cart_pos, _ = p.getBasePositionAndOrientation(self.cartpole)
        cart_pos = np.asarray(cart_pos)

        # Roll random infront distance
        distance = random.random() * 10

        # Get average direction
        vects = np.asarray(self.directions[-self.block_rate:])
        v_avg = np.asarray([np.mean(vects[:, 0]), np.mean(vects[:, 1])])
        v_norm = v_avg / np.linalg.norm(v_avg)

        # Position calculcation
        pos = [v_norm[0] * distance, v_norm[1] * distance, 0.0]

        return pos

    # Returns whether attempted pos is too close to either cartpole or existing blocks
    def too_close(self, min_dist, pos):
        p = self._p

        pos = np.asarray(pos)

        cart_pos, _ = p.getBasePositionAndOrientation(self.cartpole)
        cart_pos = np.asarray(cart_pos)

        if np.linalg.norm(cart_pos[0:2] - pos[0:2]) < min_dist:
            return True

        for block_id in self.blocks:
            block_pos, _ = p.getBasePositionAndOrientation(block_id)
            block_pos = np.asarray(block_pos)
            if np.linalg.norm(block_pos[0:2] - pos[0:2]) < min_dist:
                return True

        return False

    # Returns whether block is out of box
    def is_out(self, pos):
        if abs(pos[0]) > 4.5 or abs(pos[1]) > 4.5:
            return True
        else:
            return False
