import copy
import random

import numpy as np
import vizdoom as vzd

from .Agents import Agents

class SailonViz:

    def __init__(self, use_mock, use_novel, level, use_img, seed, difficulty, path):
        # Set internal params
        self.use_mock = use_mock
        self.use_novel = use_novel
        self.level = level
        self.use_img = use_img
        self.seed = seed
        self.difficulty = difficulty

        # Decide on agent behvoiur here
        self.Agents = Agents(self.level, self.difficulty, self.use_mock)

        # Make and load game parameters here
        game = vzd.DoomGame()
        package_path = path + "vizdoom/"
        game.load_config(package_path + 'basic.cfg')
        game.set_doom_scenario_path(package_path + "phase_2_reduced.wad")

        # Set game tie ins
        game.add_available_game_variable(vzd.vizdoom.HEALTH)
        game.add_available_game_variable(vzd.vizdoom.AMMO2)
        game.add_available_game_variable(vzd.vizdoom.USER20)
        game.add_available_game_variable(vzd.vizdoom.USER21)
        game.add_available_game_variable(vzd.vizdoom.USER22)
        game.add_available_game_variable(vzd.vizdoom.USER23)

        game.add_available_game_variable(vzd.vizdoom.USER30)
        game.add_available_game_variable(vzd.vizdoom.USER31)
        game.add_available_game_variable(vzd.vizdoom.USER32)
        game.add_available_game_variable(vzd.vizdoom.USER33)

        game.add_available_game_variable(vzd.vizdoom.USER40)
        game.add_available_game_variable(vzd.vizdoom.USER41)
        game.add_available_game_variable(vzd.vizdoom.USER42)
        game.add_available_game_variable(vzd.vizdoom.USER43)

        # Send level speicfic info here
        game.add_game_args("+set novelty " + str(self.level*10+int(self.use_mock)))
        conv = {'easy': 1, 'medium': 2, 'hard': 3}
        game.add_game_args("+set difficulty_n " + str(conv[self.difficulty]))

        # Enables information about all objects present in the current episode/level.
        game.set_objects_info_enabled(True)

        # Enables information about all sectors (map layout).
        game.set_sectors_info_enabled(True)

        # Set seed here
        random.seed(seed)
        np.random.seed(seed)
        game.set_seed(seed)

        game.init()

        self.game = game
        self.counter = 0
        self.done = None
        self.performance = None
        self.last_obs = None
        self.enemies_health = None

        self.step_limit = 2000
        self.actions = {'nothing': [False, False, False, False, False, 0],
                        'left': [True, False, False, False, False, 0],
                        'right': [False, True, False, False, False, 0],
                        'backward': [False, False, True, False, False, 0],
                        'forward': [False, False, False, True, False, 0],
                        'shoot': [False, False, False, False, True, 0],
                        'turn_left': [False, False, False, False, False, -45],
                        'turn_right': [False, False, False, False, False, 45]}

        return None

    def step(self, action):
        # Decode action
        action = self.actions[action]

        # Set agent behavoiur before making the action (which calls an ingame update)
        # Returns a string array, use as commands in vizdoom
        comands = self.Agents.act(self.get_state())
        for command in comands:
            self.game.send_game_command(command)

        # Make action
        self.game.make_action(action)

        # Calculate performance
        self.performance = (self.step_limit - self.counter) / self.step_limit

        # Get game state information
        observation = self.get_state()

        # Update counter
        self.counter = self.counter + 1

        # Check if game is done naturally, then check step limit
        self.done = self.game.is_episode_finished()
        if self.counter > (self.step_limit + 1):
            self.done = True

        if observation['player']['health'] <= 0:
            self.done = True
            self.performance = 0.0

        # Update last obs
        self.last_obs = observation

        return observation, self.performance, self.done, {'action_list': self.actions.keys()}

    def get_image(self):
        # Check to generate image or not
        if not self.use_img:
            return None

        if self.done:
            return None

        if self.game is None:
            return None

        # Get current game information
        state = self.game.get_state()
        #print('before')
        #print(state.screen_buffer.dtype)
        #print(state.screen_buffer.shape)
        #print(state.screen_buffer)
        return state.screen_buffer

        screen_buf = state.screen_buffer.tolist()

        return screen_buf

    def get_state(self, initial=False):
        # Check for game end, if so just send last value
        if self.game.is_episode_finished():
            return self.last_obs

        if self.game is None:
            return self.last_obs

        # Get current game information
        state = self.game.get_state()
        health = self.game.get_game_variable(vzd.vizdoom.HEALTH)
        ammo = self.game.get_game_variable(vzd.vizdoom.AMMO2)

        # Get enemy ids
        if initial:
            self.enemies_health = dict()
            game_vars = [vzd.vizdoom.USER20, vzd.vizdoom.USER21,
                         vzd.vizdoom.USER22, vzd.vizdoom.USER23]

            x_vars = [vzd.vizdoom.USER30, vzd.vizdoom.USER31,
                      vzd.vizdoom.USER32, vzd.vizdoom.USER33]

            y_vars = [vzd.vizdoom.USER40, vzd.vizdoom.USER41,
                      vzd.vizdoom.USER42, vzd.vizdoom.USER43]

            for object in state.objects:
                if "Zombie" in object.name and "Dead" not in object.name:
                    for i in range(4):
                        x_pos = self.game.get_game_variable(x_vars[i])
                        y_pos = self.game.get_game_variable(y_vars[i])
                        dif = abs(x_pos - object.position_x) + abs(y_pos - object.position_y)
                        if dif < 5:
                            self.enemies_health[object.id] = game_vars[i]
        # Start formatting the data
        data = {'enemies': [], 'items': {'health': [], 'ammo': [], 'trap': [], 'obstacle': []}}

        for object in state.objects:
            # print(object.name)
            # Base entity information
            entity = {'id': int(object.id),
                      'angle': round(object.angle, 4),
                      'x_position': round(float(object.position_x), 4),
                      'y_position': round(float(object.position_y), 4),
                      'z_position': round(float(object.position_z), 4)}

            # Check for player
            if object.name == 'Doomer':
                entity['health'] = float(health)
                entity['ammo'] = float(ammo)
                data['player'] = entity

            # Check for enemy
            elif "Zombie" in object.name and "Dead" not in object.name and object.id in self.enemies_health.keys():
                entity['name'] = "ZombieMan"
                entity['health'] = self.game.get_game_variable(self.enemies_health[int(object.id)])
                data['enemies'].append(entity)

            elif "Whiskeyy" in object.name:
                data['items']['trap'].append(entity)

            elif "Health" in object.name:
                data['items']['health'].append(entity)

            elif "Clip" in object.name:
                data['items']['ammo'].append(entity)

            elif "TallRedColumn2" in object.name:
                data['items']['obstacle'].append(entity)

        # Get lines
        if initial:
            data['walls'] = []
            for sector in state.sectors:
                if sector.ceiling_height < 10.0:
                    continue
                for line in sector.lines:
                    data['walls'].append({'x1': round(line.x1, 2), 'x2': round(line.x2, 2),
                                          'y1': round(line.y1, 2), 'y2': round(line.y2, 2)})

        return data

    def reset(self):
        # Reset params
        self.counter = 0
        self.done = False
        self.performance = None
        self.last_obs = None

        # Start a new episode
        self.game.new_episode()

        # Get state
        observation = self.get_state(initial=True)

        return observation