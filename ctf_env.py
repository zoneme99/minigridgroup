import functools
import gymnasium as gym
import numpy as np
from gymnasium.spaces import Discrete, Box
from pettingzoo import ParallelEnv
from minigrid.core.grid import Grid
from minigrid.core.mission import MissionSpace
from minigrid.core.world_object import Goal, Wall, Ball, Floor
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
        self.grid_size = 12  # Bigger map for more maneuvering
        self.max_steps = 200  # More steps to navigate the maze

        self.mission_space = MissionSpace(
            mission_func=lambda: "Capture the enemy flag!")

        self.env = MiniGridEnv(
            grid_size=self.grid_size,
            max_steps=self.max_steps,
            mission_space=self.mission_space
        )

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return Box(low=0, high=255, shape=(56, 56, 3), dtype=np.uint8)

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return Discrete(3)

    def render(self):
        # 1. Save the current grid state
        saved_objs = {}
        for agent in self.agents:
            if agent in self.agent_pos:  # Check if agent is still alive/active
                pos = tuple(self.agent_pos[agent])
                saved_objs[agent] = self.env.grid.get(*pos)
                self.env.grid.set(*pos, Ball(agent))

        # 2. Render
        original_agent_pos = self.env.agent_pos
        self.env.agent_pos = (-1, -1)  # Hide the default triangle cursor
        img = self.env.get_frame(highlight=False, tile_size=8)

        # 3. Restore
        self.env.agent_pos = original_agent_pos
        for agent in self.agents:
            if agent in self.agent_pos:
                pos = tuple(self.agent_pos[agent])
                self.env.grid.set(*pos, saved_objs[agent])

        return img

    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        self.steps = 0
        if seed is not None:
            np.random.seed(seed)

        self.env.step_count = 0
        self.env.mission = self.mission_space.sample()

        # 1. Build Walls
        self.env.grid = Grid(self.grid_size, self.grid_size)
        self.env.grid.wall_rect(0, 0, self.grid_size, self.grid_size)

        # Floor Colors
        mid_x = self.grid_size // 2
        for i in range(1, self.grid_size - 1):
            for j in range(1, self.grid_size - 1):
                self.env.grid.set(i, j, Floor('red' if i < mid_x else 'blue'))

        # Midfield Wall
        for y in range(1, self.grid_size - 1):
            if y % 2 == 0:
                self.env.grid.set(mid_x, y, Wall())

        # We loop until we successfully place x amount of walls
        obstacles = 0
        while obstacles < 8:
            x = np.random.randint(1, self.grid_size - 1)
            y = np.random.randint(1, self.grid_size - 1)
            # Keep the flag areas clear (roughly)
            if y == self.grid_size // 2:
                continue

            if self.env.grid.get(x, y) is None or self.env.grid.get(x, y).type == 'floor':
                self.env.grid.set(x, y, Wall())
                obstacles += 1

        # 3. Flags
        self.env.grid.set(1, self.grid_size // 2, Flag('red'))
        self.env.grid.set(self.grid_size - 2,
                          self.grid_size // 2, Flag('blue'))

        # 4. RANDOM SPAWNS
        # Instead of fixed (2, 5), we pick a random Y for each agent
        # ensuring they don't spawn inside a wall
        self.agent_pos = {}
        self.agent_dir = {"red": 0, "blue": 2}

        # Red Spawn (Left side, random Y)
        while True:
            ry = np.random.randint(1, self.grid_size - 1)
            rx = 2
            if self.env.grid.get(rx, ry).type == 'floor':
                self.agent_pos["red"] = np.array([rx, ry])
                break

        # Blue Spawn (Right side, random Y)
        while True:
            by = np.random.randint(1, self.grid_size - 1)
            bx = self.grid_size - 3
            if self.env.grid.get(bx, by).type == 'floor':
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

            # Show Enemy as Ball
            if enemy in self.agent_pos:
                enemy_pos = tuple(self.agent_pos[enemy])
                prev_obj = self.env.grid.get(*enemy_pos)
                if prev_obj is None or prev_obj.type == 'floor':
                    self.env.grid.set(*enemy_pos, Ball(enemy))

            # Render View
            self.env.agent_pos = self.agent_pos[me]
            self.env.agent_dir = self.agent_dir[me]
            observations[me] = self.env.get_pov_render(tile_size=8)

            # Cleanup
            if enemy in self.agent_pos:
                self.env.grid.set(*enemy_pos, prev_obj)

        return observations

    def step(self, actions):
        rewards = {a: -0.01 for a in self.agents}
        terminations = {a: False for a in self.agents}
        truncations = {a: False for a in self.agents}
        infos = {a: {} for a in self.agents}

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

            # Win Condition
            target_pos = (self.grid_size - 2, self.grid_size //
                          2) if agent_id == "red" else (1, self.grid_size // 2)
            if tuple(self.env.agent_pos) == target_pos:
                rewards[agent_id] = 10.0
                for a in self.agents:
                    terminations[a] = True

        if self.steps >= self.max_steps:
            for a in self.agents:
                truncations[a] = True

        observations = self._get_observations()

        if any(terminations.values()) or any(truncations.values()):
            self.agents = []

        return observations, rewards, terminations, truncations, infos
