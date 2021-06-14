#!/usr/bin/env python3
import json
import random

from .test_loader import TestLoader


class TestHandler:

    # Init function, accepts connection and address info
    def __init__(self, domain: str = 'cartpole', novelty: int = 0, difficulty: str = 'easy',
                 seed: int = 123, trial_novelty: int = 0, day_offset: int = 0):
        # Set parameters
        self.seed = seed
        self.domain = domain
        self.novelty = novelty
        self.difficulty = difficulty
        self.trial_novelty = trial_novelty
        self.difficulty = difficulty
        self.day_offset = day_offset

        # Check for using is_novel or not
        self.is_novel = bool(self.novelty)

        # Load test based on params
        self.test = TestLoader(domain=self.domain,
                               novelty_level=self.trial_novelty,
                               is_novel=self.is_novel,
                               seed=self.seed,
                               difficulty=self.difficulty,
                               day_offset=self.day_offset)

        # Get first information
        self.information = self.test.get_state()

        return

    def apply_action(self, action):
        action = action['action']
        self.test.act(action)
        self.information = self.test.get_state()
        return self.information['performance']

    def get_feature_vector(self):
        return self.information['sensors']

    def get_feature_label(self):
        return {'action': self.information['action']}

    def get_action_list(self):
        return self.information['action_list']

    def is_episode_done(self):
        return self.test.is_done

# EoF
