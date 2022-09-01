class Selector:

    def __init__(self):
        self.novelty_level = None
        self.hint_level = None
        return

    def get_hint(self, domain: str, novelty_level: int, hint_level: int):
        self.novelty_level = novelty_level
        self.hint_level = hint_level

        # Base hint object
        hint = {'level': self.novelty_level % 50,
                'entity': None,
                'attribute': None,
                'change': None}

        # Get domain specific hints
        if domain == 'cartpole':
            hint = self.cartpole_hint(hint)
        elif domain == 'vizdoom':
            hint = self.vizdoom_hint(hint)
        elif domain == 'smartenv':
            hint = self.smartenv_hint(hint)

        # Set hint to list if not already
        if type(hint) != list:
            hint = [hint]

        for i in range(len(hint)):
            # Filter based on hint level
            if hint_level == -1:
                hint[i]['level'] = None
                hint[i]['entity'] = None
                hint[i]['attribute'] = None
                hint[i]['change'] = None
            elif hint_level == 0:
                hint[i]['entity'] = None
                hint[i]['attribute'] = None
                hint[i]['change'] = None
            elif hint_level == 1:
                hint[i]['attribute'] = None
                hint[i]['change'] = None
            elif hint_level == 2:
                hint[i]['change'] = None

        return hint

    def cartpole_hint(self, hint):
        # Example Novleties
        if self.novelty_level == 101:
            hint['entity'] = 'cart'
            hint['attribute'] = 'mass'
            hint['change'] = 'increase'
        elif self.novelty_level == 102:
            hint['entity'] = 'block'
            hint['attribute'] = 'speed'
            hint['change'] = 'decrease'
        elif self.novelty_level == 103:
            hint['entity'] = 'block'
            hint['attribute'] = 'direction'
            hint['change'] = 'toward location'
        elif self.novelty_level == 104:
            hint['entity'] = 'block'
            hint['attribute'] = 'size'
            hint['change'] = 'increase'
        elif self.novelty_level == 105:
            hint['entity'] = 'block'
            hint['attribute'] = 'direction'
            hint['change'] = 'toward block'
        elif self.novelty_level == 106:
            hint['entity'] = 'block'
            hint['attribute'] = 'gravity'
            hint['change'] = 'increase'
        elif self.novelty_level == 107:
            hint['entity'] = 'block'
            hint['attribute'] = 'direction'
            hint['change'] = 'toward location'
        elif self.novelty_level == 108:
            hint['entity'] = 'block'
            hint['attribute'] = 'quantity'
            hint['change'] = 'increasing'

        return hint

    def vizdoom_hint(self, hint):
        # Example Novleties
        if self.novelty_level == 101:
            hint['entity'] = 'health'
            hint['attribute'] = 'quantity'
            hint['change'] = 'decrease'
        elif self.novelty_level == 102:
            hint['entity'] = 'enemy'
            hint['attribute'] = 'speed'
            hint['change'] = 'increase'
        elif self.novelty_level == 103:
            hint['entity'] = 'enemy'
            hint['attribute'] = 'direction'
            hint['change'] = 'toward player'
        elif self.novelty_level == 104:
            hint['entity'] = 'enemy'
            hint['attribute'] = 'damage'
            hint['change'] = 'increasing'
        elif self.novelty_level == 105:
            hint['entity'] = 'enemy'
            hint['attribute'] = 'direction'
            hint['change'] = 'away enemy'
        elif self.novelty_level == 106:
            hint = [hint] * 5
            hint[0]['entity'] = 'enemy'
            hint[0]['attribute'] = 'position'
            hint[0]['change'] = 'shift'
            hint[1]['entity'] = 'player'
            hint[1]['attribute'] = 'position'
            hint[1]['change'] = 'shift'
            hint[2]['entity'] = 'ammo'
            hint[2]['attribute'] = 'position'
            hint[2]['change'] = 'shift'
            hint[3]['entity'] = 'health'
            hint[3]['attribute'] = 'position'
            hint[3]['change'] = 'shift'
            hint[4]['entity'] = 'trap'
            hint[4]['attribute'] = 'position'
            hint[4]['change'] = 'shift'
        elif self.novelty_level == 107:
            hint['entity'] = 'enemy'
            hint['attribute'] = 'direction'
            hint['change'] = 'toward obstacle'
        elif self.novelty_level == 108:
            hint['entity'] = 'player'
            hint['attribute'] = 'ammo'
            hint['change'] = 'decreasing'

        return hint

    def smartenv_hint(self, hint):
        # Example Novleties
        if self.novelty_level == 101:
            hint['entity'] = 'sensor'
            hint['attribute'] = 'quantity'
            hint['change'] = 'decrease'
        elif self.novelty_level == 102:
            hint['entity'] = 'inhabitant'
            hint['attribute'] = 'variance'
            hint['change'] = 'decrease'
        elif self.novelty_level == 103:
            hint['entity'] = 'actvity'
            hint['attribute'] = 'quantity'
            hint['change'] = 'increase'
        elif self.novelty_level == 104:
            hint['entity'] = 'sensor'
            hint['attribute'] = 'correlation'
            hint['change'] = 'increase'
        elif self.novelty_level == 105:
            hint['entity'] = 'inhabitant'
            hint['attribute'] = 'quantity'
            hint['change'] = 'increase'
        elif self.novelty_level == 106:
            hint['entity'] = 'sensor'
            hint['attribute'] = 'frequency'
            hint['change'] = 'increase'
        elif self.novelty_level == 107:
            hint = [hint] * 2
            hint[0]['entity'] = 'leave_home'
            hint[0]['attribute'] = 'quantity'
            hint[0]['change'] = 'increase'
            hint[1]['entity'] = 'enter_home'
            hint[1]['attribute'] = 'quantity'
            hint[1]['change'] = 'increase'
        elif self.novelty_level == 108:
            hint['entity'] = 'sensor'
            hint['attribute'] = 'frequency'
            hint['change'] = 'decrease'

        return hint

