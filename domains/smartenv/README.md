# Smart Environment Domain

The novelty level-0 Smart Environment task is for the agent to recognize the
current activity of the inhabitant in the environment. The agent receives
timestamped sensor data and responds with one of 11 possible activities: wash
dishes, relax, personal hygiene, bed toilet transition, cook, sleep, take
medicine, leave home, work, enter home, eat. The agent also receives feedback
about their current performance, which is the number of correct classifications
since the beginning of the episode. The inhabitant's behavior varies from day
to day. An episode is one day's worth of data. Sensor vectors are generated
when at least one sensor changes value, not at a fixed frequency.

See the [smartenv.json](smartenv.json) file for a precise specification of the
domain, including ranges on sensor values.

## Feature vector format

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

## Feature label format

The feature label provides the correct activity according to ground truth and
is sent in JSON format. This is only provided for novelty level-0 training
instances. For SmartEnv, the possible activities are: wash\_dishes, relax,
personal\_hygiene, bed\_toilet\_transition, cook, sleep, take\_medicine,
leave\_home, work, enter\_home, eat. Note that we use "action" as the key name
to be consistent with the other domains. For example,

```
{ "action": "take_medicine" }
```

## Response format

The agent's response format is the same as the feature label format above.

## Performance format

The current performance of the agent on the current episode is provided as
feedback after each agent response and is sent in JSON format. For SmartEnv,
performance is defined as classification accuracy so far, i.e. the number of
correct predictions divided by the total number of predictions. For example,

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

