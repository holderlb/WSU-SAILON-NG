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
    "time_stamp": 1597953858.2,
    "cart_position": -1.0,
    "cart_veloctiy": 1.0,
    "pole_angle": 0.01,
    "pole_angular_velocity": 0.03
}
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

