# Used for time since epoch sensor
import copy
import sys
import json
import random
import zlib
import os.path

import numpy as np
from base64 import b64encode
import blosc


class TestLoader:

    def __init__(self, domain: str = 'cartpole', novelty_level: int = 0, trial_novelty: int = 0,
                 seed: int = 0, difficulty: str = 'easy', day_offset: int = 0,
                 week_shift: int = None, generate_days: int = None, use_img: bool = False,
                 path: str = "partial_env_generator/envs/", use_gui: bool = False,
                 ta2_generator_config: dict = None):
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
        self.use_gui = use_gui
        self.ta2_generator_config = copy.deepcopy(ta2_generator_config)

        # Set the custom seed if provided.
        if self.ta2_generator_config is not None:
            if 'episode_seed' in self.ta2_generator_config:
                if self.ta2_generator_config['episode_seed'] is not None:
                    self.seed = self.ta2_generator_config['episode_seed']

        # Determine options
        self.use_mock = False
        self.use_novel = False
        self.use_phase_one = False
        self.level = -1

        if self.novelty_level in [50, 51, 52, 53]:
            self.use_phase_one = True
        elif self.novelty_level in [101, 102, 103, 104, 105]:
            self.use_mock = True
        elif self.novelty_level in [201, 202, 203, 204, 205]:
            self.use_novel = True
            print('Real novelties [201-205] are not included in portable generator')
            raise Exception("Invalid novelty level sent to test_loader!")
        elif self.novelty_level in [200]:
            None
        else:
            raise Exception("Invalid novelty level sent to test_loader!")

        self.level = self.novelty_level % 50

        # Convert trial level to nums
        self.trial = int(str(self.trial_novelty)[-1])
        if self.trial < 0 or self.trial >= 7:
            raise Exception("Invalid trial level sent to test_loader!")

        # Do a little catching here for difficulty
        if self.difficulty not in ['easy', 'medium', 'hard']:
            raise Exception("Invalid difficulty sent to test_loader!")

        # Set initial conditions
        self.is_done = False

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
            if self.level == 0 and not self.use_phase_one:
                from .envs.cartpolepp.n_0 import CartPole

            # Mocks
            elif self.use_mock:
                if self.level == 1:
                    from .envs.cartpolepp.m_1 import CartPolePPMock1 as CartPole
                elif self.level == 2:
                    from .envs.cartpolepp.m_2 import CartPolePPMock2 as CartPole
                elif self.level == 3:
                    from .envs.cartpolepp.m_3 import CartPolePPMock3 as CartPole
                elif self.level == 4:
                    from .envs.cartpolepp.m_4 import CartPolePPMock4 as CartPole
                elif self.level == 5:
                    from .envs.cartpolepp.m_5 import CartPolePPMock5 as CartPole

            # Old phase 1 rebuilt in 3d
            elif self.use_phase_one:
                if self.level == 0:
                    from .envs.cartpolepp.p_0 import CartPole as CartPole
                elif self.level == 1:
                    from .envs.cartpolepp.p_1 import CartPole as CartPole
                elif self.level == 2:
                    from .envs.cartpolepp.p_2 import CartPole as CartPole
                elif self.level == 3:
                    from .envs.cartpolepp.p_3 import CartPole as CartPole

            # Throw error at this point
            else:
                print(self.use_mock, self.use_novel, self.level)
                raise ValueError('Domain: ' + self.domain + ', Novelty: ' +
                                 str(self.novelty_level) + ', is not recognized!')

            # Set internal reward here
            self.reward = 0.0

            # Package params here
            params = dict()
            params['seed'] = self.seed
            params['config'] = self.ta2_generator_config
            params['path'] = os.path.join(self.path, 'cartpolepp')
            params['use_img'] = self.use_img
            params['use_gui'] = self.use_gui

            # Create instance
            self.env = CartPole(self.difficulty, params=params)

        elif self.domain == 'vizdoom':
            from .envs.vizdoom.viz import SailonViz
            self.env = SailonViz(self.use_mock, self.use_novel, self.novelty_level, self.use_img,
                                 self.seed, self.difficulty, path=self.path, use_gui=self.use_gui)

            # Set internal reward here
            self.reward = 2000.0

        elif self.domain == 'smartenv':
            from .envs.smarthome.synsysenv import SynsysEnv
            self.env = SynsysEnv(novelty=self.level,
                                 difficulty=self.difficulty,
                                 use_novel=self.use_novel,
                                 use_mock=self.use_mock,
                                 use_img=self.use_img,
                                 seed=self.seed,
                                 trial=self.trial,
                                 day_offset=self.day_offset,
                                 week_shift=self.week_shift,
                                 generate_days=self.generate_days)
            # Set internal reward here
            self.reward = 0.0
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
        # Perform single step update
        obs, reward, done, info = self.env.step(action)

        # Set local state
        self.obs = obs
        self.reward = reward
        self.is_done = done
        self.info = info

        return None

    def format_sensor(self):
        if self.domain == 'cartpole':
            self.sensors = self.obs
            self.sensors['time_stamp'] = self.env.get_time()
            self.sensors['image'] = self.env.get_image()
            self.actions = self.env.get_actions()

            self.response = {'sensors': self.sensors,
                             'performance': self.reward,
                             'action_list': self.actions,
                             'action': 'left'}

        elif self.domain == 'vizdoom':
            self.sensors = self.obs
            self.sensors['time_stamp'] = self.env.get_time()
            self.sensors['image'] = self.env.get_image()
            self.actions = self.env.get_actions()

            self.response = {'sensors': self.sensors,
                             'performance': self.reward,
                             'action_list': self.actions,
                             'action': 'left'}

        elif self.domain == 'smartenv':
            self.actions = self.env.get_actions()
            self.sensors = self.obs
            self.sensors['image'] = None
            self.response = {'sensors': self.sensors,
                             'performance': self.reward,
                             'action_list': self.actions,
                             'action': self.env.last_label}

        # Compress image if not None
        if self.response['sensors']['image'] is not None:
            comp_img = blosc.pack_array(self.response['sensors']['image'])
            self.response['sensors']['image'] = b64encode(comp_img).decode('ascii')

        # Send response
        return self.response
