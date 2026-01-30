# Multi-Agent Capture the Flag (CTF) RL

A Reinforcement Learning environment where agents from two teams (Red vs. Blue) compete to capture the enemy flag and return it to their base.  
  
## Main Files
There are four main files that contains most of the code used in this project.  
- ctf_env.py   : Environment and Game Loop  
- reward_logic : Rewards, Actions and Collision  
- training_notebook.ipynb : Training Setup  
- final_tournament.ipynb : Runs the tournament with the agents from  the models directory  
  
## Environment Overview
The environment is built using **PettingZoo** (Parallel API) and **MiniGrid**.
- **Grid:** 17x17 symmetric arena with a central divider and mirrored obstacles.
- **Agents:** 4 agents (2 Red, 2 Blue).
- **Roles:** Automatically assigned at spawn into `Attacker` and `Defender` based on distance to base.

## Technical Specifications
- **Observation Space:** - `image`: (9, 84, 84) RGB tensor (3 stacked frames of 84x84 pixels).
  - `role`: Float (0 for Attacker, 1 for Defender).
- **Action Space:** `Discrete(3)` (Turn Left, Turn Right, Move Forward).
- **Frame Stacking:** Uses a stack of 3 frames to provide temporal context (detecting movement direction of others).

## Reward Structure
Behavior is shaped via the `reward_policy` in `reward_logic.py`:
- **Positive:** Picking up the enemy flag, returning the flag (Major), and tagging an enemy carrier.
- **Negative:** Step penalty (encourages speed), wall collisions, and being tagged while carrying the flag.
- **Role Shaping:** Defenders get small passive rewards for staying near the base; Attackers get rewards for minimizing distance to the enemy flag.

## Training
The agents are trained using **PPO (Proximal Policy Optimization)** via Stable Baselines3. The training setup is optimized for mid-range hardware (e.g., GTX 1080) with reduced batch sizes and memory-efficient rollout steps.

#### Installation

Use this command in your terminal to install the requirements:

pip install -r requirements.txt  
(If you run in to problems then try to remove [classic] from pettingzoo[classic], save and re-run pip install)

Connect the notebook to the environment:

1. Run: python -m ipykernel install --user --name=ctf_env --display-name "Python (CTF Project)"

2. Open your training_notebook.ipynb.

3. In the top-right corner of the notebook interface, click on the kernel name (it usually says "Python 3").

4. Select "Python (CTF Project)" from the list. (or use your standard .venv kernel)


#### Enable GPU:

Important to check if "cu121" is the right version for your GPU. On RTX 5070 Ti, "cu128" works. 

Open a terminal and paste: 
pip uninstall torch torchvision torchaudio -y
pip cache purge  # optional, to clear old wheels
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121


