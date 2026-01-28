import numpy as np
from world_object import Flag, Base


def reward_policy(self, agent_id, rewards, actions, terminations):

    # --- 1. THE ECONOMY (TOBBE-ALIGNED) ---
    # We lower the jackpot so the step penalty feels "expensive"
    REWARD_SCORE_FLAG = 500.0          # Was 2000.0
    REWARD_SCORE_FLAG_TEAM = 100.0     # Was 1000.0

    # URGENCY (The Engine)
    # We increase the cost of time. They MUST hurry.
    PENALTY_STEP = -0.2                # Was -0.05. 4x higher pressure.

    # NAVIGATION (The Steering)
    # High reward for closing the distance (Manhattan)
    REWARD_CARRY_FLAG_HOME = 3.0       # Was 1.0. Stronger pull.
    REWARD_APPROACH_ENEMY_FLAG = 0.5

    # FEAR MANAGEMENT (The Brake Removal)
    # If this is too high, they freeze. Make it low.
    PENALTY_TAGGED_CARRYING = -5.0     # Was -50.0. huge reduction.
    PENALTY_TAGGED_EMPTY = -1.0

    # PHYSICS
    # We restore a small wall penalty so they learn to steer, not just crash.
    PENALTY_WALL_CARRYING = -0.1       # Tobbe uses -0.1
    PENALTY_WALL_EMPTY = -0.1

    # EVENTS
    REWARD_PICKUP_FLAG = 40.0          # Tobbe uses 40
    REWARD_TAG_ENEMY = 5.0             # Lower tag reward to focus on objective

    # Roles
    REWARD_DEFENDER_RADIUS = 0.1
    DEFENSE_ZONE = 4

    # --- SETUP ---
    DIR_TO_VEC = [np.array([1, 0]), np.array(
        [0, 1]), np.array([-1, 0]), np.array([0, -1])]
    action = actions[agent_id]
    my_team = "red" if "red" in agent_id else "blue"
    enemy_team = "blue" if my_team == "red" else "red"
    old_pos = np.array(self.agent_pos[agent_id])

    # Sync MiniGrid
    self.env.agent_pos = old_pos
    self.env.agent_dir = self.agent_dir[agent_id]

    # Key Locations
    my_base_t = tuple(self.flag_pos[my_team])
    enemy_flag_t = tuple(self.flag_pos[enemy_team])

    # --- 2. PROXIMITY SNAP (Keep this, it's good) ---
    forced_entry_happened = False
    if self.carrying_flag[agent_id]:
        # Manhattan distance check
        dist = abs(old_pos[0] - my_base_t[0]) + abs(old_pos[1] - my_base_t[1])
        if dist <= 1:
            self.env.agent_pos = np.array(self.flag_pos[my_team])
            forced_entry_happened = True

    # --- 3. STANDARD STEP ---
    if not forced_entry_happened:
        self.env.step(action)

    new_pos = np.array(self.env.agent_pos)
    new_dir = self.env.agent_dir
    current_pos_t = tuple(new_pos)

    # --- 4. REWARD CALCULATION ---

    # A. MOVEMENT SHAPING
    my_base_loc_arr = np.array(self.flag_pos[my_team])
    enemy_flag_loc_arr = np.array(self.flag_pos[enemy_team])

    if self.carrying_flag[agent_id]:
        # CARRIER: Tobbe's Homing Logic
        dist_to_my_base = np.sum(np.abs(new_pos - my_base_loc_arr))
        old_dist_to_my_base = np.sum(np.abs(old_pos - my_base_loc_arr))

        diff = old_dist_to_my_base - dist_to_my_base

        if diff > 0:
            # Moving Closer: Reward them heavily
            rewards[agent_id] += diff * REWARD_CARRY_FLAG_HOME
        else:
            # Moving Away or Staying Still: No Reward (Time penalty will hurt them)
            # We do NOT penalize navigation correction (going around walls)
            rewards[agent_id] += 0.0

    else:
        # EMPTY HANDED
        if self.roles[agent_id] == "attacker":
            dist_to_enemy_flag = np.sum(np.abs(new_pos - enemy_flag_loc_arr))
            old_dist_to_enemy_flag = np.sum(
                np.abs(old_pos - enemy_flag_loc_arr))
            diff = old_dist_to_enemy_flag - dist_to_enemy_flag
            rewards[agent_id] += diff * REWARD_APPROACH_ENEMY_FLAG

        elif self.roles[agent_id] == "defender":
            dist_to_my_base = np.sum(np.abs(new_pos - my_base_loc_arr))
            if dist_to_my_base <= DEFENSE_ZONE:
                rewards[agent_id] += REWARD_DEFENDER_RADIUS

    # B. COLLISIONS & TAGGING
    is_camping = (current_pos_t ==
                  my_base_t and not self.carrying_flag[agent_id])

    collision_happened = False

    if is_camping:
        collision_happened = True
    elif not forced_entry_happened:
        for other_id in self.possible_agents:
            if other_id == agent_id:
                continue

            if np.array_equal(new_pos, self.agent_pos[other_id]):
                # TAG
                if (enemy_team in other_id) and self.carrying_flag[other_id]:
                    # Respawn Enemy
                    spawn_pos = self.get_safe_spawn(other_id) if hasattr(
                        self, 'get_safe_spawn') else self.spawn_pos[other_id].copy()
                    self.agent_pos[other_id] = spawn_pos
                    self.carrying_flag[other_id] = False

                    f_pos = self.flag_pos[my_team]
                    self.env.grid.set(f_pos[0], f_pos[1], Flag(my_team))

                    rewards[agent_id] += REWARD_TAG_ENEMY

                    if self.carrying_flag[other_id]:
                        rewards[other_id] += PENALTY_TAGGED_CARRYING
                    else:
                        rewards[other_id] += PENALTY_TAGGED_EMPTY
                else:
                    collision_happened = True
                    break

    # C. RESOLVE MOVEMENT
    if collision_happened:
        self.agent_pos[agent_id] = old_pos
        if not self.carrying_flag[agent_id]:
            # Only punish collision if NOT carrying (let carrier push through fear)
            rewards[agent_id] += -0.1

        if np.random.rand() < 0.2:
            self.agent_dir[agent_id] = (self.agent_dir[agent_id] + 1) % 4

    elif not forced_entry_happened:
        if np.array_equal(old_pos, new_pos) and action == 2:
            # WALL COLLISION
            if self.carrying_flag[agent_id]:
                rewards[agent_id] += PENALTY_WALL_CARRYING
            else:
                rewards[agent_id] += PENALTY_WALL_EMPTY
        else:
            self.agent_pos[agent_id] = new_pos
            self.agent_dir[agent_id] = new_dir
    else:
        # Confirm forced entry
        self.agent_pos[agent_id] = new_pos

    # D. EVENTS
    current_pos_t = tuple(self.agent_pos[agent_id])

    # Pickup
    cell_item = self.env.grid.get(*current_pos_t)
    is_flag = cell_item and (
        cell_item.type == 'goal' or isinstance(cell_item, Flag))

    if is_flag and not self.carrying_flag[agent_id]:
        item_color = getattr(cell_item, 'color', None)
        if item_color == enemy_team or current_pos_t == enemy_flag_t:
            self.carrying_flag[agent_id] = True
            if current_pos_t == enemy_flag_t:
                self.env.grid.set(
                    current_pos_t[0], current_pos_t[1], Base(enemy_team))
            else:
                self.env.grid.set(current_pos_t[0], current_pos_t[1], None)
            rewards[agent_id] += REWARD_PICKUP_FLAG
            print(f"DEBUG: {agent_id} PICKED UP FLAG")

    # Score
    if current_pos_t == my_base_t and self.carrying_flag[agent_id]:
        rewards[agent_id] += REWARD_SCORE_FLAG
        print(f"DEBUG: {agent_id} SCORED +{REWARD_SCORE_FLAG}!")

        spawn_pos = self.get_safe_spawn(agent_id) if hasattr(
            self, 'get_safe_spawn') else self.spawn_pos[agent_id].copy()
        self.agent_pos[agent_id] = spawn_pos
        self.carrying_flag[agent_id] = False

        for a in self.possible_agents:
            terminations[a] = True
            if my_team in a:
                rewards[a] += REWARD_SCORE_FLAG_TEAM

    rewards[agent_id] += PENALTY_STEP
