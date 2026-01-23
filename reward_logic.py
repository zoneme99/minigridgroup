# from minigrid.core.world_object import Floor, Goal 
# from world_object import Flag, Base
# import numpy as np

# def reward_policy(self, agent_id, rewards, actions, terminations, ):
        
#     # 1. SETUP & SIMULATION
#     action = actions[agent_id]
#     my_team = "red" if "red" in agent_id else "blue"
#     enemy_team = "blue" if my_team == "red" else "red"

#     # Capture state BEFORE move
#     old_pos = np.array(self.agent_pos[agent_id])

#     # Simulate move in the underlying MiniGrid
#     self.env.agent_pos = old_pos
#     self.env.agent_dir = self.agent_dir[agent_id]
#     self.env.step(action)
    
#     # Capture results of simulation
#     new_pos = np.array(self.env.agent_pos)
#     new_dir = self.env.agent_dir

#     # Finalize Position
#     current_pos_tuple = tuple(new_pos)
#     my_flag_pos = tuple(self.flag_pos[my_team])
#     is_camping = (current_pos_tuple == my_flag_pos and not self.carrying_flag[agent_id])


#     # 2. CHECK FOR COLLISIONS WITH OTHER PLAYERS
#     collision_happened = False
#     if is_camping: 
#         collision_happened = True
#     else:
#         for other_id in self.possible_agents:
#             if other_id == agent_id: continue
            
#             if np.array_equal(new_pos, self.agent_pos[other_id]):
#                 # CASE A: It's the enemy flag carrier -> TAG!
#                 if (enemy_team in other_id) and self.carrying_flag[other_id]:
                                
#                     # A. Reset the carrier
#                     self.agent_pos[other_id] = self.get_safe_spawn(other_id)
#                     self.carrying_flag[other_id] = False
                    
#                     # B. Reset the flag back to MY home (since the enemy was carrying it)
#                     my_flag_home = self.flag_pos[my_team]
#                     # We use Flag(my_team) because the enemy was carrying the flag they stole from me
#                     self.env.grid.set(my_flag_home[0], my_flag_home[1], Flag(my_team))
                    
#                     rewards[agent_id] += 10.0  # Tagging reward (!) Original 5.0
#                     rewards[other_id] -= 5.0  # Penalty for being caught
                
#                 # CASE B: It's a teammate or a non-flag-carrying enemy -> BLOCK
#                 else:
#                     collision_happened = True
#                     break


#     if collision_happened or is_camping:
#         # Move failed, stay at old position
#         self.agent_pos[agent_id] = old_pos
#         rewards[agent_id] -= 0.01  # Small penalty for failed move or collision <---- test change
#     else:
#         # Move succeeded
#         self.agent_pos[agent_id] = new_pos
#         self.agent_dir[agent_id] = new_dir

    
#     # --- NEW CAPTURE LOGIC ---
#     current_pos = tuple(self.agent_pos[agent_id])
#     enemy_flag_loc = tuple(self.flag_pos[enemy_team])
#     my_base_loc = tuple(self.flag_pos[my_team])


#     # DEFENDER BEHAVIOR
#     if self.roles[agent_id] == "defender":

#         dist_to_own_flag = np.sum(np.abs(np.array(current_pos) - np.array(my_flag_pos)))

#         # Strong incentive to stay near own flag
#         # if dist_to_own_flag <= 3:
#         #     rewards[agent_id] += 0.05
#         # elif dist_to_own_flag <= 4:
#         #     rewards[agent_id] += 0.2
#         # else:
#         #     rewards[agent_id] -= 0.1

#         # Extra reward for intercepting enemy carrier
#         for other_id in self.possible_agents:
#             if enemy_team in other_id:
#                 dist_to_enemy = np.sum(np.abs(np.array(current_pos) - np.array(self.agent_pos[other_id])))
#                 # Reward being close to ANY enemy (not just flag carriers)
#                 if dist_to_enemy <= 5:
#                     rewards[agent_id] += (5 - dist_to_enemy) * 0.1
#                 # Extra reward if they're carrying the flag
#                 if self.carrying_flag[other_id]:
#                     rewards[agent_id] += (6 - min(dist_to_enemy, 6)) * 0.05



#     # ATTACKER BEHAVIOR
#     elif self.roles[agent_id] == "attacker":
        
