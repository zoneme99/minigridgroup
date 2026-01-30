from collections import deque
import functools
import gymnasium as gym
import numpy as np
from gymnasium.spaces import Discrete, Box, Dict
from pettingzoo import ParallelEnv
from minigrid.core.grid import Grid
from minigrid.core.mission import MissionSpace
from minigrid.core.world_object import Goal, Wall, Ball, Floor, Key
from minigrid.minigrid_env import MiniGridEnv
from reward_logic import reward_policy
from world_object import Flag

class CaptureTheFlagPZ(ParallelEnv):
    """
    A Multi-Agent Capture the Flag environment built on MiniGrid.
    Supports two teams (Red/Blue) with two roles (Attacker/Defender).
    """
    metadata = {"render_modes": ["human", "rgb_array"], "name": "ctf_v1"}

    def __init__(self, render_mode=None):
        self.possible_agents = ["red_1", "red_2", "blue_1", "blue_2"]
        self.teams = {
            "red": ["red_1", "red_2"],
            "blue": ["blue_1", "blue_2"], 
        }

        # Frame stacking configuration (C, H, W)
        self.stack_size = 3
        self.frames = {agent: deque(maxlen=self.stack_size) for agent in self.possible_agents}

        self.agents = self.possible_agents[:]
        self.render_mode = render_mode
        self.reward_policy = reward_policy

        self.grid_size = 17 
        self.max_steps = 800 

        self.mission_space = MissionSpace(
            mission_func=lambda: "Capture the enemy flag!"
        )

        self.env = MiniGridEnv(
            grid_size=self.grid_size,
            max_steps=self.max_steps,
            mission_space=self.mission_space,
        )

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        # Image: 3 channels * 3 stacked frames = 9. Role: Binary flag.
        return gym.spaces.Dict({
            "image": Box(low=0, high=255, shape=(9, 84, 84), dtype=np.uint8),
            "role": Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
        })

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return Discrete(3) # Left, Right, Forward

    def render(self):
        """Custom render to visualize multiple agents as Balls/Keys on the grid."""
        saved_objs = {}
        for agent in self.agents:
            if agent in self.agent_pos:
                pos = tuple(self.agent_pos[agent])
                saved_objs[agent] = self.env.grid.get(*pos)

                team_color = "red" if "red" in agent else "blue"
                # If carrying flag, display as Key; otherwise, Ball
                if self.carrying_flag.get(agent, False):
                    self.env.grid.set(*pos, Key(team_color))
                else:
                    self.env.grid.set(*pos, Ball(team_color))

        original_agent_pos = self.env.agent_pos
        self.env.agent_pos = (-1, -1) # Offset main MiniGrid agent to avoid ghosting
        img = self.env.get_frame(highlight=False, tile_size=8)

        self.env.agent_pos = original_agent_pos
        for agent in self.agents:
            if agent in self.agent_pos:
                pos = tuple(self.agent_pos[agent])
                self.env.grid.set(*pos, saved_objs[agent])

        return img

    def reset(self, seed=None, options=None):
        """Creates the Environment, randomizes walls, startingpossitions and assignes player roles"""
        self.agents = self.possible_agents[:]
        self.steps = 0
        if seed is not None:
            np.random.seed(seed)

        self.env.step_count = 0
        self.env.mission = self.mission_space.sample()
        self.carrying_flag = {agent: False for agent in self.possible_agents}

        # Setup symmetric grid
        self.env.grid = Grid(self.grid_size, self.grid_size)
        self.env.grid.wall_rect(0, 0, self.grid_size, self.grid_size)

        mid_x = self.grid_size // 2
        for i in range(1, self.grid_size - 1):
            for j in range(1, self.grid_size - 1):
                self.env.grid.set(i, j, Floor("red" if i < mid_x else "blue"))

        # Add center divider with gaps
        for y in range(1, self.grid_size - 1):
            if y % 2 == 0:
                self.env.grid.set(mid_x, y, Wall())

        # Generate mirrored random obstacles
        num_pairs = 0
        target_pairs = 10
        while num_pairs < target_pairs:
            x = np.random.randint(1, mid_x)
            y = np.random.randint(1, self.grid_size - 1)
            if y == self.grid_size // 2: continue

            if self.env.grid.get(x, y).type == "floor":
                self.env.grid.set(x, y, Wall())
                self.env.grid.set(self.grid_size - 1 - x, y, Wall())
                num_pairs += 1

        self.flag_pos = {
            "red": (1, self.grid_size // 2),
            "blue": (self.grid_size - 2, self.grid_size // 2),
        }
        self.env.grid.set(*self.flag_pos["red"], Flag("red"))
        self.env.grid.set(*self.flag_pos["blue"], Flag("blue"))

        self.agent_pos = {}
        self.agent_dir = {}
        self.spawn_pos = {}

        # Initialize spawn positions and directions
        for agent_id in self.possible_agents:
            team = "red" if "red" in agent_id else "blue"
            self.agent_dir[agent_id] = 0 if team == "red" else 2

            while True:
                ry = np.random.randint(1, self.grid_size - 1)
                rx = 2 if team == "red" else self.grid_size - 3
                if self.env.grid.get(rx, ry).type == "floor":
                    if not any(np.array_equal(np.array([rx, ry]), p) for p in self.agent_pos.values()):
                        self.agent_pos[agent_id] = np.array([rx, ry])
                        self.spawn_pos[agent_id] = self.agent_pos[agent_id].copy()
                        break

        # Dynamic Role Assignment based on proximity to base
        self.roles = {}
        for team, agents_in_team in self.teams.items():
            f_pos = np.array(self.flag_pos[team])
            a0, a1 = agents_in_team
            dist0 = np.sum(np.abs(self.agent_pos[a0] - f_pos))
            dist1 = np.sum(np.abs(self.agent_pos[a1] - f_pos))

            if dist0 <= dist1:
                self.roles[a0], self.roles[a1] = "defender", "attacker"
            else:
                self.roles[a0], self.roles[a1] = "attacker", "defender"

        # Clear frame buffers for new episode
        self.frames = {agent: deque(maxlen=self.stack_size) for agent in self.possible_agents}

        return self._get_observations(), {}

    def _get_observations(self):
        """Renders what the Agents sees"""
        observations = {}
        for me in self.agents:
            saved_objs = {}
            # Temporary place other agents in the grid for POV rendering
            for other in self.agents:
                if other == me: continue
                pos = tuple(self.agent_pos[other])
                saved_objs[pos] = self.env.grid.get(*pos)
                team_color = "red" if "red" in other else "blue"
                
                # Render enemy carrier as Key to help agent identify high-priority targets
                if self.carrying_flag.get(other, False):
                    self.env.grid.set(*pos, Key(team_color))
                else:
                    self.env.grid.set(*pos, Ball(team_color))

            self.env.agent_pos = self.agent_pos[me]
            self.env.agent_dir = self.agent_dir[me]

            # Generate and stack images
            pov_img = self.env.get_pov_render(tile_size=12) 
            pov_img = np.transpose(pov_img, (2, 0, 1))
            
            if len(self.frames[me]) == 0:
                for _ in range(self.stack_size):
                    self.frames[me].append(pov_img)
            else:
                self.frames[me].append(pov_img)

            stacked_img = np.concatenate(list(self.frames[me]), axis=0)
            role_id = 0 if self.roles[me] == "attacker" else 1

            observations[me] = {
                "image": stacked_img,
                "role": np.array([role_id], dtype=np.float32)
            }

            # Grid cleanup
            for pos, obj in saved_objs.items():
                self.env.grid.set(*pos, obj)

        return observations

    def get_safe_spawn(self, agent_id):
        """BFS-like search for the nearest valid tile to spawn an agent without overlap."""
        base_spawn = tuple(self.spawn_pos[agent_id])
        if not any(np.array_equal(base_spawn, p) for p in self.agent_pos.values()):
            return np.array(base_spawn)

        for radius in range(1, 4):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    check_pos = (base_spawn[0] + dx, base_spawn[1] + dy)
                    if 0 < check_pos[0] < self.grid_size and 0 < check_pos[1] < self.grid_size:
                        cell = self.env.grid.get(*check_pos)
                        if cell and cell.type == "floor":
                            if not any(np.array_equal(check_pos, p) for p in self.agent_pos.values()):
                                return np.array(check_pos)
        return np.array(base_spawn)

    def step(self, actions):
        """The main Training and Game Loop Function"""
        rewards = {a: -0.01 for a in self.agents}
        terminations = {a: False for a in self.agents}
        truncations = {a: False for a in self.agents}
        infos = {a: {} for a in self.agents}

        self.steps += 1
        for agent_id in self.agents:
            if agent_id in actions:
                self.reward_policy(self, agent_id, rewards, actions, terminations)

        if self.steps >= self.max_steps:
            for a in self.agents: truncations[a] = True

        observations = self._get_observations()
        if any(terminations.values()) or any(truncations.values()):
            self.agents = []

        return observations, rewards, terminations, truncations, infos