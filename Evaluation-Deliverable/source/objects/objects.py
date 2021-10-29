# *****************************************************************************#
# **
# **  CASAS RabbitMQ JSON Object Python Library
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
import dateutil
import json
import logging
import logging.handlers
import pytz
import re
import time
import types
import uuid

__major_version__ = '0.7'
__minor_version__ = '6'
__db_version__ = '0.5'
__version__ = '{}.{}'.format(__major_version__, __minor_version__)
__database_version__ = re.sub('[.]', '_', __db_version__)

log = logging.getLogger(__name__)

# Database naming pattern.
DATABASE_PATTERN = '{}_v{}'.format('{}', __database_version__)

# AIQ Global Timeout
GLOBAL_TIMEOUT_SECONDS = 60 * 20  # 20 minutes

# AIQ Object Strings
REQ_MODEL = 'request_model'
REQ_STATE = 'request_state'
MODEL = 'model'
REQ_EXPERIMENT = 'request_experiment'
REQ_EXP_TRIALS = 'request_experiment_trials'
EXPERIMENT_RESP = 'experiment_response'
EXPERIMENT_START = 'experiment_start'
EXPERIMENT_END = 'experiment_end'
EXPERIMENT_EXCEPTION = 'experiment_exception'
BENCHMARK_REQ = 'benchmark_request'
BENCHMARK_DATA = 'benchmark_data'
BENCHMARK_ACK = 'benchmark_ack'
NOVELTY_START = 'novelty_level_start'
NOVELTY_END = 'novelty_level_end'
TRIAL_START = 'trial_start'
TRIAL_END = 'trial_end'
TRAINING_START = 'training_start'
TRAINING_ACTIVE = 'training_active'
TRAINING_END = 'training_end'
TRAINING_MODEL_END = 'training_model_end'
TRAINING_END_EARLY = 'training_end_early'
TRAIN_EPISODE_START = 'training_episode_start'
TRAIN_EPISODE_ACTIVE = 'training_episode_active'
TRAIN_EPISODE_END = 'training_episode_end'
TRAIN_EPISODE_NOVELTY = 'training_episode_novelty'
TRAIN_EPISODE_NOVELTY_ACK = 'training_episode_novelty_ack'
EPISODE_END = 'episode_end'
REQ_DATA = 'request_data'
BASIC_DATA = 'basic_data'
BASIC_DATA_PREDICTION = 'basic_data_prediction'
BASIC_DATA_ACK = 'basic_data_ack'
BASIC_EPISODE_NOVELTY = 'basic_episode_novelty'
REQ_TRAIN_DATA = 'request_training_data'
TRAINING_DATA = 'training_data'
TRAIN_DATA_PRED = 'training_data_prediction'
TRAIN_DATA_ACK = 'training_data_ack'
TESTING_START = 'testing_start'
TESTING_ACTIVE = 'testing_active'
TESTING_END = 'testing_end'
TEST_EPISODE_START = 'testing_episode_start'
TEST_EPISODE_ACTIVE = 'testing_episode_active'
TEST_EPISODE_END = 'testing_episode_end'
TEST_EPISODE_NOVELTY = 'testing_episode_novelty'
TEST_EPISODE_NOVELTY_ACK = 'testing_episode_novelty_ack'
REQ_TEST_DATA = 'request_testing_data'
TESTING_DATA = 'testing_data'
TEST_DATA_PRED = 'testing_data_prediction'
TEST_DATA_ACK = 'testing_data_ack'
END_EXPERIMENT = 'end_experiment'
WAIT_ON_SOTA = 'waiting_on_sota'
SOTA_IDLE = 'sota_idle'
OBJ_EPISODE = 'object_episode'
OBJ_TRAINING = 'object_training'
OBJ_NOVELTY_GRP = 'object_novelty_group'
OBJ_TRIAL = 'object_trial'
OBJ_EXPERIMENT = 'object_experiment'
REQ_NOVELTY_DESCRIPTION = 'request_novelty_description'
OBJ_NOVELTY_DESCRIPTION = 'object_novelty_description'
GENERATOR_IDLE = 'generator_idle'
GENERATOR_RESET = 'generator_reset'
START_GENERATOR = 'start_generator'
GENERATOR_RESPONSE = 'generator_response'
ANALYSIS_READY = 'analysis_ready'
ANALYSIS_PARTIAL = 'analysis_partial'
SEED_NUM_TRAINING = 42949672
SEED_NUM_TESTING = 4294967295

# AIQ Types
TYPE_EXPERIMENT_AIQ = 'AIQ'
TYPE_EXPERIMENT_SAIL_ON = 'SAIL-ON'
VALID_EXPERIMENT_TYPES = list([TYPE_EXPERIMENT_AIQ,
                               TYPE_EXPERIMENT_SAIL_ON])
DOMAIN_CARTPOLE = 'cartpole'
DOMAIN_VIZDOOM = 'vizdoom'
DOMAIN_SMARTENV = 'smartenv'
VALID_DOMAINS = list([DOMAIN_CARTPOLE,
                      DOMAIN_VIZDOOM,
                      DOMAIN_SMARTENV])
NOVELTY_1 = 1
NOVELTY_2 = 2
NOVELTY_3 = 3
NOVELTY_101 = 101
NOVELTY_102 = 102
NOVELTY_103 = 103
NOVELTY_104 = 104
NOVELTY_105 = 105
NOVELTY_200 = 200
NOVELTY_201 = 201
NOVELTY_202 = 202
NOVELTY_203 = 203
NOVELTY_204 = 204
NOVELTY_205 = 205
VALID_NOVELTY = list([NOVELTY_200,
                      NOVELTY_1,
                      NOVELTY_2,
                      NOVELTY_3,
                      NOVELTY_101,
                      NOVELTY_102,
                      NOVELTY_103,
                      NOVELTY_104,
                      NOVELTY_105,
                      NOVELTY_201,
                      NOVELTY_202,
                      NOVELTY_203,
                      NOVELTY_204,
                      NOVELTY_205])
TESTING_NOVELTY = list([NOVELTY_200,
                        NOVELTY_1,
                        NOVELTY_2,
                        NOVELTY_3,
                        NOVELTY_101,
                        NOVELTY_102,
                        NOVELTY_103,
                        NOVELTY_104,
                        NOVELTY_105,
                        NOVELTY_201,
                        NOVELTY_202,
                        NOVELTY_203,
                        NOVELTY_204,
                        NOVELTY_205])
DIFFICULTY_EASY = 'easy'
DIFFICULTY_MEDIUM = 'medium'
DIFFICULTY_HARD = 'hard'
VALID_DIFFICULTY = list([DIFFICULTY_EASY,
                         DIFFICULTY_MEDIUM,
                         DIFFICULTY_HARD])
SOURCE_RECORDED = 'recorded'
SOURCE_LIVE = 'live'
DTYPE_TRAIN = 'train'
DTYPE_TEST = 'test'
DTYPE_LIVE_TRAIN = 'live_train'
DTYPE_LIVE_TEST = 'live_test'
VALID_DATA_TYPE = list([DTYPE_TRAIN,
                        DTYPE_TEST,
                        DTYPE_LIVE_TRAIN,
                        DTYPE_LIVE_TEST])

# AIQ Queues
SERVER_MODEL_QUEUE = 'model.request.v{}'.format(__major_version__)
SERVER_EXPERIMENT_QUEUE = 'experiment.request.v{}'.format(__major_version__)
REGISTER_SOTA_QUEUE = 'register.sota.v{}'.format(__major_version__)
ANALYSIS_READY_QUEUE = 'analysis.ready.v{}'.format(__major_version__)
CLIENT_RPC_QUEUE = 'rpc.client.v{}'.format(__major_version__)
SERVER_RPC_QUEUE = 'rpc.server.v{}'.format(__major_version__)
GENERATOR_RPC_QUEUE = 'rpc.generator.v{}'.format(__major_version__)
NOVELTY_DESC_RPC_QUEUE = 'rpc.novelty_description.v{}'.format(__major_version__)
LIVE_GENERATOR_QUEUES = dict()
for domain in VALID_DOMAINS:
    LIVE_GENERATOR_QUEUES[domain] = 'live.generator.{}.v{}'.format(domain, __major_version__)

# TA1 default command line arg values.
DEFAULT_TA1_DEBUG = False
DEFAULT_TA1_FULLDEBUG = False
DEFAULT_TA1_PRINTOUT = False
DEFAULT_TA1_TESTING = False
DEFAULT_TA1_DEMO = False
DEFAULT_TA1_SHORTDEMO = False
DEFAULT_TA1_LOGFILE = None
DEFAULT_TA1_SAVE_EXPERIMENT_JSON = False
DEFAULT_TA1_LOAD_EXPERIMENT_JSON = False
DEFAULT_TA1_JSON_EXPERIMENT_FILE = 'config/experiment_file.json'

# CASAS object strings
CASAS_ERROR = 'casas_error'
CASAS_RESPONSE = 'casas_response'
CASAS_OBJ_LIST = 'casas_object_list'
CASAS_GET_OBJ = 'casas_get_object'
CASAS_SET_OBJ = 'casas_set_object'
TESTBED = 'testbed'
EVENT = 'event'
TAG = 'tag'
CONTROL = 'control'
HEARTBEAT = 'heartbeat'
TRANSLATION = 'translation'
TRANSLATION_GRP = 'translation_group'
ALGORITHM = 'algorithm'
ALG_MODEL = 'algorithm_model'
ALG_PROCESSOR = 'algorithm_processor'
ALG_PROC_REQUEST = 'algorithm_processor_request'
ALG_PROC_UPDATE = 'algorithm_processor_update'
CIL_BASE = 'cil_baseline'
CIL_METRIC = 'cil_metric'
CIL_BASE_METRIC = 'cil_baseline_metric'
CIL_DATA = 'cil_data'
REQUEST_EVENTS = 'request_events'
REQUEST_DATASET = 'request_dataset'


# CASAS error type strings
ERROR_DATA = 'data'
ERROR_JSON = 'json'
ERROR_ERROR = 'error'
ERROR_NETWORK = 'network'
ERROR_REQUEST = 'request'

# CASAS Queues
QUEUE_INFLUXDB_EVENTS = 'influxdb.monitoring'
QUEUE_INFLUXDB_TAGS = 'influxdb.monitoring.ai'
QUEUE_INFLUXDB_HEARTBEAT = 'influxdb.monitoring.heartbeat'
QUEUE_SYSTEM_TAGGER = 'system.rpc.tagger.v{}'.format(__major_version__)
QUEUE_SYSTEM_REQUESTS = 'system.rpc.requests.v{}'.format(__major_version__)
QUEUE_TESTBED_HEARTBEAT = 'testbed.rpc.heartbeat.v{}'.format(__major_version__)
QUEUE_TESTBED_EVENTS = 'testbed.rpc.events.v{}'.format(__major_version__)

# CASAS Exchanges
EXCHANGE_TAGS = 'all.ai.testbed.casas'
EXCHANGE_EVENTS = 'all.events.testbed.casas'
EXCHANGE_HEARTBEAT = 'all.heartbeat.testbed.casas'
EXCHANGE_REQUESTS = 'all.requests.system.casas'
EXCHANGE_STATESUMMARY = 'all.statesummary.testbed.casas'
EXCHANGE_SYSTEM_ALG_PROC = 'all.system.algorithm.processing'
EXCHANGE_REQUEST_STATESUMMARY = 'request.statesummary.testbed.casas'


class CasasDatetimeException(Exception):
    """A custom exception to help enforce the use of timezones in datetime objects across CASAS.

    Attributes
    ----------
    value : str
        The description of the error situation.
    """
    def __init__(self, value):
        """Initialize a CasasDatetimeException object.

        Parameters
        ----------
        value : str
            The description of the error situation.
        """
        self.value = value
        return

    def __str__(self):
        """Get a string of the exception.

        Returns
        -------
        str
            A description of the error situation.
        """
        return repr(self.value)


class CasasRabbitMQException(Exception):
    """A custom exception to help enforce the use of the consuming state versus some of the RPC
    methods in the casas.rabbitmq.Connection class.

    Attributes
    ----------
    value : str
        The description of the error situation.
    """
    def __init__(self, value):
        """Initialize a CasasRabbitMQException object.

        Parameters
        ----------
        value : str
            The description of the error situation.
        """
        self.value = value
        return

    def __str__(self):
        """Get a string of the exception.

        Returns
        -------
        str
            A description of the error situation.
        """
        return repr(self.value)


class AiqDataException(Exception):
    """A custom exception to help enforce the standardization of our data types.

    Attributes
    ----------
    value : str
        The description of the error situation.
    """
    def __init__(self, value):
        """Initialize a AiqDataException object.

        Parameters
        ----------
        value : str
            The description of the error situation.
        """
        self.value = value
        return

    def __str__(self):
        """Get a string of the exception.

        Returns
        -------
        str
            A description of the error situation.
        """
        return repr(self.value)


class AiqExperimentException(Exception):
    """A custom exception to help signal that there was an error in the experiment.

    Attributes
    ----------
    value : str
        The description of the error situation.
    """
    def __init__(self, value):
        """Initialize a AiqExperimentException object.

        Parameters
        ----------
        value : str
            The description of the error situation.
        """
        self.value = value
        return

    def __str__(self):
        """Get a string of the exception.

        Returns
        -------
        str
            A description of the error situation.
        """
        return repr(self.value)


class CasasObject(object):
    """The base class for all of the CASAS objects.

    Attributes
    ----------
    action : str
        The defined action value for json.
    target : str
        The target for this object.
    serial : str
        The serial for this object.
    sensor_1 : str
        The translated primary sensor name.
    sensor_2 : str
        The translated secondary sensor name.
    sensor_type : str
        The sensor type for this object.
    package_type : str
        The package type for this object.
    site : str
        The site this object is associated with.
    epoch : float
        A float representation of the Unix epoch for this object.
    stamp : datetime.datetime
        The UTC datetime.datetime object for the value in epoch.
    stamp_local : datetime.datetime
        The site local datetime.datetime object for the value in epoch.
    secret : str
        The secret value that is paired with key for uploading events. If this is not provided
        it is removed from the JSON object before returning.
    key : str
        The key value that is paired with secret for uploading events. If this is not provided
        it is removed from the JSON object before returning.
    """

    def __init__(self):
        """Initialize a new CasasObject object.
        """
        self.action = None
        self.target = None
        self.serial = None
        self.sensor_1 = None
        self.sensor_2 = None
        self.sensor_type = None
        self.package_type = None
        self.site = None
        self.epoch = None
        self.stamp = None
        self.stamp_local = None
        self.secret = None
        self.key = None
        return

    def localize_stamp(self, timezone=pytz.timezone('America/Los_Angeles')):
        """Converts the UTC stamp into local stamp.

        Parameters
        ----------
        timezone : pytz.timezone
            The timezone to localize stamp into (default = America/Los_Angeles).
        """
        if self.stamp is None and self.epoch is not None:
            self.stamp = datetime.datetime.utcfromtimestamp(float(self.epoch))
            self.stamp = self.stamp.replace(tzinfo=pytz.utc)

        if self.stamp is not None:
            self.stamp_local = pytz.utc.localize(self.stamp.replace(tzinfo=None),
                                                 is_dst=None).astimezone(timezone)
        return

    def translate(self, translate_group):
        if self.action not in ['event', 'tag', 'control']:
            return

        if self.target in translate_group.t_dict:
            if len(translate_group.t_dict[self.target]) == 1:
                # If there is only one entry for this target, then go ahead and translate it.
                self.sensor_1 = translate_group.t_dict[self.target][0].sensor_1
                self.sensor_2 = translate_group.t_dict[self.target][0].sensor_2
            else:
                # There are either 0 or more than 1 translations for this target, we will iterate
                # over the options and check for valid matches.
                for translate in translate_group.t_dict[self.target]:
                    if translate.start_stamp is None and translate.end_stamp is None:
                        # If both the start_epoch and end_epoch values are None, then this
                        # translation is considered valid for all times.  Technically this should
                        # only show up as a single entry.
                        self.sensor_1 = translate.sensor_1
                        self.sensor_2 = translate.sensor_2
                    elif translate.start_stamp is None and translate.end_stamp is not None:
                        if self.stamp < translate.end_stamp:
                            self.sensor_1 = translate.sensor_1
                            self.sensor_2 = translate.sensor_2
                    elif translate.start_stamp is not None and translate.end_stamp is None:
                        if translate.start_stamp <= self.stamp:
                            self.sensor_1 = translate.sensor_1
                            self.sensor_2 = translate.sensor_2
                    elif translate.start_stamp is not None and translate.end_stamp is not None:
                        if translate.start_stamp <= self.stamp < translate.end_stamp:
                            self.sensor_1 = translate.sensor_1
                            self.sensor_2 = translate.sensor_2
        return

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing this object.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
        """
        raise ValueError("This object did not implement get_json().")

    def get_detailed_json(self, secret=None, key=None):
        """Returns a JSON string representing this object with additional fields.

        If classes that inherit from this class do not implement this function, the inherited
        behavior is that this function will return the result of self.get_json(secret, key).

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
        """
        return self.get_json(secret, key)


class CasasError(CasasObject):
    """This class represents an instance of a `CasasError`, which is part of a `CasasResponse`.

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'casas_error'.
    error_type : str
        The type of the error.
    message : str
        A brief description fo the error.
    error_dict : dict
        An optional dict of additional information about the error.
    """

    def __init__(self, error_type, message, error_dict=None):
        """Initialize a new CasasError object.

        Parameters
        ----------
        error_type : str
            The type of the error.
        message : str
            A brief description of the error.
        error_dict : dict, optional
            An optional dict of additional information about the error.
        """
        super(CasasError, self).__init__()

        self.action = CASAS_ERROR
        self.error_type = error_type
        self.message = message
        self.error_dict = error_dict
        return

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the CasasError.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret, not used here.
        key : str, optional
            The key in the key:secret, not used here.

        Returns
        -------
        str
            A JSON string representing the CasasError.
        """
        obj = {"action": self.action,
               "data": {"error_type": self.error_type,
                        "message": self.message,
                        "error_dict": self.error_dict}}
        return json.dumps(obj)


class CasasResponse(CasasObject):
    """This class represents an instance of a `CasasResponse`, which is used with RPC calls.

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'casas_response'.
    status : str
        The status of the response.
    response_type : str
        The type of the response message.
    error_message : str
        An optional general error message for the response.
    error_list : list
        Optional list of `CasasError` objects.
    """

    def __init__(self, status='success', response_type='data', error_message='No Errors',
                 error_list=None):
        """Initialize a new CasasResponse object.

        Parameters
        ----------
        status : str, optional
            Define the status of the response.
        response_type : str, optional
            Define the type of the response message.
        error_message : str, optional
            Optional general error message for the response.
        error_list : list, optional
            Optional list of errors.
        """
        super(CasasResponse, self).__init__()

        # Check for a sentinel value, if there assign an empty list.
        if error_list is None:
            error_list = list()

        self.action = CASAS_RESPONSE
        self.status = status
        self.response_type = response_type
        self.error_message = error_message
        self.error_list = error_list
        return

    def add_error(self, casas_error, error_type=None):
        """Add a CasasError object to the CasasResponse.

        Parameters
        ----------
        casas_error : CasasError
            An error to add to the CasasResponse.
        error_type : str, optional
            An optional error type to set the response_type for this object.
        """
        self.status = 'error'
        self.error_list.append(casas_error)
        if error_type is not None:
            self.response_type = error_type
        return

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the CasasResponse.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret, not used here.
        key : str, optional
            The key in the key:secret, not used here.

        Returns
        -------
        str
            A JSON string representing the CasasResponse.
        """
        obj = {"action": self.action,
               "status": self.status,
               "type": self.response_type,
               "error_message": self.error_message,
               "error_list": list()}

        for error in self.error_list:
            obj['error_list'].append(json.loads(error.get_json()))

        return json.dumps(obj)


class CasasObjectList(CasasObject):
    """This class represents a list of one or more CasasObjects.
    """

    def __init__(self, object_list=None):
        """Initialize a new CasasObjectList object.

        Parameters
        ----------
        object_list : list, optional
            A list of CasasObject that you wish to handle together.
        """
        super(CasasObjectList, self).__init__()

        self.action = CASAS_OBJ_LIST
        self.site = None

        if object_list is None:
            self.object_list = list()
        else:
            self.object_list = copy.deepcopy(object_list)

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, item):
        return self.object_list[item]

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a newline delimited string of the objects in the self.object_list.

        Returns
        -------
        str
            A newline delimited string of the objects in the self.object_list.
        """
        my_list = list()
        for item in self.object_list:
            my_list.append(item.get_old_str())
        my_str = '\n'.join(my_list)
        return my_str

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the CasasObjectList.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the CasasObjectList.
        """
        obj = {'site': self.site,
               'secret': secret,
               'key': key,
               'action': self.action,
               'data': {'object_list': list()}}

        for item in self.object_list:
            obj['data']['object_list'].append(json.loads(item.get_json(secret=secret, key=key)))

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)

    def get_detailed_json(self, secret=None, key=None):
        """Returns a JSON string representing the CasasObjectList with additional fields.

        This function primarily calls the detailed JSON functions of it's contained objects.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret requi9red for uploading data.

        Returns
        -------
        str
            A JSON string representing the CasasObjectList
        """
        obj = {'site': self.site,
               'secret': secret,
               'key': key,
               'action': self.action,
               'data': {'object_list': list()}}

        for item in self.object_list:
            obj['data']['object_list'].append(json.loads(item.get_detailed_json(secret=secret,
                                                                                key=key)))

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class CasasGetObject(CasasObject):
    """This class represents an authenticated wrapper around a request for an object.

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'casas_get_object'.
    casas_object : CasasObject
        The CasasObject that we want to request.
    key : str
        The key value that is paired with secret for authorizing access to the requested object.
    secret : str
        The secret value that is paired with key for authorizing access to the requested object.
    site : str
        The testbed that is associated with the key and secret.
    """

    def __init__(self, casas_object, key, secret, site):
        """Initialize a new CasasGetObject object.

        Parameters
        ----------
        casas_object : CasasObject
            The CasasObject that we want to request.
        key : str
            The key value that is paired with secret for authorizing access to the requested object.
        secret : str
            The secret value that is paired with key for authorizing access to the requested object.
        site : str
            The testbed that is associated with the key and secret.
        """
        super(CasasGetObject, self).__init__()

        self.action = CASAS_GET_OBJ
        self.casas_object = copy.deepcopy(casas_object)
        self.key = key
        self.secret = secret
        self.site = site
        return

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the CasasGetObject.

        Parameters
        ----------
        secret : str, optional
            This value is not used, we use the class object instead.
        key : str, optional
            This value is not used, we use the class object instead.

        Returns
        -------
        str
            A JSON string representing the CasasGetObject.
        """
        obj = {'action': self.action,
               'secret': self.secret,
               'key': self.key,
               'site': self.site,
               'data': {'object': json.loads(self.casas_object.get_json())}}
        return json.dumps(obj)


