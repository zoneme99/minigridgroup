import functools
import gymnasium as gym
import numpy as np
from gymnasium.spaces import Discrete, Box
from pettingzoo import ParallelEnv
from minigrid.core.grid import Grid
from minigrid.core.mission import MissionSpace
from minigrid.core.world_object import Goal, Wall, Ball, Floor, Key
from minigrid.minigrid_env import MiniGridEnv
from reward_logic import reward_policy
from world_object import Flag


class CaptureTheFlagPZ(ParallelEnv):
    metadata = {"render_modes": ["human", "rgb_array"], "name": "ctf_v1"}

    def __init__(self, render_mode=None):
        # (4X)
        self.possible_agents = ["red_0", "red_1", "blue_0", "blue_2"]
    
        self.agents = self.possible_agents[:]
        self.render_mode = render_mode
        self.reward_policy = reward_policy

        # Grid Params
        self.grid_size = 12
        self.max_steps = 400  # Increased steps for the return trip

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
        return Box(low=0, high=255, shape=(56, 56, 3), dtype=np.uint8)

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return Discrete(3)

    def render(self):
        saved_objs = {}
        for agent in self.agents:
            if agent in self.agent_pos:
                pos = tuple(self.agent_pos[agent])
                saved_objs[agent] = self.env.grid.get(*pos)

                # (4x)
                team_color = "red" if "red" in agent else "blue"
                if self.carrying_flag.get(agent, False):
                    self.env.grid.set(*pos, Key(team_color)) # Use team color
                else:
                    self.env.grid.set(*pos, Ball(team_color)) # Use team color

        original_agent_pos = self.env.agent_pos
        self.env.agent_pos = (-1, -1)
        img = self.env.get_frame(highlight=False, tile_size=8)

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

        # (4X)
        # --- NEW: MEMORY STATE ---
        self.carrying_flag = {agent: False for agent in self.possible_agents}


        # 1. Build Walls
        self.env.grid = Grid(self.grid_size, self.grid_size)
        self.env.grid.wall_rect(0, 0, self.grid_size, self.grid_size)

        mid_x = self.grid_size // 2
        for i in range(1, self.grid_size - 1):
            for j in range(1, self.grid_size - 1):
                self.env.grid.set(i, j, Floor("red" if i < mid_x else "blue"))

        for y in range(1, self.grid_size - 1):
            # if y % 2 == 0:
            # (!) Test Fewer walls
            if y % 3 == 0:
                self.env.grid.set(mid_x, y, Wall())

        # 2. Random Obstacles
        obstacles = 0
        # while obstacles < 8:
        # (!) Test Fewer walls
        while obstacles < 6:
            x = np.random.randint(1, self.grid_size - 1)
            y = np.random.randint(1, self.grid_size - 1)
            if y == self.grid_size // 2:
                continue
            if (
                self.env.grid.get(x, y) is None
                or self.env.grid.get(x, y).type == "floor"
            ):
                self.env.grid.set(x, y, Wall())
                obstacles += 1

        # 3. Place Flags
        self.flag_pos = {
            "red": (1, self.grid_size // 2),
            "blue": (self.grid_size - 2, self.grid_size // 2),
        }
        self.env.grid.set(*self.flag_pos["red"], Flag("red"))
        self.env.grid.set(*self.flag_pos["blue"], Flag("blue"))

        # (4x)
        # 4. Spawns
        self.agent_pos = {}
        self.agent_dir = {}
        self.spawn_pos = {}

        for agent_id in self.possible_agents:
            # Determine team based on name (e.g., "red_0" -> "red")
            team = "red" if "red" in agent_id else "blue"
            self.agent_dir[agent_id] = 0 if team == "red" else 2
            
            # Find a valid spawn point for this specific agent
            while True:
                ry = np.random.randint(1, self.grid_size - 1)
                rx = 2 if team == "red" else self.grid_size - 3
                if self.env.grid.get(rx, ry).type == "floor":
                    # Check if another agent already spawned here to avoid overlap
                    if not any(np.array_equal(np.array([rx, ry]), p) for p in self.agent_pos.values()):
                        self.agent_pos[agent_id] = np.array([rx, ry])
                        self.spawn_pos[agent_id] = self.agent_pos[agent_id].copy()
                        break

        # (4x)
        # (!) Agent with Flag Collision 1/2
        # Save initial spawn positions so we can return agents here later
        # We must use .copy() so the spawn point doesn't move when the agent moves
        self.spawn_pos = {
            agent_id: self.agent_pos[agent_id].copy() 
            for agent_id in self.possible_agents
        }

        return self._get_observations(), {}

    # (4x)
    def _get_observations(self):
        observations = {}
        for me in self.agents:
            # We need to render ALL OTHER agents so 'me' can see them
            saved_objs = {}
            for other in self.agents:
                if other == me: continue
                
                pos = tuple(self.agent_pos[other])
                saved_objs[pos] = self.env.grid.get(*pos)
                
                # Render the other agent as a Ball
                team_color = "red" if "red" in other else "blue"
                # (!) This works
                # self.env.grid.set(*pos, Ball(team_color))
                
                # (!) This maybe doesn't work 
                #     it's suppose to make the AI see an enemy 
                #     carrying a flag as a key as well
                if self.carrying_flag.get(other, False):
                    self.env.grid.set(*pos, Key(team_color))
                else:
                    self.env.grid.set(*pos, Ball(team_color))

            # Render the POV for the current agent
            self.env.agent_pos = self.agent_pos[me]
            self.env.agent_dir = self.agent_dir[me]
            observations[me] = self.env.get_pov_render(tile_size=8)

            # Cleanup the grid for the next agent's observation
            for pos, obj in saved_objs.items():
                self.env.grid.set(*pos, obj)

        return observations

    # (4)
    def get_safe_spawn(self, agent_id):
        """Finds the spawn point or the closest available empty floor tile."""
        base_spawn = tuple(self.spawn_pos[agent_id])
        
        # If the exact spawn is empty, return it
        if not any(np.array_equal(base_spawn, p) for p in self.agent_pos.values()):
            return np.array(base_spawn)
        
        # Otherwise, search outward for the nearest Floor tile
        for radius in range(1, 4):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    check_pos = (base_spawn[0] + dx, base_spawn[1] + dy)
                    
                    # Check if within grid bounds
                    if 0 < check_pos[0] < self.grid_size and 0 < check_pos[1] < self.grid_size:
                        cell = self.env.grid.get(*check_pos)
                        # Must be floor and not occupied by anyone else
                        if cell and cell.type == "floor":
                            if not any(np.array_equal(check_pos, p) for p in self.agent_pos.values()):
                                return np.array(check_pos)
                                
        return np.array(base_spawn) # Fallback


    def step(self, actions):
        rewards = {a: -0.01 for a in self.agents}
        terminations = {a: False for a in self.agents}
        truncations = {a: False for a in self.agents}
        infos = {a: {} for a in self.agents}

        self.steps += 1

        for agent_id in self.agents:
            if agent_id not in actions:
                continue

            self.reward_policy(self, agent_id, rewards, actions, terminations)

        if self.steps >= self.max_steps:
            for a in self.agents:
                truncations[a] = True

        observations = self._get_observations()

        if any(terminations.values()) or any(truncations.values()):
            self.agents = []

        return observations, rewards, terminations, truncations, infos
