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
    metadata = {"render_modes": ["human", "rgb_array"], "name": "ctf_v1"}

<<<<<<< HEAD
    def __init__(self, render_mode=None, grid_size=21, center_walls=2, mirrored_walls=15):
        
        self.possible_agents = ["red_0", "red_1", "blue_0", "blue_2"]
    
=======
    def __init__(self, render_mode=None):
        # (4X)
        self.possible_agents = ["red_1", "red_2", "blue_1", "blue_2"]

        # Team definitions
        self.teams = {
        "red": ["red_1", "red_2"],
        "blue": ["blue_1", "blue_2"],}

        # Frame Stacking
        self.stack_size = 3
        self.frames ={agent: deque(maxlen=self.stack_size) for agent in self.possible_agents}


>>>>>>> main
        self.agents = self.possible_agents[:]
        self.render_mode = render_mode
        self.reward_policy = reward_policy

<<<<<<< HEAD
        # Grid Hyper Parameters
        self.max_steps = grid_size*20 # Dynamic Scaling
        self.grid_size = grid_size 
        self.center_walls = center_walls # The higher the number the fewer the walls  
        self.mirrored_walls = mirrored_walls # The lower the number the fewer walls
        # Example 
        # First Training  (Easy) grid_size 12x12, center_walls 6, mirrored_walls 2 
        # Second Training (Medium) grid_size 16x16, center_walls 4, mirrored_walls 8 
        # Third Training  (Difficult/Default) grid_size 21x21, center_walls 2, mirrored_walls 15 
=======
        # Grid Params
        self.grid_size = 17 # otherwise 21
        self.max_steps = 800  # Increased steps for the return trip
>>>>>>> main

        self.mission_space = MissionSpace(
            mission_func=lambda: "Capture the enemy flag!"
        )

        self.env = MiniGridEnv(
            grid_size=self.grid_size,
            max_steps=self.max_steps,
            mission_space=self.mission_space,
        )
    
    # Add this property to satisfy the SB3 check
    @property
    def render_mode(self):
        return self._render_mode

    @render_mode.setter
    def render_mode(self, value):
        self._render_mode = value

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return gym.spaces.Dict({
        "image": Box(low=0, high=255, shape=(9, 84, 84), dtype=np.uint8),
        "role": Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)  # 0: Attacker, 1: Defender
    })

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return Discrete(3)

    def render(self):
        """Render what we, the observer, sees."""
        saved_objs = {}
        for agent in self.agents:
            if agent in self.agent_pos:
                pos = tuple(self.agent_pos[agent])
                saved_objs[agent] = self.env.grid.get(*pos)

                
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
        self.carrying_flag = {agent: False for agent in self.possible_agents}

        # 1. Grid
        self.env.grid = Grid(self.grid_size, self.grid_size)
        self.env.grid.wall_rect(0, 0, self.grid_size, self.grid_size)

        # 2. Floor Coloring
        mid_x = self.grid_size // 2
        for i in range(1, self.grid_size - 1):
            for j in range(1, self.grid_size - 1):
                self.env.grid.set(i, j, Floor("red" if i < mid_x else "blue"))

        # 3. Center Spine
        for y in range(1, self.grid_size - 1):
            if y % self.center_walls == 0:
                self.env.grid.set(mid_x, y, Wall())

        # 4. Mirrored Obstacles
        num_pairs = 0
<<<<<<< HEAD
        target_pairs = self.mirrored_walls
=======
        target_pairs = 10
>>>>>>> main
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

        # 5. Place Flags
        self.flag_pos = {
            "red": (1, self.grid_size // 2),
            "blue": (self.grid_size - 2, self.grid_size // 2),
        }
        self.env.grid.set(*self.flag_pos["red"], Flag("red"))
        self.env.grid.set(*self.flag_pos["blue"], Flag("blue"))

        
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
        

        # ROLE ASSIGNMENT  (USES EXISTING self.teams)
        self.roles = {}

        for team, agents_in_team in self.teams.items():
            f_pos = np.array(self.flag_pos[team])

            a0, a1 = agents_in_team

            dist0 = np.sum(np.abs(self.agent_pos[a0] - f_pos))
            dist1 = np.sum(np.abs(self.agent_pos[a1] - f_pos))

            if dist0 <= dist1:
                self.roles[a0] = "defender"
                self.roles[a1] = "attacker"
            else:
                self.roles[a0] = "attacker"
                self.roles[a1] = "defender"                

        # Save initial spawn positions so we can return agents here later
        self.spawn_pos = {
            agent_id: self.agent_pos[agent_id].copy() 
            for agent_id in self.possible_agents
        }

<<<<<<< HEAD
        return self._get_observations(), {agent: {} for agent in self.possible_agents}

=======
        # Töm kön vid varje reset så att gammal info från förra rundan inte hänger kvar
        self.frames = {agent: deque(maxlen=self.stack_size) for agent in self.possible_agents}
        

        return self._get_observations(), {}
>>>>>>> main

    def _get_observations(self):
        """Renders what the agent sees."""
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

                # Render the enemy agent carrying the flag as a key
                if self.carrying_flag.get(other, False):
                    self.env.grid.set(*pos, Key(team_color))
                else:
                    self.env.grid.set(*pos, Ball(team_color))

            # Render the POV for the current agent
            self.env.agent_pos = self.agent_pos[me]
            self.env.agent_dir = self.agent_dir[me]
            
            # tile_size=12 ger 84x84 pixlar
            pov_img = self.env.get_pov_render(tile_size=12) # Ger (84, 84, 3)
            # Transponera från (H, W, C) till (C, H, W)
            pov_img = np.transpose(pov_img, (2, 0, 1))
            # 2. Hantera Frame Stacking manuellt
            if len(self.frames[me]) == 0:
                # Vid första steget, fyll stacken med kopior av första bilden
                for _ in range(self.stack_size):
                    self.frames[me].append(pov_img)
            else:
                self.frames[me].append(pov_img)

            # Slå ihop de 3 bilderna till en (9, 84, 84) tensor
            stacked_img = np.concatenate(list(self.frames[me]), axis=0)

            # --- SKAPA DICT-OBSERVATIONEN ---
            role_id = 0 if self.roles[me] == "attacker" else 1
            
            observations[me] = {
                "image": stacked_img,
                "role": np.array([role_id], dtype=np.float32)
            }

            # Cleanup the grid for the next agent's observation
            for pos, obj in saved_objs.items():
                self.env.grid.set(*pos, obj)

        return observations

    
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
