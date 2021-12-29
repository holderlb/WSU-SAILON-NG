# Installing and Running Novelty Generator

This package provides a sample TA2 client, configuation file, and auxiliary files
for interacting with the WSU SAIL-ON Novelty Generator (NG). The client
connects to the NG server and calls various methods in the TA2Agent class.

The SAIL-ON NG is a variant of the WSU AIQ testing facility, so some references
to AIQ appear.

Contact Larry Holder (holder@wsu.edu) for more information.

## Table of Contents
* [Installation](#installation)
* [Configuration File](#configurationfile)
* [Running the Client](#runningtheclient)
* [Running Modes](#runningmodes)
* [Program Flow](#programflow)
* [TA2 Agent](#ta2agent)

<a name="installation">

## Installation

The package is available here in the src directory. The code requires
some Python setup, which we describe below based on the Anaconda environment.

1. Install Anaconda.

2.  Activate the base Anaconda environment.
```
[user@host ~]$ source ~/anaconda3/bin/activate
```
3.  Ensure your base environment is up to date:
```
(base) [user@host ~]$ conda update -n base -c defaults conda
```
4.  Create a new environment with the basic versions.
```
(base) [user@host ~]$ conda create --name aiq-env python=3.7 python-dateutil==2.8.1 psutil pytz numpy
```
5.  Activate the new environment so we can finish installing the remaining packages.
```
(base) [user@host ~]$ conda activate aiq-env
```
6.  Install the remaining packages with pip.
```
(aiq-env) [user@host ~]$ pip install pika==1.1.0 blosc==1.10.4
```

<a name="configurationfile">

## Configuration File

The configuration file has three sections: `aiq-sail-on`, `sail-on`, and
`amqp`.  See `demo-client.config` for an example. This demo config works now,
but only provides a small set of novelty level 0 data. To run an actual
experiment with all novelty levels, contact us for different credentials.

### [aiq-sail-on]

*  `experiment_type` selects the type of experiment to run, `SAIL-ON` is the
    only valid experiment type currently supported.

*  `organization` is an identifier for your organization or university, this
    is associated with the experiments you run.

*  `model_name` is the identifier for your model.  This allows you to keep
    track of multiple models.

*  `username` is the email address/login for the system website (under
    construction).

*  `secret` is a secret separate from your website password that is provided
    to allow for authentication.  Once the website is complete you will be able
    to request new values for this if you compromise the previous value.

*  `description` is an optional field that will be recorded and associated
    with the experiment instance that is run.
    
* `seed` is an optional integer that will provide the random seed used when building an experiment
    so that you can always build the same experiment.

* `episode_seed` is an optional integer that will overwrite the experiment setting and force EVERY
    episode to use this seed value.

* `start_zeroed_out` is an optional boolean (default=`False`) for the CartPole domain that will
    have your cart physics start zeroed out when set to `True`.

* `start_world_state` is an optional JSON string that is converted to a dictionary representing the
    starting world state for the CartPole domain.  The string is converted using `json.loads(val)`
    and will throw an exception if the string is not a valid dictionary.

### [sail-on]

*  `domain` selects which domain you would like to test on.  The current
    available domains are `cartpole`, `vizdoom` and `smartenv`.

*  `experiment_secret` is a secret generated when a new experiment is created.  This field is
    optional if you just wish to run the system in a single linear experiment, but is required
    if you wish to run additional TA2 agents to help process trials.  The TA2 agent automatically
    updates the config file with this value once the experiment is created.  Please see the
    section [Running Modes](#runningmodes) for information on how this entry interacts
    with `no_testing` and `just_one_trial` for TA2 agent behavior.  Passing in the command line
    argument `--ignore-secret` will have the TA2 agent behave as if `experiment_secret` is not
    defined.

*  `no_testing` is an optional boolean (default=`False`) that is used for informing the TA1 that
    this TA2 does not wish to begin the testing phase of the experiment, instead it will cleanly
    exit after creating the experiment, saving the `experiment_secret` in the config file,
    processing any training episodes, and optionally training the model if needed by your domain.
    Please see the section [Running Modes](#runningmodes) for information on how this
    entry interacts with `no_testing` and `just_one_trial` for TA2 agent behavior.  The config
    file value can be overridden to `True` by passing `--no-testing` as a command line argument. 

*  `just_one_trial` is an optional boolean (default=`False`) that is used for informing the TA1
    that this TA2 should process one trial for the given `experiment_secret`.  If the entry for
    `experiment_secret` is not defined, setting `just_one_trial = True` will result in an
    exception being raised and the program exiting.  Please see the section
    [Running Modes](#runningmodes) for information on how this entry interacts with
    `no_testing` and `just_one_trial` for TA2 agent behavior.  The config file value can be
    overridden to `True` by passing `--just-one-trial` as a command line argument.

### [amqp]

*  `user` is the username for authenticating to our RabbitMQ server.

*  `pass` is the password for authenticating to our RabbitMQ server.

*  `host` is the hostname for our RabbitMQ server, `aiq.ailab.wsu.edu`.

*  `vhost` is the optional vhost to connect to on our RabbitMQ server.

*  `port` is the port on our RabbitMQ server to connect to, `5671`.

*  `ssl` is a boolean identifying if the client will use the SSL connection.

<a name="runningtheclient">

## Running the Client

To run the client on the provided `demo-client.config` configuration file, do the following.
1. Ensure that you are in the conda environment initialized above (e.g., `aiq-env`).
2. Run the TA2 client in default mode.
```
(aiq-env) [user@host client]$ python TA2.py --config=demo-client.config --printout --debug --logfile=log.txt
```
All command line arguments are described with `python TA2.py --help`.

<a name="runningmodes">

## Running Modes

There are 4 differnt modes the TA2 can run in, here are the variations using the new config values:

`experiment_secret` | `no_testing` | `just_one_trial` | Behavior
--- | --- | --- | ---
Not Defined | False | True | **Exception Thrown**
Not Defined | False | False | Mode #1 - Full Linear Experiment
\* | True | * | Mode #2 - No Testing
Defined | False | True | Mode #3 - Just One Trial
Defined | False | False | Mode #4 - Trials Until Done

For Mode #3 and Mode #4, if the experiment is complete you will receive an error message that the
experiment is already complete before cleanly exiting.  None of the functions (other than
`__init__()`) in TA2.py will be called when this happens, a function can be added requested.

<a name="runmodeone">

### Mode #1 - Full Linear Experiment

**Full linear experiment** runs the full experiment in linear fashion.

* Create experiment in database.
* Iterate through training episodes.
* Train model.
* Iterate through experiment trials.

#### Example Use

This assumes `experiment_secret` is either not defined in the config file or you add the
`--ignore-secret` flag to the command line.
```
(aiq-env) [user@host client]$ python TA2.py --config=demo-client.config --printout
```

<a name="runmodetwo">

### Mode #2 - No Testing

**No testing** informs the TA1 that the TA2 does not with to iterate through the trials on this
connection.  This is intended for use in creating the experiment before starting multiple TA2
instances running in Modes [#3](#runmodethree) or [#4](#runmodefour).

* Create experiment in database.
* Iterate through training episodes.
* Train model.

#### Example Use

Here we initially run in Mode #2 to go through any training data, if needed, and training of the
model.
```
(aiq-env) [user@host client]$ python TA2.py --config=demo-client.config --printout --no-testing
```
After this runs the `experiment_secret` has been updated in the config file, and we can now use
this config (and a trained model) to run in Mode #3 or Mode #4, with just one instance or many
at the same time.

<a name="runmodethree">

### Mode #3 - Just One Trial

**Just one trial** informs the TA1 that the TA2 only wants to process a single trial from the
defined `experiment_secret` and then cleanly exit.  This is intended for running multiple
versions of TA2 on a cluster using a job queue with a limited runtime.

* Process a single experiment trial.

#### Example Use

This requires that `experiment_secret` is set in the config file, if not it will throw an exception.
```
(aiq-env) [user@host client]$ python TA2.py --config=demo-client.config --printout --just-one-trial
```

<a name="runmodefour">

### Mode #4 - Trials Until Done

**Trials until done** informs the TA1 that the TA2 would like to process trials from the defined
`experiment_secret` until there are no more trials available for the given experiment.

In order to deal with the potential of a TA2 crashing or disconnecting before completing a trial,
the TA1 will delete the work for a trial and make it available for the next TA2 requesting work if
there has been no update to the progress of a given trial in an hour.  An experiment is only marked
complete when all trials in that experiment are marked as complete.  There is currently no
method for providing feedback on if an experiment is complete or if there are no more trials
currently available to process, this may be considered in a future version if requested.

* Iterate through experiment trials.

#### Example Use

This requires that `experiment_secret` is set in the config file, if not it will actually run in
Mode #1 and create a new experiment.
```
(aiq-env) [user@host client]$ python TA2.py --config=demo-client.config --printout
```

<a name="programflow">

## Program Flow

Running the client results in the following program flow. As the client enters different phases of 
the experiment, the corresponding method in the TA2Agent class is called.

*  The client connects to the RabbitMQ server and requests to start an
    experiment.

*  The server requests benchmarking information and waits for the results. Currently, this is just 
   hardware information from the client, but eventually will be a benchmarking script.

*  The experiment starts!

*  Training begins.

*  For `episode` in `training episodes`:

    *  For `feature vector` in `episode`:

        *  Train on `feature vector` and return `prediction`.

*  Training is over, you may optionally train your model here.

*  TA2 should save the current state of the model so you can revert back to this
    state at the start of each trial.

*  For `novelty` in `novelty levels`:

    * For `difficulty` in `difficulty levels`:

        *  For `novelty_visibility` in [`no visibility`, `novelty visible`]:
        
            * Testing begins.

            *  For `trial` in `number of trials`:

                *  TA2 should reset the model to the saved state at this point.

                *  For `episode` in `testing episodes`:

                    *  For `feature vector` in `episode`:

                        *  Evaluate `feature vector` and return your `prediction`.

            *  Testing ends.

*  The experiment concludes!

*  Analysis scripts will run with results being made available on the website.
    This is currently under construction and we will be emailing results
    while the website is completed.

<a name="ta2agent">

## TA2 Agent

The sample TA2 client in `TA2.py` provides stubs for the methods that are
called for each of the different phases of the program flow above. This is
where you implement your TA2/AI agent. See the documentation comments on these
methods in the `TA2.py` file.

