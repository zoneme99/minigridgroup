from minigrid.core.world_object import Floor, Goal 
from world_object import Flag, Base
import numpy as np


def reward_policy(self, agent_id, rewards, actions, terminations, ):
    action = actions[agent_id]
    # (4x)
    # --- Identify Teams ---
    my_team = "red" if "red" in agent_id else "blue"
    enemy_team = "blue" if my_team == "red" else "red"

    # (4x)
    # 1. PREDICT THE NEXT MOVE
    # We use the underlying env to see where the move WOULD take us
    self.env.agent_pos = self.agent_pos[agent_id]
    self.env.agent_dir = self.agent_dir[agent_id]

    # (4x)
    # Get current pos before moving
    old_pos = np.array(self.agent_pos[agent_id])
    
    # (4x)
    # Simulate move
    self.env.step(action)
    new_pos = np.array(self.env.agent_pos)
    new_dir = self.env.agent_dir

    # (4x)
    # 3. FINALIZE POSITION
    current_pos_tuple = tuple(new_pos)
    my_flag_pos = tuple(self.flag_pos[my_team])
    is_camping = (current_pos_tuple == my_flag_pos and not self.carrying_flag[agent_id])



    # (4x)
    # 2. CHECK FOR COLLISIONS WITH OTHER PLAYERS
    collision_happened = False
    if is_camping: 
        collision_happened = True
    else:
        for other_id in self.possible_agents:
            if other_id == agent_id: continue
            
            if np.array_equal(new_pos, self.agent_pos[other_id]):
                # CASE A: It's the enemy flag carrier -> TAG!
                if (enemy_team in other_id) and self.carrying_flag[other_id]:
                
                
                    # 1. Reset the carrier
                    self.agent_pos[other_id] = self.get_safe_spawn(other_id)
                    self.carrying_flag[other_id] = False
                    

                    # 2. Reset the flag back to its home
                    # flag_home = self.flag_pos[enemy_team]
                    # self.env.grid.set(*flag_home, Flag(enemy_team))# Re-spawn flag object
                    
                    # 2. Reset the flag back to MY home (since the enemy was carrying it)
                    my_flag_home = self.flag_pos[my_team]
                    # We use Flag(my_team) because the enemy was carrying the flag they stole from me
                    self.env.grid.set(my_flag_home[0], my_flag_home[1], Flag(my_team))
                    
                    # rewards[agent_id] += 5.0  # Big defense reward
                    # (!) Test
                    rewards[agent_id] += 3.0  # Big defense reward
                    rewards[other_id] -= 2.0  # Penalty for being caught
                    # Note: Movement is allowed here because we "cleared" the space
                
                # CASE B: It's a teammate or a non-flag-carrying enemy -> BLOCK
                else:
                    collision_happened = True
                    break


    if collision_happened or is_camping:
        # Move failed, stay at old position
        self.agent_pos[agent_id] = old_pos
    else:
        # Move succeeded
        self.agent_pos[agent_id] = new_pos
        self.agent_dir[agent_id] = new_dir

    # (4x)
    # --- NEW CAPTURE LOGIC ---
    current_pos = tuple(self.agent_pos[agent_id])
    enemy_flag_loc = self.flag_pos[enemy_team]
    my_base_loc = self.flag_pos[my_team]

    # (4x)
    # 3. PICKUP LOGIC
    # Check if I am standing on the ENEMY flag
    if current_pos == enemy_flag_loc and not self.carrying_flag[agent_id]:
        # Is the flag actually there? (Has another teammate already taken it?)
        # We check the grid cell type to be sure
        cell_item = self.env.grid.get(*enemy_flag_loc)
        if cell_item and cell_item.type == "goal": 
            self.carrying_flag[agent_id] = True
            # Remove flag from grid, replace with floor
            # self.env.grid.set(*enemy_flag_loc, Floor(enemy_team))
            self.env.grid.set(*enemy_flag_loc, Base(enemy_team))
            # rewards[agent_id] += 2.0  # Reward for the individual grab
            # (!) Test
            rewards[agent_id] += 5.0

            # Optional: Small reward for the whole team for progress
            for a in self.agents:
                if my_team in a and a != agent_id:
                    # rewards[a] += 0.5
                    # (!) Test
                    rewards[a] += 2
    # (4x)
    # 4. RETURN & WIN LOGIC
    # Check if I am standing on MY base while carrying the ENEMY flag
    if current_pos == my_base_loc and self.carrying_flag[agent_id]:
        # VICTORY!
        # rewards[agent_id] += 10.0  
        #(!) Test
        rewards[agent_id] += 25.0 

        # --- NEW: Respawn the scorer so they aren't blocking the base ---
        self.agent_pos[agent_id] = self.get_safe_spawn(agent_id)
        self.carrying_flag[agent_id] = False # Drop the flag status

        # TEAM REWARD: Everyone on the red team wins if red scores!
        for a in self.possible_agents:
            if my_team in a:
                # rewards[a] += 5.0  # Shared victory bonus
                # (!) Test
                rewards[a] += 15.0
                terminations[a] = True
            else:
                terminations[a] = True # End game for losers too