#         # Calculate distances
#         dist_to_enemy_flag = np.sum(np.abs(np.array(current_pos) - np.array(enemy_flag_loc)))
#         dist_to_my_base = np.sum(np.abs(np.array(current_pos) - np.array(my_base_loc)))
        
#         # PHASE 1: Not carrying flag -> Reward moving toward enemy flag
#         if not self.carrying_flag[agent_id]:
#             # Check if enemy flag is still available (not already taken by teammate)
#             cell_item = self.env.grid.get(*enemy_flag_loc)
#             enemy_flag_available = (cell_item and cell_item.type == "goal")
            
#             if enemy_flag_available:
#                 # Reward getting closer to enemy flag
#                 if not hasattr(self, 'prev_dist_to_enemy_flag'):
#                     self.prev_dist_to_enemy_flag = {}
                
#                 if agent_id in self.prev_dist_to_enemy_flag:
#                     old_dist = self.prev_dist_to_enemy_flag[agent_id]
#                     improvement = old_dist - dist_to_enemy_flag
#                     rewards[agent_id] += improvement * 0.5  # Positive if closer, negative if further

#                 else:
#                     if dist_to_enemy_flag < 15:
#                         rewards[agent_id] += 0.1  # Small initial reward for starting to approach
                
#                 self.prev_dist_to_enemy_flag[agent_id] = dist_to_enemy_flag
                
#                 # Small bonus for being very close (keeps some positional reward)
#                 if dist_to_enemy_flag <= 2:
#                     rewards[agent_id] += 0.2
        
#         # PHASE 2: Carrying flag -> Reward moving toward own base
#         else:
#             if not hasattr(self, 'prev_dist_to_base'):
#                 self.prev_dist_to_base = {}
            
#             if agent_id in self.prev_dist_to_base:
#                 old_dist = self.prev_dist_to_base[agent_id]
#                 improvement = old_dist - dist_to_my_base
#                 rewards[agent_id] += improvement * 0.5  # Getting closer to base!

#             else:
#                 if dist_to_my_base < 15:
#                     rewards[agent_id] += 0.2  # Small initial reward for starting to return

            
#             # Store current distance for next step
#             self.prev_dist_to_base[agent_id] = dist_to_my_base
            
#             # Keep some positional rewards for being very close to scoring
#             if dist_to_my_base <= 2:
#                 rewards[agent_id] += 0.5


    
    
#     # 3. PICKUP LOGIC
#     # Check if I am standing on the ENEMY flag
#     if current_pos == enemy_flag_loc and not self.carrying_flag[agent_id]:
#         # Is the flag actually there? (Has another teammate already taken it?)
#         # We check the grid cell type to be sure
#         cell_item = self.env.grid.get(*enemy_flag_loc)
#         if cell_item and cell_item.type == "goal": 
#             self.carrying_flag[agent_id] = True
#             # Remove flag from grid, replace with the Base object
#             self.env.grid.set(*enemy_flag_loc, Base(enemy_team))
#             rewards[agent_id] += 10.0 # (!) Original 2.0

#             # Optional: Small reward for the whole team for progress
#             for a in self.agents:
#                 if my_team in a and a != agent_id:
#                     rewards[a] += 2 # (!) Original 0.5
    
#     # 4. RETURN & WIN LOGIC
#     # Check if I am standing on MY base while carrying the ENEMY flag
#     if current_pos == my_base_loc and self.carrying_flag[agent_id]:
#         # VICTORY!
#         rewards[agent_id] += 50.0 # (!) Original 10

#         # --- Respawn the scorer so they aren't blocking the base ---
#         self.agent_pos[agent_id] = self.get_safe_spawn(agent_id)
#         self.carrying_flag[agent_id] = False # Drop the flag status

#         # TEAM REWARD: Everyone on the red team wins if red scores!
#         for a in self.possible_agents:
#             if my_team in a:
#                 rewards[a] += 30.0 # (!) Original 5.0
#                 terminations[a] = True
#             else:
#                 terminations[a] = True # End game for losers too

#     rewards[agent_id] -= 0.05  # Small step penalty to encourage faster play






# from minigrid.core.world_object import Floor, Goal 
# from world_object import Flag, Base
# import numpy as np

# def reward_policy(self, agent_id, rewards, actions, terminations):
#     # --- 0. INITIALISERING AV TRACKING (Problem 2 lösning) ---
#     # Vi skapar dessa om de inte finns, för att hålla koll på agenternas rekord
#     if not hasattr(self, 'min_dist_to_enemy_flag'):
#         self.min_dist_to_enemy_flag = {}
#     if not hasattr(self, 'min_dist_to_base'):
#         self.min_dist_to_base = {}

