# VizDoom Domain

The novelty level-0 VizDoom task is for the agent (player) to shoot a
stationary enemy. The agent receives sensor data about the time, the player
position and health, and the enemy position and health. The agent also receives
feedback about their current performance, which is the number of seconds
remaining in the episode, i.e., the quicker the agent kills the enemy, the
better the score. The possible actions are move left, move right, and shoot.
The player and enemy have random starting positions each episode. An episode
ends when either the enemy dies, the player dies, or a time limit is exceeded.

See the [vizdoom.json](vizdoom.json) file for a precise specification of the
domain, including ranges on sensor values.

## Feature vector format

The feature vector provides a value for each sensor and is sent in JSON format.
The high-level sensors player and enemy are further broken down by their ID,
position, and health. There may be more than one enemy.  The high-level sensor
projectile is broken down by ID and position. An example of a projectile is a
slow-moving bullet. There may be more than one projectile.

For example,

```
{
    time_stamp: 1597953858.2,
    player: {
        id: 1,
        x_position: 10.0,
        y_position: 10.0,
        z_position: 0.0,
        health: 50.0
    },
    enemy:
        id: 2,
        x_position: 10.0,
        y_position: 20.0,
        z_position: 0.0,
        health: 100.0
    },
    projectile:
        id: 11,
        x_position: 10.0,
        y_position: 15.0,
        z_position: 0.0
    }
}
```

## Feature label format

The feature label provides the correct action according to our SOTA agent and
is sent in JSON format. This is only provided for novelty level-0 training
instances. For VizDoom, the possible actions are "left", "right" and "shoot".
For example,

```
{ action: shoot }
```

## Performance format

The current performance of the agent on the current episode is provided as
feedback after each agent response and is sent in JSON format. For CartPole,
performance is defined as the number of seconds left in the episode.  For
example,

```
{ performance: 10.0 }
```

## Response format

The agent's response format is the same as the feature label format above.


