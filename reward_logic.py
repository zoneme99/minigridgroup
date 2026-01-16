from minigrid.core.world_object import Floor


def reward_policy(self, agent_id, rewards, actions, terminations):
    action = actions[agent_id]
    self.env.agent_pos = self.agent_pos[agent_id]
    self.env.agent_dir = self.agent_dir[agent_id]
    self.env.step(action)
    self.agent_pos[agent_id] = self.env.agent_pos
    self.agent_dir[agent_id] = self.env.agent_dir

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
