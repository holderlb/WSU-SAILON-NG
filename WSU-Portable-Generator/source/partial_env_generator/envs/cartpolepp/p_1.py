from .p_base import CartPoleBulletEnv
import os

class CartPole(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        if self.difficulty == 'easy':
            self.file_name = 'cartpole_easy.urdf'
        elif self.difficulty == 'medium':
            self.file_name = 'cartpole_medium.urdf'
        elif self.difficulty == 'hard':
            self.file_name = 'cartpole_hard.urdf'
        else:
            self.file_name = 'cartpole.urdf'

        return None

    def reset_world(self):
        # Reset world (assume is created)
        p = self._p

        # Delete cartpole
        if self.cartpole == -10:
            self.cartpole = p.loadURDF(os.path.join(self.path, 'models/p/', self.file_name))
        else:
            p.removeBody(self.cartpole)
            self.cartpole = p.loadURDF(os.path.join(self.path, 'models/p/', self.file_name))

        # Set cart to have no friction
        p.changeDynamics(self.cartpole, -1, linearDamping=0, angularDamping=0)
        p.changeDynamics(self.cartpole, 0, linearDamping=0, angularDamping=0)
        p.changeDynamics(self.cartpole, 1, linearDamping=0, angularDamping=0)

        # Set pole to loose
        p.setJointMotorControl2(self.cartpole, 1, p.VELOCITY_CONTROL, force=0)
        p.setJointMotorControl2(self.cartpole, 0, p.VELOCITY_CONTROL, force=0)

        # Set random initial state
        randstate = self.np_random.uniform(low=-0.01, high=0.01, size=(2,))
        p.resetJointState(self.cartpole, 0, randstate[0], 1.0)
        p.resetJointState(self.cartpole, 1, 0.0, 0.4)
        self.state = p.getJointState(self.cartpole, 1)[0:2] + p.getJointState(self.cartpole, 0)[0:2]

        return None