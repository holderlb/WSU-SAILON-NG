import math
import os.path
import time

import numpy as np
from numpy.linalg import norm

from .cartpoleplusplus import CartPoleBulletEnv


class CartPolePPNovel2(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        if self.difficulty == 'easy':
            self.min_dist = 3
            self.max_dist = 4
        elif self.difficulty == 'medium':
            self.min_dist = 2
            self.max_dist = 3
        elif self.difficulty == 'hard':
            self.min_dist = 1.5
            self.max_dist = 2
        return None

    # Unified function for getting state information
    def get_state(self, initial=False):
        p = self._p
        world_state = dict()
        round_amount = 6

        # Get cart info ============================================
        state = dict()

        # Handle pos, vel
        pos, _, _, _, _, _ = p.getLinkState(self.cartpole, 0)
        state['x_position'] = round(pos[0], round_amount)
        state['y_position'] = round(pos[1], round_amount)
        state['z_position'] = round(pos[2], round_amount)

        # Cart velocity from planar joint (buggy in PyBullet; thus reverse order)
        # _, vel, _, _ = p.getJointStateMultiDof(self.cartpole, 0)
        # state['x_velocity'] = round(vel[2], round_amount)
        # state['y_velocity'] = round(vel[1], round_amount)
        # state['z_velocity'] = round(vel[0], round_amount)

        # Cart velocity from cart
        _, _, _, _, _, _, vel, _ = p.getLinkState(self.cartpole, 0, 1)
        state['x_velocity'] = round(vel[0], round_amount)
        state['y_velocity'] = round(vel[1], round_amount)
        state['z_velocity'] = round(vel[2], round_amount)

        # Set world state of cart
        world_state['cart'] = state

        # Get pole info =============================================
        state = dict()
        use_euler = False

        # Orientation and A_velocity, the others not used
        _, _, _, _, _, ori, _, vel = p.getLinkState(self.cartpole, 1, 1)

        # Orientation
        if use_euler:
            # Convert quats to eulers
            eulers = p.getEulerFromQuaternion(ori)
            state['x_euler'] = round(eulers[0], round_amount)
            state['y_euler'] = round(eulers[1], round_amount)
            state['z_euler'] = round(eulers[2], round_amount)
        else:
            state['x_quaternion'] = round(ori[0], round_amount)
            state['y_quaternion'] = round(ori[1], round_amount)
            state['z_quaternion'] = round(ori[2], round_amount)
            state['w_quaternion'] = round(ori[3], round_amount)

        # A_velocity
        state['x_velocity'] = round(vel[0], round_amount)
        state['y_velocity'] = round(vel[1], round_amount)
        state['z_velocity'] = round(vel[2], round_amount)

        world_state['pole'] = state

        # get block info ====================================
        block_state = list()
        for ind, val in enumerate(self.blocks):
            state = dict()
            state['id'] = val

            pos, _, _, _, _, _, vel, _ = p.getLinkState(val, 0, 1)
            state['x_position'] = round(pos[0], round_amount)
            state['y_position'] = round(pos[1], round_amount)
            state['z_position'] = round(pos[2], round_amount)

            vel, _ = p.getBaseVelocity(val)
            state['x_velocity'] = round(vel[0], round_amount)
            state['y_velocity'] = round(vel[1], round_amount)
            state['z_velocity'] = round(vel[2], round_amount)

            block_state.append(state)

        world_state['blocks'] = block_state

        # Get wall info ======================================
        if initial:
            state = list()
            state.append([-5, -5, 0])
            state.append([5, -5, 0])
            state.append([5, 5, 0])
            state.append([-5, 5, 0])
            state.append([-5, -5, 10])
            state.append([5, -5, 10])
            state.append([5, 5, 10])
            state.append([-5, 5, 10])

            world_state['walls'] = state

        return world_state

    def reset_world(self):
        # Reset world (assume is created)
        p = self._p

        # Delete cartpole
        if self.cartpole == -10:
            self.cartpole = p.loadURDF(os.path.join(self.path, 'models', 'ground_cart.urdf'))
        else:
            p.removeBody(self.cartpole)
            self.cartpole = p.loadURDF(os.path.join(self.path, 'models', 'ground_cart.urdf'))

        # This big line sets the spehrical joint on the pole to loose
        p.setJointMotorControlMultiDof(self.cartpole, 1, p.POSITION_CONTROL, targetPosition=[0, 0, 0, 1],
                                       targetVelocity=[0, 0, 0], positionGain=0, velocityGain=0.0,
                                       force=[0, 0, 0])

        # Reset cart (technicaly ground object)
        if self.init_zero:
            cart_pos = list(self.np_random.uniform(low=0, high=0, size=(2,))) + [0]
            cart_vel = list(self.np_random.uniform(low=0, high=0, size=(2,))) + [0]
        else:
            cart_pos = list(self.np_random.uniform(low=-3, high=3, size=(2,))) + [0]
            cart_vel = list(self.np_random.uniform(low=-1, high=1, size=(2,))) + [0]

        p.resetBasePositionAndOrientation(self.cartpole, cart_pos, [0, 0, 0, 1])
        p.applyExternalForce(self.cartpole, 0, cart_vel, (0, 0, 0), p.LINK_FRAME)

        # Reset pole
        if self.init_zero:
            randstate = list(self.np_random.uniform(low=0, high=0, size=(6,)))
        else:
            randstate = list(self.np_random.uniform(low=-0.01, high=0.01, size=(6,)))

        pole_pos = randstate[0:3] + [1]
        # zero so it doesnt spin like a top :)
        pole_ori = list(randstate[3:5]) + [0]
        p.resetJointStateMultiDof(self.cartpole, 1, targetValue=pole_pos, targetVelocity=pole_ori)

        # Delete old blocks
        for i in self.blocks:
            p.removeBody(i)

        # Load blocks in
        self.nb_blocks = self.np_random.randint(3) + 2
        self.blocks = [None] * self.nb_blocks
        for i in range(self.nb_blocks):
            self.blocks[i] = p.loadURDF(os.path.join(self.path, 'models', 'n2', 'block.urdf'))

        # Change block params
        for i in self.blocks:
            # Set blocks to be bouncy
            p.changeDynamics(i, 0, linearDamping=0, angularDamping=0, restitution=1.0)
            # Set joint to be loose
            p.setJointMotorControl2(i, 0, p.VELOCITY_CONTROL, force=0)

        # Set line positions
        cpos, _, _, _, _, _ = p.getLinkState(self.cartpole, 0)
        cart_x = cpos[0]
        cart_y = cpos[1]

        # Set line positions
        for i in self.blocks:

            while True:
                angle = self.np_random.random() * 2 * np.pi
                pos = np.asarray(list(self.np_random.uniform(low=-4.0, high=4.0, size=(2,))))
                p1 = np.asarray([pos[0] + 20 * np.cos(angle), pos[1] + 20 * np.sin(angle)])
                p2 = np.asarray([pos[0] + 20 * np.cos(angle + np.pi), pos[1] + 20 * np.sin(angle + np.pi)])
                p3 = np.asarray([cart_x, cart_y])
                dist = norm(np.cross(p2 - p1, p1 - p3)) / norm(p2 - p1)

                if self.min_dist < dist < self.max_dist:
                    break

            height = self.np_random.uniform(low=-1.0, high=1.0, size=(1,))
            p.resetBasePositionAndOrientation(i, [pos[0], pos[1], height[0]], [0.0, 0.0, angle, 1])

            # print(angle, p1, p2)
            # print(i, dist)

        # Set block pos/ velocities
        for i in self.blocks:
            # Pos x, y
            pos = self.np_random.uniform(low=-10, high=10, size=(1,))
            p.resetJointState(i, 0, pos[0], 0)
            x, y = self.get_block_pos(i)
            while not ((-4 < x < 4) and (-4 < y < 4)):
                pos = self.np_random.uniform(low=-10, high=10, size=(1,))
                p.resetJointState(i, 0, pos[0], 0)
                x, y = self.get_block_pos(i)

            # Vel
            vel = self.np_random.uniform(low=6.0, high=10.0, size=(1,))
            for ind, val in enumerate(vel):
                if self.np_random.random() < 0.5:
                    vel[ind] = val * -1

            p.resetJointState(i, 0, pos, vel[0])

        return None

    def get_block_pos(self, i):
        base_pose, base_ori = self._p.getBasePositionAndOrientation(i)
        angle = base_ori[2]
        pos, vel, jRF, aJMT = self._p.getJointState(i, 0)

        x = base_pose[0] + (pos * np.cos(angle))
        y = base_pose[1] + (pos * np.sin(angle))

        return x, y
