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
domain.

## Feature vector format

The feature vector provides a value for each sensor and is sent in JSON format.
For example,

```
{
	time_stamp: 1597953858.2,
	cart_position: -1.0,
	cart_veloctiy: 1.0,
	pole_angle: 0.01,
	pole_angular_velocity: 0.03
}
```

## Feature label format

The feature label provides the correct action according to our SOTA agent and
is sent in JSON format. This is only provided for novelty-level-0 training
instances. For CartPole, the possible actions are "left" and "right". For
example,

```
{ action: left }
```

## Performance format

The current performance of the agent on the current episode is provided as
feedback after each agent response and is sent in JSON format. For the CartPole
domain, performance is defined as the number of seconds the pole has remained
balanced from the start of the episode. For example,

```
{ performance: 10.0 }
```

## Response format

The agent's response format is the same as the feature label format above.