class CasasSetObject(CasasObject):
    """This class represents an authenticated wrapper around a request to set or update an object.

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'casas_set_object'.
    casas_object : CasasObject
        The CasasObject that we want to request be set or updated.
    key : str
        The key value that is paired with secret for authorizing access to set or update the
        requested changes to the provided object.
    secret : str
        The secret value that is paired with key for authorizing access to set or update the
        requested changes to the provided object.
    site : str
        The testbed that is associated with the key and secret.
    """

    def __init__(self, casas_object, key, secret, site):
        """Initialize a new CasasSetObject object.

        Parameters
        ----------
        casas_object : CasasObject
            The CasasObject that we want to set or update.
        key : str
            The key value that is paired with secret for authorizing access to set or update the
            requested changes to the provided object.
        secret : str
            The secret value that is paired with key for authorizing access to set or update the
            requested changes to the provided object.
        site : str
            The testbed that is associated with the key and secret.
        """
        super(CasasSetObject, self).__init__()

        self.action = CASAS_SET_OBJ
        self.casas_object = copy.deepcopy(casas_object)
        self.key = key
        self.secret = secret
        self.site = site
        return

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the CasasSetObject.

        Parameters
        ----------
        secret : str, optional
            This value is not used, we use the class object instead.
        key : str, optional
            This value is not used, we use the class object instead.

        Returns
        -------
        str
            A JSON string representing the CasasSetObject.
        """
        obj = {'action': self.action,
               'secret': self.secret,
               'key': self.key,
               'site': self.site,
               'data': {'object': json.loads(self.casas_object.get_json())}}
        return json.dumps(obj)


class Testbed(CasasObject):
    """This class represents an instance of a Testbed.

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'testbed'.
    site : str
        The name of the Testbed.
    description : str
        An optional description of the testbed.
    active : boolean
        A flag to identify if this site is active.
    created_on : datetime.datetime
        A UTC timestamp of when this site was created.
    created_on_epoch : float
        The UNIX epoch of the `created_on` datetime.datetime.
    has_internet : boolean
        A flag to identify if this site has an internet connection.
    timezone : str
        The full time zone name for this site.
    last_seen : datetime.datetime
        The UTC timestamp of when this site was last seen.
    last_seen_epoch : float
        The UNIX epoch of the `last_seen` datetime.datetime.
    first_event : datetime.datetime
        The UTC timestamp of the first event recorded for this site.
    first_event_epoch : float
        The UNIX epoch of the `first_event` datetime.datetime.
    latest_event : datetime.datetime
        The UTC timestamp of the most recent event recorded for this site.
    latest_event_epoch : float
        The UNIX epoch of the `latest_event` datetime.datetime.
    """

    def __init__(self, site, description=None, active=False, created_on=None, has_internet=False,
                 timezone='America/Los_Angeles', last_seen=None, first_event=None,
                 latest_event=None):
        """Initialize a new Testbed object.

        Parameters
        ----------
        site : str
            The name of the Testbed.
        description : str, optional
            An optional description of the testbed.
        active : boolean, optional
            A flag to identify if this site is active.
        created_on : datetime.datetime, optional
            A UTC timestamp of when this site was created.
        has_internet : boolean, optional
            A flag to identify if this site has an internet connection.
        timezone : str, optional
            The full time zone name for this site.
        last_seen : datetime.datetime, optional
            The UTC timestamp of when this site was last seen.
        first_event : datetime.datetime, optional
            The UTC timestamp of the first event recorded for this site.
        latest_event : datetime.datetime, optional
            The UTC timestamp of the most recent event recorded for this site.

        Raises
        ------
        CasasDatetimeException
            If `created_on`, `last_seen`, `first_event`, or `latest_event` is a naive
            datetime.datetime object, where the tzinfo is not set.
        """
        super(Testbed, self).__init__()

        self.action = TESTBED
        self.site = site
        self.description = description
        self.active = active
        self.created_on = created_on
        self.created_on_epoch = make_epoch(created_on)
        self.timezone = timezone
        self.has_internet = has_internet
        self.last_seen = last_seen
        self.last_seen_epoch = make_epoch(last_seen)
        self.first_event = first_event
        self.first_event_epoch = make_epoch(first_event)
        self.latest_event = latest_event
        self.latest_event_epoch = make_epoch(latest_event)

        if self.created_on is not None:
            if self.created_on.tzinfo is None:
                raise CasasDatetimeException("Testbed.created_on is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.last_seen is not None:
            if self.last_seen.tzinfo is None:
                raise CasasDatetimeException("Testbed.last_seen is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.first_event is not None:
            if self.first_event.tzinfo is None:
                raise CasasDatetimeException("Testbed.first_event is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.latest_event is not None:
            if self.latest_event.tzinfo is None:
                raise CasasDatetimeException("Testbed.latest_event is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the Algorithm fields.

        Returns
        -------
        str
            A tab delimited string of the Algorithm fields.
        """
        mystr = "{}\t{}\t{}".format(str(self.site),
                                    str(self.active),
                                    str(self.timezone))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the Testbed.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the Testbed.

        Raises
        ------
        CasasDatetimeException
            If `created_on`, `last_seen`, `first_event`, or `latest_event` is a naive
            datetime.datetime object, where the tzinfo is not set.
        """
        if self.created_on is not None:
            if self.created_on.tzinfo is None:
                raise CasasDatetimeException("Testbed.created_on is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.last_seen is not None:
            if self.last_seen.tzinfo is None:
                raise CasasDatetimeException("Testbed.last_seen is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.first_event is not None:
            if self.first_event.tzinfo is None:
                raise CasasDatetimeException("Testbed.first_event is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.latest_event is not None:
            if self.latest_event.tzinfo is None:
                raise CasasDatetimeException("Testbed.latest_event is naive, "
                                             "datetime.datetime.tzinfo is not set!")

        self.created_on_epoch = make_epoch(self.created_on)
        self.last_seen_epoch = make_epoch(self.last_seen)

        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"description": self.description,
                        "active": self.active,
                        "timezone": self.timezone,
                        "has_internet": self.has_internet,
                        "created_on_epoch": self.created_on_epoch,
                        "last_seen_epoch": self.last_seen_epoch,
                        "first_event_epoch": self.first_event_epoch,
                        "latest_event_epoch": self.latest_event_epoch}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class Event(CasasObject):
    """Represents an Event object that gets passed around.

    This is a standard Event JSON message.

    .. code-block:: JSON
        :emphasize-lines: 5

        {"channel": "",
         "site": "",
         "secret": "",
         "key": "",
         "action": "event",
         "data": {"uuid": "",
                  "epoch": "",
                  "serial": "",
                  "target": "",
                  "message": "",
                  "by": "",
                  "category": "",
                  "sensor_type": "",
                  "package_type": ""
                  }
        }

    This is a detailed Event JSON message.

    .. code-block:: JSON
        :emphasize-lines: 5

        {"channel": "",
         "site": "",
         "secret": "",
         "key": "",
         "action": "event",
         "data": {"uuid": "",
                  "epoch": "",
                  "stamp": "",
                  "stamp_local": "",
                  "sensor_1": "",
                  "sensor_2": "",
                  "serial": "",
                  "target": "",
                  "message": "",
                  "by": "",
                  "category": "",
                  "sensor_type": "",
                  "package_type": ""
                  }
        }



    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'event'.
    by : str
        The name of the agent that created this event.
    category : str
        Identifies the category of the event.
    channel : str
        The channel that this event was published to.
    epoch : float
        A float representing the UTC epoch for when the event occurred.
    event_id : str
        An optional value representing this event's event_id in the database.
    message : str
        The core message of the event.
    package_type : str
        Defines the package type of the event.
    sensor_1 : str
        An optional translation value for this sensor target.
    sensor_2 : str
        An optional translation value for this sensor target.
    sensor_type : str
        Defines the sensor type of the event.
    serial : str
        The serial identification of the target.
    site : str
        The name of the testbed where this event was created.
    stamp : datetime.datetime
        The UTC datetime.datetime object for when the event occurred.
    stamp_local : datetime.datetime
        The local datetime.datetime object when the event occurred.
    target : str
        The target generating the event.
    uuid : str
        A UUID string identifying this event.
    """

    def __init__(self, category, package_type, sensor_type, message, target,
                 serial, by, channel, site, epoch=None, uuid=None, sensor_1=None,
                 sensor_2=None, event_id=None, stamp=None, stamp_local=None,
                 request_id=None, request_size=None):
        """Initialize a new Event object.

        Parameters
        ----------
        category : str
            Identifies the category of the event.
        package_type : str
            Defines the package type of the event.
        sensor_type : str
            Defines the sensor type of the event.
        message : str
            The core message of the event.
        target : str
            The target generating the event.
        serial : str
            The serial identification of the target.
        by : str
            The name of the agent that created this event.
        channel : str
            The channel that this event was published to.
        site : str
            The name of the testbed where this event was created.
        epoch : float
            A float representing the UTC epoch for when the event occurred.
        uuid : str, optional
            A UUID string identifying this event.
        sensor_1 : str, optional
            An optional translation value for this sensor target.
        sensor_2 : str, optional
            An optional translation value for this sensor target.
        event_id : str, optional
            An optional value representing this event's event_id in the database.
        stamp : datetime.datetime, optional
            The UTC datetime.datetime object for when the event occurred.
        stamp_local : datetime.datetime, optional
            The local datetime.datetime object when the event occurred.

        Raises
        ------
        CasasDatetimeException
            If `stamp` or `stamp_local` is a naive datetime.datetime object, where the tzinfo is
            not set.
        """
        super(Event, self).__init__()

        self.action = EVENT
        self.category = category
        self.package_type = package_type
        self.sensor_type = sensor_type
        self.message = message
        self.target = target
        self.serial = serial
        self.by = by
        self.channel = channel
        self.site = site
        self.epoch = epoch
        self.uuid = uuid
        self.sensor_1 = sensor_1
        self.sensor_2 = sensor_2
        self.stamp = stamp
        self.stamp_local = stamp_local
        self.event_id = event_id
        self.request_id = request_id
        self.request_size = request_size
        if self.stamp is not None:
            if self.stamp.tzinfo is None:
                raise CasasDatetimeException("Event.stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.stamp_local is not None:
            if self.stamp_local.tzinfo is None:
                raise CasasDatetimeException("Event.stamp_local is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        self.validate_event()
        return

    def validate_event(self):
        """Validates the event object, and converts the epoch into a UTC stamp.
        """
        if self.category == "":
            self.category = "unknown"
        if self.package_type == "":
            self.package_type = "unknown"
        if self.sensor_type == "":
            self.sensor_type = "unknown"
        if self.message == "":
            self.message = "unknown"
        if self.target == "":
            self.target = "unknown"
        if self.serial == "":
            self.serial = "unknown"
        if self.by == "":
            self.by = "unknown"
        if self.channel == "":
            self.channel = "unknown"
        if self.site == "":
            self.site = "unknown"
        if self.epoch is None or self.epoch == "":
            self.epoch = time.time()
        if self.stamp is None:
            self.stamp = datetime.datetime.utcfromtimestamp(float(self.epoch))
            self.stamp = self.stamp.replace(tzinfo=pytz.utc)
        if self.uuid is None:
            self.uuid = str(uuid.uuid4().hex)
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the Event fields.

        Returns
        -------
        str
            A tab delimited string of the Event fields.
        """
        mystr = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}" \
            .format(str(self.stamp),
                    str(self.serial),
                    str(self.target),
                    str(self.message),
                    str(self.category),
                    str(self.by),
                    str(self.sensor_type),
                    str(self.package_type),
                    str(self.channel),
                    str(self.site))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the Event.

        Parameters
        ----------
        secret : str
            The secret value that is paired with key for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        key : str
            The key value that is paired with secret for uploading events. If this is not provided
            it is removed from the JSON object before returning.

        Returns
        -------
        str
            A JSON string representing the Event.
        """
        obj = {"channel": self.channel,
               "site": self.site,
               "secret": secret,
               "key": key,
               "action": self.action,
               "data": {"uuid": self.uuid,
                        "epoch": self.epoch,
                        "serial": self.serial,
                        "target": self.target,
                        "message": self.message,
                        "by": self.by,
                        "category": self.category,
                        "sensor_type": self.sensor_type,
                        "package_type": self.package_type},
               "request": {"id": self.request_id,
                           "size": self.request_size}}
        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)

    def get_detailed_json(self, secret=None, key=None):
        """Returns a JSON string representing the Event with additional fields.

        This function adds additional optional fields into the JSON object that it returns.

        Parameters
        ----------
        secret : str
            The secret value that is paired with key for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        key : str
            The key value that is paired with secret for uploading events. If this is not provided
            it is removed from the JSON object before returning.

        Returns
        -------
        str
            A JSON string representing the Event.
        """
        obj = {"channel": self.channel,
               "site": self.site,
               "secret": secret,
               "key": key,
               "action": self.action,
               "data": {"uuid": self.uuid,
                        "epoch": self.epoch,
                        "stamp": str(self.stamp),
                        "stamp_local": str(self.stamp_local),
                        "sensor_1": self.sensor_1,
                        "sensor_2": self.sensor_2,
                        "serial": self.serial,
                        "target": self.target,
                        "message": self.message,
                        "by": self.by,
                        "category": self.category,
                        "sensor_type": self.sensor_type,
                        "package_type": self.package_type},
               "request": {"id": self.request_id,
                           "size": self.request_size}}
        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)

    def tag(self, created_by=None, label=None, value=None, dataset=None, experiment=None):
        """Returns a Tag object built from this Event and the provided parameters.

        Parameters
        ----------
        created_by : str
            A string depicting who/what created the tag being put on this event.
        label : str
            The label being tagged on this event.
        value : str
            An optional value for the tagged event.
        dataset : str
            The name of the dataset this tag is part of.
        experiment : str
            The name of the experiment this tag is part of.

        Returns
        -------
        Tag
            A new Tag object representing the tagged event.

        Raises
        ------
        ValueError
            Tag.dataset must have an actual value!
        ValueError
            Tag.experiment must have an actual value!
        """
        if created_by is None:
            created_by = "unknown"
        if dataset is None:
            raise ValueError("Tag.dataset must have an actual value!")
        if experiment is None:
            raise ValueError("Tag.experiment must have an actual value!")
        new_tag = Tag(category=self.category,
                      package_type=self.package_type,
                      sensor_type=self.sensor_type,
                      message=self.message,
                      target=self.target,
                      serial=self.serial,
                      by=self.by,
                      channel=self.channel,
                      site=self.site,
                      epoch=self.epoch,
                      uuid=self.uuid,
                      created_by=created_by,
                      label=label,
                      value=value,
                      dataset=dataset,
                      experiment=experiment,
                      sensor_1=self.sensor_1,
                      sensor_2=self.sensor_2,
                      event_id=self.event_id,
                      stamp=self.stamp,
                      stamp_local=self.stamp_local,
                      request_id=self.request_id,
                      request_size=self.request_size)
        return new_tag


class Tag(Event):
    """Represents a Tag object that gets passed around.

    This is a standard Tag JSON message.

    .. code-block:: JSON
        :emphasize-lines: 5

        {"channel": "",
         "site": "",
         "secret": "",
         "key": "",
         "action": "tag",
         "data": {"tag": {"created_by": "",
                          "label": {"name": "",
                                    "value": ""
                                   },
                          "dataset": "",
                          "experiment": ""
                          },
                  "uuid": "",
                  "epoch": "",
                  "serial": "",
                  "target": "",
                  "message": "",
                  "by": "",
                  "category": "",
                  "sensor_type": "",
                  "package_type": ""
                  }
        }

    This is a detailed Tag JSON message.

    .. code-block:: JSON
        :emphasize-lines: 5

        {"channel": "",
         "site": "",
         "secret": "",
         "key": "",
         "action": "tag",
         "data": {"tag": {"created_by": "",
                          "label": {"name": "",
                                    "value":""
                                    },
                          "dataset": "",
                          "experiment": ""
                          },
                  "uuid": "",
                  "epoch": "",
                  "stamp": "",
                  "stamp_local": "",
                  "sensor_1": "",
                  "sensor_2": "",
                  "serial": "",
                  "target": "",
                  "message": "",
                  "by": "",
                  "category": "",
                  "sensor_type": "",
                  "package_type": ""
                  }
        }

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'tag'.
    by : str
        The name of the agent that created this event.
    category : str
        Identifies the category of the event.
    channel : str
        The channel that this event was published to.
    created_by : str
        A string depicting who/what created the tag being put on this event.
    dataset : str
        The name of the dataset this tag is part of.
    epoch : float
        A float representing the UTC epoch for when the event occurred.
    event_id : str
        An optional value representing this event's event_id in the database.
    experiment : str
        The name of the experiment this tag is part of.
    label : str
        The label being tagged on this event.
    message : str
        The core message of the event.
    package_type : str
        Defines the package type of the event.
    sensor_1 : str
        An optional translation value for this sensor target.
    sensor_2 : str
        An optional translation value for this sensor target.
    sensor_type : str
        Defines the sensor type of the event.
    serial : str
        The serial identification of the target.
    site : str
        The name of the testbed where this event was created.
    stamp : datetime.datetime
        The UTC datetime.datetime object for when the event occurred.
    stamp_local : datetime.datetime
        The local datetime.datetime object when the event occurred.
    target : str
        The target generating the event.
    uuid : str
        A UUID string identifying this event.
    value : str
        An optional value for the tagged event.
    """

    def __init__(self, category, package_type, sensor_type, message, target,
                 serial, by, channel, site, epoch, uuid, created_by, label,
                 value, dataset, experiment, sensor_1=None, sensor_2=None, event_id=None,
                 stamp=None, stamp_local=None, request_id=None, request_size=None):
        """Initialize a new Tag object.

        Parameters
        ----------
        category : str
            Identifies the category of the event.
        package_type : str
            Defines the package type of the event.
        sensor_type : str
            Defines the sensor type of the event.
        message : str
            The core message of the event.
        target : str
            The target generating the event.
        serial : str
            The serial identification of the target.
        by : str
            The name of the agent that created this event.
        channel : str
            The channel that this event was published to.
        site : str
            The name of the testbed where this event was created.
        epoch : float
            A float representing the UTC epoch for when the event occurred.
        uuid : str
            A UUID string identifying this event.
        created_by : str
            A string depicting who/what created the tag being put on this event.
        label : str
            The label being tagged on this event.
        value : str
            An optional value for the tagged event.
        dataset : str
            The name of the dataset this tag is part of.
        experiment : str
            The name of the experiment this tag is part of.
        sensor_1 : str
            An optional translation value for this sensor target.
        sensor_2 : str
            An optional translation value for this sensor target.
        event_id : str
            An optional value representing this event's event_id in the database.
        stamp : datetime.datetime, optional
            The UTC datetime.datetime object for when the event occurred.
        stamp_local : datetime.datetime, optional
            The local datetime.datetime object when the event occurred.

        Raises
        ------
        CasasDatetimeException
            If `stamp` or `stamp_local` is a naive datetime.datetime object, where the tzinfo is
            not set.
        """
        super(Tag, self).__init__(category=category,
                                  package_type=package_type,
                                  sensor_type=sensor_type,
                                  message=message,
                                  target=target,
                                  serial=serial,
                                  by=by,
                                  channel=channel,
                                  site=site)

        self.action = TAG
        self.category = category
        self.package_type = package_type
        self.sensor_type = sensor_type
        self.message = message
        self.target = target
        self.serial = serial
        self.by = by
        self.channel = channel
        self.site = site
        self.epoch = epoch
        self.uuid = uuid
        self.created_by = created_by
        self.label = label
        self.value = value
        self.dataset = dataset
        self.experiment = experiment
        self.sensor_1 = sensor_1
        self.sensor_2 = sensor_2
        self.event_id = event_id
        self.stamp = stamp
        self.stamp_local = stamp_local
        self.request_id = request_id
        self.request_size = request_size
        if self.stamp is not None:
            if self.stamp.tzinfo is None:
                raise CasasDatetimeException("Tag.stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.stamp_local is not None:
            if self.stamp_local.tzinfo is None:
                raise CasasDatetimeException("Tag.stamp_local is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        self.validate_event()
        self.validate_tag()
        return

    def validate_tag(self):
        """Validates the Tag attributes.

        Raises
        ------
        ValueError
            If Tag.dataset is not defined or is an empty string.
        ValueError
            If Tag.experiment is not defined or is an empty string.
        """
        if self.created_by is None or str(self.created_by) == "":
            self.created_by = "unknown"
        if self.dataset is None or str(self.dataset) == "":
            self.dataset = "unknown"
            raise ValueError("Tag.dataset must have an actual value!")
        if self.experiment is None or str(self.experiment) == "":
            self.experiment = "unknown"
            raise ValueError("Tag.experiment must have an actual value!")
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the Tag fields.

        Returns
        -------
        str
            A tab delimited string of the Tag fields.
        """
        mystr = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{} {}\t{}\t{}\t{}" \
            .format(str(self.stamp),
                    str(self.serial),
                    str(self.target),
                    str(self.message),
                    str(self.category),
                    str(self.by),
                    str(self.sensor_type),
                    str(self.package_type),
                    str(self.channel),
                    str(self.site),
                    str(self.label),
                    str(self.value),
                    str(self.created_by),
                    str(self.dataset),
                    str(self.experiment))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the Tag.

        Parameters
        ----------
        secret : str
            The secret value that is paired with key for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        key : str
            The key value that is paired with secret for uploading events. If this is not provided
            it is removed from the JSON object before returning.

        Returns
        -------
        str
            A JSON string representing the Tag.
        """
        obj = {"channel": self.channel,
               "site": self.site,
               "secret": secret,
               "key": key,
               "action": self.action,
               "data": {"tag": {"created_by": self.created_by,
                                "label": {"name": self.label,
                                          "value": self.value},
                                "dataset": self.dataset,
                                "experiment": self.experiment},
                        "uuid": self.uuid,
                        "epoch": self.epoch,
                        "serial": self.serial,
                        "target": self.target,
                        "message": self.message,
                        "by": self.by,
                        "category": self.category,
                        "sensor_type": self.sensor_type,
                        "package_type": self.package_type},
               "request": {"id": self.request_id,
                           "size": self.request_size}}
        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)

    def get_detailed_json(self, secret=None, key=None):
        """Returns a JSON string representing the Tag with additional fields.

        This function adds additional optional fields into the JSON object that it returns.

        Parameters
        ----------
        secret : str
            The secret value that is paired with key for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        key : str
            The key value that is paired with secret for uploading events. If this is not provided
            it is removed from the JSON object before returning.

        Returns
        -------
        str
            A JSON string representing the Tag.
        """
        obj = {"channel": self.channel,
               "site": self.site,
               "secret": secret,
               "key": key,
               "action": self.action,
               "data": {"tag": {"created_by": self.created_by,
                                "label": {"name": self.label,
                                          "value": self.value},
                                "dataset": self.dataset,
                                "experiment": self.experiment},
                        "uuid": self.uuid,
                        "epoch": self.epoch,
                        "stamp": str(self.stamp),
                        "stamp_local": str(self.stamp_local),
                        "sensor_1": self.sensor_1,
                        "sensor_2": self.sensor_2,
                        "serial": self.serial,
                        "target": self.target,
                        "message": self.message,
                        "by": self.by,
                        "category": self.category,
                        "sensor_type": self.sensor_type,
                        "package_type": self.package_type},
               "request": {"id": self.request_id,
                           "size": self.request_size}}
        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class Control(CasasObject):
    """Represents a Control object that gets passed around.

    This is a standard Control JSON message.

    .. code-block:: JSON
        :emphasize-lines: 5

        {"channel": "",
         "site": "",
         "secret": "",
         "key": "",
         "action": "control",
         "data": {"uuid": "",
                  "epoch": "",
                  "serial": "",
                  "target": "",
                  "command": "",
                  "value": "",
                  "replyto": "",
                  "cid": "",
                  "by": "",
                  "category": ""
                  }
        }

    This is a Control JSON message converted to Event.

    .. code-block:: JSON
        :emphasize-lines: 5

        {"channel": "",
         "site": "",
         "secret": "",
         "key": "",
         "action": "event",
         "data": {"uuid": "",
                  "epoch": "",
                  "serial": "",
                  "target": "",
                  "message": "{'command':'','value':'','cid':'','replyto':'','response':''}",
                  "by": "",
                  "category": "control",
                  "sensor_type": "control",
                  "package_type": "control"
                  }
        }

    This is a detailed Control JSON message.

    .. code-block:: JSON
        :emphasize-lines: 5

        {"channel": "",
         "site": "",
         "secret": "",
         "key": "",
         "action": "control",
         "data": {"uuid": "",
                  "epoch": "",
                  "stamp": "",
                  "stamp_local": "",
                  "sensor_1": "",
                  "sensor_2": "",
                  "serial": "",
                  "target": "",
                  "command": "",
                  "value": "",
                  "replyto": "",
                  "cid": "",
                  "by": "",
                  "category": "",
                  "sensor_type": "",
                  "package_type": ""
                  }
        }

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'control'.
    by : str
        The name of the agent that created this command.
    category : str
        Identifies the category of the control command.
    channel : str
        The channel that this command was published to.
    cid : str, optional
        An optional value for keeping track of a control command.
    command : str
        The command message being sent.
    epoch : float
        A float representing the UTC epoch for when the command occurred.
    event_id : str
        An optional value representing this command's event_id in the database.
    message : str
        The core message of the command.
    package_type : str
        Defines the package type of the command.
    replyto : str, optional
        An optional value of an agent ID to reply to after completing the command.
    response: str, optional
        The response (if any) from executing the control command.
    sensor_1 : str
        An optional translation value for this sensor target.
    sensor_2 : str
        An optional translation value for this sensor target.
    sensor_type : str
        Defines the sensor type of the command.
    serial : str
        The serial identification of the target.
    site : str
        The name of the testbed where this command was created.
    stamp : datetime.datetime
        The UTC datetime.datetime object for when the command occurred.
    stamp_local : datetime.datetime
        The local datetime.datetime object when the command occurred.
    target : str
        The target to execute the command.
    uuid : str
        A UUID string identifying this event/command.
    value : str
        An optional value field being sent with the control command.
    """

    def __init__(self, category, target, serial, by, channel, site, command,
                 value, replyto, cid, response=None, package_type="control",
                 sensor_type="control", message=None, epoch=None, uuid=None,
                 sensor_1=None, sensor_2=None, event_id=None, stamp=None, stamp_local=None):
        """Initialize a new Control object.

        Parameters
        ----------
        category : str
            Identifies the category of the control command.
        target : str
            The target to execute the command.
        serial : str
            The serial identification of the target.
        by : str
            The name of the agent that created this command.
        channel : str
            The channel that this command was published to.
        site : str
            The name of the testbed where this command was created.
        command : str
            The command message being sent.
        value : str
            An optional value field being sent with the control command.
        replyto : str, optional
            An optional value of an agent ID to reply to after completing the command.
        cid : str, optional
            An optional value for keeping track of a control command.
        response: str, optional
            The response (if any) from executing the control command.
        package_type : str
            Defines the package type of the command.
        sensor_type : str
            Defines the sensor type of the command.
        message : str
            The core message of the command.
        epoch : float
            A float representing the UTC epoch for when the command occurred.
        uuid : str
            A UUID string identifying this event/command.
        sensor_1 : str
            An optional translation value for this sensor target.
        sensor_2 : str
            An optional translation value for this sensor target.
        event_id : str
            An optional value representing this command's event_id in the database.
        stamp : datetime.datetime, optional
            The UTC datetime.datetime object for when the command occurred.
        stamp_local : datetime.datetime, optional
            The local datetime.datetime object when the command occurred.

        Raises
        ------
        CasasDatetimeException
            If `stamp` or `stamp_local` is a naive datetime.datetime object, where the tzinfo is
            not set.
        """
        super(Control, self).__init__()

        self.action = CONTROL
        self.category = category
        self.target = target
        self.serial = serial
        self.by = by
        self.channel = channel
        self.site = site
        self.command = command
        self.value = value
        self.replyto = replyto
        self.cid = cid
        self.response = response
        self.package_type = package_type
        self.sensor_type = sensor_type
        self.message = message
        self.epoch = epoch
        self.uuid = uuid
        self.sensor_1 = sensor_1
        self.sensor_2 = sensor_2
        self.event_id = event_id
        self.stamp = stamp
        self.stamp_local = stamp_local
        if self.stamp is not None:
            if self.stamp.tzinfo is None:
                raise CasasDatetimeException("Control.stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.stamp_local is not None:
            if self.stamp_local.tzinfo is None:
                raise CasasDatetimeException("Control.stamp_local is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        self.validate_control()
        return

    def validate_control(self):
        """Validates the new Control object and converts the epoch.
        """
        if self.category == "":
            self.category = "control"
        if self.target == "":
            self.target = "unknown"
        if self.serial == "":
            self.serial = "unknown"
        if self.by == "":
            self.by = "unknown"
        if self.channel == "":
            self.channel = "unknown"
        if self.site == "":
            self.site = "unknown"
        if self.epoch is None:
            self.epoch = time.time()
        if self.stamp is None:
            self.stamp = datetime.datetime.utcfromtimestamp(float(self.epoch))
            self.stamp = self.stamp.replace(tzinfo=pytz.utc)
        if self.uuid == "":
            self.uuid = str(uuid.uuid4().hex)
        self.package_type = "control"
        self.sensor_type = "control"
        self._build_message()
        return

    def _build_message(self):
        """Builds the message from the Control fields.
        """
        self.message = dict({'command': self.command,
                             'value': self.value,
                             'cid': self.cid,
                             'replyto': self.replyto})
        if self.response is not None:
            self.message['response'] = self.response
        self.message = str(json.dumps(self.message, sort_keys=True))
        return

    def get_as_event_obj(self):
        """Returns an Event object representation of the Control object.

        Returns
        -------
        Event
            An Event object representation of this Control object.
            All Control objects are stored in the database as Event objects.
        """
        self._build_message()
        new_event = Event(category=self.category,
                          package_type=self.package_type,
                          sensor_type=self.sensor_type,
                          message=self.message,
                          target=self.target,
                          serial=self.serial,
                          by=self.by,
                          channel=self.channel,
                          site=self.site,
                          epoch=self.epoch,
                          uuid=self.uuid,
                          sensor_1=self.sensor_1,
                          sensor_2=self.sensor_2,
                          event_id=self.event_id,
                          stamp=self.stamp,
                          stamp_local=self.stamp_local)
        return new_event

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the Control fields.

        Returns
        -------
        str
            A tab delimited string of the Control fields.
        """
        mystr = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}" \
            .format(str(self.stamp),
                    str(self.serial),
                    str(self.target),
                    str(self.command),
                    str(self.value),
                    str(self.replyto),
                    str(self.cid),
                    str(self.by),
                    str(self.channel),
                    str(self.site))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the Control.

        Parameters
        ----------
        secret : str
            The secret value that is paired with key for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        key : str
            The key value that is paired with secret for uploading events. If this is not provided
            it is removed from the JSON object before returning.

        Returns
        -------
        str
            A JSON string representing the Control.
        """
        obj = {"channel": self.channel,
               "site": self.site,
               "secret": secret,
               "key": key,
               "action": self.action,
               "data": {"uuid": self.uuid,
                        "epoch": self.epoch,
                        "serial": self.serial,
                        "target": self.target,
                        "command": self.command,
                        "value": self.value,
                        "replyto": self.replyto,
                        "cid": self.cid,
                        "by": self.by,
                        "category": self.category}}
        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)

    def get_detailed_json(self, secret=None, key=None):
        """Returns a JSON string representing the Control with additional fields.

        This function adds additional optional fields into the JSON object that it returns.

        Parameters
        ----------
        secret : str
            The secret value that is paired with key for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        key : str
            The key value that is paired with secret for uploading events. If this is not provided
            it is removed from the JSON object before returning.

        Returns
        -------
        str
            A JSON string representing the Control.
        """
        obj = {"channel": self.channel,
               "site": self.site,
               "secret": secret,
               "key": key,
               "action": self.action,
               "data": {"uuid": self.uuid,
                        "epoch": self.epoch,
                        "stamp": str(self.stamp),
                        "stamp_local": str(self.stamp_local),
                        "sensor_1": self.sensor_1,
                        "sensor_2": self.sensor_2,
                        "serial": self.serial,
                        "target": self.target,
                        "command": self.command,
                        "value": self.value,
                        "replyto": self.replyto,
                        "cid": self.cid,
                        "by": self.by,
                        "category": self.category,
                        "sensor_type": self.sensor_type,
                        "package_type": self.package_type}}
        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)

    def tag(self, created_by=None, label=None, value=None, dataset=None, experiment=None):
        """Returns a Tag object built from this Control command and the provided parameters.

        Parameters
        ----------
        created_by : str
            A string depicting who/what created the tag being put on this Control command.
        label : str, optional
            The label being tagged on this Control command.
        value : str, optional
            An optional value for the tagged Control command.
        dataset : str
            The name of the dataset this tag is part of.
        experiment : str
            The name of the experiment this tag is part of.

        Returns
        -------
        Tag
            A new Tag object representing the tagged Control command.

        Raises
        ------
        ValueError
            Tag.dataset must have an actual value!
        ValueError
            Tag.experiment must have an actual value!
        """
        new_event = self.get_as_event_obj()
        new_tag = new_event.tag(created_by, label, value, dataset, experiment)
        return new_tag


class Heartbeat(CasasObject):
    """Represents a Heartbeat object that gets passed around.

    This is a standard Heartbeat JSON message.

    .. code-block:: JSON
        :emphasize-lines: 5

        {"channel": "",
         "site": "",
         "secret": "",
         "key": "",
         "action": "heartbeat",
         "data": {"epoch": ""
                  }
        }

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'heartbeat'.
    channel : str
        The channel that this heartbeat was published to.
    site : str
        The name of the testbed where this heartbeat was created.
    epoch : float
        A float representing the UTC epoch for when the heartbeat arrived.
    stamp : datetime.datetime
        The UTC datetime.datetime object for when the heartbeat arrived.
    stamp_local : datetime.datetime
        The local datetime.datetime object for when the heartbeat arrived.
    """

    def __init__(self, site, epoch=None, stamp=None, stamp_local=None):
        """Initialize a new Heartbeat object.

        Parameters
        ----------
        site : str
            The name of the testbed where this heartbeat was created.
        epoch : float
            A float representing the UTC epoch for when the heartbeat arrived.
        stamp : datetime.datetime
            The UTC datetime.datetime object for when the heartbeat arrived.
        stamp_local : datetime.datetime
            The local datetime.datetime object for when the heartbeat arrived.

        Raises
        ------
        CasasDatetimeException
            If `stamp` or `stamp_local` is a naive datetime.datetime object, where the tzinfo is
            not set.
        """
        super(Heartbeat, self).__init__()

        self.action = HEARTBEAT
        self.channel = self.action
        self.site = site
        self.epoch = epoch
        self.stamp = stamp
        self.stamp_local = stamp_local
        if self.stamp is not None:
            if self.stamp.tzinfo is None:
                raise CasasDatetimeException("Heartbeat.stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.stamp_local is not None:
            if self.stamp_local.tzinfo is None:
                raise CasasDatetimeException("Heartbeat.stamp_local is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        self.validate_heartbeat()
        return

    def validate_heartbeat(self):
        """Validates the Heartbeat object, and converts the epoch into a UTC stamp.
        """
        if self.epoch is not None:
            self.stamp = datetime.datetime.utcfromtimestamp(float(self.epoch))
            self.stamp = self.stamp.replace(tzinfo=pytz.utc)
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the Heartbeat fields.

        Returns
        -------
        str
            A tab delimited string of the Heartbeat fields.
        """
        mystr = "{}\t{}\t{}" \
            .format(str(self.stamp),
                    str(self.site),
                    str(self.action))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the Heartbeat.

        Parameters
        ----------
        secret : str
            The secret value that is paired with key for uploading events. If this is not provided
            it is removed from the JSON object before returning.
        key : str
            The key value that is paired with secret for uploading events. If this is not provided
            it is removed from the JSON object before returning.

        Returns
        -------
        str
            A JSON string representing the Heartbeat.
        """
        obj = {"channel": self.channel,
               "site": self.site,
               "secret": secret,
               "key": key,
               "action": self.action,
               "data": {"epoch": self.epoch}}
        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class Translation(CasasObject):
    """This represents the translation of a target for a site, with an optional valid time range.

    This is a standard Translation JSON message.

    .. code-block:: JSON
        :emphasize-lines: 2

        {"site": "",
         "action": "translation",
         "data": {"target": "",
                  "sensor_1": "",
                  "sensor_2": "",
                  "start_epoch": "",
                  "end_epoch": ""
                  }
        }

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'translation'.
    target : str
        The sensor name for this translation.
    site : str
        The testbed that this target translation is valid for.
    sensor_1 : str
        The primary translation value for this target.
    sensor_2 : str
        The secondary translation value for this target.
    start_epoch : float
        The UTC epoch for the start of the valid range. If this is None, then the translation is
        valid from the entire start of events for this site until the end value.
    start_stamp : datetime.datetime
        The UTC datetime.datetime object of the valid range.
    end_epoch : float
        The UTC epoch for the end of the valid range. If this is None, then the translation is
        valid from the start value onwards (through current live data).
    end_stamp : datetime.datetime
        The UTC datetime.datetime object of the valid range.
    """

    def __init__(self, site, target, sensor_1, sensor_2, start_epoch=None, end_epoch=None):
        """Initialize a new Translation object.

        Parameters
        ----------
        site : str
            The testbed that this target translation is valid for.
        target : str
            The sensor name for this translation.
        sensor_1 : str
            The primary translation value for this target.
        sensor_2 : str
            The secondary translation value for this target.
        start_epoch : float, optional
            The UTC epoch for the start of the valid range. If this is None, then the translation is
            valid from the entire start of events for this site until the end value.
        end_epoch : float, optional
            The UTC epoch for the end of the valid range. If this is None, then the translation is
            valid from the start value onwards (through current live data).
        """
        super(Translation, self).__init__()

        self.action = TRANSLATION
        self.site = site
        self.target = target
        self.sensor_1 = sensor_1
        self.sensor_2 = sensor_2
        self.start_epoch = start_epoch
        self.start_stamp = None
        self.end_epoch = end_epoch
        self.end_stamp = None
        self.validate_translation()
        return

    def validate_translation(self):
        """Validates the translation object and converts the epochs into UTC stamps.
        """
        if self.start_epoch is not None:
            self.start_stamp = datetime.datetime.utcfromtimestamp(float(self.start_epoch))
            self.start_stamp = self.start_stamp.replace(tzinfo=pytz.utc)
        if self.end_epoch is not None:
            self.end_stamp = datetime.datetime.utcfromtimestamp(float(self.end_epoch))
            self.end_stamp = self.end_stamp.replace(tzinfo=pytz.utc)
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the Translation fields.

        Returns
        -------
        str
            A tab delimited string of the Translation fields.
        """
        mystr = "{}\t{}\t{}\t{}\t{}\t{}" \
            .format(str(self.site),
                    str(self.target),
                    str(self.sensor_1),
                    str(self.sensor_2),
                    str(self.start_stamp),
                    str(self.end_stamp))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the Translation.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the Translation.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"target": self.target,
                        "sensor_1": self.sensor_1,
                        "sensor_2": self.sensor_2,
                        "start_epoch": self.start_epoch,
                        "end_epoch": self.end_epoch}}
        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class TranslationGroup(CasasObject):
    """This class represents a translate file, which contains many Translation entries for a
    single site.

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'translation_group'.
    site : str
        The testbed that this TranslationGroup is valid for.
    group_name : str
        The name or filename of this group.
    translations : list(Translation)
        A list of the Translation objects that make up this TranslationGroup.
    t_dict : dict({'target':list(Translation)}
        A dictionary where the keys are the targets, and the values are lists of Translation
        objects. This allows for quick lookups and validation when targets have different
        Translation objects across multiple times.
    """

    def __init__(self, site, group_name, translations=None):
        """Initialize a new TranslationGroup object.

        Parameters
        ----------
        site : str
            The testbed that this translation is valid for.
        group_name : str
            The name (or filename) of this translation group.
        translations : list, optional
            A list of translations that this group contains.
        """
        super(TranslationGroup, self).__init__()

        self.action = TRANSLATION_GRP
        self.site = site
        self.group_name = group_name
        # Check for a sentinel value, if there assign an empty list.
        if translations is not None:
            self.translations = copy.deepcopy(translations)
        else:
            self.translations = list()
        self.t_dict = dict()
        self.build_translation_structure()
        return

    def build_translation_structure(self):
        """Builds a dictionary->list structure for quick checking if a target has multiple
        translations available.
        """
        del self.t_dict
        self.t_dict = dict()
        for item in self.translations:
            if item.target not in self.t_dict:
                self.t_dict[item.target] = list()
            self.t_dict[item.target].append(item)

        self.validate_translation_group()
        return

    def validate_translation_group(self):
        """Validates the TranslationGroup Translation objects for the targets.

        A valid translation for a single target must fall within a couple variations such that
        there are no possible windows of time where the target does not have a translation value.

        * Single translation

            * Both the start and stop values *MUST* be empty, as this single translation value
              has to cover *ALL* possible times (past/present/future) that the target could
              have/might be observed.

        * Multiple translations

            * **The first translation**.  When sorted by temporal order, the start stamp of the
              first translation object *MUST* have a blank value, which means that there is no
              start limit to what this translation covers.

            * **All middle translations**.  For all translations objects where the start stamp is
              not empty, the start stamp of translation `i` must match the end stamp of
              translation `i-1`.

            * **All middle translations**.  For all translations objects where the end stamp is
              not empty, the end stamp of translation `i` must match the start stamp of
              translation `i+1`.

            * **The last translation**.  When sorted by temporal order, the end stamp of the
              last translation object *MUST* have a blank value, which means that there is no
              end limit to what this translation covers.


        Raises
        ------
        ValueError
            If the target has a single Translation where ether the start or stop times are not None.
        ValueError
            If there are multiple translations for a target and the start stamp of the first
            translation is not None.
        ValueError
            If there are multiple translations for a target and the end stamp does not match the
            start stamp of the next translation.
        ValueError
            If there are multiple translations for a target and the end stamp of the last
            translation is not None.
        """
        for target in self.t_dict:
            if len(self.t_dict[target]) == 1:
                if self.t_dict[target][0].start_epoch is not None or \
                        self.t_dict[target][0].end_epoch is not None:
                    error_msg = ("This single translation for a target has a defined valid "
                                 "time range (limiting) without another translation value taking "
                                 "over on the other side of the time range:\n{}").format(
                            self.t_dict[target][0].get_json())
                    log.error(error_msg)
                    raise ValueError(error_msg)
            elif len(self.t_dict[target]) > 1:
                # Build a list of start/stop values for the translations of this target that we
                # can then sort and check for coverage of the space.
                start_stop = list()
                for translation in self.t_dict[target]:
                    log.debug(translation.get_old_str())
                    start_stop.append(list([translation.start_epoch,
                                            translation.end_epoch,
                                            translation]))
                    if start_stop[-1][0] is not None:
                        start_stop[-1][0] = float(start_stop[-1][0])
                    if start_stop[-1][1] is not None:
                        start_stop[-1][1] = float(start_stop[-1][1])
                start_stop = sorted(start_stop, key=lambda item: item[0])
                # First, check the first entry to make sure the start_epoch is None.
                if start_stop[0][0] is not None:
                    error_msg = ("The earliest translation window does not have a start_epoch of "
                                 "None, there are possible early events with no defined "
                                 "translation.\n{}").format(start_stop[0][2].get_json())
                    log.error(error_msg)
                    raise ValueError(error_msg)
                # Second, check the last entry to make sure the end_epoch is None.
                if start_stop[-1][1] is not None:
                    error_msg = ("The latest translation window does not have a end_epoch of "
                                 "None, there are possible future events with no defined "
                                 "translation.\n{}").format(start_stop[-1][2].get_json())
                    log.error(error_msg)
                    raise ValueError(error_msg)
                # Third, check that every [i].end_epoch == [i+1].start_epoch.
                for i in range(len(start_stop) - 1):
                    if start_stop[i][1] != start_stop[i+1][0]:
                        error_msg = ("Two adjacent translation windows to not have matching "
                                     "end/start values, this means they are either overlapping or "
                                     "there is a window between them where there is no translation "
                                     "value for this target.\n{}\n{}").format(
                                start_stop[i][2].get_json(),
                                start_stop[i+1][2].get_json())
                        log.error(error_msg)
                        raise ValueError(error_msg)
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the TranslationGroup fields.

        Returns
        -------
        str
            A tab delimited string of the TranslationGroup fields.
        """
        mystr = "{}\t{}\n".format(str(self.site),
                                  str(self.group_name))
        for item in self.translations:
            mystr += "\t{}\n".format(str(item))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the TranslationGroup.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the TranslationGroup.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"group_name": self.group_name,
                        "translations": list()}}

        for item in self.translations:
            obj['data']['translations'].append(json.loads(item.get_json(secret=secret, key=key)))

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class Algorithm(CasasObject):
    """This class represents an instance of an Algorithm that is used to process data.

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'algorithm'.
    name : str
        The name of the Algorithm.
    version_major : str
        The MAJOR version of the Algorithm.  You only increment the major version of an Algorithm
        when there is an update such that a previously trained model is no longer compatible.
    version_minor : str
        The MINOR version of the Algorithm.  This is incremented for minor changes that do not
        effect the features or usable model.
    """

    def __init__(self, name, version_major, version_minor):
        """Initialize a new Algorithm object.

        Parameters
        ----------
        name : str
            The name of the Algorithm.
        version_major : str
            The MAJOR version of the algorithm.
        version_minor : str
            The MINOR version of the algorithm.
        """
        super(Algorithm, self).__init__()

        self.action = ALGORITHM
        self.name = name
        self.version_major = version_major
        self.version_minor = version_minor
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the Algorithm fields.

        Returns
        -------
        str
            A tab delimited string of the Algorithm fields.
        """
        mystr = "{}\t{}.{}".format(str(self.name),
                                   str(self.version_major),
                                   str(self.version_minor))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the Algorithm.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the Algorithm.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"name": self.name,
                        "version_major": self.version_major,
                        "version_minor": self.version_minor}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        if self.site is None:
            del obj['site']
        return json.dumps(obj)


