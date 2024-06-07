from pynvim import attach
from time import sleep
from sys import argv


spacer = "\u2000"
pieces = {
    "bK" : "\u2654",
    "bQ" : "\u2655",
    "bR" : "\u2656",
    "bB" : "\u2657",
    "bN" : "\u2658",
    "bP" : "\u2659",

    "wK" : "\u265A",
    "wQ" : "\u265B",
    "wR" : "\u265C",
    "wB" : "\u265D",
    "wN" : "\u265E",
    "wP" : "\u265F",
    "xX" : spacer
}


board_matrix = [
    ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
    ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
    ['xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX'],
    ['xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX'],
    ['xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX'],
    ['xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX'],
    ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
    ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR'],
]

nvim = attach('tcp', '127.0.0.1', 6789)

currentbuf = nvim.current.buffer
hl_src = nvim.new_highlight_source()
nvim.command("hi BlackSquare guibg=#b57614 || hi BorderColor guibg=#d5c4a1")
cell_width = int(argv[1])
cell_height = int(argv[2])

#board = [ spacer*cell_width*8+spacer*2 for i in range(cell_height*8+2) ]
board = [f"{pieces['bK']}"]
hl = [ ("BlackSquare", 0)]
currentbuf[:] = board
currentbuf.update_highlights(hl_src, hl, clear=True, async_=False)
