"""
Classic cart-pole system implemented by Rich Sutton et al.
Copied from http://incompleteideas.net/book/code/pole.c
"""

import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import pybullet as p2
from pybullet_utils import bullet_client as bc


class CartPoleBulletEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array'], 'video.frames_per_second': 50}

    def __init__(self, use_img=False, renders=False, discrete_actions=True):
        # start the bullet physics server
        self._renders = renders
        self._discrete_actions = discrete_actions
        self._render_height = 200
        self._render_width = 320
        self._physics_client_id = -1
        self.theta_threshold_radians = 12 * 2 * math.pi / 360
        self.x_threshold = 0.4  # 2.4
        self.use_img = use_img
        high = np.array([self.x_threshold * 2, np.finfo(np.float32).max,
                         self.theta_threshold_radians * 2, np.finfo(np.float32).max])

        # Environmental params
        self.force_mag = 15
        self.timeStep = 1.0/50.0
        self.yaw_limit = 170

        # Internal params
        self.path = "partial_env_generator/envs/cartpolepp/"
        self.tick_limit = 200
        self.tick = -1

        # Object definitions
        self.nb_blocks = None
        self.cartpole = -10
        self.ground = None
        self.blocks = list()
        self.walls = None
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
        self._configure()

        return None

    def _configure(self, display=None):
        self.display = display

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        p = self._p
        if self._discrete_actions:
            force = self.force_mag if action == 1 else -self.force_mag
        else:
            force = action[0]

        # based on action decide the x and y forces
        fx = fy = 0
        if action == 0:
            pass
        elif action == 1:
            fx = self.force_mag
        elif action == 2:
            fx = -self.force_mag
        elif action == 3:
            fy = self.force_mag
        elif action == 4:
            fy = -self.force_mag
        else:
            raise Exception("unknown discrete action [%s]" % action)
        p.applyExternalForce(self.cartpole, 0, (fx, fy, 0.0), (0, 0, 0), p.WORLD_FRAME)

        # Apply anti-gravity to blocks
        for i in self.blocks:
            p.applyExternalForce(i, -1, (0, 0, 9.8), (0, 0, 0), p.LINK_FRAME)

        p.stepSimulation()

        done = self.is_done()
        reward = self.get_reward()

        self.tick = self.tick + 1

        return self.get_state(), reward, done, {}

    # Check if is done
    def is_done(self):
        # Check tick limit condition
        if self.tick >= self.tick_limit:
            return True

        # Check pole angle condition
        p = self._p
        pos, vel, jRF, aJMT = p.getJointStateMultiDof(self.cartpole, 1)

        pos = self.quaternion_to_euler(*pos)
        if abs(pos[2]) < self.yaw_limit or abs(abs(pos[1]) - 180) < self.yaw_limit:
            return True
        else:
            return False

        return None

    def get_reward(self):
        return self.tick / self.tick_limit

    def reset(self):
        # Create client if it doesnt exist
        if self._physics_client_id < 0:
            self.generate_world()

        self.tick = -1
        self.reset_world()

        # Run for one step to get everything going
        self.step(0)

        return self.get_state(initial=True)

    # Used to generate the initial world state
    def generate_world(self):
        # Create bullet physics client
        if self._renders:
            self._p = bc.BulletClient(connection_mode=p2.GUI)
        else:
            self._p = bc.BulletClient()
        self._physics_client_id = self._p._client

        # Load world simulation
        p = self._p
        p.resetSimulation()
        p.setGravity(0, 0, -9.8)
        p.setTimeStep(self.timeStep)
        p.setRealTimeSimulation(0)

        # Load world objects
        self.cartpole = p.loadURDF(self.path + "models/ground_cart.urdf")
        self.walls = p.loadURDF(self.path + "models/walls.urdf")

        # Set walls to be bouncy
        for joint_nb in range(-1, 6):
            p.changeDynamics(self.walls, joint_nb, restitution=1.0, lateralFriction=0.0,
                             rollingFriction=0.0, spinningFriction=0.0)

        return None

    def reset_world(self):
        # Reset world (assume is created)
        p = self._p

        # Delete cartpole
        if self.cartpole == -10:
            self.cartpole = p.loadURDF(self.path + "models/ground_cart.urdf")
        else:
            p.removeBody(self.cartpole)
            self.cartpole = p.loadURDF(self.path + "models/ground_cart.urdf")

        # This big line sets the spehrical joint on the pole to loose
        p.setJointMotorControlMultiDof(self.cartpole, 1, p.POSITION_CONTROL, targetPosition=[0, 0, 0, 1],
                                       targetVelocity=[0, 0, 0], positionGain=0, velocityGain=0.1,
                                       force=[0, 0, 0])

        # Reset cart (technicaly ground object)
        cart_pos = list(self.np_random.uniform(low=-3, high=3, size=(2,))) + [0]
        cart_vel = list(self.np_random.uniform(low=-50, high=50, size=(2,))) + [0]
        p.resetBasePositionAndOrientation(self.cartpole, cart_pos, [0, 0, 0, 1])
        p.applyExternalForce(self.cartpole, 0, cart_vel, (0, 0, 0), p.LINK_FRAME)

        # Reset pole
        randstate = list(self.np_random.uniform(low=-0.05, high=0.05, size=(6,)))
        pole_pos = randstate[0:3] + [1]
        # zero so it doesnt spin like a top :)
        pole_ori = list(randstate[3:5]) + [0]
        p.resetJointStateMultiDof(self.cartpole, 1, targetValue=pole_pos, targetVelocity=pole_ori)

        # Delete old blocks
        for i in self.blocks:
            p.removeBody(i)

        # Load blocks in
        self.nb_blocks = np.random.randint(4) + 1
        self.blocks = [None] * self.nb_blocks
        for i in range(self.nb_blocks):
            self.blocks[i] = p.loadURDF(self.path + "models/block.urdf")

        # Set blocks to be bouncy
        for i in self.blocks:
            p.changeDynamics(i, -1, restitution=1.0, lateralFriction=0.0,
                             rollingFriction=0.0, spinningFriction=0.0)

        # Set block posistions
        min_dist = 1
        cart_pos, _ = p.getBasePositionAndOrientation(self.cartpole)
        cart_pos = np.asarray(cart_pos)
        for i in self.blocks:
            pos = self.np_random.uniform(low=-4.0, high=4.0, size=(3,))
            pos[2] = pos[2] + 5.0
            while np.linalg.norm(cart_pos[0:2] - pos[0:2]) < min_dist:
                pos = self.np_random.uniform(low=-4.0, high=4.0, size=(3,))
                # Z is not centered at 0.0
                pos[2] = pos[2] + 5.0
            p.resetBasePositionAndOrientation(i, pos, [0, 0, 0, 1])

        # Set block velocities
        for i in self.blocks:
            vel = self.np_random.uniform(low=6.0, high=10.0, size=(3,))
            for ind, val in enumerate(vel):
                if np.random.rand() < 0.5:
                    vel[ind] = val * -1

            p.resetBaseVelocity(i, vel, [0, 0, 0])

        return None

    # Unified function for getting state information
    def get_state(self, initial=False):
        p = self._p
        world_state = dict()
        round_amount = 6

        # Get cart info ============================================
        state = dict()

        # Handle pos, ori
        base_pose, _ = p.getBasePositionAndOrientation(self.cartpole)
        pos, vel, jRF, aJMT = p.getJointStateMultiDof(self.cartpole, 0)
        state['x_position'] = round(pos[0] + base_pose[0], round_amount)
        state['y_position'] = round(pos[1] + base_pose[1], round_amount)
        state['z_position'] = round(0.1 + base_pose[2], round_amount)

        # Handle velocity
        state['x_velocity'] = round(vel[0], round_amount)
        state['y_velocity'] = round(vel[1], round_amount)
        state['z_velocity'] = round(0.0, round_amount)

        world_state['cart'] = state

        # Get pole info =============================================
        state = dict()
        use_euler = False

        # Position and orientation, the other two not used
        pos, vel, jRF, aJMT = p.getJointStateMultiDof(self.cartpole, 1)

        # Convert quats to eulers
        eulers = self.quaternion_to_euler(*pos)

        # Position
        if use_euler:
            state['x_position'] = round(eulers[0], round_amount)
            state['y_position'] = round(eulers[1], round_amount)
            state['z_position'] = round(eulers[2], round_amount)
        else:
            state['x_quaternion'] = round(pos[0], round_amount)
            state['y_quaternion'] = round(pos[1], round_amount)
            state['z_quaternion'] = round(pos[2], round_amount)
            state['w_quaternion'] = round(pos[3], round_amount)

        # Velocity
        state['x_velocity'] = round(vel[0], round_amount)
        state['y_velocity'] = round(vel[1], round_amount)
        state['z_velocity'] = round(vel[2], round_amount)

        world_state['pole'] = state

        # get block info ====================================
        block_state = list()
        for ind, val in enumerate(self.blocks):
            state = dict()
            state['id'] = val

            pos, _ = p.getBasePositionAndOrientation(val)
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
        # Hardcoded cause I don't know how to get the info :(
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

    def get_image(self):
        if self.use_img:
            return self.render()
        else:
            return None

    def render(self, mode='human', close=False):
        if mode == "human":
            self._renders = True
        if mode != "rgb_array":
            return np.array([])
        base_pos = [0, 0, 0]
        self._cam_dist = 2
        self._cam_pitch = 0.3
        self._cam_yaw = 0
        if (self._physics_client_id >= 0):
            view_matrix = self._p.computeViewMatrixFromYawPitchRoll(
                cameraTargetPosition=base_pos,
                distance=self._cam_dist,
                yaw=self._cam_yaw,
                pitch=self._cam_pitch,
                roll=0,
                upAxisIndex=2)
            proj_matrix = self._p.computeProjectionMatrixFOV(fov=60,
                                                             aspect=float(self._render_width) /
                                                                    self._render_height,
                                                             nearVal=0.1,
                                                             farVal=100.0)
            (_, _, px, _, _) = self._p.getCameraImage(
                width=self._render_width,
                height=self._render_height,
                renderer=self._p.ER_BULLET_HARDWARE_OPENGL,
                viewMatrix=view_matrix,
                projectionMatrix=proj_matrix)
        else:
            px = np.array([[[255, 255, 255, 255]] * self._render_width] * self._render_height, dtype=np.uint8)
        rgb_array = np.array(px, dtype=np.uint8)
        rgb_array = np.reshape(np.array(px), (self._render_height, self._render_width, -1))
        rgb_array = rgb_array[:, :, :3]
        return rgb_array

    def configure(self, args):
        pass

    def eulerToQuaternion(self, yaw, pitch, roll):
        qx = np.sin(yaw / 2) * np.sin(pitch / 2) * np.cos(roll / 2) + np.cos(yaw / 2) * np.cos(pitch / 2) * np.sin(
            roll / 2)
        qy = np.sin(yaw / 2) * np.cos(pitch / 2) * np.cos(roll / 2) + np.cos(yaw / 2) * np.sin(pitch / 2) * np.sin(
            roll / 2)
        qz = np.cos(yaw / 2) * np.sin(pitch / 2) * np.cos(roll / 2) - np.sin(yaw / 2) * np.cos(pitch / 2) * np.sin(
            roll / 2)
        qw = np.cos(yaw / 2) * np.cos(pitch / 2) * np.cos(roll / 2) - np.sin(yaw / 2) * np.sin(pitch / 2) * np.sin(
            roll / 2)

        return (qx, qy, qz, qw)

    def quaternion_to_euler(self, w, x, y, z):
        ysqr = y * y

        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + ysqr)
        X = np.degrees(np.arctan2(t0, t1))

        t2 = +2.0 * (w * y - z * x)
        t2 = np.where(t2 > +1.0, +1.0, t2)
        # t2 = +1.0 if t2 > +1.0 else t2

        t2 = np.where(t2 < -1.0, -1.0, t2)
        # t2 = -1.0 if t2 < -1.0 else t2
        Y = np.degrees(np.arcsin(t2))

        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (ysqr + z * z)
        Z = np.degrees(np.arctan2(t3, t4))

        return (X, Y, Z)

    def close(self):
        if self._physics_client_id >= 0:
            self._p.disconnect()
        self._physics_client_id = -1


class CartPoleContinuousBulletEnv(CartPoleBulletEnv):
    metadata = {'render.modes': ['human', 'rgb_array'], 'video.frames_per_second': 50}

    def __init__(self, renders=False):
        # start the bullet physics server
        CartPoleBulletEnv.__init__(self, renders, discrete_actions=False)
