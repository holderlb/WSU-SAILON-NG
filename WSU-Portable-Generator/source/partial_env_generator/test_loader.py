# Loads tests and acts as go between

# Used for time since epoch sensor
from time import time
import random
import numpy as np
import sys
import json
import zlib
from base64 import b64encode
import blosc

class TestLoader:

    def __init__(self, domain: str = 'cartpole', novelty_level: int = 0, trial_novelty: bool = True,
                 seed: int = 0, difficulty: str = 'easy', day_offset: int = 0,
                 week_shift: int = None, generate_days: int = None, use_img: bool = False,
                 path: str = None):
        # Set internal params        
        self.domain = domain
        self.novelty_level = novelty_level
        self.trial_novelty = trial_novelty
        self.seed = seed
        self.difficulty = difficulty
        self.day_offset = day_offset
        self.week_shift = week_shift
        self.generate_days = generate_days
        self.use_img = use_img
        self.path = path

        # Determine level here
        self.use_mock = False
        self.use_novel = False
        self.level = -1

        if int(self.novelty_level/100) == 1:
            self.use_mock = True
        elif int(self.novelty_level/100) == 2:
            self.use_novel = True
        else:
            raise Exception("Invalid novelty level sent to test_loader!")

        self.level = int(str(self.novelty_level)[-1])
        if self.level < 0 or self.level >= 6:
            raise Exception("Invalid novelty level sent to test_loader!")

        # Do a little catching here for difficulty
        if self.difficulty not in ['easy', 'medium', 'hard']:
            raise Exception("Invalid difficulty sent to test_loader!")

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
        # Partial only has mock novelties :P
        if self.use_novel and self.level != 0:
            print('Shame on you and your ancestors!')
            print('No real novelties allowed!!')
            sys.exit()

        # Filter by domain
        if self.domain == 'cartpole':
            # Filter by novelty level
            if self.level == 0:
                from .envs.cartpolepp.n_0 import CartPole
                self.env = CartPole(self.difficulty)
            # Mocks
            elif self.use_mock:
                if self.level == 1:
                    from .envs.cartpolepp.m_1 import CartPolePPMock1 as CartPole
                    self.env = CartPole(self.difficulty)
                elif self.level == 2:
                    from .envs.cartpolepp.m_2 import CartPolePPMock2 as CartPole
                    self.env = CartPole(self.difficulty)
                elif self.level == 3:
                    from .envs.cartpolepp.m_3 import CartPolePPMock3 as CartPole
                    self.env = CartPole(self.difficulty)
                elif self.level == 4:
                    from .envs.cartpolepp.m_4 import CartPolePPMock4 as CartPole
                    self.env = CartPole(self.difficulty)
                elif self.level == 5:
                    from .envs.cartpolepp.m_5 import CartPolePPMock5 as CartPole
                    self.env = CartPole(self.difficulty)
            else:
                print(self.use_mock, self.use_novel, self.level)
                raise ValueError('Domain: ' + self.domain + ', Novelty: ' +
                                 str(self.novelty_level) + ', is not recognized!')

            # Set env camera here, fix later?
            self.env.use_img = self.use_img

            # Use seed here
            self.env.seed(self.seed)

            # Set internal path
            self.env.path = self.path + "cartpolepp/"

            # Set internal reward here
            self.reward = 0

        elif self.domain == 'vizdoom':
            from .envs.vizdoom.viz import SailonViz
            self.env = SailonViz(self.use_mock, self.use_novel, self.level, self.use_img,
                                 self.seed, self.difficulty, self.path)

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
        self.reward = reward
        self.is_done = done
        self.info = info

        return None

    def format_action(self, action):
        # Check for domain type
        if self.domain == 'cartpole':
            if action == 'nothing':
                action = 0
            elif action == 'left':
                action = 1
            elif action == 'right':
                action = 2
            elif action == 'forward':
                action = 3
            elif action == 'backward':
                action = 4

        elif self.domain == 'smartenv':
            # Do nothing
            a = 2

        return action

    def format_sensor(self):
        if self.domain == 'cartpole':

            # Add time here
            self.time = self.time + 1.0 / 30.0

            self.sensors = self.obs
            self.sensors['time_stamp'] = self.time
            self.sensors['image'] = self.env.get_image()

            self.actions = ['left', 'right', 'forward', 'backward', 'nothing']

            self.response = {'sensors': self.sensors,
                             'performance': self.reward,
                             'action_list': self.actions,
                             'action': 'left'}

        elif self.domain == 'vizdoom':
            # Add time here
            self.time = self.time + 1.0 / 30.0

            self.sensors = self.obs
            self.sensors['time_stamp'] = self.time
            self.sensors['image'] = self.env.get_image()

            self.response = {'sensors': self.sensors,
                             'performance': self.reward,
                             'action_list': self.info,
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

            self.sensors['image'] = None
            self.response = {'sensors': self.sensors,
                             'performance': self.reward,
                             'action_list': self.actions,
                             'action': label}

        # Compress image if not None
        if self.response['sensors']['image'] is not None:
            # print('raw image size = {}'.format(sys.getsizeof(
            #     json.dumps(self.response['sensors']['image']))))
            #comp_img = zlib.compress(json.dumps(self.response['sensors']['image']).encode('utf-8'))
            comp_img = blosc.pack_array(self.response['sensors']['image'])
            #print("before")
            #print(hash(comp_img))
            # del self.response['sensors']['image']
            self.response['sensors']['image'] =  b64encode(comp_img).decode('ascii')
            # self.response['sensors']['image'] = comp_img

            # print('compressed image size = {}'.format(sys.getsizeof(self.response['sensors']['image'])))
        # Send response
        return self.response

# EoF