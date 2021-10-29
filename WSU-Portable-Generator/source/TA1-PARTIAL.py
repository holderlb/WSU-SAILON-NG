#!/usr/bin/env python3
# ************************************************************************************************ #
# **                                                                                            ** #
# **    AIQ-SAIL-ON Server Agent                                                                ** #
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
import cProfile
import datetime
import copy
import json
import logging
import logging.handlers
import optparse
import pika
import psycopg2
import pytz
import queue
import random
import socket
import sys
import threading
import time
import uuid
from psycopg2.extras import Json

from objects import rabbitmq
from objects import objects


class LiveGeneratorThread(threading.Thread):
    def __init__(self, log: logging.Logger, amqp_user: str, amqp_pass: str, amqp_host: str,
                 amqp_port: str, amqp_vhost: str, amqp_ssl: bool, ta2_response_queue: queue.Queue,
                 live_output_queue: queue.Queue, domain: str, novelty: int, difficulty: str,
                 seed: int, trial_novelty: int, day_offset: int, request_timeout: int,
                 use_image: bool):
        threading.Thread.__init__(self)
        self.name = 'LiveGeneratorThread'
        self.log = log.getChild(self.name)
        self.amqp_user = amqp_user
        self.amqp_pass = amqp_pass
        self.amqp_host = amqp_host
        self.amqp_port = amqp_port
        self.amqp_vhost = amqp_vhost
        self.amqp_ssl = amqp_ssl
        self.request_timeout = abs(request_timeout - 5)
        self.ta2_response_queue = ta2_response_queue
        self.live_output_queue = live_output_queue
        self.domain = domain
        self.novelty = novelty
        self.difficulty = difficulty
        self.seed = seed
        self.trial_novelty = trial_novelty
        self.day_offset = day_offset
        self.use_image = use_image
        self.done = False

        if self.domain not in objects.VALID_DOMAINS:
            raise objects.AiqDataException(value='INVALID DOMAIN!')

        self.amqp = rabbitmq.Connection(agent_name=self.name,
                                        amqp_user=self.amqp_user,
                                        amqp_pass=self.amqp_pass,
                                        amqp_host=self.amqp_host,
                                        amqp_port=self.amqp_port,
                                        amqp_vhost=self.amqp_vhost,
                                        amqp_ssl=self.amqp_ssl,
                                        request_timeout=self.request_timeout)
        self.log.debug('Initialized')
        return

    def run(self):
        self.log.debug('run()')
        # Start the connection.
        self.amqp.run()

        # Establish connection to a generator.
        self.amqp.start_generator(domain=self.domain,
                                  novelty=self.novelty,
                                  difficulty=self.difficulty,
                                  seed=self.seed,
                                  trial_novelty=self.trial_novelty,
                                  day_offset=self.day_offset,
                                  request_timeout=self.request_timeout,
                                  use_image=self.use_image)

        # Begin our loop.
        while not self.done:
            try:
                # Try getting a message to send.
                message = self.ta2_response_queue.get(block=True, timeout=0.2)
                self.log.debug('message: {}'.format(str(message)))

                response = None
                try:
                    # If we have a message, we can send it to the generator.
                    response = self.amqp.send_generator_data(data_request=message)
                    self.log.debug('response: {}'.format(str(response)))
                except objects.AiqExperimentException:
                    self.log.warning('Generator took too long to respond.')
                    response = objects.ExperimentException(
                        message=('The generator took more than {} seconds to respond.  '
                                 'Please restart your experiment.'.format(self.request_timeout)))

                # Put the response in the outgoing queue.
                self.live_output_queue.put(response)

            except queue.Empty:
                # If the queue was empty then let amqp do a little work before trying again.
                self.amqp.process_data_events()

        # Stop the connection as we exit.
        self.amqp.stop()
        self.log.debug('exiting')
        return

    def stop(self):
        self.log.debug('stop()')
        self.done = True
        return


class NoveltyDescriptionThread(threading.Thread):
    def __init__(self, log: logging.Logger, amqp_user: str, amqp_pass: str, amqp_host: str,
                 amqp_port: str, amqp_vhost: str, amqp_ssl: bool, response_queue: queue.Queue,
                 domain: str, novelty: int, difficulty: str, request_timeout: int):
        threading.Thread.__init__(self)
        self.name = 'LiveGeneratorThread'
        self.log = log.getChild(self.name)
        self.amqp_user = amqp_user
        self.amqp_pass = amqp_pass
        self.amqp_host = amqp_host
        self.amqp_port = amqp_port
        self.amqp_vhost = amqp_vhost
        self.amqp_ssl = amqp_ssl
        self.request_timeout = abs(request_timeout - 5)
        self.response_queue = response_queue
        self.domain = domain
        self.novelty = novelty
        self.difficulty = difficulty

        if self.domain not in objects.VALID_DOMAINS:
            raise objects.AiqDataException(value='INVALID DOMAIN!')

        self.amqp = rabbitmq.Connection(agent_name=self.name,
                                        amqp_user=self.amqp_user,
                                        amqp_pass=self.amqp_pass,
                                        amqp_host=self.amqp_host,
                                        amqp_port=self.amqp_port,
                                        amqp_vhost=self.amqp_vhost,
                                        amqp_ssl=self.amqp_ssl,
                                        request_timeout=self.request_timeout)
        self.log.debug('Initialized')
        return

    def run(self):
        self.log.debug('run()')
        # Start the connection.
        self.amqp.run()

        # Make the novelty description request.
        novelty_description = self.amqp.get_novelty_description(domain=self.domain,
                                                                novelty=self.novelty,
                                                                difficulty=self.difficulty)
        self.response_queue.put(novelty_description)

        # Stop the connection as we exit.
        self.amqp.stop()
        self.log.debug('exiting')
        return

    def stop(self):
        self.log.debug('stop()')
        return


class LogMessage:
    def __init__(self, model_experiment_id: int, action: str, message: str = None,
                 data_object: dict = None, experiment_trial_id: int = None):
        self.model_experiment_id = model_experiment_id
        self.experiment_trial_id = experiment_trial_id
        self.action = action
        self.message = message
        self.data_object = copy.deepcopy(data_object)
        return


