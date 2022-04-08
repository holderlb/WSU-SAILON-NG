import random
import time
import json
import numpy as np
import zlib
from base64 import b64decode

#from sota_util.cartpole_agent import Simple as CP

use_full_generator = False
use_gui = False
use_img = False
debug = False

use_agent = False


def main():
    # Setup experiment parameters
    seed = 123
    domains = ['cartpole']
    difficulties = ['easy', 'medium', 'hard']

    np.random.seed(seed)
    random.seed(seed)

    # Set generator to use
    if use_full_generator:
        from env_generator.test_handler import TestHandler
        path = "env_generator/envs/"
        #novelty_levels = [200] + list(range(101, 106)) + list(range(201, 206))
        #novelty_levels = list(range(50, 54))
        #novelty_levels = [204] # + list(range(201, 206))
    else:
        from partial_env_generator.test_handler import TestHandler
        path = "partial_env_generator/envs/"
        #novelty_levels = [200] + list(range(101, 106))
        novelty_levels = list(range(50, 54))

    # Go through each combination
    for domain in domains:

        # Set correct action space
        if domain == 'cartpole':
            action_list = ['nothing', 'left', 'right', 'forward', 'backward']
        if domain == 'vizdoom':
            action_list = ['nothing', 'left', 'right', 'backward', 'forward',
                           'nothing', 'turn_left', 'turn_right']
        if domain == 'smartenv':
            action_list = ['wash_dishes', 'relax', 'personal_hygiene', 'bed_toilet_transition', 'cook', 'sleep',
                           'take_medicine', 'leave_home', 'work', 'enter_home', 'eat']

        # Create cartpole agent
        if use_agent:
            agent = CP()

        for novelty in novelty_levels:
            for difficulty in difficulties:
                print('Novelty:', novelty, 'Difficulty:', difficulty)
                # Set new seed for each ep
                seed = np.random.randint(100000000)

                # Clean it out
                env = None

                # Create a new instance of the environment
                config = {'start_zeroed_out': True}
                env = TestHandler(domain=domain, novelty=novelty, trial_novelty=novelty,
                                  difficulty=difficulty, seed=seed, use_img=use_img, path=path,
                                  use_gui=use_gui, ta2_generator_config=config)

                #print(seed, j, novelty, difficulty)
                counter = 0
                # Run until the environment is finished
                while not env.is_episode_done():# or debug:
                    counter = counter + 1
                    # Get observation
                    feature_vector = env.get_feature_vector()

                    # Print feature
                    if use_img:
                        #im = blosc.unpack_array(b64decode(feature_vector['image']))
                        # Direct call for faster testing
                        im = env.test.env.get_top_down()
                        plt.ion()
                        plt.show()
                        plt.imshow(im)
                        plt.draw()
                        plt.pause(0.001)
                        plt.clf()
                        feature_vector['image'] = None

                    else:
                        if debug:
                            a = feature_vector['cart']
                            b = feature_vector['pole']

                            print('=====================')
                            print('Instance:', counter)
                            print('cart --> x_v, y_v, z_v:', a['x_velocity'], a['y_velocity'], a['z_velocity'])
                            print('cart --> x_p, y_p, z_p:', a['x_position'], a['y_position'], a['z_position'])
                            print('pole --> x_q, y_q, z_q, w_q:', b['x_quaternion'], b['y_quaternion'],
                                  b['z_quaternion'], b['w_quaternion'])
                            print('pole --> x_v, y_v, z_v:', b['x_velocity'], b['y_velocity'], b['z_velocity'])
                            time.sleep(0.05)
                            #print(feature_vector['blocks'][0])

                    # We just choose random action here :)
                    action = {'action': random.choice(action_list)}
                    action = {'action': 'right'}
                    if use_agent:
                        action = agent.predict(feature_vector)

                    # Apply said action, returns performance
                    performance = env.apply_action(action)
                    #print(feature_vector)
                print(performance)

    return 0


if __name__ == "__main__":
    main()
