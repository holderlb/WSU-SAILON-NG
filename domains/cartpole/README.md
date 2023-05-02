# CartPole Domain

## Table of Contents

* [Task Description](#taskdescription)
* [Feature Vector Format](#featurevectorformat)
* [Action Label](#actionlabel)
* [Performance](#performance)
* [Novelty Indicator](#noveltyindicator)
* [Novelty Characterization](#noveltycharacterization)
* [Sample (Mock) Novelty](#samplemocknovelty)
* [Revealed Novelty](#revealednovelty)
* [Frequently Asked Questions](#faq)

<a name="taskdescription">

## Task Description

![CartPole World](cartpole.png)

For the novelty-level-0 CartPole task, the agent must keep the pole balanced
by pushing the cart forward, backward, left or right. The cart is constrained to move
in a 2D plane. The pole is affixed to the cart and can move around that fixed point
in any direction. There are other objects in the environment that move in 3D and may
collide with cart, pole, walls, or each other. The agent receives sensor
data about the time, the position and velocity of the cart, the angles and
angular velocity of the pole, and the position and velocity of the objects. The agent
also receives feedback about their current performance and an optional image. The
cart, pole and objects have different random starting states each episode. An episode ends
if the cart moves too far from center, the absolute pole angle is too large,
or a time limit is exceeded. The time limit is 200 ticks of the game, where each tick
corresponds to 0.02 seconds. The agent's final score is T/200, where T the number of
ticks they keep the pole balanced.

The graphic below provides more information about the geometry used in CartPole.

![CartPole Geometry](cartpolepp.png)

See the [cartpole.json](cartpole.json) file for a precise specification of the
domain, including ranges on sensor values.

<a name="featurevectorformat">

## Feature Vector Format

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
    "blocks": [
        {
            "id": 2,
            "x_position": -1.86226,
            "y_position": 2.550503,
            "z_position": 6.339546,
            "x_velocity": 7.707002,
            "y_velocity": -8.587865,
            "z_velocity": 6.575934
        },
        {
            "id": 3,
            "x_position": -1.275671,
            "y_position": 1.31081,
            "z_position": 2.180347,
            "x_velocity": 9.403932,
            "y_velocity": -6.88735,
            "z_velocity": 9.195959
        }
    ],

    "time_stamp": 1627668897.4486113,
    "image": null
}

```
The first call will have an additional two feature vectors:

* Walls defining the corners of the cube world.

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

* Hints given pointers to the novelty used.
```
    Full hint example:
    "hint": {
        "level": 1,
        "entity": "cart",
        "attribute": "mass",
        "change": "increase"
    }
    No hint example:
    "hint": {
        "level": None,
        "entity": None,
        "attribute": None,
        "change": None
    }
```

<a name="actionlabel">

## Action Label

Each turn, the agent provides an action to be performed, which is one of
['nothing', 'left', 'right', 'forward', 'backward']. The returned action is
referred to as the "label", which is an artifact of other domains in which
the task is classification.

<a name="performance">

## Performance

The current performance of the agent on the current episode is provided as
feedback after each agent response and is sent in JSON format. For CartPole,
performance is defined as the amount of time the pole is kept balanced
divided by the maximum time for the episode. The performance at the end of
the episode is recorded as the performance for that entire episode.

<a name="noveltyindicator">

## Novelty Indicator

After each sensor fecture vector, the novelty generator sends a novelty
indicator, which indicates if the current episode is novel "true", not novel
"false" (i.e., novelty level 0), or unknown "null". The novelty indicator will
be the same for every turn during an episode.

<a name="noveltycharacterization">

## Novelty Characterization

At the end of each episode (train and test), the agent provides a novelty characterization, which includes: 
a list of novelty levels [0, 8] and their probabilities [0.0, 1.0], 
an entity characterization string, 
an attribute characterization string, 
and directional change string.

**TA2s must report at least the novelty levels and their probabilities. Missing levels will be presumed to be 0.0.**

It should look like:
```
    "novelty_characterization": {
        "level": [
            {"level_number": int, "probability": float},
            ...,
            {"level_number": int, "probability": float}
        ], 
        "entity": str, 
        "attribute": str, 
        "change": str
    }
```

Available options are:
* Entity: cart, pole, block, obstacle, walls, location, player (+ Action)
  * Action: nothing, left, right, forward, backward
* Attribute: quantity, size, value, speed, direction, position, angle, gravity, mass, force, friction, bounce
* Change: increase, decrease, increasing, decreasing, away <entity>, toward <entity>

<a name="samplemocknovelty">

## Sample (Mock) Novelty

The CartPole novelty generator includes sample novelties for levels 1-8,
also called Mock novelties. These are described below.

* Level 1: The mass of the cart changes.
* Level 2: The objects are immovable.
* Level 3: The objects initially move toward some random point.
* Level 4: The objects change size.
* Level 5: The objects are attracted to each other.
* Level 6: Gravity affects blocks. Increased gravity the cart and pole.
* Level 7: Blocks attracted to center of floor (0, 0, 0).
* Level 8: New stationary blocks spawn over time. 

The implementations of these mock novelties can be found in the folder
[WSU-Portable-Generator/source/partial_env_generator/envs/cartpolepp](https://github.com/holderlb/WSU-SAILON-NG/tree/master/WSU-Portable-Generator/source/partial_env_generator/envs/cartpolepp).

<a name="samplehints">

## List of Mock Hints

Table of how hints are returned using hint level:

HintLevel | NoveltyLevel | Entity | Attribute | Change
---|---|---|---|---
-1 | None | None | None | None
0 | Given | None | None | None
1 | Given | Given | None | None
2 | Given | Given | Given | None
3 | Given | Given | Given | Given

Table of hints for mock novelties:

Level | Entity | Attribute | Change
---|---|---|---
1 | cart | mass | increase
2 | block | speed | decrease
2 | block | mass | increase
3 | block | direction | toward location
4 | block | size | increase
5 | block | direction | toward block
6 | block | gravity | increase
7 | block | direction | toward location
8 | block | quantity | increasing


<a name="revealednovelty">

## Revealed Novelty
[README.md](..%2Fvizdoom%2FREADME.md)
### Phase 1

<img src="phase1.png" width="600">
    
* All:
    * Action space limited to two actions ['left', 'right', 'nothing']. Other actions get mapped to 'nothing'.
    * Most sensors are set to a fixed value since the information is no longer available.
    
* Level 1 (Class): Increase length of pole
  * No Novelty: length=0.5
  * Easy: length=2
  * Medium: length=4
  * Hard: length=7
* Level 2 (Attribute): Increase friction between cart and track
  * No Novelty: friction=0
  * Easy: friction=0.0125
  * Medium: friction varies randomly from 0.0125 to 0.1 based on current zone (x pos)
  * Hard: friction=0.0125, but works in reverse, effectively increasing push force
* Level 3 (Representation): Decrease sensor precision
  * No Novelty: Maximum floating point precision
  * Easy: Each sensor value mapped to 1 of 10 buckets over sensor's range
  * Medium: Each sensor value mapped to 1 of 6 buckets over sensor's range
  * Hard: Each sensor value mapped to 1 of 3 buckets over sensor's range

### Phase 2

* Level 1 (Objects): Increase in pole length
  * No Novelty: length=2
  * Easy: length=3
  * Medium: length=5
  * Hard: length=8

* Level 2 (Agents): Blocks move in non-random way along a line some distance from origin
  * No Novelty: Blocks move normally (random initial push)
  * Easy: Blocks move along line a distance 3-4 from origin
  * Medium: Blocks move along line a distance 2-3 from origin
  * Hard: Blocks move along line a distance 1.5-2 from origin

* Level 3 (Actions): Blocks initially pushed toward cart
  * No Novelty: Blocks given random push at beginning
  * Easy: Blocks have 25% chance of being pushed toward cart
  * Medium: Blocks have 50% chance of being pushed toward cart
  * Hard: Blocks have 75% chance of being pushed toward cart

* Level 4 (Relations): Change in energy of bounces (block/wall restitution)
  * No Novelty: Block/wall restitution = 1.00
  * Easy: Block/wall restitution = 1.05 to 1.15
  * Medium: Block/wall restitution = 1.20 to 1.30
  * Hard: Block/wall restitution = 1.35 to 1.45

* Level 5 (Interactions): Pole attracted to blocks.
  * No Novelty: Attraction force = 0
  * Easy: Attraction force = 1
  * Medium: Attraction force = 3
  * Hard: Attraction force = 5

### Phase 3

* Level 6 (Rules): Wind force applied to objects (Thanks Katarina)
  * No novelty: No wind applied
  * Easy: Wind Force Multiplier 16
  * Medium: Wind Force Multiplier 18
  * Hard: Wind Force Multiplier 20

* Level 7 (Goals): Blocks pushed towards cartpole
  * No novelty: Blocks behave normally
  * Easy: Push Force = 10
  * Medium: Push Force = 20
  * Hard: Push Force = 30

* Level 8 (Events): Additional normal blocks spawned.
  * No novelty: No additional blocks
  * Easy: Ticks between spawns = 3
  * Medium: Ticks between spawns = 2
  * Hard: Ticks between spawns = 1

<a name="faq">

## Frequently Asked Questions

Coming soon...

