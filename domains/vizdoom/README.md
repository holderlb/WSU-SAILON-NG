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
    "time_stamp": 1622067743.7375498,
    "player": {
        "id": 0,
        "x_position": 10.0,
        "y_position": 10.0,
        "z_position": 0.0,
        "health": 10.0
    },
    "enemy": {
        "id": 1,
        "x_position": 10.0,
        "y_position": 20.0,
        "z_position": 0.0,
        "health": 1.0
    },
    "projectiles": [{
        "id": 3, 
        "x_position": 60.03, 
        "y_position": 25.16, 
        "z_position": 31.30
        }
    ]
}
```

## Feature label format

The feature label provides the correct action according to our SOTA agent and
is sent in JSON format. This is only provided for novelty level-0 training
instances. For VizDoom, the possible actions are:

"left", "right", "forward", "backward", "shoot", "nothing".

For example,

```
{ "action": "shoot" }
```

## Action response format

The agent's response format is the same as the feature label format above.

## Performance format

The current performance of the agent on the current episode is provided as
feedback after each agent response and is sent in JSON format. For VizDoom,
performance is defined as the amount of time left in the episode divided by
the maximium time for the episode. For example,

```
{ "performance": 0.9 }
```

The performance at the end of the episode is recorded as the performance for
that entire episode.

## Novelty indicator format

After each sensor fecture vector, the novelty generate sends the novelty
indicator, which indicates if the current episode is novel "true", not novel
"false" (i.e., novelty level 0), or unknown "null". The novelty indicator will
be the same for every interaction during an episode. For example,

```
{ "novelty_indicator": "true" }
```

## Novelty prediction format

After the agent returns the action response, it then returns the novelty 
prediction. The novelty prediction is an integer (0-10) representing the
novelty level that the agent assigns to the current episode. For example,

```
{ "novelty_prediction": 1 }
```

The agent's novelty prediction can vary during an episode, but the final 
novelty prediction for the last interaction of the episode is recorded as
the agent's novelty prediction for the whole episode.

Novelty detection is considered to have occurred at the first episode whose
final novelty\_prediction > 0.

