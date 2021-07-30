# CartPole Domain

The novelty level-0 CartPole task is for the agent to move a cart left and
right in order to keep an attached pole balanced. The agent receives sensor
data about the time, the position and velocity of the cart, and the angle and
angular velocity of the pole. The agent also receives feedback about their
current performance. The possible actions are move left and move right. The
cart and pole have different starting positions each episode. An episode ends
if the cart moves too far left or right, the absolute pole angle is too large,
or a time limit is exceeded.

See the [cartpole.json](cartpole.json) file for a precise specification of the
domain, including ranges on sensor values.

## Feature vector format

The feature vector provides a value for each sensor and is sent in JSON format.
For example,

```
{
    "cart": {
        "x_position": -0.885514,
        "y_position": -1.605059,
        "z_position": 0.1,
        "x_velocity": -11.970514,
        "y_velocity": 1.005748,
        "z_velocity": 0.0
    },
    "pole": {
        "x_quaternion": 0.064607,
        "y_quaternion": -0.065981,
        "z_quaternion": 0.67565,
        "w_quaternion": 0.731416,
        "x_velocity": 2.085099,
        "y_velocity": -0.892353,
        "z_velocity": 11.80254
    },
    "block_0": {
        "x_position": 4.051929,
        "y_position": -3.224569,
        "z_position": 2.41116,
        "x_velocity": 7.785026,
        "y_velocity": 9.065675,
        "z_velocity": 6.467906
    },
    "block_1": {
        "x_position": -0.057339,
        "y_position": -3.611403,
        "z_position": 5.08273,
        "x_velocity": 8.733008,
        "y_velocity": -7.7752,
        "z_velocity": 7.471741
    }
    "time_stamp": 1627668897.4486113,
    "image": null
}

```
The first call will have additional feature vector defining the corners of the cube world.
```
    "walls": [
        [-5,-5, 0],
        [5,-5, 0],
        [5,5, 0],
        [-5,5, 0],
        [-5,-5, 10],
        [5,-5, 10],
        [5,5, 10],
        [-5,5, 10],
    ]
```

## Feature label format

The feature label provides the correct action according to our SOTA agent and
is sent in JSON format. This is only provided for novelty level-0 training
instances. For CartPole, the possible actions are "left" and "right". For
example,

```
{ "action": "left" }
```

## Action response format

The agent's response format is the same as the feature label format above.

## Performance format

The current performance of the agent on the current episode is provided as
feedback after each agent response and is sent in JSON format. For CartPole,
performance is defined as the amount of time the pole is kept balanced
divided by the maximum time for the episode. For example,
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

