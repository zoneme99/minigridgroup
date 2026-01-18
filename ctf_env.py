import functools
import gymnasium as gym
import numpy as np
from gymnasium.spaces import Discrete, Box
from pettingzoo import ParallelEnv
from minigrid.core.grid import Grid
from minigrid.core.mission import MissionSpace
from minigrid.core.world_object import Goal, Wall, Ball, Floor, Key
from minigrid.minigrid_env import MiniGridEnv
# IMPORT LOGIC & FLAG
from reward_logic import reward_policy, handle_combat, Flag


class CaptureTheFlagPZ(ParallelEnv):
    metadata = {"render_modes": ["human", "rgb_array"], "name": "ctf_v1"}

    def __init__(self, render_mode=None):
        self.possible_agents = ["red", "blue"]
        self.agents = self.possible_agents[:]
        self.render_mode = render_mode

        self.reward_policy = reward_policy
        self.handle_combat = handle_combat

        # Map Settings
        self.grid_size = 21
        self.max_steps = 400

        self.mission_space = MissionSpace(
            mission_func=lambda: "Capture the enemy flag!"
        )

        self.env = MiniGridEnv(
            grid_size=self.grid_size,
            max_steps=self.max_steps,
            mission_space=self.mission_space,
        )

        self.spawn_pos = {}

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return Box(low=0, high=255, shape=(56, 56, 3), dtype=np.uint8)

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return Discrete(3)

    def render(self):
        saved_objs = []
        for agent in self.agents:
            if agent in self.agent_pos:
                pos = tuple(self.agent_pos[agent])
                saved_objs.append((pos, self.env.grid.get(*pos)))

        for agent in self.agents:
            if agent in self.agent_pos:
                pos = tuple(self.agent_pos[agent])
                if self.carrying_flag.get(agent, False):
                    self.env.grid.set(*pos, Key(agent))
                else:
                    self.env.grid.set(*pos, Ball(agent))

        original_agent_pos = self.env.agent_pos
        self.env.agent_pos = (-1, -1)
        img = self.env.get_frame(highlight=False, tile_size=8)
        self.env.agent_pos = original_agent_pos

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

        # 2. Floor Coloring
        mid_x = self.grid_size // 2
        for i in range(1, self.grid_size - 1):
            for j in range(1, self.grid_size - 1):
                if i < mid_x:
                    self.env.grid.set(i, j, Floor("red"))
                elif i > mid_x:
                    self.env.grid.set(i, j, Floor("blue"))

        # 3. Center Spine
        for y in range(1, self.grid_size - 1):
            if y % 2 == 0:
                self.env.grid.set(mid_x, y, Wall())

        # 4. Mirrored Obstacles
        num_pairs = 0
        target_pairs = 15
        while num_pairs < target_pairs:
            x = np.random.randint(1, mid_x)
            y = np.random.randint(1, self.grid_size - 1)

            if y == self.grid_size // 2:
                continue

            if self.env.grid.get(x, y).type == "floor":
                self.env.grid.set(x, y, Wall())
                mirror_x = self.grid_size - 1 - x
                self.env.grid.set(mirror_x, y, Wall())
                num_pairs += 1

        # 5. Flags
        self.flag_pos = {
            "red": (1, self.grid_size // 2),
            "blue": (self.grid_size - 2, self.grid_size // 2),
        }
        self.env.grid.set(*self.flag_pos["red"], Flag("red"))
        self.env.grid.set(*self.flag_pos["blue"], Flag("blue"))

        # 6. Spawns - FIXED POSITIONS
        # Calculate the middle row
        mid_y = self.grid_size // 2

        self.agent_pos = {}
        # Red faces East (0), Blue faces West (2)
        self.agent_dir = {"red": 0, "blue": 2}

        self.last_positions = {"red": (-1, -1), "blue": (-1, -1)}
        self.idle_counts = {"red": 0, "blue": 0}

        # Force clear the spawn tiles (just in case random walls hit them)
        # Red Base (Left)
        self.env.grid.set(2, mid_y, Floor("red"))
        self.spawn_pos["red"] = np.array([2, mid_y])
        self.agent_pos["red"] = np.array([2, mid_y])

        # Blue Base (Right)
        self.env.grid.set(self.grid_size - 3, mid_y, Floor("blue"))
        self.spawn_pos["blue"] = np.array([self.grid_size - 3, mid_y])
        self.agent_pos["blue"] = np.array([self.grid_size - 3, mid_y])

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
                if prev_obj is None or prev_obj.type == "floor":
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
        rewards = {a: 0.0 for a in self.agents}
        terminations = {a: False for a in self.agents}
        truncations = {a: False for a in self.agents}
        infos = {a: {} for a in self.agents}

        self.steps += 1

        for agent_id in self.agents:
            if agent_id not in actions:
                continue
            self.reward_policy(self, agent_id, rewards, actions, terminations)

        self.handle_combat(self, rewards)

        if self.steps >= self.max_steps:
            for a in self.agents:
                truncations[a] = True

        observations = self._get_observations()
        if any(terminations.values()) or any(truncations.values()):
            self.agents = []

        return observations, rewards, terminations, truncations, infos