class TA1:
    def __init__(self, options):
        # The very first thing we must do is identify what options from command line versus
        # config file we will be using, then override any of the values that are not the default
        # value from the options object.
        config = self.build_config_parser()
        config.read(str(options.config))

        # Option -> debug
        opt_debug = config.getboolean('options', 'debug')
        if options.debug != objects.DEFAULT_TA1_DEBUG:
            opt_debug = options.debug

        # Option -> fulldebug
        opt_fulldebug = config.getboolean('options', 'fulldebug')
        if options.fulldebug != objects.DEFAULT_TA1_FULLDEBUG:
            opt_fulldebug = options.fulldebug

        # Option -> printout
        opt_printout = config.getboolean('options', 'printout')
        if options.printout != objects.DEFAULT_TA1_PRINTOUT:
            opt_printout = options.printout

        # Option -> logfile
        opt_logfile = objects.DEFAULT_TA1_LOGFILE
        if options.logfile is not None:
            opt_logfile = options.logfile
        elif config.has_option(section='options', option='logfile'):
            opt_logfile = config.get('options', 'logfile')

        # Option -> testing
        opt_testing = config.getboolean('options', 'testing')
        if options.testing != objects.DEFAULT_TA1_TESTING:
            opt_testing = options.testing

        # Option -> demo
        opt_demo = config.getboolean('options', 'demo')
        if options.demo != objects.DEFAULT_TA1_DEMO:
            opt_demo = options.demo

        # Option -> shortdemo
        opt_shortdemo = config.getboolean('options', 'shortdemo')
        if options.shortdemo != objects.DEFAULT_TA1_SHORTDEMO:
            opt_shortdemo = options.shortdemo

        self.name = "TA1"
        # Log levels used for logging to the database.
        log_level = logging.WARNING
        # Define a global log object in case we need to set options for full debug.
        global_log = logging.getLogger()
        if opt_printout:
            log_level = logging.INFO
        if opt_debug:
            log_level = logging.DEBUG
        if opt_fulldebug:
            global_log.setLevel(log_level)
        # Define a logger for this class that outputs with the name.
        self.log = logging.getLogger().getChild(self.name)
        self.log.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if opt_logfile is not None:
            fh = logging.handlers.TimedRotatingFileHandler(opt_logfile,
                                                           when='midnight',
                                                           backupCount=14)
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            # Only set the handler for one of the two, otherwise you will see output doubled for
            # every message you log.
            if opt_fulldebug:
                global_log.addHandler(fh)
            else:
                self.log.addHandler(fh)
        if opt_printout:
            ch = logging.StreamHandler()
            ch.setLevel(log_level)
            ch.setFormatter(formatter)
            # Only set the handler for one of the two, otherwise you will see output doubled for
            # every message you log.
            if opt_fulldebug:
                global_log.addHandler(ch)
            else:
                self.log.addHandler(ch)

        self.is_shortdemo = opt_shortdemo
        self.is_testing = opt_testing
        self.is_demo = opt_demo
        if self.is_shortdemo:
            self.is_demo = True
        if self.is_demo:
            self.is_testing = True

        self.is_profiling = False

        # for section in config.sections():
        #     for key in config[section]:
        #         self.log.warning('{}.{} = {}'.format(section, key, config[section][key]))

        self.db_user = config.get("postgresql", "user")
        self.db_pass = config.get("postgresql", "pass")
        self.db_host = config.get("postgresql", "host")
        self.db_port = config.get("postgresql", "port")
        self.db_name = objects.DATABASE_PATTERN.format(config.get('postgresql', 'database'))
        self.log.warning('database: {}'.format(self.db_name))
        self.db_conn = None
        self.amqp_user = config.get("amqp", "user")
        self.amqp_pass = config.get("amqp", "pass")
        self.amqp_host = config.get("amqp", "host")
        self.amqp_vhost = config.get("amqp", "vhost")
        self.amqp_port = config.getint("amqp", "port")
        self.amqp_ssl = config.getboolean("amqp", "ssl")
        self._AMQP_EXPERIMENT_TIMEOUT = config.getint('sail-on', 'normal_timeout_seconds')
        self._AMQP_EXPERIMENT_TIMEOUT -= 5
        if self.is_testing and not self.is_demo:
            self._AMQP_EXPERIMENT_TIMEOUT = 60
        self._TIMEOUT_MULTIPLIER = config.getint('sail-on', 'training_timeout_multiplier')
        self._AMQP_EXP_CALLBACK_ID = None
        self._AMQP_SOTA_CALLBACK_ID = None
        self._sota_username = config.get('sota', 'username')
        self._sota_secret = config.get('sota', 'secret')
        self._training_novelty_p1 = config.getfloat('sail-on', 'training_novelty_p1')
        self._testing_novelty_p2 = config.getfloat('sail-on', 'testing_novelty_p2')
        self._training_episodes = 0
        self._testing_episodes = 0
        self._server_novelty = list()
        server_novelty = config.get('sail-on', 'novelty')
        split_novelty = str(server_novelty).split(',')
        for novelty in split_novelty:
            if int(novelty) in objects.VALID_NOVELTY:
                self._server_novelty.append(int(novelty))
        self._server_trials = config.getint('sail-on', 'trials')
        if self.is_demo:
            self._server_novelty = list([objects.NOVELTY_200])
        self._server_novelty_index = 0
        self._sota_server_novelty_index = 0
        self._server_difficulty = list()
        server_difficulty = config.get('sail-on', 'difficulty')
        split_difficulty = str(server_difficulty).split(',')
        for difficulty in split_difficulty:
            if difficulty in objects.VALID_DIFFICULTY:
                self._server_difficulty.append(difficulty)
        self._random_sleep_seconds = 0
        if config.has_option(section='sail-on', option='random_sleep_seconds'):
            random_sleep = config.getint('sail-on', 'random_sleep_seconds')
            self._random_sleep_seconds = random.randint(0, random_sleep)
        self._ep_by_domain = dict()
        self._budget_by_domain = dict()
        self._image_by_domain = dict()
        self._is_domain_live = dict()
        self._domain_data_source = dict()
        for domain in objects.VALID_DOMAINS:
            self._ep_by_domain[domain] = dict({'train': 10, 'test': 10, 'pre-novel': None})
            self._budget_by_domain[domain] = -0.1
            self._image_by_domain[domain] = False
            self._is_domain_live[domain] = False
            self._domain_data_source[domain] = objects.SOURCE_RECORDED
            if config.has_section(section=domain):
                if config.has_option(section=domain, option='training_episodes'):
                    self._ep_by_domain[domain]['train'] = config.getint(section=domain,
                                                                        option='training_episodes')
                if config.has_option(section=domain, option='testing_episodes'):
                    self._ep_by_domain[domain]['test'] = config.getint(section=domain,
                                                                       option='testing_episodes')
                if config.has_option(section=domain, option='pre_novel_episodes'):
                    self._ep_by_domain[domain]['pre-novel'] = config.getint(
                        section=domain,
                        option='pre_novel_episodes')
                    # The pre-novel count must be lower than the number of test episodes.
                    if self._ep_by_domain[domain]['pre-novel'] \
                            >= self._ep_by_domain[domain]['test']:
                        self._ep_by_domain[domain]['pre-novel'] \
                            = int(self._ep_by_domain[domain]['test'] / 2)
                # Hard coded for release
                self._is_domain_live[domain] = True
                if self._is_domain_live[domain]:
                    self._domain_data_source[domain] = objects.SOURCE_LIVE
                if config.has_option(section=domain, option='budget'):
                    self._budget_by_domain[domain] = config.getfloat(section=domain,
                                                                     option='budget')
                if config.has_option(section=domain, option='use_image'):
                    self._image_by_domain[domain] = config.getboolean(section=domain,
                                                                      option='use_image')
            if self.is_testing:
                self._ep_by_domain[domain] = dict({'train': 3, 'test': 3})

        self.sota_client_ex_req = None
        self.sota_client_ex_response = None
        self.private_queue = None
        # [dataset_id][episode_index] = dict( episode_id, data_index )
        self.episode_cache = dict()
        # [episode_id] = episode_index
        self.episode_index_cache = dict()
        # [domain_id][data_type][novelty][difficulty][trial_novelty] = dict(various dataset things)
        self.dataset_cache = dict()
        # [episode_id][data_index] = dict( data stuff )
        self.data_cache = dict()
        self.domain_cache = list()
        self.domain_ids = dict()
        self.domain_names = dict()
        self.episode_id_list = list()
        self.episode_id_list_index = None
        self.current_domain = None
        self.user_id = None
        self.model_experiment_id = None
        self.novelty_initiated = False
        self.novelty_visibility = 0
        self.rolling_score = list()
        self.experiment_type = None
        self.experiment_trial_id = None
        self.experiment_trial = None
        self.trial_episode_id = None
        self.trial_episode_performance = None
        self.trial_predicted_novelty = False
        self.trial_budget_active = False
        self.novelty_level = None
        self.novelty_vis_index = None
        self.STATE = None
        self.SOTA_STATE = None
        self.hold_during_training_gap = False
        self.refresh_dataset_cache = False
        self.episode_data_count = 0
        self.episode_data_total = 0
        self.benchmark_data = None

        self._SHORT_DEMO_EPISODE_SIZE = 200
        self._TESTING_DATA_SIZE = 100
        self._SAIL_ON_TRIALS = self._server_trials
        if self.is_testing:
            self._SAIL_ON_TRIALS = 3
        if self.is_demo:
            self._SAIL_ON_TRIALS = 1
        self._ROLLING_SCORE_SIZE = 10
        self._DOMAIN_HOP = 10
        self._NOVEL_HOP_PROB = 0.5
        self._NOVEL_HOP_CHECK = 1
        self._TEST_NUM_N_ZERO = 0
        self._TEST_NUM_N_L = 0
        self._TEST_EPISODE_BEFORE_NOVEL = random.randint(0, int(self._testing_episodes / 2))
        self._TEST_EPISODE_PROGRESS = 0
        self._TEST_WINDOW_BEFORE_NOVEL = random.randint(200, 4000)
        self._TEST_WINDOW_PROGRESS = 0
        self._DATA_CACHE_SIZE = 100
        self._DATA_CACHE_RELOAD = 2
        self._VALID_DATA_TYPES = list(['train', 'test'])
        self._TorN = 0
        self._TorN_OPTIONS = list([0, 0])
        self._SAIL_ON_VISIBILITY = list([0, 1])
        self._live_thread = None
        self._ta2_response = queue.Queue()
        self._live_output = queue.Queue()
        self._experiment = None
        self._exper_train_index = None
        self._exper_novelty_index = None
        self._exper_trial_index = None
        self._exper_episode_index = None
        self._exper_trial_novelty_desc = None
        self._exper_end_training_early = False
        self._exper_end_experiment_early = False
        self._exper_no_testing = False
        self._exper_no_training = False
        self._exper_just_one_trial = False

        self.amqp = rabbitmq.Connection(agent_name=self.name,
                                        amqp_user=self.amqp_user,
                                        amqp_pass=self.amqp_pass,
                                        amqp_host=self.amqp_host,
                                        amqp_port=self.amqp_port,
                                        amqp_vhost=self.amqp_vhost,
                                        amqp_ssl=self.amqp_ssl,
                                        request_timeout=self._AMQP_EXPERIMENT_TIMEOUT)

        self.subscribe_experiment_queue()
        self.subscribe_sota_queue()
        self.setup_publish_analysis_queue()

        self.connect_db()
        self.reconnect_db()
        random.seed(time.time())
        return

    @staticmethod
    def build_config_parser():
        config = configparser.ConfigParser()
        config.add_section("postgresql")
        config.set("postgresql", "user", "username")
        config.set("postgresql", "pass", "password")
        config.set("postgresql", "host", "hostname")
        config.set("postgresql", "port", "port")
        config.set("postgresql", "database", "database")
        config.add_section("amqp")
        config.set("amqp", "user", "username")
        config.set("amqp", "pass", "password")
        config.set("amqp", "host", "hostname")
        config.set("amqp", "vhost", "/")
        config.set("amqp", "port", "5671")
        config.set("amqp", "ssl", "True")
        # For SOTA, we will only accept a connection that can provide a pre-shared
        # username and secret, defined in the config file.
        config.add_section('sota')
        config.set('sota', 'username', 'username')
        config.set('sota', 'secret', 'secret')
        config.add_section('sail-on')
        config.set('sail-on', 'training_novelty_p1', '0.0')
        config.set('sail-on', 'testing_novelty_p2', '0.8')
        config.set('sail-on', 'novelty', '200')
        config.set('sail-on', 'difficulty', 'easy,medium,hard')
        config.set('sail-on', 'trials', '30')
        config.set('sail-on', 'normal_timeout_seconds', str(objects.GLOBAL_TIMEOUT_SECONDS))
        config.set('sail-on', 'training_timeout_multiplier', '100')
        # To allow for all the docker images to have the same command, we need to allow all
        # the usual command line args to be defined in the config file.  The command line will
        # override any setting in the config file.
        config.add_section('options')
        config.set('options', 'debug', str(objects.DEFAULT_TA1_DEBUG))
        config.set('options', 'fulldebug', str(objects.DEFAULT_TA1_FULLDEBUG))
        config.set('options', 'printout', str(objects.DEFAULT_TA1_PRINTOUT))
        config.set('options', 'testing', str(objects.DEFAULT_TA1_TESTING))
        config.set('options', 'demo', str(objects.DEFAULT_TA1_DEMO))
        config.set('options', 'shortdemo', str(objects.DEFAULT_TA1_SHORTDEMO))
        return config

    def subscribe_experiment_queue(self):
        self.amqp.setup_subscribe_to_queue(queue_name=objects.SERVER_EXPERIMENT_QUEUE,
                                           queue_durable=True,
                                           queue_exclusive=False,
                                           queue_auto_delete=False,
                                           casas_events=True,
                                           callback_function=self.on_experiment_request,
                                           auto_ack=False,
                                           callback_full_params=True)
        return

    def subscribe_sota_queue(self):
        self.amqp.setup_subscribe_to_queue(queue_name=objects.REGISTER_SOTA_QUEUE,
                                           queue_durable=True,
                                           queue_exclusive=False,
                                           queue_auto_delete=False,
                                           casas_events=True,
                                           callback_function=self.on_sota_register_request,
                                           auto_ack=False,
                                           callback_full_params=True)
        return

    def unsubscribe_experiment_queue(self):
        self.amqp.remove_subscribe_to_queue(queue_name=objects.SERVER_EXPERIMENT_QUEUE)
        return

    def unsubscribe_sota_queue(self):
        self.amqp.remove_subscribe_to_queue(queue_name=objects.REGISTER_SOTA_QUEUE)
        return

    def setup_publish_analysis_queue(self):
        self.amqp.setup_publish_to_queue(queue_name=objects.ANALYSIS_READY_QUEUE,
                                         queue_durable=True,
                                         queue_exclusive=False,
                                         queue_auto_delete=False)
        return

    def publish_analysis(self, model_experiment_id: int):
        analysis_ready = objects.AnalysisReady(model_experiment_id=model_experiment_id)

        self.amqp.publish_to_queue(queue_name=objects.ANALYSIS_READY_QUEUE,
                                   casas_object=analysis_ready)
        return

    def publish_partial_analysis(self, model_experiment_id: int = None,
                                 experiment_trial_id: int = None):
        analysis_partial = objects.AnalysisPartial(
            model_experiment_id=model_experiment_id,
            experiment_trial_id=experiment_trial_id)

        self.amqp.publish_to_queue(queue_name=objects.ANALYSIS_READY_QUEUE,
                                   casas_object=analysis_partial)
        return

    def start(self):
        """Starts the main event loop in the RabbitMQ object.
        """
        time.sleep(self._random_sleep_seconds)
        self.log.debug("start()")

        x = True
        while x:
            try:
                self.amqp.run()
                self.amqp.start_consuming()
                x = False
            except KeyboardInterrupt:
                break
        return

    def connect_db(self):
        """Creates the psycopg2 connection to the postgres database.
        """
        self.log.debug("connect_db()")
        try:
            self.db_conn = psycopg2.connect(database=self.db_name,
                                            host=self.db_host,
                                            port=self.db_port,
                                            user=self.db_user,
                                            password=self.db_pass)
        except psycopg2.Error as e:
            self.log.error("Error trying to connect to the database: " + str(e.pgerror))
            time.sleep(1)
        return

    def reconnect_db(self):
        """This is called when the connection is disconnected while working, only returns once the
        connection is valid again.
        """
        self.log.debug("reconnect_db()")
        while self.db_conn is None:
            self.connect_db()
        while self.db_conn.closed != 0:
            self.connect_db()
        return

    def log_message(self, msg: LogMessage):
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    self.log.debug('{}   {}   {}'.format(msg.action, msg.message, msg.data_object))
                    if msg.message is None and msg.data_object is None:
                        sql = ('INSERT INTO experiment_log (model_experiment_id, action) '
                               'VALUES (%s, %s) RETURNING experiment_log_id;')
                        data = (msg.model_experiment_id,
                                msg.action,)
                    elif msg.message is not None and msg.data_object is None:
                        sql = ('INSERT INTO experiment_log (model_experiment_id, action, message) '
                               'VALUES (%s, %s, %s) RETURNING experiment_log_id;')
                        data = (msg.model_experiment_id,
                                msg.action,
                                msg.message,)
                    elif msg.message is None and msg.data_object is not None:
                        sql = ('INSERT INTO experiment_log (model_experiment_id, action, object) '
                               'VALUES (%s, %s, %s) RETURNING experiment_log_id;')
                        data = (msg.model_experiment_id,
                                msg.action,
                                Json(msg.data_object),)
                    else:
                        sql = ('INSERT INTO experiment_log (model_experiment_id, action, message, '
                               'object) VALUES (%s, %s, %s, %s) RETURNING experiment_log_id;')
                        data = (msg.model_experiment_id,
                                msg.action,
                                msg.message,
                                Json(msg.data_object),)
                    self.log.debug(cr.mogrify(sql, data))
                    cr.execute(sql, data)
                    self.db_conn.commit()
                    if msg.experiment_trial_id is not None:
                        row = cr.fetchone()
                        if row is not None:
                            experiment_log_id = row[0]
                            sql = ('UPDATE experiment_log SET experiment_trial_id=%s '
                                   'WHERE experiment_log_id=%s;')
                            data = (msg.experiment_trial_id,
                                    experiment_log_id)
                            cr.execute(sql, data)
                            self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
        return

    def handle_user(self, aiq_username: str, aiq_secret: str, errormsgs: list):
        self.log.debug('handle_user( {}, {} )'.format(aiq_username, aiq_secret))
        user_id = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = "SELECT user_id FROM users WHERE username=%s AND secret=%s;"
                    data = (aiq_username, aiq_secret,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        user_id = row[0]
                    else:
                        errormsgs.append('This username/secret does not exist, please contact '
                                         'us to create an account.')
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors collecting the user.")
        return user_id

    def handle_organization(self, organization_name: str, errormsgs: list) -> int:
        self.log.debug('handle_organization( {} )'.format(organization_name))
        organization_id = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = 'SELECT organization_id FROM organization WHERE name=%s;'
                    data = (organization_name,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        organization_id = row[0]
                    else:
                        sql = ('INSERT INTO organization (name) VALUES (%s) '
                               'RETURNING organization_id;')
                        data = (organization_name,)
                        cr.execute(sql, data)
                        row = cr.fetchone()
                        if row is not None:
                            organization_id = row[0]
                        else:
                            errormsgs.append('There was an error processing the organization.')
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors handling the organization.")
        return organization_id

    def handle_organization_users(self, organization_id: int, user_id: int, errormsgs: list):
        self.log.debug('handle_organization_users( {}, {} )'.format(organization_id, user_id))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT organization_id, user_id FROM organization_users WHERE '
                           'organization_id=%s AND user_id=%s;')
                    data = (organization_id,
                            user_id,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is None:
                        sql = ('INSERT INTO organization_users (organization_id, user_id) '
                               'VALUES (%s, %s);')
                        data = (organization_id,
                                user_id,)
                        cr.execute(sql, data)
                        self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors building the organization_users.")
        return

    def get_experiment_user_id(self, model_experiment_id: int, errormsgs: list):
        self.log.debug('get_experiment_user_id( {} )'.format(model_experiment_id))
        user_id = None
        c_name = None
        c_secret = None
        c_organization = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT users.user_id, users.username, users.secret, organization.name '
                           'FROM users '
                           'INNER JOIN model ON model.user_id = users.user_id '
                           'INNER JOIN model_experiment '
                           'ON model_experiment.model_id = model.model_id '
                           'INNER JOIN organization '
                           'ON model.organization_id=organization.organization_id '
                           'WHERE model_experiment.model_experiment_id=%s;')
                    data = (model_experiment_id,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        user_id = row[0]
                        c_name = row[1]
                        c_secret = row[2]
                        c_organization = row[3]
                    else:
                        errormsgs.append('This model_experiment_id does not exist!')
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors collecting the user_id.")
        return user_id, c_name, c_secret, c_organization

    def handle_model(self, model_request: objects.RequestModel, user_id: int, errormsgs: list,
                     insert_data: bool = True):
        self.log.debug("handle_model()")
        model = None
        organization_id = self.handle_organization(organization_name=model_request.organization,
                                                   errormsgs=errormsgs)
        self.handle_organization_users(organization_id=organization_id,
                                       user_id=user_id,
                                       errormsgs=errormsgs)
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT name, organization_id, description, model_id FROM model WHERE '
                           'user_id=%s AND name=%s AND organization_id=%s;')
                    data = (user_id,
                            model_request.model_name,
                            organization_id,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        model = objects.Model(model_name=row[0],
                                              organization=model_request.organization,
                                              aiq_username=model_request.aiq_username,
                                              aiq_secret=model_request.aiq_secret,
                                              description=row[2])
                        model.model_id = row[3]
                    elif insert_data:
                        sql = ('INSERT INTO model (user_id, name, organization_id, description) '
                               'VALUES (%s, %s, %s, %s);')
                        data = (user_id,
                                model_request.model_name,
                                organization_id,
                                model_request.description,)
                        cr.execute(sql, data)
                        self.db_conn.commit()
                        model = self.handle_model(model_request=model_request,
                                                  user_id=user_id,
                                                  errormsgs=errormsgs)
                    else:
                        errormsgs.append('Model does not exist for provided credentials.')
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors collecting/inserting the model.")
        return model

    def handle_experiment_request(self, experiment_request: objects.RequestExperiment,
                                  new_model: objects.Model, vhost: str, errormsgs: list):
        self.log.debug('handle_experiment_request({}, vhost={})'.format(
            str(experiment_request), vhost))
        experiment_response = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    if experiment_request.seed is None:
                        experiment_request.seed = random.randint(1, 1000000000)
                    experiment_secret = uuid.uuid4().hex
                    sql = ('INSERT INTO model_experiment '
                           '(model_id, novelty, novelty_visibility, seed, git_version, secret, '
                           'experiment_type, vhost) '
                           'VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING model_experiment_id;')
                    data = (new_model.model_id,
                            experiment_request.novelty,
                            experiment_request.novelty_visibility,
                            experiment_request.seed,
                            experiment_request.git_version,
                            experiment_secret,
                            experiment_request.experiment_type,
                            vhost,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
                    row = cr.fetchone()
                    if row is not None:
                        experiment_response = objects.ExperimentResponse(
                            server_rpc_queue='?',
                            experiment_secret=experiment_secret,
                            model_experiment_id=row[0],
                            experiment_timeout=self._AMQP_EXPERIMENT_TIMEOUT)
                        if experiment_request.description is not None:
                            sql = ('UPDATE model_experiment SET description=%S WHERE '
                                   'model_experiment_id=%s;')
                            data = (experiment_request.description,
                                    row[0],)
                            cr.execute(sql, data)
                            self.db_conn.commit()
                    self.log.debug('experiment_response: {}'.format(str(experiment_response)))
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the experiment.")
        random.seed(experiment_request.seed)
        return experiment_response

    def add_json_to_model_experiment(self, model_experiment_id: int, experiment: objects.Experiment,
                                     errormsgs: list):
        self.log.debug('add_json_to_model_experiment(model_experiment_id={})'.format(
                       model_experiment_id))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('UPDATE model_experiment SET experiment_json=%s WHERE '
                           'model_experiment_id=%s;')
                    data = (Json(experiment.get_json_obj()),
                            model_experiment_id,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the experiment JSON.")
        return

    def add_sota_to_experiment(self, model_experiment_id: int, sota_model_experiment_id: int,
                               errormsgs: list):
        self.log.debug('add_sota_to_experiment(model_experiment_id={}, '
                       'sota_experiment_id={})'.format(model_experiment_id,
                                                       sota_model_experiment_id))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('UPDATE model_experiment SET sota_experiment_id=%s '
                           'WHERE model_experiment_id=%s;')
                    data = (sota_model_experiment_id,
                            model_experiment_id,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors updating the experiment.")
        return

    def get_model_experiment_id_from_secret(self, vhost: str,
                                            request: objects.RequestExperimentTrials,
                                            errormsgs: list) -> int:
        self.log.debug('get_model_experiment_id_from_secret(vhost={})'.format(vhost))
        model_experiment_id = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT model_experiment_id, is_active FROM model_experiment WHERE '
                           'vhost=%s AND secret=%s;')
                    data = (vhost,
                            request.experiment_secret,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is None:
                        errormsgs.append('The provided experiment does not exist for the '
                                         'provided configuration.')
                    if row is not None:
                        if row[1]:
                            # is_active is True, so we can set the experiment.
                            model_experiment_id = row[0]
                        else:
                            # The experiment is completed, so we return an error instead.
                            errormsgs.append('The requested experiment is already completed!')
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors searching for the experiment.")
        return model_experiment_id

    def get_model_experiment_id_for_work(self, domain_id: int, vhost: str, model: objects.Model,
                                         request: objects.RequestExperimentTrials,
                                         errormsgs: list) -> int:
        self.log.debug('get_model_experiment_id_for_work(domain_id={}, vhost={})'.format(
            domain_id,
            vhost))
        model_experiment_id = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT model_experiment_id, is_active FROM model_experiment WHERE '
                           'model_id=%s AND vhost=%s AND secret=%s;')
                    data = (model.model_id,
                            vhost,
                            request.experiment_secret,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is None:
                        errormsgs.append('The provided experiment does not exist for the '
                                         'provided configuration.')
                    if row is not None:
                        if row[1]:
                            # is_active is True, so we can set the experiment.
                            model_experiment_id = row[0]
                        else:
                            # The experiment is completed, so we return an error instead.
                            errormsgs.append('The requested experiment is already completed!')
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors searching for the experiment.")
        return model_experiment_id

    def get_model_experiment_json(self, model_experiment_id: int, errormsgs: list) \
            -> objects.Experiment:
        self.log.debug('get_model_experiment_json(model_experiment_id={}'.format(
            model_experiment_id))
        experiment = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT experiment_json FROM model_experiment WHERE '
                           'model_experiment_id=%s;')
                    data = (model_experiment_id,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        msg = '[{}]'.format(json.dumps(row[0]))
                        experiment = objects.build_objects_from_json(message=msg)
                        experiment = experiment[0]
                        experiment.model_experiment_id = model_experiment_id
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors getting the experiment json.")
        return experiment

    def clear_abandoned_trials(self, errormsgs: list):
        self.log.debug('clear_abandoned_trials()')
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT experiment_trial_id FROM experiment_trial WHERE '
                           'is_active=%s AND is_complete=%s AND '
                           'utc_last_updated<(NOW() - interval\'1 hour\');')
                    data = (True,
                            False,)
                    self.log.debug(cr.mogrify(sql, data))
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    trial_ids = list()
                    while row is not None:
                        trial_ids.append(row[0])
                        row = cr.fetchone()

                    trial_sql = ('UPDATE experiment_trial SET locked_by=NULL, is_active=%s, '
                                 'utc_last_updated=NULL WHERE experiment_trial_id=%s;')
                    episode_sql = ('UPDATE trial_episode SET novelty=NULL, performance=NULL, '
                                   'novelty_probability=NULL, novelty_characterization=NULL, '
                                   'novelty_threshold=NULL, utc_stamp_started=NULL, '
                                   'utc_stamp_ended=NULL WHERE experiment_trial_id=%s;')
                    for t_id in trial_ids:
                        episode_ids = list()
                        sql = ('SELECT trial_episode_id FROM trial_episode WHERE '
                               'experiment_trial_id=%s;')
                        data = (t_id,)
                        self.log.debug(cr.mogrify(sql, data))
                        cr.execute(sql, data)
                        row = cr.fetchone()
                        while row is not None:
                            episode_ids.append(row[0])
                            row = cr.fetchone()

                        for ep_id in episode_ids:
                            # Refresh any needed AMQP heartbeats.
                            self.amqp.process_data_events()

                            del_sql = 'DELETE FROM test_instance WHERE trial_episode_id=%s;'
                            data = (ep_id,)
                            self.log.debug(cr.mogrify(del_sql, data))
                            cr.execute(del_sql, data)
                            data = (t_id,)
                            self.log.debug(cr.mogrify(episode_sql, data))
                            cr.execute(episode_sql, data)
                            data = (False,
                                    t_id,)
                            self.log.debug(cr.mogrify(trial_sql, data))
                            cr.execute(trial_sql, data)
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the experiment_trial.")
        return

    def add_all_experiment_trials(self, model_experiment_id: int, experiment: objects.Experiment,
                                  errormsgs: list):
        self.log.debug('add_all_experiment_trials()')
        for novelty_group in experiment.novelty_groups:
            for i, trial in enumerate(novelty_group.trials):
                # Refresh any needed AMQP heartbeats.
                self.amqp.process_data_events()

                domain = None
                if len(trial.episodes) > 0:
                    domain = trial.episodes[0].domain
                description = self.get_novelty_description(domain=domain,
                                                           novelty=trial.novelty,
                                                           difficulty=trial.difficulty)
                experiment_trial_id = self.handle_experiment_trial(
                    model_experiment_id=model_experiment_id,
                    novelty_description=description.novelty_description,
                    trial=i,
                    novelty=trial.novelty,
                    novelty_visibility=trial.novelty_visibility,
                    difficulty=trial.difficulty,
                    is_active=False,
                    errormsgs=errormsgs)

                self.add_all_trial_episodes(experiment_trial_id=experiment_trial_id,
                                            trial=trial,
                                            errormsgs=errormsgs)
        return

    def handle_experiment_trial(self, model_experiment_id: int, novelty_description: dict,
                                errormsgs: list, trial: int = 0, novelty: int = 0,
                                novelty_visibility: int = 0,
                                difficulty: str = objects.DIFFICULTY_MEDIUM,
                                is_active: bool = True):
        self.log.debug('handle_experiment_trial(model_experiment_id={}, '
                       'trial={}, novelty={}, difficulty={}, '
                       'novelty_description={}, '
                       'novelty_visibility={})'.format(model_experiment_id,
                                                       trial,
                                                       novelty,
                                                       difficulty,
                                                       str(novelty_description),
                                                       novelty_visibility))
        experiment_trial_id = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('INSERT INTO experiment_trial (model_experiment_id, trial, novelty, '
                           'novelty_visibility, difficulty, novelty_description, is_active) '
                           'VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING experiment_trial_id;')
                    data = (model_experiment_id,
                            trial,
                            novelty,
                            novelty_visibility,
                            difficulty,
                            Json(novelty_description),
                            is_active,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
                    row = cr.fetchone()
                    if row is not None:
                        experiment_trial_id = row[0]
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the experiment_trial.")
        return experiment_trial_id

    def add_training_episodes(self, experiment_trial_id: int, num_episodes: int, errormsgs: list):
        self.log.debug('add_training_episodes(experiment_trial_id={}, num_episodes={})'
                       .format(experiment_trial_id,
                               num_episodes))
        for i in range(num_episodes):
            self.handle_trial_episode(experiment_trial_id=experiment_trial_id,
                                      episode_index=i,
                                      novelty=objects.NOVELTY_200,
                                      novelty_initiated=False,
                                      errormsgs=errormsgs)
        return

    def add_all_trial_episodes(self, experiment_trial_id: int, trial: objects.Trial,
                               errormsgs: list):
        self.log.debug('add_all_trial_episodes(experiment_trial_id={}, len_episodes={})'
                       .format(experiment_trial_id, len(trial.episodes)))
        for i in range(len(trial.episodes)):
            novelty_initiated = (trial.episodes[i].novelty == trial.episodes[i].trial_novelty)
            self.handle_trial_episode(experiment_trial_id=experiment_trial_id,
                                      episode_index=trial.episodes[i].trial_episode_index,
                                      novelty=trial.episodes[i].novelty,
                                      novelty_initiated=novelty_initiated,
                                      errormsgs=errormsgs)

        return

    def handle_trial_episode(self, experiment_trial_id: int, episode_index: int, novelty: int,
                             novelty_initiated: bool, errormsgs: list):
        self.log.debug('handle_trial_episode(experiment_trial_id={}, episode_index={}, novelty={}, '
                       'novelty_initiated={})'
                       .format(experiment_trial_id,
                               episode_index,
                               novelty,
                               novelty_initiated))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('INSERT INTO trial_episode (experiment_trial_id, episode_index, '
                           'novelty, novelty_initiated) VALUES (%s, %s, %s, %s);')
                    data = (experiment_trial_id,
                            episode_index,
                            novelty,
                            novelty_initiated,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the trial_episode.")
        return

    def start_experiment_trial(self, experiment_trial_id: int, errormsgs: list):
        self.log.debug('start_experiment_trial(experiment_trial_id={})'.format(experiment_trial_id))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('UPDATE experiment_trial SET is_active=%s, utc_stamp_started=NOW(), '
                           'utc_last_updated=NOW() WHERE experiment_trial_id=%s;')
                    data = (True,
                            experiment_trial_id,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors starting the experiment_trial.")
        return

    def update_experiment_trial(self, experiment_trial_id: int, errormsgs: list):
        self.log.debug('update_experiment_trial(experiment_trial_id={})'.format(
            experiment_trial_id))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('UPDATE experiment_trial SET utc_last_updated=NOW() '
                           'WHERE experiment_trial_id=%s;')
                    data = (experiment_trial_id,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors updating the experiment_trial.")
        return

    def end_experiment_trial(self, experiment_trial_id: int, errormsgs: list):
        self.log.debug('end_experiment_trial(experiment_trial_id={})'.format(experiment_trial_id))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('UPDATE experiment_trial SET is_active=%s, is_complete=%s, '
                           'utc_stamp_ended=NOW(), locked_by=NULL WHERE experiment_trial_id=%s;')
                    data = (False,
                            True,
                            experiment_trial_id,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors ending the experiment_trial.")
        return

    def lock_experiment_trial(self, model_experiment_id: int, errormsgs: list) -> int:
        self.log.debug('lock_experiment_trial(model_experiment_id={})'.format(model_experiment_id))
        experiment_trial_id = None
        try:
            my_uuid = str(uuid.uuid4())
            is_locked = False
            max_wait = 10.0
            end_time = float(time.time()) + max_wait
            while not is_locked and float(time.time()) < end_time:
                with self.db_conn:
                    with self.db_conn.cursor() as cr:
                        sql = ('SELECT experiment_trial_id FROM experiment_trial WHERE '
                               'model_experiment_id=%s AND is_active=%s AND is_complete=%s AND '
                               'locked_by IS NULL LIMIT 1;')
                        data = (model_experiment_id,
                                False,
                                False,)
                        self.log.debug(cr.mogrify(sql, data))
                        cr.execute(sql, data)
                        row = cr.fetchone()
                        if row is None:
                            # There is no available trial, so no point in trying again.
                            is_locked = True
                        elif row is not None:
                            ext_id = row[0]
                            sql = ('UPDATE experiment_trial SET locked_by=%s WHERE '
                                   'model_experiment_id=%s AND is_active=%s AND is_complete=%s AND '
                                   'locked_by IS NULL AND experiment_trial_id=%s;')
                            data = (my_uuid,
                                    model_experiment_id,
                                    False,
                                    False,
                                    ext_id,)
                            cr.execute(sql, data)
                            self.db_conn.commit()
                            sql = ('SELECT experiment_trial_id FROM experiment_trial WHERE '
                                   'locked_by=%s AND model_experiment_id=%s AND '
                                   'experiment_trial_id=%s;')
                            data = (my_uuid,
                                    model_experiment_id,
                                    ext_id,)
                            cr.execute(sql, data)
                            row = cr.fetchone()
                            if row is not None:
                                if row[0] is not None:
                                    experiment_trial_id = row[0]
                                    is_locked = True
                            if not is_locked:
                                self.amqp.sleep(duration=(random.random() / 2.0))
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors locking the experiment_trial.")
        return experiment_trial_id

    def set_experiment_trial_index(self, experiment_trial_id: int, errormsgs: list):
        self.log.debug('set_experiment_trial_index(experiment_trial_id={})'.format(
            experiment_trial_id))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT trial, novelty, novelty_visibility, difficulty, '
                           'novelty_description FROM experiment_trial '
                           'WHERE experiment_trial_id=%s;')
                    data = (experiment_trial_id,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        trial = row[0]
                        novelty = row[1]
                        novelty_vis = row[2]
                        difficulty = row[3]
                        nov_description = row[4]
                        ng_index = 0
                        found = False
                        for ng in self._experiment.novelty_groups:
                            if len(ng.trials) > trial:
                                ngt = ng.trials[trial]
                                if ngt.novelty == novelty and ngt.difficulty == difficulty and \
                                        ngt.novelty_visibility == novelty_vis:
                                    found = True
                                    break
                            if not found:
                                ng_index += 1
                        if found:
                            self._exper_novelty_index = ng_index
                            self._exper_trial_index = trial
                            self._exper_episode_index = 0
                            self._exper_trial_novelty_desc = copy.deepcopy(nov_description)

        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors setting the experiment_trial index in TA1.")
        return

    def start_trial_episode(self, experiment_trial_id: int, episode_index: int,
                            budget_active: bool, errormsgs: list) -> int:
        self.log.debug('start_trial_episode(experiment_trial_id={}, episode_index={}, '
                       'budget_active={})'
                       .format(experiment_trial_id,
                               episode_index,
                               budget_active))
        trial_episode_id = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT trial_episode_id FROM trial_episode '
                           'WHERE experiment_trial_id=%s AND episode_index=%s;')
                    data = (experiment_trial_id,
                            episode_index,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        trial_episode_id = row[0]
                        sql = ('UPDATE trial_episode SET utc_stamp_started=NOW(), budget_active=%s '
                               'WHERE trial_episode_id=%s;')
                        data = (budget_active,
                                trial_episode_id,)
                        cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors starting the trial_episode.")
        return trial_episode_id

    def stop_trial_episode(self, trial_episode_id: int, errormsgs: list):
        self.log.debug('stop_trial_episode(trial_episode_id={})'.format(trial_episode_id))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('UPDATE trial_episode SET utc_stamp_ended=NOW() '
                           'WHERE trial_episode_id=%s;')
                    data = (trial_episode_id,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors stopping the trial_episode.")
        return

    def set_trial_episode_stats(self, trial_episode_id: int, novelty: int, performance: float,
                                novelty_probability: float, novelty_threshold: float,
                                novelty_characterization: dict, errormsgs: list):
        self.log.debug('set_trial_episode_stats(trial_episode_id={}, novelty={}, performance={}, '
                       'novelty_probability={}, novelty_threshold={}, characterization={})'
                       .format(trial_episode_id,
                               novelty,
                               performance,
                               novelty_probability,
                               novelty_threshold,
                               novelty_characterization))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('UPDATE trial_episode SET novelty=%s, performance=%s, '
                           'novelty_probability=%s, novelty_threshold=%s, '
                           'novelty_characterization=%s '
                           'WHERE trial_episode_id=%s;')
                    data = (novelty,
                            performance,
                            novelty_probability,
                            novelty_threshold,
                            Json(novelty_characterization),
                            trial_episode_id,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors updating the trial_episode.")
        return

    def handle_domains(self, experiment_request: objects.RequestExperiment, errormsgs: list):
        self.log.debug("handle_domains()")
        domain_id_dict = dict()
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = 'SELECT name, domain_id FROM domain WHERE name=ANY(%s);'
                    data = (list(experiment_request.domain_dict.keys()),)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    while row is not None:
                        domain_id_dict[row[0]] = row[1]
                        row = cr.fetchone()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors collecting the domains.")
        return domain_id_dict

    def set_experiment_domains(self, experiment_request: objects.RequestExperiment,
                               experiment_response: objects.ExperimentResponse,
                               domain_id_dict: dict, errormsgs: list):
        self.log.debug('set_experiment_domains()')
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    for domain in list(domain_id_dict.keys()):
                        if experiment_request.domain_dict[domain]:
                            sql = ('SELECT model_experiment_id, domain_id FROM experiment_domain '
                                   'WHERE model_experiment_id=%s AND domain_id=%s;')
                            data = (experiment_response.model_experiment_id,
                                    domain_id_dict[domain],)
                            cr.execute(sql, data)
                            row = cr.fetchone()
                            if row is None:
                                sql = ('INSERT INTO experiment_domain (model_experiment_id, '
                                       'domain_id) VALUES (%s, %s);')
                                data = (experiment_response.model_experiment_id,
                                        domain_id_dict[domain],)
                                cr.execute(sql, data)
                                self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the experiment domains.")
        return

    def update_experiment_end(self, model_experiment_id: int, errormsgs: list):
        self.log.debug('update_experiment_end(model_experiment_id={})'.format(model_experiment_id))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT COUNT(*) FROM experiment_trial WHERE '
                           'model_experiment_id=%s AND is_complete=%s;')
                    data = (model_experiment_id,
                            False,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    is_done = False
                    if row is not None:
                        if int(row[0]) == 0:
                            is_done = True
                    if is_done:
                        sql = ('UPDATE model_experiment SET utc_stamp_ended=NOW(), is_active=%s '
                               'WHERE model_experiment_id=%s AND utc_stamp_ended IS NULL;')
                        data = (False,
                                model_experiment_id,)
                        cr.execute(sql, data)
                        sql = ('UPDATE experiment_trial SET is_active=%s WHERE '
                               'model_experiment_id=%s;')
                        data = (False,
                                model_experiment_id,)
                        cr.execute(sql, data)
                        self.db_conn.commit()

                        # Publish this experiment for a full analysis.
                        self.publish_analysis(model_experiment_id=model_experiment_id)
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors updating the experiment.")
        return

    def refresh_dataset_in_cache(self, dataset_id: int, errormsgs: list):
        self.log.debug('refresh_dataset_in_cache(dataset_id={})'.format(dataset_id))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT domain_id, data_type, novelty, difficulty, episodes, name, '
                           'version, trial_novelty FROM dataset WHERE dataset_id=%s;')
                    data = (dataset_id,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        domain_id = row[0]
                        data_type = row[1]
                        novelty = row[2]
                        difficulty = row[3]
                        episodes = row[4]
                        name = row[5]
                        version = row[6]
                        trial_novelty = row[7]
                        self.dataset_cache[domain_id][data_type][novelty][difficulty][
                            trial_novelty]['episodes'] = episodes
                        self.dataset_cache[domain_id][data_type][novelty][difficulty][
                            trial_novelty]['name'] = name
                        self.dataset_cache[domain_id][data_type][novelty][difficulty][
                            trial_novelty]['version'] = version
                        for i in range(episodes):
                            self.add_episode_to_cache(dataset_id=dataset_id,
                                                      episode_index=i)
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors refreshing the cached dataset.")
        return

    def get_dataset_id(self, d_id: int, d_type: str, novel: int, d_diff: str, t_nov: int,
                       errormsgs: list):
        self.log.debug('get_dataset_id()')
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT dataset_id FROM dataset WHERE novelty=%s AND data_type=%s '
                           'AND domain_id=%s AND difficulty=%s and trial_novelty=%s;')
                    data = (novel,
                            d_type,
                            d_id,
                            d_diff,
                            t_nov,)
                    self.log.debug(cr.mogrify(sql, data))
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is None:
                        dataset_name = '{}.{}.{}.{}.{}'.format(self.domain_names[d_id],
                                                               d_type,
                                                               novel,
                                                               t_nov,
                                                               d_diff)
                        # There is no dataset matching what we need, so we create a new one.
                        sql = ('INSERT INTO dataset (name, version, novelty, data_type, '
                               'domain_id, seed, difficulty, episodes, trial_novelty) '
                               'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);')
                        data = (dataset_name,
                                objects.__version__,
                                novel,
                                d_type,
                                d_id,
                                '0',
                                d_diff,
                                0,
                                t_nov,)
                        self.log.debug(cr.mogrify(sql, data))
                        cr.execute(sql, data)
                        self.db_conn.commit()
                    sql = ('SELECT dataset_id, episodes, name, version FROM dataset WHERE '
                           'novelty=%s AND data_type=%s AND domain_id=%s AND difficulty=%s '
                           'AND trial_novelty=%s ORDER BY version DESC;')
                    data = (novel,
                            d_type,
                            d_id,
                            d_diff,
                            t_nov,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        self.log.debug('dataset_id = {}  name = {}  episodes = {}  version = {}'
                                       ''.format(row[0], row[2], row[1], row[3]))
                        self.dataset_cache[d_id][d_type][novel][d_diff][t_nov][
                            'dataset_id'] = row[0]
                        self.dataset_cache[d_id][d_type][novel][d_diff][t_nov]['episodes'] = row[1]
                        self.dataset_cache[d_id][d_type][novel][d_diff][t_nov]['name'] = row[2]
                        self.dataset_cache[d_id][d_type][novel][d_diff][t_nov]['version'] = row[3]
                        self.episode_cache[row[0]] = dict()
                        if row[1] is not None:
                            for i in range(row[1]):
                                self.add_episode_to_cache(dataset_id=row[0],
                                                          episode_index=i)
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors gathering the dataset IDs.")
        return

    def add_episode_to_cache(self, dataset_id: int, episode_index: int):
        # First make sure the dataset_id is in the episode_cache.
        if dataset_id not in self.episode_cache:
            self.episode_cache[dataset_id] = dict()

        # Only add episode if it is not in the episode_cache already.
        if episode_index not in self.episode_cache[dataset_id]:
            self.episode_cache[dataset_id][episode_index] = dict({
                'episode_id': None,
                'dataset_id': dataset_id,
                'test_instance_id': None,
                'size': None,
                'data_index': 0})
        return

    def get_dataset_ids(self, errormsgs: list):
        self.log.debug('get_dataset_ids()')

        for d_id in list(self.dataset_cache.keys()):
            for d_type in list(self.dataset_cache[d_id].keys()):
                for novel in list(self.dataset_cache[d_id][d_type].keys()):
                    for d_diff in list(self.dataset_cache[d_id][d_type][novel].keys()):
                        for t_nov in list(self.dataset_cache[d_id][d_type][novel][d_diff].keys()):
                            self.get_dataset_id(d_id=d_id,
                                                d_type=d_type,
                                                novel=novel,
                                                d_diff=d_diff,
                                                t_nov=t_nov,
                                                errormsgs=errormsgs)
        return

    def build_domain_cache(self, request: objects.RequestExperiment, errormsgs: list):
        self.log.debug('build_domain_cache()')
        self.domain_ids = dict()
        self.domain_ids = self.handle_domains(experiment_request=request,
                                              errormsgs=errormsgs)
        self.domain_cache = list()
        for domain in list(request.domain_dict.keys()):
            self.domain_names[self.domain_ids[domain]] = domain
            if request.domain_dict[domain]:
                self.domain_cache.append(self.domain_ids[domain])
        return

    def build_dataset_cache(self, request: objects.RequestExperiment, errormsgs: list,
                            experiment: objects.Experiment = None):
        self.log.debug('build_dataset_cache()')
        # [dataset_id][episode_index] = dict( episode_id, data_index )
        self.episode_cache = dict()
        # [domain_id][data_type][novelty][difficulty] = dict( various things )
        self.dataset_cache = dict()
        # [episode_id][data_index] = dict( data stuff )
        self.data_cache = dict()
        self.rolling_score = list()
        self._server_novelty_index = 0
        self._sota_server_novelty_index = 0
        if request.experiment_type == objects.TYPE_EXPERIMENT_SAIL_ON:
            self.novelty_level = self._server_novelty[self._server_novelty_index]
        elif request.experiment_type == objects.TYPE_EXPERIMENT_AIQ:
            self.novelty_level = 0

        domain = None
        for req_domain in list(request.domain_dict.keys()):
            if request.domain_dict[req_domain]:
                domain = req_domain

        if self._is_domain_live[domain]:
            train_type = objects.DTYPE_LIVE_TRAIN
            test_type = objects.DTYPE_LIVE_TEST
        else:
            train_type = objects.DTYPE_TRAIN
            test_type = objects.DTYPE_TEST

        cache_valid_domains = list(request.domain_dict.keys())
        cache_valid_data_types = None
        cache_novelty_types = list([objects.NOVELTY_200] + self._server_novelty)
        cache_trial_novelty = dict({
            train_type: dict({objects.NOVELTY_200: list([objects.NOVELTY_200])}),
            test_type: dict({objects.NOVELTY_200: list([objects.NOVELTY_200]),
                             objects.NOVELTY_101: list([objects.NOVELTY_200]),
                             objects.NOVELTY_102: list([objects.NOVELTY_200]),
                             objects.NOVELTY_103: list([objects.NOVELTY_200]),
                             objects.NOVELTY_104: list([objects.NOVELTY_200]),
                             objects.NOVELTY_105: list([objects.NOVELTY_200]),
                             objects.NOVELTY_201: list([objects.NOVELTY_200]),
                             objects.NOVELTY_202: list([objects.NOVELTY_200]),
                             objects.NOVELTY_203: list([objects.NOVELTY_200]),
                             objects.NOVELTY_204: list([objects.NOVELTY_200]),
                             objects.NOVELTY_205: list([objects.NOVELTY_200])})})
        if objects.DOMAIN_SMARTENV in cache_valid_domains and experiment is None:
            cache_trial_novelty = dict({
                train_type: dict({objects.NOVELTY_200: list([objects.NOVELTY_200,
                                                             objects.NOVELTY_101,
                                                             objects.NOVELTY_102,
                                                             objects.NOVELTY_103,
                                                             objects.NOVELTY_104,
                                                             objects.NOVELTY_105,
                                                             objects.NOVELTY_201,
                                                             objects.NOVELTY_202,
                                                             objects.NOVELTY_203,
                                                             objects.NOVELTY_204,
                                                             objects.NOVELTY_205])}),
                test_type: dict({objects.NOVELTY_200: list([objects.NOVELTY_200,
                                                            objects.NOVELTY_101,
                                                            objects.NOVELTY_102,
                                                            objects.NOVELTY_103,
                                                            objects.NOVELTY_104,
                                                            objects.NOVELTY_105,
                                                            objects.NOVELTY_201,
                                                            objects.NOVELTY_202,
                                                            objects.NOVELTY_203,
                                                            objects.NOVELTY_204,
                                                            objects.NOVELTY_205]),
                                 objects.NOVELTY_101: list([objects.NOVELTY_101]),
                                 objects.NOVELTY_102: list([objects.NOVELTY_102]),
                                 objects.NOVELTY_103: list([objects.NOVELTY_103]),
                                 objects.NOVELTY_104: list([objects.NOVELTY_104]),
                                 objects.NOVELTY_105: list([objects.NOVELTY_105]),
                                 objects.NOVELTY_201: list([objects.NOVELTY_201]),
                                 objects.NOVELTY_202: list([objects.NOVELTY_202]),
                                 objects.NOVELTY_203: list([objects.NOVELTY_203]),
                                 objects.NOVELTY_204: list([objects.NOVELTY_204]),
                                 objects.NOVELTY_205: list([objects.NOVELTY_205])})})
        if experiment is not None:
            cache_valid_data_types = list()
            cache_trial_novelty = dict()
            for episode in experiment.training.episodes:
                if episode.domain not in cache_valid_domains:
                    cache_valid_domains.append(episode.domain)
                if episode.data_type not in cache_valid_data_types:
                    cache_valid_data_types.append(episode.data_type)
                    cache_trial_novelty[episode.data_type] = dict()
                if episode.novelty not in cache_novelty_types:
                    cache_novelty_types.append(episode.novelty)
                if episode.novelty not in cache_trial_novelty[episode.data_type]:
                    cache_trial_novelty[episode.data_type][episode.novelty] = list()
                if episode.trial_novelty not in \
                        cache_trial_novelty[episode.data_type][episode.novelty]:
                    cache_trial_novelty[episode.data_type][episode.novelty].append(
                        episode.trial_novelty)
            for novelty_group in experiment.novelty_groups:
                for trial in novelty_group.trials:
                    for episode in trial.episodes:
                        if episode.domain not in cache_valid_domains:
                            cache_valid_domains.append(episode.domain)
                        if episode.data_type not in cache_valid_data_types:
                            cache_valid_data_types.append(episode.data_type)
                            cache_trial_novelty[episode.data_type] = dict()
                        if episode.novelty not in cache_novelty_types:
                            cache_novelty_types.append(episode.novelty)
                        if episode.novelty not in cache_trial_novelty[episode.data_type]:
                            cache_trial_novelty[episode.data_type][episode.novelty] = list()
                        if episode.trial_novelty not in \
                                cache_trial_novelty[episode.data_type][episode.novelty]:
                            cache_trial_novelty[episode.data_type][episode.novelty].append(
                                episode.trial_novelty)
        self.log.debug(str(cache_trial_novelty))

        for domain in cache_valid_domains:
            # Only prepare the domains we want.
            if not request.domain_dict[domain]:
                continue

            if cache_valid_data_types is None:
                cache_valid_data_types = list()
                if self._is_domain_live[domain]:
                    cache_valid_data_types.append(objects.DTYPE_LIVE_TRAIN)
                    cache_valid_data_types.append(objects.DTYPE_LIVE_TEST)
                else:
                    cache_valid_data_types.append(objects.DTYPE_TRAIN)
                    cache_valid_data_types.append(objects.DTYPE_TEST)
            domain_id = self.domain_ids[domain]
            self.dataset_cache[domain_id] = dict()
            for data_type in cache_valid_data_types:
                self.log.debug('data_type = {}'.format(data_type))
                self.dataset_cache[domain_id][data_type] = dict()
                self.log.debug('cache_novelty_types: {}'.format(str(cache_novelty_types)))
                for novelty in cache_novelty_types:
                    self.log.debug('novelty = {}'.format(novelty))
                    self.dataset_cache[domain_id][data_type][novelty] = dict()
                    for difficulty in self._server_difficulty:
                        self.log.debug('difficulty = {}'.format(difficulty))
                        self.dataset_cache[domain_id][data_type][novelty][difficulty] = dict()
                        self.log.debug('cache_trial_novelty = {}'.format(str(cache_trial_novelty)))
                        self.log.debug('ctn[dt] = {}'.format(str(cache_trial_novelty[data_type])))
                        if novelty in cache_trial_novelty[data_type]:
                            for t_novelty in cache_trial_novelty[data_type][novelty]:
                                self.dataset_cache[domain_id][data_type][novelty][difficulty][
                                    t_novelty] = dict({
                                        'domain_id': domain_id,
                                        'domain': domain,
                                        'novelty': novelty,
                                        'trial_novelty': t_novelty,
                                        'data_type': data_type,
                                        'difficulty': difficulty,
                                        'name': None,
                                        'version': None,
                                        'dataset_id': None,
                                        'episodes': None,
                                        'test_instance_id': None,
                                        'episode_index': 0})
                                self.log.debug('DATASET: {}'.format(
                                    self.dataset_cache[domain_id][data_type][novelty][difficulty][
                                        t_novelty]))
        self.get_dataset_ids(errormsgs=errormsgs)
        return

    def get_dataset_episodes(self, dataset_id: int, errormsgs: list) -> int:
        self.log.debug('get_dataset_episodes(dataset_id={})'.format(dataset_id))
        episodes = 0
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = 'SELECT count(*) FROM episode WHERE dataset_id=%s;'
                    data = (dataset_id,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        if row[0] is not None:
                            episodes = row[0]
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors gathering the dataset episodes count.")
        return episodes

    def update_dataset_episodes(self, dataset_id: int, episodes: int, errormsgs: list):
        self.log.debug('update_dataset_episodes(dataset_id={}, episodes={})'.format(dataset_id,
                                                                                    episodes))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = 'UPDATE dataset SET episodes=%s WHERE dataset_id=%s'
                    data = (episodes,
                            dataset_id,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors updating the dataset episodes count.")
        return

    def lock_dataset(self, dataset_id: int, my_uuid: str, errormsgs: list):
        self.log.debug('lock_dataset(dataset_id={}, my_uuid={})'.format(dataset_id, my_uuid))
        try:
            is_locked = False
            max_wait = 30.0
            end_time = float(time.time()) + max_wait
            while not is_locked and float(time.time()) < end_time:
                with self.db_conn:
                    with self.db_conn.cursor() as cr:
                        sql = ('UPDATE dataset SET locked_by=%s, locked_at=NOW() WHERE '
                               'dataset_id=%s AND ( locked_by IS NULL OR '
                               'locked_at<(NOW() - interval \'10 seconds\') ) '
                               'RETURNING locked_by;')
                        data = (my_uuid,
                                dataset_id,)
                        self.log.debug(cr.mogrify(sql, data))
                        cr.execute(sql, data)
                        row = cr.fetchone()
                        if row is not None:
                            if row[0] is not None:
                                if my_uuid == row[0]:
                                    is_locked = True
                        if not is_locked:
                            sql = ('SELECT locked_by, locked_at, NOW() FROM dataset WHERE '
                                   'dataset_id=%s;')
                            data = (dataset_id,)
                            cr.execute(sql, data)
                            row = cr.fetchone()
                            self.log.debug('not locked... locked_by={}, locked_at={} NOW()={} '
                                           'remaining={}'.format(row[0],
                                                                 str(row[1]),
                                                                 str(row[2]),
                                                                 end_time - time.time()))
                            self.amqp.sleep(duration=(random.random() / 2.0))
            # The dataset is now locked and we may modify it.
            if not is_locked:
                # The dataset took too long to lock, throw an exception.
                raise objects.AiqExperimentException('Could not lock the dataset.')
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors locking the dataset.")
        return

    def unlock_dataset(self, dataset_id: int, my_uuid: str, errormsgs: list):
        self.log.debug('unlock_dataset(dataset_id={}, my_uuid={})'.format(dataset_id, my_uuid))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('UPDATE dataset SET locked_by=NULL WHERE '
                           'dataset_id=%s AND locked_by=%s;')
                    data = (dataset_id,
                            my_uuid,)
                    cr.execute(sql, data)
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors unlocking the dataset.")
        return

    def add_episode_to_dataset(self, dataset_id: int, seed: int, errormsgs: list) -> int:
        self.log.debug('add_episode_to_dataset( dataset_id={}, seed={} )'.format(dataset_id,
                                                                                 seed))
        episode_index = -1
        try:
            # with self.db_conn:
            #     with self.db_conn.cursor() as cr:
            # First we need to lock the dataset to add a new episode and update the count.
            my_uuid = str(uuid.uuid4())
            self.lock_dataset(dataset_id=dataset_id,
                              my_uuid=my_uuid,
                              errormsgs=errormsgs)

            # Refresh the dataset cache while locked.
            self.refresh_dataset_in_cache(dataset_id=dataset_id,
                                          errormsgs=errormsgs)

            # Now get the episode count.
            episodes = self.get_dataset_episodes(dataset_id=dataset_id,
                                                 errormsgs=errormsgs)
            episode_index = episodes

            # Add the new episode to the episode_cache so we can then add episode_id.
            self.add_episode_to_cache(dataset_id=dataset_id,
                                      episode_index=episode_index)
            episodes += 1

            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    # Insert the new episode.
                    sql = ('INSERT INTO episode (dataset_id, episode_index, size, seed) '
                           'VALUES (%s, %s, %s, %s) RETURNING episode_id;')
                    data = (dataset_id,
                            episode_index,
                            0,
                            seed)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        episode_id = row[0]
                        self.episode_cache[dataset_id][episode_index]['episode_id'] = episode_id
                        self.episode_cache[dataset_id][episode_index]['size'] = 0

            # Update the dataset with new episodes value.
            self.update_dataset_episodes(dataset_id=dataset_id,
                                         episodes=episodes,
                                         errormsgs=errormsgs)

            # Finally, unlock the dataset row.
            self.unlock_dataset(dataset_id=dataset_id,
                                my_uuid=my_uuid,
                                errormsgs=errormsgs)
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors gathering the dataset episodes count.")
        return episode_index

    def get_episode_ids(self, dataset_id: int, episode_index: int, errormsgs: list):
        self.log.debug('get_episode_ids()')
        self.add_episode_to_cache(dataset_id=dataset_id,
                                  episode_index=episode_index)
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT episode_id, size FROM episode WHERE '
                           'dataset_id=%s AND episode_index=%s;')
                    data = (dataset_id,
                            episode_index,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        self.episode_cache[dataset_id][episode_index]['episode_id'] = row[0]
                        self.episode_cache[dataset_id][episode_index]['size'] = row[1]
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors gathering the episode IDs.")
        return

    def load_data_to_cache(self, episode_id: int, at_data_index: int, errormsgs: list):
        self.log.debug('load_data_to_cache( episode_id={}, at_data_index={} )'.format(
            episode_id,
            at_data_index))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT data_index, feature_vector, label, data_id FROM data WHERE '
                           'episode_id=%s AND data_index BETWEEN %s AND %s '
                           'ORDER BY data_index;')
                    data = (episode_id,
                            at_data_index,
                            at_data_index + self._DATA_CACHE_SIZE,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if episode_id not in self.data_cache:
                        self.data_cache[episode_id] = dict()
                    while row is not None:
                        self.data_cache[episode_id][row[0]] = dict({
                            'data_index': row[0],
                            'feature_vector': copy.deepcopy(row[1]),
                            'label': copy.deepcopy(row[2]),
                            'data_id': row[3]})
                        row = cr.fetchone()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors loading data to the cache.")
        return

    def update_episode_size(self, episode_id: int, size: int, errormsgs: list):
        self.log.debug('update_episode_size(episode_id={}, size={})'.format(episode_id, size))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = 'UPDATE episode SET size=%s WHERE episode_id=%s'
                    data = (size,
                            episode_id,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors updating the episode size..")
        return

    def create_data_instance(self, episode_id: int, feature_vector: dict, label: dict,
                             data_index: int, errormsgs: list) -> int:
        self.log.debug('create_data_instance( episode_id={}, feature_vector={}, label={}, '
                       'data_index={} )'.format(episode_id,
                                                str(feature_vector),
                                                str(label),
                                                data_index))
        data_id = -1
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    tmp_fv = copy.deepcopy(feature_vector)
                    if 'image' in tmp_fv:
                        del tmp_fv['image']
                    sql = ('INSERT INTO data (episode_id, feature_vector, label, data_index) '
                           'VALUES (%s, %s, %s, %s) RETURNING data_id;')
                    data = (episode_id,
                            Json(tmp_fv),
                            Json(label),
                            data_index,)
                    # self.log.debug(cr.mogrify(sql, data))
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        data_id = row[0]
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the data instance.")
        return data_id

    def create_test_instance(self, data_id: int, trial_episode_id: int, errormsgs: list):
        self.log.debug('create_test_instance( data_id={}, trial_episode_id={} )'.format(
            data_id, trial_episode_id))
        test_instance_id = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT test_instance_id FROM test_instance WHERE '
                           'data_id=%s AND trial_episode_id=%s;')
                    data = (data_id,
                            trial_episode_id,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        test_instance_id = row[0]
                    else:
                        sql = ('INSERT INTO test_instance (trial_episode_id, data_id) VALUES '
                               '(%s, %s) RETURNING test_instance_id;')
                        data = (trial_episode_id,
                                data_id,)
                        cr.execute(sql, data)
                        row = cr.fetchone()
                        if row is not None:
                            test_instance_id = row[0]
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the test_instance.")
        return test_instance_id

    def update_test_instance(self, test_instance_id: int, remote_stamp_arrived: datetime.datetime,
                             remote_stamp_delivered: datetime.datetime, errormsgs: list):
        self.log.debug('update_test_instance(test_instance_id={}, stamp_arrived={}, '
                       'stamp_delivered={})'.format(test_instance_id,
                                                    remote_stamp_arrived,
                                                    remote_stamp_delivered))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('UPDATE test_instance SET utc_stamp_received=NOW(), '
                           'utc_remote_stamp_arrived=%s, utc_remote_stamp_replied=%s '
                           'WHERE test_instance_id=%s;')
                    data = (remote_stamp_arrived,
                            remote_stamp_delivered,
                            test_instance_id,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors updating the test_instance.")
        return

    def create_test_label(self, test_instance_id: int, label_prediction: dict, performance: float,
                          errormsgs: list, feedback: dict = None):
        self.log.debug('create_test_label(test_instance_id={}, label_prediction={}, '
                       'performance={}, feedback={})'
                       .format(test_instance_id,
                               label_prediction,
                               performance,
                               str(feedback)))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    if feedback is None:
                        sql = ('INSERT INTO test_label (test_instance_id, label_prediction, '
                               'performance) '
                               'VALUES (%s, %s, %s);')
                        data = (test_instance_id,
                                Json(label_prediction),
                                performance,)
                        cr.execute(sql, data)
                    else:
                        sql = ('INSERT INTO test_label (test_instance_id, label_prediction, '
                               'performance, feedback) '
                               'VALUES (%s, %s, %s, %s);')
                        data = (test_instance_id,
                                Json(label_prediction),
                                performance,
                                Json(feedback),)
                        cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the test_label.")
        return

    def insert_sota_experiment(self, domain_id: int, model_experiment_id: int,
                               experiment: objects.Experiment, vhost: str, errormsgs: list):
        self.log.debug('insert_sota_experiment(domain_id={}, model_experiment_id={}, vhost={}, '
                       'experiment)'.format(domain_id, model_experiment_id, vhost))
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('INSERT INTO sota_experiments (experiment_json, domain_id, version, '
                           'model_experiment_id, vhost) '
                           'VALUES (%s, %s, %s, %s, %s);')
                    data = (Json(experiment.get_json_obj()),
                            domain_id,
                            objects.__version__,
                            model_experiment_id,
                            vhost,)
                    cr.execute(sql, data)
                    self.db_conn.commit()
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the SOTA experiment.")
        return

    def get_sota_experiment(self, domain_id: int, vhost: str, errormsgs: list) ->\
            objects.Experiment:
        self.log.debug('get_sota_experiment(domain_id={}, vhost={})'.format(domain_id, vhost))
        experiment = None
        try:
            with self.db_conn:
                with self.db_conn.cursor() as cr:
                    sql = ('SELECT sota_experiments_id FROM sota_experiments WHERE '
                           'version=%s AND '
                           'domain_id=%s AND '
                           'vhost=%s AND '
                           'claimed_id IS NULL '
                           'ORDER BY utc_created_on ASC;')
                    data = (objects.__version__,
                            domain_id,
                            vhost,)
                    cr.execute(sql, data)
                    row = cr.fetchone()
                    if row is not None:
                        sota_experiments_id = row[0]
                        sota_uuid = str(uuid.uuid4().hex)
                        sql = ('UPDATE sota_experiments SET claimed_id=%s WHERE '
                               'sota_experiments_id=%s AND '
                               'claimed_id IS NULL;')
                        data = (sota_uuid,
                                sota_experiments_id,)
                        cr.execute(sql, data)
                        self.db_conn.commit()
                        sql = ('SELECT experiment_json, model_experiment_id '
                               'FROM sota_experiments WHERE '
                               'sota_experiments_id=%s AND '
                               'claimed_id=%s;')
                        data = (sota_experiments_id,
                                sota_uuid,)
                        cr.execute(sql, data)
                        row = cr.fetchone()
                        if row is not None:
                            msg = '[{}]'.format(json.dumps(row[0]))
                            experiment = objects.build_objects_from_json(message=msg)
                            experiment = experiment[0]
                            experiment.model_experiment_id = copy.deepcopy(row[1])
        except psycopg2.InterfaceError as e:
            self.log.error("psycopg2.InterfaceError: " + str(e.pgerror))
            errormsgs.append("Database connection unavailable, please try again in a few minutes")
            self.reconnect_db()
        except psycopg2.DatabaseError as e:
            self.log.error("psycopg2.DatabaseError: " + str(e.pgerror))
            errormsgs.append("There were errors inserting the SOTA experiment.")
        return experiment

    def get_novelty_indicator_value(self):
        self.log.debug('get_novelty_indicator_value() visibility={} initiated={}'.format(
            self.novelty_visibility, self.novelty_initiated))
        novelty_indicator = None

        # Don't send any info.
        if self.novelty_visibility == 0:
            novelty_indicator = None
        # Send true/false if novelty is initiated.
        elif self.novelty_visibility == 1:
            novelty_indicator = self.novelty_initiated
        return novelty_indicator

    def update_rolling_score(self, solution: dict, prediction: dict):
        score = 0.0
        # Make sure both are lists and not None.
        if isinstance(prediction, dict) and isinstance(solution, dict):
            # We can only grade a valid score if they return the correct value.
            if 'action' in prediction and 'action' in solution:
                if prediction['action'] == solution['action']:
                    score = 1.0
        self.rolling_score.append(score)
        return

    def get_rolling_score(self):
        self.log.debug('get_rolling_score()')
        score = 0.0
        if self.domain_names[self.current_domain] in \
                [objects.DOMAIN_CARTPOLE, objects.DOMAIN_VIZDOOM]:
            score = None
        elif self.episode_data_total > 0:
            score = float(sum(self.rolling_score)) / float(self.episode_data_total)
        return score

    def get_episode_dataset_id(self, episode_id: int, episode_index: int):
        self.log.debug('get_episode_dataset_id({}, {})'.format(episode_id, episode_index))
        dataset_id = -1
        for d_id_key in list(self.episode_cache.keys()):
            if episode_index in self.episode_cache[d_id_key]:
                if self.episode_cache[d_id_key][episode_index]['episode_id'] == episode_id:
                    dataset_id = d_id_key
                    break
        return dataset_id

    def calculate_episode_numbers_for_domain(self, domain_id: int, data_type: str, novelty: int,
                                             difficulty: str, trial_novelty: int, novelty_p: float,
                                             initial_episodes: int, n_zero: int = None,
                                             n_level: int = None, pre_novel_eps: int = None) \
            -> (int, int, int):
        self.log.debug('calculate_episode_numbers_for_domain(domain_id={}, data_type={}, '
                       'novelty={}, difficulty={}, trial_novelty={}, novelty_p={}, '
                       'initial_episodes={}, n_zero={}, n_level={})'.format(
            domain_id,
            data_type,
            novelty,
            difficulty,
            trial_novelty,
            novelty_p,
            initial_episodes,
            n_zero,
            n_level))
        ep_before_novel = 1
        ep_n_level = 1
        ep_n_zero = 1
        num_eps = initial_episodes
        num_n_zero = n_zero
        if num_n_zero is None:
            num_n_zero = self.dataset_cache[domain_id][data_type][objects.NOVELTY_200][
                difficulty][trial_novelty]['episodes']
        num_n_level = n_level
        if num_n_level is None:
            num_n_level = self.dataset_cache[domain_id][data_type][novelty][difficulty][
                trial_novelty]['episodes']
        num_episodes = num_n_zero + num_n_level
        if num_eps > num_episodes:
            num_eps = num_episodes
        valid_size = False
        while not valid_size and num_eps >= 3:
            if pre_novel_eps is not None:
                test_before_novel = pre_novel_eps
            else:
                # Hard coded for release
                test_before_novel = int(num_eps * 0.3)
            test_num_n_l = int((num_eps - test_before_novel) * novelty_p)
            test_num_n_zero = num_eps - test_before_novel - test_num_n_l
            self.log.debug('valid_size={}, num_eps={}, test_before_novel={}, test_num_n_l={}, '
                           'test_num_n_zero={}'.format(str(valid_size),
                                                       num_eps,
                                                       test_before_novel,
                                                       test_num_n_l,
                                                       test_num_n_zero))
            if test_num_n_l <= num_n_level and \
                    (test_before_novel + test_num_n_zero) <= num_n_zero:
                valid_size = True
                ep_before_novel = int(test_before_novel)
                ep_n_level = int(test_num_n_l)
                ep_n_zero = int(test_num_n_zero)
            else:
                num_eps = num_eps - 1
            if self.is_demo:
                valid_size = True
                ep_before_novel = 1
                ep_n_level = 1
                ep_n_zero = 1
        self.log.debug('returning: ep_before_novel={}, ep_n_level={}, ep_n_zero={}'
                       .format(ep_before_novel, ep_n_zero, ep_n_zero))
        return ep_before_novel, ep_n_level, ep_n_zero

    def select_first_episode_index(self, domain_id: int, data_type: str, novelty: int,
                                   difficulty: str, trial_novelty: int, size: int) -> int:
        episode_index = 0
        num_episodes = self.dataset_cache[domain_id][data_type][novelty][difficulty][
            trial_novelty]['episodes'] - 1
        if size < num_episodes:
            num_episodes = num_episodes - size
        episode_index = random.randint(0, num_episodes)
        return episode_index

    def build_sail_on_experiment(self, domain_id: int, data_source: str) -> objects.Experiment:
        self.log.debug('build_sail_on_experiment( ' +
                       'domain_id = {}, '.format(domain_id) +
                       'data_source = {})'.format(data_source))
        if self.is_demo:
            return self.build_demo_sail_on_experiment(domain_id=domain_id,
                                                      data_source=data_source)
        training_seeds = list()
        training_episodes = list()
        episode_indexes = list()
        domain = self.domain_names[domain_id]
        num_episodes = self._ep_by_domain[domain][objects.DTYPE_TRAIN]
        # Build an even split between the different difficulties.
        type_episodes = dict()
        for difficulty in [objects.DIFFICULTY_EASY]:
            type_episodes[difficulty] = int(num_episodes)
        data_type = objects.DTYPE_TRAIN
        if data_source == objects.SOURCE_LIVE:
            data_type = objects.DTYPE_LIVE_TRAIN

        # Build a list of novelties for smartenv to train on.
        training_novelty = list([objects.NOVELTY_101,
                                 objects.NOVELTY_102,
                                 objects.NOVELTY_103])

        # If the domain is not smartenv proceed as normal.
        if domain != objects.DOMAIN_SMARTENV:
            for difficulty in [objects.DIFFICULTY_EASY]:
                if data_source == objects.SOURCE_RECORDED:
                    available_episodes = \
                        self.dataset_cache[domain_id][objects.DTYPE_TRAIN][objects.NOVELTY_200][
                            difficulty][objects.NOVELTY_200]['episodes']
                    episode_indexes = list(range(available_episodes))
                for i in list(range(type_episodes[difficulty])):
                    episode_index = None
                    # Guarantee unique seeds for every training episode.
                    seed = random.randint(0, objects.SEED_NUM_TRAINING)
                    # We only care about this for live training.
                    if data_source == objects.SOURCE_LIVE:
                        while seed in training_seeds:
                            seed = random.randint(0, objects.SEED_NUM_TRAINING)
                        training_seeds.append(seed)
                    else:
                        episode_index = random.choice(episode_indexes)
                        episode_indexes.remove(episode_index)
                    ep = objects.Episode(novelty=objects.NOVELTY_200,
                                         difficulty=difficulty,
                                         seed=seed,
                                         domain=domain,
                                         data_type=data_type,
                                         episode_index=episode_index,
                                         trial_novelty=objects.NOVELTY_200,
                                         use_image=self._image_by_domain[domain])
                    training_episodes.append(copy.deepcopy(ep))
            # Give training_episodes a good shuffle before putting it in the Training object.
            random.shuffle(training_episodes)
        else:
            # Currently all smartenv training will be easy difficulty.
            difficulty = objects.DIFFICULTY_EASY
            # We have a custom training structure for the smartenv domain.
            novelty_eps = list()
            running_total = 0
            for i in list(range(len(training_novelty))):
                novelty_eps.append(list())
                novelty_eps[-1].append(int(num_episodes / len(training_novelty)))
                novelty_eps[-1].append(training_novelty[i])
                running_total += novelty_eps[-1][0]
            # See how many we are above or below the episode count.
            final_diff = running_total - num_episodes
            # Subtract that from the final item in the list.
            novelty_eps[-1][0] = novelty_eps[-1][0] - final_diff
            # Now iterate
            for novelty_eps_count, train_novelty in novelty_eps:
                # Get the first episode index for this novelty.
                episode_index = self.select_first_episode_index(domain_id=domain_id,
                                                                data_type=data_type,
                                                                novelty=objects.NOVELTY_200,
                                                                difficulty=difficulty,
                                                                trial_novelty=train_novelty,
                                                                size=novelty_eps_count)
                for i in list(range(novelty_eps_count)):
                    # Guarantee unique seeds for every training episode.
                    seed = random.randint(0, objects.SEED_NUM_TRAINING)
                    # We only care about this for live training.
                    if data_source == objects.SOURCE_LIVE:
                        while seed in training_seeds:
                            seed = random.randint(0, objects.SEED_NUM_TRAINING)
                        training_seeds.append(seed)
                        episode_index = None
                    ep = objects.Episode(novelty=objects.NOVELTY_200,
                                         difficulty=difficulty,
                                         seed=seed,
                                         domain=domain,
                                         data_type=data_type,
                                         episode_index=episode_index,
                                         trial_novelty=train_novelty,
                                         day_offset=i,
                                         use_image=self._image_by_domain[domain])
                    training_episodes.append(copy.deepcopy(ep))
                    if data_source == objects.SOURCE_RECORDED:
                        episode_index += 1

        for i in range(len(training_episodes)):
            training_episodes[i].trial_episode_index = i
        training = objects.Training(episodes=training_episodes)

        # Build a list of valid novelties to test on.
        testing_novelty = list()
        for n in self._server_novelty:
            if n in objects.TESTING_NOVELTY:
                testing_novelty.append(n)

        novelty_groups = list()
        testing_seeds = list()
        episode_indexes = dict()
        num_episodes = self._ep_by_domain[domain][objects.DTYPE_TEST]
        pre_novel_episodes = self._ep_by_domain[domain]['pre-novel']
        data_type = objects.DTYPE_TEST
        if data_source == objects.SOURCE_LIVE:
            data_type = objects.DTYPE_LIVE_TEST
        else:
            episode_indexes[objects.NOVELTY_200] = dict()
            for d in self._server_difficulty:
                episode_indexes[objects.NOVELTY_200][d] = dict()
                for n in testing_novelty:
                    available_episodes = self.dataset_cache[domain_id][objects.DTYPE_TEST][
                        objects.NOVELTY_200][d][n]['episodes']
                    episode_indexes[objects.NOVELTY_200][d][n] = list(range(available_episodes))
        novelty_diff = list()

        for n in testing_novelty:
            for d in self._server_difficulty:
                novelty_diff.append((n, d))
                if data_source == objects.SOURCE_RECORDED and domain != objects.DOMAIN_SMARTENV:
                    if objects.NOVELTY_200 not in episode_indexes:
                        episode_indexes[objects.NOVELTY_200] = dict()
                    if d not in episode_indexes[objects.NOVELTY_200]:
                        episode_indexes[objects.NOVELTY_200][d] = dict()
                    if n not in episode_indexes:
                        episode_indexes[n] = dict()
                    if d not in episode_indexes[n]:
                        episode_indexes[n][d] = dict()
                    if n not in episode_indexes[objects.NOVELTY_200][d]:
                        size = self.dataset_cache[domain_id][objects.DTYPE_TEST][
                            objects.NOVELTY_200][d][n]['episodes']
                        episode_indexes[objects.NOVELTY_200][d][n] = list(range(size))
                    if n not in episode_indexes[n][d]:
                        size = self.dataset_cache[domain_id][objects.DTYPE_TEST][
                            n][d][n]['episodes']
                        episode_indexes[n][d][n] = list(range(size))

        for novelty_visibility in [0, 1]:
            for novelty, difficulty in novelty_diff:
                # Refresh any needed AMQP heartbeats.
                self.amqp.process_data_events()
                n_zero = None
                n_level = None
                if data_source == objects.SOURCE_LIVE:
                    n_zero = objects.SEED_NUM_TESTING
                    n_level = objects.SEED_NUM_TESTING

                trials = list()
                for t in list(range(self._SAIL_ON_TRIALS)):
                    ep_before_nov, ep_n_level, ep_n_zero = \
                        self.calculate_episode_numbers_for_domain(
                            domain_id=domain_id,
                            data_type=data_type,
                            novelty=novelty,
                            difficulty=difficulty,
                            trial_novelty=novelty,
                            novelty_p=self._testing_novelty_p2,
                            initial_episodes=num_episodes,
                            n_zero=n_zero,
                            n_level=n_level,
                            pre_novel_eps=pre_novel_episodes)
                    episode_index_z = None
                    episode_index_l = None
                    episode_index = None
                    if data_source == objects.SOURCE_RECORDED:
                        if domain == objects.DOMAIN_SMARTENV:
                            episode_index_z = self.select_first_episode_index(
                                domain_id=domain_id,
                                data_type=data_type,
                                novelty=objects.NOVELTY_200,
                                difficulty=difficulty,
                                trial_novelty=novelty,
                                size=ep_before_nov + ep_n_zero)
                            episode_index_l = self.select_first_episode_index(
                                domain_id=domain_id,
                                data_type=data_type,
                                novelty=novelty,
                                difficulty=difficulty,
                                trial_novelty=novelty,
                                size=ep_n_level)
                        else:
                            size = self.dataset_cache[domain_id][objects.DTYPE_TEST][
                                objects.NOVELTY_200][difficulty][novelty]['episodes']
                            episode_indexes[objects.NOVELTY_200][difficulty][novelty] = \
                                list(range(size))
                            size = self.dataset_cache[domain_id][objects.DTYPE_TEST][novelty][
                                difficulty][novelty]['episodes']
                            episode_indexes[novelty][difficulty][novelty] = list(range(size))
                    trial_episodes = list()
                    for i in list(range(ep_before_nov)):
                        # Guarantee unique seeds for every training episode.
                        seed = random.randint(objects.SEED_NUM_TRAINING,
                                              objects.SEED_NUM_TESTING)
                        # We only care about this for live training.
                        if data_source == objects.SOURCE_LIVE:
                            while seed in testing_seeds:
                                seed = random.randint(objects.SEED_NUM_TRAINING,
                                                      objects.SEED_NUM_TESTING)
                            testing_seeds.append(seed)
                        else:
                            if domain == objects.DOMAIN_SMARTENV:
                                episode_index = episode_index_z
                                episode_index_z += 1
                            else:
                                episode_index = random.choice(episode_indexes[objects.NOVELTY_200][
                                                                  difficulty][novelty])
                                episode_indexes[objects.NOVELTY_200][difficulty][
                                    novelty].remove(episode_index)
                        ep = objects.Episode(novelty=objects.NOVELTY_200,
                                             difficulty=difficulty,
                                             seed=seed,
                                             domain=domain,
                                             data_type=data_type,
                                             episode_index=episode_index,
                                             trial_novelty=novelty,
                                             use_image=self._image_by_domain[domain])
                        trial_episodes.append(copy.deepcopy(ep))
                    # Only shuffle the episodes if not smartenv.
                    if domain != objects.DOMAIN_SMARTENV:
                        random.shuffle(trial_episodes)

                    # At this point if the testing_novelty_p2 is greater than 0 we want to
                    # guarantee that the first episode after initiating novelty is always
                    # a novel episode.
                    if self._testing_novelty_p2 > 0.0:
                        # Here we append a single episode of a novelty level at the point where
                        # novelty has been initiated (big red button).
                        episode_index = None
                        # Guarantee unique seeds for every training episode.
                        seed = random.randint(objects.SEED_NUM_TRAINING,
                                              objects.SEED_NUM_TESTING)
                        # We only care about this for live training.
                        if data_source == objects.SOURCE_LIVE:
                            while seed in testing_seeds:
                                seed = random.randint(objects.SEED_NUM_TRAINING,
                                                      objects.SEED_NUM_TESTING)
                            testing_seeds.append(seed)
                        else:
                            if domain == objects.DOMAIN_SMARTENV:
                                episode_index = episode_index_l
                                episode_index_l += 1
                            else:
                                episode_index = random.choice(episode_indexes[novelty][difficulty][
                                                                  novelty])
                                episode_indexes[novelty][difficulty][novelty].remove(episode_index)
                        ep = objects.Episode(novelty=novelty,
                                             difficulty=difficulty,
                                             seed=seed,
                                             domain=domain,
                                             data_type=data_type,
                                             episode_index=episode_index,
                                             trial_novelty=novelty,
                                             use_image=self._image_by_domain[domain])
                        trial_episodes.append(copy.deepcopy(ep))

                    temp_episodes = list()
                    for i in list(range(ep_n_zero)):
                        episode_index = None
                        # Guarantee unique seeds for every training episode.
                        seed = random.randint(objects.SEED_NUM_TRAINING,
                                              objects.SEED_NUM_TESTING)
                        # We only care about this for live training.
                        if data_source == objects.SOURCE_LIVE:
                            while seed in testing_seeds:
                                seed = random.randint(objects.SEED_NUM_TRAINING,
                                                      objects.SEED_NUM_TESTING)
                            testing_seeds.append(seed)
                        else:
                            if domain == objects.DOMAIN_SMARTENV:
                                episode_index = episode_index_z
                                episode_index_z += 1
                            else:
                                episode_index = random.choice(episode_indexes[objects.NOVELTY_200][
                                                                  difficulty][novelty])
                                episode_indexes[objects.NOVELTY_200][difficulty][
                                    novelty].remove(episode_index)
                        ep = objects.Episode(novelty=objects.NOVELTY_200,
                                             difficulty=difficulty,
                                             seed=seed,
                                             domain=domain,
                                             data_type=data_type,
                                             episode_index=episode_index,
                                             trial_novelty=novelty,
                                             use_image=self._image_by_domain[domain])
                        temp_episodes.append(copy.deepcopy(ep))
                    # We remove 1 from ep_n_level for the episode immediately after the big red
                    # button is pressed.  Only do this if ep_n_level is greater than 0 and
                    # self._testing_novelty_p2 is greater than 0.0.
                    if ep_n_level > 0 and self._testing_novelty_p2 > 0.0:
                        ep_n_level = ep_n_level - 1
                    for i in list(range(ep_n_level)):
                        episode_index = None
                        # Guarantee unique seeds for every training episode.
                        seed = random.randint(objects.SEED_NUM_TRAINING,
                                              objects.SEED_NUM_TESTING)
                        # We only care about this for live training.
                        if data_source == objects.SOURCE_LIVE:
                            while seed in testing_seeds:
                                seed = random.randint(objects.SEED_NUM_TRAINING,
                                                      objects.SEED_NUM_TESTING)
                            testing_seeds.append(seed)
                        else:
                            if domain == objects.DOMAIN_SMARTENV:
                                episode_index = episode_index_l
                                episode_index_l += 1
                            else:
                                episode_index = random.choice(episode_indexes[novelty][difficulty][
                                    novelty])
                                episode_indexes[novelty][difficulty][novelty].remove(episode_index)
                        ep = objects.Episode(novelty=novelty,
                                             difficulty=difficulty,
                                             seed=seed,
                                             domain=domain,
                                             data_type=data_type,
                                             episode_index=episode_index,
                                             trial_novelty=novelty,
                                             use_image=self._image_by_domain[domain])
                        temp_episodes.append(copy.deepcopy(ep))
                    # Only shuffle the episodes if not smartenv.
                    if domain != objects.DOMAIN_SMARTENV:
                        random.shuffle(temp_episodes)

                    for ep in temp_episodes:
                        trial_episodes.append(copy.deepcopy(ep))

                    for i in range(len(trial_episodes)):
                        # Iterate through and give day offsets for smartenv domain.
                        if domain == objects.DOMAIN_SMARTENV:
                            trial_episodes[i].day_offset = i
                        # Set the trial_episode_index for all episodes.
                        trial_episodes[i].trial_episode_index = i

                    trial = objects.Trial(episodes=trial_episodes,
                                          novelty=novelty,
                                          novelty_visibility=novelty_visibility,
                                          difficulty=difficulty)
                    trials.append(copy.deepcopy(trial))
                novelty_group = objects.NoveltyGroup(trials=trials)
                novelty_groups.append(copy.deepcopy(novelty_group))

        new_experiment = objects.Experiment(training=training,
                                            novelty_groups=novelty_groups,
                                            budget=self._budget_by_domain[domain])
        return new_experiment

    def build_demo_sail_on_experiment(self, domain_id: int, data_source: str) -> objects.Experiment:
        difficulty = objects.DIFFICULTY_EASY
        novelty = objects.NOVELTY_200
        num_eps = 3
        vis_list = list([0, 1])
        domain = self.domain_names[domain_id]
        new_experiment = None

        if self.is_shortdemo:
            num_eps = 3
            vis_list = list([1])
            training_episodes = list()
            for i in list(range(num_eps)):
                ep_index = None
                data_type = objects.DTYPE_LIVE_TRAIN
                if data_source == objects.SOURCE_RECORDED:
                    ep_index = i
                    data_type = objects.DTYPE_TRAIN
                ep = objects.Episode(novelty=novelty,
                                     difficulty=difficulty,
                                     seed=i,
                                     domain=self.domain_names[domain_id],
                                     data_type=data_type,
                                     episode_index=ep_index,
                                     trial_novelty=i+1,
                                     use_image=self._image_by_domain[domain])
                training_episodes.append(copy.deepcopy(ep))

            for i in range(len(training_episodes)):
                training_episodes[i].trial_episode_index = i
            training = objects.Training(episodes=training_episodes)

            novelty_groups = list()
            novelty_trials = list()

            for visibility in vis_list:
                for j in list(range(num_eps)):
                    trial_episodes = list()
                    for i in list(range(num_eps)):
                        ep_index = None
                        data_type = objects.DTYPE_LIVE_TEST
                        if data_source == objects.SOURCE_RECORDED:
                            ep_index = i
                            data_type = objects.DTYPE_TEST
                        ep = objects.Episode(novelty=novelty,
                                             difficulty=difficulty,
                                             seed=i + 3,
                                             domain=self.domain_names[domain_id],
                                             data_type=data_type,
                                             episode_index=ep_index,
                                             trial_novelty=j+1,
                                             use_image=self._image_by_domain[domain])
                        trial_episodes.append(copy.deepcopy(ep))
                    for i in range(len(trial_episodes)):
                        trial_episodes[i].trial_episode_index = i
                    trial = objects.Trial(episodes=trial_episodes,
                                          novelty=j+1,
                                          novelty_visibility=visibility,
                                          difficulty=difficulty)
                    novelty_trials.append(copy.deepcopy(trial))
            novelty_group = objects.NoveltyGroup(trials=novelty_trials)
            novelty_groups.append(copy.deepcopy(novelty_group))
            new_experiment = objects.Experiment(training=training,
                                                novelty_groups=novelty_groups,
                                                budget=self._budget_by_domain[domain])
        else:
            training_episodes = list()
            for i in list(range(num_eps)):
                ep_index = None
                data_type = objects.DTYPE_LIVE_TRAIN
                if data_source == objects.SOURCE_RECORDED:
                    ep_index = i
                    data_type = objects.DTYPE_TRAIN
                ep = objects.Episode(novelty=novelty,
                                     difficulty=difficulty,
                                     seed=i,
                                     domain=self.domain_names[domain_id],
                                     data_type=data_type,
                                     episode_index=ep_index,
                                     use_image=self._image_by_domain[domain])
                training_episodes.append(copy.deepcopy(ep))
            for i in range(len(training_episodes)):
                training_episodes[i].trial_episode_index = i
            training = objects.Training(episodes=training_episodes)

            novelty_groups = list()
            novelty_trials = list()

            for visibility in vis_list:
                trial_episodes = list()
                for i in list(range(num_eps)):
                    ep_index = None
                    data_type = objects.DTYPE_LIVE_TEST
                    if data_source == objects.SOURCE_RECORDED:
                        ep_index = i
                        data_type = objects.DTYPE_TEST
                    ep = objects.Episode(novelty=novelty,
                                         difficulty=difficulty,
                                         seed=i + 3,
                                         domain=self.domain_names[domain_id],
                                         data_type=data_type,
                                         episode_index=ep_index,
                                         use_image=self._image_by_domain[domain])
                    trial_episodes.append(copy.deepcopy(ep))
                for i in range(len(trial_episodes)):
                    trial_episodes[i].trial_episode_index = i
                trial = objects.Trial(episodes=trial_episodes,
                                      novelty=novelty,
                                      novelty_visibility=visibility,
                                      difficulty=difficulty)
                novelty_trials.append(copy.deepcopy(trial))
            novelty_group = objects.NoveltyGroup(trials=novelty_trials)
            novelty_groups.append(copy.deepcopy(novelty_group))
            new_experiment = objects.Experiment(training=training,
                                                novelty_groups=novelty_groups,
                                                budget=self._budget_by_domain[domain])
        return new_experiment

    def log_ta1_state(self):
        server_state = dict({'is_testing': self.is_testing,
                             'is_demo': self.is_demo,
                             'is_shortdemo': self.is_shortdemo,
                             'TESTING_DATA_SIZE': self._TESTING_DATA_SIZE,
                             'AMQP_EXPERIMENT_TIMEOUT': self._AMQP_EXPERIMENT_TIMEOUT,
                             'TIMEOUT_MULTIPLIER': self._TIMEOUT_MULTIPLIER,
                             'SAIL_ON_TRIALS': self._SAIL_ON_TRIALS,
                             'DATA_CACHE_SIZE': self._DATA_CACHE_SIZE,
                             'DATA_CACHE_RELOAD': self._DATA_CACHE_RELOAD,
                             'training_novelty_p1': self._training_novelty_p1,
                             'testing_novelty_p2': self._testing_novelty_p2,
                             'episodes_by_domain': self._ep_by_domain,
                             'budget_by_domain': self._budget_by_domain,
                             'image_by_domain': self._image_by_domain,
                             'is_domain_live': self._is_domain_live,
                             'server_novelty': self._server_novelty,
                             'version': objects.__version__,
                             'exper_no_testing': self._exper_no_testing,
                             'exper_just_one_trial': self._exper_just_one_trial})
        self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                        action='server_state',
                                        data_object=server_state,
                                        experiment_trial_id=self.experiment_trial_id))
        return

    def setup_aiq_experiment(self, model: objects.Model, request: objects.RequestExperiment,
                             errormsgs: list):
        experiment_response = None
        self.experiment_type = objects.TYPE_EXPERIMENT_AIQ
        self.novelty_visibility = request.novelty_visibility
        self._TEST_WINDOW_PROGRESS = 0
        self.rolling_score = list()
        self.STATE = objects.BenchmarkRequest(benchmark_script='BENCHMARKING SCRIPT GOES HERE.')

        if len(errormsgs) == 0:
            # Insert the experiment into the database.
            experiment_response = self.handle_experiment_request(experiment_request=request,
                                                                 new_model=model,
                                                                 vhost=self.amqp_vhost,
                                                                 errormsgs=errormsgs)
            # Save the model_experiment_id. We need that for trials.
            self.model_experiment_id = experiment_response.model_experiment_id

        if len(errormsgs) == 0:
            # Insert a new trial in the database.
            self.experiment_trial = 0
            self.experiment_trial_id = self.handle_experiment_trial(
                model_experiment_id=int(self.model_experiment_id),
                trial=self.experiment_trial,
                novelty=self.novelty_level,
                novelty_visibility=self.novelty_visibility,
                novelty_description=dict(),
                errormsgs=errormsgs)

        if len(errormsgs) == 0:
            # Set the experiment domains.
            self.set_experiment_domains(experiment_request=request,
                                        experiment_response=experiment_response,
                                        domain_id_dict=self.domain_ids,
                                        errormsgs=errormsgs)

        if len(errormsgs) == 0:
            # Things have gone well. Setup a new RPC queue just for this experiment and stop
            # listening to the other "general" queues.
            self.private_queue = objects.SERVER_RPC_QUEUE + '.{}'.format(uuid.uuid4().hex)
            experiment_response.server_rpc_queue = self.private_queue
            self.amqp.setup_subscribe_to_queue(
                queue_name=self.private_queue,
                queue_exclusive=True,
                queue_auto_delete=True,
                casas_events=True,
                callback_function=self.on_aiq_request,
                callback_full_params=True)
            self.unsubscribe_experiment_queue()
            self.unsubscribe_sota_queue()
        return experiment_response

    def setup_sail_on_experiment(self, model: objects.Model, request: objects.RequestExperiment,
                                 errormsgs: list):
        experiment_response = None
        self.experiment_type = objects.TYPE_EXPERIMENT_SAIL_ON
        self.novelty_visibility = 0
        self.novelty_vis_index = 0
        self.rolling_score = list()
        self.STATE = objects.BenchmarkRequest(benchmark_script='BENCHMARKING SCRIPT GOES HERE.')

        if len(errormsgs) == 0:
            # Insert the experiment into the database.
            experiment_response = self.handle_experiment_request(experiment_request=request,
                                                                 new_model=model,
                                                                 vhost=self.amqp_vhost,
                                                                 errormsgs=errormsgs)
            # Save the model_experiment_id. We need that for trials.
            self.model_experiment_id = experiment_response.model_experiment_id
            self.sota_client_ex_req = copy.deepcopy(request)
            self.sota_client_ex_response = copy.deepcopy(experiment_response)

        if len(errormsgs) == 0:
            # Insert a new trial in the database.
            # Training is an even split between all 3 difficulties, so we will mark it as medium.
            self.experiment_trial_id = self.handle_experiment_trial(
                model_experiment_id=int(self.model_experiment_id),
                trial=-1,
                novelty=objects.NOVELTY_200,
                novelty_visibility=self.novelty_visibility,
                difficulty=objects.DIFFICULTY_MEDIUM,
                novelty_description=dict(),
                errormsgs=errormsgs)

            # Start the created training (-1) experiment_trial.
            self.start_experiment_trial(experiment_trial_id=self.experiment_trial_id,
                                        errormsgs=errormsgs)
            self.clear_abandoned_trials(errormsgs=errormsgs)

        if len(errormsgs) == 0:
            # Set the experiment domain.
            self.set_experiment_domains(experiment_request=request,
                                        experiment_response=experiment_response,
                                        domain_id_dict=self.domain_ids,
                                        errormsgs=errormsgs)

        if len(errormsgs) == 0:
            # Things have gone well. Setup a new RPC queue just for this experiment and stop
            # listening to the other "general" queues.
            self.private_queue = objects.SERVER_RPC_QUEUE + '.{}'.format(uuid.uuid4().hex)
            experiment_response.server_rpc_queue = self.private_queue
            self.amqp.setup_subscribe_to_queue(
                queue_name=self.private_queue,
                queue_exclusive=True,
                queue_auto_delete=True,
                casas_events=True,
                callback_function=self.on_sail_on_request,
                callback_full_params=True)
            self.unsubscribe_experiment_queue()
            self.unsubscribe_sota_queue()
        return experiment_response

    def on_experiment_request(self, ch, method, props, body, request):
        self.log.info('on_experiment_request( {} )'.format(str(request)))
        errormsgs = list()
        experiment_response = None
        response = objects.CasasResponse(status='success',
                                         response_type='data',
                                         error_message='No Errors')

        if isinstance(request, objects.RequestExperiment) and \
                not isinstance(request, objects.RequestExperimentTrials):
            model = None
            user_id = self.handle_user(aiq_username=request.model.aiq_username,
                                       aiq_secret=request.model.aiq_secret,
                                       errormsgs=errormsgs)
            if len(errormsgs) == 0:
                model_request = objects.RequestModel(aiq_username=request.model.aiq_username,
                                                     aiq_secret=request.model.aiq_secret,
                                                     model_name=request.model.model_name,
                                                     organization=request.model.organization)
                model = self.handle_model(model_request=model_request,
                                          user_id=user_id,
                                          errormsgs=errormsgs)

            if len(errormsgs) == 0:
                self.build_domain_cache(request=request,
                                        errormsgs=errormsgs)

            if len(errormsgs) == 0:
                # Refresh any needed AMQP heartbeats.
                self.amqp.process_data_events()
                self.build_dataset_cache(request=request,
                                         errormsgs=errormsgs)
                self.current_domain = self.domain_cache[0]
                self.novelty_initiated = False
                self.novelty_visibility = request.novelty_visibility
                self.novelty_vis_index = 0

            if len(errormsgs) == 0:
                if request.experiment_type == objects.TYPE_EXPERIMENT_AIQ:
                    errormsgs.append('This experiment type is temporarily disabled.')
                    # experiment_response = self.setup_aiq_experiment(model=model,
                    #                                                 request=request,
                    #                                                 errormsgs=errormsgs)
                elif request.experiment_type == objects.TYPE_EXPERIMENT_SAIL_ON:
                    experiment_response = self.setup_sail_on_experiment(model=model,
                                                                        request=request,
                                                                        errormsgs=errormsgs)

            if len(errormsgs) == 0 and request.experiment_type == objects.TYPE_EXPERIMENT_SAIL_ON:
                for domain in list(request.domain_dict.keys()):
                    # Only process the domain we want.
                    if not request.domain_dict[domain]:
                        continue
                    domain_id = self.domain_ids[domain]

                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    experiment = self.build_sail_on_experiment(
                        domain_id=domain_id,
                        data_source=self._domain_data_source[domain])

                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    if not self.is_demo:
                        # Don't generate requests for SOTA on demo experiments.
                        self.insert_sota_experiment(domain_id=domain_id,
                                                    model_experiment_id=self.model_experiment_id,
                                                    experiment=experiment,
                                                    vhost=self.amqp_vhost,
                                                    errormsgs=errormsgs)
                    self._experiment = experiment
                    self._exper_train_index = 0
                    self._exper_novelty_index = 0
                    self._exper_trial_index = 0
                    self._exper_episode_index = 0
                    self._exper_end_training_early = False
                    self._exper_end_experiment_early = False
                    self._exper_no_testing = request.no_testing
                    self._exper_no_training = False
                    self._exper_just_one_trial = False

                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    self.add_training_episodes(experiment_trial_id=self.experiment_trial_id,
                                               num_episodes=len(self._experiment.training.episodes),
                                               errormsgs=errormsgs)

                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    # Rebuild the dataset cache with what the experiment needs.
                    self.build_dataset_cache(request=request,
                                             experiment=self._experiment,
                                             errormsgs=errormsgs)

                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    # Save the experiment JSON in the model_experiment table.
                    self.add_json_to_model_experiment(model_experiment_id=self.model_experiment_id,
                                                      experiment=self._experiment,
                                                      errormsgs=errormsgs)

                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    # Populate the experiment_trials for this experiment.
                    self.add_all_experiment_trials(model_experiment_id=self.model_experiment_id,
                                                   experiment=self._experiment,
                                                   errormsgs=errormsgs)
        elif isinstance(request, objects.RequestExperimentTrials):
            # Things we must check on this request:
            # - Valid user.
            # - The user's model.
            # - Valid experiment for the user's model.
            # - Experiment in the same vhost.
            # - Experiment is not complete already.
            model = None
            user_id = self.handle_user(aiq_username=request.model.aiq_username,
                                       aiq_secret=request.model.aiq_secret,
                                       errormsgs=errormsgs)
            if len(errormsgs) == 0:
                model_request = objects.RequestModel(aiq_username=request.model.aiq_username,
                                                     aiq_secret=request.model.aiq_secret,
                                                     model_name=request.model.model_name,
                                                     organization=request.model.organization)
                model = self.handle_model(model_request=model_request,
                                          user_id=user_id,
                                          insert_data=False,
                                          errormsgs=errormsgs)
                # If we didn't put an entry in errormsgs, that means the model is valid for
                # the user we have provided.

            if len(errormsgs) == 0:
                self.build_domain_cache(request=request,
                                        errormsgs=errormsgs)

            if len(errormsgs) == 0:
                # Refresh any needed AMQP heartbeats.
                self.amqp.process_data_events()

                self.build_dataset_cache(request=request,
                                         errormsgs=errormsgs)
                self.current_domain = self.domain_cache[0]
                self.novelty_initiated = False
                self.novelty_visibility = request.novelty_visibility
                self.novelty_vis_index = 0

            if len(errormsgs) == 0:
                self.experiment_type = objects.TYPE_EXPERIMENT_SAIL_ON
                self.novelty_visibility = 0
                self.novelty_vis_index = 0
                self.rolling_score = list()
                self.STATE = objects.BenchmarkRequest(
                    benchmark_script='BENCHMARKING SCRIPT GOES HERE.')

                # Here we should check if the experiment exists for the model,
                # if it is for the same vhost, and if it is not complete.
                self.model_experiment_id = self.get_model_experiment_id_for_work(
                    domain_id=self.current_domain,
                    vhost=self.amqp_vhost,
                    model=model,
                    request=request,
                    errormsgs=errormsgs)

            if len(errormsgs) == 0 and self.model_experiment_id is not None:
                # Refresh any needed AMQP heartbeats.
                self.amqp.process_data_events()

                self._experiment = self.get_model_experiment_json(
                    model_experiment_id=self.model_experiment_id,
                    errormsgs=errormsgs)
                self._exper_train_index = 0
                self._exper_novelty_index = 0
                self._exper_trial_index = 0
                self._exper_episode_index = 0
                self._exper_end_training_early = False
                self._exper_end_experiment_early = False
                self._exper_no_testing = False
                self._exper_no_training = True
                self._exper_just_one_trial = request.just_one_trial

            if len(errormsgs) == 0:
                # Refresh any needed AMQP heartbeats.
                self.amqp.process_data_events()

                # Rebuild the dataset cache with what the experiment needs.
                self.build_dataset_cache(request=request,
                                         experiment=self._experiment,
                                         errormsgs=errormsgs)

            if len(errormsgs) == 0:
                # Things have gone well. Setup a new RPC queue just for this experiment and stop
                # listening to the other "general" queues.
                self.private_queue = objects.SERVER_RPC_QUEUE + '.{}'.format(uuid.uuid4().hex)
                self.amqp.setup_subscribe_to_queue(
                    queue_name=self.private_queue,
                    queue_exclusive=True,
                    queue_auto_delete=True,
                    casas_events=True,
                    callback_function=self.on_sail_on_request,
                    callback_full_params=True)
                self.unsubscribe_experiment_queue()
                self.unsubscribe_sota_queue()
                experiment_response = objects.ExperimentResponse(
                    server_rpc_queue=self.private_queue,
                    experiment_secret=request.experiment_secret,
                    model_experiment_id=self.model_experiment_id,
                    experiment_timeout=self._AMQP_EXPERIMENT_TIMEOUT)
        else:
            errormsgs.append('This queue is only for requesting to start an experiment.')

        if len(errormsgs) > 0:
            response.add_error(
                casas_error=objects.CasasError(
                    error_type='error',
                    message='There were errors processing part or all of '
                            'your request, please see errors for details.',
                    error_dict=dict({'errors': errormsgs})))
            for msg in errormsgs:
                self.log.debug(msg)
        else:
            self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                            action=request.obj_type,
                                            data_object=request.get_json_obj(),
                                            experiment_trial_id=self.experiment_trial_id))
            self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                            action=objects.EXPERIMENT_RESP,
                                            data_object=experiment_response.get_json_obj(),
                                            experiment_trial_id=self.experiment_trial_id))
            self.log_ta1_state()

        if props.reply_to is not None:
            if response.status == 'error':
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=response,
                                           correlation_id=props.correlation_id)
            elif experiment_response is not None:
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=experiment_response,
                                           correlation_id=props.correlation_id)
                self._AMQP_EXP_CALLBACK_ID = self.amqp.call_later(
                    seconds=self._AMQP_EXPERIMENT_TIMEOUT,
                    function=self.force_end_experiment)
        return

    def on_sota_register_request(self, ch, method, props, body, request):
        self.log.debug('on_sota_register_request()')
        response = objects.SotaIdle()
        errormsgs = list()

        if isinstance(request, objects.RequestExperiment) and \
                not isinstance(request, objects.RequestExperimentTrials):
            # First check that the request is not too old.
            is_valid = True
            max_delta = 4.0
            if abs(time.time() - request.epoch) > max_delta:
                is_valid = False

            if is_valid:
                self.log.info('on_sota_register_request({})'.format(str(request)))

            # Validate the username/secret trying to register.
            if request.model.aiq_username == self._sota_username and \
                    request.model.aiq_secret == self._sota_secret and is_valid:
                sota_domain = None
                for domain in list(request.domain_dict.keys()):
                    if request.domain_dict[domain]:
                        sota_domain = domain

                if sota_domain is None:
                    errormsgs.append('There was no provided domain.')

                if len(errormsgs) == 0:
                    self.build_domain_cache(request=request,
                                            errormsgs=errormsgs)

                if len(errormsgs) == 0:
                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    self.build_dataset_cache(request=request,
                                             errormsgs=errormsgs)
                    self.current_domain = self.domain_cache[0]
                    self.novelty_initiated = False
                    self.novelty_visibility = 0
                    self.novelty_vis_index = 0
                    self.rolling_score = list()

                experiment = None
                model = None
                ex_request = None
                if len(errormsgs) == 0:
                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    experiment = self.get_sota_experiment(
                        domain_id=self.domain_ids[sota_domain],
                        vhost=self.amqp_vhost,
                        errormsgs=errormsgs)

                if len(errormsgs) == 0 and experiment is not None:
                    self._experiment = experiment
                    self._exper_train_index = 0
                    self._exper_novelty_index = 0
                    self._exper_trial_index = 0
                    self._exper_episode_index = 0
                    self._exper_end_training_early = False
                    self._exper_end_experiment_early = False
                    self._exper_no_testing = request.no_testing
                    self._exper_no_training = False
                    self._exper_just_one_trial = False

                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    # Rebuild the dataset cache with what the experiment needs.
                    self.build_dataset_cache(request=request,
                                             experiment=self._experiment,
                                             errormsgs=errormsgs)

                    # Get the user_id of the client.
                    user_id, c_name, c_secret, c_organization = self.get_experiment_user_id(
                        model_experiment_id=experiment.model_experiment_id,
                        errormsgs=errormsgs)
                    model_request = objects.RequestModel(
                        aiq_username=c_name,
                        aiq_secret=c_secret,
                        model_name='SOTA_{}'.format(sota_domain),
                        organization=c_organization)

                    if len(errormsgs) == 0:
                        # Insert the model in the db if needed and return the object.
                        model = self.handle_model(model_request=model_request,
                                                  user_id=user_id,
                                                  errormsgs=errormsgs)

                    if len(errormsgs) == 0:
                        # Let's create the SOTA experiment object in the database.
                        self.novelty_visibility = 0
                        ex_request = objects.RequestExperiment(
                            model=model,
                            novelty=objects.NOVELTY_200,
                            novelty_visibility=0,
                            client_rpc_queue='',
                            git_version=objects.__version__,
                            experiment_type=objects.TYPE_EXPERIMENT_SAIL_ON,
                            seed=None,
                            domain_dict=request.domain_dict)
                        response = self.handle_experiment_request(
                            experiment_request=ex_request,
                            new_model=model,
                            vhost=self.amqp_vhost,
                            errormsgs=errormsgs)

                    if len(errormsgs) == 0:
                        # Refresh any needed AMQP heartbeats.
                        self.amqp.process_data_events()

                        # Add the SOTA model_experiment_id to the client's.
                        self.model_experiment_id = response.model_experiment_id
                        self.add_sota_to_experiment(
                            model_experiment_id=experiment.model_experiment_id,
                            sota_model_experiment_id=self.model_experiment_id,
                            errormsgs=errormsgs)

                    if len(errormsgs) == 0:
                        # Save the experiment JSON in the model_experiment table.
                        self.add_json_to_model_experiment(
                            model_experiment_id=self.model_experiment_id,
                            experiment=self._experiment,
                            errormsgs=errormsgs)

                    if len(errormsgs) == 0:
                        # Refresh any needed AMQP heartbeats.
                        self.amqp.process_data_events()

                        # Populate the experiment_trials for this experiment.
                        self.add_all_experiment_trials(
                            model_experiment_id=self.model_experiment_id,
                            experiment=self._experiment,
                            errormsgs=errormsgs)

                    if len(errormsgs) == 0:
                        # Refresh any needed AMQP heartbeats.
                        self.amqp.process_data_events()

                        # Insert a new trial in the database.
                        # Training is an even split between all 3 difficulties, so we will
                        # mark it as medium.
                        self.experiment_trial_id = self.handle_experiment_trial(
                            model_experiment_id=self.model_experiment_id,
                            trial=-1,
                            novelty=objects.NOVELTY_200,
                            novelty_visibility=self.novelty_visibility,
                            difficulty=objects.DIFFICULTY_MEDIUM,
                            novelty_description=dict(),
                            errormsgs=errormsgs)

                        self.add_training_episodes(
                            experiment_trial_id=self.experiment_trial_id,
                            num_episodes=len(self._experiment.training.episodes),
                            errormsgs=errormsgs)

                        # Start the created training (-1) experiment_trial.
                        self.start_experiment_trial(experiment_trial_id=self.experiment_trial_id,
                                                    errormsgs=errormsgs)

                        # Refresh any needed AMQP heartbeats.
                        self.amqp.process_data_events()

                        self.clear_abandoned_trials(errormsgs=errormsgs)

                    if len(errormsgs) == 0:
                        # Set the experiment domain.
                        self.set_experiment_domains(experiment_request=ex_request,
                                                    experiment_response=response,
                                                    domain_id_dict=self.domain_ids,
                                                    errormsgs=errormsgs)

                    if len(errormsgs) == 0:
                        # Things have gone well.  Set state ready for benchmark.
                        self.STATE = objects.BenchmarkRequest(
                            benchmark_script='BENCHMARKING SCRIPT GOES HERE.')

                        # Setup a new RPC queue just for this experiment and stop listening to
                        # the other general queues used for requesting to start.
                        self.private_queue = objects.SERVER_RPC_QUEUE + '.{}'.format(
                            uuid.uuid4().hex)
                        response.server_rpc_queue = self.private_queue
                        self.amqp.setup_subscribe_to_queue(
                            queue_name=self.private_queue,
                            queue_exclusive=True,
                            queue_auto_delete=True,
                            casas_events=True,
                            callback_function=self.on_sail_on_request,
                            callback_full_params=True)
                        self.unsubscribe_experiment_queue()
                        self.unsubscribe_sota_queue()

                        if self._AMQP_EXP_CALLBACK_ID is not None:
                            self.amqp.cancel_call_later(
                                timeout_id=self._AMQP_EXP_CALLBACK_ID)
                        self._AMQP_EXP_CALLBACK_ID = self.amqp.call_later(
                            seconds=self._AMQP_EXPERIMENT_TIMEOUT,
                            function=self.force_end_experiment)
        elif isinstance(request, objects.RequestExperimentTrials):
            # First check that the request is not too old.
            is_valid = True
            max_delta = 4.0
            if abs(time.time() - request.epoch) > max_delta:
                is_valid = False

            if is_valid:
                self.log.info('on_sota_register_request({})'.format(str(request)))

            # Things we must check on this request:
            # - Valid user.
            # - The user's model.
            # - Valid experiment for the user's model.
            # - Experiment in the same vhost.
            # - Experiment is not complete already.
            # 1) Check if experiment actually exists.
            # 2) Check if model is SOTA and actually exists.
            # 3) Check if experiment belongs to SOTA model, is valid for the current vhost,
            #    and is not complete.

            # Validate the username/secret trying to register.
            if request.model.aiq_username == self._sota_username and \
                    request.model.aiq_secret == self._sota_secret and is_valid:
                sota_domain = None
                for domain in list(request.domain_dict.keys()):
                    if request.domain_dict[domain]:
                        sota_domain = domain

                if sota_domain is None:
                    errormsgs.append('There was no provided domain.')

                if len(errormsgs) == 0:
                    self.build_domain_cache(request=request,
                                            errormsgs=errormsgs)

                if len(errormsgs) == 0:
                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    self.build_dataset_cache(request=request,
                                             errormsgs=errormsgs)
                    self.current_domain = self.domain_cache[0]
                    self.novelty_initiated = False
                    self.novelty_visibility = 0
                    self.novelty_vis_index = 0
                    self.rolling_score = list()

                experiment = None
                model = None
                ex_request = None
                model_ex_id = None

                if len(errormsgs) == 0:
                    model_ex_id = self.get_model_experiment_id_from_secret(
                        vhost=self.amqp_vhost,
                        request=request,
                        errormsgs=errormsgs)

                if len(errormsgs) == 0:
                    # Get the user_id of the client.
                    user_id, c_name, c_secret, c_organization = self.get_experiment_user_id(
                        model_experiment_id=model_ex_id,
                        errormsgs=errormsgs)
                    model_request = objects.RequestModel(
                        aiq_username=c_name,
                        aiq_secret=c_secret,
                        model_name='SOTA_{}'.format(sota_domain),
                        organization=c_organization)
                    model = self.handle_model(model_request=model_request,
                                              user_id=user_id,
                                              insert_data=False,
                                              errormsgs=errormsgs)
                    # If we didn't put an entry in errormsgs, that means the model is valid for
                    # the user we have provided.

                if len(errormsgs) == 0:
                    self.experiment_type = objects.TYPE_EXPERIMENT_SAIL_ON
                    # Here we should check if the experiment exists for the model,
                    # if it is for the same vhost, and if it is not complete.
                    self.model_experiment_id = self.get_model_experiment_id_for_work(
                        domain_id=self.current_domain,
                        vhost=self.amqp_vhost,
                        model=model,
                        request=request,
                        errormsgs=errormsgs)

                if len(errormsgs) == 0 and self.model_experiment_id is not None:
                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    self._experiment = self.get_model_experiment_json(
                        model_experiment_id=self.model_experiment_id,
                        errormsgs=errormsgs)
                    self._exper_train_index = 0
                    self._exper_novelty_index = 0
                    self._exper_trial_index = 0
                    self._exper_episode_index = 0
                    self._exper_end_training_early = False
                    self._exper_end_experiment_early = False
                    self._exper_no_testing = False
                    self._exper_no_training = True
                    self._exper_just_one_trial = request.just_one_trial

                    # Refresh any needed AMQP heartbeats.
                    self.amqp.process_data_events()

                    # Rebuild the dataset cache with what the experiment needs.
                    self.build_dataset_cache(request=request,
                                             experiment=self._experiment,
                                             errormsgs=errormsgs)

                if len(errormsgs) == 0:
                    # Things have gone well.  Set state ready for benchmark.
                    self.STATE = objects.BenchmarkRequest(
                        benchmark_script='BENCHMARKING SCRIPT GOES HERE.')

                    # Setup a new RPC queue just for this experiment and stop listening to
                    # the other general queues used for requesting to start.
                    self.private_queue = objects.SERVER_RPC_QUEUE + '.{}'.format(
                        uuid.uuid4().hex)
                    self.amqp.setup_subscribe_to_queue(
                        queue_name=self.private_queue,
                        queue_exclusive=True,
                        queue_auto_delete=True,
                        casas_events=True,
                        callback_function=self.on_sail_on_request,
                        callback_full_params=True)
                    self.unsubscribe_experiment_queue()
                    self.unsubscribe_sota_queue()
                    response = objects.ExperimentResponse(
                        server_rpc_queue=self.private_queue,
                        experiment_secret=request.experiment_secret,
                        model_experiment_id=self.model_experiment_id,
                        experiment_timeout=self._AMQP_EXPERIMENT_TIMEOUT)

                    if self._AMQP_EXP_CALLBACK_ID is not None:
                        self.amqp.cancel_call_later(
                            timeout_id=self._AMQP_EXP_CALLBACK_ID)
                    self._AMQP_EXP_CALLBACK_ID = self.amqp.call_later(
                        seconds=self._AMQP_EXPERIMENT_TIMEOUT,
                        function=self.force_end_experiment)

        err_response = None
        if len(errormsgs) > 0:
            err_response = objects.CasasResponse(status='success',
                                                 response_type='data',
                                                 error_message='No Errors')
            err_response.add_error(
                casas_error=objects.CasasError(
                    error_type='error',
                    message='There were errors processing part or all of '
                            'your request, please see errors for details.',
                    error_dict=dict({'errors': errormsgs})))
            for msg in errormsgs:
                self.log.debug(msg)
        elif not isinstance(response, objects.SotaIdle):
            # It went well and we are starting an experiment for SOTA.
            self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                            action=request.obj_type,
                                            data_object=request.get_json_obj(),
                                            experiment_trial_id=self.experiment_trial_id))
            self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                            action=objects.EXPERIMENT_RESP,
                                            data_object=response.get_json_obj(),
                                            experiment_trial_id=self.experiment_trial_id))
            self.log_ta1_state()

        if props.reply_to is not None:
            if len(errormsgs) == 0:
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=response,
                                           correlation_id=props.correlation_id)
            else:
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=err_response,
                                           correlation_id=props.correlation_id)
        return

    """
    def on_aiq_request(self, ch, method, props, body, request):
        self.log.debug('on_aiq_request( {} )'.format(str(request)))
        errormsgs = list()
        data = None
        refresh_dataset_cache = False
        response = objects.CasasResponse(status='success',
                                         response_type='data',
                                         error_message='No Errors')

        if self._AMQP_EXP_CALLBACK_ID is not None:
            self.amqp.cancel_call_later(timeout_id=self._AMQP_EXP_CALLBACK_ID)
            self._AMQP_EXP_CALLBACK_ID = None

        # AIQ states sent back:
        # - objects.ExperimentResponse
        # - objects.BenchmarkRequest
        # - objects.ExperimentStart
        # - for d in domains:
        #     - objects.TrialStart(d)
        #     - objects.TrainingStart
        #     - for e in episodes:
        #         - object.TrainingEpisodeStart
        #         - Client then requests objects.TrainingData, and responds with
        #           objects.TrainingDataPrediction. This repeats until we send an
        #           objects.TrainingEpisodeEnd response instead of the usual ack object back.
        #     - objects.TrainingEnd
        #     - objects.TestingStart
        #     - for e in episodes:
        #         - object.TrainingEpisodeStart
        #         - Client then requests objects.TestingData, and response with
        #           objects.TestingDataPrediction. This repeats until we send an
        #           objects.TestingEpisodeEnd response instead of an objects.TestingDataAck.
        #     - objects.TestingEnd
        #     - objects.TrialEnd
        # - objects.ExperimentEnd

        if isinstance(request, objects.RequestState):
            data = copy.deepcopy(self.STATE)
            self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                            action=objects.REQ_STATE,
                                            data_object=data.get_json_obj()))
            if isinstance(self.STATE, objects.BenchmarkRequest):
                self.STATE = objects.ExperimentStart()
            elif isinstance(self.STATE, objects.ExperimentStart):
                self.STATE = objects.TrialStart(
                    trial_number=self.experiment_trial,
                    total_trials=len(self.domain_cache),
                    message=self.dataset_cache[self.current_domain]['train'][0]['domain'])
            elif isinstance(self.STATE, objects.TrialStart):
                self.STATE = objects.TrainingStart()
                domain = self.domain_names[self.current_domain]
                self._training_episodes = self._ep_by_domain[domain]['train']
                self._testing_episodes = self._ep_by_domain[domain]['test']
            elif isinstance(self.STATE, objects.TrainingStart):
                # Build the list of episode_ids we will be using to train.
                # get the dataset_id and number of training episodes.
                train_size = self._training_episodes
                num_episodes = self.dataset_cache[self.current_domain]['train'][0]['episodes']
                dataset_id = self.dataset_cache[self.current_domain]['train'][0]['dataset_id']
                if train_size > num_episodes:
                    train_size = num_episodes

                # Reset the episode_id_list and episode_index_cache so we can populate it.
                del self.episode_id_list
                self.episode_id_list = list()
                self.episode_id_list_index = 0
                del self.episode_index_cache
                self.episode_index_cache = dict()

                # Get a random sample of episode indexes from the dataset.
                episode_list = random.sample(range(num_episodes), train_size)
                if self.is_demo:
                    episode_list = list([0, 1, 2])
                random.shuffle(episode_list)

                # Populate the episode_id_list with the episode_id values.
                for episode_index in episode_list:
                    self.get_episode_ids(dataset_id=dataset_id,
                                         episode_index=episode_index,
                                         errormsgs=errormsgs)
                    episode_id = self.episode_cache[dataset_id][episode_index]['episode_id']
                    self.episode_id_list.append(episode_id)
                    self.episode_index_cache[episode_id] = episode_index

                # Get the first episode_id to train and load it from the database.
                episode_id = self.episode_id_list[self.episode_id_list_index]
                episode_index = self.episode_index_cache[episode_id]
                # Set the current data_index for the episode to 0.
                self.episode_cache[dataset_id][episode_index]['data_index'] = 0
                # Load the episode data to the data_cache.
                self.load_data_to_cache(
                    episode_id=episode_id,
                    at_data_index=0,
                    errormsgs=errormsgs)
                self.STATE = objects.TrainingEpisodeStart(
                    episode_number=self.episode_id_list_index,
                    total_episodes=len(self.episode_id_list))
            elif isinstance(self.STATE, objects.TrainingEpisodeStart):
                self.STATE = objects.TrainingEpisodeActive()
                # Get the next episode_id, episode_index, and dataset_id for the episode.
                episode_id = self.episode_id_list[self.episode_id_list_index]
                episode_index = self.episode_index_cache[episode_id]
                dataset_id = self.get_episode_dataset_id(episode_id=episode_id,
                                                         episode_index=episode_index)
                # Set the current data_index for the episode to 0.
                self.episode_cache[dataset_id][episode_index]['data_index'] = 0
                # Load the episode data to the data_cache.
                self.load_data_to_cache(
                    episode_id=episode_id,
                    at_data_index=0,
                    errormsgs=errormsgs)
            elif isinstance(self.STATE, objects.TrainingEnd):
                self.STATE = objects.TestingStart()
            elif isinstance(self.STATE, objects.TestingStart):
                self._TEST_EPISODE_PROGRESS = -1
                # Update the episode numbers for this domain.
                ep_b_n, ep_n_l, ep_n_z = self.calculate_episode_numbers_for_domain(
                    domain_id=self.current_domain,
                    data_type='test',
                    novelty=self.novelty_level,
                    novelty_p=0.0,
                    initial_episodes=self._testing_episodes)
                self._TEST_EPISODE_BEFORE_NOVEL = ep_b_n
                self._TEST_NUM_N_L = ep_n_l
                self._TEST_NUM_N_ZERO = ep_n_z
                server_state = dict({'trial_number': self.experiment_trial,
                                     'TEST_NUM_BEFORE_NOVEL': self._TEST_EPISODE_BEFORE_NOVEL,
                                     'TEST_NUM_n0_AFTER_NOVEL': self._TEST_NUM_N_ZERO,
                                     'TEST_NUM_nL_AFTER_NOVEL': self._TEST_NUM_N_L})
                self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                                action='server_state_update',
                                                data_object=server_state))
                # Build the list of episode_ids we will be using to test.
                # Get the dataset_id and number of testing episodes.
                n_level = self.novelty_level
                dset_id_z = self.dataset_cache[self.current_domain]['test'][0]['dataset_id']
                num_ep_z = self.dataset_cache[self.current_domain]['test'][0]['episodes']
                eps_z = list(range(num_ep_z))
                dset_id_n = self.dataset_cache[self.current_domain]['test'][n_level]['dataset_id']
                num_ep_n = self.dataset_cache[self.current_domain]['test'][n_level]['episodes']
                eps_n = list(range(num_ep_n))

                # Reset the episode_id_list and episode_index_cache so we can populate it.
                del self.episode_id_list
                self.episode_id_list = list()
                self.episode_id_list_index = 0
                del self.episode_index_cache
                self.episode_index_cache = dict()

                # Get a random sample of episode indexes from the dataset.
                episode_list = random.sample(eps_z, self._TEST_EPISODE_BEFORE_NOVEL)
                random.shuffle(episode_list)

                # Remove those chosen from the current list of n0.
                for ep_idx in episode_list:
                    eps_z.remove(ep_idx)

                # Populate the episode_id_list with the episode_id values.
                for episode_index in episode_list:
                    self.get_episode_ids(dataset_id=dset_id_z,
                                         episode_index=episode_index,
                                         errormsgs=errormsgs)
                    episode_id = self.episode_cache[dset_id_z][episode_index]['episode_id']
                    self.episode_id_list.append(episode_id)
                    self.episode_index_cache[episode_id] = episode_index

                # Get the novel episodes we will mix with non-novel episodes.
                episode_list_n = random.sample(eps_n, self._TEST_NUM_N_L)
                random.shuffle(episode_list_n)
                episode_list_z = random.sample(eps_z, self._TEST_NUM_N_ZERO)
                random.shuffle(episode_list_z)

                episode_id_list = list()
                for episode_index in episode_list_n:
                    self.get_episode_ids(dataset_id=dset_id_n,
                                         episode_index=episode_index,
                                         errormsgs=errormsgs)
                    episode_id = self.episode_cache[dset_id_n][episode_index]['episode_id']
                    episode_id_list.append(episode_id)
                    self.episode_index_cache[episode_id] = episode_index

                for episode_index in episode_list_z:
                    self.get_episode_ids(dataset_id=dset_id_z,
                                         episode_index=episode_index,
                                         errormsgs=errormsgs)
                    episode_id = self.episode_cache[dset_id_z][episode_index]['episode_id']
                    episode_id_list.append(episode_id)
                    self.episode_index_cache[episode_id] = episode_index

                random.shuffle(episode_id_list)

                for episode_id in episode_id_list:
                    self.episode_id_list.append(episode_id)

                if self.is_demo:
                    del self.episode_id_list
                    self.episode_id_list = list()
                    for episode_index in list(range(3)):
                        self.get_episode_ids(dataset_id=dset_id_z,
                                             episode_index=episode_index,
                                             errormsgs=errormsgs)
                        episode_id = self.episode_cache[dset_id_z][episode_index]['episode_id']
                        self.episode_id_list.append(episode_id)
                        self.episode_index_cache[episode_id] = episode_index
                    random.shuffle(self.episode_id_list)

                # Get the first episode_id to train and load it from the database.
                episode_id = self.episode_id_list[self.episode_id_list_index]
                episode_index = self.episode_index_cache[episode_id]
                dataset_id = self.get_episode_dataset_id(episode_id=episode_id,
                                                         episode_index=episode_index)
                # Set the current data_index for the episode to 0.
                self.episode_cache[dataset_id][episode_index]['data_index'] = 0
                # Load the episode data to the data_cache.
                self.load_data_to_cache(
                    episode_id=episode_id,
                    at_data_index=0,
                    errormsgs=errormsgs)
                self.STATE = objects.TestingEpisodeStart(
                    episode_number=self.episode_id_list_index,
                    total_episodes=len(self.episode_id_list))
            elif isinstance(self.STATE, objects.TestingEpisodeStart):
                self.STATE = objects.TestingEpisodeActive()
                # Get the next episode_id, episode_index, and dataset_id for the episode.
                episode_id = self.episode_id_list[self.episode_id_list_index]
                episode_index = self.episode_index_cache[episode_id]
                dataset_id = self.get_episode_dataset_id(episode_id=episode_id,
                                                         episode_index=episode_index)
                # Set the current data_index for the episode to 0.
                self.episode_cache[dataset_id][episode_index]['data_index'] = 0
                # Load the episode data to the data_cache.
                self.load_data_to_cache(
                    episode_id=episode_id,
                    at_data_index=0,
                    errormsgs=errormsgs)

                # Check to see if we reached novelty.
                self._TEST_EPISODE_PROGRESS += 1
                if self._TEST_EPISODE_PROGRESS > self._TEST_EPISODE_BEFORE_NOVEL and \
                        not self.novelty_initiated:
                    self.novelty_initiated = True
                    self.log_message(
                        msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                       action='novelty_initiated'))
            elif isinstance(self.STATE, objects.TestingEnd):
                self.STATE = objects.TrialEnd()
            elif isinstance(self.STATE, objects.TrialEnd):
                domain_index = self.domain_cache.index(self.current_domain)
                if (domain_index + 1) < len(self.domain_cache):
                    # Set the next domain.
                    self.current_domain = self.domain_cache[domain_index + 1]
                    # Increment to a new trial for the next domain and insert into the database.
                    self.experiment_trial += 1
                    self.experiment_trial_id = self.handle_next_experiment_trial(
                        model_experiment_id=int(self.model_experiment_id),
                        experiment_trial_id=self.experiment_trial_id,
                        trial=self.experiment_trial,
                        novelty=self.novelty_level,
                        novelty_visibility=self.novelty_visibility,
                        errormsgs=errormsgs)
                    self.STATE = objects.TrialStart(
                        trial_number=self.experiment_trial,
                        total_trials=len(self.domain_cache),
                        message=self.dataset_cache[self.current_domain]['train'][0]['domain'])
                else:
                    self.STATE = objects.ExperimentEnd()
            elif isinstance(self.STATE, objects.ExperimentEnd):
                self.update_experiment_end(model_experiment_id=self.model_experiment_id,
                                           errormsgs=errormsgs)
                self.amqp.remove_subscribe_to_queue(queue_name=self.private_queue)
                self.subscribe_experiment_queue()
                self.private_queue = None
                self.current_domain = None
                self.model_experiment_id = None
                self.experiment_trial_id = None
                self.experiment_trial = None
                self.experiment_type = None
                self.novelty_initiated = False
                self.novelty_visibility = 0
                self._TEST_WINDOW_PROGRESS = 0
                self.STATE = None
                del self.domain_ids
                self.domain_ids = dict()
                del self.domain_cache
                self.domain_cache = list()
                del self.dataset_cache
                self.dataset_cache = dict()
                del self.episode_cache
                self.episode_cache = dict()
                del self.data_cache
                self.data_cache = dict()
                del self.rolling_score
                self.rolling_score = list()
                if self._AMQP_EXP_CALLBACK_ID is not None:
                    self.amqp.cancel_call_later(timeout_id=self._AMQP_EXP_CALLBACK_ID)
                    self._AMQP_EXP_CALLBACK_ID = None
        elif isinstance(request, objects.BenchmarkData):
            if not isinstance(self.STATE, objects.ExperimentStart):
                errormsgs.append('ERROR: Will not accept BenchmarkData outside of the '
                                 'initial benchmarking state!')
            else:
                self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                                action=request.obj_type,
                                                data_object=request.get_json_obj()))
                data = objects.BenchmarkAck()
        elif isinstance(request, objects.RequestTrainingData):
            if not isinstance(self.STATE, objects.TrainingEpisodeActive):
                errormsgs.append('ERROR: You are not allowed to request training data outside '
                                 'of the TrainingEpisodeActive state!')
            else:
                # Get the next episode_id, episode_index, and dataset_id for the episode.
                episode_id = self.episode_id_list[self.episode_id_list_index]
                episode_index = self.episode_index_cache[episode_id]
                dataset_id = self.get_episode_dataset_id(episode_id=episode_id,
                                                         episode_index=episode_index)
                data_index = self.episode_cache[dataset_id][episode_index]['data_index']
                data_id = self.data_cache[episode_id][data_index]['data_id']
                test_instance_id = self.create_test_instance(
                    data_id=data_id,
                    experiment_trial_id=self.experiment_trial_id,
                    errormsgs=errormsgs)
                self.episode_cache[dataset_id][episode_index]['test_instance_id'] \
                    = test_instance_id
                data = objects.TrainingData(
                    secret=request.secret,
                    feature_vector=self.data_cache[episode_id][data_index]['feature_vector'],
                    feature_label=self.data_cache[episode_id][data_index]['label'])
                data.utc_remote_epoch_received = None
        elif isinstance(request, objects.TrainingDataPrediction):
            if not isinstance(self.STATE, objects.TrainingEpisodeActive):
                errormsgs.append('ERROR: Will not accept a TrainingDataAck outside of the '
                                 'TrainingEpisodeActive state!')
            else:
                # Get the next episode_id, episode_index, and dataset_id for the episode.
                episode_id = self.episode_id_list[self.episode_id_list_index]
                episode_index = self.episode_index_cache[episode_id]
                dataset_id = self.get_episode_dataset_id(episode_id=episode_id,
                                                         episode_index=episode_index)
                data_index = self.episode_cache[dataset_id][episode_index]['data_index']
                dataset_size = self.episode_cache[dataset_id][episode_index]['size']
                test_instance_id \
                    = self.episode_cache[dataset_id][episode_index]['test_instance_id']
                remote_stamp_arrived = objects.epoch_to_stamp(request.utc_remote_epoch_received)
                remote_stamp_delivered = objects.epoch_to_stamp(request.utc_remote_epoch_sent)
                self.update_test_instance(test_instance_id=test_instance_id,
                                          remote_stamp_arrived=remote_stamp_arrived,
                                          remote_stamp_delivered=remote_stamp_delivered,
                                          errormsgs=errormsgs)
                self.create_test_label(test_instance_id=test_instance_id,
                                       label_prediction=request.label_prediction,
                                       novelty=request.novelty,
                                       novelty_probability=request.novelty_probability,
                                       novelty_initiated=self.novelty_initiated,
                                       errormsgs=errormsgs)

                self.update_rolling_score(
                    solution=self.data_cache[episode_id][data_index]['label'],
                    prediction=request.label_prediction)
                data = objects.TrainingDataAck(secret=request.secret,
                                               performance=self.get_rolling_score())

                # Go ahead and delete the data instance.
                del self.data_cache[episode_id][data_index]

                # Increment the index on the dataset we just finished a test instance on.
                self.episode_cache[dataset_id][episode_index]['data_index'] += 1

                # Check if we need to mark the flag for a dataset reload.
                if len(self.data_cache[episode_id]) < self._DATA_CACHE_RELOAD:
                    refresh_dataset_cache = True

                if self.is_testing and not self.is_demo:
                    # If we are in testing mode we just want to limit the dataset sizes so we
                    # can quickly iterate through the various states.
                    if self._TESTING_DATA_SIZE < dataset_size:
                        dataset_size = self._TESTING_DATA_SIZE

                if (data_index + 1) >= dataset_size:
                    data = objects.TrainingEpisodeEnd()

                    # Check to see if we have a next training episode.
                    next_episode_index = self.episode_id_list_index + 1
                    if next_episode_index < len(self.episode_id_list):
                        # Start another episode!
                        self.episode_id_list_index += 1
                        self.STATE = objects.TrainingEpisodeStart(
                            episode_number=self.episode_id_list_index,
                            total_episodes=len(self.episode_id_list))
                    else:
                        # Done with the training episode list, moving on past training.
                        self.STATE = objects.TrainingEnd()

                    self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                                    action=data.obj_type,
                                                    data_object=data.get_json_obj()))
        elif isinstance(request, objects.RequestTestingData):
            if not isinstance(self.STATE, objects.TestingEpisodeActive):
                errormsgs.append('ERROR: You are not allowed to request testing data outside '
                                 'of the TestingEpisodeActive state!')
            else:
                # Get the next episode_id, episode_index, and dataset_id for the episode.
                episode_id = self.episode_id_list[self.episode_id_list_index]
                episode_index = self.episode_index_cache[episode_id]
                dataset_id = self.get_episode_dataset_id(episode_id=episode_id,
                                                         episode_index=episode_index)
                data_index = self.episode_cache[dataset_id][episode_index]['data_index']
                data_id = self.data_cache[episode_id][data_index]['data_id']
                test_instance_id = self.create_test_instance(
                    data_id=data_id,
                    experiment_trial_id=self.experiment_trial_id,
                    errormsgs=errormsgs)
                self.episode_cache[dataset_id][episode_index]['test_instance_id'] \
                    = test_instance_id
                data = objects.TestingData(
                    secret=request.secret,
                    feature_vector=self.data_cache[episode_id][data_index]['feature_vector'],
                    feature_vector_id=test_instance_id,
                    novelty_indicator=self.get_novelty_indicator_value())
                data.utc_remote_epoch_received = None
        elif isinstance(request, objects.TestingDataPrediction):
            if not isinstance(self.STATE, objects.TestingEpisodeActive):
                errormsgs.append('ERROR: Will not accept a TestingDataPrediction outside of the '
                                 'TestingEpisodeActive state!')
            else:
                # Get the next episode_id, episode_index, and dataset_id for the episode.
                episode_id = self.episode_id_list[self.episode_id_list_index]
                episode_index = self.episode_index_cache[episode_id]
                dataset_id = self.get_episode_dataset_id(episode_id=episode_id,
                                                         episode_index=episode_index)
                data_index = self.episode_cache[dataset_id][episode_index]['data_index']
                dataset_size = self.episode_cache[dataset_id][episode_index]['size']
                test_instance_id \
                    = self.episode_cache[dataset_id][episode_index]['test_instance_id']
                remote_stamp_arrived = objects.epoch_to_stamp(request.utc_remote_epoch_received)
                remote_stamp_delivered = objects.epoch_to_stamp(request.utc_remote_epoch_sent)
                self.update_test_instance(test_instance_id=test_instance_id,
                                          remote_stamp_arrived=remote_stamp_arrived,
                                          remote_stamp_delivered=remote_stamp_delivered,
                                          errormsgs=errormsgs)
                self.create_test_label(test_instance_id=test_instance_id,
                                       label_prediction=request.label_prediction,
                                       novelty=request.novelty,
                                       novelty_probability=request.novelty_probability,
                                       novelty_initiated=self.novelty_initiated,
                                       errormsgs=errormsgs)

                self.update_rolling_score(
                    solution=self.data_cache[episode_id][data_index]['label'],
                    prediction=request.label_prediction)
                data = objects.TestingDataAck(secret=request.secret,
                                              performance=self.get_rolling_score())

                # Go ahead and delete the data instance.
                del self.data_cache[episode_id][data_index]

                # Increment the index on the dataset we just finished a test instance on.
                self.episode_cache[dataset_id][episode_index]['data_index'] += 1

                # Check if we need to mark the flag for a dataset reload.
                if len(self.data_cache[episode_id]) < self._DATA_CACHE_RELOAD:
                    refresh_dataset_cache = True

                if self.is_testing:
                    # If we are in testing mode we just want to limit the dataset sizes so we
                    # can quickly iterate through the various states.
                    if self._TESTING_DATA_SIZE < dataset_size:
                        dataset_size = self._TESTING_DATA_SIZE

                # If we have reached the end of our testing window, prepare to end the trial.
                if (data_index + 1) >= dataset_size:
                    data = objects.TestingEpisodeEnd()

                    # Check to see if we have a next testing episode.
                    next_episode_index = self.episode_id_list_index + 1
                    if next_episode_index < len(self.episode_id_list):
                        # Start another episode!
                        self.episode_id_list_index += 1
                        self.STATE = objects.TestingEpisodeStart(
                            episode_number=self.episode_id_list_index,
                            total_episodes=len(self.episode_id_list))
                    else:
                        # Done with the episode list, moving on past testing.
                        self.STATE = objects.TestingEnd()

                    self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                                    action=data.obj_type,
                                                    data_object=data.get_json_obj()))

        if len(errormsgs) > 0:
            response.add_error(
                casas_error=objects.CasasError(
                    error_type='error',
                    message='There were errors processing part or all of '
                            'your request, please see errors for details.',
                    error_dict=dict({'errors': errormsgs})))

        if props.reply_to is not None:
            if response.status == 'error':
                self.log.error(str(response))
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=response,
                                           correlation_id=props.correlation_id)
            elif data is not None:
                self.log.debug('REPLY: {}'.format(str(data)))
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=data,
                                           correlation_id=props.correlation_id)

        if refresh_dataset_cache:
            # Get the next episode_id, episode_index, and dataset_id for the episode.
            episode_id = self.episode_id_list[self.episode_id_list_index]
            episode_index = self.episode_index_cache[episode_id]
            dataset_id = self.get_episode_dataset_id(episode_id=episode_id,
                                                     episode_index=episode_index)
            # Get the current data_index for the episode.
            data_index = self.episode_cache[dataset_id][episode_index]['data_index']
            # Load the episode data to the data_cache.
            self.load_data_to_cache(
                episode_id=episode_id,
                at_data_index=data_index,
                errormsgs=errormsgs)

        if self.STATE is not None:
            self._AMQP_EXP_CALLBACK_ID = self.amqp.call_later(
                seconds=self._AMQP_EXPERIMENT_TIMEOUT,
                function=self.force_end_experiment)
        return
    """

    def get_novelty_description(self, domain: str, novelty: int, difficulty: str) -> \
            objects.NoveltyDescription:
        response_queue = queue.Queue()
        tmp_thread = NoveltyDescriptionThread(log=self.log,
                                              amqp_user=self.amqp_user,
                                              amqp_pass=self.amqp_pass,
                                              amqp_host=self.amqp_host,
                                              amqp_port=self.amqp_port,
                                              amqp_vhost=self.amqp_vhost,
                                              amqp_ssl=self.amqp_ssl,
                                              response_queue=response_queue,
                                              domain=domain,
                                              novelty=novelty,
                                              difficulty=difficulty,
                                              request_timeout=self._AMQP_EXPERIMENT_TIMEOUT)
        tmp_thread.start()
        start = time.time()
        done = False
        response = None
        while abs(time.time() - start) < self._AMQP_EXPERIMENT_TIMEOUT and not done:
            try:
                response = response_queue.get(block=True, timeout=2.0)
                done = True
            except queue.Empty:
                self.amqp.process_data_events()
        tmp_thread.stop()
        tmp_thread.join()
        del tmp_thread
        del response_queue
        return response

    def prepare_episode(self, episode: objects.Episode, errormsgs: list):
        self.log.debug('prepare_episode(episode={})'.format(str(episode)))
        # Check if recorded or live training episode.
        if episode.data_type in [objects.DTYPE_TRAIN, objects.DTYPE_TEST]:
            self.log.info('prepare_episode({})'.format(str(episode)))
            # Get the next episode_id, episode_index, and dataset_id for the episode.
            domain_id = self.domain_ids[episode.domain]
            dataset_id = self.dataset_cache[domain_id][episode.data_type][episode.novelty][
                episode.difficulty][episode.trial_novelty]['dataset_id']
            self.get_episode_ids(dataset_id=dataset_id,
                                 episode_index=episode.episode_index,
                                 errormsgs=errormsgs)
            episode_id = self.episode_cache[dataset_id][episode.episode_index]['episode_id']
            episode.episode_id = episode_id
            # Set the current data_index for the episode to 0.
            self.episode_cache[dataset_id][episode.episode_index]['data_index'] = 0
            self.episode_data_total = self.episode_cache[dataset_id][episode.episode_index]['size']
            del self.rolling_score
            self.rolling_score = list()
            # Load the episode data to the data_cache.
            self.load_data_to_cache(
                episode_id=episode_id,
                at_data_index=0,
                errormsgs=errormsgs)
        elif episode.data_type in [objects.DTYPE_LIVE_TRAIN, objects.DTYPE_LIVE_TEST]:
            self.episode_data_count = 0
            del self._ta2_response
            self._ta2_response = queue.Queue()
            del self._live_output
            self._live_output = queue.Queue()
            self._live_thread = LiveGeneratorThread(log=self.log,
                                                    amqp_user=self.amqp_user,
                                                    amqp_pass=self.amqp_pass,
                                                    amqp_host=self.amqp_host,
                                                    amqp_port=self.amqp_port,
                                                    amqp_vhost=self.amqp_vhost,
                                                    amqp_ssl=self.amqp_ssl,
                                                    ta2_response_queue=self._ta2_response,
                                                    live_output_queue=self._live_output,
                                                    domain=episode.domain,
                                                    novelty=episode.novelty,
                                                    difficulty=episode.difficulty,
                                                    seed=episode.seed,
                                                    trial_novelty=episode.trial_novelty,
                                                    day_offset=episode.day_offset,
                                                    request_timeout=self._AMQP_EXPERIMENT_TIMEOUT,
                                                    use_image=episode.use_image)
            self._live_thread.start()
            # Get the dataset_id so we can add a new episode.
            domain_id = self.domain_ids[episode.domain]
            """
            self.log.debug('domain_id={} data_type={} novelty={} difficulty={}'.format(
                domain_id, episode.data_type, episode.novelty, episode.difficulty))
            self.log.debug('{}'.format(self.dataset_cache[domain_id]))
            self.log.debug('{}'.format(self.dataset_cache[domain_id][episode.data_type]))
            self.log.debug('{}'.format(self.dataset_cache[domain_id][episode.data_type]
                                       [episode.novelty]))
            self.log.debug('{}'.format(self.dataset_cache[domain_id][episode.data_type]
                                       [episode.novelty][episode.difficulty]))
            self.log.debug('{}'.format(self.dataset_cache[domain_id][episode.data_type]
                                       [episode.novelty][episode.difficulty]['dataset_id']))
            """
            dataset_id = self.dataset_cache[domain_id][episode.data_type][episode.novelty][
                episode.difficulty][episode.trial_novelty]['dataset_id']
            # Create the new episode and return the index.
            episode_index = self.add_episode_to_dataset(dataset_id=dataset_id,
                                                        seed=episode.seed,
                                                        errormsgs=errormsgs)
            episode_id = self.episode_cache[dataset_id][episode_index]['episode_id']
            # Save the episode_id and episode_index to the episode object.
            episode.episode_index = episode_index
            episode.episode_id = episode_id
        return

    def get_episode_data(self, request: objects.RequestData, episode: objects.Episode,
                         errormsgs: list) -> objects.AiqObject:
        self.log.debug('get_episode_data(request={})'.format(str(request)))
        data = objects.AiqObject()
        # Check if recorded or live training episode.
        if episode.data_type in [objects.DTYPE_TRAIN, objects.DTYPE_TEST]:
            # Get the episode_id, episode_index, and dataset_id for the episode.
            domain_id = self.domain_ids[episode.domain]
            dataset_id = self.dataset_cache[domain_id][episode.data_type][episode.novelty][
                episode.difficulty][episode.trial_novelty]['dataset_id']
            self.get_episode_ids(dataset_id=dataset_id,
                                 episode_index=episode.episode_index,
                                 errormsgs=errormsgs)
            episode_id = self.episode_cache[dataset_id][episode.episode_index]['episode_id']
            episode_index = episode.episode_index

            # Grab the data_index and data_id for the feature vector we will be sending.
            # The data itself should already be in self.data_cache.
            data_index = self.episode_cache[dataset_id][episode_index]['data_index']
            data_id = self.data_cache[episode_id][data_index]['data_id']
            # Create the test_instance row for this evaluation.
            test_instance_id = self.create_test_instance(
                data_id=data_id,
                trial_episode_id=self.trial_episode_id,
                errormsgs=errormsgs)
            # Store the test_instance_id for use later.
            self.episode_cache[dataset_id][episode_index]['test_instance_id'] \
                = test_instance_id
            # Create the response object to send to TA2/SOTA.
            if episode.data_type == objects.DTYPE_TRAIN:
                data = objects.TrainingData(
                    secret=request.secret,
                    feature_vector=self.data_cache[episode_id][data_index]['feature_vector'],
                    feature_label=self.data_cache[episode_id][data_index]['label'])
            elif episode.data_type == objects.DTYPE_TEST:
                data = objects.TestingData(
                    secret=request.secret,
                    feature_vector=self.data_cache[episode_id][data_index]['feature_vector'],
                    novelty_indicator=self.get_novelty_indicator_value())
            data.utc_remote_epoch_received = None
        elif episode.data_type in [objects.DTYPE_LIVE_TRAIN, objects.DTYPE_LIVE_TEST]:
            self._ta2_response.put(request)
            start = time.time()
            done = False
            response = None
            while abs(time.time() - start) < self._AMQP_EXPERIMENT_TIMEOUT and not done:
                try:
                    response = self._live_output.get(block=True, timeout=2.0)
                    done = True
                except queue.Empty:
                    self.amqp.process_data_events()
            self.log.debug('GEN RESPONSE: {}'.format(str(response)))
            if isinstance(response, objects.ExperimentException):
                data = copy.deepcopy(response)
                self._live_thread.stop()
                self._live_thread.join()
                self._live_thread = None
            elif isinstance(response, objects.BasicData):
                self.episode_data_count += 1
                # Grab the domain_id and dataset_id that we are dealing with.
                domain_id = self.domain_ids[episode.domain]
                dataset_id = self.dataset_cache[domain_id][episode.data_type][episode.novelty][
                    episode.difficulty][episode.trial_novelty]['dataset_id']
                # The next data_index is the current size, as we start with 0.
                data_index = self.episode_cache[dataset_id][episode.episode_index]['size']
                # Create the data instance in the database.
                data_id = self.create_data_instance(episode_id=episode.episode_id,
                                                    feature_vector=response.feature_vector,
                                                    label=response.feature_label,
                                                    data_index=data_index,
                                                    errormsgs=errormsgs)
                # Update the episode size in cache and in the database.
                self.episode_cache[dataset_id][episode.episode_index]['size'] += 1
                self.update_episode_size(episode_id=episode.episode_id,
                                         size=self.episode_cache[dataset_id][episode.episode_index][
                                             'size'],
                                         errormsgs=errormsgs)
                # Create the test_instance row for this evaluation.
                test_instance_id = self.create_test_instance(
                    data_id=data_id,
                    trial_episode_id=self.trial_episode_id,
                    errormsgs=errormsgs)
                # Store the test_instance_id for use later.
                self.episode_cache[dataset_id][episode.episode_index]['test_instance_id'] \
                    = test_instance_id
                # Create the response object to send to TA2/SOTA.
                if episode.data_type == objects.DTYPE_LIVE_TRAIN:
                    data = objects.TrainingData(
                        secret=request.secret,
                        feature_vector=response.feature_vector,
                        feature_label=response.feature_label)
                elif episode.data_type == objects.DTYPE_LIVE_TEST:
                    data = objects.TestingData(
                        secret=request.secret,
                        feature_vector=response.feature_vector,
                        novelty_indicator=self.get_novelty_indicator_value())
                data.utc_remote_epoch_received = None
        return data

    def process_episode_data_prediction(self, request: objects.BasicDataPrediction,
                                        episode: objects.Episode, errormsgs: list)\
            -> objects.AiqObject:
        self.log.debug('process_episode_data_prediction({})'.format(str(request)))
        data = objects.AiqObject()
        # We have some basic things that apply to ALL episode types first.
        # Get the episode_id, episode_index, and dataset_id for the episode.
        domain_id = self.domain_ids[episode.domain]
        dataset_id = self.dataset_cache[domain_id][episode.data_type][episode.novelty][
            episode.difficulty][episode.trial_novelty]['dataset_id']
        test_instance_id \
            = self.episode_cache[dataset_id][episode.episode_index]['test_instance_id']
        remote_stamp_arrived = objects.epoch_to_stamp(request.utc_remote_epoch_received)
        remote_stamp_delivered = objects.epoch_to_stamp(request.utc_remote_epoch_sent)
        self.update_test_instance(test_instance_id=test_instance_id,
                                  remote_stamp_arrived=remote_stamp_arrived,
                                  remote_stamp_delivered=remote_stamp_delivered,
                                  errormsgs=errormsgs)
        # Check if recorded or live training episode.
        if episode.data_type in [objects.DTYPE_TRAIN, objects.DTYPE_TEST]:
            # Get the data_index and episode size.
            data_index = self.episode_cache[dataset_id][episode.episode_index]['data_index']
            dataset_size = self.episode_cache[dataset_id][episode.episode_index]['size']
            # Update the score.
            self.log.debug('data_cache keys: {}'.format(str(self.data_cache.keys())))
            self.log.debug('episode_id = {}'.format(episode.episode_id))
            self.log.debug('data_cache[ep_id] keys: {}'.format(str(self.data_cache[
                episode.episode_id].keys())))
            self.log.debug('data_index = {}'.format(data_index))
            self.log.debug('data_cache object = {}'.format(
                self.data_cache[episode.episode_id][data_index]))
            self.update_rolling_score(
                solution=self.data_cache[episode.episode_id][data_index]['label'],
                prediction=request.label_prediction)
            performance = self.get_rolling_score()
            feedback = None
            if self.trial_budget_active:
                if random.random() < self._experiment.budget:
                    feedback = dict({'class_label': copy.deepcopy(self.data_cache[
                                                                  episode.episode_id][
                                                                  data_index]['label'])})
            self.trial_episode_performance = performance
            # Log the response values in the database.
            self.create_test_label(test_instance_id=test_instance_id,
                                   label_prediction=request.label_prediction,
                                   performance=performance,
                                   feedback=feedback,
                                   errormsgs=errormsgs)

            # Go ahead and delete the data instance.
            del self.data_cache[episode.episode_id][data_index]

            # Increment the index on the dataset we just finished a test instance on.
            self.episode_cache[dataset_id][episode.episode_index]['data_index'] += 1

            # Check if we need to mark the flag for a dataset reload.
            if len(self.data_cache[episode.episode_id]) < self._DATA_CACHE_RELOAD:
                self.refresh_dataset_cache = True

            if self.is_testing and not self.is_demo:
                # If we are in testing mode we just want to limit the dataset sizes so we
                # can quickly iterate through the various states.
                if self._TESTING_DATA_SIZE < dataset_size:
                    dataset_size = self._TESTING_DATA_SIZE

            if self.is_shortdemo:
                # Only end an episode early like this if it is a shortdemo.
                if self._SHORT_DEMO_EPISODE_SIZE < dataset_size:
                    dataset_size = self._SHORT_DEMO_EPISODE_SIZE

            # Check to see if this is the end of the episode.
            episode_has_ended = False
            if (data_index + 1) >= dataset_size:
                episode_has_ended = True

            if episode.data_type == objects.DTYPE_TRAIN:
                if episode_has_ended:
                    # The training episode has ended, so return objects.TrainingEpisodeEnd.
                    data = objects.TrainingEpisodeEnd(performance=performance,
                                                      feedback=feedback)
                else:
                    # The training episode is not over, so return objects.TrainingDataAck.
                    data = objects.TrainingDataAck(secret=request.secret,
                                                   performance=performance,
                                                   feedback=feedback)
            elif episode.data_type == objects.DTYPE_TEST:
                if episode_has_ended:
                    # The testing episode has ended, so return objects.TestingEpisodeEnd.
                    data = objects.TestingEpisodeEnd(performance=performance,
                                                     feedback=feedback)
                else:
                    # The testing episode is not over, so return objects.TestingDataAck.
                    data = objects.TestingDataAck(secret=request.secret,
                                                  performance=performance,
                                                  feedback=feedback)
        elif episode.data_type in [objects.DTYPE_LIVE_TRAIN, objects.DTYPE_LIVE_TEST]:
            self._ta2_response.put(request)
            start = time.time()
            done = False
            response = None
            while abs(time.time() - start) < self._AMQP_EXPERIMENT_TIMEOUT and not done:
                try:
                    response = self._live_output.get(block=True, timeout=2.0)
                    self.trial_episode_performance = response.performance
                    done = True
                except queue.Empty:
                    self.amqp.process_data_events()
            self.log.debug('GEN RESPONSE: {}'.format(str(response)))
            feedback = None
            if self.trial_budget_active:
                if random.random() < self._experiment.budget:
                    feedback = copy.deepcopy(response.feedback)
            if isinstance(response, objects.ExperimentException):
                data = copy.deepcopy(response)
                self._live_thread.stop()
                self._live_thread.join()
                self._live_thread = None
            elif isinstance(response, (objects.BasicDataAck, objects.EpisodeEnd)):
                if self.is_shortdemo:
                    # Only end an episode early like this if it is a shortdemo.
                    if self.episode_data_count >= self._SHORT_DEMO_EPISODE_SIZE:
                        self._ta2_response.put(objects.GeneratorReset())
                        response = objects.EpisodeEnd(performance=response.performance,
                                                      feedback=feedback)
                # Log the response values in the database.
                self.create_test_label(test_instance_id=test_instance_id,
                                       label_prediction=request.label_prediction,
                                       performance=response.performance,
                                       feedback=feedback,
                                       errormsgs=errormsgs)
                if episode.data_type == objects.DTYPE_LIVE_TRAIN:
                    if isinstance(response, objects.EpisodeEnd):
                        data = objects.TrainingEpisodeEnd(performance=response.performance,
                                                          feedback=feedback)
                    elif isinstance(response, objects.BasicDataAck):
                        data = objects.TrainingDataAck(secret=request.secret,
                                                       performance=response.performance,
                                                       feedback=feedback)
                elif episode.data_type == objects.DTYPE_LIVE_TEST:
                    if isinstance(response, objects.EpisodeEnd):
                        data = objects.TestingEpisodeEnd(performance=response.performance,
                                                         feedback=feedback)
                    elif isinstance(response, objects.BasicDataAck):
                        data = objects.TestingDataAck(secret=request.secret,
                                                      performance=response.performance,
                                                      feedback=feedback)

                # Check if it's the end and stop then join the live thread.
                if isinstance(response, objects.EpisodeEnd):
                    self._live_thread.stop()
                    self._live_thread.join()
                    self._live_thread = None
        return data

    def on_sail_on_request(self, ch, method, props, body, request):
        self.log.debug('on_sail_on_request( {} )'.format(str(request)))
        self.log.debug('STATE: {}'.format(str(self.STATE)))
        errormsgs = list()
        data = None
        current_episode = None
        self.refresh_dataset_cache = False
        response = objects.CasasResponse(status='success',
                                         response_type='data',
                                         error_message='No Errors')

        if self._AMQP_EXP_CALLBACK_ID is not None:
            self.amqp.cancel_call_later(timeout_id=self._AMQP_EXP_CALLBACK_ID)
            self._AMQP_EXP_CALLBACK_ID = None

        # SAIL-ON SAIL states sent back:
        # - objects.ExperimentResponse
        # - objects.BenchmarkRequest
        # - objects.ExperimentStart
        # - objects.TrainingStart
        # - for e in episodes:
        #     - objects.TrainingEpisodeStart
        #     - Client then requests objects.TrainingData, and responds with
        #       objects.TrainingDataAck. This repeats until we send an objects.TrainingEpisodeEnd
        #       response instead of the same ack object back.
        #     - During this, the TA1 state is objects.TrainingEpisodeActive.
        # - objects.TrainingEnd
        # - objects.TrainingModelEnd
        # - for T trials:
        #     - objects.TrialStart
        #     - objects.TestingStart
        #     - for e in trial episodes:
        #         - objects.TestingEpisodeStart
        #         - Client then requests objects.TestingData, and response with
        #           objects.TestingDataPrediction. This repeats until we send an
        #           objects.TestingEpisodeEnd response instead of an objects.TestingDataAck.
        #         - During this, the TA1 state is objects.TestingEpisodeActive.
        #     - objects.TrialEnd
        # - objects.ExperimentEnd

        if isinstance(request, objects.RequestState):
            data = copy.deepcopy(self.STATE)
            self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                            action=objects.REQ_STATE,
                                            data_object=data.get_json_obj(),
                                            experiment_trial_id=self.experiment_trial_id))
            if isinstance(self.STATE, objects.BenchmarkRequest):
                self.STATE = objects.ExperimentStart()
            elif isinstance(self.STATE, objects.ExperimentStart):
                if not self._exper_no_training:
                    # We are not skipping testing, training can begin.
                    self.STATE = objects.TrainingStart()
                else:
                    # Do a little housekeeping on any abandoned trials.
                    self.clear_abandoned_trials(errormsgs=errormsgs)
                    # We are skipping testing and jumping to 1 or more trials.
                    self.experiment_trial_id = self.lock_experiment_trial(
                        model_experiment_id=self.model_experiment_id,
                        errormsgs=errormsgs)

                    if self.experiment_trial_id is None:
                        # A value of None means there are no trials available.
                        self.STATE = objects.ExperimentEnd()
                    else:
                        # We have claimed an experiment_trial_id to work on, proceeding to set
                        # up TA1 to begin processing the trial.
                        self.start_experiment_trial(experiment_trial_id=self.experiment_trial_id,
                                                    errormsgs=errormsgs)
                        self.set_experiment_trial_index(
                            experiment_trial_id=self.experiment_trial_id,
                            errormsgs=errormsgs)

                        # Set the state to TrialStart.
                        self.STATE = objects.TrialStart(
                            trial_number=self._exper_trial_index,
                            message='Please RESET TA2 model to SAVED state.',
                            novelty_description=self._exper_trial_novelty_desc)
            elif isinstance(self.STATE, objects.TrainingStart):
                self.trial_predicted_novelty = False
                self.trial_budget_active = False
                self.STATE = objects.TrainingEpisodeStart(
                    episode_number=self._exper_train_index)
            elif isinstance(self.STATE, objects.TrainingEpisodeStart):
                self.STATE = objects.TrainingEpisodeActive()

                # Get the episode.
                episode = self._experiment.training.episodes[self._exper_train_index]
                current_episode = episode

                # Prepare the training episode.
                self.prepare_episode(episode=episode,
                                     errormsgs=errormsgs)

                # Start the trial_episode and get the trial_episode_id.
                self.trial_episode_id = self.start_trial_episode(
                    experiment_trial_id=self.experiment_trial_id,
                    episode_index=episode.trial_episode_index,
                    budget_active=self.trial_budget_active,
                    errormsgs=errormsgs)

                # Update the training trial as still active.
                self.update_experiment_trial(experiment_trial_id=self.experiment_trial_id,
                                             errormsgs=errormsgs)
            elif isinstance(self.STATE, objects.TrainingEnd):
                # objects.TrainingEnd is what we are sending to the TA2/SOTA, so there might be
                # a long wait on what we set up here.

                # Set the training experiment_trial as done.
                self.end_experiment_trial(experiment_trial_id=self.experiment_trial_id,
                                          errormsgs=errormsgs)

                # The next state will be objects.TrainingModelEnd to set things up after any
                # large blocks of time that might be needed for training a model.
                self.STATE = objects.TrainingModelEnd()
            elif isinstance(self.STATE, objects.TrainingModelEnd):
                # Check if we were just training and need to revert the timeout.
                if self.hold_during_training_gap:
                    # Done with the training gap wait, returning the timeouts to normal limits.
                    self.hold_during_training_gap = False
                    self._AMQP_EXPERIMENT_TIMEOUT = (self._AMQP_EXPERIMENT_TIMEOUT
                                                     / self._TIMEOUT_MULTIPLIER)

                if self._exper_no_testing:
                    # We have received a flag that they do not wish for any trials, so this is
                    # the end of the experiment now.
                    self.STATE = objects.ExperimentEnd()
                else:
                    # Do a little housekeeping on any abandoned trials.
                    self.clear_abandoned_trials(errormsgs=errormsgs)
                    # There was no flag for no testing, so we continue on to try and secure a
                    # trial to evaluate on.
                    self.experiment_trial_id = self.lock_experiment_trial(
                        model_experiment_id=self.model_experiment_id,
                        errormsgs=errormsgs)

                    if self.experiment_trial_id is None:
                        # A value of None means there are no trials available.
                        self.STATE = objects.ExperimentEnd()
                    else:
                        # We have claimed an experiment_trial_id to work on, proceeding to set
                        # up TA1 to begin processing the trial.
                        self.start_experiment_trial(experiment_trial_id=self.experiment_trial_id,
                                                    errormsgs=errormsgs)
                        # Set the internal index values for this trial.
                        self.set_experiment_trial_index(
                            experiment_trial_id=self.experiment_trial_id,
                            errormsgs=errormsgs)

                        # Set the state to TrialStart.
                        self.STATE = objects.TrialStart(
                            trial_number=self._exper_trial_index,
                            message='Please RESET TA2 model to SAVED state.',
                            novelty_description=self._exper_trial_novelty_desc)
            elif isinstance(self.STATE, objects.TrialStart):
                # Set the state as TestingStart.
                self.STATE = objects.TestingStart()

                self.trial_predicted_novelty = False
                self.trial_budget_active = False

                # Get the trial.
                trial = self._experiment.novelty_groups[self._exper_novelty_index] \
                    .trials[self._exper_trial_index]

                # Set the system novelty_visibility based on the trial's config.
                self.novelty_visibility = trial.novelty_visibility

                # Reset the episode index to 0.
                self._exper_episode_index = 0

                # Reset the novelty_initated value to false at the start of the trial.
                self.novelty_initiated = False

                # Log the cached benchmark data for this trial so we know the stats of the
                # computer running this trial.
                self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                                action=self.benchmark_data.obj_type,
                                                data_object=self.benchmark_data.get_json_obj(),
                                                experiment_trial_id=self.experiment_trial_id))
            elif isinstance(self.STATE, objects.TestingStart):
                # Set the state to TestingEpisodeStart.
                self.STATE = objects.TestingEpisodeStart(
                    episode_number=self._exper_episode_index)

                # Get the trial.
                trial = self._experiment.novelty_groups[self._exper_novelty_index] \
                    .trials[self._exper_trial_index]
                # Get the episode.
                episode = trial.episodes[self._exper_episode_index]

                # Check to see if the data_type is recorded.
                if episode.data_type == objects.DTYPE_TEST:
                    for i in range(len(trial.episodes)):
                        # Get the episode_id, episode_index, and dataset_id for the episode.
                        domain_id = self.domain_ids[trial.episodes[i].domain]
                        dataset_id = self.dataset_cache[domain_id][episode.data_type][
                            episode.novelty][episode.difficulty][episode.trial_novelty][
                            'dataset_id']

                        # Load episode_id and size to episode_cache from the database.
                        self.get_episode_ids(dataset_id=dataset_id,
                                             episode_index=trial.episodes[i].episode_index,
                                             errormsgs=errormsgs)
                        self.log.debug('i = {}'.format(i))
                        self.log.debug('len(trial.episodes) = {}'.format(len(trial.episodes)))
                        self.log.debug('dataset_id = {}'.format(dataset_id))
                        self.log.debug('episode_cache dataset_ids = {}'.format(
                            str(list(self.episode_cache.keys()).sort())))
                        self.log.debug('trial.episodes[i].episode_index = {}'.format(
                            trial.episodes[i].episode_index))
                        self.log.debug('episode_cache[dataset_id].keys = {}'.format(
                            str(list(self.episode_cache[dataset_id].keys()).sort())))
                        # Update the episode_id in the Episode object.
                        trial.episodes[i].episode_id = self.episode_cache[dataset_id][
                            trial.episodes[i].episode_index]['episode_id']

                    # Get the dataset_id for the current episode.
                    domain_id = self.domain_ids[episode.domain]
                    dataset_id = self.dataset_cache[domain_id][episode.data_type][episode.novelty][
                        episode.difficulty][episode.trial_novelty]['dataset_id']

                    # Set the current data_index for the episode to 0.
                    self.episode_cache[dataset_id][episode.episode_index]['data_index'] = 0

                    # Load the episode data to the data_cache.
                    self.load_data_to_cache(
                        episode_id=episode.episode_id,
                        at_data_index=0,
                        errormsgs=errormsgs)
            elif isinstance(self.STATE, objects.TestingEpisodeStart):
                self.STATE = objects.TestingEpisodeActive()

                # Get the trial.
                trial = self._experiment.novelty_groups[self._exper_novelty_index] \
                    .trials[self._exper_trial_index]
                # Get the episode.
                episode = trial.episodes[self._exper_episode_index]
                current_episode = episode

                # Prepare the testing episode.
                self.prepare_episode(episode=episode,
                                     errormsgs=errormsgs)

                # Start the trial_episode and get the trial_episode_id.
                self.trial_episode_id = self.start_trial_episode(
                    experiment_trial_id=self.experiment_trial_id,
                    episode_index=episode.trial_episode_index,
                    budget_active=self.trial_budget_active,
                    errormsgs=errormsgs)

                # Check to see if we reached novelty.
                if episode.novelty != objects.NOVELTY_200 and not self.novelty_initiated:
                    self.novelty_initiated = True
                    self.log_message(
                        msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                       action='novelty_initiated',
                                       experiment_trial_id=self.experiment_trial_id))
                # Update the current trial as still active.
                self.update_experiment_trial(experiment_trial_id=self.experiment_trial_id,
                                             errormsgs=errormsgs)
            elif isinstance(self.STATE, objects.TestingEnd):
                self.STATE = objects.TrialEnd()
            elif isinstance(self.STATE, objects.TrialEnd):
                # End the current experiment_trial.
                self.end_experiment_trial(experiment_trial_id=self.experiment_trial_id,
                                          errormsgs=errormsgs)
                self.publish_partial_analysis(model_experiment_id=self.model_experiment_id,
                                              experiment_trial_id=self.experiment_trial_id)
                # Check to see if we still have more trials or if this is the end.
                if self._exper_just_one_trial:
                    # Just running one trial, moving toward clean end of things.
                    self.STATE = objects.ExperimentEnd()
                else:
                    # Do a little housekeeping on any abandoned trials.
                    self.clear_abandoned_trials(errormsgs=errormsgs)
                    # Lets see if we can get another trial to process.
                    self.experiment_trial_id = self.lock_experiment_trial(
                        model_experiment_id=self.model_experiment_id,
                        errormsgs=errormsgs)

                    if self.experiment_trial_id is None:
                        # A value of None means there are no trials available.
                        self.STATE = objects.ExperimentEnd()
                    else:
                        # We have claimed an experiment_trial_id to work on, proceeding to set
                        # up TA1 to begin processing the trial.
                        self.start_experiment_trial(experiment_trial_id=self.experiment_trial_id,
                                                    errormsgs=errormsgs)
                        self.set_experiment_trial_index(
                            experiment_trial_id=self.experiment_trial_id,
                            errormsgs=errormsgs)

                        # Set the state to TrialStart.
                        self.STATE = objects.TrialStart(
                            trial_number=self._exper_trial_index,
                            message='Please RESET TA2 model to SAVED state.',
                            novelty_description=self._exper_trial_novelty_desc)
            elif isinstance(self.STATE, objects.ExperimentEnd):
                if not self._exper_no_testing:
                    self.update_experiment_end(model_experiment_id=self.model_experiment_id,
                                               errormsgs=errormsgs)
                self.amqp.remove_subscribe_to_queue(queue_name=self.private_queue)
                self.subscribe_experiment_queue()
                self.subscribe_sota_queue()
                self.private_queue = None
                self.current_domain = None
                self.model_experiment_id = None
                self.experiment_trial_id = None
                self.trial_episode_id = None
                self.trial_episode_performance = None
                self.trial_predicted_novelty = False
                self.trial_budget_active = False
                self.experiment_type = None
                self.novelty_initiated = False
                self.novelty_visibility = 0
                self._experiment = None
                self._exper_train_index = None
                self._exper_novelty_index = None
                self._exper_trial_index = None
                self._exper_episode_index = None
                del self._exper_trial_novelty_desc
                self._exper_trial_novelty_desc = None
                self._exper_end_training_early = False
                self._exper_end_experiment_early = False
                self._exper_no_testing = False
                self._exper_no_training = False
                self._exper_just_one_trial = False
                self.benchmark_data = None
                self.STATE = None
                del self.domain_ids
                self.domain_ids = dict()
                del self.domain_cache
                self.domain_cache = list()
                del self.dataset_cache
                self.dataset_cache = dict()
                del self.episode_cache
                self.episode_cache = dict()
                del self.data_cache
                self.data_cache = dict()
                del self.rolling_score
                self.rolling_score = list()
                if self._AMQP_EXP_CALLBACK_ID is not None:
                    self.amqp.cancel_call_later(timeout_id=self._AMQP_EXP_CALLBACK_ID)
                    self._AMQP_EXP_CALLBACK_ID = None
        elif isinstance(request, objects.BenchmarkData):
            if not isinstance(self.STATE, objects.ExperimentStart):
                errormsgs.append('ERROR: Will not accept BenchmarkData outside of the '
                                 'initial benchmarking state!')
            else:
                self.benchmark_data = copy.deepcopy(request)
                self.log_message(msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                                action=request.obj_type,
                                                data_object=request.get_json_obj(),
                                                experiment_trial_id=self.experiment_trial_id))
                data = objects.BenchmarkAck()
        elif isinstance(request, objects.RequestTrainingData):
            if not isinstance(self.STATE, objects.TrainingEpisodeActive):
                errormsgs.append('ERROR: You are not allowed to request training data outside '
                                 'of the TrainingEpisodeActive state!')
            else:
                # Get the episode.
                episode = self._experiment.training.episodes[self._exper_train_index]
                current_episode = episode

                # Get the data to send.
                data = self.get_episode_data(request=request,
                                             episode=episode,
                                             errormsgs=errormsgs)
        elif isinstance(request, objects.TrainingDataPrediction):
            if not isinstance(self.STATE, objects.TrainingEpisodeActive):
                errormsgs.append('ERROR: Will not accept a TrainingDataPrediction outside of the '
                                 'TrainingEpisodeActive state!')
            else:
                if request.end_early:
                    self._exper_end_training_early = True
                # Get the episode.
                episode = self._experiment.training.episodes[self._exper_train_index]
                current_episode = episode

                # Process the prediction.
                data = self.process_episode_data_prediction(request=request,
                                                            episode=episode,
                                                            errormsgs=errormsgs)

                # Check to see if we received an objects.TrainingEpisodeEnd.
                if isinstance(data, objects.EpisodeEnd):
                    self.stop_trial_episode(trial_episode_id=self.trial_episode_id,
                                            errormsgs=errormsgs)
                    # Check to see if we have a next training episode.
                    next_episode_index = self._exper_train_index + 1
                    if next_episode_index < len(self._experiment.training.episodes) and \
                            not self._exper_end_training_early:
                        # We still have more training episodes!
                        # Increment the training episode index.
                        self._exper_train_index += 1
                        self.STATE = objects.TrainingEpisodeStart(
                            episode_number=self._exper_train_index)
                    else:
                        # This was the last training episode, prepare to move past training.
                        self.STATE = objects.TrainingEnd(
                            message='Please SAVE TA2 model in current state.')
                        # Increasing the timeout length by multiplier so client/sota can train
                        # models without getting kicked from the experiment.
                        self.hold_during_training_gap = True
                        self._AMQP_EXPERIMENT_TIMEOUT = (self._AMQP_EXPERIMENT_TIMEOUT
                                                         * self._TIMEOUT_MULTIPLIER)
                    self.log_message(
                        msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                       action=data.obj_type,
                                       data_object=data.get_json_obj(),
                                       experiment_trial_id=self.experiment_trial_id))
        elif isinstance(request, objects.TrainingEpisodeNovelty):
            if not isinstance(self.STATE, (objects.TrainingEpisodeStart, objects.TrainingEnd)):
                errormsgs.append('ERROR: Will not accept a TrainingEpisodeNovelty in this state!')
            else:
                # Save the episode data.
                self.set_trial_episode_stats(
                    trial_episode_id=self.trial_episode_id,
                    novelty=request.novelty,
                    performance=self.trial_episode_performance,
                    novelty_probability=request.novelty_probability,
                    novelty_threshold=request.novelty_threshold,
                    novelty_characterization=request.novelty_characterization,
                    errormsgs=errormsgs)

                if not self.trial_budget_active:
                    # Check if they predicted novelty.
                    if request.novelty_probability is not None \
                            and request.novelty_threshold is not None:
                        if request.novelty_probability >= request.novelty_threshold:
                            self.trial_predicted_novelty = True
                            self.trial_budget_active = True

                # Respond with a TrainingEpisodeNoveltyAck.
                data = objects.TrainingEpisodeNoveltyAck()
        elif isinstance(request, objects.RequestTestingData):
            if not isinstance(self.STATE, objects.TestingEpisodeActive):
                errormsgs.append('ERROR: You are not allowed to request testing data outside '
                                 'of the TestingEpisodeActive state!')
            else:
                # Get the episode.
                episode = self._experiment.novelty_groups[self._exper_novelty_index]\
                              .trials[self._exper_trial_index]\
                              .episodes[self._exper_episode_index]
                current_episode = episode

                # Get the data to send.
                data = self.get_episode_data(request=request,
                                             episode=episode,
                                             errormsgs=errormsgs)
        elif isinstance(request, objects.TestingDataPrediction):
            if not isinstance(self.STATE, objects.TestingEpisodeActive):
                errormsgs.append('ERROR: Will not accept a TestingDataPrediction outside of the '
                                 'TestingEpisodeActive state!')
            else:
                if request.end_early:
                    self._exper_end_experiment_early = True
                # Get the episode.
                episode = self._experiment.novelty_groups[self._exper_novelty_index] \
                              .trials[self._exper_trial_index] \
                              .episodes[self._exper_episode_index]
                current_episode = episode
                # Get the trial.
                trial = self._experiment.novelty_groups[self._exper_novelty_index] \
                            .trials[self._exper_trial_index]

                # Process the prediction.
                data = self.process_episode_data_prediction(request=request,
                                                            episode=episode,
                                                            errormsgs=errormsgs)

                # Check to see if we received an objects.TestingEpisodeEnd.
                if isinstance(data, objects.EpisodeEnd):
                    self.stop_trial_episode(trial_episode_id=self.trial_episode_id,
                                            errormsgs=errormsgs)
                    # Check to see if we have a next testing episode.
                    next_episode_index = self._exper_episode_index + 1
                    if next_episode_index < len(trial.episodes) and \
                            not self._exper_end_experiment_early:
                        # We still have more testing episodes!
                        # Increment the testing episode index.
                        self._exper_episode_index += 1
                        self.STATE = objects.TestingEpisodeStart(
                            episode_number=self._exper_episode_index)
                    else:
                        # This was the last testing episode in the trial.
                        self.STATE = objects.TestingEnd()
                    self.log_message(
                        msg=LogMessage(model_experiment_id=self.model_experiment_id,
                                       action=data.obj_type,
                                       data_object=data.get_json_obj(),
                                       experiment_trial_id=self.experiment_trial_id))
        elif isinstance(request, objects.TestingEpisodeNovelty):
            if not isinstance(self.STATE, (objects.TestingEpisodeStart, objects.TestingEnd)):
                errormsgs.append('ERROR: Will not accept a TestingEpisodeNovelty in this state!')
            else:
                # Save the episode data.
                self.set_trial_episode_stats(
                    trial_episode_id=self.trial_episode_id,
                    novelty=request.novelty,
                    performance=self.trial_episode_performance,
                    novelty_probability=request.novelty_probability,
                    novelty_threshold=request.novelty_threshold,
                    novelty_characterization=request.novelty_characterization,
                    errormsgs=errormsgs)

                if not self.trial_budget_active:
                    # Check if they predicted novelty.
                    if request.novelty_probability is not None \
                            and request.novelty_threshold is not None:
                        if request.novelty_probability >= request.novelty_threshold:
                            self.trial_predicted_novelty = True
                            self.trial_budget_active = True

                # Respond with a TestingEpisodeNoveltyAck.
                data = objects.TestingEpisodeNoveltyAck()

        if len(errormsgs) > 0:
            response.add_error(
                casas_error=objects.CasasError(
                    error_type='error',
                    message='There were errors processing part or all of '
                            'your request, please see errors for details.',
                    error_dict=dict({'errors': errormsgs})))

        if props.reply_to is not None:
            if response.status == 'error':
                self.log.debug('RESPONSE: {}'.format(str(response.get_json())))
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=response,
                                           correlation_id=props.correlation_id)
            elif data is not None:
                self.log.debug('RESPONSE: {}'.format(str(data.get_json())))
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=data,
                                           correlation_id=props.correlation_id)

        self.log.debug('STATE: {}'.format(str(self.STATE)))

        if self.refresh_dataset_cache and current_episode is not None:
            # Get the next episode_id, episode_index, and dataset_id for the episode.
            episode_id = current_episode.episode_id
            episode_index = current_episode.episode_index
            dataset_id = self.get_episode_dataset_id(episode_id=episode_id,
                                                     episode_index=episode_index)
            # Get the current data_index for the episode.
            data_index = self.episode_cache[dataset_id][episode_index]['data_index']
            # Load the episode data to the data_cache.
            self.load_data_to_cache(
                episode_id=episode_id,
                at_data_index=data_index,
                errormsgs=errormsgs)

        if self.STATE is not None:
            self._AMQP_EXP_CALLBACK_ID = self.amqp.call_later(
                seconds=self._AMQP_EXPERIMENT_TIMEOUT,
                function=self.force_end_experiment)

        if self.is_profiling:
            if isinstance(self.STATE, objects.ExperimentEnd):
                self.amqp.stop()

        if isinstance(data, objects.AiqExperimentException):
            self.force_end_experiment()
        return

    def force_end_experiment(self):
        self.log.warning('force_end_experiment({})'.format(self.model_experiment_id))
        if self.experiment_type == objects.TYPE_EXPERIMENT_AIQ:
            if self.model_experiment_id is not None:
                self.log_message(msg=LogMessage(
                    model_experiment_id=copy.copy(self.model_experiment_id),
                    action='force_quit',
                    message=('Experiment timed out after {} seconds'.format(
                        self._AMQP_EXPERIMENT_TIMEOUT)),
                    experiment_trial_id=self.experiment_trial_id))
            errormsgs = list()
            if self.private_queue is not None:
                self.amqp.remove_subscribe_to_queue(queue_name=self.private_queue)
            self.subscribe_experiment_queue()
            self.subscribe_sota_queue()
            self.private_queue = None
            self.current_domain = None
            self.model_experiment_id = None
            self.experiment_trial_id = None
            self.trial_episode_id = None
            self.trial_episode_performance = None
            self.trial_predicted_novelty = False
            self.trial_budget_active = False
            self.experiment_type = None
            self.novelty_initiated = False
            self.novelty_visibility = 0
            self._experiment = None
            self._exper_train_index = None
            self._exper_novelty_index = None
            self._exper_trial_index = None
            self._exper_episode_index = None
            del self._exper_trial_novelty_desc
            self._exper_trial_novelty_desc = None
            self._exper_end_training_early = False
            self._exper_end_experiment_early = False
            self._exper_no_testing = False
            self._exper_no_training = False
            self._exper_just_one_trial = False
            self.benchmark_data = None
            self.STATE = None
            del self.domain_ids
            self.domain_ids = dict()
            del self.domain_cache
            self.domain_cache = list()
            del self.dataset_cache
            self.dataset_cache = dict()
            del self.episode_cache
            self.episode_cache = dict()
            del self.data_cache
            self.data_cache = dict()
            del self.rolling_score
            self.rolling_score = list()
            if self._AMQP_EXP_CALLBACK_ID is not None:
                self.amqp.cancel_call_later(timeout_id=self._AMQP_EXP_CALLBACK_ID)
                self._AMQP_EXP_CALLBACK_ID = None
        elif self.experiment_type == objects.TYPE_EXPERIMENT_SAIL_ON:
            if self.model_experiment_id is not None:
                self.log_message(msg=LogMessage(
                    model_experiment_id=copy.copy(self.model_experiment_id),
                    action='force_quit',
                    message=('Experiment timed out after {} seconds'.format(
                        self._AMQP_EXPERIMENT_TIMEOUT)),
                    experiment_trial_id=self.experiment_trial_id))
            errormsgs = list()
            if self.private_queue is not None:
                self.amqp.remove_subscribe_to_queue(queue_name=self.private_queue)
            self.subscribe_experiment_queue()
            self.subscribe_sota_queue()
            self.private_queue = None
            self.current_domain = None
            self.model_experiment_id = None
            self.experiment_trial_id = None
            self.trial_episode_id = None
            self.trial_episode_performance = None
            self.trial_predicted_novelty = False
            self.trial_budget_active = False
            self.experiment_type = None
            self.novelty_initiated = False
            self.novelty_visibility = 0
            self._experiment = None
            self._exper_train_index = None
            self._exper_novelty_index = None
            self._exper_trial_index = None
            self._exper_episode_index = None
            del self._exper_trial_novelty_desc
            self._exper_trial_novelty_desc = None
            self._exper_end_training_early = False
            self._exper_end_experiment_early = False
            self._exper_no_testing = False
            self._exper_no_training = False
            self._exper_just_one_trial = False
            self.benchmark_data = None
            self.STATE = None
            del self.domain_ids
            self.domain_ids = dict()
            del self.domain_cache
            self.domain_cache = list()
            del self.dataset_cache
            self.dataset_cache = dict()
            del self.episode_cache
            self.episode_cache = dict()
            del self.data_cache
            self.data_cache = dict()
            del self.rolling_score
            self.rolling_score = list()
            if self._live_thread is not None:
                self._live_thread.stop()
                self._live_thread.join()
                self._live_thread = None
            del self._ta2_response
            self._ta2_response = queue.Queue()
            del self._live_output
            self._live_output = queue.Queue()
            if self._AMQP_EXP_CALLBACK_ID is not None:
                self.amqp.cancel_call_later(timeout_id=self._AMQP_EXP_CALLBACK_ID)
                self._AMQP_EXP_CALLBACK_ID = None

        return


