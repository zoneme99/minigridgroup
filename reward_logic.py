from minigrid.core.world_object import Floor, Goal

# --- CLASS DEFINITIONS ---
# Included here so the Environment can import it for respawning flags


class Flag(Goal):
    def __init__(self, color):
        super().__init__()
        self.color = color


def reward_policy(env, agent_id, rewards, actions, terminations):
    """
    NEUTRAL / BALANCED REWARD SCHEME
    A fair starting point for the group. 
    """

    # --- DOCUMENTATION (From Main Branch) ---
    # env.agent_pos: Dictionary with keys for each agent, giving their (x, y) positions.
    # env.agent_dir: Dictionary, giving facing direction (int) for each agent.
    # env.carrying_flag: Dictionary, True if the agent is carrying a flag.
    # env.flag_pos: Dictionary, position of each team's flag.
    # env.steps: Current time step (int).
    # env.grid_size: Grid dimensions.
    # env.spawn_pos: Original spawn positions for each agent.
    # env.max_steps: Maximum steps per episode.
    # actions: Dictionary of last actions.

    # 1. THE EXISTENCE TAX
    # Small penalty to encourage movement, but low enough to allow some patience.
    rewards[agent_id] -= 0.01

    # 2. HEAVY FLAG PENALTY (Disabled for Neutral Start)
    # Uncomment this if you want to force the carrier to rush home.
    # if env.carrying_flag[agent_id]:
    #    rewards[agent_id] -= 0.1

    # 3. EXECUTE MOVEMENT (Physics)
    # We update the environment state here.
    action = actions[agent_id]
    env.env.agent_pos = env.agent_pos[agent_id]
    env.env.agent_dir = env.agent_dir[agent_id]
    env.env.step(action)
    env.agent_pos[agent_id] = env.env.agent_pos
    env.agent_dir[agent_id] = env.env.agent_dir

    # 4. IDLE PENALTY (Anti-Camping)
    # Prevents agents from freezing in place due to bugs or bad training.
    current_pos = tuple(env.env.agent_pos)

    # Initialize tracking if not present (Safety check)
    if not hasattr(env, "last_positions"):
        env.last_positions = {a: (-1, -1) for a in env.agents}
        env.idle_counts = {a: 0 for a in env.agents}

    if current_pos == env.last_positions[agent_id]:
        env.idle_counts[agent_id] += 1
    else:
        env.idle_counts[agent_id] = 0
        env.last_positions[agent_id] = current_pos

    # If stuck for 10 steps, apply a gentle nudge penalty
    if env.idle_counts[agent_id] > 10:
        rewards[agent_id] -= 0.1

    # --- OBJECTIVE LOGIC ---
    enemy = "blue" if agent_id == "red" else "red"
    enemy_flag_loc = env.flag_pos[enemy]
    my_base_loc = env.flag_pos[agent_id]

    # 5. PICKUP REWARD (+1.0)
    # Matches Main Branch. A small bonus to acknowledge the milestone.
    if current_pos == enemy_flag_loc and not env.carrying_flag[agent_id]:
        env.carrying_flag[agent_id] = True
        env.env.grid.set(*enemy_flag_loc, Floor(enemy))
        rewards[agent_id] += 1.0

    # 6. VICTORY REWARD (+10.0)
    # Matches Main Branch. The primary goal.
    if current_pos == my_base_loc and env.carrying_flag[agent_id]:
        rewards[agent_id] += 10.0
        for a in env.agents:
            terminations[a] = True


def handle_combat(env, rewards):
    """
    Handles Collision and Tagging.
    """
    # Only run if both agents are alive
    if "red" in env.agent_pos and "blue" in env.agent_pos:
        red_p = tuple(env.agent_pos["red"])
        blue_p = tuple(env.agent_pos["blue"])

        if red_p == blue_p:
            for carrier, tagger in [("red", "blue"), ("blue", "red")]:
                if env.carrying_flag[carrier]:
                    # 7. COMBAT REWARDS (Zero-Sum)
                    # The Carrier loses exactly what the Tagger gains.
                    # This is fair and neutral.
                    rewards[carrier] -= 5.0
                    rewards[tagger] += 5.0

                    # Reset Carrier
                    env.carrying_flag[carrier] = False
                    env.agent_pos[carrier] = env.spawn_pos[carrier].copy()

                    # Return Flag to Base
                    flag_home = env.flag_pos[tagger]
                    env.env.grid.set(*flag_home, Flag(tagger))
