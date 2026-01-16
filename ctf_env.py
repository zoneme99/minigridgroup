import functools
import gymnasium as gym
import numpy as np
from gymnasium.spaces import Discrete, Box
from pettingzoo import ParallelEnv
from minigrid.core.grid import Grid
from minigrid.core.mission import MissionSpace
from minigrid.core.world_object import Goal, Wall, Ball, Floor, Key
from minigrid.minigrid_env import MiniGridEnv


class Flag(Goal):
    def __init__(self, color):
        super().__init__()
        self.color = color


class CaptureTheFlagPZ(ParallelEnv):
    metadata = {"render_modes": ["human", "rgb_array"], "name": "ctf_v1"}

    def __init__(self, render_mode=None):
        self.possible_agents = ["red", "blue"]
        self.agents = self.possible_agents[:]
        self.render_mode = render_mode

        # Grid Params
        self.grid_size = 12
        self.max_steps = 400

        self.mission_space = MissionSpace(
            mission_func=lambda: "Capture the enemy flag!")

        self.env = MiniGridEnv(
            grid_size=self.grid_size,
            max_steps=self.max_steps,
            mission_space=self.mission_space
        )

        self.spawn_pos = {}

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return Box(low=0, high=255, shape=(56, 56, 3), dtype=np.uint8)

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return Discrete(3)

    def render(self):
        # --- FIX 1: THE GHOST FIX ---
        # Separate the "Save" loop from the "Draw" loop.
        # This ensures we never accidentally save another agent as 'background'.
        saved_objs = []

        # 1. Save Backgrounds
        for agent in self.agents:
            if agent in self.agent_pos:
                pos = tuple(self.agent_pos[agent])
                # We save the (pos, obj) tuple
                saved_objs.append((pos, self.env.grid.get(*pos)))

        # 2. Draw Agents
        for agent in self.agents:
            if agent in self.agent_pos:
                pos = tuple(self.agent_pos[agent])
                if self.carrying_flag.get(agent, False):
                    self.env.grid.set(*pos, Key(agent))
                else:
                    self.env.grid.set(*pos, Ball(agent))

        # 3. Take Picture
        original_agent_pos = self.env.agent_pos
        self.env.agent_pos = (-1, -1)
        img = self.env.get_frame(highlight=False, tile_size=8)
        self.env.agent_pos = original_agent_pos

        # 4. Restore Backgrounds
        # We restore in reverse order just to be safe, though not strictly necessary now
        for pos, obj in reversed(saved_objs):
            self.env.grid.set(*pos, obj)

        return img

    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        self.steps = 0
        if seed is not None:
            np.random.seed(seed)

        self.env.step_count = 0
        self.env.mission = self.mission_space.sample()

        self.carrying_flag = {"red": False, "blue": False}

        # 1. Grid
        self.env.grid = Grid(self.grid_size, self.grid_size)
        self.env.grid.wall_rect(0, 0, self.grid_size, self.grid_size)

        mid_x = self.grid_size // 2
        for i in range(1, self.grid_size - 1):
            for j in range(1, self.grid_size - 1):
                self.env.grid.set(i, j, Floor('red' if i < mid_x else 'blue'))

        for y in range(1, self.grid_size - 1):
            if y % 2 == 0:
                self.env.grid.set(mid_x, y, Wall())

        # 2. Obstacles
        obstacles = 0
        while obstacles < 8:
            x = np.random.randint(1, self.grid_size - 1)
            y = np.random.randint(1, self.grid_size - 1)
            if y == self.grid_size // 2:
                continue
            if self.env.grid.get(x, y) is None or self.env.grid.get(x, y).type == 'floor':
                self.env.grid.set(x, y, Wall())
                obstacles += 1

        # 3. Flags
        self.flag_pos = {
            "red": (1, self.grid_size // 2),
            "blue": (self.grid_size - 2, self.grid_size // 2)
        }
        self.env.grid.set(*self.flag_pos["red"], Flag('red'))
        self.env.grid.set(*self.flag_pos["blue"], Flag('blue'))

        # 4. Spawns
        self.agent_pos = {}
        self.agent_dir = {"red": 0, "blue": 2}

        # Red Spawn
        while True:
            ry = np.random.randint(1, self.grid_size - 1)
            rx = 2
            if self.env.grid.get(rx, ry).type == 'floor':
                self.spawn_pos["red"] = np.array([rx, ry])
                self.agent_pos["red"] = np.array([rx, ry])
                break

        # Blue Spawn
        while True:
            by = np.random.randint(1, self.grid_size - 1)
            bx = self.grid_size - 3
            if self.env.grid.get(bx, by).type == 'floor':
                self.spawn_pos["blue"] = np.array([bx, by])
                self.agent_pos["blue"] = np.array([bx, by])
                break

        self.env.agent_pos = self.agent_pos["red"]
        self.env.agent_dir = self.agent_dir["red"]

        return self._get_observations(), {}

    def _get_observations(self):
        observations = {}
        for agent_id in self.agents:
            me = agent_id
            enemy = "blue" if me == "red" else "red"

            if enemy in self.agent_pos:
                enemy_pos = tuple(self.agent_pos[enemy])
                prev_obj = self.env.grid.get(*enemy_pos)
                if prev_obj is None or prev_obj.type == 'floor':
                    if self.carrying_flag[enemy]:
                        self.env.grid.set(*enemy_pos, Key(enemy))
                    else:
                        self.env.grid.set(*enemy_pos, Ball(enemy))

            self.env.agent_pos = self.agent_pos[me]
            self.env.agent_dir = self.agent_dir[me]
            observations[me] = self.env.get_pov_render(tile_size=8)

            if enemy in self.agent_pos:
                self.env.grid.set(*enemy_pos, prev_obj)

        return observations

    def step(self, actions):
        rewards = {a: -0.01 for a in self.agents}
        terminations = {a: False for a in self.agents}
        truncations = {a: False for a in self.agents}
        infos = {a: {} for a in self.agents}

        # --- FIX 2: THE HEAVY FLAG ---
        # Increase the "Time Pressure" on the flag carrier.
        # If they just run in circles, they will lose points fast.
        for agent in self.agents:
            if self.carrying_flag[agent]:
                rewards[agent] -= 0.1  # 10x higher penalty than normal walking

        self.steps += 1

        for agent_id in self.agents:
            if agent_id not in actions:
                continue

            action = actions[agent_id]
            self.env.agent_pos = self.agent_pos[agent_id]
            self.env.agent_dir = self.agent_dir[agent_id]

            self.env.step(action)

            self.agent_pos[agent_id] = self.env.agent_pos
            self.agent_dir[agent_id] = self.env.agent_dir

            # CAPTURE LOGIC
            current_pos = tuple(self.env.agent_pos)
            enemy = "blue" if agent_id == "red" else "red"
            enemy_flag_loc = self.flag_pos[enemy]
            my_base_loc = self.flag_pos[agent_id]

            if current_pos == enemy_flag_loc and not self.carrying_flag[agent_id]:
                self.carrying_flag[agent_id] = True
                self.env.grid.set(*enemy_flag_loc, Floor(enemy))
                rewards[agent_id] += 5.0

            if current_pos == my_base_loc and self.carrying_flag[agent_id]:
                rewards[agent_id] += 20.0
                for a in self.agents:
                    terminations[a] = True

        # TAGGING LOGIC
        if "red" in self.agent_pos and "blue" in self.agent_pos:
            red_p = tuple(self.agent_pos["red"])
            blue_p = tuple(self.agent_pos["blue"])

            if red_p == blue_p:
                for carrier, tagger in [("red", "blue"), ("blue", "red")]:
                    if self.carrying_flag[carrier]:
                        rewards[carrier] -= 2.0
                        rewards[tagger] += 2.0

                        self.carrying_flag[carrier] = False
                        self.agent_pos[carrier] = self.spawn_pos[carrier].copy()

                        flag_home = self.flag_pos[tagger]
                        self.env.grid.set(*flag_home, Flag(tagger))

        if self.steps >= self.max_steps:
            for a in self.agents:
                truncations[a] = True

        observations = self._get_observations()
        if any(terminations.values()) or any(truncations.values()):
            self.agents = []

        return observations, rewards, terminations, truncations, infos
