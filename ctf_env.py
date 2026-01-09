import gymnasium as gym
import numpy as np
from minigrid.core.grid import Grid
from minigrid.core.mission import MissionSpace
from minigrid.core.world_object import WorldObj, Goal, Wall, Ball, Floor
from minigrid.minigrid_env import MiniGridEnv


class Flag(Goal):
    def __init__(self, color):
        super().__init__()
        self.color = color


class CaptureTheFlagEnv(MiniGridEnv):
    def __init__(self, size=10, max_steps=100, **kwargs):
        self.size = size
        mission_space = MissionSpace(
            mission_func=lambda: "Capture the enemy flag!")

        self.agent1_pos = None
        self.agent2_pos = None

        super().__init__(
            mission_space=mission_space,
            grid_size=size,
            max_steps=max_steps,
            **kwargs
        )

    def _gen_grid(self, width, height):
        self.grid = Grid(width, height)

        # 1. Draw the Outer Walls
        self.grid.wall_rect(0, 0, width, height)

        # 2. Paint the Floor (Red Base vs Blue Base)
        mid_x = width // 2
        for i in range(1, width - 1):
            for j in range(1, height - 1):
                if i < mid_x:
                    self.grid.set(i, j, Floor('red'))
                else:
                    self.grid.set(i, j, Floor('blue'))

        # 3. Create the Midfield Barrier
        for y in range(1, height - 1):
            if y % 2 == 0:
                self.grid.set(mid_x, y, Wall())

        # 4. Place Flags
        self.grid.set(1, height // 2, Flag('red'))
        self.grid.set(width - 2, height // 2, Flag('blue'))

        # 5. Place Agents
        self.agent1_pos = (2, height // 2)
        self.agent1_dir = 0
        self.agent2_pos = (width - 3, height // 2)
        self.agent2_dir = 2

        self.agent_pos = self.agent1_pos
        self.agent_dir = self.agent1_dir
        self.mission = "Capture the flag!"

    def get_obs_for_agent(self, agent_id):
        # 1. Determine who is who
        if agent_id == 1:
            my_pos = self.agent1_pos
            my_dir = self.agent1_dir
            enemy_pos = self.agent2_pos
            enemy_color = 'blue'
        else:
            my_pos = self.agent2_pos
            my_dir = self.agent2_dir
            enemy_pos = self.agent1_pos
            enemy_color = 'red'

        # 2. HACK: Temporarily place the enemy as a Ball so the camera sees it
        previous_obj = self.grid.get(*enemy_pos)
        if previous_obj is None or previous_obj.type == 'floor':
            self.grid.set(*enemy_pos, Ball(enemy_color))

        self.agent_pos = my_pos
        self.agent_dir = my_dir

        # 3. GENERATE OBSERVATION
        # If we are in RGB mode, we return pixels (0-255).
        # If we are in default mode, we return integers.
        if self.render_mode == 'rgb_array':
            # tile_size=8 gives a 56x56 image for a 7x7 view
            pov = self.get_pov_render(tile_size=8)
            obs = {'image': pov}
        else:
            obs = self.gen_obs()

        # 4. Cleanup: Restore the floor/object
        self.grid.set(*enemy_pos, previous_obj)

        return obs

    def step_multi_agent(self, action_red, action_blue):
        # RED TURN
        self.agent_pos = self.agent1_pos
        self.agent_dir = self.agent1_dir

        obs, reward_red, terminated, truncated, _ = super().step(action_red)

        self.agent1_pos = self.agent_pos
        self.agent1_dir = self.agent_dir

        if tuple(self.agent1_pos) == (self.width - 2, self.height // 2):
            reward_red = 10
            terminated = True
        else:
            reward_red = -0.01

        # BLUE TURN
        self.agent_pos = self.agent2_pos
        self.agent_dir = self.agent2_dir

        obs, reward_blue, terminated_blue, _, _ = super().step(action_blue)

        self.agent2_pos = self.agent_pos
        self.agent2_dir = self.agent_dir

        if tuple(self.agent2_pos) == (1, self.height // 2):
            reward_blue = 10
            terminated_blue = True
        else:
            reward_blue = -0.01

        done = terminated or terminated_blue

        obs_red = self.get_obs_for_agent(1)
        obs_blue = self.get_obs_for_agent(2)

        return obs_red, reward_red, obs_blue, reward_blue, done
