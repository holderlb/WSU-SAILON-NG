#!/usr/bin/env python3
# ************************************************************************************************ #
# **                                                                                            ** #
# **    AIQ-SAIL-ON Generator Agent Example                                                     ** #
# **                                                                                            ** #
# **        Brian L Thomas, 2020                                                                ** #
# **                                                                                            ** #
# **  Tools by the AI Lab - Artificial Intelligence Quotient (AIQ) in the School of Electrical  ** #
# **  Engineering and Computer Science at Washington State University.                          ** #
# **                                                                                            ** #
# **  Copyright Washington State University, 2020                                               ** #
# **  Copyright Brian L. Thomas, 2020                                                           ** #
# **                                                                                            ** #
# **  All rights reserved                                                                       ** #
# **  Modification, distribution, and sale of this work is prohibited without permission from   ** #
# **  Washington State University.                                                              ** #
# **                                                                                            ** #
# **  Contact: Brian L. Thomas (bthomas1@wsu.edu)                                               ** #
# **  Contact: Larry Holder (holder@wsu.edu)                                                    ** #
# **  Contact: Diane J. Cook (djcook@wsu.edu)                                                   ** #
# ************************************************************************************************ #

import configparser
import datetime
import copy
import json
import logging
import logging.handlers
import optparse
import pytz
import queue
import random
import sys
import threading
import time
import uuid

from objects.GENERATOR_logic import GeneratorLogic
from env_generator.test_handler import TestHandler


class ThreadedTestHandler(threading.Thread):
    def __init__(self, domain: str, novelty: int, difficulty: str, seed: int, trial_novelty: int,
                 day_offset: int, response_queue: queue.Queue, use_image: bool,
                 ta2_generator_config: dict):
        threading.Thread.__init__(self)
        self.domain = domain
        self.novelty = novelty
        self.difficulty = difficulty
        self.seed = seed
        self.trial_novelty = trial_novelty
        self.day_offset = day_offset
        self.response_queue = response_queue
        self.use_image = use_image
        self.ta2_generator_config = copy.deepcopy(ta2_generator_config)

        self.is_done = False
        return

    def run(self):
        # Initialize GENERATOR here with novelty, difficulty, and seed.
        self.response_queue.put(TestHandler(domain=self.domain,
                                            novelty=self.novelty,
                                            difficulty=self.difficulty,
                                            seed=self.seed,
                                            trial_novelty=self.trial_novelty,
                                            day_offset=self.day_offset,
                                            use_img=self.use_image,
                                            ta2_generator_config=self.ta2_generator_config))
        while not self.is_done:
            time.sleep(0.1)
        return

    def stop(self):
        self.is_done = True
        return


class GeneratorAgent(GeneratorLogic):
    def __init__(self, options):
        super().__init__(config_file=options.config,
                         printout=options.printout,
                         debug=options.debug,
                         fulldebug=options.fulldebug,
                         logfile=options.logfile,
                         domain=options.domain)

        self.is_episode_done = False
        self.GENERATOR = None
        self.episode_data_number = None
        self.episode_data_count = None
        self.last_label = dict()
        self.episode_score = list()
        return

    def get_novelty_description(self, domain: str, novelty: int, difficulty: str) -> dict:
        novelty_description = dict()
        return novelty_description

    def initilize_generator(self, domain: str, novelty: int, difficulty: str, seed: int,
                            trial_novelty: int, day_offset: int, use_image: bool,
                            ta2_generator_config: dict):
        del self.GENERATOR
        # Set variable is_episode_done to False.
        self.is_episode_done = False

        self.GENERATOR = None
        response_queue = queue.Queue()
        # Initialize GENERATOR here with novelty, difficulty, and seed.
        threaded_gen = ThreadedTestHandler(domain=domain,
                                           novelty=novelty,
                                           difficulty=difficulty,
                                           seed=seed,
                                           trial_novelty=trial_novelty,
                                           day_offset=day_offset,
                                           response_queue=response_queue,
                                           use_image=use_image,
                                           ta2_generator_config=ta2_generator_config)
        threaded_gen.start()
        while self.GENERATOR is None:
            try:
                # Try to get the response from the queue for 1 second before letting the
                # network event loop do some work.
                self.GENERATOR = response_queue.get(block=True, timeout=1)

            except queue.Empty:
                # If the queue was empty then let amqp do a little work before trying again.
                self.amqp.process_data_events(time_limit=1.0)

        threaded_gen.stop()
        threaded_gen.join()
        return

    def get_feature_vector(self) -> (dict, dict):
        feature_vector = dict()
        feature_label = dict()

        # Provide the current feature vector.
        # feature_vector = self.GENERATOR.get_feature_vector()
        feature_vector = self.GENERATOR.get_feature_vector()

        # Provide the current feature label.
        # This can be left as a dict() if there is no label to provide.
        # feature_label = self.GENERATOR.get_feature_label()
        feature_label = self.GENERATOR.get_feature_label()

        return feature_vector, feature_label

    def apply_action(self, label_prediction: dict) -> float:
        self.log.debug('action: {}'.format(label_prediction))
        # Apply the given action and return the new performance value.
        # performance = self.GENERATOR.apply_action(label_prediction)
        performance = self.GENERATOR.apply_action(label_prediction)

        # Check if the episode is done, if so then set the is_episode_done variable to True.
        # if self.GENERATOR.is_episode_done():
        #     self.is_episode_done = True
        if self.GENERATOR.is_episode_done():
            self.is_episode_done = True

        return performance

    def cleanup_generator(self):
        # This function is called when self.is_episode_done == True or if the server takes too
        # long and we need to reset to an available state.
        if self.is_episode_done:
            self.log.debug('Test has finished')
        else:
            self.log.debug('Server comms cut')

        del self.GENERATOR
        self.GENERATOR = None
        return


if __name__ == "__main__":
    parser = optparse.OptionParser(usage="usage: %prog [options]")
    parser.add_option("--domain",
                      dest="domain",
                      help="Override any domain in the config file.")
    parser.add_option("--config",
                      dest="config",
                      help="Custom Generator config file.",
                      default="client.config")
    parser.add_option("--debug",
                      dest="debug",
                      action="store_true",
                      help="Set logging level to DEBUG from INFO.",
                      default=False)
    parser.add_option("--fulldebug",
                      dest="fulldebug",
                      action="store_true",
                      help="Set logging level to DEBUG from INFO for all imported libraries.",
                      default=False)
    parser.add_option("--logfile",
                      dest="logfile",
                      help="Filename if you want to write the log to disk.")
    parser.add_option("--printout",
                      dest="printout",
                      action="store_true",
                      help="Print output to the screen at given logging level.",
                      default=False)
    (options, args) = parser.parse_args()
    if options.fulldebug:
        options.debug = True
    agent = GeneratorAgent(options)
    agent.run()
    agent.stop()