if __name__ == "__main__":
    parser = optparse.OptionParser(usage="usage: %prog [options]")
    parser.add_option("--config",
                      dest="config",
                      help="Custom AIQ-SAIL-ON TA1 config file.",
                      default="TA1.config")
    parser.add_option("--debug",
                      dest="debug",
                      action="store_true",
                      help="Set logging level to DEBUG from INFO.",
                      default=objects.DEFAULT_TA1_DEBUG)
    parser.add_option("--fulldebug",
                      dest="fulldebug",
                      action="store_true",
                      help="Set logging level to DEBUG from INFO for all imported libraries.",
                      default=objects.DEFAULT_TA1_FULLDEBUG)
    parser.add_option("--printout",
                      dest="printout",
                      action="store_true",
                      help="Print output to the screen at given logging level.",
                      default=objects.DEFAULT_TA1_PRINTOUT)
    parser.add_option("--logfile",
                      dest="logfile",
                      help="Custom location to write log data",
                      default=objects.DEFAULT_TA1_LOGFILE)
    parser.add_option("--testing",
                      dest="testing",
                      action="store_true",
                      help="Put TA1 in testing mode and limit datasets to 100 items.",
                      default=objects.DEFAULT_TA1_TESTING)
    parser.add_option("--demo",
                      dest="demo",
                      action="store_true",
                      help="Put TA1 in demo mode, limits episode size and trials.",
                      default=objects.DEFAULT_TA1_DEMO)
    parser.add_option("--shortdemo",
                      dest="shortdemo",
                      action="store_true",
                      help=("Put TA1 in shortdemo mode, REALLY limits the episode size "
                            "and trials."),
                      default=objects.DEFAULT_TA1_SHORTDEMO)
    (options, args) = parser.parse_args()
    if options.fulldebug:
        options.debug = True
    service = TA1(options)
    if service.is_profiling:
        cProfile.run('service.start()', 'TA1_stats.{}'.format(time.time()))
    else:
        service.start()

