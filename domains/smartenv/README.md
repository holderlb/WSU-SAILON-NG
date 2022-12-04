# Smart Environment Domain

## Table of Contents

* [Task Description](#taskdescription)
* [Feature Vector Format](#featurevectorformat)
* [Action Label Response and Feedback](#actionlabel)
* [Performance](#performance)
* [Novelty Indicator](#noveltyindicator)
* [Novelty Characterization](#noveltycharacterization)
* [Sample (Mock) Novelty](#samplemocknovelty)
* [Revealed Novelty](#revealednovelty)
* [Frequently Asked Questions](#faq)

<a name="taskdescription">

## Task Description

The novelty level-0 Smart Environment task is for the agent to recognize the
current activity of the inhabitant in the environment. The agent receives
timestamped sensor data and responds with one of 11 possible activities: wash
dishes, relax, personal hygiene, bed toilet transition, cook, sleep, take
medicine, leave home, work, enter home, eat. The agent also receives feedback
about their current performance, which is the percentage of correct classifications
since the beginning of the episode. The inhabitant's behavior varies from day
to day. An episode is one day's worth of data. Sensor vectors are generated
when at least one sensor changes value, not at a fixed frequency. Below is a
sample floorplan of one of the smart environments.

![Sample Floorplan](floorplan.png)

See the [smartenv.json](smartenv.json) file for a precise specification of the
domain, including ranges on sensor values.

<a name="featurevectorformat">

## Feature Vector Format

The feature vector provides a value for each sensor and is sent in JSON format.
There are five types of sensors: motion, motion area, light switch, light
level, and door.  Each sensor is described by its ID and value. There may be
more than one of each sensor type.

For example,

```
{
    "time_stamp": 1597953858.2,
    "motion_sensors": [
        { "id": "M001", "value": 0.0 },
        { "id": "M002", "value": 1.0 }
    ],
    "motion_area_sensors": [
        { "id": "MA007", "value": 1.0 }
    ],
    "door_sensors": [
        { "id": "D011", "value": 0.0 }
    ],
    "light_switch_sensors": [
        { "id": "L021", "value": 1.0 },
        { "id": "L022", "value": 0.0 }
    ],
    "light_level_sensors": [
        { "id": "LL025", "value": 70.0 }
    ]
}
```
The first call will have an additional feature vector:

* Hints given pointers to the novelty used.
```
    Full hint example:
    "hint": {
        "level": 1,
        "entity": "sensor",
        "attribute": "quantity",
        "change": "decrease"
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

## Activity Label Response and Feedback

After each sensor vector, the agent responds with one of 11 possible activity
classifications: wash\_dishes, relax, personal\_hygiene, bed\_toilet\_transition,
cook, sleep, take\_medicine, leave\_home, work, enter\_home, eat.

The agent is then provided with the correct activiy classification according to
a budget. E.g., if the budget is 50%, then the correct classificaton is provided
half the time. The budget is set within the novelty generator and made known
to the TA2 team.

<a name="performance">

## Performance

The current performance of the agent on the current episode is provided as
feedback after each agent response and is sent in JSON format. For SmartEnv,
performance is defined as classification accuracy so far, i.e. the number of
correct predictions divided by the total number of predictions. The performance
at the end of the episode is recorded as the performance for
that entire episode.

<a name="noveltyindicator">

## Novelty Indicator

After each sensor fecture vector, the novelty generator sends a novelty
indicator, which indicates if the current episode is novel "true", not novel
"false" (i.e., novelty level 0), or unknown "null". The novelty indicator will
be the same for every turn during an episode.

<a name="noveltycharacterization">

## Novelty Characterization

At the end of each episode, the agent provides a novelty characterization
for the episode, which includes a probability of novelty, probability threshold,
novelty level, and a characterization string.

<a name="samplemocknovelty">

## Sample (Mock) Novelty

The SmartEnv novelty generator includes sample Phase 2 novelties for levels 1-5,
also called Mock novelties. These are described below.

* Level 1: Some sensors turned off.
* Level 2: Inhabitant performs exact same behavior each day.
* Level 3: Activity not seen in pre-novelty, but seen in post-novelty.
* Level 4: Two sensor values always give same reading.
* Level 5: Second inhabitant simulated by overlaying copy of existing inhabitant.
* Level 6: Sensor values provided at random times.
* Level 7: Inhabitant spends more time outside of home.
* Level 8: Multiple days of data compressed into one.

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
1 | sensor | quantity | decrease
2 | sensor | variance | decrease
3 | activity | distribution | shift
4 | sensor | correlation | increase
5 | inhabitant | quantity | increase
6 | sensor | frequency | shift
7 | leave_home | quantity | increase
7 | enter_home | quantity | increase
8 | sensor | frequency | decrease

<a name="revealednovelty">

## Revealed Novelty

### Phase 1

* Level 1 (Class): Time shifts to some time in the future.
  * No Novelty: Episodes are contiguous days
  * Easy: Novel episodes are ? days into the future
  * Medium: Novel episodes are ? days into the future
  * Hard: Novel episodes are ? days into the future

* Level 2 (Attribute): Sensors inactive in pre-novelty become active post-novelty
  * No Novelty: 0 inactive sensors become active
  * Easy: 5 inactive sensors become active
  * Medium: 10 inactive sensors become active
  * Hard: All inactive sensors become active (15-20 depending on floorplan)

* Level 3 (Representation): Partition floorplan into areas; all sensors in area have same value
  * No novelty: # areas = # sensors
  * Easy: Floorplan partitioned into 10 areas
  * Medium: Floorplan partitioned into 8 areas
  * Hard: Floorplan partitioned into 5 areas

### Phase 2

* Level 1 (Objects): Increase in available sensors
  * No novelty: No additional sensors
  * Easy: 5 additional sensors
  * Medium: 10 additional sensors
  * Hard: Rest 30 additional sensors

* Level 2 (Agents): Time shifts to some time in the future
  * No Novelty: Episodes are contiguous days
  * Easy: Novel episodes are 30-60 days into the future
  * Medium: Novel episodes are 120-150 days into the future
  * Hard: Novel episodes are 260-300 days into the future

* Level 3 (Actions): Different inhabitant in same floorplan
  * No novelty: No change in inhabitant
  * Easy: Small change in inhabitant behavior
  * Medium: Medium change in inhabitant behavior
  * Hard: Large change in inhabitant behavior

* Level 4 (Relations): Sensors in one room turned off
  * No novelty: No sensors turned off
  * Easy: Study (5) sensors turned off in a room
  * Medium: Living room (6) sensors turned off in a room
  * Hard: Bedroom (7) sensors turned off in a room

* Level 5 (Interactions): Second inhabitant visits the environment
  * No novelty: No additional inhabitants
  * Easy: ? additional inhabitants visit for duration ?
  * Medium: ? additional inhabitants visit for duration ?
  * Hard: ? additional inhabitants visit for duration ?

<a name="faq">

## Frequently Asked Questions

Coming soon...

