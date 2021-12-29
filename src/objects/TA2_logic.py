#!/usr/bin/env python3
# ************************************************************************************************ #
# **                                                                                            ** #
# **    AIQ-SAIL-ON TA2 Client Core Logic                                                       ** #
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
import os.path
import psutil
import pytz
import queue
import random
import sys
import threading
import time
import uuid
import zlib
import blosc
import numpy

from base64 import b64decode
from . import rabbitmq
from . import objects


class TA2Logic(object):
    def __init__(self):
        options = self._get_command_line_options()
        config_file = options.config
        printout = options.printout
        debug = options.debug
        fulldebug = options.fulldebug
        logfile = options.logfile
        no_testing = options.no_testing
        just_one_trial = options.just_one_trial
        ignore_secret = options.ignore_secret
        self._agent_name = "TA2"

        # First check that the config file exists.
        if len(config_file) == 0:
            raise ValueError('Config filename can not be an empty string.')

        valid_config_file = False
        if os.path.exists(config_file):
            if os.path.isfile(config_file):
                valid_config_file = True

        if not valid_config_file:
            raise ValueError('Provided config filename does not exist. {}'.format(config_file))

        # If logfile was provided, check that the location to save the file exists.
        if logfile is not None:
            head, tail = os.path.split(logfile)
            valid_log_file = False
            if len(head) > 0:
                if os.path.exists(head) and os.path.isdir(head):
                    valid_log_file = True
                else:
                    raise ValueError('Path to save logfile does not exist. {}'.format(logfile))

        self._printout = printout
        self._debug = debug

        log_level = logging.WARNING
        # Define a global log object in case we need to set options for fulldebug.
        global_log = logging.getLogger()
        if printout:
            log_level = logging.INFO
        if debug:
            log_level = logging.DEBUG
        if fulldebug:
            global_log.setLevel(log_level)
        # Define a logger for this class that outputs with the name.
        self.log = logging.getLogger(__name__).getChild(self._agent_name)
        self.log.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if logfile is not None:
            fh = logging.handlers.TimedRotatingFileHandler(logfile,
                                                           when='midnight',
                                                           backupCount=30)
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            # Only set the handler for one of the two, otherwise you will see output doubled for
            # every message you log.
            if fulldebug:
                global_log.addHandler(fh)
            else:
                self.log.addHandler(fh)
        if printout:
            ch = logging.StreamHandler()
            ch.setLevel(log_level)
            ch.setFormatter(formatter)
            # Only set the handler for one of the two, otherwise you will see output doubled for
            # every message you log.
            if fulldebug:
                global_log.addHandler(ch)
            else:
                self.log.addHandler(ch)

        self._config_file = str(config_file)
        self._config = self._build_config_parser()
        self._config.read(self._config_file)

        self._amqp_user = self._config.get("amqp", "user")
        self._amqp_pass = self._config.get("amqp", "pass")
        self._amqp_host = self._config.get("amqp", "host")
        self._amqp_vhost = self._config.get("amqp", "vhost")
        self._amqp_port = self._config.getint("amqp", "port")
        self._amqp_ssl = self._config.getboolean("amqp", "ssl")

        self._description = None
        self._seed = None
        self._sail_on_domain = None
        self._novelty = None
        self._experiment_secret = None
        self._no_testing = False
        self._just_one_trial = False
        self._episode_seed = None
        self._start_zeroed_out = False
        self._start_world_state = None

        self._experiment_type = self._config.get('aiq-sail-on', 'experiment_type')
        if self._experiment_type not in objects.VALID_EXPERIMENT_TYPES:
            raise objects.AiqDataException('Invalid experiment type provided in config: {}'.format(
                self._experiment_type))
        if not self._config.has_option('aiq-sail-on', 'model_name'):
            raise objects.AiqDataException('Missing configfile entry for [aiq-sail-on].model_name.')
        self._model_name = self._config.get('aiq-sail-on', 'model_name')
        if not self._config.has_option('aiq-sail-on', 'organization'):
            raise objects.AiqDataException('Missing configfile entry for [aiq-sail-on].'
                                           'organization.')
        self._organization = self._config.get('aiq-sail-on', 'organization')
        if self._config.has_option('aiq-sail-on', 'description'):
            self._description = self._config.get('aiq-sail-on', 'description')
        self._aiq_username = self._config.get('aiq-sail-on', 'username')
        self._aiq_secret = self._config.get('aiq-sail-on', 'secret')
        if self._config.has_option('aiq-sail-on', 'seed'):
            self._seed = self._config.getint('aiq-sail-on', 'seed')
        if self._config.has_option('aiq-sail-on', 'episode_seed'):
            self._episode_seed = self._config.getint('aiq-sail-on', 'episode_seed')
        if self._config.has_option('aiq-sail-on', 'start_zeroed_out'):
            self._start_zeroed_out = self._config.getboolean('aiq-sail-on', 'start_zeroed_out')
        if self._config.has_option('aiq-sail-on', 'start_world_state'):
            self._start_world_state = self._config.get('aiq-sail-on', 'start_world_state')
            self._start_world_state = json.loads(self.start_world_state)

        self._sail_on_domain = self._config.get('sail-on', 'domain')
        if self._sail_on_domain not in objects.VALID_DOMAINS:
            raise objects.AiqDataException('Invalid domain provided in config: {}'.format(
                self._sail_on_domain))

        # Attempt to load things from the config file if they are there.
        if self._config.has_option('sail-on', 'experiment_secret'):
            self._experiment_secret = self._config.get('sail-on', 'experiment_secret')
        if self._config.has_option('sail-on', 'no_testing'):
            self._no_testing = self._config.getboolean('sail-on', 'no_testing')
        if self._config.has_option('sail-on', 'just_one_trial'):
            self._just_one_trial = self._config.getboolean('sail-on', 'just_one_trial')

        # Let any command line args overwrite settings from config file if needed.
        if no_testing:
            self._no_testing = no_testing
        if just_one_trial:
            self._just_one_trial = just_one_trial
        if ignore_secret:
            self._experiment_secret = None

        # Apply logic.
        if self._no_testing:
            self._just_one_trial = False

        if self._just_one_trial and self._experiment_secret is None:
            raise objects.AiqDataException('You cannot request just one trial of work without '
                                           'providing the experiment_secret in the config.')

        self._amqp = rabbitmq.Connection(agent_name=self._agent_name,
                                         amqp_user=self._amqp_user,
                                         amqp_pass=self._amqp_pass,
                                         amqp_host=self._amqp_host,
                                         amqp_port=self._amqp_port,
                                         amqp_vhost=self._amqp_vhost,
                                         amqp_ssl=self._amqp_ssl)

        self._model_filename_pat = 'model/model.TA2.{}.{}.file'.format(self._sail_on_domain, '{}')
        self._model_filename = None
        self.end_training_early = False
        self.end_experiment_early = False
        return

    def _get_command_line_options(self):
        parser = optparse.OptionParser(usage="usage: %prog [options]")
        parser = self._add_command_line_options(parser)
        parser = self._add_ta2_command_line_options(parser)

        (options, args) = parser.parse_args()
        if options.fulldebug:
            options.debug = True
        return options

    @staticmethod
    def _add_command_line_options(parser):
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
        parser.add_option("--no-testing",
                          dest="no_testing",
                          action="store_true",
                          help=(
                              'Instruct the TA2 to just create the experiment, update the config, '
                              'consume training data (if any), train the model (if needed), saves '
                              'the model to disk, and then exits. This disables the use of '
                              '--just-one-trial when set.'),
                          default=False)
        parser.add_option("--just-one-trial",
                          dest="just_one_trial",
                          action="store_true",
                          help="Process just one trial and then exit.",
                          default=False)
        parser.add_option("--ignore-secret",
                          dest="ignore_secret",
                          action="store_true",
                          help=('Causes the program to ignore any secret stored in experiment_'
                                'secret.'),
                          default=False)
        return parser

    def _add_ta2_command_line_options(self, parser):
        return parser

    def _set_model_filename(self):
        self._model_filename = self._model_filename_pat.format(self._experiment_secret)
        return

    @staticmethod
    def _build_config_parser():
        config = configparser.ConfigParser()
        # Base section for both experiment types.
        config.add_section('aiq-sail-on')
        config.set('aiq-sail-on', 'experiment_type', objects.TYPE_EXPERIMENT_SAIL_ON)
        # config.set('aiq-sail-on', 'model_name', 'model_name')
        # config.set('aiq-sail-on', 'organization', 'organization')
        config.set('aiq-sail-on', 'username', 'username')
        config.set('aiq-sail-on', 'secret', 'secret')
        # Details for SAIL-ON experiments.
        config.add_section('sail-on')
        config.set('sail-on', 'domain', 'domain')
        # The RabbitMQ authentication information.
        config.add_section('amqp')
        config.set("amqp", "user", "username")
        config.set("amqp", "pass", "password")
        config.set("amqp", "host", "hostname")
        config.set("amqp", "vhost", "/")
        config.set("amqp", "port", "5671")
        config.set("amqp", "ssl", "True")
        return config

    def _write_config_file(self):
        if self._experiment_secret is not None:
            self._config.set('sail-on', 'experiment_secret', self._experiment_secret)

        with open(self._config_file, 'w') as configfile:
            self._config.write(configfile)
        return

    @staticmethod
    def _get_benchmark_data() -> dict:
        # Get number of physical CPUs
        num_physical_cpu = psutil.cpu_count(logical=False)
        # Get number of logical CPUs
        num_logical_cpu = psutil.cpu_count(logical=True)
        # Get CPU max speed in MHz
        cpu_max_speed = psutil.cpu_freq().max
        # Get total physical RAM in bytes
        physical_ram = psutil.virtual_memory().total
        result = dict({'num_physical_cpu': num_physical_cpu,
                       'num_logical_cpu': num_logical_cpu,
                       'cpu_max_speed': cpu_max_speed,
                       'physical_ram': physical_ram})
        return result

    def _run_sail_on_trial(self):
        # We already called the trial start function with the trial number.

        # Reset the model to the saved state.
        self.reset_model(filename=self._model_filename)

        # Expect to receive TestingStart.
        my_state = self._amqp.get_state()
        # self.log.info(str(my_state))
        if isinstance(my_state, objects.TestingStart):
            # We have receive an objects.TestingStart.
            self.testing_start()

            # Get the next state, should be Testing Episode Start.
            my_state = self._amqp.get_state()
            # self.log.info(str(my_state))

            # Iterate over episodes.
            while isinstance(my_state, objects.TestingEpisodeStart):
                # We just received an objects.TestingEpisodeStart.
                self.testing_episode_start(episode_number=my_state.episode_number)

                # Collect testing data until we get TestingEpisodeEnd.
                while not isinstance(my_state, objects.TestingEpisodeEnd):
                    # Get testing data.
                    test_data = self._amqp.get_testing_data()

                    # Decompress the image if there is one.
                    if 'image' in test_data.feature_vector:
                        if test_data.feature_vector['image'] is not None:
                            comp_image = b64decode(test_data.feature_vector['image'])
                            test_data.feature_vector['image'] \
                                = blosc.unpack_array(comp_image)

                    # Evaluate the testing data.
                    label_prediction = \
                        self.testing_instance(feature_vector=test_data.feature_vector,
                                              novelty_indicator=test_data.novelty_indicator)

                    # Send the prediction and update my_state, expecting TestingDataAck until
                    # the training episode is over.
                    my_state = self._amqp.send_testing_predictions(
                        label_prediction=label_prediction,
                        end_early=self.end_experiment_early)
                    if isinstance(my_state, objects.TestingDataAck):
                        self.testing_performance(performance=my_state.performance,
                                                 feedback=my_state.feedback)

                # We are done with the training episode.
                if isinstance(my_state, objects.TestingEpisodeEnd):
                    novelty_probability, novelty_threshold, novelty, novelty_characterization = \
                        self.testing_episode_end(performance=my_state.performance,
                                                 feedback=my_state.feedback)
                    my_state = self._amqp.send_testing_episode_novelty(
                        novelty_characterization=novelty_characterization,
                        novelty_probability=novelty_probability,
                        novelty_threshold=novelty_threshold,
                        novelty=novelty)

                self.log.debug(str(my_state))

                # Find out if we have another episode or if the trial is over.
                my_state = self._amqp.get_state()
                # self.log.info(str(my_state))

        if isinstance(my_state, objects.TestingEnd):
            # We have received an objects.TestingEnd.
            self.testing_end()

            # Next we should receive an objects.TrialEnd.
            while not isinstance(my_state, objects.TrialEnd):
                my_state = self._amqp.get_state()
                # self.log.info(str(my_state))

        # We have received an objects.TrialEnd.
        self.trial_end()
        return

    def _run_sail_on_experiment(self):
        my_state = self._amqp.get_state()
        if isinstance(my_state, objects.BenchmarkRequest):
            # self.log.info(str(my_state))
            benchmark_data = self._get_benchmark_data()
            my_state = self._amqp.send_benchmark_data(benchmark_data=benchmark_data)
            # self.log.info(str(my_state))

        # Wait until we are ready to start experiment.
        while not isinstance(my_state, objects.ExperimentStart):
            my_state = self._amqp.get_state()
            # self.log.info(str(my_state))

        # We have received objects.ExperimentStart.
        self.experiment_start()

        # Experiment has started, now look for TrainingStart.
        while not isinstance(my_state, objects.TrainingStart):
            my_state = self._amqp.get_state()
            # self.log.info(str(my_state))

        # We have received objects.TrainingStart.
        self.training_start()

        my_state = self._amqp.get_state()
        # self.log.info(str(my_state))

        # Iterate over episodes.
        while isinstance(my_state, objects.TrainingEpisodeStart):
            # We have received objects.TrainingEpisodeStart.
            self.training_episode_start(episode_number=my_state.episode_number)

            # Collect training data until we get TrainingEpisodeEnd
            while not isinstance(my_state, objects.TrainingEpisodeEnd):
                # Get training data.
                training_data = self._amqp.get_training_data()

                # Decompress the image if there is one.
                if 'image' in training_data.feature_vector:
                    if training_data.feature_vector['image'] is not None:
                        comp_image = b64decode(training_data.feature_vector['image'])
                        training_data.feature_vector['image'] \
                            = blosc.unpack_array(comp_image)
                # Handle the training data.
                label_prediction = \
                    self.training_instance(feature_vector=training_data.feature_vector,
                                           feature_label=training_data.feature_label)

                # Send the prediction and update my_state, expecting TrainingDataAck until
                # the training episode is over.
                my_state = self._amqp.send_training_predictions(
                    label_prediction=label_prediction,
                    end_early=self.end_training_early)
                if isinstance(my_state, objects.TrainingDataAck):
                    self.training_performance(performance=my_state.performance,
                                              feedback=my_state.feedback)

            if isinstance(my_state, objects.TrainingEpisodeEnd):
                # We have received objects.TrainingEpisodeEnd.
                novelty_probability, novelty_threshold, novelty, novelty_characterization = \
                    self.training_episode_end(performance=my_state.performance,
                                              feedback=my_state.feedback)
                my_state = self._amqp.send_training_episode_novelty(
                    novelty_characterization=novelty_characterization,
                    novelty_probability=novelty_probability,
                    novelty_threshold=novelty_threshold,
                    novelty=novelty)

            self.log.debug(str(my_state))

            # Find out if we are going to start another episode or not.
            my_state = self._amqp.get_state()

        # We must have received objects.TrainingEnd.
        if isinstance(my_state, objects.TrainingEnd):
            self.training_end()

            # Now stop the connection for training.
            self.log.info('Stopping connection to train model if needed.')
            self._amqp.stop()

            # Call the function to train our model
            self.train_model()

            # Save the model to disk.
            self.save_model(filename=self._model_filename)

            self.log.info('Starting the connection back up.')
            self._amqp.run()

            # Expect to get objects.TrainingModelEnd here.
            my_state = self._amqp.get_state()

        self._run_sail_on_testing()
        return

    def _run_jump_to_sail_on_testing(self):
        self.log.debug('_run_jump_to_sail_on_testing()')
        my_state = self._amqp.get_state()
        self.log.debug(str(my_state))
        if isinstance(my_state, objects.BenchmarkRequest):
            # self.log.info(str(my_state))
            benchmark_data = self._get_benchmark_data()
            my_state = self._amqp.send_benchmark_data(benchmark_data=benchmark_data)
            self.log.debug(str(my_state))

        # Wait until we are ready to start experiment.
        while not isinstance(my_state, objects.ExperimentStart):
            my_state = self._amqp.get_state()
            self.log.info(str(my_state))

        # We have received objects.ExperimentStart.
        # Be nice and call experiment_start() before we begin jumping into testing.
        self.experiment_start()

        self._run_sail_on_testing()
        return

    def _run_sail_on_testing(self):
        self.log.debug('_run_sail_on_testing()')
        # Based on which path we took to reach here, the current state must be
        # objects.ExperimentStart or objects.TrainingModelEnd, the next state should be either
        # objects.TrialStart or objects.ExperimentEnd.
        my_state = self._amqp.get_state()
        self.log.info(str(my_state))

        # Iterate over the trials we will run.
        while isinstance(my_state, objects.TrialStart):
            # We just received an objects.TrialStart.
            self.trial_start(trial_number=my_state.trial_number,
                             novelty_description=my_state.novelty_description)

            # Run the trial.
            self._run_sail_on_trial()

            # Check to see if we get another go at this loop or continue.
            # This will either be objects.ExperimentEnd of objects.TrialStart.
            my_state = self._amqp.get_state()
            self.log.info(str(my_state))

        # Get Confirmation of ExperimentEnd.
        while not isinstance(my_state, objects.ExperimentEnd):
            my_state = self._amqp.get_state()
            self.log.info(str(my_state))
        self.experiment_end()

        self._amqp.process_data_events(time_limit=1)
        return

    def _run_sail_on(self):
        try:
            self._amqp.run()

            # Build the model.
            model = objects.Model(model_name=self._model_name,
                                  organization=self._organization,
                                  aiq_username=self._aiq_username,
                                  aiq_secret=self._aiq_secret)

            # Let the user know we are attempting to connect to an available TA1, and we will
            # wait if one is not available yet.
            message = ('Attempting to connect to an available TA1, if all are currently busy '
                       'this will wait in line until one is available.')
            if self._printout:
                self.log.info(message)
            else:
                print(message)

            generator_config = dict({'episode_seed': self._episode_seed,
                                     'start_zeroed_out': self._start_zeroed_out,
                                     'start_world_state': self._start_world_state})
            # Start a SAIL-ON experiment!
            if self._experiment_secret is None or self._no_testing:
                # Based on these variables, we need to start a new experiment.
                my_experiment = self._amqp.start_sail_on_experiment(
                    model=model,
                    domain=self._sail_on_domain,
                    no_testing=self._no_testing,
                    seed=self._seed,
                    description=self._description,
                    generator_config=generator_config)
                self.log.info('experiment is gathering requirements!')
                # self.log.debug(str(my_experiment))
                # Store the experiment_secret locally.
                self._experiment_secret = my_experiment.experiment_secret
                if self._experiment_secret is not None:
                    # Now we can set the model filename.
                    self._set_model_filename()
                    # Set the experiment_secret in the config object.
                    self._config.set('sail-on', 'experiment_secret', self._experiment_secret)
                    # Write out the config with the new experiment_secret value.
                    self._write_config_file()

                    # Run the SAIL-ON experiment!
                    self._run_sail_on_experiment()
            else:
                self._set_model_filename()
                # Here we don't need to start a new experiment, just register to work on 1 or
                # many trials for the given experiment.
                my_experiment = self._amqp.start_work_on_experiment_trials(
                    model=model,
                    experiment_secret=self._experiment_secret,
                    just_one_trial=self._just_one_trial,
                    domain=self._sail_on_domain,
                    generator_config=generator_config)
                if isinstance(my_experiment, objects.CasasResponse):
                    if my_experiment.status == 'error':
                        for casas_error in my_experiment.error_list:
                            self.log.error(casas_error.message)
                            self.log.error(str(casas_error.error_dict))
                else:
                    # We have our response.
                    # Start working on trials until TA1 tells us the experiment is done, or at
                    # least we are done with what we requested.
                    self._run_jump_to_sail_on_testing()

        except KeyboardInterrupt:
            self._stop()
        except objects.AiqExperimentException as e:
            self.log.error(e.value)
            self._stop()
        self._stop()
        return

    def run(self):
        self._run_sail_on()
        return

    def _stop(self):
        self._amqp.stop()
        return

    def process_amqp_events(self):
        self._amqp.process_data_events(time_limit=0.5)
        return

    def experiment_start(self):
        """This function is called when this TA2 has connected to a TA1 and is ready to begin
        the experiment.
        """
        raise ValueError('experiment_start() not defined.')

    def training_start(self):
        """This function is called when we are about to begin training on episodes of data in
        your chosen domain.
        """
        raise ValueError('training_start() not defined.')

    def training_episode_start(self, episode_number: int):
        """This function is called at the start of each training episode, with the current episode
        number (0-based) that you are about to begin.

        Parameters
        ----------
        episode_number : int
            This identifies the 0-based episode number you are about to begin training on.
        """
        raise ValueError('training_episode_start() not defined.')

    def training_instance(self, feature_vector: dict, feature_label: dict) -> dict:
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
        dict
            A dictionary of your label prediction of the format {'action': label}.  This is
                strictly enforced and the incorrect format will result in an exception being thrown.
        """
        raise ValueError('training_instance() not defined.')

    def training_performance(self, performance: float, feedback: dict = None):
        """Provides the current performance on training after each instance.

        Parameters
        ----------
        performance : float
            The normalized performance score.
        feedback : dict, optional
            A dictionary that may provide additional feedback on your prediction based on the
            budget set in the TA1. If there is no feedback, the object will be None.
        """
        raise ValueError('training_performance() not defined.')

    def training_episode_end(self, performance: float, feedback: dict = None) -> \
            (float, float, int, dict):
        """Provides the final performance on the training episode and indicates that the training
        episode has ended.

        Parameters
        ----------
        performance : float
            The final normalized performance score of the episode.
        feedback : dict, optional
            A dictionary that may provide additional feedback on your prediction based on the
            budget set in the TA1. If there is no feedback, the object will be None.

        Returns
        -------
        float, float, int, dict
            A float of the probability of there being novelty.
            A float of the probability threshold for this to evaluate as novelty detected.
            Integer representing the predicted novelty level.
            A JSON-valid dict characterizing the novelty.
        """
        raise ValueError('training_episode_end() not defined.')

    def training_end(self):
        """This function is called when we have completed the training episodes.
        """
        raise ValueError('training_end() not defined.')

    def train_model(self):
        """Train your model here if needed.  If you don't need to train, just leave the function
        empty.  After this completes, the logic calls save_model() and reset_model() as needed
        throughout the rest of the experiment.
        """
        raise ValueError('train_model() not defined.')

    def save_model(self, filename: str):
        """Saves the current model in memory to disk so it may be loaded back to memory again.

        Parameters
        ----------
        filename : str
            The filename to save the model to.
        """
        raise ValueError('save_model() not defined.')

    def reset_model(self, filename: str):
        """Loads the model from disk to memory.

        Parameters
        ----------
        filename : str
            The filename where the model was stored.
        """
        raise ValueError('reset_model() not defined.')

    def trial_start(self, trial_number: int, novelty_description: dict):
        """This is called at the start of a trial with the current 0-based number.

        Parameters
        ----------
        trial_number : int
            This is the 0-based trial number in the novelty group.
        novelty_description : dict
            A dictionary that will have a description of the trial's novelty.
        """
        raise ValueError('trial_start() not defined.')

    def testing_start(self):
        """This is called after a trial has started but before we begin going through the
        episodes.
        """
        raise ValueError('testing_start() not defined.')

    def testing_episode_start(self, episode_number: int):
        """This is called at the start of each testing episode in a trial, you are provided the
        0-based episode number.

        Parameters
        ----------
        episode_number : int
            This is the 0-based episode number in the current trial.
        """
        raise ValueError('testing_episode_start() not defined.')

    def testing_instance(self, feature_vector: dict, novelty_indicator: bool = None) -> dict:
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
        dict
            A dictionary of your label prediction of the format {'action': label}.  This is
                strictly enforced and the incorrect format will result in an exception being thrown.
        """
        raise ValueError('testing_instance() not defined.')

    def testing_performance(self, performance: float, feedback: dict = None):
        """Provides the current performance on training after each instance.

        Parameters
        ----------
        performance : float
            The normalized performance score.
        feedback : dict, optional
            A dictionary that may provide additional feedback on your prediction based on the
            budget set in the TA1. If there is no feedback, the object will be None.
        """
        raise ValueError('testing_performance() not defined.')

    def testing_episode_end(self, performance: float, feedback: dict = None) -> \
            (float, float, int, dict):
        """Provides the final performance on the testing episode.

        Parameters
        ----------
        performance : float
            The final normalized performance score of the episode.
        feedback : dict, optional
            A dictionary that may provide additional feedback on your prediction based on the
            budget set in the TA1. If there is no feedback, the object will be None.

        Returns
        -------
        float, float, int, dict
            A float of the probability of there being novelty.
            A float of the probability threshold for this to evaluate as novelty detected.
            Integer representing the predicted novelty level.
            A JSON-valid dict characterizing the novelty.
        """
        raise ValueError('testing_episode_end() not defined.')

    def testing_end(self):
        """This is called after the last episode of a trial has completed, before trial_end().
        """
        raise ValueError('testing_end() not defined.')

    def trial_end(self):
        """This is called at the end of each trial.
        """
        raise ValueError('trial_end() not defined.')

    def experiment_end(self):
        """This is called when the experiment is done.
        """
        raise ValueError('experiment_end() not defined.')

