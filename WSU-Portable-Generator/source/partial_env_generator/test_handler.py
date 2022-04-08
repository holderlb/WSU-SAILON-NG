#!/usr/bin/env python3
import copy
import json
import random

from .test_loader import TestLoader


class TestHandler:

    # Init function, accepts connection and address info
    def __init__(self, domain: str = 'cartpole', novelty: int = 0, difficulty: str = 'easy',
                 seed: int = 123, trial_novelty: int = 0, day_offset: int = 0, use_img: bool = False,
                 path: str = "partial_env_generator/envs/", use_gui: bool = False,
                 ta2_generator_config: dict = None):

        # Set parameters
        self.seed = seed
        self.domain = domain
        self.novelty = novelty
        self.difficulty = difficulty
        self.trial_novelty = trial_novelty
        self.difficulty = difficulty
        self.day_offset = day_offset
        self.use_img = use_img
        self.path = path
        self.use_gui = use_gui
        self.ta2_generator_config = copy.deepcopy(ta2_generator_config)

        # Load test based on params
        self.test = TestLoader(domain=self.domain,
                               novelty_level=self.novelty,
                               trial_novelty=self.trial_novelty,
                               seed=self.seed,
                               difficulty=self.difficulty,
                               day_offset=self.day_offset,
                               use_img=self.use_img,
                               path=self.path,
                               use_gui=self.use_gui,
                               ta2_generator_config=self.ta2_generator_config)

        # Get first information
        self.information = self.test.get_state()

        return None

    def apply_action(self, action):
        action = action['action']
        self.test.act(action)
        self.information = self.test.get_state()
        return self.information['performance']

    def get_feature_vector(self):
        return self.information['sensors']

    def get_feature_label(self):
        return {'action': self.information['action']}

    def is_episode_done(self):
        return self.test.is_done