class AlgorithmModel(CasasObject):
    """This class represents a trained model that is stored on disk with a config file.

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'algorithm_model'.
    name : str
        The human name of the AlgorithmModel.
    filename : str
        The absolute path for the AlgorithmModel file.
    configfile : str
        The path for the model config file.
    algorithm : Algorithm
        The associated Algorithm object for this AlgorithmModel.
    """

    def __init__(self, name, filename, configfile, algorithm):
        """Initialize a new AlgorithmModel object.

        Parameters
        ----------
        name : str
            The human name of the AlgorithmModel.
        filename : str
            The absolute path for the AlgorithmModel file.
        configfile : str
            The path for the model config file.
        algorithm : Algorithm
            The associated Algorithm object for this AlgorithmModel.
        """
        super(AlgorithmModel, self).__init__()

        self.action = ALG_MODEL
        self.name = name
        self.filename = filename
        self.configfile = configfile
        self.algorithm = algorithm
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the AlgorithmModel fields.

        Returns
        -------
        str
            A tab delimited string of the AlgorithmModel fields.
        """
        mystr = "{}\t{}\t{}\t{}".format(str(self.name),
                                        str(self.filename),
                                        str(self.configfile),
                                        str(self.algorithm))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the AlgorithmModel.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the AlgorithmModel.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"name": self.name,
                        "filename": self.filename,
                        "configfile": self.configfile,
                        "algorithm": {"name": self.algorithm.name,
                                      "version_major": self.algorithm.version_major,
                                      "version_minor": self.algorithm.version_minor}}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        if self.site is None:
            del obj['site']
        return json.dumps(obj)


class AlgorithmProcessor(CasasObject):
    """This class represents an instance of an AlgorithmProcessor that performs analysis of
    streaming data for a given site using the defined algorithm, algorithm_model,
    translation_group, and timestamp range. Labeled events are uploaded using the provided
    key and secret.

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'algorithm_model'.
    algorithm : Algorithm
        The associated Algorithm object for this AlgorithmProcessor.
    algorithm_model : AlgorithmModel
        The associated AlgorithmModel object for this AlgorithmProcessor.
    translation_group : TranslationGroup
        The associated TranslationGroup object for this AlgorithmProcessor.
    site : str
        The testbed that this AlgorithmProcessor is valid for.
    key : str
        The key in the key:secret pair used to upload the AlgorithmProcessor output.
    secret : str
        The secret in the key:secret pair used to upload the AlgorithmProcessor output.
    use_live_data : boolean
        A flag to identify if this AlgorithmProcessor will be listening to live data.
    use_historic_data : boolean
        A flag to identify if this AlgorithmProcessor will request a stream of historic data.
    start_stamp : datetime.datetime
        The UTC stamp for the start of the coverage by this AlgorithmProcessor. If this is
        None, then the start of this AlgorithmProcessor would be the first event for the site
        if use_historic_data is True, otherwise it would start with the first live event it
        receives.
    start_epoch : float
        The UTC epoch value representing the UTC stamp in start_stamp. If start_stamp is None, then
        this variable is also None.
    end_stamp : datetime.datetime
        The UTC stamp for the end of the coverage by this AlgorithmProcessor. If this is None,
        then this AlgorithmProcessor will continue processing data for this site forever.
    end_epoch : float
        The UTC epoch value representing the UTC stamp in end_stamp. If end_stamp is None, then
        this variable is also None.
    current_stamp : datetime.datetime
        The current UTC stamp for where the AlgorithmProcessor is currently working.
    current_epoch : float
        The UTC epoch value representing the UTC stamp in current_stamp.
    processing_historic_data: boolean
        A flag to identify if this AlgorithmProcessor is still processing historic data,
        this will be updated when it is ready to start processing live data.
    """

    def __init__(self, algorithm, algorithm_model, translation_group, site, key, secret,
                 use_live_data, use_historic_data, start_stamp=None, end_stamp=None,
                 current_stamp=None, processing_historic_data=False, is_active=True):
        """Initialize a new AlgorithmProcessor object.

        Parameters
        ----------
        algorithm : Algorithm
            The associated Algorithm object for this AlgorithmProcessor.
        algorithm_model : AlgorithmModel
            The associated AlgorithmModel object for this AlgorithmProcessor.
        translation_group : TranslationGroup
            The associated TranslationGroup object for this AlgorithmProcessor.
        site : str
            The testbed that this AlgorithmProcessor is valid for.
        key : str
            The key in the key:secret pair used to upload the AlgorithmProcessor output.
        secret : str
            The secret in the key:secret pair used to upload the AlgorithmProcessor output.
        use_live_data : boolean
            A flag to identify if this AlgorithmProcessor will be listening to live data.
        use_historic_data : boolean
            A flag to identify if this AlgorithmProcessor will request a stream of historic data.
        start_stamp : datetime.datetime, optional
            The UTC stamp for the start of the coverage by this AlgorithmProcessor. If this is
            None, then the start of this AlgorithmProcessor would be the first event for the site
            if use_historic_data is True, otherwise it would start with the first live event it
            receives.
        end_stamp : datetime.datetime, optional
            The UTC stamp for the end of the coverage by this AlgorithmProcessor. If this is None,
            then this AlgorithmProcessor will continue processing data for this site forever.
        current_stamp : datetime.datetime, optional
            The current UTC stamp for where the AlgorithmProcessor is currently working.
        processing_historic_data: boolean, optional
            A flag to identify if this AlgorithmProcessor is still processing historic data,
            this will be updated when it is ready to start processing live data.
        is_active: boolean, optional
            A flag to denote if this AlgorithmProcessor should be actively running or if it should
            not be active.

        Raises
        ------
        CasasDatetimeException
            If `start_stamp` or `end_stamp` is a naive datetime.datetime object, where the tzinfo
            is not set.
        """
        super(AlgorithmProcessor, self).__init__()

        self.action = ALG_PROCESSOR
        self.algorithm = algorithm
        self.algorithm_model = algorithm_model
        self.translation_group = translation_group
        self.site = site
        self.upload_key = key
        self.upload_secret = secret
        self.use_live_data = use_live_data
        self.use_historic_data = use_historic_data
        self.start_stamp = start_stamp
        self.start_epoch = make_epoch(self.start_stamp)
        self.end_stamp = end_stamp
        self.end_epoch = make_epoch(self.end_stamp)
        self.current_stamp = current_stamp
        self.current_epoch = make_epoch(current_stamp)
        self.processing_historic_data = processing_historic_data
        self.is_active = is_active
        if self.start_stamp is not None:
            if self.start_stamp.tzinfo is None:
                raise CasasDatetimeException("AlgorithmProcessor.start_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.end_stamp is not None:
            if self.end_stamp.tzinfo is None:
                raise CasasDatetimeException("AlgorithmProcessor.end_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the AlgorithmProcessor fields.

        Returns
        -------
        str
            A tab delimited string of the AlgorithmProcessor fields.
        """
        mystr = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(str(self.site),
                                                          str(self.use_live_data),
                                                          str(self.use_historic_data),
                                                          str(self.start_stamp),
                                                          str(self.end_stamp),
                                                          str(self.current_stamp),
                                                          str(self.processing_historic_data),
                                                          str(self.is_active))
        mystr += "{}\n{}\n{}".format(str(self.algorithm),
                                     str(self.algorithm_model),
                                     str(self.translation_group))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the AlgorithmProcessor.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the AlgorithmProcessor.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"algorithm": json.loads(self.algorithm.get_json()),
                        "algorithm_model": json.loads(self.algorithm_model.get_json()),
                        "translation_group": json.loads(self.translation_group.get_json()),
                        "upload_key": self.upload_key,
                        "upload_secret": self.upload_secret,
                        "use_live_data": self.use_live_data,
                        "use_historic_data": self.use_historic_data,
                        "start_epoch": self.start_epoch,
                        "end_epoch": self.end_epoch,
                        "current_epoch": self.current_epoch,
                        "processing_historic_data": self.processing_historic_data,
                        "is_active": self.is_active}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class AlgorithmProcessorRequest(CasasObject):
    """This class represents a query request to get a list of AlgorithmProcessor objects that
    a program will be in charge of handling.

    Attributes
    ----------
    action : str
        The defined action for the json, this object is 'algorithm_processor_request'.
    algorithm_name : str
        An Algorithm name to search for.
    version_major : str
        An Algorithm major version value to search for.
    version_minor : str
        An Algorithm minor version value to search for.
    algorithm_model_name : str
        The AlgorithmModel name to use in our search.
    """
    def __init__(self, algorithm_name, version_major, version_minor, algorithm_model_name):
        """Initialize a new AlgorithmProcessorRequest object.

        Parameters
        ----------
        algorithm_name : str
            An Algorithm name to search for.
        version_major : str
            An Algorithm major version value to search for.
        version_minor : str
            An Algorithm minor version value to search for.
        algorithm_model_name : str
            The AlgorithmModel name to use in our search.
        """
        super(AlgorithmProcessorRequest, self).__init__()

        self.action = ALG_PROC_REQUEST
        self.algorithm_name = algorithm_name
        self.version_major = version_major
        self.version_minor = version_minor
        self.algorithm_model_name = algorithm_model_name
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the AlgorithmProcessorRequest fields.

        Returns
        -------
        str
            A tab delimited string of the AlgorithmProcessorRequest fields.
        """
        mystr = "{}\t{}\t{}\t{}".format(str(self.algorithm_name),
                                        str(self.version_major),
                                        str(self.version_minor),
                                        str(self.algorithm_model_name))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the AlgorithmProcessorRequest.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the AlgorithmProcessorRequest.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"algorithm_name": self.algorithm_name,
                        "version_major": self.version_major,
                        "version_minor": self.version_minor,
                        "algorithm_model_name": self.algorithm_model_name}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class AlgorithmProcessorUpdate(CasasObject):
    def __init__(self, algorithm_processor, new_algorithm=None, new_algorithm_model=None,
                 new_translation_group=None, new_upload_key=None, new_upload_secret=None,
                 new_use_live_data=None, new_use_historic_data=None, new_start_stamp=None,
                 new_end_stamp=None, new_current_stamp=None, new_processing_historic_data=None,
                 new_is_active=None):
        """Initialize a new AlgorithmProcessor object.

        Parameters
        ----------
        algorithm_processor : AlgorithmProcessor
            The AlgorithmProcessor object to update in the database.
        new_algorithm : Algorithm, optional
            The associated Algorithm object for this AlgorithmProcessor.
        new_algorithm_model : AlgorithmModel, optional
            The associated AlgorithmModel object for this AlgorithmProcessor.
        new_translation_group : TranslationGroup, optional
            The associated TranslationGroup object for this AlgorithmProcessor.
        new_upload_key : str, optional
            The key in the key:secret pair used to upload the AlgorithmProcessor output.
        new_upload_secret : str, optional
            The secret in the key:secret pair used to upload the AlgorithmProcessor output.
        new_use_live_data : boolean, optional
            A flag to identify if this AlgorithmProcessor will be listening to live data.
        new_use_historic_data : boolean, optional
            A flag to identify if this AlgorithmProcessor will request a stream of historic data.
        new_start_stamp : datetime.datetime, optional
            The UTC stamp for the start of the coverage by this AlgorithmProcessor. If this is
            None, then the start of this AlgorithmProcessor would be the first event for the site
            if use_historic_data is True, otherwise it would start with the first live event it
            receives.
        new_end_stamp : datetime.datetime, optional
            The UTC stamp for the end of the coverage by this AlgorithmProcessor. If this is None,
            then this AlgorithmProcessor will continue processing data for this site forever.
        new_current_stamp : datetime.datetime, optional
            The current UTC stamp for where the AlgorithmProcessor is currently working.
        new_processing_historic_data: boolean, optional
            A flag to identify if this AlgorithmProcessor is still processing historic data,
            this will be updated when it is ready to start processing live data.
        new_is_active: boolean, optional
            A flag to denote if this AlgorithmProcessor should be actively running or if it should
            not be active.

        Raises
        ------
        CasasDatetimeException
            If `new_start_stamp`, `new_end_stamp`, or `new_current_stamp` is a naive
            datetime.datetime object, where the tzinfo is not set.
        """
        super(AlgorithmProcessorUpdate, self).__init__()

        self.action = ALG_PROC_UPDATE
        self.algorithm_processor = algorithm_processor
        self.site = algorithm_processor.site
        self.new_algorithm = new_algorithm
        self.new_algorithm_model = new_algorithm_model
        self.new_translation_group = new_translation_group
        self.new_upload_key = new_upload_key
        self.new_upload_secret = new_upload_secret
        self.new_use_live_data = new_use_live_data
        self.new_use_historic_data = new_use_historic_data
        self.new_start_stamp = new_start_stamp
        self.new_start_epoch = make_epoch(self.new_start_stamp)
        self.new_end_stamp = new_end_stamp
        self.new_end_epoch = make_epoch(new_end_stamp)
        self.new_current_stamp = new_current_stamp
        self.new_current_epoch = make_epoch(new_current_stamp)
        self.new_processing_historic_data = new_processing_historic_data
        self.new_is_active = new_is_active
        if self.new_start_stamp is not None:
            if self.new_start_stamp.tzinfo is None:
                raise CasasDatetimeException("AlgorithmProcessorUpdate.new_start_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.new_end_stamp is not None:
            if self.new_end_stamp.tzinfo is None:
                raise CasasDatetimeException("AlgorithmProcessorUpdate.new_end_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.new_current_stamp is not None:
            if self.new_current_stamp.tzinfo is None:
                raise CasasDatetimeException("AlgorithmProcessorUpdate.new_current_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        mystr = self.algorithm_processor.get_old_str()
        return mystr

    def get_json(self, secret=None, key=None):
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"algorithm_processor": json.loads(self.algorithm_processor.get_json())}}
        if self.new_algorithm is not None:
            obj['data']['algorithm'] = json.loads(self.new_algorithm.get_json())
        if self.new_algorithm_model is not None:
            obj['data']['algorithm_model'] = json.loads(self.new_algorithm_model.get_json())
        if self.new_translation_group is not None:
            obj['data']['translation_group'] = json.loads(self.new_translation_group.get_json())
        if self.new_upload_key is not None:
            obj['data']['upload_key'] = self.new_upload_key
        if self.new_upload_secret is not None:
            obj['data']['upload_secret'] = self.new_upload_secret
        if self.new_use_live_data is not None:
            obj['data']['use_live_data'] = self.new_use_live_data
        if self.new_use_historic_data is not None:
            obj['data']['use_historic_data'] = self.new_use_historic_data
        if self.new_start_epoch is not None:
            obj['data']['start_epoch'] = self.new_start_epoch
        if self.new_end_epoch is not None:
            obj['data']['end_epoch'] = self.new_end_epoch
        if self.new_current_epoch is not None:
            obj['data']['current_epoch'] = self.new_current_epoch
        if self.new_processing_historic_data is not None:
            obj['data']['processing_historic_data'] = self.new_processing_historic_data
        if self.new_is_active is not None:
            obj['data']['is_active'] = self.new_is_active

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class CilBaseline(CasasObject):
    def __init__(self, site, is_ready, start_stamp, end_stamp):
        """Initialize a new CilBaseline object.

        Parameters
        ----------
        site : str
            The testbed that this is baseline is valid for.
        is_ready : boolean
            A flag to denote if this baseline is ready to use.
        start_stamp : datetime.datetime
            The UTC stamp for the start of the window to use in calculating the baseline.
        end_stamp : datetime.datetime
            The UTC stamp for the end of the window to use in calculating the baseline.

        Raises
        ------
        CasasDatetimeException
            If `start_stamp` or `end_stamp` is a naive datetime.datetime object, where the tzinfo
            is not set.
        """
        super(CilBaseline, self).__init__()

        self.action = CIL_BASE
        self.site = site
        self.is_ready = is_ready
        self.start_stamp = start_stamp
        self.start_epoch = make_epoch(self.start_stamp)
        self.end_stamp = end_stamp
        self.end_epoch = make_epoch(self.end_stamp)
        if self.start_stamp is not None:
            if self.start_stamp.tzinfo is None:
                raise CasasDatetimeException("CilBaseline.start_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.end_stamp is not None:
            if self.end_stamp.tzinfo is None:
                raise CasasDatetimeException("CilBaseline.end_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the CilBaseline fields.

        Returns
        -------
        str
            A tab delimited string of the CilBaseline fields.
        """
        mystr = "{}\t{}\t{}\t{}".format(str(self.site),
                                        str(self.is_ready),
                                        str(self.start_stamp),
                                        str(self.end_stamp))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the CilBaseline.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the CilBaseline.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"is_ready": self.is_ready,
                        "start_epoch": self.start_epoch,
                        "end_epoch": self.end_epoch}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class CilMetric(CasasObject):
    def __init__(self, name):
        """Initialize a new CilMetric object.

        Parameters
        ----------
        name : str
            The name of the CilMetric.
        """
        super(CilMetric, self).__init__()

        self.action = CIL_METRIC
        self.name = name
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the CilMetric fields.

        Returns
        -------
        str
            A tab delimited string of the CilMetric fields.
        """
        mystr = "{}".format(str(self.name))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the CilMetric.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the CilMetric.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"name": self.name}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        if self.site is None:
            del obj['site']
        return json.dumps(obj)


class CilBaselineMetric(CasasObject):
    def __init__(self, baseline, metric, value_zero_five_std, value_one_std, value_one_five_std):
        """Initialize a new CilBaselineMetric object.

        Parameters
        ----------
        baseline : CilBaseline
            The CilBaseline this CilBaselineMetric is part of.
        metric : CilMetric
            The CilMetric this CilBaselineMetric is linked to.
        value_zero_five_std : float
            The standard deviation of the baseline metric multiplied by 0.5.
        value_one_std : float
            The standard deviation of the baseline metric.
        value_one_five_std : float
            The standard deviation of the baseline metric multiplied by 1.5.
        """
        super(CilBaselineMetric, self).__init__()

        self.action = CIL_BASE_METRIC
        self.baseline = baseline
        self.metric = metric
        self.value_zero_five_std = value_zero_five_std
        self.value_one_std = value_one_std
        self.value_one_five_std = value_one_five_std
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the CilBaselineMetric fields.

        Returns
        -------
        str
            A tab delimited string of the CilBaselineMetric fields.
        """
        mystr = "{}\t{}\t{}\t{}\t{}".format(str(self.baseline),
                                            str(self.metric),
                                            str(self.value_zero_five_std),
                                            str(self.value_one_std),
                                            str(self.value_one_five_std))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the CilBaselineMetric.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the CilBaselineMetric.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"baseline": json.loads(self.baseline.get_json()),
                        "metric": json.loads(self.metric.get_json()),
                        "0.5_std": self.value_zero_five_std,
                        "1.0_std": self.value_one_std,
                        "1.5_std": self.value_one_five_std}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        if self.site is None:
            del obj['site']
        return json.dumps(obj)


