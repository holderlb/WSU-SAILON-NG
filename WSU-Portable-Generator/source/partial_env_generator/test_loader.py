# Loads tests and acts as go between

# Used for time since epoch sensor
from time import time
import random
import numpy as np


class TestLoader:

    def __init__(self, domain: str = 'cartpole', novelty_level: int = 0, is_novel: bool = True,
                 seed: int = 0, difficulty: str = 'easy', day_offset: int = 0,
                 week_shift: int = None, generate_days: int = None):
        # Set internal params        
        self.domain = domain
        self.novelty_level = novelty_level
        self.is_novel = is_novel
        self.seed = seed
        self.difficulty = difficulty
        self.day_offset = day_offset
        self.week_shift = week_shift
        self.generate_days = generate_days

        # Set initial conditions
        self.is_done = False
        self.time = time()

        # Initialize empty variables for assignment in the next few function calls.
        self.env = None
        self.reward = None
        self.obs = None
        self.info = None
        self.player = None
        self.enemy = None
        self.projectile = None
        self.sensors = None
        self.actions = None
        self.response = None

        # Set seeds (thread wide here)
        random.seed(self.seed)
        np.random.seed(self.seed)

        # Load the test
        self.load_test()

        # Start episode
        self.begin()

        return

    def load_test(self):
        # Filter by domain
        if self.domain == 'cartpole':
            # Filter by novelty level
            if self.novelty_level == 0 or not self.is_novel:
                from .envs.cartpole.cartpole_n0 import CartpoleN0
                self.env = CartpoleN0()
            # Obvious novelty
            elif self.novelty_level == 10:
                from .envs.cartpole.cartpole_n10 import CartpoleN10
                self.env = CartpoleN10(self.difficulty)
            else:
                raise ValueError('Domain: ' + self.domain + ', Novelty: ' +
                                 str(self.novelty_level) + ', is not recognized!')

            # Set internal reward here
            self.reward = 0

        elif self.domain == 'vizdoom':
            from .envs.vizdoom.viz import viz
            if self.novelty_level == 0 or not self.is_novel:
                self.env = viz('n0', self.seed, self.difficulty)
            elif self.novelty_level == 10:
                self.env = viz('n_10', self.seed, self.difficulty)
            else:
                raise ValueError('Domain: ' + self.domain + ', Novelty: ' +
                                 str(self.novelty_level) + ', is not recognized!')

            # Set internal reward here
            self.reward = 2000

        elif self.domain == 'smartenv':
            from .envs.smarthome.synsysenv import SynsysEnv
            self.env = SynsysEnv(novelty=self.novelty_level,
                                 difficulty=self.difficulty,
                                 use_novel=self.is_novel,
                                 day_offset=self.day_offset,
                                 week_shift=self.week_shift,
                                 generate_days=self.generate_days)
            # Set internal reward here
            self.reward = 0
        else:
            raise ValueError('Domain: ' + self.domain + ', is not recognized!')

        return None

    # Prepare env
    def begin(self):
        # Reset env
        obs = self.env.reset()

        # Set local state
        self.obs = obs
        self.is_done = False
        self.info = {}

        return None

    # Return state vars
    def get_state(self):
        return self.format_sensor()

    # Action input to env
    def act(self, action):
        # Format action into correct space
        action = self.format_action(action)

        # Perform single step update
        obs, reward, done, info = self.env.step(action)

        # Set local state
        self.obs = obs
        if self.domain == 'smartenv' or self.domain == 'vizdoom':
            self.reward = reward
        else:
            self.reward = self.reward + reward
        self.is_done = done
        self.info = info

        return None

    def format_action(self, action):
        # Check for domain type
        if self.domain == 'cartpole':
            if action == 'right':
                action = 1
            elif action == 'left':
                action = 0

        elif self.domain == 'smartenv':
            # Do nothing
            a = 2

        return action

    def format_sensor(self):
        if self.domain == 'cartpole':

            # Add time here
            self.time = self.time + 1.0 / 30.0
            self.sensors = {'time_stamp': self.time,
                            'cart_position': self.obs[0],
                            'cart_veloctiy': self.obs[1],
                            'pole_angle': self.obs[2],
                            'pole_angular_velocity': self.obs[3]}

            self.actions = ['left', 'right']

            self.response = {'sensors': self.sensors,
                             'performance': self.reward / 200,
                             'action_list': self.actions,
                             'action': 'left'}

        elif self.domain == 'vizdoom':
            # Add time here
            self.time = self.time + 1.0 / 30.0

            self.sensors = self.obs
            self.sensors['time_stamp'] = self.time

            self.actions = ['left', 'right', 'forward', 'backward', 'shoot', 'nothing']

            self.response = {'sensors': self.sensors,
                             'performance': self.reward,
                             'action_list': self.actions,
                             'action': 'left'}

        elif self.domain == 'smartenv':
            # Set local vars
            timestamp = self.obs[0]
            sensors = self.obs[1]
            label = self.obs[2]
            testbed_id = self.obs[3]

            # Filter out sensor types
            motion_sensors = list()
            motion_area_sensors = list()
            door_sensors = list()
            light_switch_sensors = list()
            light_level_sensors = list()
            for name in sensors:
                if "MA" in name:
                    motion_area_sensors.append(dict({'id': name,
                                                     'value': sensors[name]}))
                elif "M" in name:
                    motion_sensors.append(dict({'id': name,
                                                'value': sensors[name]}))
                elif "D" in name:
                    door_sensors.append(dict({'id': name,
                                              'value': sensors[name]}))
                elif "LL" in name:
                    light_level_sensors.append(dict({'id': name,
                                                     'value': sensors[name]}))
                elif "L" in name:
                    light_switch_sensors.append(dict({'id': name,
                                                      'value': sensors[name]}))

            self.sensors = {'time_stamp': timestamp,
                            'testbed_id': testbed_id,
                            'motion_sensors': motion_sensors,
                            'motion_area_sensors': motion_area_sensors,
                            'door_sensors': door_sensors,
                            'light_switch_sensors': light_switch_sensors,
                            'light_level_sensors': light_level_sensors}

            self.actions = {'wash_dishes': 'wash_dishes',
                            'relax': 'relax',
                            'personal_hygiene': 'personal_hygiene',
                            'bed_toilet_transition': 'bed_toilet_transition',
                            'cook': 'cook',
                            'sleep': 'sleep',
                            'take_medicine': 'take_medicine',
                            'leave_home': 'leave_home',
                            'work': 'work',
                            'enter_home': 'enter_home',
                            'eat': 'eat'}

            self.response = {'sensors': self.sensors,
                             'performance': self.reward,
                             'action_list': self.actions,
                             'action': label}

        # Send response
        return self.response

# EoF
