# Example Deliverable

This directory is a barebones example deliverable of a TA2 agent for evaluation.

Please modify the `Dockerfile-PARTIAL-TA2` to install what you need for your agent to run.

The contents of `configs/evaluation/evaluation.config` will be replaced by WSU when testing/evaluating your agent.

# How the Evaluation Works

Ideally, after building your agent's docker container, we will use the `--scale` option in 
docker-compose to run several copies of your agent on the same machine in parallel to work
through the evaluation trials.
Using the example here, that would look like this.
```
docker-compose -f groupname-ta2.yml build
docker-compose -f groupname-ta2.yml up -d --scale groupname-ta2=10
```