class CilData(CasasObject):
    def __init__(self, site, metric, value, stamp):
        """Initialize a new CilData object.

        Parameters
        ----------
        site : str
            The testbed that this CilData is valid for.
        metric : CilMetric
            The CilMetric that this data is for.
        value : float
            The calculated data value for this metric.
        stamp : datetime.datetime
            The UTC stamp that this data is for.

        Raises
        ------
        CasasDatetimeException
            If `stamp` is a naive datetime.datetime object, where the tzinfo is not set.
        """
        super(CilData, self).__init__()

        self.action = CIL_DATA
        self.site = site
        self.metric = metric
        self.value = float(value)
        self.stamp = stamp
        self.epoch = make_epoch(self.stamp)
        if self.stamp is not None:
            if self.stamp.tzinfo is None:
                raise CasasDatetimeException("CilData.stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the CilData fields.

        Returns
        -------
        str
            A tab delimited string of the CilData fields.
        """
        mystr = "{}\t{}\t{}\t{}".format(str(self.site),
                                        str(self.metric),
                                        str(self.value),
                                        str(self.stamp))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the CilData.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the CilData.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"metric": json.loads(self.metric.get_json()),
                        "value": self.value,
                        "epoch": self.epoch}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class RequestEvents(CasasObject):
    def __init__(self, site, start_stamp, end_stamp, sensor_types=None):
        """Initialize a new RequestEvents object.

        Parameters
        ----------
        site : str
            The testbed that this RequestEvents object is for.
        start_stamp : datetime.datetime
            The UTC timestamp for the start of the requested window of data.
        end_stamp : datetime.datetime
            The UTC timestamp for the end of the requested window of data.
        sensor_types : list, optional
            An optional list of sensor types to limit our request to.

        Raises
        ------
        CasasDatetimeException
            If `start_stamp` or `end_stamp` is a naive datetime.datetime object, where the tzinfo
            is not set.
        """
        super(RequestEvents, self).__init__()

        self.action = REQUEST_EVENTS
        self.site = site
        self.start_stamp = start_stamp
        self.start_epoch = make_epoch(self.start_stamp)
        self.end_stamp = end_stamp
        self.end_epoch = make_epoch(self.end_stamp)
        self.sensor_types = sensor_types
        td_max = datetime.timedelta(hours=25)
        if self.start_stamp > self.end_stamp:
            raise ValueError("RequestEvents: start_stamp MUST be before end_stamp.")
        if abs(self.end_stamp - self.start_stamp) > td_max:
            raise ValueError("RequestEvents: data request is limited to a 24 hour window.")
        if self.start_stamp is not None:
            if self.start_stamp.tzinfo is None:
                raise CasasDatetimeException("RequestEvents.start_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.end_stamp is not None:
            if self.end_stamp.tzinfo is None:
                raise CasasDatetimeException("RequestEvents.end_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the RequestEvents fields.

        Returns
        -------
        str
            A tab delimited string of the RequestEvents fields.
        """
        mystr = "{}\t{}\t{}\t{}".format(str(self.site),
                                        str(self.start_stamp),
                                        str(self.end_stamp),
                                        str(self.sensor_types))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the RequestEvents.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the RequestEvents.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"start_epoch": self.start_epoch,
                        "end_epoch": self.end_epoch,
                        "sensor_types": self.sensor_types}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class RequestDataset(CasasObject):
    def __init__(self, site, start_stamp, end_stamp, experiment, dataset, sensor_types=None):
        """Initialize a new RequestDataset object.

        Parameters
        ----------
        site : str
            The testbed that this RequestDataset object is for.
        start_stamp : datetime.datetime
            The UTC timestamp for the start of the requested window of data.
        end_stamp : datetime.datetime
            The UTC timestamp for the end of the requested window of data.
        experiment : str
            The name of the experiment we wish to get data from.
        dataset : str
            The name of the dataset we wish to get data from.
        sensor_types : list, optional
            An optional list of sensor types to limit our request to.

        Raises
        ------
        CasasDatetimeException
            If `start_stamp` or `end_stamp` is a naive datetime.datetime object, where the tzinfo
            is not set.
        """
        super(RequestDataset, self).__init__()

        self.action = REQUEST_DATASET
        self.site = site
        self.start_stamp = start_stamp
        self.start_epoch = make_epoch(self.start_stamp)
        self.end_stamp = end_stamp
        self.end_epoch = make_epoch(self.end_stamp)
        self.experiment = experiment
        self.dataset = dataset
        self.sensor_types = sensor_types
        td_max = datetime.timedelta(hours=25)
        if self.start_stamp > self.end_stamp:
            raise ValueError("RequestDataset: start_stamp MUST be before end_stamp.")
        if abs(self.end_stamp - self.start_stamp) > td_max:
            raise ValueError("RequestDataset: data request is limited to a 24 hour window.")
        if self.start_stamp is not None:
            if self.start_stamp.tzinfo is None:
                raise CasasDatetimeException("RequestDataset.start_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        if self.end_stamp is not None:
            if self.end_stamp.tzinfo is None:
                raise CasasDatetimeException("RequestDataset.end_stamp is naive, "
                                             "datetime.datetime.tzinfo is not set!")
        return

    def __str__(self):
        return self.get_old_str()

    def get_old_str(self):
        """Returns a tab delimited string of the RequestDataset fields.

        Returns
        -------
        str
            A tab delimited string of the RequestDataset fields.
        """
        mystr = "{}\t{}\t{}\t{}\t{}\t{}".format(str(self.site),
                                                str(self.start_stamp),
                                                str(self.end_stamp),
                                                str(self.experiment),
                                                str(self.dataset),
                                                str(self.sensor_types))
        return mystr

    def get_json(self, secret=None, key=None):
        """Returns a JSON string representing the RequestDataset.

        Parameters
        ----------
        secret : str, optional
            The secret in the key:secret required for uploading data.
        key : str, optional
            The key in the key:secret required for uploading data.

        Returns
        -------
        str
            A JSON string representing the RequestDataset.
        """
        obj = {"site": self.site,
               "action": self.action,
               "secret": secret,
               "key": key,
               "data": {"start_epoch": self.start_epoch,
                        "end_epoch": self.end_epoch,
                        "experiment": self.experiment,
                        "dataset": self.dataset,
                        "sensor_types": self.sensor_types}}

        if secret is None:
            del obj['secret']
        if key is None:
            del obj['key']
        return json.dumps(obj)


class AiqObject(CasasObject):
    def __init__(self):
        super().__init__()
        self.obj_type = 'BASE_CLASS'
        return

    def __str__(self):
        return self.get_json_str()

    def get_json(self, key=None, secret=None):
        return self.get_json_str()

    def get_json_obj(self):
        raise ValueError('This object did not implement get_json_obj().')

    def get_json_str(self) -> str:
        return json.dumps(self.get_json_obj())


class RequestModel(AiqObject):
    def __init__(self, aiq_username: str, aiq_secret: str, model_name: str, organization: str,
                 description: str = None):
        super().__init__()
        self.obj_type = REQ_MODEL
        self.aiq_username = aiq_username
        self.aiq_secret = aiq_secret
        self.model_name = model_name
        self.organization = organization
        self.description = description
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'aiq_username': self.aiq_username,
               'aiq_secret': self.aiq_secret,
               'model_name': self.model_name,
               'organization': self.organization,
               'description': self.description}
        return copy.deepcopy(obj)


class RequestState(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = REQ_STATE
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class Model(AiqObject):
    def __init__(self, model_name: str, organization: str, aiq_username: str, aiq_secret: str,
                 description: str = None):
        super().__init__()
        self.obj_type = MODEL
        self.model_name = model_name
        self.organization = organization
        self.aiq_username = aiq_username
        self.aiq_secret = aiq_secret
        self.description = description
        self.model_id = None
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'model_name': self.model_name,
               'organization': self.organization,
               'description': self.description,
               'aiq_username': self.aiq_username,
               'aiq_secret': self.aiq_secret}
        return copy.deepcopy(obj)


class RequestExperiment(AiqObject):
    def __init__(self, model: Model, novelty: int, novelty_visibility: int, client_rpc_queue: str,
                 git_version: str, experiment_type: str, seed: int = None,
                 domain_dict: dict = None, epoch: float = None, no_testing: bool = False,
                 description: str = None):
        super().__init__()
        self.obj_type = REQ_EXPERIMENT
        self.model = copy.deepcopy(model)
        self.novelty = novelty
        self.novelty_visibility = novelty_visibility
        self.client_rpc_queue = client_rpc_queue
        self.git_version = git_version
        if experiment_type not in VALID_EXPERIMENT_TYPES:
            raise AiqDataException('INVALID experiment type requested.')
        self.experiment_type = experiment_type
        self.seed = seed
        if domain_dict is None:
            domain_dict = dict()
        for domain in VALID_DOMAINS:
            if domain not in domain_dict:
                domain_dict[domain] = False
        self.domain_dict = copy.deepcopy(domain_dict)
        self.epoch = epoch
        if self.epoch is None:
            self.epoch = time.time()
        self.no_testing = no_testing

        # Verify that we have at least one domain chosen.
        true_domain = False
        for domain in self.domain_dict:
            if self.domain_dict[domain]:
                true_domain = True
        if not true_domain:
            raise AiqDataException('An experiment MUST have at least one domain selected.')
        self.description = description
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'model': self.model.get_json_str(),
               'novelty': self.novelty,
               'novelty_visibility': self.novelty_visibility,
               'client_rpc_queue': self.client_rpc_queue,
               'git_version': self.git_version,
               'seed': self.seed,
               'domain_dict': self.domain_dict,
               'epoch': self.epoch,
               'no_testing': self.no_testing,
               'experiment_type': self.experiment_type,
               'description': self.description}
        return copy.deepcopy(obj)


class RequestExperimentTrials(RequestExperiment):
    def __init__(self, model: Model, experiment_secret: str, client_rpc_queue: str,
                 just_one_trial: bool = False, epoch: float = None, domain_dict: dict = None):
        super().__init__(model=model,
                         novelty=0,
                         novelty_visibility=0,
                         client_rpc_queue=client_rpc_queue,
                         git_version=__version__,
                         experiment_type=TYPE_EXPERIMENT_SAIL_ON,
                         domain_dict=domain_dict,
                         epoch=epoch)
        self.obj_type = REQ_EXP_TRIALS
        self.model = copy.deepcopy(model)
        self.experiment_secret = experiment_secret
        self.client_rpc_queue = client_rpc_queue
        self.just_one_trial = just_one_trial
        self.epoch = epoch
        if self.epoch is None:
            self.epoch = time.time()
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'model': self.model.get_json_str(),
               'experiment_secret': self.experiment_secret,
               'client_rpc_queue': self.client_rpc_queue,
               'just_one_trial': self.just_one_trial,
               'domain_dict': self.domain_dict,
               'epoch': self.epoch}
        return copy.deepcopy(obj)


class ExperimentResponse(AiqObject):
    def __init__(self, server_rpc_queue: str, experiment_secret: str, model_experiment_id: int,
                 experiment_timeout: float):
        super().__init__()
        self.obj_type = EXPERIMENT_RESP
        self.server_rpc_queue = server_rpc_queue
        self.experiment_secret = experiment_secret
        self.model_experiment_id = model_experiment_id
        self.experiment_timeout = experiment_timeout
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'server_rpc_queue': self.server_rpc_queue,
               'experiment_secret': self.experiment_secret,
               'model_experiment_id': self.model_experiment_id,
               'experiment_timeout': self.experiment_timeout}
        return copy.deepcopy(obj)


class ExperimentStart(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = EXPERIMENT_START
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class ExperimentEnd(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = EXPERIMENT_END
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class ExperimentException(AiqObject):
    def __init__(self, message: str):
        super().__init__()
        self.obj_type = EXPERIMENT_EXCEPTION
        self.message = message
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'message': self.message}
        return copy.deepcopy(obj)


class BenchmarkRequest(AiqObject):
    def __init__(self, benchmark_script: str):
        super().__init__()
        self.obj_type = BENCHMARK_REQ
        self.benchmark_script = benchmark_script
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'benchmark_script': self.benchmark_script}
        return copy.deepcopy(obj)


class BenchmarkData(AiqObject):
    def __init__(self, benchmark_data: dict):
        super().__init__()
        self.obj_type = BENCHMARK_DATA
        self.benchmark_data = copy.deepcopy(benchmark_data)
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'benchmark_data': self.benchmark_data}
        return copy.deepcopy(obj)


