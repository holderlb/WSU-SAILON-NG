import os
import sys
import math

import numpy as np

import pybullet as p2
from pybullet_utils import bullet_client as bc

from .cartpoleplusplus import CartPoleBulletEnv


class CartPolePPNovel4(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        self.rest = 1.0
        if self.difficulty == 'easy':
            # Between 1.05 and 1.15
            self.rest = 1.05 + self.np_random.random() / 10
        elif self.difficulty == 'medium':
            # Between 1.20 and 1.30
            self.rest = 1.2 + self.np_random.random() / 10
        elif self.difficulty == 'hard':
            # Between 1.35 and 1.45
            self.rest = 1.35 + self.np_random.random() / 10

        return None

    # Used to generate the initial world state
    def generate_world(self):
        # Read user config here
        if self.config is not None:
            if 'start_zeroed_out' in self.config:
                self.init_zero = self.config['start_zeroed_out']
            if 'episode_seed' in self.config:
                if self.config['episode_seed'] is not None:
                    self.seed(self.config['episode_seed'])
            if 'start_world_state' in self.config:
                if self.config['start_world_state'] is not None:
                    self.set_world(self.config['start_world_state'])

        # Create bullet physics client
        if self._renders:
            self._p = bc.BulletClient(connection_mode=p2.GUI)
        else:
            self._p = bc.BulletClient(connection_mode=p2.DIRECT)
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K") # Clear to the end of line

        # Client id link, for closing or checking if running
        self._physics_client_id = self._p._client

        # Load world simulation
        p = self._p
        p.resetSimulation()
        p.setGravity(0, 0, -9.8)
        p.setTimeStep(self.timeStep)
        p.setRealTimeSimulation(0)

        # Load world objects
        self.cartpole = p.loadURDF(os.path.join(self.path, 'models', 'ground_cart.urdf'))
        self.walls = p.loadURDF(os.path.join(self.path, 'models', 'walls.urdf'))
        self.origin = p.loadURDF(os.path.join(self.path, 'models', 'origin.urdf'))

        # Set walls to be bouncy
        for joint_nb in range(-1, 6):
            p.changeDynamics(self.walls, joint_nb, restitution=self.rest, lateralFriction=0.0,
                             rollingFriction=0.0, spinningFriction=0.0)

        return None

    def reset_world(self):
        super().reset_world()
        p = self._p

        # Set blocks to be bouncy
        for i in self.blocks:
            p.changeDynamics(i, -1, restitution=self.rest)

        return None
