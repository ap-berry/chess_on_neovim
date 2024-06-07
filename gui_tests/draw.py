from pynvim import attach
from time import sleep
from sys import argv
from numpy import array

spacer = "\u2000"
pieces = {
    "wK" : "\u2654",
    "wQ" : "\u2655",
    "wR" : "\u2656",
    "wB" : "\u2657",
    "wN" : "\u2658",
    "wP" : "\u2659",

    "bK" : "\u265A",
    "bQ" : "\u265B",
    "bR" : "\u265C",
    "bB" : "\u265D",
    "bN" : "\u265E",
    "bP" : "\u265F",
    "xX" : spacer
}


board_matrix = [
    ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
    ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
    ['xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX'],
    ['xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX'],
    ['xX', 'xX', 'xX', 'xX', 'wP', 'xX', 'xX', 'xX'],
    ['xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX', 'xX'],
    ['wP', 'wP', 'wP', 'wP', 'xX', 'wP', 'wP', 'wP'],
    ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR'],
]

board_matrix = array([array(ln) for ln in board_matrix])

nvim = attach('tcp', '127.0.0.1', 6789)

currentbuf = nvim.current.buffer
hl_src = nvim.new_highlight_source()
nvim.command("hi BlackSquare guibg=#b57614 || hi BorderColor guibg=#d5c4a1")
cell_width =  3
cell_height = 1
flip_board = False



#board highlight gen
border_gap = 1
hl = []
board = []
#board borderless
for i in range(8):
    line = ''
    for j in range(8):
        line+= spacer + pieces[board_matrix[i][j]] + spacer
        if (i+j) % 2 != 0:
            hl.append(("BlackSquare", i+border_gap, j*cell_width*3+border_gap, j*cell_width*3+cell_width*3+border_gap))
    board.append(line)

    
# hl += [ ("BorderColor", 0, 1, cell_width*8+1), ("BorderColor", 8*cell_height+1, 1, cell_width*8+1) ]
# hl += [ ("BorderColor", ln, 0, 1) for ln in range(8*cell_height+2) ] 
# hl += [ ("BorderColor", ln, cell_width*8+1, cell_width*8+1 +3) for ln in range(8*cell_height+2) ] 
# border_top = spacer*cell_width*8+spacer*2
# border_bottom = spacer*2 + (spacer*2).join(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']) + spacer*2
# board.insert(0, border_top)
# board.append(border_bottom)

nvim.api.buf_set_lines(0, 0, 11, False, board)
#nvim.command("call cursor(11, 1)")
#nvim.command("redraw!")
currentbuf.update_highlights(hl_src, hl, clear=True, async_=False)

while True:
    print(nvim.current.window.cursor)
    sleep(0.5)

