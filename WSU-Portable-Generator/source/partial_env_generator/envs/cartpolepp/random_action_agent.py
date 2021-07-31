#!/usr/bin/env python
import argparse
import random
import time

from m_5 import CartPolePPMock5 as CartPoleBulletEnv

# Params
use_gui = True
env = CartPoleBulletEnv('hard', renders=use_gui)

# Number of episodes
nb_episodes = 200
steps = 0
for _ in range(nb_episodes):
    env.reset()
    done = False
    total_reward = 0
    #steps = 0
    while True:
        action = 0#env.action_space.sample()
        state, reward, done, info = env.step(action)
        #print('-----')
        #print(state)
        steps += 1
        total_reward += reward
        time.sleep(1/50)

    print('steps:', steps/(_+1))

print(total_reward)

env.reset()  # hack to flush last event log if required
