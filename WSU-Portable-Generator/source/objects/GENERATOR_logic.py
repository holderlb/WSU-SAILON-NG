#!/usr/bin/env python3
# ************************************************************************************************ #
# **                                                                                            ** #
# **    AIQ-SAIL-ON Generator Core Logic                                                        ** #
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

from . import rabbitmq
from . import objects


class GeneratorLogic(object):
    def __init__(self, config_file: str, printout: bool, debug: bool, fulldebug: bool,
                 logfile: str, domain: str):
        self.agent_name = 'Generator'

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
        self.log = logging.getLogger(__name__).getChild(self.agent_name)
        self.log.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if logfile is not None:
            fh = logging.handlers.TimedRotatingFileHandler(logfile,
                                                           when='midnight',
                                                           backupCount=7)
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

        self.config_file = str(config_file)
        self.config = self._build_config_parser()
        self.config.read(self.config_file)

        self.amqp_user = self.config.get("amqp", "user")
        self.amqp_pass = self.config.get("amqp", "pass")
        self.amqp_host = self.config.get("amqp", "host")
        self.amqp_vhost = self.config.get("amqp", "vhost")
        self.amqp_port = self.config.getint("amqp", "port")
        self.amqp_ssl = self.config.getboolean("amqp", "ssl")

        self.keyboard_ended = False

        self._private_queue = None
        self.domain = None
        self.novelty = None
        self.difficulty = None
        self.seed = None
        self.trial_novelty = None
        self.day_offset = None
        self.is_episode_done = False
        self.use_image = False
        self.request_timeout = 30
        self.ta2_generator_config = None

        self.GENERATOR = None

        self.domain = self.config.get('sail-on', 'domain')
        if domain is not None:
            self.domain = domain

        if self.domain not in objects.VALID_DOMAINS:
            raise objects.AiqDataException('Invalid domain provided in config: {}'.format(
                self.domain))

        self.amqp = rabbitmq.Connection(agent_name=self.agent_name,
                                        amqp_user=self.amqp_user,
                                        amqp_pass=self.amqp_pass,
                                        amqp_host=self.amqp_host,
                                        amqp_port=self.amqp_port,
                                        amqp_vhost=self.amqp_vhost,
                                        amqp_ssl=self.amqp_ssl)

        self._timeout_callback_id = None
        self._subscribe_generator_queue()
        return

    @staticmethod
    def _build_config_parser():
        config = configparser.ConfigParser()
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

    def _subscribe_generator_queue(self):
        self.log.debug('_subscribe_generator_queue()')
        self.amqp.setup_subscribe_to_queue(
            queue_name=objects.LIVE_GENERATOR_QUEUES[self.domain],
            queue_durable=True,
            queue_exclusive=False,
            queue_auto_delete=False,
            casas_events=True,
            callback_function=self.on_generator_request,
            auto_ack=False,
            callback_full_params=True)
        self.amqp.setup_subscribe_to_queue(
            queue_name=objects.NOVELTY_DESC_RPC_QUEUE,
            queue_durable=True,
            queue_exclusive=False,
            queue_auto_delete=False,
            casas_events=True,
            callback_function=self.on_novelty_description_request,
            auto_ack=False,
            callback_full_params=True)
        return

    def _unsubscribe_generator_queue(self):
        self.log.debug('_subscribe_generator_queue()')
        self.amqp.remove_subscribe_to_queue(
            queue_name=objects.LIVE_GENERATOR_QUEUES[self.domain])
        self.amqp.remove_subscribe_to_queue(
            queue_name=objects.NOVELTY_DESC_RPC_QUEUE)
        return

    def _subscribe_private_queue(self):
        self.log.debug('_subscribe_private_queue()')
        if self._private_queue is None:
            self._private_queue = '{}.{}'.format(objects.GENERATOR_RPC_QUEUE,
                                                 str(uuid.uuid4().hex))
            self.amqp.setup_subscribe_to_queue(
                queue_name=self._private_queue,
                queue_exclusive=True,
                queue_auto_delete=True,
                casas_events=True,
                callback_function=self.on_data_request,
                callback_full_params=True)
        return

    def _unsubscribe_private_queue(self):
        self.log.debug('_unsubscribe_private_queue()')
        if self._private_queue is not None:
            self.amqp.remove_subscribe_to_queue(
                queue_name=self._private_queue)
            self._private_queue = None
        return

    def _reset_timeout(self):
        self.log.debug('_reset_timeout()')
        if self._timeout_callback_id is not None:
            self.amqp.cancel_call_later(timeout_id=self._timeout_callback_id)
        self._timeout_callback_id = self.amqp.call_later(
            seconds=self.request_timeout,
            function=self._reset_system)
        return

    def _reset_system(self):
        self.log.debug('_reset_system()')
        self._unsubscribe_private_queue()
        self._subscribe_generator_queue()

        self.cleanup_generator()

        if self._timeout_callback_id is not None:
            self.amqp.cancel_call_later(timeout_id=self._timeout_callback_id)
        self._timeout_callback_id = None
        return

    def on_novelty_description_request(self, ch, method, props, body, request):
        self.log.debug('on_novelty_description_request( {} )'.format(str(request)))

        response = None

        if isinstance(request, objects.RequestNoveltyDescription):
            novelty_description = self.get_novelty_description(domain=request.domain,
                                                               novelty=request.novelty,
                                                               difficulty=request.difficulty)
            response = objects.NoveltyDescription(novelty_description=novelty_description)

            if props.reply_to is not None:
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=response,
                                           correlation_id=props.correlation_id)

                self._reset_timeout()
        return

    def on_generator_request(self, ch, method, props, body, request):
        self.log.info('on_generator_request( {} )'.format(str(request)))

        response = None

        if isinstance(request, objects.StartGenerator):
            self.novelty = request.novelty
            self.difficulty = request.difficulty
            self.seed = request.seed
            self.trial_novelty = request.trial_novelty
            self.day_offset = request.day_offset
            self.use_image = request.use_image
            self.request_timeout = request.request_timeout
            self.ta2_generator_config = request.generator_config

            self.initilize_generator(domain=self.domain,
                                     novelty=self.novelty,
                                     difficulty=self.difficulty,
                                     seed=self.seed,
                                     trial_novelty=self.trial_novelty,
                                     day_offset=self.day_offset,
                                     use_image=self.use_image,
                                     ta2_generator_config=self.ta2_generator_config)
            self._unsubscribe_generator_queue()
            self._subscribe_private_queue()

            response = objects.GeneratorResponse(generator_rpc_queue=self._private_queue)

            if props.reply_to is not None:
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=response,
                                           correlation_id=props.correlation_id)

                self._reset_timeout()
        return

    def on_data_request(self, ch, method, props, body, request):
        self.log.debug('on_data_request( {} )'.format(str(request)))
        response = None

        if isinstance(request, objects.RequestData):
            feature_vector, feature_label = self.get_feature_vector()

            response = objects.BasicData(feature_vector=feature_vector,
                                         feature_label=feature_label)
        elif isinstance(request, objects.BasicDataPrediction):
            performance = self.apply_action(label_prediction=request.label_prediction)

            self.log.debug('self.is_episode_done = {}'.format(self.is_episode_done))
            if not self.is_episode_done:
                response = objects.BasicDataAck(performance=performance)
            else:
                response = objects.EpisodeEnd(performance=performance)
        elif isinstance(request, objects.GeneratorReset):
            if props.reply_to is not None:
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=request,
                                           correlation_id=props.correlation_id)
            self.log.info('TA1 sent GeneratorReset, cleaning up.')
            self._reset_system()

        if response is not None:
            if props.reply_to is not None:
                self.amqp.publish_to_queue(queue_name=props.reply_to,
                                           casas_object=response,
                                           correlation_id=props.correlation_id)

                self._reset_timeout()

            if isinstance(response, objects.EpisodeEnd):
                self._reset_system()
        return

    def _run_sail_on(self):
        self.log.debug('_run_sail_on()')
        try:
            self.amqp.run()
            self.amqp.start_consuming()
        except KeyboardInterrupt:
            self.stop()
            self.keyboard_ended = True
        except objects.AiqExperimentException as e:
            self.log.error(e.value)
            self.stop()
        return

    def run(self):
        self.log.debug('run()')
        while not self.keyboard_ended:
            self._run_sail_on()
        return

    def stop(self):
        self.log.debug('stop()')
        self.amqp.stop()
        return

    def get_novelty_description(self, domain: str, novelty: int, difficulty: str) -> dict:
        raise ValueError('get_novelty_description() not defined in client.')

    def initilize_generator(self, domain: str, novelty: int, difficulty: str, seed: int,
                            trial_novelty: int, day_offset: int, use_image: bool,
                            ta2_generator_config: dict):
        raise ValueError('initilize_generator() not defined in client.')

    def get_feature_vector(self) -> (dict, dict):
        raise ValueError('get_feature_vector() not defined in client.')

    def apply_action(self, label_prediction: dict) -> float:
        raise ValueError('apply_action() not defined in client.')

    def cleanup_generator(self):
        raise ValueError('cleanup_generator() not defined in client.')

