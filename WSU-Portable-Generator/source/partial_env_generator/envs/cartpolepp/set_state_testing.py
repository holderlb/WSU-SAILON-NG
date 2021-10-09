# test the set state method in cartpoleplusplus
import pdb
import importlib.util
import numpy as np
import random
#env_location = importlib.util.spec_from_file_location('CartPoleBulletEnv', \
#    'WSU-SAILON-NG-master/WSU-Portable-Generator/source/partial_env_generator/envs/cartpolepp/cartpoleplusplus.py')
env_location = importlib.util.spec_from_file_location('CartPoleBulletEnv', 'cartpoleplusplus.py')
env_class = importlib.util.module_from_spec(env_location)
env_location.loader.exec_module(env_class)

print("Start test")

env = env_class.CartPoleBulletEnv()
env1 = env_class.CartPoleBulletEnv()
env.path = "WSU-SAILON-NG/WSU-Portable-Generator/source/partial_env_generator/envs/cartpolepp"
env1.path = "WSU-SAILON-NG*sh/WSU-Portable-Generator/source/partial_env_generator/envs/cartpolepp"
env.path = "."
env1.path = "."


#env.seed(1)
#env1.seed(93)

env.reset()
env1.reset()
#env2.reset()

feature_vector = env.get_state()
#print("Original env: ", env.get_state())
#print("ev1: ", env1.get_state())

env1.setState(feature_vector)
#print("updated ev1: ", env1.get_state())

print("\n\nState diff", env.state_diff(env1.get_state()))
print()
print("Step 0  both environments.")
env1.step(0)
env.step(0)
print("Stepped State diff", env.state_diff(env1.get_state()))

print()
print("Step 1 both environments.")
env1.setState(env.get_state())
env.step(1)
env1.step(1)
print("after step State diff", env.state_diff(env1.get_state()))
print()

for i in range(20):
    env1.setState(env.get_state())
    raction = random.randint(0,4)
    env.step(raction)
    env1.step(raction)
print("Step reset step 20x State diff", env.state_diff(env1.get_state()))

for i in range(20):
    env1.setState(env.get_state())
    raction = random.randint(0,4)
    env.step(raction)
    env1.step(raction)
print("Stepstep 20x State diff", env.state_diff(env1.get_state()))

print("If all stat differences are < 10^-5 (or 10*roundamount) then smile, be happy")





