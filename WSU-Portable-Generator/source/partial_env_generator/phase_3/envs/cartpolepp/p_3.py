from .p_base import CartPoleBulletEnv
import numpy as np

class CartPole(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        if self.difficulty == 'easy':
            self.buckets = 30
        if self.difficulty == 'medium':
            self.buckets = 20
        if self.difficulty == 'hard':
            self.buckets = 10

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
        # print(self.state)
        number = self.buckets

        angle = np.arange(start=-6, stop=6, step=12/number)
        angle_b = min(angle, key=lambda x: abs(x-self.state[0]))

        anglespeed = np.arange(start=-10, stop=10, step=20/number)
        anglespeed_b = min(anglespeed, key=lambda x: abs(x-self.state[1]))

        pos = np.arange(start=-2.4, stop=2.4, step=4.8/number)
        pos_b = min(pos, key=lambda x: abs(x-self.state[2]))

        speed = np.arange(start=-1, stop=1, step=2/number)
        speed_b = min(speed, key=lambda x: abs(x-self.state[3]))

        self.state = angle_b, anglespeed_b, pos_b, speed_b
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
        quat = p.getQuaternionFromEuler([0,theta,0])

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
