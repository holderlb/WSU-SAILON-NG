import math
import numpy as np

from .cartpoleplusplus import CartPoleBulletEnv


class CartPolePPMock6(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        if self.difficulty == 'easy':
            self.gravity = -20
        elif self.difficulty == 'medium':
            self.gravity = -30
        elif self.difficulty == 'hard':
            self.gravity = -40

        return None

    def step(self, action):
        p = self._p

        # Convert from string to int
        if action == 'nothing':
            action = 0
        elif action == 'right':
            action = 1
        elif action == 'left':
            action = 2
        elif action == 'forward':
            action = 3
        elif action == 'backward':
            action = 4

        # Adjust forces so they always apply in reference to world frame
        _, ori, _, _, _, _ = p.getLinkState(self.cartpole, 0)
        cart_angle = p.getEulerFromQuaternion(ori)[2] # yaw
        fx = self.force_mag * np.cos(cart_angle)
        fy = self.force_mag * np.sin(cart_angle) * -1

        # based on action decide the x and y forces
        if action == 0:
            fx = 0.0
            fy = 0.0
        elif action == 1:
            fx = fx
            fy = fy
        elif action == 2:
            fx = -fx
            fy = - fy
        elif action == 3:
            tmp = fx
            fx = -fy
            fy = tmp
        elif action == 4:
            tmp = fx
            fx = fy
            fy = -tmp
        else:
            raise Exception("unknown discrete action [%s]" % action)

        # Apply correccted forces
        p.applyExternalForce(self.cartpole, 0, (fx, fy, 0.0), (0, 0, 0), p.LINK_FRAME)
        # Rotation forces
        # p.applyExternalForce(self.cartpole, 0, (1, 0, 0.0), (1.0, 1.0, 0), p.LINK_FRAME)
        # p.applyExternalForce(self.cartpole, 0, (-1, 0, 0.0), (-1.0, 0, 0), p.LINK_FRAME)

        # Apply anti-gravity to blocks
        #for i in self.blocks:
        #    mass = p.getDynamicsInfo(i, -1)[0]
        #    p.applyExternalForce(i, -1, (0, 0, -1 * mass * self.gravity), (0, 0, 0), p.LINK_FRAME)

        p.stepSimulation()

        done = self.is_done()
        reward = self.get_reward()

        self.tick = self.tick + 1

        return self.get_state(), reward, done, {}
