import numpy as np
from world_object import Flag, Base


def reward_policy(self, agent_id, rewards, actions, terminations):
    STEP_FACTOR = self.steps / self.max_steps
    # --- Hyper ---
    REWARD_TAG_ENEMY = 250
    PENALTY_GETTING_TAGGED = -100
    REWARD_PICKUP_FLAG = 200
    PENALTY_COLLISION_PLAYER = -0.05
    PENALTY_COLLISION_WALL = -0.1
    # Homing
    # Rewards player for taking the quickest road home while carrying the flag (Manhattan Distance)
    REWARD_HOMING = 100
    # Gives a penalty if the player diverges from the quickest road flag (Manhattan Distance)
    PENALTY_HOMING = -5
    REWARD_SCORE_FLAG_TEAM = 250
    REWARD_SCORE_FLAG = 10000
    PENALTY_STEP = STEP_FACTOR * 1.5

    # --- Role specific rewards ---
    REWARD_DEFENDER_RADIUS = (
        0.5 - STEP_FACTOR
    ) * 50  # Belöning för att vara nära sin egen bas
    REWARD_ATTACKER_PROGRESS = (
        STEP_FACTOR * 50  # Låg belöning för att gå mot fiendens flagga
    )
    DEFENSE_ZONE = 3  # Hur nära basen försvararen ska vara

    # --- 1. SETUP ---
    action = actions[agent_id]
    my_team = "red" if "red" in agent_id else "blue"
    enemy_team = "blue" if my_team == "red" else "red"
    old_pos = np.array(self.agent_pos[agent_id])
    my_role = self.roles[agent_id]

    # Sync MiniGrid internal status
    self.env.agent_pos = old_pos
    self.env.agent_dir = self.agent_dir[agent_id]

    # Perform step
    self.env.step(action)

    new_pos = np.array(self.env.agent_pos)
    new_dir = self.env.agent_dir

    # Feature 1: Check if agent is trying to stand on/block their own flag spawn
    current_pos_tuple = tuple(new_pos)
    my_flag_pos = tuple(self.flag_pos[my_team])
    is_camping = current_pos_tuple == my_flag_pos and not self.carrying_flag[agent_id]

    # Positioner för logik
    my_base_loc = tuple(self.flag_pos[my_team])
    enemy_flag_loc = tuple(self.flag_pos[enemy_team])
    current_pos_tuple = tuple(new_pos)

    # --- ROLLSPECIFIK LOGIK ---
    dist_to_my_base = np.sum(np.abs(new_pos - np.array(my_base_loc)))
    dist_to_enemy_flag = np.sum(np.abs(new_pos - np.array(enemy_flag_loc)))
    old_dist_to_enemy_flag = np.sum(np.abs(old_pos - np.array(enemy_flag_loc)))

    if my_role == "defender":
        # Belöna försvarare för att hålla sig nära basen
        if dist_to_my_base <= DEFENSE_ZONE:
            rewards[agent_id] += REWARD_DEFENDER_RADIUS

    elif my_role == "attacker":
        # Belöna anfallare för framsteg mot flaggan (bara om de inte bär den)
        if not self.carrying_flag[agent_id]:
            if dist_to_enemy_flag < old_dist_to_enemy_flag:
                rewards[agent_id] += REWARD_ATTACKER_PROGRESS

    # --- 2. COLLISION & TAG-LOGIK ---
    collision_happened = False

    if is_camping:
        collision_happened = True
    else:
        for other_id in self.possible_agents:
            if other_id == agent_id:
                continue

            if np.array_equal(new_pos, self.agent_pos[other_id]):
                # If we collide with enemy carrying OUR flag -> TAG
                if (enemy_team in other_id) and self.carrying_flag[other_id]:
                    # Use get_safe_spawn if available, otherwise fallback to spawn_pos
                    spawn_pos = (
                        self.get_safe_spawn(other_id)
                        if hasattr(self, "get_safe_spawn")
                        else self.spawn_pos[other_id].copy()
                    )

                    self.agent_pos[other_id] = spawn_pos
                    self.carrying_flag[other_id] = False

                    # Reset flag to home
                    f_pos = self.flag_pos[my_team]
                    self.env.grid.set(f_pos[0], f_pos[1], Flag(my_team))

                    rewards[agent_id] += REWARD_TAG_ENEMY
                    rewards[other_id] += PENALTY_GETTING_TAGGED
                    print(f"DEBUG: {agent_id} TAGGED {other_id}!")
                else:
                    collision_happened = True
                    break

    # --- 3. MOVEMENT RESOLUTION ---
    if collision_happened:
        self.agent_pos[agent_id] = old_pos
        rewards[agent_id] += PENALTY_COLLISION_PLAYER
        # Prevent deadlock
        if np.random.rand() < 0.3:
            self.agent_dir[agent_id] = (self.agent_dir[agent_id] + 1) % 4
    else:
        # MiniGrid wall collision check
        if np.array_equal(old_pos, new_pos) and action == 2:
            rewards[agent_id] += PENALTY_COLLISION_WALL
        else:
            self.agent_pos[agent_id] = new_pos
            self.agent_dir[agent_id] = new_dir

    # --- 4. GOAL LOGIC ---
    current_pos = tuple(self.agent_pos[agent_id])
    enemy_flag_loc = tuple(self.flag_pos[enemy_team])
    my_base_loc = tuple(self.flag_pos[my_team])

    # PICKUP FLAG
    if current_pos == enemy_flag_loc and not self.carrying_flag[agent_id]:
        # Verification check from old code: is the flag actually there?
        cell_item = self.env.grid.get(enemy_flag_loc[0], enemy_flag_loc[1])
        if cell_item and (cell_item.type == "goal" or isinstance(cell_item, Flag)):
            self.carrying_flag[agent_id] = True
            self.env.grid.set(enemy_flag_loc[0], enemy_flag_loc[1], Base(enemy_team))
            rewards[agent_id] += REWARD_PICKUP_FLAG
            print(f"DEBUG: {agent_id} PICKED UP FLAG!")

    # HOMING REWARD
    if self.carrying_flag[agent_id]:
        old_dist = np.sum(np.abs(old_pos - np.array(my_base_loc)))
        new_dist = np.sum(np.abs(np.array(current_pos) - np.array(my_base_loc)))
        if new_dist < old_dist:
            rewards[agent_id] += REWARD_HOMING
        elif new_dist > old_dist:
            rewards[agent_id] += PENALTY_HOMING

    # SCORE & RESET (Feature 2: Respawn scorer to allow continuous play/multiple flags)
    if current_pos == my_base_loc and self.carrying_flag[agent_id]:
        rewards[agent_id] += REWARD_SCORE_FLAG
        print(f"DEBUG: {agent_id} SCORE!")

        # Reset the scorer so they don't block the base for teammates
        spawn_pos = (
            self.get_safe_spawn(agent_id)
            if hasattr(self, "get_safe_spawn")
            else self.spawn_pos[agent_id].copy()
        )
        self.agent_pos[agent_id] = spawn_pos
        self.carrying_flag[agent_id] = False

        # Team reward and termination
        for a in self.possible_agents:
            terminations[a] = True
            if my_team in a:
                rewards[a] += REWARD_SCORE_FLAG_TEAM

    # Time penalty

    rewards[agent_id] += PENALTY_STEP
