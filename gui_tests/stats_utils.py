from chess import Board

def timems_to_incstring(timems: int):
    assert timems <= 180 * 1000, "Increment cannot exceed 180s"
    m = timems // 60000 % 60
    s = timems // 1000 % 60
    return f"{m}:{ s if s > 9 else '0'+str(s)}"


def timems_to_timestring(timems: int):
    h = timems // 3600000
    m = timems // 60000 % 60
    s = timems // 1000 % 60
    ms = timems % 3600000  # todo
    return f"{ str(h)+':' if h != 0 else '' }{ m if m > 9 else '0'+str(m) }:{ s if s > 9 else '0'+str(s) }"

def white_pieces_taken(board: Board):
    """ white pieces are refered as uppercase letters"""
    pieces_taken = {
        "king": 1,
        "queen": 1,
        "pawn" : 8,
        "knight": 2,
        "bishop": 2,
        "rook": 2,
    }
    for c in board.board_fen():
        if c == "K":
            pieces_taken['king']-=1
        elif c == "Q":
            pieces_taken["queen"]-=1
        elif c == "N":
            pieces_taken["knight"]-=1
        elif c == "B":
            pieces_taken["bishop"]-=1
        elif c == "P":
            pieces_taken["pawn"]-=1
        elif c == "R":
            pieces_taken["rook"]-=1
        
    total = pieces_taken["queen"]*9
    + pieces_taken['bishop']*3
    + pieces_taken['knight']*3 
    + pieces_taken['rook']*5
    + pieces_taken['pawn']

    return [pieces_taken, total]

def black_pieces_taken(board: Board):
    """ black pieces are refered as lowercase letters"""
    pieces_taken = {
        "king": 1,
        "queen": 1,
        "pawn" : 8,
        "knight": 2,
        "bishop": 2,
        "rook": 2,
    }
    for c in board.board_fen():
        if c == "k":
            pieces_taken['king']-=1
        elif c == "q":
            pieces_taken["queen"]-=1
        elif c == "n":
            pieces_taken["knight"]-=1
        elif c == "b":
            pieces_taken["bishop"]-=1
        elif c == "p":
            pieces_taken["pawn"]-=1
        elif c == "r":
            pieces_taken["rook"]-=1
        
    total = pieces_taken["queen"]*9
    + pieces_taken['bishop']*3
    + pieces_taken['knight']*3 
    + pieces_taken['rook']*5
    + pieces_taken['pawn']

    return [pieces_taken, total]

