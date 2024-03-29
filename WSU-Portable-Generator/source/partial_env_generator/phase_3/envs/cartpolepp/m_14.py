import math
import numpy as np
import os.path

from .cartpoleplusplus import CartPoleBulletEnv


# Copy of novel 3
class CartPolePPMock14(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        self.r = 0.5
        if self.difficulty == 'easy':
            self.force = 2.0
        elif self.difficulty == 'medium':
            self.force = 3.0
        elif self.difficulty == 'hard':
            self.force = 4.0

        return None


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
            self.blocks[i] = p.loadURDF(os.path.join(self.path, 'models', 'block.urdf'))

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
            p.resetBasePositionAndOrientation(i, pos, [0, 0, 1, 0])

        # Cartpole pos
        pos, _, _, _, _, _ = p.getLinkState(self.cartpole, 0)
        cart_x = pos[0]
        cart_y = pos[1]
        cart_z = 0.5

        for i in self.blocks:
            if self.np_random.random() < self.r:
                pos, _ = p.getBasePositionAndOrientation(i)
                u1 = np.asarray([cart_x - pos[0], cart_y - pos[1], cart_z - pos[2]])
                if np.linalg.norm(u1) == 0.0:
                    u1 = np.asarray([self.np_random.random() * 9, self.np_random.random() * 9, self.np_random.random() * 4 + 5])
                else:
                    u1 = np.multiply(u1 / np.linalg.norm(u1), self.force)
                p.resetBaseVelocity(i, u1, [0, 0, 0])
            else:
                vel = self.np_random.uniform(low=-1.0, high=1.0, size=(3,))
                vel = np.multiply(vel, self.force)
                p.resetBaseVelocity(i, vel, [0, 0, 0])

        return None
