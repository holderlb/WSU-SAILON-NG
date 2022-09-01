from .p_base import CartPoleBulletEnv


class CartPole(CartPoleBulletEnv):

    def __init__(self, difficulty, params: dict = None):
        super().__init__(params=params)

        self.difficulty = difficulty

        return None

