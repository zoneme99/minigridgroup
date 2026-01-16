from minigrid.core.world_object import Floor


def reward_policy(self, agent_id, rewards, actions, terminations):
    action = actions[agent_id]
    self.env.agent_pos = self.agent_pos[agent_id]
    self.env.agent_dir = self.agent_dir[agent_id]
    self.env.step(action)
    self.agent_pos[agent_id] = self.env.agent_pos
    self.agent_dir[agent_id] = self.env.agent_dir

    # Available vars
    # - self.agent_pos: Dictionary with keys for each agent, giving their (x, y) positions on the grid.
    # - self.agent_dir: Dictionary, giving facing direction (as an int) for each agent.
    # - self.carrying_flag: Dictionary, True if the agent is carrying a flag.
    # - self.flag_pos: Dictionary, position of each team's flag.
    # - self.steps: Current time step (int).
    # - self.grid_size: Grid dimensions.
    # - self.spawn_pos: Original spawn positions for each agent.
    # - self.max_steps: Maximum steps per episode.
    # - actions: Dictionary of last actions (indices, up to Discrete(3)).

    # --- NEW CAPTURE LOGIC ---
    current_pos = tuple(self.env.agent_pos)
    enemy = "blue" if agent_id == "red" else "red"
    enemy_flag_loc = self.flag_pos[enemy]
    my_base_loc = self.flag_pos[agent_id]

    # 1. PICKUP
    if current_pos == enemy_flag_loc and not self.carrying_flag[agent_id]:
        self.carrying_flag[agent_id] = True
        self.env.grid.set(*enemy_flag_loc, Floor(enemy))
        rewards[agent_id] += 1.0  # Bonus for picking up

    # 2. RETURN & WIN
    if current_pos == my_base_loc and self.carrying_flag[agent_id]:
        rewards[agent_id] += 10.0  # Victory!
        for a in self.agents:
            terminations[a] = True
