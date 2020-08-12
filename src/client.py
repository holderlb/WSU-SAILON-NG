#!/usr/bin/env python3
# ************************************************************************************************ #
# **                                                                                            ** #
# **    AIQ-SAIL-ON Client Agent Example                                                        ** #
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
import psutil
import pytz
import queue
import random
import sys
import threading
import time
import uuid

from objects import rabbitmq
from objects import objects

from TA2Agent import TA2Agent

class ClientAgent(object):
    def __init__(self, options):
        self.agent_name = "ClientAgent"
        self.ta2_agent = TA2Agent()
        log_level = logging.WARNING
        # Define a global log object in case we need to set options for fulldebug.
        global_log = logging.getLogger()
        if options.printout:
            log_level = logging.INFO
        if options.debug:
            log_level = logging.DEBUG
        if options.fulldebug:
            global_log.setLevel(log_level)
        # Define a logger for this class that outputs with the name.
        self.log = logging.getLogger(__name__).getChild(self.agent_name)
        self.log.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if options.logfile is not None:
            fh = logging.handlers.TimedRotatingFileHandler(options.logfile,
                                                           when='midnight',
                                                           backupCount=7)
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            # Only set the handler for one of the two, otherwise you will see output doubled for
            # every message you log.
            if options.fulldebug:
                global_log.addHandler(fh)
            else:
                self.log.addHandler(fh)
        if options.printout:
            ch = logging.StreamHandler()
            ch.setLevel(log_level)
            ch.setFormatter(formatter)
            # Only set the handler for one of the two, otherwise you will see output doubled for
            # every message you log.
            if options.fulldebug:
                global_log.addHandler(ch)
            else:
                self.log.addHandler(ch)

        self.config_file = str(options.config)
        self.config = self.build_config_parser()
        self.config.read(self.config_file)

        self.amqp_user = self.config.get("amqp", "user")
        self.amqp_pass = self.config.get("amqp", "pass")
        self.amqp_host = self.config.get("amqp", "host")
        self.amqp_vhost = self.config.get("amqp", "vhost")
        self.amqp_port = self.config.getint("amqp", "port")
        self.amqp_ssl = self.config.getboolean("amqp", "ssl")

        self.description = None
        self.domains = dict()
        self.sail_on_domain = None
        self.novelty = None

        self.experiment_type = self.config.get('aiq-sail-on', 'experiment_type')
        self.model_name = self.config.get('aiq-sail-on', 'model_name')
        self.organization = self.config.get('aiq-sail-on', 'organization')
        if self.config.has_option('aiq-sail-on', 'description'):
            self.description = self.config.get('aiq-sail-on', 'description')
        self.aiq_username = self.config.get('aiq-sail-on', 'username')
        self.aiq_secret = self.config.get('aiq-sail-on', 'secret')

        for domain in objects.VALID_DOMAINS:
            self.domains[domain] = self.config.getboolean('aiq_domains', domain)

        self.sail_on_domain = self.config.get('sail-on', 'domain')

        self.amqp = rabbitmq.Connection(agent_name=self.agent_name,
                                        amqp_user=self.amqp_user,
                                        amqp_pass=self.amqp_pass,
                                        amqp_host=self.amqp_host,
                                        amqp_port=self.amqp_port,
                                        amqp_vhost=self.amqp_vhost,
                                        amqp_ssl=self.amqp_ssl)
        return

    @staticmethod
    def build_config_parser():
        config = configparser.ConfigParser()
        # Base section for both experiment types.
        config.add_section('aiq-sail-on')
        config.set('aiq-sail-on', 'experiment_type', objects.TYPE_EXPERIMENT_AIQ)
        config.set('aiq-sail-on', 'model_name', 'model_name')
        config.set('aiq-sail-on', 'organization', 'organization')
        config.set('aiq-sail-on', 'username', 'username')
        config.set('aiq-sail-on', 'secret', 'secret')
        # Domains for AIQ experiments.
        config.add_section('aiq_domains')
        for domain in objects.VALID_DOMAINS:
            config.set('aiq_domains', domain, 'False')
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

    def run_sail_on_trial(self):
        self.ta2_agent.trial_start()
        # Expect to receive TestingStart.
        my_state = self.amqp.get_state()
        self.log.info(str(my_state))
        if isinstance(my_state, objects.TestingStart):
            self.ta2_agent.testing_start()
            my_state = self.amqp.get_state()
            self.log.info(str(my_state))
            # Iterate over episodes.
            while isinstance(my_state, objects.TestingEpisodeStart):
                self.ta2_agent.testing_episode_start()
                # Collect testing data until we get TestingEpisodeEnd.
                while not isinstance(my_state, objects.TestingEpisodeEnd):
                    # Get a testing feature vector.
                    test_data = self.amqp.get_testing_data()
                    self.log.debug('Feature Vector:     {}'.format(test_data.feature_vector))
                    self.log.debug('Novelty Indicator:  {}'.format(test_data.novelty_indicator))
                    # Evaluate the instance.
                    label_prediction, novelty_detected, novelty = self.ta2_agent.testing_instance(test_data.feature_vector, test_data.novelty_indicator)
                    my_state = self.amqp.send_testing_predictions(testing_data=test_data,
                                                                  label_prediction=label_prediction,
                                                                  novelty_detected=novelty_detected,
                                                                  novelty=novelty)
                    performance = 0.0
                    if isinstance(my_state, objects.TestingDataAck):
                        # self.log.info(my_state.performance)
                        self.log.debug('Rolling Accuracy:   {}'.format(my_state.performance))
                        performance = my_state.performance
                    else:
                        if isinstance(my_state, objects.TestingEpisodeEnd):
                            self.log.info(str(my_state))
                        else:
                            self.log.error('Was expecting a TestingDataAck or TestingEpisodeEnd '
                                           'here.')
                            self.log.error(str(my_state))
                    self.ta2_agent.testing_performance(performance)
                self.ta2_agent.testing_episode_end()
                my_state = self.amqp.get_state()
                self.log.info(str(my_state))
        if isinstance(my_state, objects.TestingEnd):
            self.ta2_agent.testing_end()
            while not isinstance(my_state, objects.TrialEnd):
                my_state = self.amqp.get_state()
                self.log.info(str(my_state))
        self.ta2_agent.trial_end()
        return

    def run_sail_on(self):
        try:
            self.amqp.run()

            # Build the model.
            model = objects.Model(model_name=self.model_name,
                                  organization=self.organization,
                                  aiq_username=self.aiq_username,
                                  aiq_secret=self.aiq_secret)
            self.log.debug(str(model))

            # Start an AIQ experiment!
            my_experiment = self.amqp.start_sail_on_experiment(model=model, domain=self.sail_on_domain)
            self.log.info('experiment is gathering requirements!')
            self.log.debug(str(my_experiment))

            # Wait for SOTA client to connect.
            my_state = self.amqp.get_state()
            while isinstance(my_state, objects.WaitOnSota):
                self.amqp.sleep(duration=2)
                self.log.info(str(my_state))
                my_state = self.amqp.get_state()

            # Run some benchmarks.
            if isinstance(my_state, objects.BenchmarkRequest):
                self.log.info(str(my_state))
                # For now, get hardware CPU and RAM info
                benchmark_data = self.benchmarks()
                self.log.debug('Benchmarks: {}'.format(benchmark_data))
                my_state = self.amqp.send_benchmark_data(benchmark_data=benchmark_data)
                self.log.info(str(my_state))

            # Wait until we are ready to start experiment.
            while not isinstance(my_state, objects.ExperimentStart):
                my_state = self.amqp.get_state()
                self.log.info(str(my_state))
            self.ta2_agent.experiment_start()

            # Experiment has started, now look for TrainingStart.
            while not isinstance(my_state, objects.TrainingStart):
                my_state = self.amqp.get_state()
                self.log.info(str(my_state))
            self.ta2_agent.training_start()

            my_state = self.amqp.get_state()
            self.log.info(str(my_state))
            # Iterate over episodes.
            while isinstance(my_state, objects.TrainingEpisodeStart):
                # Collect training data until we get TrainingEpisodeEnd
                self.ta2_agent.training_episode_start()
                while not isinstance(my_state, objects.TrainingEpisodeEnd):
                    # Get a training feature vector.
                    training_data = self.amqp.get_training_data()
                    self.log.debug('Feature Vector:   {}'.format(training_data.feature_vector))
                    self.log.debug('Feature Label:    {}'.format(training_data.feature_label))
                    label_prediction, novelty_detected, novelty = self.ta2_agent.training_instance(training_data.feature_vector, training_data.feature_label)
                    my_state = self.amqp.send_training_predictions(
                        training_data=training_data,
                        label_prediction=label_prediction,
                        novelty_detected=novelty_detected,
                        novelty=novelty)
                    performance = 0.0
                    if isinstance(my_state, objects.TrainingDataAck):
                        self.log.debug('Rolling Accuracy: {}'.format(my_state.performance))
                        performance = my_state.performance
                    self.ta2_agent.training_performance(performance)
                self.ta2_agent.training_episode_end()
                self.log.info(str(my_state))
                # Find out if we are going to start another episode or not.
                my_state = self.amqp.get_state()
                if not isinstance(my_state, objects.TrainingEnd):
                    self.log.info(str(my_state))
                    
            self.ta2_agent.training_end()
            if isinstance(my_state, objects.TrainingEnd):
                self.log.info('Stopping connection to "train" model.')
                self.amqp.stop()
                self.log.info('"Training" model...')
                self.ta2_agent.train_model()
                self.log.info('Starting the connection back up.')
                self.amqp.run()
            self.log.info(str(my_state))

            # Must have received TrainingEnd.
            # This should get NoveltyStart.
            my_state = self.amqp.get_state()
            self.log.info(str(my_state))
            while isinstance(my_state, objects.NoveltyStart):
                self.ta2_agent.novelty_start()
                my_state = self.amqp.get_state()
                self.log.info(str(my_state))
                # Iterate over the trials we will run.
                while isinstance(my_state, objects.TrialStart):
                    self.run_sail_on_trial()
                    my_state = self.amqp.get_state()
                    self.log.info(str(my_state))
                # Above loop just received a TrialEnd.
                # Find out if we get another NoveltyStart or NoveltyEnd.
                my_state = self.amqp.get_state()
                self.log.info(str(my_state))
            self.ta2_agent.novelty_end()

            # Get Confirmation of ExperimentEnd
            while not isinstance(my_state, objects.ExperimentEnd):
                my_state = self.amqp.get_state()
                self.log.info(str(my_state))
            self.ta2_agent.experiment_end()
            
            self.amqp.process_data_events(time_limit=1)
        except KeyboardInterrupt:
            self.stop()
        except objects.AiqExperimentException as e:
            self.log.error(e.value)
            self.stop()
        return
    
    def benchmarks(self):
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

    def run(self):
        self.run_sail_on()
        return

    def stop(self):
        self.amqp.stop()
        return


if __name__ == "__main__":
    parser = optparse.OptionParser(usage="usage: %prog [options]")
    parser.add_option("--config",
                      dest="config",
                      help="Custom ClientAgent config file.",
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

    agent = ClientAgent(options)
    agent.run()
    agent.stop()