class BenchmarkAck(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = BENCHMARK_ACK
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class NoveltyStart(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = NOVELTY_START
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class NoveltyEnd(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = NOVELTY_END
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TrialStart(AiqObject):
    def __init__(self, trial_number: int = 0, total_trials: int = 0, message: str = None,
                 novelty_description: dict = None):
        super().__init__()
        self.obj_type = TRIAL_START
        self.trial_number = trial_number
        self.total_trials = total_trials
        self.message = message
        self.novelty_description = copy.deepcopy(novelty_description)
        if self.novelty_description is None:
            self.novelty_description = dict()
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'trial_number': self.trial_number,
               'total_trials': self.total_trials,
               'message': self.message,
               'novelty_description': self.novelty_description}
        return copy.deepcopy(obj)


class TrialEnd(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TRIAL_END
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TrainingStart(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TRAINING_START
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TrainingActive(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TRAINING_ACTIVE
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TrainingEnd(AiqObject):
    def __init__(self, message: str = None):
        super().__init__()
        self.obj_type = TRAINING_END
        self.message = message
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'message': self.message}
        return copy.deepcopy(obj)


class TrainingModelEnd(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TRAINING_MODEL_END
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TrainingEndEarly(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TRAINING_END_EARLY
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TrainingEpisodeStart(AiqObject):
    def __init__(self, episode_number: int = 0, total_episodes: int = 0):
        super().__init__()
        self.obj_type = TRAIN_EPISODE_START
        self.episode_number = episode_number
        self.total_episodes = total_episodes
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'episode_number': self.episode_number,
               'total_episodes': self.total_episodes}
        return copy.deepcopy(obj)


class TrainingEpisodeActive(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TRAIN_EPISODE_ACTIVE
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class EpisodeEnd(AiqObject):
    def __init__(self, performance: float, feedback: dict = None):
        super().__init__()
        self.obj_type = EPISODE_END
        self.performance = performance
        self.feedback = copy.deepcopy(feedback)
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'performance': self.performance,
               'feedback': self.feedback}
        return copy.deepcopy(obj)


class BasicData(AiqObject):
    def __init__(self, feature_vector: dict, feature_label: dict):
        super().__init__()
        self.obj_type = BASIC_DATA
        self.feature_vector = feature_vector
        self.feature_label = dict()
        valid_label = False
        if 'action' in feature_label:
            self.feature_label['action'] = feature_label['action']
            if isinstance(self.feature_label['action'], str):
                valid_label = True
        if not valid_label:
            raise AiqDataException('A feature label must be a dict({"action": str(value)})!')
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'feature_vector': self.feature_vector,
               'feature_label': self.feature_label}
        return copy.deepcopy(obj)


class BasicDataPrediction(AiqObject):
    def __init__(self, label_prediction: dict = None):
        super().__init__()
        self.obj_type = BASIC_DATA_PREDICTION
        self.label_prediction = dict()
        valid_label = False
        if 'action' in label_prediction:
            self.label_prediction['action'] = label_prediction['action']
            if isinstance(self.label_prediction['action'], str):
                valid_label = True
        if not valid_label:
            raise AiqDataException('A label prediction must be a dict({"action": str(value)})!')
        self.utc_remote_epoch_received = None
        self.utc_remote_epoch_sent = None
        self.end_early = False
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'label_prediction': self.label_prediction}
        return copy.deepcopy(obj)


class BasicDataAck(AiqObject):
    def __init__(self, performance: float = None, feedback: dict = None):
        super().__init__()
        self.obj_type = BASIC_DATA_ACK
        self.performance = performance
        self.feedback = copy.deepcopy(feedback)
        if self.feedback is None:
            self.feedback = dict()
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'performance': self.performance,
               'feedback': self.feedback}
        return copy.deepcopy(obj)


class BasicEpisodeNovelty(AiqObject):
    def __init__(self, novelty_probability: float = None, novelty_threshold: float = None,
                 novelty: int = None, novelty_characterization: dict = None):
        super().__init__()
        self.obj_type = BASIC_EPISODE_NOVELTY
        self.novelty_probability = novelty_probability
        self.novelty_threshold = novelty_threshold
        self.novelty = novelty
        self.novelty_characterization = copy.deepcopy(novelty_characterization)
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'novelty_probability': self.novelty_probability,
               'novelty_threshold': self.novelty_threshold,
               'novelty': self.novelty,
               'novelty_characterization': self.novelty_characterization}
        return copy.deepcopy(obj)


class TrainingEpisodeEnd(EpisodeEnd):
    def __init__(self, performance: float = None, feedback: dict = None):
        super().__init__(performance=performance,
                         feedback=feedback)
        self.obj_type = TRAIN_EPISODE_END
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'performance': self.performance,
               'feedback': self.feedback}
        return copy.deepcopy(obj)


class RequestData(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = REQ_DATA
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class RequestTrainingData(RequestData):
    def __init__(self, model_experiment_id: str, secret: str):
        super().__init__()
        self.obj_type = REQ_TRAIN_DATA
        self.model_experiment_id = model_experiment_id
        self.secret = secret
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'model_experiment_id': self.model_experiment_id,
               'secret': self.secret}
        return copy.deepcopy(obj)


class TrainingData(AiqObject):
    def __init__(self, secret: str, feature_vector: dict, feature_label: dict,
                 utc_remote_epoch_received: float = None, utc_remote_epoch_sent: float = None):
        super().__init__()
        self.obj_type = TRAINING_DATA
        self.secret = secret
        self.feature_vector = copy.deepcopy(feature_vector)
        self.feature_label = dict()
        valid_label = False
        if 'action' in feature_label:
            self.feature_label['action'] = feature_label['action']
            if isinstance(self.feature_label['action'], str):
                valid_label = True
        if not valid_label:
            raise AiqDataException('A feature label must be a dict({"action": str(value)})!')
        self.utc_remote_epoch_received = utc_remote_epoch_received
        if self.utc_remote_epoch_received is None:
            self.utc_remote_epoch_received = time.time()
        self.utc_remote_epoch_sent = utc_remote_epoch_sent
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'secret': self.secret,
               'feature_vector': self.feature_vector,
               'feature_label': self.feature_label,
               'utc_remote_epoch_received': self.utc_remote_epoch_received,
               'utc_remote_epoch_sent': time.time()}
        return copy.deepcopy(obj)


class TrainingDataPrediction(BasicDataPrediction):
    def __init__(self, secret: str, utc_remote_epoch_received: float = None,
                 utc_remote_epoch_sent: float = None, label_prediction: dict = None,
                 end_early: bool = False):
        super().__init__(label_prediction=label_prediction)
        self.obj_type = TRAIN_DATA_PRED
        self.secret = secret
        self.utc_remote_epoch_received = utc_remote_epoch_received
        if self.utc_remote_epoch_received is None:
            self.utc_remote_epoch_received = time.time()
        self.utc_remote_epoch_sent = utc_remote_epoch_sent
        self.label_prediction = dict()
        valid_label = False
        if 'action' in label_prediction:
            self.label_prediction['action'] = label_prediction['action']
            if isinstance(self.label_prediction['action'], str):
                valid_label = True
        if not valid_label:
            raise AiqDataException('A label prediction must be a dict({"action": str(value)})!')
        self.end_early = end_early
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'secret': self.secret,
               'utc_remote_epoch_received': self.utc_remote_epoch_received,
               'utc_remote_epoch_sent': time.time(),
               'label_prediction': self.label_prediction,
               'end_early': self.end_early}
        return copy.deepcopy(obj)


class TrainingDataAck(AiqObject):
    def __init__(self, secret: str, performance: float = None, feedback: dict = None):
        super().__init__()
        self.obj_type = TRAIN_DATA_ACK
        self.secret = secret
        self.performance = performance
        self.feedback = copy.deepcopy(feedback)
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'secret': self.secret,
               'performance': self.performance,
               'feedback': self.feedback}
        return copy.deepcopy(obj)


class TrainingEpisodeNovelty(BasicEpisodeNovelty):
    def __init__(self, novelty_probability: float = None, novelty_threshold: float = None,
                 novelty: int = None, novelty_characterization: dict = None):
        super().__init__(novelty_probability=novelty_probability,
                         novelty_threshold=novelty_threshold,
                         novelty=novelty,
                         novelty_characterization=novelty_characterization)
        self.obj_type = TRAIN_EPISODE_NOVELTY
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'novelty_probability': self.novelty_probability,
               'novelty_threshold': self.novelty_threshold,
               'novelty': self.novelty,
               'novelty_characterization': self.novelty_characterization}
        return copy.deepcopy(obj)


class TrainingEpisodeNoveltyAck(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TRAIN_EPISODE_NOVELTY_ACK
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TestingStart(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TESTING_START
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TestingActive(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TESTING_ACTIVE
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TestingEnd(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TESTING_END
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TestingEpisodeStart(AiqObject):
    def __init__(self, episode_number: int = 0, total_episodes: int = 0):
        super().__init__()
        self.obj_type = TEST_EPISODE_START
        self.episode_number = episode_number
        self.total_episodes = total_episodes
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'episode_number': self.episode_number,
               'total_episodes': self.total_episodes}
        return copy.deepcopy(obj)


class TestingEpisodeActive(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TEST_EPISODE_ACTIVE
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class TestingEpisodeEnd(EpisodeEnd):
    def __init__(self, performance: float = None, feedback: dict = None):
        super().__init__(performance=performance,
                         feedback=feedback)
        self.obj_type = TEST_EPISODE_END
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'performance': self.performance,
               'feedback': self.feedback}
        return copy.deepcopy(obj)


class RequestTestingData(RequestData):
    def __init__(self, model_experiment_id: str, secret: str):
        super().__init__()
        self.obj_type = REQ_TEST_DATA
        self.model_experiment_id = model_experiment_id
        self.secret = secret
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'model_experiment_id': self.model_experiment_id,
               'secret': self.secret}
        return copy.deepcopy(obj)


class TestingData(AiqObject):
    def __init__(self, secret: str, feature_vector: dict, utc_remote_epoch_received: float = None,
                 utc_remote_epoch_sent: float = None, novelty_indicator: bool = None):
        super().__init__()
        self.obj_type = TESTING_DATA
        self.secret = secret
        self.feature_vector = copy.deepcopy(feature_vector)
        self.utc_remote_epoch_received = utc_remote_epoch_received
        if self.utc_remote_epoch_received is None:
            self.utc_remote_epoch_received = time.time()
        self.utc_remote_epoch_sent = utc_remote_epoch_sent
        self.novelty_indicator = novelty_indicator
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'secret': self.secret,
               'feature_vector': self.feature_vector,
               'utc_remote_epoch_received': self.utc_remote_epoch_received,
               'utc_remote_epoch_sent': time.time(),
               'novelty_indicator': self.novelty_indicator}
        return copy.deepcopy(obj)


class TestingDataPrediction(BasicDataPrediction):
    def __init__(self, secret: str, utc_remote_epoch_received: float = None,
                 utc_remote_epoch_sent: float = None, label_prediction: dict = None,
                 end_early: bool = False):
        super().__init__(label_prediction=label_prediction)
        self.obj_type = TEST_DATA_PRED
        self.secret = secret
        self.utc_remote_epoch_received = utc_remote_epoch_received
        if self.utc_remote_epoch_received is None:
            self.utc_remote_epoch_received = time.time()
        self.utc_remote_epoch_sent = utc_remote_epoch_sent
        self.label_prediction = dict()
        valid_label = False
        if 'action' in label_prediction:
            self.label_prediction['action'] = label_prediction['action']
            if isinstance(self.label_prediction['action'], str):
                valid_label = True
        if not valid_label:
            raise AiqDataException('A label prediction must be a dict({"action": str(value)})!')
        self.end_early = end_early
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'secret': self.secret,
               'utc_remote_epoch_received': self.utc_remote_epoch_received,
               'utc_remote_epoch_sent': time.time(),
               'label_prediction': self.label_prediction,
               'end_early': self.end_early}
        return copy.deepcopy(obj)


class TestingDataAck(AiqObject):
    def __init__(self, secret: str, performance: float = None, feedback: dict = None):
        super().__init__()
        self.obj_type = TEST_DATA_ACK
        self.secret = secret
        self.performance = performance
        self.feedback = copy.deepcopy(feedback)
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'secret': self.secret,
               'performance': self.performance,
               'feedback': self.feedback}
        return copy.deepcopy(obj)


class TestingEpisodeNovelty(BasicEpisodeNovelty):
    def __init__(self, novelty_probability: float = None, novelty_threshold: float = None,
                 novelty: int = None, novelty_characterization: dict = None):
        super().__init__(novelty_probability=novelty_probability,
                         novelty_threshold=novelty_threshold,
                         novelty=novelty,
                         novelty_characterization=novelty_characterization)
        self.obj_type = TEST_EPISODE_NOVELTY
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'novelty_probability': self.novelty_probability,
               'novelty_threshold': self.novelty_threshold,
               'novelty': self.novelty,
               'novelty_characterization': self.novelty_characterization}
        return copy.deepcopy(obj)


class TestingEpisodeNoveltyAck(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = TEST_EPISODE_NOVELTY_ACK
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class EndExperiment(AiqObject):
    def __init__(self, model_experiment_id: str, secret: str):
        super().__init__()
        self.obj_type = END_EXPERIMENT
        self.model_experiment_id = model_experiment_id
        self.secret = secret
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'model_experiment_id': self.model_experiment_id,
               'secret': self.secret}
        return copy.deepcopy(obj)


class WaitOnSota(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = WAIT_ON_SOTA
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class SotaIdle(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = SOTA_IDLE
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class Episode(AiqObject):
    def __init__(self, novelty: int, difficulty: str, seed: int, domain: str, data_type: str,
                 episode_index: int = None, episode_id: int = None,
                 trial_novelty: int = NOVELTY_200, day_offset: int = 0,
                 trial_episode_index: int = None, use_image: bool = False):
        super().__init__()
        self.obj_type = OBJ_EPISODE
        self.novelty = novelty
        if self.novelty not in VALID_NOVELTY:
            raise AiqDataException('{} is not a valid novelty.'.format(self.novelty))
        self.difficulty = difficulty
        if self.difficulty not in VALID_DIFFICULTY:
            raise AiqDataException('{} is not a valid difficulty.'.format(self.difficulty))
        self.seed = seed
        self.domain = domain
        if self.domain not in VALID_DOMAINS:
            raise AiqDataException('{} is not a valid domain.'.format(self.domain))
        self.data_type = data_type
        if self.data_type not in VALID_DATA_TYPE:
            raise AiqDataException('{} is not a valid data type.'.format(self.data_type))
        self.episode_index = episode_index
        self.episode_id = episode_id
        self.trial_novelty = trial_novelty
        if self.trial_novelty not in VALID_NOVELTY:
            raise AiqDataException('{} is not a valid trial_novelty.'.format(self.trial_novelty))
        self.day_offset = day_offset
        self.trial_episode_index = trial_episode_index
        self.use_image = use_image
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'novelty': self.novelty,
               'difficulty': self.difficulty,
               'seed': self.seed,
               'domain': self.domain,
               'data_type': self.data_type,
               'episode_index': self.episode_index,
               'episode_id': self.episode_id,
               'trial_novelty': self.trial_novelty,
               'day_offset': self.day_offset,
               'trial_episode_index': self.trial_episode_index,
               'use_image': self.use_image}
        return copy.deepcopy(obj)


class Training(AiqObject):
    def __init__(self, episodes: list):
        super().__init__()
        self.obj_type = OBJ_TRAINING
        self.episodes = copy.deepcopy(episodes)
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'episodes': list()}
        for ep in self.episodes:
            obj['episodes'].append(ep.get_json_obj())
        return copy.deepcopy(obj)


class Trial(AiqObject):
    def __init__(self, episodes: list, novelty: int, novelty_visibility: int, difficulty: str):
        super().__init__()
        self.obj_type = OBJ_TRIAL
        self.episodes = copy.deepcopy(episodes)
        self.novelty = novelty
        self.novelty_visibility = novelty_visibility
        self.difficulty = difficulty
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'episodes': list(),
               'novelty': self.novelty,
               'novelty_visibility': self.novelty_visibility,
               'difficulty': self.difficulty}
        for ep in self.episodes:
            obj['episodes'].append(ep.get_json_obj())
        return copy.deepcopy(obj)


class NoveltyGroup(AiqObject):
    def __init__(self, trials: list):
        super().__init__()
        self.obj_type = OBJ_NOVELTY_GRP
        self.trials = copy.deepcopy(trials)
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'trials': list()}
        for trial in self.trials:
            obj['trials'].append(trial.get_json_obj())
        return copy.deepcopy(obj)


class Experiment(AiqObject):
    def __init__(self, training: Training, novelty_groups: list, budget: float):
        super().__init__()
        self.obj_type = OBJ_EXPERIMENT
        self.training = copy.deepcopy(training)
        self.novelty_groups = copy.deepcopy(novelty_groups)
        self.budget = budget
        self.model_experiment_id = None
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'training': self.training.get_json_obj(),
               'novelty_groups': list(),
               'budget': self.budget}
        for nov_group in self.novelty_groups:
            obj['novelty_groups'].append(nov_group.get_json_obj())
        return copy.deepcopy(obj)


class RequestNoveltyDescription(AiqObject):
    def __init__(self, r_domain: str, novelty: int, difficulty: str):
        super().__init__()
        self.obj_type = REQ_NOVELTY_DESCRIPTION
        if r_domain not in VALID_DOMAINS:
            raise AiqDataException('INVALID r_domain provided! {}'.format(r_domain))
        self.domain = r_domain
        if novelty not in VALID_NOVELTY:
            raise AiqDataException('INVALID novelty provided! {}'.format(novelty))
        self.novelty = novelty
        if difficulty not in VALID_DIFFICULTY:
            raise AiqDataException('INVALID difficulty provided! {}'.format(difficulty))
        self.difficulty = difficulty
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'domain': self.domain,
               'novelty': self.novelty,
               'difficulty': self.difficulty}
        return copy.deepcopy(obj)


class NoveltyDescription(AiqObject):
    def __init__(self, novelty_description: dict):
        super().__init__()
        self.obj_type = OBJ_NOVELTY_DESCRIPTION
        self.novelty_description = copy.deepcopy(novelty_description)
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'novelty_description': self.novelty_description}
        return copy.deepcopy(obj)


class GeneratorIdle(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = GENERATOR_IDLE
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class GeneratorReset(AiqObject):
    def __init__(self):
        super().__init__()
        self.obj_type = GENERATOR_RESET
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type}
        return copy.deepcopy(obj)


class StartGenerator(AiqObject):
    def __init__(self, domain: str, novelty: int, difficulty: str, seed: int, server_rpc_queue: str,
                 trial_novelty: int, epoch: float = None, day_offset: int = 0,
                 request_timeout: int = 20, use_image: bool = False):
        super().__init__()
        self.obj_type = START_GENERATOR
        if domain not in VALID_DOMAINS:
            raise AiqDataException('INVALID domain provided! {}'.format(domain))
        self.domain = domain
        if novelty not in VALID_NOVELTY:
            raise AiqDataException('INVALID novelty provided! {}'.format(novelty))
        self.novelty = novelty
        if difficulty not in VALID_DIFFICULTY:
            raise AiqDataException('INVALID difficulty provided! {}'.format(difficulty))
        self.difficulty = difficulty
        self.seed = seed
        self.server_rpc_queue = server_rpc_queue
        self.trial_novelty = trial_novelty
        if trial_novelty not in VALID_NOVELTY:
            raise AiqDataException('INVALID trial_novelty provided! {}'.format(trial_novelty))
        self.epoch = epoch
        if self.epoch is None:
            self.epoch = time.time()
        self.day_offset = day_offset
        self.request_timeout = request_timeout
        self.use_image = use_image
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'domain': self.domain,
               'novelty': self.novelty,
               'difficulty': self.difficulty,
               'seed': self.seed,
               'server_rpc_queue': self.server_rpc_queue,
               'trial_novelty': self.trial_novelty,
               'epoch': self.epoch,
               'day_offset': self.day_offset,
               'request_timeout': self.request_timeout,
               'use_image': self.use_image}
        return copy.deepcopy(obj)


class GeneratorResponse(AiqObject):
    def __init__(self, generator_rpc_queue: str):
        super().__init__()
        self.obj_type = GENERATOR_RESPONSE
        self.generator_rpc_queue = generator_rpc_queue
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'generator_rpc_queue': self.generator_rpc_queue}
        return copy.deepcopy(obj)


class AnalysisReady(AiqObject):
    def __init__(self, model_experiment_id: int):
        super().__init__()
        self.obj_type = ANALYSIS_READY
        self.model_experiment_id = model_experiment_id
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'model_experiment_id': self.model_experiment_id}
        return copy.deepcopy(obj)


class AnalysisPartial(AiqObject):
    def __init__(self, model_experiment_id: int, experiment_trial_id: int):
        super().__init__()
        self.obj_type = ANALYSIS_PARTIAL
        self.model_experiment_id = model_experiment_id
        self.experiment_trial_id = experiment_trial_id
        return

    def get_json_obj(self):
        obj = {'obj_type': self.obj_type,
               'model_experiment_id': self.model_experiment_id,
               'experiment_trial_id': self.experiment_trial_id}
        return copy.deepcopy(obj)


"""
[{"action": "event",
  "secret": "XXXX",
  "key": "XXXX",
  "data": {"category": "entity",
           "uuid": "6a3f05d6a4f243d5a76d5654d529db6a",
           "message": "ON",
           "package_type": "c4:cardaccess_inhome:WMS10-2",
           "epoch": "1445569748.405201",
           "sensor_type": "Control4-Motion",
           "serial": "000680000001150d",
           "by": "ZigbeeAgent",
           "target": "OfficeADesk"},
  "site": "tokyo",
  "channel": "rawevents"}]

[{"action": "tag",
  "secret": "XXXX",
  "key": "XXXX",
  "data": {"category": "entity",
           "uuid": "6a3f05d6a4f243d5a76d5654d529db6a",
           "message": "ON",
           "package_type": "c4:cardaccess_inhome:WMS10-2",
           "epoch": "1445569748.405201",
           "sensor_type": "Control4-Motion",
           "serial": "000680000001150d",
           "by": "ZigbeeAgent",
           "target": "M009",
           "tag": {"created_by": "RAT",
                   "label": {"name": "Work_On_Computer",
                             "value": ""},
                   "dataset": "P3302",
                   "experiment": "Test Experiment"}},
  "site": "tokyo",
  "channel": "tag"}]

[{"action": "control",
  "secret": "XXXX",
  "key": "XXXX",
  "data": {"category": "control",
           "uuid": "6a3f05d6a4f243d5a76d5654d529db6a",
           "command": "ON",
           "value": "",
           "replyto": "automate@tokyo",
           "cid": "42",
           "epoch": "1445569748.405201",
           "serial": "000680000001150d",
           "by": "AutomationAgent",
           "target": "LL009"},
  "site": "tokyo",
  "channel": "control"}]
"""


