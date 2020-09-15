#!/usr/bin/env python3
# ************************************************************************************************ #
# **                                                                                            ** #
# **    AIQ-SAIL-ON TA2 Agent Example                                                           ** #
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

import copy
import optparse
import random
import time

from objects.TA2_logic import TA2Logic


class TA2Agent(TA2Logic):
    def __init__(self, options):
        super().__init__(config_file=options.config,
                         printout=options.printout,
                         debug=options.debug,
                         fulldebug=options.fulldebug,
                         logfile=options.logfile)

        self.possible_answers = list()
        return

    def experiment_start(self):
        """This function is called when this TA2 has connected to a TA1 and is ready to begin
        the experiment.
        """
        self.log.info('Experiment Start')
        return

    def training_start(self):
        """This function is called when we are about to begin training on episodes of data in
        your chosen domain.
        """
        self.log.info('Training Start')
        return

    def training_episode_start(self, episode_number: int):
        """This function is called at the start of each training episode, with the current episode
        number (0-based) that you are about to begin.

        Parameters
        ----------
        episode_number : int
            This identifies the 0-based episode number you are about to begin training on.
        """
        self.log.info('Training Episode Start: #{}'.format(episode_number))
        return

    def training_instance(self, feature_vector: dict, feature_label: dict) -> (dict, bool, int):
        """Process a training

        Parameters
        ----------
        feature_vector : dict
            The dictionary of the feature vector.  Domain specific feature vector formats are
            defined on the github (https://github.com/holderlb/WSU-SAILON-NG).
        feature_label : dict
            The dictionary of the label for this feature vector.  Domain specific feature labels
            are defined on the github (https://github.com/holderlb/WSU-SAILON-NG). This will always
            be in the format of {'action': label}.  Some domains that do not need an 'oracle' label
            on training data will receive a valid action chosen at random.

        Returns
        -------
        dict, bool, int
            A dictionary of your label prediction of the format {'action': label}.  This is
                strictly enforced and the incorrect format will result in an exception being thrown.
            A boolean as to whether agent detects novelty.
            Integer representing the predicted novelty level.
        """
        self.log.debug('Training Instance: feature_vector={}  feature_label={}'.format(
            feature_vector, feature_label))
        if feature_label not in self.possible_answers:
            self.possible_answers.append(copy.deepcopy(feature_label))

        label_prediction = random.choice(self.possible_answers)
        novelty_detected = False
        novelty = 0

        return label_prediction, novelty_detected, novelty

    def training_performance(self, performance: float):
        """Provides the current performance on training after each instance.

        Parameters
        ----------
        performance : float
            The normalized performance score.
        """
        self.log.debug('Training Performance: {}'.format(performance))
        return

    def training_episode_end(self, performance: float):
        """Provides the final performance on the training episode and indicates that the training
        episode has ended.

        Parameters
        ----------
        performance : float
            The final normalized performance score of the episode.
        """
        self.log.info('Training Episode End: performance={}'.format(performance))
        return

    def training_end(self):
        """This function is called when we have completed the training episodes.
        """
        self.log.info('Training End')
        return

    def train_model(self):
        """Train your model here if needed.  If you don't need to train, just leave the function
        empty.  After this completes, the logic calls save_model() and reset_model() as needed
        throughout the rest of the experiment.
        """
        self.log.info('Train the model here if needed.')

        # Simulate training the model by sleeping.
        self.log.info('Simulating training with a 5 second sleep.')
        time.sleep(5)

        return

    def save_model(self, filename: str):
        """Saves the current model in memory to disk so it may be loaded back to memory again.

        Parameters
        ----------
        filename : str
            The filename to save the model to.
        """
        self.log.info('Save model to disk.')
        return

    def reset_model(self, filename: str):
        """Loads the model from disk to memory.

        Parameters
        ----------
        filename : str
            The filename where the model was stored.
        """
        self.log.info('Load model from disk.')
        return

    def novelty_start(self):
        """This indicates the start of a series of trials at a novelty level/difficulty.
        """
        self.log.info('Novelty Space Start')
        return

    def testing_start(self):
        """This is called before the trials in the novelty level/difficulty.
        """
        self.log.info('Testing Start')
        return

    def trial_start(self, trial_number: int):
        """This is called at the start of a trial with the current 0-based number.

        Parameters
        ----------
        trial_number : int
            This is the 0-based trial number in the novelty group.
        """
        self.log.info('Trial Start: #{}'.format(trial_number))
        return

    def testing_episode_start(self, episode_number: int):
        """This is called at the start of each testing episode in a trial, you are provided the
        0-based episode number.

        Parameters
        ----------
        episode_number : int
            This is the 0-based episode number in the current trial.
        """
        self.log.info('Testing Episode Start: #{}'.format(episode_number))
        return

    def testing_instance(self, feature_vector: dict, novelty_indicator: bool = None) -> \
            (dict, bool, int):
        """Evaluate a testing instance.  Returns the predicted label or action, if you believe
        this episode is novel, and what novelty level you beleive it to be.

        Parameters
        ----------
        feature_vector : dict
            The dictionary containing the feature vector.  Domain specific feature vectors are
            defined on the github (https://github.com/holderlb/WSU-SAILON-NG).
        novelty_indicator : bool, optional
            An indicator about the "big red button".
                - True == novelty has been introduced.
                - False == novelty has not been introduced.
                - None == no information about novelty is being provided.

        Returns
        -------
        dict, bool, int
            A dictionary of your label prediction of the format {'action': label}.  This is
                strictly enforced and the incorrect format will result in an exception being thrown.
            A boolean as to whether agent detects novelty.
            Integer representing the predicted novelty level.
        """
        self.log.debug('Testing Instance: feature_vector={}, novelty_indicator={}'.format(
            feature_vector, novelty_indicator))

        # Return dummy random choices, but should be determined by trained model
        label_prediction = random.choice(self.possible_answers)
        novelty_detected = random.choice([True, False])
        novelty = random.choice(list(range(4)))

        return label_prediction, novelty_detected, novelty

    def testing_performance(self, performance: float):
        """Provides the current performance on training after each instance.

        Parameters
        ----------
        performance : float
            The normalized performance score.
        """
        return

    def testing_episode_end(self, performance: float):
        """Provides the final performance on the testing episode.

        Parameters
        ----------
        performance : float
            The final normalized performance score of the episode.
        """
        self.log.info('Testing Episode End: performance={}'.format(performance))
        return

    def trial_end(self):
        """This is called at the end of each trial.
        """
        self.log.info('Trial End')
        return

    def testing_end(self):
        """This is called after the trials in a novelty level/difficulty are completed.
        """
        self.log.info('Testing End')
        return

    def novelty_end(self):
        """This is called when we are done with a novelty level/difficulty.
        """
        self.log.info('Novelty Space End')
        return

    def experiment_end(self):
        """This is called when the experiment is done.
        """
        self.log.info('Experiment End')
        return


if __name__ == "__main__":
    parser = optparse.OptionParser(usage="usage: %prog [options]")
    parser.add_option("--config",
                      dest="config",
                      help="Custom ClientAgent config file.",
                      default="TA2.config")
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

    agent = TA2Agent(options)
    agent.run()