#     # Om agenten saknar rekord (t.ex. nyss resetat), sätt till oändligt
#     if agent_id not in self.min_dist_to_enemy_flag:
#         self.min_dist_to_enemy_flag[agent_id] = float('inf')
#     if agent_id not in self.min_dist_to_base:
#         self.min_dist_to_base[agent_id] = float('inf')

#     # 1. SETUP & SIMULATION
#     action = actions[agent_id]
#     my_team = "red" if "red" in agent_id else "blue"
#     enemy_team = "blue" if my_team == "red" else "red"
#     old_pos = np.array(self.agent_pos[agent_id])

#     # Simulera rörelsen i MiniGrid-miljön
#     self.env.agent_pos = old_pos
#     self.env.agent_dir = self.agent_dir[agent_id]
#     self.env.step(action)
    
#     new_pos = np.array(self.env.agent_pos)
#     new_dir = self.env.agent_dir
#     current_pos_tuple = tuple(new_pos)
#     my_flag_pos = tuple(self.flag_pos[my_team])
    
#     # Camping-skydd: man får inte stå på sin egen flagga om man inte bär fiendens flagga
#     is_camping = (current_pos_tuple == my_flag_pos and not self.carrying_flag[agent_id])

#     # 2. KOLLISIONER & TAGS
#     collision_happened = False
#     if is_camping: 
#         collision_happened = True
#     else:
#         for other_id in self.possible_agents:
#             if other_id == agent_id: continue
            
#             if np.array_equal(new_pos, self.agent_pos[other_id]):
#                 # Fiende med flaggan? TAG!
#                 if (enemy_team in other_id) and self.carrying_flag[other_id]:
#                     # Återställ fienden
#                     self.agent_pos[other_id] = self.get_safe_spawn(other_id)
#                     self.carrying_flag[other_id] = False
                    
#                     # VIKTIGT: Nollställ fiendens rekord så de kan få nya belöningar på vägen tillbaka
#                     self.min_dist_to_base[other_id] = float('inf')
#                     self.min_dist_to_enemy_flag[other_id] = float('inf')
                    
#                     # Flytta tillbaka flaggan till mitt hem
#                     my_flag_home = self.flag_pos[my_team]
#                     self.env.grid.set(my_flag_home[0], my_flag_home[1], Flag(my_team))
                    
#                     rewards[agent_id] += 15.0  # Belöning för tagg
#                     rewards[other_id] -= 5.0   # Straff för att bli fångad
#                 else:
#                     # Annars är det bara en blockering (teampolare eller fiende utan flagga)
#                     collision_happened = True
#                     break

#     # Hantera lyckad/misslyckad rörelse
#     if collision_happened:
#         self.agent_pos[agent_id] = old_pos
#         rewards[agent_id] -= 0.08  # Litet straff för krock
#     else:
#         self.agent_pos[agent_id] = new_pos
#         self.agent_dir[agent_id] = new_dir

#     # Uppdatera nuvarande positioner för avståndsberäkning
#     current_pos = np.array(self.agent_pos[agent_id])
#     enemy_flag_loc = np.array(self.flag_pos[enemy_team])
#     my_base_loc = np.array(self.flag_pos[my_team])

#     # 3. ROLLSPECIFIKA BELÖNINGAR (Best-so-far logik)
    
#     # --- DEFENDER ---
#     if self.roles[agent_id] == "defender":
#         # Belöna närhet till fiender (särskilt de med flagga)
#         for other_id in self.possible_agents:
#             if enemy_team in other_id:
#                 dist_to_enemy = np.sum(np.abs(current_pos - self.agent_pos[other_id]))
#                 if dist_to_enemy <= 5:
#                     multiplier = 0.2 if self.carrying_flag[other_id] else 0.1
#                     rewards[agent_id] += (6 - dist_to_enemy) * multiplier

#     # --- ATTACKER ---
#     elif self.roles[agent_id] == "attacker":
#         if not self.carrying_flag[agent_id]:
#             # Fas 1: Gå mot fiendens flagga
#             dist = np.sum(np.abs(current_pos - enemy_flag_loc))
            