def make_epoch(utc_datetime):
    """This function converts a datetime.datetime object into its float equivalent for the
    unix epoch.

    Parameters
    ----------
    utc_datetime : datetime.datetime
        A UTC datetime.datetime object to convert into an epoch.

    Returns
    -------
    float
        The UTC epoch value for the provided UTC datetime.datetime object.

    Raises
    ------
    CasasDatetimeException
        If `utc_datetime` is a naive datetime.datetime object, where the tzinfo is not set or
        is not the UTC timezone.
    """
    epoch = None
    if utc_datetime is not None:
        if utc_datetime.tzinfo is None:
            raise CasasDatetimeException("make_epoch(utc_datetime) is naive, "
                                         "datetime.datetime.tzinfo is not set!")
        elif utc_datetime.tzinfo != pytz.utc:
            raise CasasDatetimeException("make_epoch(utc_datetime) is not UTC!")
        epoch = (utc_datetime - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
    return epoch


def epoch_to_stamp(utc_epoch):
    """This function converts a float representing a UTC unix epoch into a datetime.datetime
    object that is aware of the timezone.

    Parameters
    ----------
    utc_epoch : float
        A representation of a UTC unix epoch.

    Returns
    -------
    datetime.datetime
        The datetime.datetime object created from the `utc_epoch`.
    """
    utc_stamp = None
    if utc_epoch is not None:
        utc_stamp = datetime.datetime.utcfromtimestamp(float(utc_epoch)).replace(tzinfo=pytz.utc)
    return utc_stamp


def get_routing_key(casas_object):
    """This function takes in a CasasObject subclass and returns the RabbitMQ routing key for
    the given object class.

    Parameters
    ----------
    casas_object : CasasObject
        The object that we want the routing key for.

    Returns
    -------
    str
        The routing key for casas_object.
    """
    routing_key = ""

    if casas_object.action in [EVENT, TAG, CONTROL]:
        routing_key = "{}.{}.casas".format(str(casas_object.sensor_type),
                                           str(casas_object.site))
    elif casas_object.action in [HEARTBEAT, TRANSLATION]:
        routing_key = str(casas_object.site)
    elif casas_object.action in [ALG_PROCESSOR]:
        routing_key = "{}.{}.{}.{}".format(str(casas_object.algorithm.name),
                                           str(casas_object.algorithm.version_major),
                                           str(casas_object.algorithm.version_minor),
                                           str(casas_object.site))
    elif casas_object.action in [CIL_BASE]:
        routing_key = "{}.baseline.cil".format(str(casas_object.site))
    elif casas_object.action in [CIL_METRIC]:
        routing_key = "{}.metric.cil".format(str(casas_object.name))
    elif casas_object.action in [CIL_BASE_METRIC]:
        routing_key = "{}.baseline.{}.metric.cil".format(str(casas_object.baseline.site),
                                                         str(casas_object.metric.name))
    elif casas_object.action in [CIL_DATA]:
        routing_key = "{}.metric.{}.data.cil".format(str(casas_object.metric.name),
                                                     str(casas_object.site))

    return routing_key


def build_routing_key(action=EVENT, sensor_type='*', package_type='*', site='*',
                      algorithm_name='*', algorithm_version_major='*', algorithm_version_minor='*',
                      metric='*'):
    """This function builds a routing key from the provided parameters.

    Parameters
    ----------
    action : str
    sensor_type : str, optional
        This is the desired sensor_type, default is '*' for all values.
    package_type : str, optional
        This is the desired package_type, default is '*' for all values.
    site : str, optional
        This is the desired site, default is '*' for all values.

    Returns
    -------
    str
        The built routing key.
    """
    routing_key = '#'
    if action in [EVENT, TAG, CONTROL]:
        routing_key = "{}.{}.casas".format(str(sensor_type),
                                           str(site))
    elif action in [HEARTBEAT, TRANSLATION]:
        routing_key = str(site)
    elif action in [ALG_PROCESSOR]:
        routing_key = "{}.{}.{}.{}".format(str(algorithm_name),
                                           str(algorithm_version_major),
                                           str(algorithm_version_minor),
                                           str(site))
    elif action in [CIL_BASE]:
        routing_key = "{}.baseline.cil".format(str(site))
    elif action in [CIL_METRIC]:
        routing_key = "{}.metric.cil".format(str(metric))
    elif action in [CIL_BASE_METRIC]:
        routing_key = "{}.baseline.{}.metric.cil".format(str(site),
                                                         str(metric))
    elif action in [CIL_DATA]:
        routing_key = "{}.metric.{}.data.cil".format(str(metric),
                                                     str(site))
    return routing_key


def build_objects_from_json(message):
    """This function converts a string message into a list of casas.objects.

    Parameters
    ----------
    message : str
        A string of a JSON list containing dictionaries.

    Returns
    -------
    list(casas.objects)
        A list containing Event, Tag, Control, Heartbeat, or Translation objects.
        This list can be mixed for different types so make sure to check the action variable.
    """
    log.debug("build_objects_from_json( {} )".format(str(message)))
    response = CasasResponse(status='success',
                             response_type='data',
                             error_message='No Errors')
    return_objects = list()
    result = None
    try:
        blob = json.loads(message)

        # AIQ quick modification.
        if isinstance(blob, dict):
            if 'obj_type' in blob:
                blob = list([copy.deepcopy(blob)])

        if len(blob) == 0:
            response.add_error(
                casas_error=CasasError(error_type='data',
                                       message='The JSON array contains 0 values.'))

        element_id = 0
        for obj in blob:
            log.debug("object: {}".format(str(obj)))
            errormsgs = list()
            obj_uuid = "unknown"

            if 'obj_type' in obj:
                if obj['obj_type'] == REQ_MODEL:
                    if 'aiq_username' not in obj:
                        errormsgs.append('Could not obtain attribute aiq_username, '
                                         'please include json attribute aiq_username.')
                    if 'aiq_secret' not in obj:
                        errormsgs.append('Could not obtain attribute aiq_secret, '
                                         'please include json attribute aiq_secret.')
                    if 'model_name' not in obj:
                        errormsgs.append('Could not obtain attribute model_name, '
                                         'please include json attribute model_name.')
                    if 'organization' not in obj:
                        errormsgs.append('Could not obtain attribute organization, '
                                         'please include json attribute organization.')
                    if 'description' not in obj:
                        errormsgs.append('Could not obtain attribute description, '
                                         'please include json attribute description.')
                    if len(errormsgs) == 0:
                        result = RequestModel(aiq_username=obj['aiq_username'],
                                              aiq_secret=obj['aiq_secret'],
                                              model_name=obj['model_name'],
                                              organization=obj['organization'],
                                              description=obj['description'])
                elif obj['obj_type'] == REQ_STATE:
                    if len(errormsgs) == 0:
                        result = RequestState()
                elif obj['obj_type'] == MODEL:
                    if 'aiq_username' not in obj:
                        errormsgs.append('Could not obtain attribute aiq_username, '
                                         'please include json attribute aiq_username.')
                    if 'aiq_secret' not in obj:
                        errormsgs.append('Could not obtain attribute aiq_secret, '
                                         'please include json attribute aiq_secret.')
                    if 'model_name' not in obj:
                        errormsgs.append('Could not obtain attribute model_name, '
                                         'please include json attribute model_name.')
                    if 'organization' not in obj:
                        errormsgs.append('Could not obtain attribute organization, '
                                         'please include json attribute organization.')
                    if 'description' not in obj:
                        errormsgs.append('Could not obtain attribute description, '
                                         'please include json attribute description.')
                    result = Model(model_name=obj['model_name'],
                                   organization=obj['organization'],
                                   aiq_username=obj['aiq_username'],
                                   aiq_secret=obj['aiq_secret'],
                                   description=obj['description'])
                elif obj['obj_type'] == REQ_EXPERIMENT:
                    model = None
                    epoch = None
                    if 'model' in obj:
                        model = get_subobject(casas_object=obj['model'],
                                              errormsgs=errormsgs)
                    else:
                        errormsgs.append('Could not obtain attribute model, '
                                         'please include json attribute model.')
                    if 'novelty' not in obj:
                        errormsgs.append('Could not obtain attribute novelty, '
                                         'please include json attribute novelty.')
                    if 'novelty_visibility' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_visibility, '
                                         'please include json attribute novelty_visibility.')
                    if 'client_rpc_queue' not in obj:
                        errormsgs.append('Could not obtain attribute client_rpc_queue, '
                                         'please include json attribute client_rpc_queue.')
                    if 'git_version' not in obj:
                        errormsgs.append('Could not obtain attribute git_version, '
                                         'please include json attribute git_version.')
                    if 'seed' not in obj:
                        errormsgs.append('Could not obtain attribute seed, '
                                         'please include json attribute seed.')
                    if 'domain_dict' not in obj:
                        errormsgs.append('Could not obtain attribute domain_dict, '
                                         'please include json attribute domain_dict.')
                    if 'experiment_type' not in obj:
                        errormsgs.append('Could not obtain attribute experiment_type, '
                                         'please include json attribute experiment_type.')
                    if 'no_testing' not in obj:
                        errormsgs.append('Could not obtain attribute no_testing, '
                                         'please include json attribute no_testing.')
                    if 'description' not in obj:
                        errormsgs.append('Could not obtain attribute description, '
                                         'please include json attribute description.')
                    if 'epoch' in obj:
                        epoch = obj['epoch']
                    if len(errormsgs) == 0:
                        result = RequestExperiment(model=model,
                                                   novelty=obj['novelty'],
                                                   novelty_visibility=obj['novelty_visibility'],
                                                   client_rpc_queue=obj['client_rpc_queue'],
                                                   git_version=obj['git_version'],
                                                   experiment_type=obj['experiment_type'],
                                                   seed=obj['seed'],
                                                   domain_dict=obj['domain_dict'],
                                                   epoch=epoch,
                                                   no_testing=obj['no_testing'],
                                                   description=obj['description'])
                elif obj['obj_type'] == REQ_EXP_TRIALS:
                    model = None
                    epoch = None
                    if 'model' in obj:
                        model = get_subobject(casas_object=obj['model'],
                                              errormsgs=errormsgs)
                    else:
                        errormsgs.append('Could not obtain attribute model, '
                                         'please include json attribute model.')
                    if 'experiment_secret' not in obj:
                        errormsgs.append('Could not obtain attribute experiment_secret, '
                                         'please include json attribute experiment_secret.')
                    if 'client_rpc_queue' not in obj:
                        errormsgs.append('Could not obtain attribute client_rpc_queue, '
                                         'please include json attribute client_rpc_queue.')
                    if 'just_one_trial' not in obj:
                        errormsgs.append('Could not obtain attribute just_one_trial, '
                                         'please include json attribute just_one_trial.')
                    if 'domain_dict' not in obj:
                        errormsgs.append('Could not obtain attribute domain_dict, '
                                         'please include json attribute domain_dict.')
                    if 'epoch' in obj:
                        epoch = obj['epoch']
                    if len(errormsgs) == 0:
                        result = RequestExperimentTrials(
                            model=model,
                            experiment_secret=obj['experiment_secret'],
                            client_rpc_queue=obj['client_rpc_queue'],
                            just_one_trial=obj['just_one_trial'],
                            domain_dict=obj['domain_dict'],
                            epoch=epoch)
                elif obj['obj_type'] == EXPERIMENT_RESP:
                    if 'server_rpc_queue' not in obj:
                        errormsgs.append('Could not obtain attribute server_rpc_queue, '
                                         'please include json attribute server_rpc_queue.')
                    if 'experiment_secret' not in obj:
                        errormsgs.append('Could not obtain attribute experiment_secret, '
                                         'please include json attribute experiment_secret.')
                    if 'model_experiment_id' not in obj:
                        errormsgs.append('Could not obtain attribute model_experiment_id, '
                                         'please include json attribute model_experiment_id.')
                    if 'experiment_timeout' not in obj:
                        errormsgs.append('Could not obtain attribute experiment_timeout, '
                                         'please include json attribute experiment_timeout.')
                    if len(errormsgs) == 0:
                        result = ExperimentResponse(server_rpc_queue=obj['server_rpc_queue'],
                                                    experiment_secret=obj['experiment_secret'],
                                                    model_experiment_id=obj['model_experiment_id'],
                                                    experiment_timeout=obj['experiment_timeout'])
                elif obj['obj_type'] == EXPERIMENT_START:
                    if len(errormsgs) == 0:
                        result = ExperimentStart()
                elif obj['obj_type'] == EXPERIMENT_END:
                    if len(errormsgs) == 0:
                        result = ExperimentEnd()
                elif obj['obj_type'] == EXPERIMENT_EXCEPTION:
                    if 'message' not in obj:
                        raise AiqExperimentException(
                            value='Experiment Exception raised without a message!')
                    else:
                        raise AiqExperimentException(value=obj['message'])
                elif obj['obj_type'] == BENCHMARK_REQ:
                    if 'benchmark_script' not in obj:
                        errormsgs.append('Could not obtain attribute benchmark_script, '
                                         'please include json attribute benchmark_script.')
                    if len(errormsgs) == 0:
                        result = BenchmarkRequest(benchmark_script=obj['benchmark_script'])
                elif obj['obj_type'] == BENCHMARK_DATA:
                    if 'benchmark_data' not in obj:
                        errormsgs.append('Could not obtain attribute benchmark_data, '
                                         'please include json attribute benchmark_data.')
                    if len(errormsgs) == 0:
                        result = BenchmarkData(benchmark_data=obj['benchmark_data'])
                elif obj['obj_type'] == BENCHMARK_ACK:
                    if len(errormsgs) == 0:
                        result = BenchmarkAck()
                elif obj['obj_type'] == NOVELTY_START:
                    if len(errormsgs) == 0:
                        result = NoveltyStart()
                elif obj['obj_type'] == NOVELTY_END:
                    if len(errormsgs) == 0:
                        result = NoveltyEnd()
                elif obj['obj_type'] == TRIAL_START:
                    if 'trial_number' not in obj:
                        errormsgs.append('Could not obtain attribute trial_number, '
                                         'please include json attribute trial_number.')
                    if 'total_trials' not in obj:
                        errormsgs.append('Could not obtain attribute total_trials, '
                                         'please include json attribute total_trials.')
                    if 'message' not in obj:
                        errormsgs.append('Could not obtain attribute message, '
                                         'please include json attribute message.')
                    if 'novelty_description' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_description, '
                                         'please include json attribute novelty_description.')
                    if len(errormsgs) == 0:
                        result = TrialStart(trial_number=obj['trial_number'],
                                            total_trials=obj['total_trials'],
                                            message=obj['message'],
                                            novelty_description=obj['novelty_description'])
                elif obj['obj_type'] == TRIAL_END:
                    if len(errormsgs) == 0:
                        result = TrialEnd()
                elif obj['obj_type'] == TRAINING_START:
                    if len(errormsgs) == 0:
                        result = TrainingStart()
                elif obj['obj_type'] == TRAINING_ACTIVE:
                    if len(errormsgs) == 0:
                        result = TrainingActive()
                elif obj['obj_type'] == TRAINING_END:
                    if 'message' not in obj:
                        errormsgs.append('Could not obtain attribute message, '
                                         'please include json attribute message.')
                    if len(errormsgs) == 0:
                        result = TrainingEnd(message=obj['message'])
                elif obj['obj_type'] == TRAINING_MODEL_END:
                    if len(errormsgs) == 0:
                        result = TrainingModelEnd()
                elif obj['obj_type'] == TRAINING_END_EARLY:
                    if len(errormsgs) == 0:
                        result = TrainingEndEarly()
                elif obj['obj_type'] == TRAIN_EPISODE_START:
                    if 'episode_number' not in obj:
                        errormsgs.append('Could not obtain attribute episode_number, '
                                         'please include json attribute episode_number.')
                    if 'total_episodes' not in obj:
                        errormsgs.append('Could not obtain attribute total_episodes, '
                                         'please include json attribute total_episodes.')
                    if len(errormsgs) == 0:
                        result = TrainingEpisodeStart(episode_number=obj['episode_number'],
                                                      total_episodes=obj['total_episodes'])
                elif obj['obj_type'] == TRAIN_EPISODE_ACTIVE:
                    if len(errormsgs) == 0:
                        result = TrainingEpisodeActive()
                elif obj['obj_type'] == TRAIN_EPISODE_END:
                    if 'performance' not in obj:
                        errormsgs.append('Could not obtain attribute performance, '
                                         'please include json attribute performance.')
                    if 'feedback' not in obj:
                        errormsgs.append('Could not obtain attribute feedback, '
                                         'please include json attribute feedback.')
                    if len(errormsgs) == 0:
                        result = TrainingEpisodeEnd(performance=obj['performance'],
                                                    feedback=obj['feedback'])
                elif obj['obj_type'] == EPISODE_END:
                    if 'performance' not in obj:
                        errormsgs.append('Could not obtain attribute performance, '
                                         'please include json attribute performance.')
                    if 'feedback' not in obj:
                        errormsgs.append('Could not obtain attribute feedback, '
                                         'please include json attribute feedback.')
                    if len(errormsgs) == 0:
                        result = EpisodeEnd(performance=obj['performance'],
                                            feedback=obj['feedback'])
                elif obj['obj_type'] == BASIC_DATA:
                    if 'feature_vector' not in obj:
                        errormsgs.append('Could not obtain attribute feature_vector, '
                                         'please include json attribute feature_vector.')
                    if 'feature_label' not in obj:
                        errormsgs.append('Could not obtain attribute feature_label, '
                                         'please include json attribute feature_label.')
                    if len(errormsgs) == 0:
                        result = BasicData(feature_vector=obj['feature_vector'],
                                           feature_label=obj['feature_label'])
                elif obj['obj_type'] == BASIC_DATA_PREDICTION:
                    if 'label_prediction' not in obj:
                        errormsgs.append('Could not obtain attribute label_prediction, '
                                         'please include json attribute label_prediction.')
                    if len(errormsgs) == 0:
                        result = BasicDataPrediction(label_prediction=obj['label_prediction'])
                elif obj['obj_type'] == BASIC_DATA_ACK:
                    if 'performance' not in obj:
                        errormsgs.append('Could not obtain attribute performance, '
                                         'please include json attribute performance.')
                    if 'feedback' not in obj:
                        errormsgs.append('Could not obtain attribute feedback, '
                                         'please include json attribute feedback.')
                    if len(errormsgs) == 0:
                        result = BasicDataAck(performance=obj['performance'],
                                              feedback=obj['feedback'])
                elif obj['obj_type'] == BASIC_EPISODE_NOVELTY:
                    if 'novelty_probability' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_probability, '
                                         'please include json attribute novelty_probability.')
                    if 'novelty_threshold' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_threshold, '
                                         'please include json attribute novelty_threshold.')
                    if 'novelty' not in obj:
                        errormsgs.append('Could not obtain attribute novelty, '
                                         'please include json attribute novelty.')
                    if 'novelty_characterization' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_characterization, '
                                         'please include json attribute novelty_characterization.')
                    if len(errormsgs) == 0:
                        result = BasicEpisodeNovelty(
                            novelty_probability=obj['novelty_probability'],
                            novelty_threshold=obj['novelty_threshold'],
                            novelty=obj['novelty'],
                            novelty_characterization=obj['novelty_characterization'])
                elif obj['obj_type'] == REQ_DATA:
                    if len(errormsgs) == 0:
                        result = RequestData()
                elif obj['obj_type'] == REQ_TRAIN_DATA:
                    if 'model_experiment_id' not in obj:
                        errormsgs.append('Could not obtain attribute model_experiment_id, '
                                         'please include json attribute model_experiment_id.')
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if len(errormsgs) == 0:
                        result = RequestTrainingData(model_experiment_id=obj['model_experiment_id'],
                                                     secret=obj['secret'])
                elif obj['obj_type'] == TRAINING_DATA:
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if 'feature_vector' not in obj:
                        errormsgs.append('Could not obtain attribute feature_vector, '
                                         'please include json attribute feature_vector.')
                    if 'feature_label' not in obj:
                        errormsgs.append('Could not obtain attribute feature_label, '
                                         'please include json attribute feature_label.')
                    if 'utc_remote_epoch_received' not in obj:
                        errormsgs.append('Could not obtain attribute utc_remote_epoch_received, '
                                         'please include json attribute utc_remote_epoch_received.')
                    if 'utc_remote_epoch_sent' not in obj:
                        errormsgs.append('Could not obtain attribute utc_remote_epoch_sent, '
                                         'please include json attribute utc_remote_epoch_sent.')
                    if len(errormsgs) == 0:
                        result = TrainingData(
                            secret=obj['secret'],
                            feature_vector=obj['feature_vector'],
                            feature_label=obj['feature_label'],
                            utc_remote_epoch_received=obj['utc_remote_epoch_received'],
                            utc_remote_epoch_sent=obj['utc_remote_epoch_sent'])
                elif obj['obj_type'] == TRAIN_DATA_PRED:
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if 'utc_remote_epoch_received' not in obj:
                        errormsgs.append('Could not obtain attribute utc_remote_epoch_received, '
                                         'please include json attribute utc_remote_epoch_received.')
                    if 'utc_remote_epoch_sent' not in obj:
                        errormsgs.append('Could not obtain attribute utc_remote_epoch_sent, '
                                         'please include json attribute utc_remote_epoch_sent.')
                    if 'label_prediction' not in obj:
                        errormsgs.append('Could not obtain attribute label_prediction, '
                                         'please include json attribute label_prediction.')
                    if 'end_early' not in obj:
                        errormsgs.append('Could not obtain attribute end_early, '
                                         'please include json attribute end_early.')
                    if len(errormsgs) == 0:
                        result = TrainingDataPrediction(
                            secret=obj['secret'],
                            utc_remote_epoch_received=obj['utc_remote_epoch_received'],
                            utc_remote_epoch_sent=obj['utc_remote_epoch_sent'],
                            label_prediction=obj['label_prediction'],
                            end_early=obj['end_early'])
                elif obj['obj_type'] == TRAIN_DATA_ACK:
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if 'performance' not in obj:
                        errormsgs.append('Could not obtain attribute performance, '
                                         'please include json attribute performance.')
                    if 'feedback' not in obj:
                        errormsgs.append('Could not obtain attribute feedback, '
                                         'please include json attribute feedback.')
                    if len(errormsgs) == 0:
                        result = TrainingDataAck(
                            secret=obj['secret'],
                            performance=obj['performance'],
                            feedback=obj['feedback'])
                elif obj['obj_type'] == TRAIN_EPISODE_NOVELTY:
                    if 'novelty_probability' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_probability, '
                                         'please include json attribute novelty_probability.')
                    if 'novelty_threshold' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_threshold, '
                                         'please include json attribute novelty_threshold.')
                    if 'novelty' not in obj:
                        errormsgs.append('Could not obtain attribute novelty, '
                                         'please include json attribute novelty.')
                    if 'novelty_characterization' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_characterization, '
                                         'please include json attribute novelty_characterization.')
                    if len(errormsgs) == 0:
                        result = TrainingEpisodeNovelty(
                            novelty_probability=obj['novelty_probability'],
                            novelty_threshold=obj['novelty_threshold'],
                            novelty=obj['novelty'],
                            novelty_characterization=obj['novelty_characterization'])
                elif obj['obj_type'] == TRAIN_EPISODE_NOVELTY_ACK:
                    if len(errormsgs) == 0:
                        result = TrainingEpisodeNoveltyAck()
                elif obj['obj_type'] == TESTING_START:
                    if len(errormsgs) == 0:
                        result = TestingStart()
                elif obj['obj_type'] == TESTING_ACTIVE:
                    if len(errormsgs) == 0:
                        result = TestingActive()
                elif obj['obj_type'] == TESTING_END:
                    if len(errormsgs) == 0:
                        result = TestingEnd()
                elif obj['obj_type'] == TEST_EPISODE_START:
                    if 'episode_number' not in obj:
                        errormsgs.append('Could not obtain attribute episode_number, '
                                         'please include json attribute episode_number.')
                    if 'total_episodes' not in obj:
                        errormsgs.append('Could not obtain attribute total_episodes, '
                                         'please include json attribute total_episodes.')
                    if len(errormsgs) == 0:
                        result = TestingEpisodeStart(episode_number=obj['episode_number'],
                                                     total_episodes=obj['total_episodes'])
                elif obj['obj_type'] == TEST_EPISODE_ACTIVE:
                    if len(errormsgs) == 0:
                        result = TestingEpisodeActive()
                elif obj['obj_type'] == TEST_EPISODE_END:
                    if 'performance' not in obj:
                        errormsgs.append('Could not obtain attribute performance, '
                                         'please include json attribute performance.')
                    if 'feedback' not in obj:
                        errormsgs.append('Could not obtain attribute feedback, '
                                         'please include json attribute feedback.')
                    if len(errormsgs) == 0:
                        result = TestingEpisodeEnd(performance=obj['performance'],
                                                   feedback=obj['feedback'])
                elif obj['obj_type'] == REQ_TEST_DATA:
                    if 'model_experiment_id' not in obj:
                        errormsgs.append('Could not obtain attribute model_experiment_id, '
                                         'please include json attribute model_experiment_id.')
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if len(errormsgs) == 0:
                        result = RequestTestingData(model_experiment_id=obj['model_experiment_id'],
                                                    secret=obj['secret'])
                elif obj['obj_type'] == TESTING_DATA:
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if 'feature_vector' not in obj:
                        errormsgs.append('Could not obtain attribute feature_vector, '
                                         'please include json attribute feature_vector.')
                    if 'utc_remote_epoch_received' not in obj:
                        errormsgs.append('Could not obtain attribute utc_remote_epoch_received, '
                                         'please include json attribute utc_remote_epoch_received.')
                    if 'utc_remote_epoch_sent' not in obj:
                        errormsgs.append('Could not obtain attribute utc_remote_epoch_sent, '
                                         'please include json attribute utc_remote_epoch_sent.')
                    if 'novelty_indicator' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_indicator, '
                                         'please include json attribute novelty_indicator.')
                    if len(errormsgs) == 0:
                        result = TestingData(
                            secret=obj['secret'],
                            feature_vector=obj['feature_vector'],
                            utc_remote_epoch_received=obj['utc_remote_epoch_received'],
                            utc_remote_epoch_sent=obj['utc_remote_epoch_sent'],
                            novelty_indicator=obj['novelty_indicator'])
                elif obj['obj_type'] == TEST_DATA_PRED:
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if 'utc_remote_epoch_received' not in obj:
                        errormsgs.append('Could not obtain attribute utc_remote_epoch_received, '
                                         'please include json attribute utc_remote_epoch_received.')
                    if 'utc_remote_epoch_sent' not in obj:
                        errormsgs.append('Could not obtain attribute utc_remote_epoch_sent, '
                                         'please include json attribute utc_remote_epoch_sent.')
                    if 'label_prediction' not in obj:
                        errormsgs.append('Could not obtain attribute label_prediction, '
                                         'please include json attribute label_prediction.')
                    if 'end_early' not in obj:
                        errormsgs.append('Could not obtain attribute end_early, '
                                         'please include json attribute end_early.')
                    if len(errormsgs) == 0:
                        result = TestingDataPrediction(
                            secret=obj['secret'],
                            utc_remote_epoch_received=obj['utc_remote_epoch_received'],
                            utc_remote_epoch_sent=obj['utc_remote_epoch_sent'],
                            label_prediction=obj['label_prediction'],
                            end_early=obj['end_early'])
                elif obj['obj_type'] == TEST_DATA_ACK:
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if 'performance' not in obj:
                        errormsgs.append('Could not obtain attribute performance, '
                                         'please include json attribute performance.')
                    if 'feedback' not in obj:
                        errormsgs.append('Could not obtain attribute feedback, '
                                         'please include json attribute feedback.')
                    if len(errormsgs) == 0:
                        result = TestingDataAck(secret=obj['secret'],
                                                performance=obj['performance'],
                                                feedback=obj['feedback'])
                elif obj['obj_type'] == TEST_EPISODE_NOVELTY:
                    if 'novelty_probability' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_probability, '
                                         'please include json attribute novelty_probability.')
                    if 'novelty_threshold' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_threshold, '
                                         'please include json attribute novelty_threshold.')
                    if 'novelty' not in obj:
                        errormsgs.append('Could not obtain attribute novelty, '
                                         'please include json attribute novelty.')
                    if 'novelty_characterization' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_characterization, '
                                         'please include json attribute novelty_characterization.')
                    if len(errormsgs) == 0:
                        result = TestingEpisodeNovelty(
                            novelty_probability=obj['novelty_probability'],
                            novelty_threshold=obj['novelty_threshold'],
                            novelty=obj['novelty'],
                            novelty_characterization=obj['novelty_characterization'])
                elif obj['obj_type'] == TEST_EPISODE_NOVELTY_ACK:
                    if len(errormsgs) == 0:
                        result = TestingEpisodeNoveltyAck()
                elif obj['obj_type'] == END_EXPERIMENT:
                    if 'model_experiment_id' not in obj:
                        errormsgs.append('Could not obtain attribute model_experiment_id, '
                                         'please include json attribute model_experiment_id.')
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if len(errormsgs) == 0:
                        result = EndExperiment(model_experiment_id=obj['model_experiment_id'],
                                               secret=obj['secret'])
                elif obj['obj_type'] == WAIT_ON_SOTA:
                    if len(errormsgs) == 0:
                        result = WaitOnSota()
                elif obj['obj_type'] == SOTA_IDLE:
                    if len(errormsgs) == 0:
                        result = SotaIdle()
                elif obj['obj_type'] == OBJ_EPISODE:
                    if 'novelty' not in obj:
                        errormsgs.append('Could not obtain attribute novelty, '
                                         'please include json attribute novelty.')
                    if 'difficulty' not in obj:
                        errormsgs.append('Could not obtain attribute difficulty, '
                                         'please include json attribute difficulty.')
                    if 'seed' not in obj:
                        errormsgs.append('Could not obtain attribute seed, '
                                         'please include json attribute seed.')
                    if 'domain' not in obj:
                        errormsgs.append('Could not obtain attribute domain, '
                                         'please include json attribute domain.')
                    if 'data_type' not in obj:
                        errormsgs.append('Could not obtain attribute data_type, '
                                         'please include json attribute data_type.')
                    if 'episode_index' not in obj:
                        errormsgs.append('Could not obtain attribute episode_index, '
                                         'please include json attribute episode_index.')
                    if 'episode_id' not in obj:
                        errormsgs.append('Could not obtain attribute episode_id, '
                                         'please include json attribute episode_id.')
                    if 'trial_novelty' not in obj:
                        errormsgs.append('Could not obtain attribute trial_novelty, '
                                         'please include json attribute trial_novelty.')
                    if 'day_offset' not in obj:
                        errormsgs.append('Could not obtain attribute day_offset, '
                                         'please include json attribute day_offset.')
                    if 'trial_episode_index' not in obj:
                        errormsgs.append('Could not obtain attribute trial_episode_index, '
                                         'please include json attribute trial_episode_index.')
                    if 'use_image' not in obj:
                        errormsgs.append('Could not obtain attribute use_image, '
                                         'please include json attribute use_image.')
                    if len(errormsgs) == 0:
                        result = Episode(novelty=obj['novelty'],
                                         difficulty=obj['difficulty'],
                                         domain=obj['domain'],
                                         data_type=obj['data_type'],
                                         seed=obj['seed'],
                                         episode_index=obj['episode_index'],
                                         episode_id=obj['episode_id'],
                                         trial_novelty=obj['trial_novelty'],
                                         day_offset=obj['day_offset'],
                                         trial_episode_index=obj['trial_episode_index'],
                                         use_image=obj['use_image'])
                elif obj['obj_type'] == OBJ_TRAINING:
                    if 'episodes' not in obj:
                        errormsgs.append('Could not obtain attribute episodes, '
                                         'please include json attribute episodes.')
                    episodes = list()
                    if len(errormsgs) == 0:
                        if len(obj['episodes']) > 0:
                            episodes = get_subobject_list(
                                casas_object=json.dumps(obj['episodes']),
                                errormsgs=errormsgs)
                    if len(errormsgs) == 0:
                        result = Training(episodes=episodes)
                elif obj['obj_type'] == OBJ_TRIAL:
                    if 'episodes' not in obj:
                        errormsgs.append('Could not obtain attribute episodes, '
                                         'please include json attribute episodes.')
                    if 'novelty' not in obj:
                        errormsgs.append('Could not obtain attribute novelty, '
                                         'please include json attribute novelty.')
                    if 'novelty_visibility' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_visibility, '
                                         'please include json attribute novelty_visibiliy.')
                    if 'difficulty' not in obj:
                        errormsgs.append('Could not obtain attribute difficulty, '
                                         'please include json attribute difficulty.')
                    episodes = list()
                    if len(errormsgs) == 0:
                        if len(obj['episodes']) > 0:
                            episodes = get_subobject_list(
                                casas_object=json.dumps(obj['episodes']),
                                errormsgs=errormsgs)
                    if len(errormsgs) == 0:
                        result = Trial(episodes=episodes,
                                       novelty=obj['novelty'],
                                       novelty_visibility=obj['novelty_visibility'],
                                       difficulty=obj['difficulty'])
                elif obj['obj_type'] == OBJ_NOVELTY_GRP:
                    if 'trials' not in obj:
                        errormsgs.append('Could not obtain attribute trials, '
                                         'please include json attribute trials.')
                    trials = list()
                    if len(errormsgs) == 0:
                        if len(obj['trials']) > 0:
                            trials = get_subobject_list(
                                casas_object=json.dumps(obj['trials']),
                                errormsgs=errormsgs)
                    if len(errormsgs) == 0:
                        result = NoveltyGroup(trials=trials)
                elif obj['obj_type'] == OBJ_EXPERIMENT:
                    if 'training' not in obj:
                        errormsgs.append('Could not obtain attribute training, '
                                         'please include json attribute training.')
                    if 'novelty_groups' not in obj:
                        errormsgs.append('Could not obtain attribute novelty_groups, '
                                         'please include json attribute novelty_groups.')
                    if 'budget' not in obj:
                        errormsgs.append('Could not obtain attribute budget, '
                                         'please include json attribute budget.')
                    training = None
                    nov_groups = list()
                    if len(errormsgs) == 0:
                        training = get_subobject(
                            casas_object='[{}]'.format(json.dumps(obj['training'])),
                            errormsgs=errormsgs)
                    if len(errormsgs) == 0:
                        if len(obj['novelty_groups']) > 0:
                            nov_groups = get_subobject_list(
                                casas_object=json.dumps(obj['novelty_groups']),
                                errormsgs=errormsgs)
                    if len(errormsgs) == 0:
                        result = Experiment(training=training,
                                            novelty_groups=nov_groups,
                                            budget=obj['budget'])
                elif obj['obj_type'] == REQ_NOVELTY_DESCRIPTION:
                    if 'domain' not in obj:
                        errormsgs.append('Could not obtain attribute domain, '
                                         'please include json attribute domain.')
                    if 'novelty' not in obj:
                        errormsgs.append('Could not obtain attribute novelty, '
                                         'please include json attribute novelty.')
                    if 'difficulty' not in obj:
                        errormsgs.append('Could not obtain attribute difficulty, '
                                         'please include json attribute difficulty.')
                    if len(errormsgs) == 0:
                        result = RequestNoveltyDescription(r_domain=obj['domain'],
                                                           novelty=obj['novelty'],
                                                           difficulty=obj['difficulty'])
                elif obj['obj_type'] == OBJ_NOVELTY_DESCRIPTION:
                    if 'novelty_description' not in obj:
                        errormsgs.append('Coule not obtain attribute novelty_description, '
                                         'please include json attribute novelty_description.')
                    if len(errormsgs) == 0:
                        result = NoveltyDescription(novelty_description=obj['novelty_description'])
                elif obj['obj_type'] == GENERATOR_IDLE:
                    if len(errormsgs) == 0:
                        result = GeneratorIdle()
                elif obj['obj_type'] == GENERATOR_RESET:
                    if len(errormsgs) == 0:
                        result = GeneratorReset()
                elif obj['obj_type'] == START_GENERATOR:
                    if 'domain' not in obj:
                        errormsgs.append('Could not obtain attribute domain, '
                                         'please include json attribute domain.')
                    if 'novelty' not in obj:
                        errormsgs.append('Could not obtain attribute novelty, '
                                         'please include json attribute novelty.')
                    if 'difficulty' not in obj:
                        errormsgs.append('Could not obtain attribute difficulty, '
                                         'please include json attribute difficulty.')
                    if 'seed' not in obj:
                        errormsgs.append('Could not obtain attribute seed, '
                                         'please include json attribute seed.')
                    if 'server_rpc_queue' not in obj:
                        errormsgs.append('Could not obtain attribute server_rpc_queue, '
                                         'please include json attribute server_rpc_queue.')
                    if 'trial_novelty' not in obj:
                        errormsgs.append('Could not obtain attribute trial_novelty, '
                                         'please include json attribute trial_novelty.')
                    if 'epoch' not in obj:
                        errormsgs.append('Could not obtain attribute epoch, '
                                         'please include json attribute epoch.')
                    if 'day_offset' not in obj:
                        errormsgs.append('Could not obtain attribute day_offset, '
                                         'please include json attribute day_offset.')
                    if 'request_timeout' not in obj:
                        errormsgs.append('Could not obtain attribute request_timeout, '
                                         'please include json attribute request_timeout.')
                    if 'use_image' not in obj:
                        errormsgs.append('Could not obtain attribute use_image, '
                                         'please include json attribute use_image.')
                    if len(errormsgs) == 0:
                        result = StartGenerator(domain=obj['domain'],
                                                novelty=obj['novelty'],
                                                difficulty=obj['difficulty'],
                                                seed=obj['seed'],
                                                server_rpc_queue=obj['server_rpc_queue'],
                                                trial_novelty=obj['trial_novelty'],
                                                epoch=obj['epoch'],
                                                day_offset=obj['day_offset'],
                                                request_timeout=obj['request_timeout'],
                                                use_image=obj['use_image'])
                elif obj['obj_type'] == GENERATOR_RESPONSE:
                    if 'generator_rpc_queue' not in obj:
                        errormsgs.append('Could not obtain attribute generator_rpc_queue, '
                                         'please include json attribute generator_rpc_queue.')
                    if len(errormsgs) == 0:
                        result = GeneratorResponse(generator_rpc_queue=obj['generator_rpc_queue'])
                elif obj['obj_type'] == ANALYSIS_READY:
                    if 'model_experiment_id' not in obj:
                        errormsgs.append('Could not obtain attribute model_experiment_id, '
                                         'please include json attribute model_experiment_id.')
                    if len(errormsgs) == 0:
                        result = AnalysisReady(model_experiment_id=obj['model_experiment_id'])
                elif obj['obj_type'] == ANALYSIS_PARTIAL:
                    if 'model_experiment_id' not in obj:
                        errormsgs.append('Could not obtain attribute model_experiment_id, '
                                         'please include json attribute model_experiment_id.')
                    if 'experiment_trial_id' not in obj:
                        errormsgs.append('Could not obtain attribute experiment_trial_id, '
                                         'please include json attribute experiment_trial_id.')
                    if len(errormsgs) == 0:
                        result = AnalysisPartial(model_experiment_id=obj['model_experiment_id'],
                                                 experiment_trial_id=obj['experiment_trial_id'])
                return_objects.append(copy.deepcopy(result))
            elif 'action' not in obj:
                errormsgs.append("Could not obtain attribute action, "
                                 "please include json attribute action.")
            elif len(errormsgs) == 0 and 'action' in obj:
                if obj['action'] == CASAS_ERROR:
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'error_type' not in obj['data']:
                            errormsgs.append("Could not obtain attribute error_type, "
                                             "please include json attribute data->error_type.")
                        if 'message' not in obj['data']:
                            errormsgs.append("Could not obtain attribute message, "
                                             "please include json attribute data->message.")
                        if 'error_dict' not in obj['data']:
                            errormsgs.append("Could not obtain attribute error_dict, "
                                             "please include json attribute data->error_dict.")
                    if len(errormsgs) == 0:
                        ce = CasasError(error_type=obj['data']['error_type'],
                                        message=obj['data']['message'],
                                        error_dict=obj['data']['error_dict'])
                        return_objects.append(copy.deepcopy(ce))
                elif obj['action'] == CASAS_RESPONSE:
                    error_list = list()
                    if 'status' not in obj:
                        errormsgs.append("Could not obtain attribute status, "
                                         "please include json attribute status.")
                    if 'type' not in obj:
                        errormsgs.append("Could not obtain attribute type, "
                                         "please include json attribute type.")
                    if 'error_message' not in obj:
                        errormsgs.append("Could not obtain attribute error_message, "
                                         "please include json attribute error_message.")
                    if 'error_list' not in obj:
                        errormsgs.append("Could not obtain attribute error_list, "
                                         "please include json attribute error_list.")
                    if len(errormsgs) == 0:
                        if len(obj['error_list']) > 0:
                            error_list = get_subobject_list(
                                casas_object=json.dumps(obj['error_list']),
                                errormsgs=errormsgs)
                    if len(errormsgs) == 0:
                        cr = CasasResponse(status=obj['status'],
                                           response_type=obj['type'],
                                           error_message=obj['error_message'],
                                           error_list=error_list)
                        return_objects.append(copy.deepcopy(cr))
                elif obj['action'] == CASAS_OBJ_LIST:
                    if 'data' not in obj:
                        errormsgs.append('Could not obtain attribute data, '
                                         'please include json attribute data.')
                    else:
                        if 'object_list' not in obj['data']:
                            errormsgs.append('Could not obtain attribute object_list, '
                                             'please include json attribute data->object_list.')
                    if len(errormsgs) == 0:
                        object_list = build_objects_from_json(
                            message=json.dumps(obj['data']['object_list']))
                        if len(object_list) > 0:
                            if not isinstance(object_list, CasasResponse):
                                for object_list_item in object_list:
                                    return_objects.append(copy.deepcopy(object_list_item))
                elif obj['action'] == CASAS_GET_OBJ:
                    if 'key' not in obj:
                        errormsgs.append('Could not obtain attribute key, '
                                         'please include json attribute key.')
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if 'site' not in obj:
                        errormsgs.append('Could not obtain attribute site, '
                                         'please include json attribute site.')
                    if 'data' not in obj:
                        errormsgs.append('Could not obtain attribute data, '
                                         'please include json attribute data.')
                    else:
                        if 'object' not in obj['data']:
                            errormsgs.append('Could not obtain attribute object, '
                                             'please include json attribute data->object.')
                    casas_obj = None
                    if len(errormsgs) == 0:
                        casas_obj = get_subobject(
                            casas_object='[{}]'.format(json.dumps(obj['data']['object'])),
                            errormsgs=errormsgs)
                    if len(errormsgs) == 0:
                        cgo = CasasGetObject(casas_object=casas_obj,
                                             key=obj['key'],
                                             secret=obj['secret'],
                                             site=obj['site'])
                        return_objects.append(copy.deepcopy(cgo))
                elif obj['action'] == CASAS_SET_OBJ:
                    if 'key' not in obj:
                        errormsgs.append('Could not obtain attribute key, '
                                         'please include json attribute key.')
                    if 'secret' not in obj:
                        errormsgs.append('Could not obtain attribute secret, '
                                         'please include json attribute secret.')
                    if 'site' not in obj:
                        errormsgs.append('Could not obtain attribute site, '
                                         'please include json attribute site.')
                    if 'data' not in obj:
                        errormsgs.append('Could not obtain attribute data, '
                                         'please include json attribute data.')
                    else:
                        if 'object' not in obj['data']:
                            errormsgs.append('Could not obtain attribute object, '
                                             'please include json attribute data->object.')
                    casas_obj = None
                    if len(errormsgs) == 0:
                        casas_obj = get_subobject(
                            casas_object='[{}]'.format(json.dumps(obj['data']['object'])),
                            errormsgs=errormsgs)
                    if len(errormsgs) == 0:
                        cso = CasasSetObject(casas_object=casas_obj,
                                             key=obj['key'],
                                             secret=obj['secret'],
                                             site=obj['site'])
                        return_objects.append(copy.deepcopy(cso))
                elif obj['action'] == TESTBED:
                    key = None
                    secret = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'description' not in obj['data']:
                            errormsgs.append("Could not obtain attribute description, "
                                             "please include json attribute data->description.")
                        if 'active' not in obj['data']:
                            errormsgs.append("Could not obtain attribute active, "
                                             "please include json attribute data->active.")
                        if 'timezone' not in obj['data']:
                            errormsgs.append("Could not obtain attribute timezone, "
                                             "please include json attribute data->timezone.")
                        if 'has_internet' not in obj['data']:
                            errormsgs.append("Could not obtain attribute has_internet, "
                                             "please include json attribute data->has_internet.")
                        if 'created_on_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute created_on_epoch, "
                                             "please include json attribute "
                                             "data->created_on_epoch.")
                        if 'last_seen_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute last_seen_epoch, "
                                             "please include json attribute data->last_seen_epoch.")
                        if 'first_event_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute first_event_epoch, "
                                             "please include json attribute "
                                             "data->first_event_epoch.")
                        if 'latest_event_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute latest_event_epoch, "
                                             "please include json attribute "
                                             "data->latest_event_epoch.")
                    if len(errormsgs) == 0:
                        t = Testbed(site=obj['site'],
                                    description=obj['data']['description'],
                                    active=obj['data']['active'],
                                    timezone=obj['data']['timezone'],
                                    has_internet=obj['data']['has_internet'],
                                    created_on=epoch_to_stamp(obj['data']['created_on_epoch']),
                                    last_seen=epoch_to_stamp(obj['data']['last_seen_epoch']),
                                    first_event=epoch_to_stamp(obj['data']['first_event_epoch']),
                                    latest_event=epoch_to_stamp(obj['data']['latest_event_epoch']))
                        t.key = key
                        t.secret = secret
                        return_objects.append(copy.deepcopy(t))
                elif obj['action'] == EVENT:
                    key = None
                    secret = None
                    request_id = None
                    request_size = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'channel' not in obj:
                        errormsgs.append("Could not obtain attribute channel, "
                                         "please include json attribute channel.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'category' not in obj['data']:
                            errormsgs.append("Could not obtain attribute category, "
                                             "please include json attribute data->category.")
                        if 'package_type' not in obj['data']:
                            errormsgs.append("Could not obtain attribute package_type, "
                                             "please include json attribute data->package_type.")
                        if 'epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute epoch, "
                                             "please include json attribute data->epoch.")
                        if 'sensor_type' not in obj['data']:
                            errormsgs.append("Could not obtain attribute sensor_type, "
                                             "please include json attribute data->sensor_type.")
                        if 'message' not in obj['data']:
                            errormsgs.append("Could not obtain attribute message, "
                                             "please include json attribute data->message.")
                        if 'target' not in obj['data']:
                            errormsgs.append("Could not obtain attribute target, "
                                             "please include json attribute data->target.")
                        if 'serial' not in obj['data']:
                            errormsgs.append("Could not obtain attribute serial, "
                                             "please include json attribute data->serial.")
                        if 'by' not in obj['data']:
                            errormsgs.append("Could not obtain attribute by, "
                                             "please include json attribute data->by.")
                        if 'uuid' not in obj['data']:
                            errormsgs.append("Could not obtain attribute uuid, "
                                             "please include json attribute data->uuid.")
                        else:
                            obj_uuid = obj['data']['uuid']
                    if 'request' in obj:
                        if 'id' in obj['request']:
                            request_id = obj['request']['id']
                        if 'size' in obj['request']:
                            request_size = obj['request']['size']

                    if len(errormsgs) == 0:
                        e = Event(category=obj['data']['category'],
                                  package_type=obj['data']['package_type'],
                                  sensor_type=obj['data']['sensor_type'],
                                  message=obj['data']['message'],
                                  target=obj['data']['target'],
                                  serial=obj['data']['serial'],
                                  by=obj['data']['by'],
                                  channel=obj['channel'],
                                  site=obj['site'],
                                  epoch=obj['data']['epoch'],
                                  uuid=obj['data']['uuid'],
                                  request_id=request_id,
                                  request_size=request_size)
                        e.key = key
                        e.secret = secret
                        return_objects.append(copy.deepcopy(e))

                elif obj['action'] == TAG:
                    key = None
                    secret = None
                    request_id = None
                    request_size = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'channel' not in obj:
                        errormsgs.append("Could not obtain attribute channel, "
                                         "please include json attribute channel.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'category' not in obj['data']:
                            errormsgs.append("Could not obtain attribute category, "
                                             "please include json attribute data->category.")
                        if 'package_type' not in obj['data']:
                            errormsgs.append("Could not obtain attribute package_type, "
                                             "please include json attribute data->package_type.")
                        if 'epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute epoch, "
                                             "please include json attribute data->epoch.")
                        if 'sensor_type' not in obj['data']:
                            errormsgs.append("Could not obtain attribute sensor_type, "
                                             "please include json attribute data->sensor_type.")
                        if 'message' not in obj['data']:
                            errormsgs.append("Could not obtain attribute message, "
                                             "please include json attribute data->message.")
                        if 'target' not in obj['data']:
                            errormsgs.append("Could not obtain attribute target, "
                                             "please include json attribute data->target.")
                        if 'serial' not in obj['data']:
                            errormsgs.append("Could not obtain attribute serial, "
                                             "please include json attribute data->serial.")
                        if 'by' not in obj['data']:
                            errormsgs.append("Could not obtain attribute by, "
                                             "please include json attribute data->by.")
                        if 'uuid' not in obj['data']:
                            errormsgs.append("Could not obtain attribute uuid, "
                                             "please include json attribute data->uuid.")
                        else:
                            obj_uuid = obj['data']['uuid']
                        if 'tag' not in obj['data']:
                            errormsgs.append("Could not obtain attribute tag, "
                                             "please include json attribute data->tag.")
                        else:
                            if 'created_by' not in obj['data']['tag']:
                                errormsgs.append("Could not obtain attribute created_by, "
                                                 "please include json attribute "
                                                 "data->tag->created_by.")
                            if 'experiment' not in obj['data']['tag']:
                                errormsgs.append("Could not obtain attribute experiment, "
                                                 "please include json attribute "
                                                 "data->tag->experiment.")
                            if 'dataset' not in obj['data']['tag']:
                                errormsgs.append("Could not obtain attribute dataset, "
                                                 "please include json attribute "
                                                 "data->tag->dataset.")
                            if 'label' not in obj['data']['tag']:
                                errormsgs.append("Could not obtain attribute label, "
                                                 "please include json attribute "
                                                 "data->tag->label.")
                            else:
                                if 'name' not in obj['data']['tag']['label']:
                                    errormsgs.append("Could not obtain attribute name, "
                                                     "please include json attribute "
                                                     "data->tag->label->name.")
                                if 'value' not in obj['data']['tag']['label']:
                                    errormsgs.append("Could not obtain attribute value, "
                                                     "please include json attribute "
                                                     "data->tag->label->value.")
                    if 'request' in obj:
                        if 'id' in obj['request']:
                            request_id = obj['request']['id']
                        if 'size' in obj['request']:
                            request_size = obj['request']['size']

                    if len(errormsgs) == 0:
                        t = Tag(category=obj['data']['category'],
                                package_type=obj['data']['package_type'],
                                sensor_type=obj['data']['sensor_type'],
                                message=obj['data']['message'],
                                target=obj['data']['target'],
                                serial=obj['data']['serial'],
                                by=obj['data']['by'],
                                channel=obj['channel'],
                                site=obj['site'],
                                epoch=obj['data']['epoch'],
                                uuid=obj['data']['uuid'],
                                created_by=obj['data']['tag']['created_by'],
                                label=obj['data']['tag']['label']['name'],
                                value=obj['data']['tag']['label']['value'],
                                dataset=obj['data']['tag']['dataset'],
                                experiment=obj['data']['tag']['experiment'],
                                request_id=request_id,
                                request_size=request_size)
                        t.key = key
                        t.secret = secret
                        return_objects.append(copy.deepcopy(t))

                elif obj['action'] == CONTROL:
                    key = None
                    secret = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'channel' not in obj:
                        errormsgs.append("Could not obtain attribute channel, "
                                         "please include json attribute channel.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'command' not in obj['data']:
                            errormsgs.append("Could not obtain attribute command, "
                                             "please include json attribute data->command.")
                        if 'value' not in obj['data']:
                            errormsgs.append("Could not obtain attribute value, "
                                             "please include json attribute data->value.")
                        if 'replyto' not in obj['data']:
                            errormsgs.append("Could not obtain attribute replyto, "
                                             "please include json attribute data->replyto.")
                        if 'cid' not in obj['data']:
                            errormsgs.append("Could not obtain attribute cid, "
                                             "please include json attribute data->cid.")
                        if 'response' not in obj['data']:
                            obj['data']['response'] = ""
                        if 'category' not in obj['data']:
                            errormsgs.append("Could not obtain attribute category, "
                                             "please include json attribute data->category.")
                        if 'epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute epoch, "
                                             "please include json attribute data->epoch.")
                        if 'target' not in obj['data']:
                            errormsgs.append("Could not obtain attribute target, "
                                             "please include json attribute data->target.")
                        if 'serial' not in obj['data']:
                            errormsgs.append("Could not obtain attribute serial, "
                                             "please include json attribute data->serial.")
                        if 'by' not in obj['data']:
                            errormsgs.append("Could not obtain attribute by, "
                                             "please include json attribute data->by.")
                        if 'uuid' not in obj['data']:
                            errormsgs.append("Could not obtain attribute uuid, "
                                             "please include json attribute data->uuid.")

                        obj['data']['package_type'] = "control"
                        obj['data']['sensor_type'] = "control"

                        if len(errormsgs) == 0:
                            c = Control(category=obj['data']['category'],
                                        target=obj['data']['target'],
                                        serial=obj['data']['serial'],
                                        by=obj['data']['by'],
                                        channel=obj['channel'],
                                        site=obj['site'],
                                        command=obj['data']['command'],
                                        value=obj['data']['value'],
                                        replyto=obj['data']['replyto'],
                                        cid=obj['data']['cid'],
                                        response=obj['data']['response'],
                                        package_type=obj['data']['package_type'],
                                        sensor_type=obj['data']['sensor_type'],
                                        message="",
                                        epoch=obj['data']['epoch'],
                                        uuid=obj['data']['uuid'])
                            c.key = key
                            c.secret = secret
                            return_objects.append(copy.deepcopy(c))
                elif obj['action'] == HEARTBEAT:
                    key = None
                    secret = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    new_heartbeat = Heartbeat(site=obj['site'])
                    if 'data' in obj:
                        if 'epoch' in obj['data']:
                            new_heartbeat.epoch = obj['data']['epoch']
                            new_heartbeat.validate_heartbeat()
                    new_heartbeat.key = key
                    new_heartbeat.secret = secret
                    return_objects.append(copy.deepcopy(new_heartbeat))
                elif obj['action'] == TRANSLATION:
                    translation_start_epoch = None
                    translation_end_epoch = None
                    key = None
                    secret = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'target' not in obj['data']:
                            errormsgs.append("Could not obtain attribute target, "
                                             "please include json attribute data->target.")
                        if 'sensor_1' not in obj['data']:
                            errormsgs.append("Could not obtain attribute sensor_1, "
                                             "please include json attribute data->sensor_1.")
                        if 'sensor_2' not in obj['data']:
                            errormsgs.append("Could not obtain attribute sensor_2, "
                                             "please include json attribute data->sensor_2.")

                        if 'start_epoch' in obj['data']:
                            translation_start_epoch = obj['data']['start_epoch']
                        if 'end_epoch' in obj['data']:
                            translation_end_epoch = obj['data']['end_epoch']

                    if len(errormsgs) == 0:
                        new_translation = Translation(site=obj['site'],
                                                      target=obj['data']['target'],
                                                      sensor_1=obj['data']['sensor_1'],
                                                      sensor_2=obj['data']['sensor_2'],
                                                      start_epoch=translation_start_epoch,
                                                      end_epoch=translation_end_epoch)
                        new_translation.key = key
                        new_translation.secret = secret
                        return_objects.append(copy.deepcopy(new_translation))
                elif obj['action'] == TRANSLATION_GRP:
                    key = None
                    secret = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'group_name' not in obj['data']:
                            errormsgs.append("Could not obtain attribute group_name, "
                                             "please include json attribute data->group_name.")
                        if 'translations' not in obj['data']:
                            errormsgs.append("Could not obtain attribute translations, "
                                             "please include json attribute data->translations.")
                    if len(errormsgs) == 0:
                        translations = list()
                        for translation in obj['data']['translations']:
                            translation_start_epoch = None
                            translation_end_epoch = None
                            if 'site' not in translation:
                                errormsgs.append("Could not obtain attribute site, "
                                                 "please include json attribute "
                                                 "data->translations->site.")
                            if 'data' not in translation:
                                errormsgs.append("Could not obtain attribute data, "
                                                 "please include json attribute "
                                                 "data->translations->data.")
                            else:
                                if 'target' not in translation['data']:
                                    errormsgs.append("Could not obtain attribute target, "
                                                     "please include json attribute "
                                                     "data->translations->data->target.")
                                if 'sensor_1' not in translation['data']:
                                    errormsgs.append("Could not obtain attribute sensor_1, "
                                                     "please include json attribute "
                                                     "data->translations->data->sensor_1.")
                                if 'sensor_2' not in translation['data']:
                                    errormsgs.append("Could not obtain attribute sensor_2, "
                                                     "please include json attribute "
                                                     "data->translations->data->sensor_2.")
                                if 'start_epoch' in translation['data']:
                                    translation_start_epoch = translation['data']['start_epoch']
                                if 'end_epoch' in translation['data']:
                                    translation_end_epoch = translation['data']['end_epoch']

                            if len(errormsgs) == 0:
                                new_translation = Translation(
                                    site=translation['site'],
                                    target=translation['data']['target'],
                                    sensor_1=translation['data']['sensor_1'],
                                    sensor_2=translation['data']['sensor_2'],
                                    start_epoch=translation_start_epoch,
                                    end_epoch=translation_end_epoch)
                                new_translation.key = key
                                new_translation.secret = secret
                                translations.append(copy.deepcopy(new_translation))

                        if len(errormsgs) == 0:
                            new_translation_group = TranslationGroup(
                                site=obj['site'],
                                group_name=obj['data']['group_name'],
                                translations=translations)
                            new_translation_group.key = key
                            new_translation_group.secret = secret
                            return_objects.append(copy.deepcopy(new_translation_group))
                elif obj['action'] == ALGORITHM:
                    key = None
                    secret = None
                    site = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' in obj:
                        site = obj['site']
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'name' not in obj['data']:
                            errormsgs.append("Could not obtain attribute name, "
                                             "please include json attribute data->name.")
                        if 'version_major' not in obj['data']:
                            errormsgs.append("Could not obtain attribute version_major, "
                                             "please include json attribute data->version_major.")
                        if 'version_minor' not in obj['data']:
                            errormsgs.append("Could not obtain attribute version_minor, "
                                             "please include json attribute data->version_minor.")

                    if len(errormsgs) == 0:
                        alg = Algorithm(name=obj['data']['name'],
                                        version_major=obj['data']['version_major'],
                                        version_minor=obj['data']['version_minor'])
                        alg.key = key
                        alg.secret = secret
                        alg.site = site
                        return_objects.append(copy.deepcopy(alg))
                elif obj['action'] == ALG_MODEL:
                    key = None
                    secret = None
                    site = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' in obj:
                        site = obj['site']
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'name' not in obj['data']:
                            errormsgs.append("Could not obtain attribute name, "
                                             "please include json attribute data->name.")
                        if 'filename' not in obj['data']:
                            errormsgs.append("Could not obtain attribute filename, "
                                             "please include json attribute data->filename.")
                        if 'configfile' not in obj['data']:
                            errormsgs.append("Could not obtain attribute configfile, "
                                             "please include json attribute data->configfile.")
                        if 'algorithm' not in obj['data']:
                            errormsgs.append("Could not obtain attribute algorithm, "
                                             "please include json attribute data->algorithm.")
                        else:
                            if 'name' not in obj['data']['algorithm']:
                                errormsgs.append("Could not obtain attribute name, "
                                                 "please include json attribute "
                                                 "data->algorithm->name.")
                            if 'version_major' not in obj['data']['algorithm']:
                                errormsgs.append("Could not obtain attribute version_major, "
                                                 "please include json attribute "
                                                 "data->algorithm->version_major.")
                            if 'version_minor' not in obj['data']['algorithm']:
                                errormsgs.append("Could not obtain attribute version_minor, "
                                                 "please include json attribute "
                                                 "data->algorithm->version_minor.")

                    if len(errormsgs) == 0:
                        alg = Algorithm(name=obj['data']['algorithm']['name'],
                                        version_major=obj['data']['algorithm']['version_major'],
                                        version_minor=obj['data']['algorithm']['version_minor'])
                        alg.key = key
                        alg.secret = secret
                        alg.site = site

                        alg_mod = AlgorithmModel(name=obj['data']['name'],
                                                 filename=obj['data']['filename'],
                                                 configfile=obj['data']['configfile'],
                                                 algorithm=alg)
                        alg_mod.key = key
                        alg_mod.secret = secret
                        alg_mod.site = site
                        return_objects.append(copy.deepcopy(alg_mod))
                elif obj['action'] == ALG_PROCESSOR:
                    key = None
                    secret = None
                    algorithm = None
                    algorithm_model = None
                    translation_group = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'algorithm' not in obj['data']:
                            errormsgs.append("Could not obtain attribute algorithm, "
                                             "please include json attribute data->algorithm.")
                        if 'algorithm_model' not in obj['data']:
                            errormsgs.append("Could not obtain attribute algorithm_model, "
                                             "please include json attribute data->algorithm_model.")
                        if 'translation_group' not in obj['data']:
                            errormsgs.append("Could not obtain attribute translation_group, "
                                             "please include json attribute "
                                             "data->translation_group.")
                        if 'upload_key' not in obj['data']:
                            errormsgs.append("Could not obtain attribute upload_key, "
                                             "please include json attribute data->upload_key.")
                        if 'upload_secret' not in obj['data']:
                            errormsgs.append("Could not obtain attribute upload_secret, "
                                             "please include json attribute data->upload_secret.")
                        if 'use_live_data' not in obj['data']:
                            errormsgs.append("Could not obtain attribute use_live_data, "
                                             "please include json attribute data->use_live_data.")
                        if 'use_historic_data' not in obj['data']:
                            errormsgs.append("Could not obtain attribute use_historic_data, "
                                             "please include json attribute "
                                             "data->use_historic_data.")
                        if 'start_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute start_epoch, "
                                             "please include json attribute data->start_epoch.")
                        if 'end_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute end_epoch, "
                                             "please include json attribute data->end_epoch.")
                        if 'current_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute current_epoch, "
                                             "please include json attribute data->current_epoch.")
                        if 'processing_historic_data' not in obj['data']:
                            errormsgs.append("Could not obtain json attribute "
                                             "processing_historic_data, "
                                             "please include json attribute "
                                             "data->processing_historic_data.")
                        if 'is_active' not in obj['data']:
                            errormsgs.append("Could not obtain attribute is_active, "
                                             "please include json attribute data->is_active.")

                    if len(errormsgs) == 0:
                        algorithm = get_subobject(
                            casas_object="[{}]".format(json.dumps(obj['data']['algorithm'])),
                            errormsgs=errormsgs)
                        algorithm_model = get_subobject(
                            casas_object="[{}]".format(json.dumps(obj['data']['algorithm_model'])),
                            errormsgs=errormsgs)
                        translation_group = get_subobject(
                            casas_object="[{}]".format(
                                json.dumps(obj['data']['translation_group'])),
                            errormsgs=errormsgs)

                    if len(errormsgs) == 0:
                        start_stamp = None
                        end_stamp = None
                        current_stamp = None
                        if obj['data']['start_epoch'] is not None:
                            start_stamp = datetime.datetime.utcfromtimestamp(
                                float(obj['data']['start_epoch']))
                            start_stamp = start_stamp.replace(tzinfo=pytz.utc)
                        if obj['data']['end_epoch'] is not None:
                            end_stamp = datetime.datetime.utcfromtimestamp(
                                float(obj['data']['end_epoch']))
                            end_stamp = end_stamp.replace(tzinfo=pytz.utc)
                        if obj['data']['current_epoch'] is not None:
                            current_stamp = datetime.datetime.utcfromtimestamp(
                                float(obj['data']['current_epoch']))
                            current_stamp = current_stamp.replace(tzinfo=pytz.utc)
                        ap = AlgorithmProcessor(
                            algorithm=algorithm,
                            algorithm_model=algorithm_model,
                            translation_group=translation_group,
                            site=obj['site'],
                            key=obj['data']['upload_key'],
                            secret=obj['data']['upload_secret'],
                            use_live_data=obj['data']['use_live_data'],
                            use_historic_data=obj['data']['use_historic_data'],
                            start_stamp=start_stamp,
                            end_stamp=end_stamp,
                            current_stamp=current_stamp,
                            processing_historic_data=obj['data']['processing_historic_data'],
                            is_active=obj['data']['is_active'])
                        ap.key = key
                        ap.secret = secret
                        return_objects.append(copy.deepcopy(ap))
                elif obj['action'] == ALG_PROC_REQUEST:
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'algorithm_name' not in obj['data']:
                            errormsgs.append("Could not obtain attribute algorithm_name, "
                                             "please include json attribute data->algorithm_name.")
                        if 'version_major' not in obj['data']:
                            errormsgs.append("Could not obtain attribute version_major, "
                                             "please include json attribute data->version_major.")
                        if 'version_minor' not in obj['data']:
                            errormsgs.append("Could not obtain attribute version_minor, "
                                             "please include json attribute data->version_minor.")
                        if 'algorithm_model_name' not in obj['data']:
                            errormsgs.append("Could not obtain attribute algorithm_model_name, "
                                             "please include json attribute "
                                             "data->algorithm_model_name.")

                    if len(errormsgs) == 0:
                        apr = AlgorithmProcessorRequest(
                            algorithm_name=obj['data']['algorithm_name'],
                            version_major=obj['data']['version_major'],
                            version_minor=obj['data']['version_minor'],
                            algorithm_model_name=obj['data']['algorithm_model_name'])
                        return_objects.append(copy.deepcopy(apr))
                elif obj['action'] == ALG_PROC_UPDATE:
                    algorithm_processor = None
                    new_algorithm = None
                    new_algorithm_model = None
                    new_translation_group = None
                    new_upload_key = None
                    new_upload_secret = None
                    new_use_live_data = None
                    new_use_historic_data = None
                    new_start_stamp = None
                    new_end_stamp = None
                    new_current_stamp = None
                    new_processing_historic_data = None
                    new_is_active = None
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'algorithm_processor' not in obj['data']:
                            errormsgs.append("Could not obtain attribute algorithm_processor, "
                                             "please include json attribute "
                                             "data->algorithm_processor.")
                        if 'algorithm' in obj['data']:
                            new_algorithm = get_subobject(
                                casas_object="[{}]".format(
                                    json.dumps(obj['data']['algorithm'])),
                                errormsgs=errormsgs)
                        if 'algorithm_model' in obj['data']:
                            new_algorithm_model = get_subobject(
                                casas_object="[{}]".format(
                                    json.dumps(obj['data']['algorithm_model'])),
                                errormsgs=errormsgs)
                        if 'translation_group' in obj['data']:
                            new_translation_group = get_subobject(
                                casas_object="[{}]".format(
                                    json.dumps(obj['data']['translation_group'])),
                                errormsgs=errormsgs)
                        if 'upload_key' in obj['data']:
                            new_upload_key = obj['data']['upload_key']
                        if 'upload_secret' in obj['data']:
                            new_upload_secret = obj['data']['upload_secret']
                        if 'use_live_data' in obj['data']:
                            new_use_live_data = obj['data']['use_live_data']
                        if 'use_historic_data' in obj['data']:
                            new_use_historic_data = obj['data']['use_historic_data']
                        if 'start_epoch' in obj['data']:
                            new_start_stamp = datetime.datetime.utcfromtimestamp(
                                float(obj['data']['start_epoch']))
                            new_start_stamp = new_start_stamp.replace(tzinfo=pytz.utc)
                        if 'end_epoch' in obj['data']:
                            new_end_stamp = datetime.datetime.utcfromtimestamp(
                                float(obj['data']['end_epoch']))
                            new_end_stamp = new_end_stamp.replace(tzinfo=pytz.utc)
                        if 'current_epoch' in obj['data']:
                            new_current_stamp = datetime.datetime.utcfromtimestamp(
                                float(obj['data']['current_epoch']))
                            new_current_stamp = new_current_stamp.replace(tzinfo=pytz.utc)
                        if 'processing_historic_data' in obj['data']:
                            new_processing_historic_data = obj['data']['processing_historic_data']
                        if 'is_active' in obj['data']:
                            new_is_active = obj['data']['is_active']

                    if len(errormsgs) == 0:
                        algorithm_processor = get_subobject(
                            casas_object="[{}]".format(
                                json.dumps(obj['data']['algorithm_processor'])),
                            errormsgs=errormsgs)
                    if len(errormsgs) == 0:
                        apu = AlgorithmProcessorUpdate(
                            algorithm_processor=algorithm_processor,
                            new_algorithm=new_algorithm,
                            new_algorithm_model=new_algorithm_model,
                            new_translation_group=new_translation_group,
                            new_upload_key=new_upload_key,
                            new_upload_secret=new_upload_secret,
                            new_use_live_data=new_use_live_data,
                            new_use_historic_data=new_use_historic_data,
                            new_start_stamp=new_start_stamp,
                            new_end_stamp=new_end_stamp,
                            new_current_stamp=new_current_stamp,
                            new_processing_historic_data=new_processing_historic_data,
                            new_is_active=new_is_active)
                        return_objects.append(copy.deepcopy(apu))
                elif obj['action'] == CIL_BASE:
                    key = None
                    secret = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'is_ready' not in obj['data']:
                            errormsgs.append("Could not obtain attribute is_ready, "
                                             "please include json attribute data->is_ready.")
                        if 'start_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute start_epoch, "
                                             "please include json attribute data->start_epoch.")
                        if 'end_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute end_epoch, "
                                             "please include json attribute data->end_epoch.")

                    if len(errormsgs) == 0:
                        start_stamp = datetime.datetime.utcfromtimestamp(
                            float(obj['data']['start_epoch']))
                        start_stamp = start_stamp.replace(tzinfo=pytz.utc)
                        end_stamp = datetime.datetime.utcfromtimestamp(
                            float(obj['data']['end_epoch']))
                        end_stamp = end_stamp.replace(tzinfo=pytz.utc)
                        cb = CilBaseline(site=obj['site'],
                                         is_ready=obj['data']['is_ready'],
                                         start_stamp=start_stamp,
                                         end_stamp=end_stamp)
                        cb.key = key
                        cb.secret = secret
                        return_objects.append(copy.deepcopy(cb))
                elif obj['action'] == CIL_METRIC:
                    key = None
                    secret = None
                    site = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' in obj:
                        site = obj['site']
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'name' not in obj['data']:
                            errormsgs.append("Could not obtain attribute name, "
                                             "please include json attribute data->name.")

                    if len(errormsgs) == 0:
                        cm = CilMetric(name=obj['data']['name'])
                        cm.key = key
                        cm.secret = secret
                        cm.site = site
                        return_objects.append(copy.deepcopy(cm))
                elif obj['action'] == CIL_BASE_METRIC:
                    key = None
                    secret = None
                    site = None
                    baseline = None
                    metric = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' in obj:
                        site = obj['site']
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'baseline' not in obj['data']:
                            errormsgs.append("Could not obtain attribute baseline, "
                                             "please include json attribute data->baseline.")
                        if 'metric' not in obj['data']:
                            errormsgs.append("Could not obtain attribute metric, "
                                             "please include json attribute data->metric.")
                        if '0.5_std' not in obj['data']:
                            errormsgs.append("Could not obtain attribute 0.5_std, "
                                             "please include json attribute data->0.5_std.")
                        if '1.0_std' not in obj['data']:
                            errormsgs.append("Could not obtain attribute 1.0_std, "
                                             "please include json attribute data->1.0_std.")
                        if '1.5_std' not in obj['data']:
                            errormsgs.append("Could not obtain attribute 1.5_std, "
                                             "please include json attribute data->1.5_std.")

                    if len(errormsgs) == 0:
                        baseline = get_subobject(
                            casas_object="[{}]".format(json.dumps(obj['data']['baseline'])),
                            errormsgs=errormsgs)
                        metric = get_subobject(
                            casas_object="[{}]".format(json.dumps(obj['data']['metric'])),
                            errormsgs=errormsgs)

                    if len(errormsgs) == 0:
                        cbm = CilBaselineMetric(baseline=baseline,
                                                metric=metric,
                                                value_zero_five_std=obj['data']['0.5_std'],
                                                value_one_std=obj['data']['1.0_std'],
                                                value_one_five_std=obj['data']['1.5_std'])
                        cbm.key = key
                        cbm.secret = secret
                        cbm.site = site
                        return_objects.append(copy.deepcopy(cbm))
                elif obj['action'] == CIL_DATA:
                    key = None
                    secret = None
                    metric = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'metric' not in obj['data']:
                            errormsgs.append("Could not obtain attribute metric, "
                                             "please include json attribute data->metric.")
                        if 'value' not in obj['data']:
                            errormsgs.append("Could not obtain attribute value, "
                                             "please include json attribute data->value.")
                        if 'epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute epoch, "
                                             "please include json attribute data->epoch.")

                    if len(errormsgs) == 0:
                        metric = get_subobject(
                            casas_object="[{}]".format(json.dumps(obj['data']['metric'])),
                            errormsgs=errormsgs)

                    if len(errormsgs) == 0:
                        stamp = datetime.datetime.utcfromtimestamp(float(obj['data']['epoch']))
                        stamp = stamp.replace(tzinfo=pytz.utc)
                        cd = CilData(site=obj['site'],
                                     metric=metric,
                                     value=obj['data']['value'],
                                     stamp=stamp)
                        cd.key = key
                        cd.secret = secret
                        return_objects.append(copy.deepcopy(cd))
                elif obj['action'] == REQUEST_EVENTS:
                    key = None
                    secret = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'start_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute start_epoch, "
                                             "please include json attribute data->start_epoch.")
                        if 'end_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute end_epoch, "
                                             "please include json attribute data->end_epoch.")
                        if 'sensor_types' not in obj['data']:
                            errormsgs.append("Could not obtain attribute sensor_types, "
                                             "please include json attribute data->sensor_types.")

                    if len(errormsgs) == 0:
                        start_stamp = datetime.datetime.utcfromtimestamp(
                            float(obj['data']['start_epoch']))
                        start_stamp = start_stamp.replace(tzinfo=pytz.utc)
                        end_stamp = datetime.datetime.utcfromtimestamp(
                            float(obj['data']['end_epoch']))
                        end_stamp = end_stamp.replace(tzinfo=pytz.utc)
                        try:
                            reqev = RequestEvents(site=obj['site'],
                                                  start_stamp=start_stamp,
                                                  end_stamp=end_stamp,
                                                  sensor_types=obj['data']['sensor_types'])
                            reqev.key = key
                            reqev.secret = secret
                            return_objects.append(copy.deepcopy(reqev))
                        except ValueError as e:
                            errormsgs.append(str(e))
                elif obj['action'] == REQUEST_DATASET:
                    key = None
                    secret = None
                    if 'key' in obj:
                        key = obj['key']
                    if 'secret' in obj:
                        secret = obj['secret']
                    if 'site' not in obj:
                        errormsgs.append("Could not obtain attribute site, "
                                         "please include json attribute site.")
                    if 'data' not in obj:
                        errormsgs.append("Could not obtain attribute data, "
                                         "please include json attribute data.")
                    else:
                        if 'start_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute start_epoch, "
                                             "please include json attribute data->start_epoch.")
                        if 'end_epoch' not in obj['data']:
                            errormsgs.append("Could not obtain attribute end_epoch, "
                                             "please include json attribute data->end_epoch.")
                        if 'experiment' not in obj['data']:
                            errormsgs.append("Could not obtain attribute experiment, "
                                             "please include json attribute data->experiment.")
                        if 'dataset' not in obj['data']:
                            errormsgs.append("Could not obtain attribute dataset, "
                                             "please include json attribute data->dataset.")
                        if 'sensor_types' not in obj['data']:
                            errormsgs.append("Could not obtain attribute sensor_types, "
                                             "please include json attribute data->sensor_types.")

                    if len(errormsgs) == 0:
                        start_stamp = datetime.datetime.utcfromtimestamp(
                            float(obj['data']['start_epoch']))
                        start_stamp = start_stamp.replace(tzinfo=pytz.utc)
                        end_stamp = datetime.datetime.utcfromtimestamp(
                            float(obj['data']['end_epoch']))
                        end_stamp = end_stamp.replace(tzinfo=pytz.utc)
                        try:
                            reqds = RequestDataset(site=obj['site'],
                                                   start_stamp=start_stamp,
                                                   end_stamp=end_stamp,
                                                   experiment=obj['data']['experiment'],
                                                   dataset=obj['data']['dataset'],
                                                   sensor_types=obj['data']['sensor_types'])
                            reqds.key = key
                            reqds.secret = secret
                            return_objects.append(copy.deepcopy(reqds))
                        except ValueError as e:
                            errormsgs.append(str(e))

            if len(errormsgs) > 0:
                response.add_error(
                    casas_error=CasasError(error_type='data',
                                           message="There were errors processing part or all of "
                                                   "your data, please see error_dict for details.",
                                           error_dict=dict({'element': element_id,
                                                            'uuid': obj_uuid,
                                                            'error': ' | '.join(errormsgs)})))
                # response['status'] = 'error'
                # response['errormessage'] = ("There were errors processing part or all of your "
                #                             "event data, please see errors for details")
                # response['errors'].append(dict({'element': element_id,
                #                                 'uuid': obj_uuid,
                #                                 'error': ' | '.join(errormsgs)}))
                log.error("Error processing message: " + response.error_list[-1].get_json())
            element_id += 1

    except TypeError as e:
        log.error("JSON TYPE ERROR: " + str(e))
        response.add_error(
            error_type='json',
            casas_error=CasasError(error_type='json',
                                   message='TypeError: The conversion of JSON failed possibly due '
                                           'to improperly formatted JSON set in the message.',
                                   error_dict=dict({'error': str(e)})))
        # response['status'] = 'error'
        # response['type'] = 'json'
        # response['errormessage'] = ("The conversion of JSON failed "
        #                             "possibly due to improperly formatted JSON in the message.")
        # response['errors'].append(str(e))
        log.debug(message)
        log.warning(response.get_json())
    except ValueError as e:
        log.error("JSON VALUE ERROR: " + str(e))
        response.add_error(
            error_type='json',
            casas_error=CasasError(error_type='json',
                                   message='ValueError: The conversion of JSON failed possibly due '
                                           'to improperly formatted JSON set in the message.',
                                   error_dict=dict({'error': str(e)})))
        # response['status'] = 'error'
        # response['type'] = 'json'
        # response['errormessage'] = ("The conversion of JSON failed "
        #                             "possibly due to improperly formatted JSON set in the message.")
        # response['errors'].append(str(e))
        log.debug(message)
        log.warning(response.get_json())

    if response.status != 'success':
        return_objects.append(copy.deepcopy(response))
    return return_objects


