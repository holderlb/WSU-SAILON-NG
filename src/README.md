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
(base) [user@host ~]$ conda create --name aiq-env python=3.7 python-dateutil==2.8.1 psutil pytz
```
5.  Activate the new environment so we can finish installing the remaining packages.
```
(base) [user@host ~]$ conda activate aiq-env
```
6.  Install the remaining packages with pip.
```
(aiq-env) [user@host ~]$ pip install pika==1.1.0
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

### [sail-on]

*  `domain` selects which domain you would like to test on.  The current
    available domains are `cartpole`, `vizdoom`, and `smartenv`.

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
2. Run the TA2 client.
```
(aiq-env) [user@host client]$ python TA2.py --config=demo-client.config --printout --debug --logfile=log.txt
```
All command line arguments are described with `python TA2.py --help`.

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

