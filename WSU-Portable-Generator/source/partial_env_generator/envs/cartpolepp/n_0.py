from .cartpoleplusplus import CartPoleBulletEnv


class CartPole(CartPoleBulletEnv):

    def __init__(self, difficulty, renders=False):
        super().__init__(renders=renders)

        self.difficulty = difficulty

        return None

