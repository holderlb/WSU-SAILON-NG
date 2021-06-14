import numpy as np
import random
import copy

import vizdoom as vzd


class viz:

    def __init__(self, params, seed, difficulty):
        self.difficulty = str(difficulty)
        self.novelty_string = str(params)

        DEFAULT_CONFIG = "env_generator/envs/vizdoom/basic.cfg"

        game = vzd.DoomGame()

        # Use other config file if you wish.
        game.load_config(DEFAULT_CONFIG)

        if self.novelty_string == 'n_10':
            game.set_doom_scenario_path("env_generator/envs/vizdoom/" +
                                        self.novelty_string +
                                        "_" + self.difficulty + ".wad")
        else:
            game.set_doom_scenario_path("env_generator/envs/vizdoom/" + str(self.novelty_string) + ".wad")
        game.set_render_hud(False)

        game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)

        # Set cv2 friendly format.
        game.set_screen_format(vzd.ScreenFormat.BGR24)

        # Enables labeling of the in game objects.
        game.set_labels_buffer_enabled(True)

        game.clear_available_game_variables()
        game.add_available_game_variable(vzd.GameVariable.POSITION_X)
        game.add_available_game_variable(vzd.GameVariable.POSITION_Y)
        game.add_available_game_variable(vzd.GameVariable.POSITION_Z)

        # Set seed here
        random.seed(seed)
        np.random.seed(seed)
        game.set_seed(seed)

        game.init()

        # print(game.get_seed(), flush=True)

        self.game = game
        self.counter = 0
        self.last_obs = None

        self.performance = -1.0

        self.step_limit = 2000
        self.actions = {'nothing': [False, False, False, False, False],
                        'left': [True, False, False, False, False],
                        'right': [False, True, False, False, False],
                        'backward': [False, False, True, False, False],
                        'forward': [False, False, False, True, False],
                        'shoot': [False, False, False, False, True]}

    def seed(self, num):
        random.seed(num)
        np.random.seed(num)
        return None

    # Used for CEM Agent
    def step(self, action):
        return self.act(action)

    def act(self, action):
        # Take action
        action = self.decode_action(action)
        self.game.make_action(action)

        # Get game state information
        state = self.get_state()
        observation = state
        done = self.game.is_episode_finished()
        info = {'actions': ['nothing', 'left', 'right', 'backward', 'forward', 'shoot']}
        if self.counter >= self.step_limit:
            done = True

        self.performance = (self.step_limit - self.counter) / self.step_limit
        self.counter = self.counter + 1

        # Copy just incase
        local_obs = copy.deepcopy(observation)

        return local_obs, self.performance, done, info

    def decode_action(self, action):
        return self.actions[action]

    def get_state(self):
        # Check for game end, if so just send last value
        if self.game.is_episode_finished():
            return self.last_obs

        # Get current game information
        state = self.game.get_state()
        labels = state.labels
        health = self.game.get_game_variable(vzd.vizdoom.HEALTH)

        # Start formatting the data
        data = {'projectiles': []}
        for l in labels:
            entity = {'id': int(l.object_id),
                      'x_position': round(float(l.object_position_x), 4),
                      'y_position': round(float(l.object_position_y), 4),
                      'z_position': round(float(l.object_position_z), 4)}
            # Check for player
            if l.object_id == 0:
                entity['health'] = float(health)
                data['player'] = entity
            # Check for enemy
            elif l.object_id == 1:
                entity['health'] = float(1.0)
                data['enemy'] = entity
            # Anything else (for now always projectiles)
            else:
                data['projectiles'].append(entity)

        # Save last obs
        self.last_obs = data

        return data

    def reset(self):
        # self.game.set_seed(1234)
        self.game.new_episode()
        state = self.get_state()
        local_obs = copy.deepcopy(state)

        return local_obs

