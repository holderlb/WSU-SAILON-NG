from .cartpole import Cartpole


class CartpoleN10(Cartpole):

    def __init__(self, difficulty):

        if difficulty == 'easy':
            masscart = 2.0
        elif difficulty == 'medium':
            masscart = 4.0
        elif difficulty == 'hard':
            masscart = 8.0

        super().__init__(masscart=masscart)

        return None
