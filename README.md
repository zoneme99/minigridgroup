# MiniGrid Tournament

- Researching...

Use this command in your terminal to install the requirements:

pip install -r requirements.txt

Connect the notebook to the environment:

1. Run: python -m ipykernel install --user --name=ctf_env --display-name "Python (CTF Project)"

2. Open your training_notebook.ipynb.

3. In the top-right corner of the notebook interface, click on the kernel name (it usually says "Python 3").

4. Select "Python (CTF Project)" from the list.


Enable GPU:

Important to check if "cu121" is the right version for your GPU. On RTX 5070 Ti, "cu128" works. 

Open a terminal and paste: 
pip uninstall torch torchvision torchaudio -y
pip cache purge  # optional, to clear old wheels
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
