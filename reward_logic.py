from minigrid.core.world_object import Floor, Goal

# --- CLASS DEFINITION ---


class Flag(Goal):
    def __init__(self, color):
        super().__init__()
        self.color = color


def reward_policy(env, agent_id, rewards, actions, terminations):
    """
    NEUTRAL BASE TEMPLATE
    A fair, un-biased reward structure for the group to start from.
    """
    # 1. THE EXISTENCE TAX (Standard RL Practice)
    # A tiny penalty to encourage efficiency, but not panic.
    rewards[agent_id] -= 0.01

    # 2. HEAVY FLAG PENALTY
    # If we want our agents to force urgency we should enable this.
    # if env.carrying_flag[agent_id]:
    #    rewards[agent_id] -= 0.0

    # 3. EXECUTE MOVEMENT
    action = actions[agent_id]
    env.env.agent_pos = env.agent_pos[agent_id]
    env.env.agent_dir = env.agent_dir[agent_id]
    env.env.step(action)
    env.agent_pos[agent_id] = env.env.agent_pos
    env.agent_dir[agent_id] = env.env.agent_dir

    # 4. IDLE PENALTY (Kept low to prevent broken "stuck" agents)
    # This is a technical fix, not a strategic one.
    current_pos = tuple(env.env.agent_pos)
    if current_pos == env.last_positions[agent_id]:
        env.idle_counts[agent_id] += 1
    else:
        env.idle_counts[agent_id] = 0
        env.last_positions[agent_id] = current_pos

    if env.idle_counts[agent_id] > 10:
        rewards[agent_id] -= 0.1  # Gentle nudge, not a punishment

    # --- OBJECTIVE LOGIC ---
    enemy = "blue" if agent_id == "red" else "red"
    enemy_flag_loc = env.flag_pos[enemy]
    my_base_loc = env.flag_pos[agent_id]

    # 5. PICKUP REWARD (+1.0)
    # A small "cookie" to acknowledge the milestone.
    if current_pos == enemy_flag_loc and not env.carrying_flag[agent_id]:
        env.carrying_flag[agent_id] = True
        env.env.grid.set(*enemy_flag_loc, Floor(enemy))
        rewards[agent_id] += 1.0

    # 6. VICTORY REWARD (+10.0)
    # The clear goal, but not astronomically high.
    if current_pos == my_base_loc and env.carrying_flag[agent_id]:
        rewards[agent_id] += 10.0
        for a in env.agents:
            terminations[a] = True


def handle_combat(env, rewards):
    """
    Standard Zero-Sum Combat Logic.
    """
    if "red" in env.agent_pos and "blue" in env.agent_pos:
        red_p = tuple(env.agent_pos["red"])
        blue_p = tuple(env.agent_pos["blue"])

        if red_p == blue_p:
            for carrier, tagger in [("red", "blue"), ("blue", "red")]:
                if env.carrying_flag[carrier]:
                    # 7. COMBAT REWARDS (Symmetric)
                    # Carrier loses what Tagger gains. Fair trade.
                    rewards[carrier] -= 5.0
                    rewards[tagger] += 5.0

                    # Reset Carrier
                    env.carrying_flag[carrier] = False
                    env.agent_pos[carrier] = env.spawn_pos[carrier].copy()

                    # Return Flag
                    flag_home = env.flag_pos[tagger]
                    env.env.grid.set(*flag_home, Flag(tagger))
