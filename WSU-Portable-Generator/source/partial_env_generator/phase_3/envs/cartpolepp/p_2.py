from .p_base import CartPoleBulletEnv
import numpy as np
import os


class CartPole(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        if self.difficulty == 'medium':
            zones = 20
            self.friction_zones = np.random.uniform(low=0.0125, high=0.1, size=(zones,))

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

        if self.difficulty == 'hard':
            theta, theta_dot, x, x_dot = p.getJointState(self.cartpole, 1)[0:2] + \
                                         p.getJointState(self.cartpole, 0)[0:2]
            fx = fx + (np.sign(x) * 1.0)

        if self.difficulty == 'medium':
            theta, theta_dot, x, x_dot = p.getJointState(self.cartpole, 1)[0:2] + \
                                         p.getJointState(self.cartpole, 0)[0:2]
            friction = self.friction_zones[int(x)+10]
            p.changeDynamics(self.cartpole, -1, linearDamping=friction, angularDamping=0)
            p.changeDynamics(self.cartpole, 0, linearDamping=friction, angularDamping=0)
            p.changeDynamics(self.cartpole, 1, linearDamping=friction, angularDamping=0)

        p.applyExternalForce(self.cartpole, 0, (fx, 0.0, 0.0), (0, 0, 0), p.LINK_FRAME)

        p.stepSimulation()

        done = self.is_done()
        reward = self.get_reward()

        self.tick = self.tick + 1

        return self.get_state(), reward, done, {}

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
        if self.difficulty == 'easy':
            p.changeDynamics(self.cartpole, -1, linearDamping=0.125, angularDamping=0)
            p.changeDynamics(self.cartpole, 0, linearDamping=0.125, angularDamping=0)
            p.changeDynamics(self.cartpole, 1, linearDamping=0.125, angularDamping=0)
        else:
            p.changeDynamics(self.cartpole, -1, linearDamping=0.0, angularDamping=0)
            p.changeDynamics(self.cartpole, 0, linearDamping=0.0, angularDamping=0)
            p.changeDynamics(self.cartpole, 1, linearDamping=0.0, angularDamping=0)

        # Set pole to loose
        p.setJointMotorControl2(self.cartpole, 1, p.VELOCITY_CONTROL, force=0)
        p.setJointMotorControl2(self.cartpole, 0, p.VELOCITY_CONTROL, force=0)

        # Set random initial state
        randstate = self.np_random.uniform(low=-0.01, high=0.01, size=(2,))
        p.resetJointState(self.cartpole, 0, randstate[0], 1.0)
        p.resetJointState(self.cartpole, 1, 0.0, 0.4)
        self.state = p.getJointState(self.cartpole, 1)[0:2] + p.getJointState(self.cartpole, 0)[0:2]

        return None