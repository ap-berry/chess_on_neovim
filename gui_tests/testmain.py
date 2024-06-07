
from pynvim import attach
import os
from dotenv import load_dotenv
load_dotenv()

from dynamic_stats import StatsWin, Stats
from board import BoardWin
from utils import find_buf, create_window, create_buf

import berserk 
from chess import Board, Move







nvim = attach("tcp", "127.0.0.1", 6789)
API_TOKEN = os.getenv("API_TOKEN")
session  = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)

MAINWINDOW_CONFIG = {
  "relative"  : "editor",
  "width"     : nvim.current.window.width,
  "height"    : nvim.current.window.height,
  "focusable" : True,
  "row"       : 0,
  "col"       : 0,
  "external"  : False,
  "zindex"    : 500,
  "border"    : "none"
}


# curwin = nvim.current.window
# curbuf = nvim.current.buffer

# em_buf = find_buf(nvim, "whatever")
# em_buf = em_buf if em_buf else create_buf(nvim, "whatever")

# mainwin = create_window(nvim, em_buf, True, MAINWINDOW_CONFIG)


STATSWINDOW_CONFIG = {
  "relative"  : "win",
  "win"       : 0 ,
  "width"     : 30,
  "height"    : 8,
  "focusable" : True,
  "row"       : 0,
  "col"       : 0,
  "external"  : False,
  "zindex"    : 901,
  "style"     : "minimal",
  "border"    : "none"
}

# sb = find_buf(nvim, "stats_buffer")
# statswin = StatsWin(nvim, sb, STATSWINDOW_CONFIG)

# boardwin = BoardWin(nvim, bb, None)


stream_events = client.board.stream_incoming_events()

for e in stream_events:
  print(e)
  if e["type"] == "gameStart":
    board = Board(e['game']['fen'])
    bb = find_buf(nvim, "board_buffer")
    board_window = BoardWin(nvim, bb, board, MAINWINDOW_CONFIG)
    board_window.draw_board()
    
    game_stream_events = client.board.stream_game_state(e["game"]["gameId"])
    for ge in game_stream_events:
      if ge["type"] == "gameState":
        moves = ge["moves"].split(" ")
        last_move = moves.pop()
        
        board_window.push_move(last_move)
        
    board_window.kill_window()
      
        







# def capture_stream():
#   stream = client.board.stream_incoming_events()
#   for e in stream:
#     if e["type"] == 'gameStart':
      
#       gamestream = client.board.stream_game_state(e["game"]["gameId"])
#       for g in gamestream:
#         if g["type"] == "gameFull":
#           boardwin.board.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'
#           boardwin.draw_board()
#         print(g,"\n")
      
#       #board = Board()
#       # statwin.draw_stats(data.format_readable(flip=False))

# def intercept_events():
#   event_stream = client.board.stream_incoming_events()
#   for e in event_stream:
#      pass
   
# capture_stream()
# statwin.draw_stats(["Waiting for events...."])
        
      
    

# nvim.exec_lua("""
#               function hihello()
#                 local m = vim.api.nvim_win_get_cursor(0)
#                 print(m)
#                 vim.api.nvim_win_set_cursor(0, m)
#               end""")

# nvim.command("noremap <LeftMouse> <cmd>lua hihello()<CR>")

