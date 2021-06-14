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


# Experiment Configuration
You can change some of the experiment parameters using the `configs/partial/TA1.config` config file.
Change `[sail-on].trials` to change the number of trials per novelty/difficulty/visibility
configuration.  Change `[cartpole].testing_episodes` to change the number of cartpole episodes in
a trial.  Change `[vizdoom].testing_episodes` to change the number of vizdoom episodes in a trial.
The smartenv domain is currently not provided in this release.


# Adding Your TA2 Agent
You can add in your code to the TA2.py (and other code files).  Please update the
Dockerfile-PARTIAL-TA2 to bring in additional files and requirements-TA2.txt with requirements
your TA2 agent may need.  Logfiles written to the logs directory will be accessable outside the
docker environment and can be saved.  Your TA2 agent is responsible for retaining its own results.


# Mock Novelty
### Cartpole
The code for mock novelty and three levels of difficulty for cartpole are located in
`source/partial_env_generator/envs/cartpole/cartpole_n10.py`.  If you wish to introduce your own
novelties, you may edit that code.

### Vizdoom
The simulator configurations for mock novelty and three levels of difficulty for vizdoom are
located in `source/partial_env_generator/envs/vizdoom/n_10_[DIFFICULTY].wad`.  You may edit those
configuration files to introduce your own novelties.
