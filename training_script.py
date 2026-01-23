import torch
import matplotlib.pyplot as plt
import supersuit as ss
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.vec_env import VecFrameStack
from ctf_env import CaptureTheFlagPZ

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
print(torch.cuda.is_available())
print(torch.version.cuda)

# Initialize PettingZoo Env
env = CaptureTheFlagPZ(render_mode="rgb_array")


# env = ss.resize_v1(env, x_size=84, y_size=84)
# env = ss.color_reduction_v0(env, mode='full')
# env = ss.frame_stack_v1(env, 3)

# Convert to SB3 Vector Env
# This allows PPO to see "Red" and "Blue" as just two independent samples in a batch
vec_env = ss.pettingzoo_env_to_vec_env_v1(env)
# Concatenate them so PPO trains on 2 agents at once
# num_vec_envs=4 to better utilize GPU
vec_env = ss.concat_vec_envs_v1(
    vec_env, num_vec_envs=4, num_cpus=0, base_class="stable_baselines3"
)


print(f"Observation Space: {vec_env.observation_space.shape}")
# Should be (84, 84, 3) -> 84x84 pixels, 3 stacked frames

# Train with PPO
# We use CnnPolicy because we are using images
# Added device="cpu" to bypass the GPU error
# Increased batch size to fully utilize GPU memory
# model = PPO(
#     "CnnPolicy",
#     vec_env,
#     verbose=1,
#     batch_size=512,
#     learning_rate=1e-4,
#     device=device)

model = PPO(
    "MultiInputPolicy",
    vec_env,
    verbose=1,
    batch_size=4096,
    learning_rate=1e-4,
    ent_coef=0.05,  # High exploration
    n_steps=2048,  # More data per update
    device=device,
)


print("Starting Training...")
model.learn(total_timesteps=1_000_000)
print("Training Finished!")

# 5. Save the Champion
model.save("ctf_champion_1m_offensive")
# 3 million timesteps takes 444 min (8h) to train on a CPU
# On GPU it takes aound 35 min
