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
    time_stamp: 1597953858.2,
    motion_sensor: {id: 1, value: 0.0},
    motion_sensor: {id: 2, value: 1.0},
    motion_area_sensor: {id: 7, value: 1.0},
    door_sensor: {id: 11, value: 0.0},
    light_switch_sensor: { id: 21, value: 1.0 },
    light_switch_sensor: { id: 22, value: 0.0 },
    light_level_sensor: { id: 25, value: 70.0 },
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
{ action: take_medicine }
```

## Performance format

The current performance of the agent on the current episode is provided as
feedback after each agent response and is sent in JSON format. For SmartEnv,
performance is defined as the number of correct activity recognitions since
the beginning of the episode.  For example,

```
{ performance: 10.0 }
```

## Response format

The agent's response format is the same as the feature label format above.



