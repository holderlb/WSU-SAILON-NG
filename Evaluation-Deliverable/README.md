# Example Deliverable

This directory is a barebones example deliverable of a TA2 agent for evaluation.

Please modify the `Dockerfile-PARTIAL-TA2` to install what you need for your agent to run.

The contents of `configs/evaluation/evaluation.config` will be replaced by WSU when
testing/evaluating your agent.

# How the Evaluation Works

Ideally, after building your agent's docker container, we will use the `--scale` option in 
docker-compose to run several copies of your agent on the same machine in parallel to work
through the evaluation trials.
Using the example here, that would look like this.
```
docker-compose -f groupname-ta2.yml build
docker-compose -f groupname-ta2.yml up -d --scale groupname-ta2=10
```

## A More Detailed View
**NOTE** You can test the behavior below with the provided config in `evaluation.config` that
connects to the demo example, or replace the content with your config that connects to the
MockN (mock novelty) API.  Requests for MockN credentials can be sent to Brian Thomas
(bthomas1@wsu.edu).

1) Build the TA2 agent.
```
docker-compose -f groupname-ta2.yml build
```
2) Start 1 instance of TA2 to initiate the experiment and populate the `evaluation.config` file
with the experiment identifier.
```
docker-compose -f groupname-ta2.yml up -d --scale groupname-ta2=1
```
3) Now that the file `evaluation.config` has been updated outside the docker container, we can
scale up additional instances of your agent.
```
docker-compose -f groupname-ta2.yml up -d --scale groupname-ta2=2
```

If you are not providing a pre-trained model and will be training on the provided training
episodes, then we would wait for your agent to complete training and start processing it's first
trial before scaling up the number of instances of your agent.

