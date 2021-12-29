# Table of Contents
* [Quick Start](#quickstart)
* [Mock Novelty](#mocknovelty)
* [TA1 Configuration File](#ta1configurationfile)
* [TA2 Configuration File](#ta2configurationfile)
* [TA2 Running Modes](#runningmodes)
* [Program Flow](#programflow)
* [TA2 Agent](#ta2agent)
    * [TA2 in Docker](#ta2docker)
    * [External TA2 Agent](#ta2external)
    * [TA2 GUI Agents](#ta2gui)

<a name="quickstart">

# Quick Start

Run the full package with the demo TA2.py agent.
```
docker-compose -f portable-generator.yml build
docker-compose -f portable-generator.yml up
```
When you are done, ctrl-C to exit, then run
```
docker-compose -f portable-generator.yml down
```
to clean up the containers.


**NOTE** Make sure the `experiment_secret` line in the `configs/partial/demo-client.config` config
file is removed before you start a new experiment.


You can run multiple TA1, GENERATOR, and TA2 agents with a single postgres container using the --scale
argument when using the `up` command.
```
docker-compose -f portable-generator.yml up -d --scale mockn-ta1=3 --scale mockn-gen-vizdoom=3 --scale mockn-demo-ta2=3
```

Then to watch the output use the logs command.
```
docker-compose -f portable-generator.yml logs -f --tail=10
```

And as before, when you are done run the down command to clean up the containers.
```
docker-compose -f portable-generator.yml down
```

<a name="changelog">

# Change Log

## v0.7.9

* Moved `episode_seed` definition from inside TA2.py to the config file.
* Moved `start_zeroed_out` definition from inside TA2.py to the config file.
* Moved `start_world_state` definition from inside TA2.py to the config file.

## v0.7.3

### CartPole

* Reduced applied force to 10
* Decreased initial cart force from [-50, 50] to [-1, 1]
* Decreased initial pole angle from [-0.05, 0.05] to [-0.01, 0.01]
* Removed friction from pole-to-cart joint
* Fixed Push force being applied oddly
* Fixed gui being enabled by default
* Removed extra print statement for argvs

### ViZDoom

* Revamped enemy movement to be instantaneous.
* Obstacles are more circular so running along side it will sometimes not work.  
* Obstacles will no longer spawn close together.
* Enemies with shoot command act first, then enemies with move commands.
* Fixed enemies getting swapped with each other.
* Fixed enemies having ghosts sometimes.
* Fixed enemies not acting sometimes.
* Fixed game ending incorrectly when monster 1 then monster 2 was killed.
* Fixed distance calculation for enemies not shooting each other.

<a name="mocknovelty">

# Mock Novelty

### Cartpole

The code for mock novelty and three levels of difficulty for cartpole are located in
`source/partial_env_generator/envs/cartpolepp/m_[novelty].py`.  If you wish to introduce your own
novelties, you may edit that code.

### Vizdoom

The simulator configurations for mock novelty and three levels of difficulty for vizdoom are
located in `source/partial_env_generator/envs/vizdoom/phase_2_reduced.wad`.  You may edit those
configuration files to introduce your own novelties.


<a name="ta1configurationfile">

# TA1 Configuration File

You can change some of the experiment parameters using the `configs/partial/TA1.config` config file.

* `[sail-on].trials` (int) changes the number of trials per novelty/difficulty/visibility
  combination. The *total* number of trials in an experiment is
  ```
  total_trials = trials * len(novelty) * len(difficulty) * 2
  ```
  The last `2` represents the visibility of the novelty (if the TA2 is informed of the novelty
  having been initiated or not) and is currently not configurable.
* `[sail-on].novelty` (comma separated list) are the novelties the TA1 will use in building a new
  experiment. For our internal system `200` represents level-0 novelty and `101`-`105` represents
  the mock novelties.
* `[sail-on].difficulty` (comma separated list) are the difficulties the TA1 will use in building
  a new experiment. Valid options are `easy`, `medium`, and `hard`.

### Per-Domain Options

Replace `DOMAIN` with `cartpole` or `vizdoom` depending on which domain you are targeting.
The smartenv domain is currently not provided in this release.

* `[DOMAIN].training_episodes` (int) represents the number of training episodes the experiment
  provides before calling the training function, and then proceeding to trials.
* `[DOMAIN].testing_episodes` (int) represents the total number of episodes in a trial.
* `[DOMAIN].pre_novel_episodes` (int, optional) represents the number of episodes in a trial before
  switching to novelty. If this is not provided the default value of 30% of `testing_episodes`
  will be used.
* `[DOMAIN].live` (bool) *REQUIRED VALUE OF True FOR THE PORTABLE GENERATOR*.
* `[DOMAIN].use_image` (bool) will instruct the generator to build and include images for the
  domain feature_vectors. Use of this feature will increase CPU usage.


<a name="ta2configurationfile">

## TA2 Configuration File

The configuration file has three sections: `aiq-sail-on`, `sail-on`, and
`amqp`.  See `configs/partial/demo-client.config` for an example. This config works,
but only provides a small set of mock novelties.

### [aiq-sail-on]

* `experiment_type` selects the type of experiment to run, `SAIL-ON` is the
    only valid experiment type currently supported.

* `organization` is an identifier for your organization or university, this
    is associated with the experiments you run.

* `model_name` is the identifier for your model.  This allows you to keep
    track of multiple models.

* `username` is the email address/login for the system website (under
    construction).

* `secret` is a secret separate from your website password that is provided
    to allow for authentication.  Once the website is complete you will be able
    to request new values for this if you compromise the previous value.

* `description` is an optional field that will be recorded and associated
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

# TA2 Agent

The sample TA2 client in `TA2.py` provides stubs for the methods that are
called for each of the different phases of the program flow above. This is
where you implement your TA2/AI agent. See the documentation comments on these
methods in the `TA2.py` file.

<a name="ta2docker">

## Adding Your TA2 Agent to Docker 
You can add in your code to the TA2.py (and other code files).  Please update the
Dockerfile-PARTIAL-TA2 to bring in additional files and requirements-TA2.txt with any python 
requirements your TA2 agent may need.  Logfiles written to the `/aiq-sail-on/logs` directory will
be accessable outside the docker environment and can be saved.  Your TA2 agent is responsible for
retaining its own results when using the portable generator.

<a name="ta2external">

## Using an External TA2 Agent

You can run a TA2 agent on the portable generator outside the docker environment.  The code
requires some Python setup, which we describe below based on an Anaconda environment.

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

### Running the External TA2 Agent

To run the TA2 externally you will need to use the config file `configs/partial/gui-client.config`
to communicate with the portable generator, and you will need to use the `portable-gui.yml`
docker-compose file that opens a local port 5432 for the RabbitMQ communication connection.  In a
terminal window, build and start up the portable generator system
```
docker-compose -f portable-gui.yml build
docker-compose -f portable-gui.yml up
```
Then in a second terminal, using the `aiq-env` Anaconda environment we set up, change to the
source directory
```
(aiq-env) [user@host WSU-Portable-Generator]$ cd source
```
Then start up the TA2 agent.
```
(aiq-env) [user@host source]$ python TA2.py --config=../configs/partial/gui-client.config --printout --debug --logfile=logs/log.txt
```

When you are done make sure to bring down the portable generator system in the docker-compose
terminal window
```
docker-compose -f portable-gui.yml down
```

<a name="ta2gui">

## TA2 GUI Agents

The `GUI-Cartpole.py` and `GUI-Vizdoom.py` agents allow humans to test out the mock novelties in
their respective domains.  To set up the Python environment for these agents, follow the
instructions in [Using an External TA2 Agent](#ta2external) to set up an Anaconda environment.
Once you have followed those instructions there is 1 more package required for the GUI agents
```
(aiq-env) [user@host ~]$ pip install opencv-python
```

### Running the TA2 GUI Agents

First you need to make sure the TA1.config has been updated to tell the system to generate images
(see `use_image` in [TA1 Configuration](#ta1configurationfile)). Then you need to start up the
portable generation system in docker-compose that opens a local port (5672) for the GUI agent to
connect to the RabbitMQ communication system
```
docker-compose -f portable-gui.yml build
docker-compose -f portable-gui.yml up
```

Now in a separate window, using the `aiq-env` Anaconda environment we built, change to the source
directory
```
(aiq-env) [user@host WSU-Portable-Generator]$ cd source
```
Then start up the GUI agent, we will use GUI-Vizdoom.py in this example
```
(aiq-env) [user@host source]$ python GUI-Vizdoom.py --config=../configs/partial/gui-client.config --printout --ignore-secret
```
Please note that we included `--ignore-secret` in the command line args, this ensures you are
requesting a new experiment each time you run the GUI agent as the previously stored experiment
secret may have been wiped from the database the last time you brought the docker-compose system
down.

When you are done please don't forget to bring the docker-compose system down, or you may spend
more time debugging some errors than you would like the next time to try to start the system.
```
docker-compose -f portable-gui.yml down
```

### GUI Agents Gameplay Controls

Once an experiment has been created and the GUI agent has received the first feature vector an
image of the game will pop up.  Click on the image, then the following keys are used to control
the game actions.

#### Cartpole

key | action
--- | ---
w | forward
s | backward
a | left
d | right
q | quit

#### Vizdoom

key | action
--- | ---
w | forward
s | backward
a | left
d | right
q | quit
j | shoot
k | turn left 45 degrees
l | turn right 45 degrees

