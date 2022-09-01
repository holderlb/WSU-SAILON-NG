import math
import numpy as np
import os.path

from .cartpoleplusplus import CartPoleBulletEnv


class CartPolePPMock7(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        if self.difficulty == 'easy':
            self.block_force = 15
        elif self.difficulty == 'medium':
            self.block_force = 25
        elif self.difficulty == 'hard':
            self.block_force = 35

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

        # Apply anti-gravity to blocks
        for i in self.blocks:
            mass = p.getDynamicsInfo(i, -1)[0]
            p.applyExternalForce(i, -1, (0, 0, 9.8), (0, 0, 0), p.LINK_FRAME)

        # Apply attraction force
        ori_x = 0.0
        ori_y = 0.0
        ori_z = 0.0

        for i in self.blocks:
            pos, ori = p.getBasePositionAndOrientation(i)
            u1 = np.asarray([ori_x - pos[0], ori_y - pos[1], ori_z - pos[2]])
            if np.linalg.norm(u1) == 0.0:
                u1 = np.asarray([np.random.rand(), np.random.rand(), np.random.rand()])
            else:
                u1 = np.multiply(u1 / np.linalg.norm(u1), self.block_force)
            p.applyExternalForce(i, -1, (-u1[0], -u1[1], u1[2]), (0, 0, 0), p.LINK_FRAME)

        p.stepSimulation()

        done = self.is_done()
        reward = self.get_reward()

        self.tick = self.tick + 1

        return self.get_state(), reward, done, {}
