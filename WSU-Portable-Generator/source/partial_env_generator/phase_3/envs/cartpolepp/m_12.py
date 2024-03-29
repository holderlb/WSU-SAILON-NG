import math
import numpy as np
import os.path

from .cartpoleplusplus import CartPoleBulletEnv


class CartPolePPMock12(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        self.seed(1)  # force a constant seed for demo purpuses
        return None



        return None


    def reset_world(self):
        # Reset world (assume is created)
        p = self._p

        #for demo force seed based on current tick
        self.seed(self.tick)


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
#        self.nb_blocks = self.np_random.integers(3) + 2
        self.nb_blocks =  1  #one attacker is enough and easier to see what is going on        
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
        
        # Set block velocities

        TBmod=True   #TB mod sets mock to aim at agent not a random point, and to move more slowly        
        if(TBmod):
            u1 = cart_pos         
            force = self.np_random.random()*2+2  # don't alow zero force
            alreadyattacking = False;
            for i in self.blocks:
                pos, ori = p.getBasePositionAndOrientation(i)
                u2 = np.asarray([u1[0] - pos[0], u1[1] - pos[1], u1[2] - pos[2]])
                if (alreadyattacking or np.linalg.norm(u2) == 0.0): # if bad norm or if not first block
                    u2 = np.asarray([self.np_random.random() * 4+2, self.np_random.random() * 4+2, self.np_random.random() * 3 +1])
                else:
                    u2 = np.multiply(u2 / np.linalg.norm(u2), force)
#                    alreadyattacking = True;
        else:
            # Set block velocities to aim at ramdon lociton but move fast
            u1 = self.np_random.uniform(low=-4.0, high=4.0, size=(3,))
            u1[2] = u1[2] + 5.0
            force = self.np_random.random() * 10.0
            for i in self.blocks:
                pos, ori = p.getBasePositionAndOrientation(i)
                u2 = np.asarray([u1[0] - pos[0], u1[1] - pos[1], u1[2] - pos[2]])
                if np.linalg.norm(u1) == 0.0:
                    u2 = np.asarray([self.np_random.random() * 9, self.np_random.random() * 9, self.np_random.random() * 4 + 5])
                else:
                    u2 = np.multiply(u2 / np.linalg.norm(u2), force)
        p.resetBaseVelocity(i, [u2[0], u2[1], u2[2]], [0, 0, 0])

        return None
