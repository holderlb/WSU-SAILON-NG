"""
Classic cart-pole system implemented by Rich Sutton et al.
Copied from http://incompleteideas.net/book/code/pole.c
"""

import math
import gym
from gym import spaces
from gym.utils import seeding
import os.path
import numpy as np
import pybullet as p2
from pybullet_utils import bullet_client as bc

import sys
import os
import time

from .cartpoleplusplus import CartPoleBulletEnv


class CartPoleBulletEnv(CartPoleBulletEnv):

    def __init__(self, params: dict = None):
        super().__init__(params=params)
        self.params = params
        # start the bullet physics server
        self._renders = self.params['use_gui']
        self._discrete_actions = True # get from params?
        self._render_height = 480
        self._render_width = 640
        self._physics_client_id = -1
        self.theta_threshold_radians = 12 * 2 * math.pi / 360
        self.x_threshold = 2.4
        self.use_img = self.params['use_img']
        high = np.array([self.x_threshold * 2, np.finfo(np.float32).max,
                         self.theta_threshold_radians * 2, np.finfo(np.float32).max])

        # Environmental params
        self.force_mag = 10
        self.timeStep = 1.0 / 50.0
        self.angle_limit = 10
        self.actions = ['left', 'right', 'nothing']

        # Internal params
        self.path = self.params['path']
        self.tick_limit = 200
        self.tick = 0
        self.time = None
        self.use_img = self.params['use_img']

        # Param for setting initial conditions to zero
        self.init_zero = False

        # Object definitions
        self.cartpole = -10
        self.state = None

        if self._discrete_actions:
            self.action_space = spaces.Discrete(5)
        else:
            action_dim = 1
            action_high = np.array([self.force_mag] * action_dim)
            self.action_space = spaces.Box(-action_high, action_high)

        self.observation_space = spaces.Box(-high, high, dtype=np.float32)

        self.seed()
        self.viewer = None

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
        else:
            # print('Invalid action sent to p_base, only left right allowed')
            # print('Supplymenting nothing action!')
            action = 0

        fx = 0
        if action == 1:
            fx = self.force_mag
        elif action == 2:
            fx = -self.force_mag

        p.applyExternalForce(self.cartpole, 0, (fx, 0.0, 0.0), (0, 0, 0), p.LINK_FRAME)

        p.stepSimulation()

        done = self.is_done()
        reward = self.get_reward()

        self.tick = self.tick + 1

        return self.get_state(), reward, done, {}

    # Check if is done
    def is_done(self):
        state = self.get_state()

        if abs(state['cart']['x_position']) > self.x_threshold:
            return True
        if abs(state['pole']['y_quaternion']) > self.theta_threshold_radians:
            return True

        return False

    # Used to generate the initial world state
    def generate_world(self):
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
        self.cartpole = p.loadURDF(os.path.join(self.path, 'models/p/', 'cartpole.urdf'))

        return None

    def reset_world(self):
        # Reset world (assume is created)
        p = self._p

        # Delete cartpole
        if self.cartpole == -10:
            self.cartpole = p.loadURDF(os.path.join(self.path, 'models/p/', 'cartpole.urdf'))
        else:
            p.removeBody(self.cartpole)
            self.cartpole = p.loadURDF(os.path.join(self.path, 'models/p/', 'cartpole.urdf'))

        # Set cart to have no friction
        p.changeDynamics(self.cartpole, -1, linearDamping=0, angularDamping=0)
        p.changeDynamics(self.cartpole, 0, linearDamping=0, angularDamping=0)
        p.changeDynamics(self.cartpole, 1, linearDamping=0, angularDamping=0)

        # Set pole to loose
        p.setJointMotorControl2(self.cartpole, 1, p.VELOCITY_CONTROL, force=0, positionGain=0, velocityGain=0.0)
        p.setJointMotorControl2(self.cartpole, 0, p.VELOCITY_CONTROL, force=0, positionGain=0, velocityGain=0.0)

        # Set random initial state
        randstate = self.np_random.uniform(low=-0.01, high=0.01, size=(2,))
        p.resetJointState(self.cartpole, 0, randstate[0], 1.0)
        p.resetJointState(self.cartpole, 1, 0.0, 0.4)
        self.state = p.getJointState(self.cartpole, 1)[0:2] + p.getJointState(self.cartpole, 0)[0:2]

        return None

    # Unified function for getting state information
    def get_state(self, initial=False):
        p = self._p
        world_state = dict()
        round_amount = 6

        # Get cart info ============================================
        state = dict()

        # Handle pos, ori
        self.state = p.getJointState(self.cartpole, 1)[0:2] + p.getJointState(self.cartpole, 0)[0:2]
        theta, theta_dot, x, x_dot = self.state
        state['x_position'] = round(x, round_amount)
        state['y_position'] = round(0.0, round_amount)
        state['z_position'] = round(0.0, round_amount)

        # Handle velocity
        state['x_velocity'] = round(x_dot, round_amount)
        state['y_velocity'] = round(0.0, round_amount)
        state['z_velocity'] = round(0.0, round_amount)

        world_state['cart'] = state
        
        # Get pole info =============================================
        #quat = self.eulerToQuaternion(theta, 0, 0)
        # Pole angle along x is a rotation about the y axis (Euler pitch)
        quat = p.getQuaternionFromEuler([0, theta, 0])

        state = dict()
        #state['x_quaternion'] = round(quat[1], round_amount)
        #state['y_quaternion'] = round(quat[0], round_amount)
        state['x_quaternion'] = round(quat[0], round_amount)
        state['y_quaternion'] = round(quat[1], round_amount)
        state['z_quaternion'] = round(quat[2], round_amount)
        state['w_quaternion'] = round(quat[3], round_amount)

        # Velocity
        #state['x_velocity'] = round(theta_dot, round_amount)
        #state['y_velocity'] = round(0.0, round_amount)
        state['x_velocity'] = round(0.0, round_amount)
        state['y_velocity'] = round(theta_dot, round_amount)
        state['z_velocity'] = round(0.0, round_amount)

        world_state['pole'] = state

        # get block info ====================================
        block_state = list()
        for ind, val in enumerate(range(3)):
            state = dict()
            state['id'] = val

            state['x_position'] = 1.0
            state['y_position'] = 1.0
            state['z_position'] = 3.0

            state['x_velocity'] = 0.0
            state['y_velocity'] = 0.0
            state['z_velocity'] = 0.0

            block_state.append(state)

        world_state['blocks'] = block_state

        # Not needed for phase one but for compatability
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
