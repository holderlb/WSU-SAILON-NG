import random
import numpy as np


class Agents:

    def __init__(self, level, difficulty, mock):
        # level and novelty selections
        self.level = level
        self.difficulty = difficulty
        self.mock = mock

        # Set looking bounds (vision cone)
        self.left_side = 7 / 8 * np.pi
        self.right_side = np.pi / 8

        self.id_to_cvar = None

        # Used for checking wall colision
        self.walls = None

        # Used for check
        self.last_dist = np.zeros((4, 4))

        # Abandonded novelties
        # For un-used novelty
        self.hunger_games_tick = None

        # Mock novelties
        # Used for revealed novelty 7
        self.covers = None
        self.hiding = None

        # REAL NOVELTIES BELOW
        # Used for real novelty 3
        self.last = [10] * 4
        self.lastlast = [10] * 4

        # Used for real novelty 5
        self.hunting = False
        self.tick_counter = -1
        self.hunt_tick = None

        return None

    # Run agent behavoir here
    def act(self, state, id_to_cvar):
        self.tick_counter = self.tick_counter + 1
        if self.id_to_cvar is None:
            self.id_to_cvar = id_to_cvar

        commands = list()

        # Prime the spinny agents (used for detecting if something went wrong)
        for ind in range(4):
            # Always turn left
            commands.append("set ai_" + str(ind + 1) + " " + str(3))

        # Enemies move towards player
        if self.level == 103:
            commands = self.move_towards(state, commands)

        # Enemies move away from avg
        elif self.level == 105:
            commands = self.spread_out(state, commands)

        # Enemies move away from avg
        elif self.level == 107:
            commands = self.take_cover(state, commands)

        # Enemies move away from player
        elif self.level == 203:
            commands = self.teleport(state, commands)

        # Enemies switch between moving and shooting
        elif self.level == 205:
            commands = self.hunt(state, commands)
            if self.hunting:
                return commands

        # Any other is pure random
        else:
            commands = []
            # Random behavoiur:
            for ind in range(4):
                action = random.choice(list(range(7))) + 1
                commands.append("set ai_" + str(ind + 1) + " " + str(action))

        # Enemies always check for facing to see if shoot
        commands = self.check_shoot(state, commands)

        # Enemies never shoot towards other enemies
        commands = self.check_enemies(state, commands)

        return commands

    # Novelty 103
    # Move agent towards player
    def move_towards(self, state, commands):
        for ind, val in enumerate(state['enemies']):
            # Get info
            angle, sign = self.get_angle(state['player'], val)

            if angle < self.right_side:
                # Forward, left, right, shoot?
                action = random.choice([1, 3, 4, 7])
            else:
                if sign == -1.0:
                    # Turn right
                    action = 6
                else:
                    # Turn left
                    action = 5

            # Send ai action
            commands[self.id_to_cvar[val['id']] - 1] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(action)

        return commands

    # Novelty 105
    # Enemies move away
    def spread_out(self, state, commands):
        # Find avg pos
        avg_x = 0.0
        avg_y = 0.0
        for ind, val in enumerate(state['enemies']):
            avg_x = avg_x + val['x_position']
            avg_y = avg_y + val['y_position']

        avg_x = avg_x / len(state['enemies'])
        avg_y = avg_y / len(state['enemies'])

        # Do spread out logic
        for ind, val in enumerate(state['enemies']):
            # Get info
            pl = {'x_position': avg_x, 'y_position': avg_y}

            angle, sign = self.get_angle(pl, val)

            # If enemy is face towards player turn away
            if angle > self.left_side:
                # Forward, left, right, shoot?
                action = random.choice([1, 3, 4, 7])
            else:
                if sign == 1.0:
                    # Turn right
                    action = 6
                else:
                    # Turn left
                    action = 5

            # Send ai action
            commands[self.id_to_cvar[val['id']] - 1] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(action)

        return commands

    # Novelty 107
    # Enemies move away from player behind cover
    def take_cover(self, state, commands):
        if self.difficulty == 'easy':
            cover_dist = 256
        elif self.difficulty == 'medium':
            cover_dist = 128
        elif self.difficulty == 'hard':
            cover_dist = 64

        # Assign closet obstacle to agent
        if self.covers is None:
            self.covers = {}
            for en_ind, enemy in enumerate(state['enemies']):
                enemy_pos = np.asarray([enemy['x_position'], enemy['y_position']])
                min_dist = None

                for obs_ind, obstacle in enumerate(state['items']['obstacle']):
                    obs_pos = np.asarray([obstacle['x_position'], obstacle['y_position']])
                    dist = np.linalg.norm(enemy_pos - obs_pos)
                    if min_dist is None or dist < min_dist:
                        min_dist = dist
                        self.covers[en_ind] = obs_ind

        # TODO: This is default goto script, make better
        for ind, val in enumerate(state['enemies']):
            obs = state['items']['obstacle'][self.covers[ind]]
            # Determine point to go to
            obs_pos = np.asarray([obs['x_position'], obs['y_position']])
            player_pos = np.asarray([state['player']['x_position'], state['player']['y_position']])

            angle = np.arctan2(obs_pos[0] - player_pos[0], obs_pos[1] - player_pos[1])

            goal = {'x_position': obs_pos[0] + -np.cos(angle) * cover_dist,
                    'y_position': obs_pos[1] + -np.sin(angle) * cover_dist}

            # Get info
            angle, sign = self.get_angle(goal, val)

            if angle < self.right_side:
                # Forward, left, right, shoot?
                action = random.choice([1, 3, 4])
            else:
                if sign == -1.0:
                    # Turn right
                    action = 5
                else:
                    # Turn left
                    action = 6

            # Send ai action
            commands[self.id_to_cvar[val['id']] - 1] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(action)

        return commands


    # Real novelty 203
    def teleport(self, state, commands):
        # Update health table
        current_health = []
        for ind, val in enumerate(state['enemies']):
            current_health.append(val['health'])

        # Do logic
        for ind, val in enumerate(state['enemies']):
            # Check for double shots
            if current_health[ind] != self.last[ind]:
                commands[self.id_to_cvar[val['id']] - 1] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(9)

        # Update last tables
        self.lastlast = self.last
        self.last = current_health

        return commands

    # Real 205
    def hunt(self, state, commands):
        # Roll for the hunt
        if self.hunting:
            for ind, val in enumerate(state['enemies']):
                angle, sign = self.get_angle(state['player'], val)
                if angle < np.pi / 8:
                    commands[self.id_to_cvar[val['id']] - 1] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(7)

                # Do movement here
                else:
                    if sign == -1.0:
                        # Turn right
                        action = 6
                    else:
                        # Turn left
                        action = 5

                    # Send ai action
                    commands[self.id_to_cvar[val['id']] - 1] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(
                        action)

        else:
            if self.hunt_tick is None:
                r = random.random()
                if self.difficulty == 'easy':
                    r = 10
                elif self.difficulty == 'medium':
                    r = 5
                elif self.difficulty == 'hard':
                    r = 0

                self.hunt_tick = r
            else:
                if self.tick_counter > self.hunt_tick:
                    self.hunting = True

        return commands

    # Enemies shoot at player
    def check_shoot(self, state, commands):
        for ind, val in enumerate(state['enemies']):
            my_command = None
            for command in commands:
                if "ai_" + str(self.id_to_cvar[val['id']]) in command:
                    my_command = command
            if '9' in my_command:
                continue

            angle, sign = self.get_angle(state['player'], val)

            if angle < self.right_side:
                if random.random() > 0.5:
                    # Shoot is action = 7
                    commands[self.id_to_cvar[val['id']] - 1] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(7)

        return commands

    # Enemies never shoot each other
    def check_enemies(self, state, commands):
        # From enemy
        for ind, val in enumerate(state['enemies']):
            # If an enemy is not shooting, dont mess with anything
            my_command = None
            for command in commands:
                if "ai_" + str(self.id_to_cvar[val['id']]) in command:
                    my_command = command
            if '7' not in my_command:
                continue

            # To enemy
            for ind2, val2 in enumerate(state['enemies']):
                # Check for self
                if ind == ind2:
                    continue

                # Distance check sections
                # Get self angle
                angle = val['angle'] * 2 * np.pi / 360
                x = np.cos(angle)
                y = np.sin(angle)

                # Line start
                p1 = np.asarray([val['x_position'], val['y_position']])
                # Line end
                p2 = np.asarray([val['x_position'] + x, val['y_position'] + y])
                # Enemy point
                p3 = np.asarray([val2['x_position'], val2['y_position']])

                dist = np.abs(np.linalg.norm(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1))
                angle, sign = self.get_angle(val2, val)

                check_dist = min(self.last_dist[ind][ind2], dist)
                if check_dist < (30 + dist/20) and angle < np.pi / 2:
                    action = random.choice([1, 2, 3, 4])
                    commands[self.id_to_cvar[val['id']] - 1] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(action)

                self.last_dist[ind][ind2] = dist

        return commands

    # Utility function for getting angle from B-direction to A
    def get_angle(self, player, enemy):
        pl_x = player['x_position']
        pl_y = player['y_position']

        en_x = enemy['x_position']
        en_y = enemy['y_position']
        en_ori = enemy['angle'] * 2 * np.pi / 360

        # Get angle between player and enemy
        # Convert enemy ori to unit vector
        v1_x = np.cos(en_ori)
        v1_y = np.sin(en_ori)

        enemy_vector = np.asarray([v1_x, v1_y]) / np.linalg.norm(np.asarray([v1_x, v1_y]))

        # If its buggy throw random value out
        #TODO: Figure out why an enemy is in the exact same pos as player
        if np.linalg.norm(np.asarray([pl_x - en_x, pl_y - en_y])) == 0:
            return random.random() * 3.14, 1

        enemy_face_vector = np.asarray([pl_x - en_x, pl_y - en_y]) / np.linalg.norm(
            np.asarray([pl_x - en_x, pl_y - en_y]))

        angle = np.arccos(np.clip(np.dot(enemy_vector, enemy_face_vector), -1.0, 1.0))

        sign = np.sign(np.linalg.det(
            np.stack((enemy_vector[-2:], enemy_face_vector[-2:]))
        ))

        return angle, sign

    def ccw(self, A,B,C):
        return (C['y']-A['y']) * (B['x']-A['x']) > (B['y']-A['y']) * (C['x']-A['x'])

    # Return true if line segments AB and CD intersect
    def intersect(self, A,B,C,D):
        return self.ccw(A,C,D) != self.ccw(B,C,D) and self.ccw(A,B,C) != self.ccw(A,B,D)