#             # Kolla om vi har nått ett nytt rekord-nära avstånd
#             if dist < self.min_dist_to_enemy_flag[agent_id]:
#                 if self.min_dist_to_enemy_flag[agent_id] != float('inf'):
#                     improvement = self.min_dist_to_enemy_flag[agent_id] - dist
#                     rewards[agent_id] += improvement * 0.5 # Belöna varje steg närmare
#                 self.min_dist_to_enemy_flag[agent_id] = dist
#         else:
#             # Fas 2: Bära flaggan hem till basen
#             dist = np.sum(np.abs(current_pos - my_base_loc))
            
#             if dist < self.min_dist_to_base[agent_id]:
#                 if self.min_dist_to_base[agent_id] != float('inf'):
#                     improvement = self.min_dist_to_base[agent_id] - dist
#                     rewards[agent_id] += improvement * 0.8 # Högre belöning på vägen hem
#                 self.min_dist_to_base[agent_id] = dist

#     # 4. PICKUP LOGIC
#     if np.array_equal(current_pos, enemy_flag_loc) and not self.carrying_flag[agent_id]:
#         cell_item = self.env.grid.get(*enemy_flag_loc)
#         if cell_item and cell_item.type == "goal": 
#             self.carrying_flag[agent_id] = True
#             self.env.grid.set(enemy_flag_loc[0], enemy_flag_loc[1], Base(enemy_team))
#             rewards[agent_id] += 15.0
            
#             # Nollställ "hemresans" rekord så vi kan börja mäta framsteg mot basen
#             self.min_dist_to_base[agent_id] = float('inf')

#             # Team-belöning: teampolaren blir också glad!
#             for a in self.possible_agents:
#                 if my_team in a and a != agent_id:
#                     rewards[a] += 3.0

#     # 5. RETURN & WIN LOGIC
#     if np.array_equal(current_pos, my_base_loc) and self.carrying_flag[agent_id]:
#         rewards[agent_id] += 100.0
        
#         # Nollställ agentens position efter mål
#         self.agent_pos[agent_id] = self.get_safe_spawn(agent_id)
#         self.carrying_flag[agent_id] = False
        
#         # Nollställ rekorden inför nästa runda
#         self.min_dist_to_enemy_flag[agent_id] = float('inf')

#         for a in self.possible_agents:
#             if my_team in a:
#                 rewards[a] += 30.0 # Hela laget vinner
#                 terminations[a] = True
#             else:
#                 terminations[a] = True # Fienden förlorar

#     # Tidsstraff (Step penalty) - håller agenten i rörelse
#     rewards[agent_id] -= 0.00


import numpy as np
from world_object import Flag, Base

def reward_policy(self, agent_id, rewards, actions, terminations):

    # --- Hyper ---
    REWARD_TAG_ENEMY = 3
    PENALTY_GETTING_TAGGED = -2
    REWARD_PICKUP_FLAG = 50
    PENALTY_COLLISION_PLAYER = -0.05
    PENALTY_COLLISION_WALL = -0.1
    # Homing
    # Rewards player for taking the quickest road home while carrying the flag (Manhattan Distance)
    REWARD_HOMING = 2.0
    # Gives a penalty if the player diverges from the quickest road flag (Manhattan Distance)
    PENALTY_HOMING = -0.03
    REWARD_SCORE_FLAG_TEAM = 50
    REWARD_SCORE_FLAG = 300
    PENALTY_STEP = (self.steps / self.max_steps) * 1 

    # --- Role specific rewards ---
    REWARD_DEFENDER_RADIUS = 0.1     # Belöning för att vara nära sin egen bas
    REWARD_ATTACKER_PROGRESS = 0.3   # Låg belöning för att gå mot fiendens flagga
    DEFENSE_ZONE = 3                 # Hur nära basen försvararen ska vara

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
    is_camping = (current_pos_tuple == my_flag_pos and not self.carrying_flag[agent_id])

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
                    spawn_pos = self.get_safe_spawn(other_id) if hasattr(self, 'get_safe_spawn') else self.spawn_pos[other_id].copy()
                    
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
        spawn_pos = self.get_safe_spawn(agent_id) if hasattr(self, 'get_safe_spawn') else self.spawn_pos[agent_id].copy()
        self.agent_pos[agent_id] = spawn_pos
        self.carrying_flag[agent_id] = False 

        # Team reward and termination
        for a in self.possible_agents:
            terminations[a] = True
            if my_team in a: 
                rewards[a] += REWARD_SCORE_FLAG_TEAM

    # Time penalty

    rewards[agent_id] += PENALTY_STEP