def get_subobject(casas_object, errormsgs):
    log.debug("get_subobject( {} )".format(str(casas_object)))
    new_object = None
    values = build_objects_from_json(casas_object)
    if isinstance(values, list):
        if len(values) > 0:
            new_object = values[0]
        else:
            errormsgs.append("There were errors processing a sub-object in your json data, "
                             "no objects were returned.")
    else:
        errormsgs.append("There errors processing a sub-object in your json data, "
                         "the error messages are appended.")
        errormsgs.append(json.dumps(values))
    return new_object


def get_subobject_list(casas_object, errormsgs):
    log.debug("get_subobject( {} )".format(str(casas_object)))
    new_object_list = list()
    values = build_objects_from_json(casas_object)
    valid = False
    if isinstance(values, list):
        if len(values) > 0:
            if not isinstance(values[0], CasasResponse):
                valid = True
            else:
                errormsgs.append("There were errors processing a sub-object in your json data, "
                                 "the error messages are appended.")
                for item in values:
                    errormsgs.append(item.get_json())
        else:
            errormsgs.append("There were errors processing a sub-object in your json data, "
                             "no objects were returned.")
    else:
        errormsgs.append("There errors processing a sub-object in your json data, "
                         "the error messages are appended.")
        errormsgs.append(json.dumps(values))
    if valid:
        new_object_list = values
    return new_object_list
