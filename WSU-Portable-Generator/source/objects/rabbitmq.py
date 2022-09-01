# *****************************************************************************#
# **
# **  CASAS RabbitMQ Python Library
# **
# **    Brian L Thomas, 2017-2020
# **
# ** Tools by the Center for Advanced Studies in Adaptive Systems at
# **  the School of Electrical Engineering and Computer Science at
# **  Washington State University
# **
# ** Copyright Washington State University, 2020
# ** Copyright Brian L. Thomas, 2020
# **
# ** All rights reserved
# ** Modification, distribution, and sale of this work is prohibited without
# **  permission from Washington State University
# **
# ** If this code is used for public research, any resulting publications need
# ** to cite work done by Brian L. Thomas at the Center for Advanced Study of
# ** Adaptive Systems (CASAS) at Washington State University.
# **
# ** Contact: Brian L. Thomas (bthomas1@wsu.edu)
# ** Contact: Diane J. Cook (djcook@wsu.edu)
# *****************************************************************************#
import copy
import datetime
import json
import logging
import logging.handlers
import pika
import pytz
import re
import socket
import threading
import time
import uuid

from . import objects


class ConsumeCallback(object):
    """This is a helper class for subscribing to RabbitMQ exchanges and queues then using
    callback functions with the processed results.

    """

    def __init__(self, casas_events=True, callback_function=None,
                 is_exchange=False, exchange_name=None, is_queue=False,
                 queue_name=None, limit_to_sensor_types=None, auto_ack=False,
                 callback_full_params=False, translations=None,
                 timezone=None, manual_ack=False):
        """Initialize an instance of a ConsumeCallback object.

        Parameters
        ----------
        casas_events : bool
            Boolean defining if this exchange will be sending casas events.
        callback_function : function
            The callback function to call when events from this queue binding arrive.
        is_exchange : bool
            Boolean defining if we are subscribed to an exchange.
        exchange_name : str
            Name of the RabbitMQ exchange.
        is_queue : bool
            Boolean defining if we are subscribed to a queue.
        queue_name : str
            Name of the RabbitMQ queue.
        limit_to_sensor_types : list
            A list that will define what sensor types will be allowed through.
            All sensors are allowed through by default.
        auto_ack : bool
            Boolean that if set to True, automatic acknowledgement mode will be used
        callback_full_params : bool
            Boolean defining if the callback_function will be expecting the full callback
            parameters (channel, method, properties, body) or just body.
        translations : dict
            A dictionary of TranslationGroup objects.
            translations[SITE] = TranslationGroup
        timezone : dict
            A dictionary of sites as keys, with the value as the timezone string for that site.
            Assumes all sites are 'America/Los_Angeles' unless given in dict().
        manual_ack : bool, optional
            Boolean that determines if the calling program will manually be sending the message
            ack.  This variable is overridden to False if auto_ack is True or if
            callback_full_params is False (as you need those to send the ack).  The default value
            is False.
        """
        self.log = logging.getLogger(__name__).getChild('ConsumeCallback')
        self.casas_events = casas_events
        self.callback_function = callback_function
        self.is_exchange = is_exchange
        self.exchange_name = exchange_name
        self.is_queue = is_queue
        self.queue_name = queue_name
        # Check for a sentinel value, if there assign an empty list.
        if limit_to_sensor_types is not None:
            self.limit_to_sensor_types = copy.deepcopy(limit_to_sensor_types)
        else:
            self.limit_to_sensor_types = list()
        self.is_limiting = False
        if len(self.limit_to_sensor_types) > 0:
            self.is_limiting = True
        self.auto_ack = auto_ack
        self.callback_full_params = callback_full_params
        # Check for a sentinel value, if there assign an empty dictionary.
        if translations is not None:
            self.translations = copy.deepcopy(translations)
        else:
            self.translations = dict()
        # Check for a sentinel value, if there assign an empty dictionary.
        if timezone is not None:
            self.timezone = copy.deepcopy(timezone)
        else:
            self.timezone = dict()
        self.manual_ack = manual_ack
        if auto_ack is True:
            self.manual_ack = False
        return

    def on_message(self, channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        Parameters
        ----------
        channel : pika.channel.Channel
            The channel object.
        basic_deliver : pika.Spec.Basic.Deliver
            basic_deliver method.
        properties : pika.Spec.BasicProperties
            properties object.
        body : str|unicode
            The message body.
        """
        self.log.debug("on_message({})".format(str(body)))

        if self.casas_events:
            obj = objects.build_objects_from_json(body)
            self.log.debug("obj = {}".format(str(obj)))
            self.log.debug("size of obj = {}".format(str(len(obj))))
            if len(obj) > 0:
                if self.callback_full_params:
                    self.callback_function(channel, basic_deliver, properties, body, obj[0])
                else:
                    self.callback_function(obj[0])
        else:
            if self.callback_full_params:
                self.callback_function(channel, basic_deliver, properties, body)
            else:
                self.callback_function(body)

        if not self.auto_ack and not self.manual_ack:
            channel.basic_ack(delivery_tag=basic_deliver.delivery_tag)
        return


class Connection:
    """
    This is a consumer that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.

    If RabbitMQ closes the connection, it will reopen it. You should
    look at the output, as there are limited reasons why the connection may
    be closed, which usually are tied to permission related issues or
    socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.
    """

    def __init__(self, agent_name, amqp_user, amqp_pass, amqp_host, amqp_port,
                 amqp_vhost='/', amqp_ssl=True, translations=None,
                 timezone=None, request_timeout=None):
        """
        Create a new instance of the CASAS RammitMQ Connection class.

        Parameters
        ----------
        agent_name : str
            The name of the agent using the RabbitMQ connection, used in logging and debugging.
        amqp_user : str
            The RabbitMQ username.
        amqp_pass : str
            The RabbitMQ password.
        amqp_host : str
            The RabbitMQ hostname.
        amqp_port : str
            The RabbitMQ port to use for connecting.
        amqp_vhost : str,optional
            The RabbitMQ virtual host to connect to, with a default value of '/'.
        amqp_ssl : bool,optional
            Defines if using SSL to make the connection to the RabbitMQ server.
        translations : dict,optional
            A dictionary of dictionaries with format
            translations[SITE][TARGET] = (sensor_1,sensor_2)
        timezone : dict,optional
            A dictionary of sites as keys, with the value as the timezone string for that site.
            Assumes all sites are 'America/Los_Angeles' unless given in dict().
        request_timeout : int,optional
            An integer of the global timeout to use.
        """
        self.name = re.sub('\s', '', str(agent_name))
        self.log = logging.getLogger(__name__).getChild('Connection')

        self._connection = None
        self._channel = None
        self._closing = False
        self._has_on_cancel_callback = False

        # To subscribe to an exchange we need:
        #     - an exclusive queue to bind to the exchange
        #       val = "{}.{}".format(self.name, str(uuid.uuid4().hex))
        #     - the exchange type ('topic')
        #     - the exchange durable type (True/False)
        #     - a routing key for the exchange
        #     - a callback function to call when we get a message
        self._exchanges_subscribe = list()
        self._exchanges_publish = list()
        self._queues_subscribe = list()
        self._queues_publish = list()

        self._on_connect_callback = None
        self._on_disconnect_callback = None
        self._on_connection_blocked_callback = None
        self._on_connection_unblocked_callback = None
        self._on_request_callbacks = dict()
        self._on_request_events = dict()
        self._waiting_on_request = False
        self._waiting_on_events = False
        self._is_consuming = False
        self._request_response = dict()
        self._model_experiment_id = None
        self._model_experiment_secret = None
        self._server_experiment_rpc_queue = None
        self._client_rpc_queue = None
        self._local_epoch_received = time.time()

        self.amqp_user = amqp_user
        self.amqp_pass = amqp_pass
        self.amqp_host = amqp_host
        self.amqp_port = amqp_port
        self.amqp_vhost = amqp_vhost
        self.amqp_ssl = amqp_ssl
        self.amqp_url_start = "amqp://"
        if self.amqp_ssl:
            self.amqp_url_start = "amqps://"
        # Check for a sentinel value, if there assign an empty dictionary.
        if translations is not None:
            self.translations = copy.deepcopy(translations)
        else:
            self.translations = dict()
        self.timezone = dict()
        self.timezone['default'] = pytz.timezone('America/Los_Angeles')
        if isinstance(timezone, dict):
            for key in list(timezone.keys()):
                self.timezone[str(key)] = pytz.timezone(str(timezone[key]))

        self._request_timeout = objects.GLOBAL_TIMEOUT_SECONDS
        if request_timeout is not None:
            self._request_timeout = request_timeout

        self._url = "{}{}:{}@{}:{}{}".format(str(self.amqp_url_start),
                                             str(self.amqp_user),
                                             str(self.amqp_pass),
                                             str(self.amqp_host),
                                             str(self.amqp_port),
                                             str(self.amqp_vhost))
        return

    def set_on_connect_callback(self, callback):
        """Set a callback function to call when the agent has connected.

        Parameters
        ----------
        callback : function
            The callback function that will be called after a connection is established.
            The function can not require any parameters.
        """
        self._on_connect_callback = callback
        return

    def clear_on_connect_callback(self):
        """Clear a callback function that may or may not have been set for on_connect.
        """
        self._on_connect_callback = None
        return

    def set_on_disconnect_callback(self, callback):
        """Set a callback function to call when the agent has been disconnected.

        Parameters
        ----------
        callback : function
            The callback function that will be called after the agent has been disconnected.
            The function can not require any parameters.
        """
        self._on_disconnect_callback = callback
        return

    def clear_on_disconnect_callback(self):
        """Clear a callback function that may or may not have been set for on_disconnect.
        """
        self._on_disconnect_callback = None
        return

    def set_on_connection_blocked_callback(self, callback):
        """Set a callback function to call when the agent has been blocked from publishing.

        Parameters
        ----------
        callback : function
            The callback function that will be called after the agent has been blocked from
            publishing.
            The function can not require any parameters.
        """
        self._on_connection_blocked_callback = callback

        if self._channel:
            self._add_on_connection_blocked_callback()
        return

    def clear_on_connection_blocked_callback(self):
        """Clear a callback function that may or may not have been set for on_connection_blocked.
        """
        self._on_connection_blocked_callback = None
        return

    def set_on_connection_unblocked_callback(self, callback):
        """Set a callback function to call when the agent has been unblocked from publishing.

        Parameters
        ----------
        callback : function
            The callback function that will be called after the agent has been unblocked from
            publishing.
            The function can not require any parameters.
        """
        self._on_connection_unblocked_callback = callback

        if self._channel:
            self._add_on_connection_unblocked_callback()
        return

    def clear_on_connection_unblocked_callback(self):
        """Clear a callback function that may or may not have been set for on_connection_unblocked.
        """
        self._on_connection_unblocked_callback = None
        return

    def get_state(self):
        self.log.debug('get_state()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established an experiment yet!')

        state_request = objects.RequestState()

        response = self._set_system_request(casas_object=state_request,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        return response

    def start_aiq_experiment(self, model: objects.Model, seed: int = None,
                             domain_dict: dict = None, description: str = None):
        self.log.debug('start_aiq_experiment()')

        if self._client_rpc_queue is None:
            self._client_rpc_queue = objects.CLIENT_RPC_QUEUE + '.{}'.format(str(uuid.uuid4().hex))
            # Subscribe to the callback queue.
            self.setup_subscribe_to_queue(
                queue_name=self._client_rpc_queue,
                queue_exclusive=True,
                queue_auto_delete=True,
                casas_events=True,
                callback_function=self.process_system_request_callback,
                callback_full_params=True)

        experiment_request = objects.RequestExperiment(model=model,
                                                       novelty=0,
                                                       novelty_visibility=0,
                                                       client_rpc_queue=self._client_rpc_queue,
                                                       git_version=objects.__version__,
                                                       experiment_type=objects.TYPE_EXPERIMENT_AIQ,
                                                       seed=seed,
                                                       domain_dict=domain_dict,
                                                       description=description)

        response = self._set_system_request(casas_object=experiment_request,
                                            queue_name=objects.SERVER_EXPERIMENT_QUEUE,
                                            client_callback_queue=self._client_rpc_queue,
                                            disable_timeout=True)
        return response

    def start_sail_on_experiment(self, model: objects.Model, domain: str, no_testing: bool,
                                 seed: int = None, description: str = None,
                                 generator_config: dict = None):
        self.log.debug('start_sail_on_experiment()')

        if domain not in objects.VALID_DOMAINS:
            raise objects.AiqDataException('{} is not a VALID domain choice.'.format(domain))

        if self._client_rpc_queue is None:
            self._client_rpc_queue = objects.CLIENT_RPC_QUEUE + '.{}'.format(str(uuid.uuid4().hex))
            # Subscribe to the callback queue.
            self.setup_subscribe_to_queue(
                queue_name=self._client_rpc_queue,
                queue_exclusive=True,
                queue_auto_delete=True,
                casas_events=True,
                callback_function=self.process_system_request_callback,
                callback_full_params=True)

        domain_dict = dict({domain: True})

        experiment_request = objects.RequestExperiment(
            model=model,
            novelty=0,
            novelty_visibility=0,
            client_rpc_queue=self._client_rpc_queue,
            git_version=objects.__version__,
            experiment_type=objects.TYPE_EXPERIMENT_SAIL_ON,
            seed=seed,
            domain_dict=domain_dict,
            no_testing=no_testing,
            description=description,
            generator_config=generator_config)

        response = self._set_system_request(casas_object=experiment_request,
                                            queue_name=objects.SERVER_EXPERIMENT_QUEUE,
                                            client_callback_queue=self._client_rpc_queue,
                                            disable_timeout=True)
        return response

    def start_work_on_experiment_trials(self, model: objects.Model, experiment_secret: str,
                                        just_one_trial: bool, domain: str,
                                        generator_config: dict = None):
        self.log.debug('start_work_on_experiment_trials()')

        if self._client_rpc_queue is None:
            self._client_rpc_queue = objects.CLIENT_RPC_QUEUE + '.{}'.format(str(uuid.uuid4().hex))
            # Subscribe to the callback queue.
            self.setup_subscribe_to_queue(
                queue_name=self._client_rpc_queue,
                queue_exclusive=True,
                queue_auto_delete=True,
                casas_events=True,
                callback_function=self.process_system_request_callback,
                callback_full_params=True)

        domain_dict = dict({domain: True})

        experiment_request = objects.RequestExperimentTrials(
            model=model,
            experiment_secret=experiment_secret,
            client_rpc_queue=self._client_rpc_queue,
            experiment_type=objects.TYPE_EXPERIMENT_SAIL_ON,
            just_one_trial=just_one_trial,
            domain_dict=domain_dict,
            generator_config=generator_config)

        response = self._set_system_request(casas_object=experiment_request,
                                            queue_name=objects.SERVER_EXPERIMENT_QUEUE,
                                            client_callback_queue=self._client_rpc_queue,
                                            disable_timeout=True)
        return response

    def register_as_sota(self, model: objects.Model, domain: str, no_testing: bool,
                         seed: int = None, description: str = None):
        self.log.debug('start_sail_on_experiment()')

        if domain not in objects.VALID_DOMAINS:
            raise objects.AiqDataException('{} is not a VALID domain choice.'.format(domain))

        if self._client_rpc_queue is None:
            self._client_rpc_queue = objects.CLIENT_RPC_QUEUE + '.{}'.format(str(uuid.uuid4().hex))
            # Subscribe to the callback queue.
            self.setup_subscribe_to_queue(
                queue_name=self._client_rpc_queue,
                queue_exclusive=True,
                queue_auto_delete=True,
                casas_events=True,
                callback_function=self.process_system_request_callback,
                callback_full_params=True)

        domain_dict = dict({domain: True})

        experiment_request = objects.RequestExperiment(
            model=model,
            novelty=0,
            novelty_visibility=0,
            client_rpc_queue=self._client_rpc_queue,
            git_version=objects.__version__,
            experiment_type=objects.TYPE_EXPERIMENT_SAIL_ON_SOTA,
            seed=seed,
            domain_dict=domain_dict,
            no_testing=no_testing,
            description=description)

        response = self._set_system_request(casas_object=experiment_request,
                                            queue_name=objects.REGISTER_SOTA_QUEUE,
                                            client_callback_queue=self._client_rpc_queue,
                                            disable_timeout=True)
        return response

    def start_work_on_sota_trials(self, model: objects.Model, experiment_secret: str,
                                  just_one_trial: bool, domain: str):
        self.log.debug('start_work_on_sota_trials()')

        if self._client_rpc_queue is None:
            self._client_rpc_queue = objects.CLIENT_RPC_QUEUE + '.{}'.format(str(uuid.uuid4().hex))
            # Subscribe to the callback queue.
            self.setup_subscribe_to_queue(
                queue_name=self._client_rpc_queue,
                queue_exclusive=True,
                queue_auto_delete=True,
                casas_events=True,
                callback_function=self.process_system_request_callback,
                callback_full_params=True)

        domain_dict = dict({domain: True})

        experiment_request = objects.RequestExperimentTrials(
            model=model,
            experiment_secret=experiment_secret,
            client_rpc_queue=self._client_rpc_queue,
            experiment_type=objects.TYPE_EXPERIMENT_SAIL_ON_SOTA,
            just_one_trial=just_one_trial,
            domain_dict=domain_dict)

        response = self._set_system_request(casas_object=experiment_request,
                                            queue_name=objects.REGISTER_SOTA_QUEUE,
                                            client_callback_queue=self._client_rpc_queue,
                                            disable_timeout=True)
        return response

    def start_generator(self, domain: str, novelty: int, difficulty: str, seed: int,
                        trial_novelty: int, day_offset: int, request_timeout: int, use_image: bool,
                        hint_level: int, phase: str, generator_config: dict = None):
        self.log.debug('start_generator()')

        if self._client_rpc_queue is None:
            self._client_rpc_queue = objects.SERVER_RPC_QUEUE + '.{}'.format(str(uuid.uuid4().hex))
            # Subscribe to the callback queue.
            self.setup_subscribe_to_queue(
                queue_name=self._client_rpc_queue,
                queue_exclusive=True,
                queue_auto_delete=True,
                casas_events=True,
                callback_function=self.process_system_request_callback,
                callback_full_params=True)

        start_gen = objects.StartGenerator(
            domain=domain,
            novelty=novelty,
            difficulty=difficulty,
            seed=seed,
            server_rpc_queue=self._client_rpc_queue,
            trial_novelty=trial_novelty,
            day_offset=day_offset,
            request_timeout=request_timeout,
            use_image=use_image,
            generator_config=generator_config,
            hint_level=hint_level,
            phase=phase)

        response = self._set_system_request(casas_object=start_gen,
                                            queue_name=objects.LIVE_GENERATOR_QUEUES[domain],
                                            client_callback_queue=self._client_rpc_queue,
                                            disable_timeout=True)
        return response

    def get_novelty_description(self, domain: str, novelty: int, difficulty: str):
        self.log.debug('get_novelty_description(domain={}, novelty={}, difficulty={})'.format(
            domain, novelty, difficulty))

        req_nov_desc = objects.RequestNoveltyDescription(r_domain=domain,
                                                         novelty=novelty,
                                                         difficulty=difficulty)
        response = self._set_system_request(casas_object=req_nov_desc,
                                            queue_name=objects.NOVELTY_DESC_RPC_QUEUE)
        return response

    def send_generator_data(self, data_request):
        self.log.debug('send_generator_data()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established a generator yet!')

        response = self._set_system_request(casas_object=data_request,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        return response

    def send_benchmark_data(self, benchmark_data: dict):
        self.log.debug('send_benchmark_data()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established an experiment yet!')

        data = objects.BenchmarkData(benchmark_data=benchmark_data)

        response = self._set_system_request(casas_object=data,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        return response

    def get_training_data(self):
        self.log.debug('get_training_data()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established an experiment yet!')

        training_data_request = objects.RequestTrainingData(
            model_experiment_id=self._model_experiment_id,
            secret=self._model_experiment_secret)

        response = self._set_system_request(casas_object=training_data_request,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        return response

    def send_training_predictions(self, label_prediction: dict, end_early: bool = False):
        self.log.debug('send_training_prediction()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established an experiment yet!')

        training_prediction = objects.TrainingDataPrediction(
            secret=self._model_experiment_secret,
            label_prediction=label_prediction,
            end_early=end_early)

        response = self._set_system_request(casas_object=training_prediction,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        return response

    def send_training_episode_novelty(self, novelty_characterization: dict,
                                      novelty_probability: float = 0.0,
                                      novelty_threshold: float = 0.0, novelty: int = 0):
        self.log.debug('send_training_episode_novelty()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established an experiment yet!')

        training_episode_novelty = objects.TrainingEpisodeNovelty(
            novelty_probability=novelty_probability,
            novelty_threshold=novelty_threshold,
            novelty=novelty,
            novelty_characterization=novelty_characterization)

        response = self._set_system_request(casas_object=training_episode_novelty,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        return response

    def end_training_early(self):
        self.log.debug('end_training_early()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established an experiment yet!')

        training_end_early = objects.TrainingEndEarly()

        response = self._set_system_request(casas_object=training_end_early,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        return response

    def get_testing_data(self):
        self.log.debug('get_testing_data()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established an experiment yet!')

        testing_data_request = objects.RequestTestingData(
            model_experiment_id=self._model_experiment_id,
            secret=self._model_experiment_secret)

        response = self._set_system_request(casas_object=testing_data_request,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        return response

    def send_testing_predictions(self, label_prediction: dict, end_early: bool = False):
        self.log.debug('send_testing_predictions()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established an experiment yet!')

        testing_prediction = objects.TestingDataPrediction(
            secret=self._model_experiment_secret,
            label_prediction=label_prediction,
            end_early=end_early)

        response = self._set_system_request(casas_object=testing_prediction,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        return response

    def send_testing_episode_novelty(self, novelty_characterization: dict,
                                     novelty_probability: float = 0.0,
                                     novelty_threshold: float = 0.0, novelty: int = 0):
        self.log.debug('send_testing_episode_novelty()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established an experiment yet!')

        testing_episode_novelty = objects.TestingEpisodeNovelty(
            novelty_probability=novelty_probability,
            novelty_threshold=novelty_threshold,
            novelty=novelty,
            novelty_characterization=novelty_characterization)

        response = self._set_system_request(casas_object=testing_episode_novelty,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        return response

    def end_experiment(self):
        self.log.debug('end_experiment()')

        if self._server_experiment_rpc_queue is None:
            raise objects.CasasRabbitMQException('You have not established an experiment yet!')

        end_experiment_request = objects.EndExperiment(
            model_experiment_id=self._model_experiment_id,
            secret=self._model_experiment_secret)

        response = self._set_system_request(casas_object=end_experiment_request,
                                            queue_name=self._server_experiment_rpc_queue,
                                            declare_server_queue=False,
                                            client_callback_queue=self._client_rpc_queue)
        self.remove_subscribe_to_queue(self._client_rpc_queue)
        self._client_rpc_queue = None
        self._model_experiment_id = None
        self._model_experiment_secret = None
        self._server_experiment_rpc_queue = None
        return

    def _set_system_request(self, casas_object, key=None, secret=None,
                            queue_name=objects.QUEUE_SYSTEM_REQUESTS, declare_server_queue=True,
                            client_callback_queue=None, disable_timeout=False):
        """Helper function for processing all casas.objects classes when they are being sent to the
        system request processor in the cloud.  This function does not return until the system
        request has been processed and returned.

        Parameters
        ----------
        casas_object : objects.CasasObject
            The casas object that will be sent up to CommandProcessor and added to the database if
            the key and secret are not None.
        key : str, optional
            The key value that is paired with secret for uploading objects to the database.
        secret : str, optional
            The secret value that is paired with key for uploading objects to the database.
        queue_name : str, optional
            The name of the queue to send the event to.

        Raises
        ------
        objects.CasasRabbitMQException
            If the connection is currently in the consuming state and not able to be utilized for
            RPC type calls right now.
        """
        # Check to see if Connection is consuming, if so, then raise objects.CasasRabbitMQException.
        if self._is_consuming:
            raise objects.CasasRabbitMQException('The connection is currently in the consuming '
                                                 'state and can not be used for RPC methods '
                                                 'right now!')
        self._waiting_on_request = True
        start_time = float(time.time())
        max_time_delta = self._request_timeout
        response = None
        while response is None:
            if not disable_timeout:
                if abs(float(time.time()) - start_time) > max_time_delta:
                    raise objects.AiqExperimentException('Server took too long to respond.')
            corr_id = str(uuid.uuid4())
            if client_callback_queue is None:
                callback_queue = 'rpc.system.request.{}'.format(str(uuid.uuid4().hex))
            else:
                callback_queue = client_callback_queue
            try:
                self._on_request_callbacks[corr_id] = dict()
                self._on_request_callbacks[corr_id]['casas_object'] = casas_object
                self._on_request_callbacks[corr_id]['queue'] = callback_queue
                self._on_request_callbacks[corr_id]['corr_id'] = corr_id
                self._on_request_callbacks[corr_id]['publish_queue'] = queue_name
                self._on_request_callbacks[corr_id]['keep_queue'] = True
                if client_callback_queue is None:
                    self._on_request_callbacks[corr_id]['keep_queue'] = False
                    # Subscribe to the callback queue.
                    self.setup_subscribe_to_queue(
                        queue_name=callback_queue,
                        queue_exclusive=True,
                        queue_auto_delete=True,
                        casas_events=True,
                        callback_function=self.process_system_request_callback,
                        callback_full_params=True)

                self._request_response[corr_id] = None

                # Declare the queue we are going to publish to.
                if declare_server_queue:
                    self.setup_publish_to_queue(queue_name=queue_name,
                                                queue_durable=True,
                                                queue_exclusive=False,
                                                queue_auto_delete=False)

                if isinstance(casas_object, (objects.TrainingDataPrediction,
                                             objects.TestingDataPrediction)):
                    casas_object.utc_remote_epoch_received = self._local_epoch_received
                # Publish the system request casas_object and then return.
                self.publish_to_queue(queue_name=queue_name,
                                      casas_object=casas_object,
                                      correlation_id=corr_id,
                                      delivery_mode=1,
                                      key=key,
                                      secret=secret,
                                      reply_to=callback_queue)

                if disable_timeout:
                    while self._request_response[corr_id] is None:
                        self.process_data_events(time_limit=0.02)
                    response = copy.deepcopy(self._request_response[corr_id])
                    del self._request_response[corr_id]
                else:
                    while self._request_response[corr_id] is None and \
                            abs(float(time.time()) - start_time) < max_time_delta:
                        self.process_data_events(time_limit=0.05)
                    if self._request_response[corr_id] is not None:
                        response = copy.deepcopy(self._request_response[corr_id])
                        del self._request_response[corr_id]
            except pika.exceptions.AMQPError:
                self.log.error('_set_system_request(): pika.exceptions.AMQPError '
                               'AMQP failed, trying again.')
                self.stop()
                time.sleep(1)
                self.run(timeout=max_time_delta)
                if client_callback_queue is None:
                    self.remove_subscribe_to_queue(callback_queue)
        self._waiting_on_request = False
        return response

    def process_system_request_callback(self, ch, method, props, body, response):
        """This is a callback function for processing the response to the getting or setting of a
        system request type object.

        Parameters
        ----------
        ch : pika.channel.Channel
            The channel object.
        method : pika.Spec.Basic.Deliver
            Basic deliver method.
        props : pika.Spec.BasicProperties
            Properties of the message.
        body : str|unicode
            The message body.
        response : list
            A list of processed casas.objects that have been built from the JSON provided in
            the message body.
        """
        self.log.info('process_system_request_callback( {} )'.format(body))
        corr_id = props.correlation_id
        if corr_id in self._on_request_callbacks:
            # Remove our publish to the queue.
            self.remove_publish_to_queue(self._on_request_callbacks[corr_id]['publish_queue'])
            if not self._on_request_callbacks[corr_id]['keep_queue']:
                # Remove our subscription to the callback queue.
                self.remove_subscribe_to_queue(self._on_request_callbacks[corr_id]['queue'])

            if isinstance(response, (objects.TrainingData, objects.TestingData)):
                self._local_epoch_received = response.utc_remote_epoch_received
            elif isinstance(response, objects.ExperimentResponse):
                self._request_timeout = response.experiment_timeout
                self._model_experiment_id = response.model_experiment_id
                self._model_experiment_secret = response.experiment_secret
                self._server_experiment_rpc_queue = response.server_rpc_queue
            elif isinstance(response, objects.GeneratorResponse):
                self._server_experiment_rpc_queue = response.generator_rpc_queue
            elif isinstance(response, objects.ExperimentEnd):
                self.remove_subscribe_to_queue(self._client_rpc_queue)
                self._client_rpc_queue = None
                self._model_experiment_id = None
                self._model_experiment_secret = None
                self._server_experiment_rpc_queue = None

            # We have finished processing this system request callback, now we remove the
            # entry from our dict().
            del self._on_request_callbacks[corr_id]
            self._request_response[corr_id] = response
            self.log.info('_request_response[{}] = {}'.format(corr_id,
                                                              self._request_response[corr_id]))
        return

    def request_dataset(self, site, start_stamp, end_stamp, experiment, dataset, key, secret,
                        sensor_types=None, callback=None, completed_callback=None,
                        callback_full_params=False, manual_ack=False):
        """Request a dataset be sent to a provided function, event-by-event.

        Parameters
        ----------
        site : str
            The testbed that this request is for.
        start_stamp : datetime.datetime
            The UTC timestamp for the start of the requested window of data.
        end_stamp : datetime.datetime
            The UTC timestamp for the end of the request window of data.
        experiment : str
            The name of the experiment we wish to get data from.
        dataset : str
            The name of the dataset we wish to get data from.
        key : str
            The key value that is paired with secret for accessing data.
        secret : str
            The secret value that is paired with key for accessing data.
        sensor_types : list, optional
            An optional list of sensor types to limit our request to.
        callback : function, optional
            The callback function that will receive the requested events.
        completed_callback : function, optional
            A function that will be called once the full dataset has been requested.
        callback_full_params : bool, optional
            Boolean defining if the callback function will be expecting the full callback
            parameters (channel, method, properties, body) or just body.  The default value
            is False.
        manual_ack : bool, optional
            Boolean that determines if the calling program will manually be sending the message
            ack.  This variable is overridden to False if callback_full_params is False (as you
            need those to send the ack).  The default value is False.

        Raises
        ------
        objects.CasasDatetimeException
            If `start_stamp` or `end_stamp` is a naive datetime.datetime object, where the tzinfo
            is not set.
        objects.CasasRabbitMQException
            If the connection is currently in the consuming state and not able to be utilized for
            RPC type calls right now.
        """
        self._request_data(site=site,
                           start_stamp=start_stamp,
                           end_stamp=end_stamp,
                           experiment=experiment,
                           dataset=dataset,
                           key=key,
                           secret=secret,
                           sensor_types=sensor_types,
                           callback=callback,
                           completed_callback=completed_callback,
                           callback_full_params=callback_full_params,
                           manual_ack=manual_ack)
        return

    def request_events_historic(self, site, start_stamp, end_stamp, key, secret, sensor_types=None,
                                callback=None, completed_callback=None, callback_full_params=False,
                                manual_ack=False):
        """Request historic events in a given time range be sent to a provided function callback,
        event-by-event.

        Parameters
        ----------
        site : str
            The testbed that this request is for.
        start_stamp : datetime.datetime
            The UTC timestamp for the start of the requested window of data.
        end_stamp : datetime.datetime
            The UTC timestamp for the end of the request window of data.
        key : str
            The key value that is paired with secret for accessing data.
        secret : str
            The secret value that is paired with key for accessing data.
        sensor_types : list, optional
            An optional list of sensor types to limit our request to.
        callback : function, optional
            The callback function that will receive the requested events.
        completed_callback : function, optional
            A function that will be called once the full dataset has been requested.
        callback_full_params : bool, optional
            Boolean defining if the callback function will be expecting the full callback
            parameters (channel, method, properties, body) or just body.  The default value
            is False.
        manual_ack : bool, optional
            Boolean that determines if the calling program will manually be sending the message
            ack.  This variable is overridden to False if callback_full_params is False (as you
            need those to send the ack).  The default value is False.

        Raises
        ------
        objects.CasasDatetimeException
            If `start_stamp` or `end_stamp` is a naive datetime.datetime object, where the tzinfo
            is not set.
        objects.CasasRabbitMQException
            If the connection is currently in the consuming state and not able to be utilized for
            RPC type calls right now.
        """
        self._request_data(site=site,
                           start_stamp=start_stamp,
                           end_stamp=end_stamp,
                           experiment=None,
                           dataset=None,
                           key=key,
                           secret=secret,
                           sensor_types=sensor_types,
                           callback=callback,
                           completed_callback=completed_callback,
                           callback_full_params=callback_full_params,
                           manual_ack=manual_ack)
        return

    def _request_data(self, site, start_stamp, end_stamp, experiment, dataset, key, secret,
                      sensor_types=None, callback=None, completed_callback=None,
                      callback_full_params=False, manual_ack=False):
        """Request data be sent to a provided function, event-by-event.  This function does not
        return until the full dataset has been received and processed by the callbacks.

        Parameters
        ----------
        site : str
            The testbed that this request is for.
        start_stamp : datetime.datetime
            The UTC timestamp for the start of the requested window of data.
        end_stamp : datetime.datetime
            The UTC timestamp for the end of the request window of data.
        experiment : str
            The name of the experiment we wish to get data from.
        dataset : str
            The name of the dataset we wish to get data from.
        key : str
            The key value that is paired with secret for accessing data.
        secret : str
            The secret value that is paired with key for accessing data.
        sensor_types : list, optional
            An optional list of sensor types to limit our request to.
        callback : function, optional
            The callback function that will receive the requested events.
        completed_callback : function, optional
            A function that will be called once the full dataset has been requested.
        callback_full_params : bool, optional
            Boolean defining if the callback function will be expecting the full callback
            parameters (channel, method, properties, body) or just body.  The default value
            is False.
        manual_ack : bool, optional
            Boolean that determines if the calling program will manually be sending the message
            ack.  This variable is overridden to False if callback_full_params is False (as you
            need those to send the ack).  The default value is False.

        Raises
        ------
        objects.CasasDatetimeException
            If `start_stamp` or `end_stamp` is a naive datetime.datetime object, where the tzinfo
            is not set.
        objects.CasasRabbitMQException
            If the connection is currently in the consuming state and not able to be utilized for
            RPC type calls right now.
        """
        self.log.info('_request_data( {}, {}, {}, {}, {}, {}, {}, {})'.format(site,
                                                                              str(start_stamp),
                                                                              str(end_stamp),
                                                                              experiment,
                                                                              dataset,
                                                                              key,
                                                                              secret,
                                                                              str(sensor_types)))
        # Check to see if Connection is consuming, if so, then raise objects.CasasRabbitMQException.
        if self._is_consuming:
            raise objects.CasasRabbitMQException('The connection is currently in the consuming '
                                                 'state and can not be used for RPC methods '
                                                 'right now!')
        corr_id = str(uuid.uuid4())
        callback_queue = 'rpc.request.events.{}'.format(str(uuid.uuid4().hex))
        queue_name = objects.QUEUE_SYSTEM_REQUESTS

        td_max = datetime.timedelta(hours=24)
        casas_object = None
        if abs(end_stamp - start_stamp) > td_max:
            if experiment is not None and dataset is not None:
                casas_object = objects.RequestDataset(site=site,
                                                      start_stamp=start_stamp,
                                                      end_stamp=(start_stamp + td_max),
                                                      experiment=experiment,
                                                      dataset=dataset,
                                                      sensor_types=sensor_types)
            else:
                casas_object = objects.RequestEvents(site=site,
                                                     start_stamp=start_stamp,
                                                     end_stamp=(start_stamp + td_max),
                                                     sensor_types=sensor_types)
        else:
            if experiment is not None and dataset is not None:
                casas_object = objects.RequestDataset(site=site,
                                                      start_stamp=start_stamp,
                                                      end_stamp=end_stamp,
                                                      experiment=experiment,
                                                      dataset=dataset,
                                                      sensor_types=sensor_types)
            else:
                casas_object = objects.RequestEvents(site=site,
                                                     start_stamp=start_stamp,
                                                     end_stamp=end_stamp,
                                                     sensor_types=sensor_types)

        self._on_request_events[corr_id] = dict()
        self._on_request_events[corr_id]['callback'] = callback
        self._on_request_events[corr_id]['callback_full_params'] = callback_full_params
        self._on_request_events[corr_id]['manual_ack'] = manual_ack
        self._on_request_events[corr_id]['completed_callback'] = completed_callback
        self._on_request_events[corr_id]['queue'] = callback_queue
        self._on_request_events[corr_id]['publish_queue'] = queue_name
        self._on_request_events[corr_id]['site'] = copy.deepcopy(site)
        self._on_request_events[corr_id]['start_stamp'] = copy.deepcopy(start_stamp)
        self._on_request_events[corr_id]['end_stamp'] = copy.deepcopy(end_stamp)
        self._on_request_events[corr_id]['experiment'] = copy.deepcopy(experiment)
        self._on_request_events[corr_id]['dataset'] = copy.deepcopy(dataset)
        self._on_request_events[corr_id]['current_stamp'] = copy.deepcopy(start_stamp)
        self._on_request_events[corr_id]['key'] = copy.deepcopy(key)
        self._on_request_events[corr_id]['secret'] = copy.deepcopy(secret)
        self._on_request_events[corr_id]['sensor_types'] = copy.deepcopy(sensor_types)

        self._waiting_on_events = True
        self._request_response[corr_id] = None

        # Subscribe to the callback queue.
        self.setup_subscribe_to_queue(queue_name=callback_queue,
                                      queue_exclusive=True,
                                      queue_auto_delete=True,
                                      casas_events=True,
                                      callback_function=self.process_request_events_callback,
                                      callback_full_params=True,
                                      manual_ack=manual_ack)
        # Declare the queue we are going to publish to.
        self.setup_publish_to_queue(queue_name=queue_name,
                                    queue_durable=True,
                                    queue_exclusive=False,
                                    queue_auto_delete=False)
        # Publish the RequestEvents object and then return.
        self.publish_to_queue(queue_name=queue_name,
                              casas_object=casas_object,
                              correlation_id=corr_id,
                              key=key,
                              secret=secret,
                              reply_to=callback_queue)

        while self._request_response[corr_id] is None:
            self._connection.process_data_events(time_limit=0.05)
        return

    def process_request_events_callback(self, ch, method, props, body, response):
        """This is a callback function for processing the responses to a request for historical
        events, and possibly tags.

        Parameters
        ----------
        ch : pika.channel.Channel
            The channel object.
        method : pika.Spec.Basic.Deliver
            Basic deliver method.
        props : pika.Spec.BasicProperties
            Properties of the message.
        body : str|unicode
            The message body.
        response : list
            A list of processed casas.objects that have been built from the JSON provided in
            the message body.
        """
        self.log.debug("process_request_events_callback({})".format(str(response)))
        corr_id = props.correlation_id
        if corr_id in self._on_request_events:
            # If the request dict included a callback function in the request, then send the list
            # of objects to the callback function.
            is_request_events = False
            for obj in response:
                if obj.action in [objects.REQUEST_EVENTS, objects.REQUEST_DATASET]:
                    is_request_events = True
                    if self._on_request_events[corr_id]['manual_ack']:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
            if self._on_request_events[corr_id]['callback'] is not None and not is_request_events:
                if self._on_request_events[corr_id]['callback_full_params']:
                    self._on_request_events[corr_id]['callback'](ch, method, props, body, response)
                else:
                    self._on_request_events[corr_id]['callback'](response)

            for obj in response:
                if obj.action in [objects.REQUEST_EVENTS, objects.REQUEST_DATASET]:
                    td_max = datetime.timedelta(hours=24)
                    current_stamp = self._on_request_events[corr_id]['current_stamp']
                    end_stamp = self._on_request_events[corr_id]['end_stamp']

                    if (current_stamp + td_max) < end_stamp:
                        # The current_stamp is still more than 1 day from the end_stamp so we will
                        # need to increment it by 1 day and make another request.
                        current_stamp += td_max
                        site = self._on_request_events[corr_id]['site']
                        experiment = self._on_request_events[corr_id]['experiment']
                        dataset = self._on_request_events[corr_id]['dataset']
                        sensor_types = self._on_request_events[corr_id]['sensor_types']
                        key = self._on_request_events[corr_id]['key']
                        secret = self._on_request_events[corr_id]['secret']
                        queue_name = self._on_request_events[corr_id]['publish_queue']
                        callback_queue = self._on_request_events[corr_id]['queue']

                        casas_object = None
                        if abs(end_stamp - current_stamp) > td_max:
                            if experiment is not None and dataset is not None:
                                casas_object = objects.RequestDataset(
                                    site=site,
                                    start_stamp=current_stamp,
                                    end_stamp=(current_stamp + td_max),
                                    experiment=experiment,
                                    dataset=dataset,
                                    sensor_types=sensor_types)
                            else:
                                casas_object = objects.RequestEvents(
                                    site=site,
                                    start_stamp=current_stamp,
                                    end_stamp=(current_stamp + td_max),
                                    sensor_types=sensor_types)
                        else:
                            if experiment is not None and dataset is not None:
                                casas_object = objects.RequestDataset(
                                    site=site,
                                    start_stamp=current_stamp,
                                    end_stamp=end_stamp,
                                    experiment=experiment,
                                    dataset=dataset,
                                    sensor_types=sensor_types)
                            else:
                                casas_object = objects.RequestEvents(
                                    site=site,
                                    start_stamp=current_stamp,
                                    end_stamp=end_stamp,
                                    sensor_types=sensor_types)

                        # Update the current stamp in our dict.
                        self._on_request_events[corr_id]['current_stamp'] = \
                            copy.deepcopy(current_stamp)
                        # Declare the queue we are going to publish to.
                        #self.setup_publish_to_queue(queue_name=queue_name,
                        #                            queue_durable=True,
                        #                            queue_exclusive=False,
                        #                            queue_auto_delete=False)
                        # Publish the next RequestEvents object.
                        self.publish_to_queue(queue_name=queue_name,
                                              casas_object=casas_object,
                                              correlation_id=corr_id,
                                              key=key,
                                              secret=secret,
                                              reply_to=callback_queue)
                    else:
                        # The current_stamp was less than 1 day from the end_stamp, this means that
                        # we have received the final event from this meta RequestEvents. We will
                        # now clean up out queues from this before returning.

                        # If the request dict included a completed_callback function in the
                        # request, then call the completed_callback function.
                        if self._on_request_events[corr_id]['completed_callback'] is not None:
                            self._on_request_events[corr_id]['completed_callback']()

                        # Now, remove our subscription to the callback queue.
                        self.remove_subscribe_to_queue(self._on_request_events[corr_id]['queue'])
                        # Remove out publish to the queue.
                        self.remove_publish_to_queue(
                            self._on_request_events[corr_id]['publish_queue'])
                        # Remove the full entry from our dict().
                        del self._on_request_events[corr_id]
                        self._waiting_on_events = False
                        self._request_response[corr_id] = response
        return

    def setup_subscribe_to_exchange(self, exchange_name, exchange_type='topic', routing_key='#',
                                    exchange_durable=True, exchange_auto_delete=False,
                                    casas_events=True, callback_function=None, queue_name=None,
                                    queue_durable=False, queue_exclusive=True,
                                    queue_auto_delete=True, limit_to_sensor_types=None,
                                    auto_ack=False, callback_full_params=False, manual_ack=False):
        """This function sets up a subscription to events from an exchange.

        Parameters
        ----------
        exchange_name : str
            Name of the RabbitMQ exchange.
        exchange_type : str, optional
            The type of the exchange, usually 'topic'.
        routing_key : str, optional
            The routing key to use when binding to the exchange,
            can be used for filtering by sensor_type.
        exchange_durable : bool, optional
            Boolean defining exchange durability.
        exchange_auto_delete : bool, optional
            Remove exchange when no more queues are bound to it.
        casas_events : bool, optional
            Boolean defining if this exchange will be sending casas events.
        callback_function : function
            The callback function to call when events from this queue binding arrive.
        queue_name : str, optional
            Name of the RabbitMQ queue.
        queue_durable : bool, optional
            Boolean defining queue durability.
        queue_exclusive : bool, optional
            Boolean defining queue exclusivity.
        queue_auto_delete : bool, optional
            Boolean defining if the queue should be automatically deleted on consumer disconnection.
        limit_to_sensor_types : list
            A list that will define what sensor types will be allowed through.
            All sensors are allowed through by default.
        auto_ack : bool, optional
            Boolean that if set to True, automatic acknowledgement mode will be used.
        callback_full_params : bool, optional
            Boolean defining if the callback_function will be expecting the full callback
            parameters (channel, method, properties, body) or just body.
        manual_ack : bool, optional
            Boolean that determines if the calling program will manually be sending the message
            ack.  This variable is overridden to False if auto_ack is True or if
            callback_full_params is False (as you need those to send the ack).  The default value
            is False.
        """
        self.log.info("{}({}, {}, {}, {}, {}, {})".format("setup_subscribe_to_exchange",
                                                          str(exchange_name),
                                                          str(exchange_type),
                                                          str(routing_key),
                                                          str(exchange_durable),
                                                          str(casas_events),
                                                          str(callback_function)))
        if callback_function is None:
            self.log.error("casas.rabbitmq.Connection.setup_subscribe_to_exchange(): "
                           "Error! callback_function needs to be provided for "
                           "handling events from the exchange.")
            return
        new_sub = dict()
        new_sub['exchange_name'] = exchange_name
        new_sub['exchange_type'] = exchange_type
        new_sub['routing_key'] = routing_key
        new_sub['exchange_durable'] = exchange_durable
        new_sub['exchange_auto_delete'] = exchange_auto_delete
        new_sub['casas_events'] = casas_events
        new_sub['callback_function'] = callback_function
        new_sub['callback_full_params'] = callback_full_params
        # Check for a sentinel value, if there assign an empty list.
        if limit_to_sensor_types is not None:
            new_sub['limit_to_sensor_types'] = copy.deepcopy(limit_to_sensor_types)
        else:
            new_sub['limit_to_sensor_types'] = list()
        if queue_name is None:
            new_sub['queue_name'] = "{}.{}.{}".format(self.name,
                                                      exchange_name,
                                                      str(uuid.uuid4().hex))
        else:
            new_sub['queue_name'] = queue_name
        new_sub['queue_durable'] = queue_durable
        new_sub['queue_exclusive'] = queue_exclusive
        new_sub['queue_auto_delete'] = queue_auto_delete
        new_sub['auto_ack'] = auto_ack
        new_sub['consume'] = ConsumeCallback(casas_events=casas_events,
                                             callback_function=callback_function,
                                             is_exchange=True,
                                             exchange_name=exchange_name,
                                             limit_to_sensor_types=limit_to_sensor_types,
                                             auto_ack=auto_ack,
                                             callback_full_params=callback_full_params,
                                             translations=self.translations,
                                             timezone=self.timezone,
                                             manual_ack=manual_ack)
        new_sub['consumer_tag'] = ""
        new_sub['setup_exchange'] = False
        new_sub['setup_queue'] = False
        self._exchanges_subscribe.append(new_sub)
        self._setup_all_exchanges()
        return

    def remove_subscribe_to_exchange(self, exchange_name, routing_key='#'):
        """Removes a subscription to an exchange with the given routing_key.  If the exchange_name
        and/or routing_key are not currently being used, then it simply returns with no errors.

        Parameters
        ----------
        exchange_name : str
            The name of the exchange that we would like to unsubscribe.
        routing_key : str, optional
            The routing key used in the subscription of the exchange.
        """
        self.log.info('remove_subscribe_to_exchange({}, {})'.format(str(exchange_name),
                                                                    str(routing_key)))
        if self._channel:
            for ex in self._exchanges_subscribe:
                if ex['exchange_name'] == exchange_name and ex['routing_key'] == routing_key:
                    if ex['setup_exchange'] and ex['setup_queue']:
                        self._channel.queue_unbind(queue=ex['queue_name'],
                                                   exchange=ex['exchange_name'],
                                                   routing_key=ex['routing_key'])
                        self._channel.basic_cancel(consumer_tag=ex['consumer_tag'])
                        del ex
        return

    def setup_publish_to_exchange(self, exchange_name, exchange_type='topic',
                                  exchange_durable=True, routing_key=None,
                                  exchange_auto_delete=False):
        """Prepare the Connection to publish to the exchange.

        Parameters
        ----------
        exchange_name : str
            The name of the exchange you wish to publish to.
        exchange_type : str, optional
            The type of the exchange you wish to publish to.
        exchange_durable : bool, optional
            Boolean defining exchange durability.
        routing_key : str, optional
            Ignore this parameter for now.
        exchange_auto_delete : bool, optional
            Remove exchange when no more queues are bound to it.
        """
        new_pub = dict()
        new_pub['exchange_name'] = exchange_name
        new_pub['exchange_type'] = exchange_type
        new_pub['exchange_durable'] = exchange_durable
        new_pub['routing_key'] = routing_key
        new_pub['exchange_auto_delete'] = exchange_auto_delete
        new_pub['setup_exchange'] = False
        self._exchanges_publish.append(new_pub)
        self._setup_all_exchanges()
        return

    def remove_publish_to_exchange(self, exchange_name):
        """Removes the entry holder in the config to publish to the provided exchange.  If the
        exchange_name are not currently in the config, then it simply returns with no errors.

        Parameters
        ----------
        exchange_name : str
            The name of the exchange we wish to stop publishing to.
        """
        for ex in self._exchanges_publish:
            if ex['exchange_name'] == exchange_name:
                del ex
                break
        return

    def setup_subscribe_to_queue(self, queue_name, queue_durable=False, queue_exclusive=False,
                                 queue_auto_delete=False, casas_events=True, callback_function=None,
                                 limit_to_sensor_types=None, auto_ack=False,
                                 callback_full_params=False, manual_ack=False):
        """This function sets up a subscription to events from a queue.

        Parameters
        ----------
        queue_name : str
            Name of the RabbitMQ queue.
        queue_durable : bool, optional
            Boolean defining queue durability.
        queue_exclusive : bool, optional
            Boolean defining queue exclusivity.
        queue_auto_delete : bool, optional
            Boolean defining if the queue should be automatically deleted on consumer disconnection.
        casas_events : bool
            Boolean defining if this queue will be sending casas events.
        callback_function : function
            The callback function to call when events from this queue arrive.
        limit_to_sensor_types : list, optional
            A list of sensor types to limit sending to the callback function, an empty list results
            in no filtering of events.
        auto_ack : bool, optional
            Boolean that if set to True, automatic acknowledgement mode will be used.
        callback_full_params : bool, optional
            Boolean defining if the callback_function will be expecting the full callback
            parameters (channel, method, properties, body) or just body.
        manual_ack : bool, optional
            Boolean that determines if the calling program will manually be sending the message
            ack.  This variable is overridden to False if auto_ack is True or if
            callback_full_params is False (as you need those to send the ack).  The default value
            is False.
        """
        if callback_function is None:
            self.log.error("casas.rabbitmq.Connection.setup_subscribe_to_queue(): "
                           "Error! callback_function needs to be provided for handling "
                           "events from the queue.")
            return
        new_sub = dict()
        new_sub['queue_name'] = queue_name
        new_sub['queue_durable'] = queue_durable
        new_sub['queue_exclusive'] = queue_exclusive
        new_sub['queue_auto_delete'] = queue_auto_delete
        new_sub['casas_events'] = casas_events
        new_sub['callback_function'] = callback_function
        new_sub['callback_full_params'] = callback_full_params
        # Check for a sentinel value, if there assign an empty list.
        if limit_to_sensor_types is not None:
            new_sub['limit_to_sensor_types'] = copy.deepcopy(limit_to_sensor_types)
        else:
            new_sub['limit_to_sensor_types'] = list()
        new_sub['auto_ack'] = auto_ack
        new_sub['consume'] = ConsumeCallback(casas_events=casas_events,
                                             callback_function=callback_function,
                                             is_queue=True,
                                             queue_name=queue_name,
                                             limit_to_sensor_types=limit_to_sensor_types,
                                             auto_ack=auto_ack,
                                             callback_full_params=callback_full_params,
                                             translations=self.translations,
                                             timezone=self.timezone,
                                             manual_ack=manual_ack)
        new_sub['consumer_tag'] = ""
        new_sub['setup_queue'] = False
        self._queues_subscribe.append(new_sub)
        self._setup_all_queues()
        return

    def remove_subscribe_to_queue(self, queue_name, limit_to_sensor_types=None):
        """Removes a subscription to a queue.  If the queue_name and limit_to_sensor_types list
        are not currently being used, then it simply returns with no errors.

        Parameters
        ----------
        queue_name : str
            The name of the queue that we would like to unsubscribe from.
        limit_to_sensor_types : list, optional
            The list of sensor types to limit sending to the callback function.
        """
        if limit_to_sensor_types is None:
            limit_to_sensor_types = list()
        self.log.info('remove_subscribe_to_queue({}, {})'.format(str(queue_name),
                                                                 str(limit_to_sensor_types)))
        if self._channel:
            for qu in self._queues_subscribe:
                if qu['queue_name'] == queue_name and \
                        sorted(qu['limit_to_sensor_types']) == sorted(limit_to_sensor_types):
                    if qu['setup_queue']:
                        self._channel.basic_cancel(consumer_tag=qu['consumer_tag'])

            self._queues_subscribe = [x for x in self._queues_subscribe
                                      if not (x['queue_name'] == queue_name and
                                              sorted(x['limit_to_sensor_types']) == sorted(
                                              limit_to_sensor_types))]
        return

    def setup_publish_to_queue(self, queue_name, queue_durable=False,
                               queue_exclusive=False, queue_auto_delete=False,
                               delivery_mode=2):
        """Prepare the Connection to publish to a queue.

        Parameters
        ----------
        queue_name : str
            The name of the queue we wish to publish to.
        queue_durable : bool, optional
            Boolean defining the durability of the queue.
        queue_exclusive : bool, optional
            Boolean defining the exclusivity of the queue.
        queue_auto_delete : bool, optional
            Boolean defining if the queue will automatically be deleted on disconnection.
        delivery_mode : int
            Integer defining the delivery method for RabbitMQ.
        """
        new_pub = dict()
        new_pub['queue_name'] = queue_name
        new_pub['queue_durable'] = queue_durable
        new_pub['queue_exclusive'] = queue_exclusive
        new_pub['queue_auto_delete'] = queue_auto_delete
        new_pub['delivery_mode'] = delivery_mode
        new_pub['setup_queue'] = False
        self._queues_publish.append(new_pub)
        self._setup_all_queues()
        return

    def remove_publish_to_queue(self, queue_name):
        """Removes the entry holder in the config to publish to the provided queue.  If the
        queue_name is not currently in the config, then it simply returns with no errors.

        Parameters
        ----------
        queue_name : str
            The name of the queue we wish to stop publishing to.
        """
        self.log.info('remove_publish_to_queue({})'.format(str(queue_name)))
        for qu in self._queues_publish:
            if qu['queue_name'] == queue_name:
                del qu
                break
        self._queues_publish = [qu for qu in self._queues_publish
                                if not qu['queue_name'] == queue_name]
        return

    def _connect(self, prefetch_count=1):
        """This method connects to RabbitMQ.

        Parameters
        ----------
        prefetch_count : int
            Specifies a prefetch window in terms of whole messages. This field may be used in
            combination with the prefetch-size field; a message will only be sent in advance if
            both prefetch windows (and those at the channel and connection level) allow it. The
            prefetch-count is ignored if the no-ack option is set in the consumer.
        """
        self.log.info('Connecting to %s', self._url)
        self._connection = pika.BlockingConnection(parameters=pika.URLParameters(self._url))
        self._channel = self._connection.channel()
        self._channel.basic_qos(prefetch_count=prefetch_count)

        self._add_on_connection_blocked_callback()
        self._add_on_connection_unblocked_callback()
        self._setup_all_exchanges()
        self._setup_all_queues()
        if self._on_connect_callback is not None and \
                not self._is_consuming and \
                not self._waiting_on_request:
            self._on_connect_callback()
        return

    def _reset_all_exchanges_queues(self):
        """Reset the state of configured exchanges and queues so they are declared and set up
        after the Connection reconnects to the server.
        """
        self.log.debug('self._reset_all_exchanges_queues()')
        for ex in self._exchanges_subscribe:
            ex['setup_exchange'] = False
            ex['setup_queue'] = False
        for ex in self._exchanges_publish:
            ex['setup_exchange'] = False
        for qu in self._queues_subscribe:
            qu['setup_queue'] = False
        for qu in self._queues_publish:
            qu['setup_queue'] = False
        return

    def _add_on_connection_blocked_callback(self):
        """Set the on_connection_blocked callback if a function has been set.
        """
        if self._on_connection_blocked_callback is not None:
            self._connection.add_on_connection_blocked_callback(self._on_connection_blocked)
        return

    def _on_connection_blocked(self, method):
        """Callback for when RabbitMQ has sent a 'Connection.Blocked' frame indicating that
        RabbitMQ is low on resources. Publishers can use this to voluntarily suspend publishing,
        instead of relying on back pressure throttling.

        Parameters
        ----------
        method : pika.frame.Method
            The 'Connection.Blocked' method frame.
        """
        if self._on_connection_blocked_callback is not None:
            self._on_connection_blocked_callback()
        return

    def _add_on_connection_unblocked_callback(self):
        """Set the on_connection_unblocked callback if a function has been set.
        """
        if self._on_connection_unblocked_callback is not None:
            self._connection.add_on_connection_unblocked_callback(self._on_connection_unblocked)
        return

    def _on_connection_unblocked(self, method):
        """Callback for when RabbitMQ has sent a 'Connection.Unblocked' frame letting publishers
        know that it's ok to start publishing again.

        Parameters
        ----------
        method : pika.frame.Method
            The 'Connection.Unblocked' method frame.
        """
        if self._on_connection_unblocked_callback is not None:
            self._on_connection_unblocked_callback()
        return

    def _setup_all_exchanges(self):
        """Setup the exchanges on RabbitMQ by invoking self.setup_exchange(...)
        for each exchange we have defined.
        """
        if self._channel:
            self.log.info('Setting up defined exchanges')
            for ex in self._exchanges_subscribe:
                self.log.info("checking: {}".format(str(ex['exchange_name'])))
                self.log.debug('  setup_exchange = {}'.format(ex['setup_exchange']))
                if 'consume' in ex:
                    self.log.debug('  setup_queue = {}'.format(ex['setup_queue']))
            for ex in self._exchanges_publish:
                self.log.info("checking: {}".format(str(ex['exchange_name'])))
                self.log.debug('  setup_exchange = {}'.format(ex['setup_exchange']))
            for ex in self._exchanges_subscribe:
                self.log.info("setting up: {}".format(str(ex['exchange_name'])))
                self._setup_exchange(ex)
            for ex in self._exchanges_publish:
                self.log.info("setting up: {}".format(str(ex['exchange_name'])))
                self._setup_exchange(ex)
            self._add_on_cancel_callback()
            for ex in self._exchanges_subscribe:
                self.log.info("checking: {}".format(str(ex['exchange_name'])))
                self.log.debug('  setup_exchange = {}'.format(ex['setup_exchange']))
                if 'consume' in ex:
                    self.log.debug('  setup_queue = {}'.format(ex['setup_queue']))
            for ex in self._exchanges_publish:
                self.log.info("checking: {}".format(str(ex['exchange_name'])))
                self.log.debug('  setup_exchange = {}'.format(ex['setup_exchange']))
        return

    def _setup_exchange(self, ex):
        """Setup the exchange on RabbitMQ with the appropriate binding to the queue, and assign
        the consumer callback for the queue.

        Parameters
        ----------
        ex : dict
            The dict of the exchange to start setting up.
        """
        try:
            if not ex['setup_exchange']:
                self.log.info('Declaring exchange %s', ex['exchange_name'])
                self._channel.exchange_declare(exchange=ex['exchange_name'],
                                               exchange_type=ex['exchange_type'],
                                               durable=ex['exchange_durable'],
                                               auto_delete=ex['exchange_auto_delete'])
                ex['setup_exchange'] = True
                if 'consume' in ex:
                    self.log.info('Declaring queue %s', ex['queue_name'])
                    self._channel.queue_declare(queue=ex['queue_name'],
                                                durable=ex['queue_durable'],
                                                exclusive=ex['queue_exclusive'],
                                                auto_delete=ex['queue_auto_delete'])
                    self._channel.queue_bind(exchange=ex['exchange_name'],
                                             queue=ex['queue_name'],
                                             routing_key=ex['routing_key'])
                    ex['setup_queue'] = True
                    # self._channel.basic_qos(prefetch_count=0)
                    ex['consumer_tag'] = self._channel.basic_consume(
                        queue=ex['queue_name'],
                        on_message_callback=ex['consume'].on_message,
                        auto_ack=ex['auto_ack'])
        except pika.exceptions.AMQPChannelError:
            self.log.error("{} {} {}".format("casas.rabbitmq.Connection.setup_exchange():",
                                             "pika.exceptions.AMQPChannelError,",
                                             ex['exchange_name']))
            self.log.error("  name={} type={} durable={}".format(str(ex['exchange_name']),
                                                                 str(ex['exchange_type']),
                                                                 str(ex['exchange_durable'])))
        return

    def _setup_all_queues(self):
        """Setup the queues on RabbitMQ by invoking self.setup_queue(...) for
        each queue we have defined.
        """
        if self._channel:
            self.log.info('Setting up defined queues')
            for qu in self._queues_subscribe:
                self.log.info("checking: {}".format(str(qu['queue_name'])))
                self.log.debug('  setup_queue = {}'.format(qu['setup_queue']))
            for qu in self._queues_publish:
                self.log.info("checking: {}".format(str(qu['queue_name'])))
                self.log.debug('  setup_queue = {}'.format(qu['setup_queue']))
            for qu in self._queues_subscribe:
                self.log.info("setting up: {}".format(str(qu['queue_name'])))
                self._setup_queue(qu)
            for qu in self._queues_publish:
                self.log.info("setting up: {}".format(str(qu['queue_name'])))
                self._setup_queue(qu)
            self._add_on_cancel_callback()
            for qu in self._queues_subscribe:
                self.log.info("checking: {}".format(str(qu['queue_name'])))
                self.log.debug('  setup_queue = {}'.format(qu['setup_queue']))
            for qu in self._queues_publish:
                self.log.info("checking: {}".format(str(qu['queue_name'])))
                self.log.debug('  setup_queue = {}'.format(qu['setup_queue']))
        return

    def _setup_queue(self, qu):
        """Setup the queue on RabbitMQ and assign the consumer callback for the queue.

        Parameters
        ----------
        qu : dict
            The dict of the queue to start setting up.
        """
        try:
            if not qu['setup_queue'] and self._connection.is_open:
                self.log.info('Declaring queue %s', qu['queue_name'])
                self._channel.queue_declare(queue=qu['queue_name'],
                                            durable=qu['queue_durable'],
                                            exclusive=qu['queue_exclusive'],
                                            auto_delete=qu['queue_auto_delete'])
                qu['setup_queue'] = True
                if 'consume' in qu:
                    # self._channel.basic_qos(prefetch_count=0)
                    qu['consumer_tag'] = self._channel.basic_consume(
                        queue=qu['queue_name'],
                        on_message_callback=qu['consume'].on_message,
                        auto_ack=qu['auto_ack'])
        except pika.exceptions.AMQPChannelError:
            self.log.error("{} {}".format("setup_queue(): pika.exceptions.AMQPChannelError,"
                                          , qu['queue_name']))
            self.log.error("  name={} exclusive={} durable={}".format(str(qu['queue_name']),
                                                                      str(qu['queue_exclusive']),
                                                                      str(qu['queue_durable'])))
        return

    def publish_to_exchange(self, exchange_name, casas_object=None,
                            body_str=None, routing_key=None,
                            correlation_id=None, delivery_mode=2, key=None, secret=None,
                            reply_to=None):
        """Publish a message to the exchange.

        Parameters
        ----------
        exchange_name : str
            Name of the exchange we are publishing to.
        casas_object : objects.CasasObject
            CASAS object to uploaded, this function handles the standard behaviors for us.
        body_str : str, optional
            Use if you are publishing a non-CASAS object.  This value will be overwritten if you
            provide a value for casas_object.
        routing_key : str, optional
            Use if you are using body_str to publish, this will be overwritten if using
            casas_object to upload.
        correlation_id : str, optional
            This is an optional correlation ID to use when performing RPC style calls.
        delivery_mode : int, optional
            Integer defining the delivery method for RabbitMQ.
        key : str, optional
            The key value that is paired with secret for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        secret : str, optional
            The secret value that is paired with key for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        reply_to : str, optional
            This is the name of the exclusive queue that the RPC style call on the other end
            should publish the response to.

        Returns
        -------

        """
        # TODO: Redefine routing key structure in objects.py.
        if routing_key is None:
            if casas_object is None:
                routing_key = "unknown.unknown.casas"
            else:
                routing_key = objects.get_routing_key(casas_object)
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        if self._channel:
            if casas_object is not None:
                body_str = casas_object.get_json(secret=secret, key=key)
                body_str = "[{}]".format(body_str)
            debug_msg = "publish_to_exchange(exchange={}, ".format(str(exchange_name))
            debug_msg += "casas_obj={}, body={}, routing_key={}, ".format(str(casas_object),
                                                                          str(body_str),
                                                                          str(routing_key))
            debug_msg += "corr_id={}, key={}, secret={})".format(str(correlation_id),
                                                                 str(key),
                                                                 str(secret))
            self.log.debug(debug_msg)
            self._channel.basic_publish(exchange=exchange_name,
                                        routing_key=routing_key,
                                        properties=pika.BasicProperties(
                                            correlation_id=correlation_id,
                                            delivery_mode=delivery_mode,
                                            reply_to=reply_to),
                                        body=str(body_str))
        return

    def publish_to_queue(self, queue_name, casas_object=None, body_str=None,
                         correlation_id=None, delivery_mode=2, key=None,
                         secret=None, reply_to=None):
        """Publish a message to the queue.

        Parameters
        ----------
        queue_name : str
            Name of the queue we are publishing to.
        casas_object : objects.CasasObject
            CASAS object to be uploaded, this function handles the standard behaviors for us.
        body_str : str, optional
            Use if you are publishing a non-CASAS object.  This value will be overwritten if you
            provide a value for casas_object.
        correlation_id : str, optional
            This is an optional correlation ID to use when performing RPC style calls.
        delivery_mode : int, optional
            Integer defining the delivery method for RabbitMQ.
        key : str, optional
            The key value that is paired with secret for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        secret : str, optional
            The secret value that is paired with key for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        reply_to : str, optional
            This is the name of the exclusive queue that the RPC style call on the other end
            should publish the response to.
        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        if self._channel:
            if casas_object is not None:
                body_str = casas_object.get_json(secret=secret, key=key)
                body_str = "[{}]".format(body_str)
            debug_msg = "publish_to_queue(queue={}, ".format(str(queue_name))
            debug_msg += "casas_obj={}, body={}, corr_id={}, ".format(str(casas_object),
                                                                      str(body_str),
                                                                      str(correlation_id))
            debug_msg += "del_mode={}, key={}, secret={})".format(str(delivery_mode),
                                                                  str(key),
                                                                  str(secret))
            self.log.debug(debug_msg)
            self._channel.basic_publish(exchange='',
                                        routing_key=queue_name,
                                        properties=pika.BasicProperties(
                                            correlation_id=correlation_id,
                                            delivery_mode=delivery_mode,
                                            reply_to=reply_to),
                                        body=str(body_str))
        return

    def _add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.
        """
        if not self._has_on_cancel_callback:
            self.log.info('Adding consumer cancellation callback')
            self._channel.add_on_cancel_callback(self._on_consumer_cancelled)
            self._has_on_cancel_callback = True
        return

    def _on_consumer_cancelled(self, method_frame=None):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        Parameters
        ----------
        method_frame : pika.frame.Method
            The Basic.Cancel frame.
        """
        self.log.info('Consumer was cancelled remotely, shutting down: %s', str(method_frame))
        if self._channel:
            if not self._channel.is_closing:
                self._channel.close()
            self._connection.close()
        return

    def _stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.
        """
        if self._channel:
            self.log.info('Sending a Basic.Cancel RPC commands to RabbitMQ')
            for ex in self._exchanges_subscribe:
                if not ex['setup_exchange'] and not ex['setup_queue']:
                    continue
                if self._channel.is_open:
                    self._channel.basic_cancel(consumer_tag=ex['consumer_tag'])

            for qu in self._queues_subscribe:
                if not qu['setup_queue']:
                    continue
                if self._channel.is_open:
                    self._channel.basic_cancel(consumer_tag=qu['consumer_tag'])
        return

    def basic_get(self, queue):
        """

        Parameters
        ----------
        queue : str
            Name of the queue from which to get a message.

        Returns
        -------
        (pika.spec.Basic.GetOk|None, pika.spec.BasicProperties|None, str|None)
        """
        method = None
        header = None
        body = None
        if self._channel:
            method, header, body = self._channel.basic_get(queue)
        return method, header, body

    def basic_ack(self, delivery_tag):
        """Acknowledge one message.

        Parameters
        ----------
        delivery_tag : int
            The server-assigned delivery tag.
        """
        if self._channel:
            self._channel.basic_ack(delivery_tag)
        return

    def start_consuming(self):
        """Tells the connection to start consuming available messages.

        Raises
        ------
        objects.CasasRabbitMQException
            If the connection is currently waiting on a direct RPC request or RPC event/dataset
            callback processing we can not enable the connection to consume right now.
        """
        if self._waiting_on_events or self._waiting_on_request:
            raise objects.CasasRabbitMQException(value="This Connection object is currently "
                                                       "waiting on RPC responses and can not enter "
                                                       "a consuming state.")

        if self._connection.is_open:
            self._is_consuming = True
            while self._is_consuming:
                try:
                    if self._connection.is_open:
                        self.log.info('self._channel.start_consuming()')
                        self._channel.start_consuming()
                    else:
                        # TODO: Determine if we need to disable the on_connect_callback for this.
                        self.log.debug('start_consuming() self.stop()')
                        self.stop()
                        self.log.debug('start_consuming() self._reset_all_exchanges_queues()')
                        self._reset_all_exchanges_queues()
                        self._is_consuming = True
                        self.log.debug('start_consuming() self.run()')
                        self.run()
                except pika.exceptions.AMQPChannelError as err:
                    self.log.error('Caught a channel error: {}'.format(err))
                    time.sleep(2)
                    continue
                except pika.exceptions.AMQPConnectionError:
                    self.log.error('Connection was closed, reconnecting...')
                    time.sleep(2)
                    continue
                except pika.exceptions.AMQPError as err:
                    self.log.error('AMQPError: {}'.format(err))
                    time.sleep(1)
                    continue
                except socket.timeout as err:
                    self.log.error('socket.timeout, connection failed, '
                                   'trying again... {}'.format(err))
                    time.sleep(1)
                    continue
                except socket.gaierror as err:
                    self.log.error('socket.gaierror, connection failure, '
                                   'trying again... {}'.format(err))
                    time.sleep(1)
                    continue
        return

    def stop_consuming(self):
        """Tell the connection to stop consuming available messages right now.
        """
        self.log.debug('stop_consuming()')
        if self._is_consuming:
            self._is_consuming = False
            if self._channel.is_open:
                self.log.debug('stop_consuming() self._channel.stop_consuming()')
                self._channel.stop_consuming()
        return

    def process_data_events(self, time_limit=0):
        """Will make sure that data events are processed.  Dispatches timer and channel callbacks
        if not called from the scope of BlockingConnection or BlockingChannel callback.

        Parameters
        ----------
        time_limit : float
            Suggested upper bound on processing time in seconds.  The actual blocking time depends
            on the granularity of the underlying ioloop.  Zero means return as soon as possible.
            None means there is no limit on processing time and the function will block until I/O
            produces actionable events.

        Returns
        -------

        """
        self._connection.process_data_events(time_limit=time_limit)
        return

    def sleep(self, duration):
        self._connection.sleep(duration=duration)
        return

    def run(self, prefetch_count=1, timeout=None):
        """Run the Connection object by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.
        """
        self.log.debug('run(prefetch_count={})'.format(prefetch_count))
        startup_success = False
        start_time = float(time.time())
        while not startup_success:
            if timeout is not None:
                if abs(float(time.time()) - start_time) > timeout:
                    break
            try:
                self._connect(prefetch_count=prefetch_count)
                startup_success = True
            except pika.exceptions.ConnectionOpenAborted as err:
                self.log.error('run() ConnectionOpenAborted error: {}'.format(err))
                time.sleep(2)
                continue
            except pika.exceptions.AMQPChannelError as err:
                self.log.error('run() Caught a channel error: {}'.format(err))
                time.sleep(2)
                continue
            except pika.exceptions.AMQPConnectionError:
                self.log.error('run() Connection was closed, reconnecting...')
                time.sleep(1)
                continue
            except pika.exceptions.AMQPError as err:
                self.log.error('run() AMQPError: {}'.format(err))
                time.sleep(1)
                continue
            except socket.timeout as err:
                self.log.error('socket.timeout, connection failed, trying again... {}'.format(err))
                time.sleep(1)
                continue
            except socket.gaierror as err:
                self.log.error('socket.gaierror, conn. failure, trying again... {}'.format(err))
                time.sleep(1)
                continue
        return

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the Connection object
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.
        """
        self.log.debug('stop()')
        if not self._closing:
            self.log.info('Stopping')
            if self._on_disconnect_callback is not None:
                self._on_disconnect_callback()
            self._closing = True
            if self._is_consuming:
                self.stop_consuming()
            self._stop_consuming()
            try:
                if self._channel:
                    self.log.debug('stop() self._channel.close()')
                    self._channel.close()
                if self._connection:
                    if self._connection.is_open:
                        self.log.debug('stop() self._connection.close()')
                        self._connection.close()
            except pika.exceptions.AMQPError as err:
                self.log.error('stop() AMQPError: {}'.format(err))
            self._reset_all_exchanges_queues()
            self.log.info('Stopped')
        return

    def call_later(self, seconds, function):
        """Adds a callback to the IO loop.

        Parameters
        ----------
        seconds : int
            Number of seconds to wait before calling function.
        function : function
            The callback function to call when seconds have passed.

        Returns
        -------
        str
            The timeout ID handle.
        """
        return self._connection.call_later(seconds, function)

    def cancel_call_later(self, timeout_id):
        """Cancel the call_later for the provided timeout_id.

        Parameters
        ----------
        timeout_id : str
            The timeout ID handle.
        """
        self._connection.remove_timeout(timeout_id)
        return

    def call_later_threadsafe(self, function):
        """Requests a call to the given function as soon as possible in the context of this
        connection's thread.

        Parameters
        ----------
        function : callable
            The callback method/function.
        """
        self._connection.add_callback_threadsafe(function)
        return

    @property
    def is_open(self):
        """Returns a boolean reporting the current connection state.

        Returns
        -------
        bool
            The current connection state.
        """
        return self._connection.is_open

    @property
    def is_closed(self):
        """Returns a boolean reporting the current connection state.

        Returns
        -------
        bool
            The current connection state.
        """
        return self._connection.is_closed

    @property
    def is_closing(self):
        """Returns a boolean reporting the current connection state.

        Returns
        -------
        bool
            The current connection state.
        """
        return self._connection.is_closing
