from threading import Thread, Lock
from time import sleep
import berserk

import os
from dotenv import load_dotenv
load_dotenv()



from pynvim import attach
from chess import Board, Move


from dynamic_stats import StatsWin, StatsDict
from board import BoardWin
from utils import find_buf, config_gen


API_TOKEN = os.getenv("API_TOKEN")
session  = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)

events = []
lock = Lock()



nvim = attach("tcp", "127.0.0.1", 6789)

board: Board
boardWin: BoardWin
statsWin: StatsWin
stats: StatsDict = {}

def read_stream():
  print("reading stream")
  global events
  stream = client.board.stream_incoming_events()
  
  for event in stream:
    if event['type'] == "gameStart":
      events.append(event)
      game_events = client.board.stream_game_state(event['game']['gameId'])
      for game_event in game_events:
        with lock:
          events.append(game_event)
    else:
      with lock:
        events.append(event)


def read_events():
  print("reading events")
  global events
  i=0
  while True:
    with lock:
      if events:
        for event in events:
          print(event)
          process_new_event(event)
        events = []
      else:
        
        print(i)
        i+=1
    sleep(0.2)



def process_new_event(event):
  global board, boardWin, statsWin, stats
  if event['type'] == 'gameStart':
    game = event['game']  
    board = Board(fen=game['fen'])
    boardWin = BoardWin(nvim, fen=game['fen'])
    boardWin.draw_board()
    statsWin = StatsWin(nvim)
    stats = {}
    
  elif event['type'] == "gameFull":
    update_stats(event)
    statsWin.initialize_stats(stats)
    statsWin.draw()
    
    #update board move stack for middle of match connections
    state = event['state']
    moves = state['moves'].split(" ")

    if moves[0] != '':
      moves = list(map(Move.from_uci, moves))
      board.move_stack = moves.copy()
      
  elif event['type'] == 'gameState':
    process_gameState_event(event)
  else:
    print("to do\n")
  
def update_stats(event):
  global stats
  
  black = event['black']
  white = event['white']
  state = event['state']
  
  if "id" in event['black']:   
    stats.update({
      'bname': black['name'],
      'bflair': "@",
      'brating' : black['rating'],
      'btime' : state['btime'],
      'binc' : state['binc'],
      'btitle' : black['title'] or "--"
    })
  else:
    stats.update({
      'bname': 'StockFish' + str(black['aiLevel']),
      'bflair': "@",
      'brating' : '',
      'btime' : state['btime'],
      'binc' : state['binc'],
      'btitle' : ''
    })
    
    
  if "id" in event['white']:
    stats.update({
      'wname': white['name'],
      'wflair': "@",
      'wrating' : white['rating'],
      'wtime' : state['wtime'],
      'winc' : state['winc'],
      'wtitle' : white['title'] or "--"
    })
  else:
    stats.update({
      'wname': 'StockFish' + str(white['aiLevel']),
      'wflair': "@",
      'wrating' : '',
      'wtime' : state['wtime'],
      'winc' : state['winc'],
      'wtitle' : ''
    })
    
  stats.update({
    'speed' : event['speed'],
    "moves" : state['moves']
  })
  

def process_gameState_event(event):
  global board, boardWin, statsWin, stats
  moves = event['moves']
  status = event['status']
  
  if status == "started":
    if len(moves) > len(board.move_stack):
      #make move
      latest_move = moves.rsplit(" ", 1)[-1]
      if latest_move == "":
        raise "something went terribly fucking wrong"
      
      
      board.push_uci(latest_move)
      
      boardWin.display_push_move(board.move_stack[-1].uci())
      
      statsWin.sync_gui_time(wtime=event['wtime'], btime=event['btime'])
      statsWin._serialize_moves(board=board)
      statsWin.refresh_gui()
      statsWin.draw()

      
    elif len(moves) < len(board.move_stack):
      #takeback
      pass
    else:
      raise "WHAT THE FUCK" 
  elif status == "resign":
    statsWin.initialize_winner(event['winner'])
    statsWin.draw()
    
  
thread1 = Thread(target=read_stream)
thread2 = Thread(target=read_events)

thread1.start()
thread2.start()
