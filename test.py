import chess
import numpy as np


def board_to_tensor(board, include_legal_moves=True):
    """
    Konverterar ett schackbräde till en tensor med shape (12, 8, 8) eller (13, 8, 8).

    Channels:
    0-5: Vita pjäser (P, N, B, R, Q, K)
    6-11: Svarta pjäser (p, n, b, r, q, k)
    12: Legal moves (om include_legal_moves=True)
        1.0 = legal move för spelaren vars tur det är
        -1.0 = illegal move
    Args:
        board: chess.Board object
        include_legal_moves: Om True, lägg till channel för legal moves

    Returns:
        numpy array med shape (12, 8, 8) eller (13, 8, 8)
    """
    # Mapping från pjäs-symbol till channel index
    piece_to_channel = {
        "P": 0,
        "N": 1,
        "B": 2,
        "R": 3,
        "Q": 4,
        "K": 5,  # Vita
        "p": 6,
        "n": 7,
        "b": 8,
        "r": 9,
        "q": 10,
        "k": 11,  # Svarta
    }

    # Skapa tom tensor
    num_channels = 13 if include_legal_moves else 12
    tensor = np.zeros((num_channels, 8, 8), dtype=np.float32)

    # Få board som string och splitta i rader
    board_str = str(board)
    lines = board_str.strip().split("\n")

    # Iterera genom varje rad (8 rader)
    for row_idx, line in enumerate(lines):
        # Ta bort mellanslag och få bara pjäserna
        pieces = line.split()

        # Iterera genom varje kolumn (8 kolumner)
        for col_idx, piece in enumerate(pieces):
            if piece != ".":  # Om det inte är en tom ruta
                channel = piece_to_channel[piece]
                tensor[channel, row_idx, col_idx] = 1.0

    # Lägg till legal moves om det begärs
    if include_legal_moves:
        # Fyll hela channeln med -1 (illegal moves)
        tensor[12, :, :] = -1.0

        # Markera destination-rutor för alla legal moves med 1
        for move in board.legal_moves:
            to_square = move.to_square
            row = 7 - (to_square // 8)  # Konvertera från board index till rad
            col = to_square % 8
            tensor[12, row, col] = 1.0

    return tensor


board = chess.Board()
print(board)

board_tensor = board_to_tensor(board)
print(board_tensor.shape)  # Bör vara (12, 8, 8)
print(board_tensor)  # Visa tensorinnehållet
