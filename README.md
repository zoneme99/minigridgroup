# MiniGrid Tournament (2v2)

#### Implemented Features 
- Implemented 2v2 gameplay
- Less Random Walls 
	This is for testing so use ctrl+f and type "Fewer walls" to find where you can change it back, 
	(There is one line of code for the random walls and one line for the walls in the middle)
- Block Flag Spawn
	Prevent players from moving on to there own flag spawn point (unless they carry a flag)
	This is to prevent players from flag camping
- Players now block other players
	A player can move on top another player unless they carry a flag
- Advanced Respawn 
	Preventing players from respawning on top of each other after being tagged
- Individual and Team Rewards
	You can give rewards to the player or to the player team to encourage team work

#### Possible Improvements 
*Vision (What the agent sees)*
- Shared Vision (Encourage team work)
- Vision of the enemy that carries the flag (Encourage tagging)
- Individual Colors (Help with enforcing team role behavior)
*Rewards*
- Player Specific Rewards (Help with enforcing team role behavior)
*Gameplay*
- Double Flags (Discourage flag camping)
	Each team has two flags to protect 
- 3 Flags to Win (Longer games more complex behavior)
	Set the victory condition to be retrieve 3 flags
- Protect the Flag (Encourage tagging)
	Your own flag has to be home before you can turn in enemy flag 
- Prevent flag camping (ideas???)
*Observer (What we see)*
- Victory Screen 
- Replace graphics with pixel art

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


