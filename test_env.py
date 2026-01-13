import matplotlib.pyplot as plt
import numpy as np
from ctf_env import CaptureTheFlagPZ

# 1. Initialize
env = CaptureTheFlagPZ(render_mode="rgb_array")
observations, infos = env.reset()

print("Environment initialized!")
print("Agents:", env.possible_agents)
print("Observation Shape:", observations["red"].shape)  # Should be (56, 56, 3)

# 2. Visualize Initial State
fig, ax = plt.subplots(1, 2, figsize=(10, 5))
ax[0].imshow(observations["red"])
ax[0].set_title("Red View")
ax[1].imshow(observations["blue"])
ax[1].set_title("Blue View")
plt.show()

# 3. Run a Quick Random Episode
print("Running random episode...")
for i in range(10):
    # Create random actions for all active agents
    actions = {agent: env.action_space(agent).sample() for agent in env.agents}

    observations, rewards, terms, truncs, infos = env.step(actions)

    print(f"Step {i}: Rewards {rewards}")

    if not env.agents:
        print("Game Over!")
        break
