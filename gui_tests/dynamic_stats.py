from pynvim.api import Nvim, Buffer
from utils import create_buf, buf_set_lines, create_window, find_buf, config_gen, force_redraw
from berserk.utils import to_millis
from datetime import datetime
from typing import Literal, Dict, TypedDict, Optional
from chess import Move, Board

class StatsDict(TypedDict, total=False):
    wname: str
    wflair: str
    wtitle: str
    wrating: int | str
    wtime: int
    winc: int
    bname: str
    bflair: str
    btitle: str
    brating: int | str
    btime: int
    binc: int
    speed: str
    moves: str

class Stats:
  def __init__(self, data: dict, myside : Literal["black", "white"]):
    self.data = data
    self.data_type = data["type"]
    self.wtime: int = to_millis(data["wtime"])
    self.btime: int = to_millis(data["btime"])
    self.move_list = []
    self.myside = myside
  
  def white_time(self) -> str:
    return self._timems_to_string(self.wtime, "White", "@")

  def black_time(self) -> str:
    return self._timems_to_string(self.btime, "Black", "@")
  
  def displayable(self, flip: bool = False):
    """ will flip automatically, set value to override"""
    
    _flip = self.myside == "black"
    _flip = not _flip if flip else flip # took me 15 minutes to figure out do not touch
    
    
    if self.data_type == "gameState":
      return self._displayable_gameState(_flip)
    elif self.data_type == "gameStart":
      return ["nothing to show yet..."]
    elif self.data_type == "gameFull":
      return ["nothing to show yet..."]
    elif self.data_type == "gameFinish":
      return ["nothing to show yet..."]
    
  def _displayable_gameState(self, flip: bool) -> list[str]:
    stats = self._serialize_moves(self.data["moves"]) 
    
    #add border
    stats.insert(0, "-----------------")
    stats.append("-----------------")
    
    if flip:
      stats.insert(0, self._timems_to_string(self.wtime, "White", "@"))
      stats.append(self._timems_to_string(self.btime, "Black", "@"))
    else:
      stats.insert(0, self._timems_to_string(self.btime, "Black", "@"))
      stats.append(self._timems_to_string(self.wtime, "White", "@"))
      
    return stats
  
    
  def _displayable_gameStart(self):
    _displayable_stats = self._serialize_moves('')
    
    
clear_stats = ["/ / / Waiting For Stats / / /",
              "/ / / / / / / / / / / / / / /",
              "/ / / / / / / / / / / / / / /",
              "/ / / / / / / / / / / / / / /",
              "/ / / / / / / / / / / / / / /",
              "/ / / / / / / / / / / / / / /",
              "/ / / / / / / / / / / / / / /",
              "/ / / / / / / / / / / / / / /",
              "/ / / / / / / / / / / / / / /",
              "/ / / / / / / / / / / / / / /",
              "/ / / / / / / / / / / / / / /",]

      
        

class StatsWin:
  """time and increment must be in ms"""
  def __init__(self, 
               session: Nvim, 
               stats: Optional[StatsDict] = None,
               window_config: Optional[dict]= None,):
    self.stats = stats
    self.stats_buffer = find_buf(session, "stats_buffer") or create_buf(session, "stats_buffer")
    self.session = session
    self.stats_win = create_window(self.session, self.stats_buffer, False, window_config or config_gen(session, config='stats'))
    
    
    
    if stats:
      self.initialize_stats(stats=stats)
      self.gui_initialized = True
    else:
      global clear_stats
      self.stats_gui = clear_stats
      self.gui_initialized = False
      
  def __str__(self) -> str:
    self.stats_gui = self.create_gui_ingame()
    return "\n".join(self.stats_gui)  
  
  def refresh_gui(self):
    self.stats_gui = self.create_gui_ingame()
    
  def initialize_winner(self, winner: str):
    self.set_winner(winner=winner)
    
    self.stats_gui = self.create_gui_winner()
    
  
  def initialize_stats(self, stats: StatsDict):
    self.lborder = '|'
    self.lpad = ' '
    self.spacer = '  '
    self.bar = '='*28

    self.wname = stats['wname']
    self.wflair = stats['wflair']
    self.wtime = self._timems_to_timestring(stats['wtime'])
    self.winc = self._timems_to_incstring(stats['winc'])
    self.wtitle = stats['wtitle']
    self.wrating = str(stats['wrating'])
    self.wate = 'todo'


    self.bname = stats['bname']
    self.bflair = stats['bflair']
    self.btime = self._timems_to_timestring(stats['btime'])
    self.binc = self._timems_to_incstring(stats['binc'])
    self.btitle = stats['btitle']
    self.brating = str(stats['brating'])
    self.bate = 'todo'

    self.index = [ "  " for i in range(3) ]
    self.formatted_moves = [ "---" for i in range(6)]
    

    self.gui_initialized = True
    self.stats_gui = self.create_gui_ingame()
    
  def create_gui_ingame(self) -> list[str]:
    assert self.gui_initialized == True, "Stats not initialized with data"
    return [
      "".join([self.lborder, self.lpad, self.bname, self.bflair, self.spacer, self.btitle, self.spacer, self.brating]),
      "".join([self.lborder, self.bar]),
      "".join([self.lborder, self.lpad, self.btime, self.spacer, self.binc, self.spacer, self.bate]),
      "".join([self.lborder, self.bar]),
      "".join([self.lborder, self.lpad, self.index[0], " ", self.formatted_moves[0], self.spacer, self.formatted_moves[1]]),
      "".join([self.lborder, self.lpad, self.index[1], " ", self.formatted_moves[2], self.spacer, self.formatted_moves[3]]),
      "".join([self.lborder, self.lpad, self.index[2], " ", self.formatted_moves[4], self.spacer, self.formatted_moves[5]]),
      "".join([self.lborder, self.bar]),
      "".join([self.lborder, self.lpad, self.wtime, self.spacer, self.winc, self.spacer, self.wate]),
      "".join([self.lborder, self.bar]),
      "".join([self.lborder, self.lpad, self.wname, self.wflair, self.spacer, self.wtitle, self.spacer, self.wrating]),
    ]
  
  def set_winner(self, winner: Literal["white", "black", "draw"]):
    if winner == "white":
      self.score = "1-0"
    elif winner == 'black':
      self.score == "0-1"  
    else:
      self.score = "1/2-1/2"
  
  
  def create_gui_winner(self) -> list[str]:
    assert self.gui_initialized == True, "Stats not initialized with data"
    return [
      "".join([self.lborder, self.lpad, self.bname, self.bflair, self.spacer, self.btitle, self.spacer, self.brating]),
      "".join([self.lborder, self.bar]),
      "".join([self.lborder, self.lpad, self.btime, self.spacer, self.binc, self.spacer, self.bate]),
      "".join([self.lborder, self.bar]),
      "".join([self.lborder, self.lpad, ]),
      "".join([self.lborder, self.lpad, self.spacer, self.spacer, "score:", self.spacer, self.score]),
      "".join([self.lborder, self.lpad, ]),
      "".join([self.lborder, self.bar]),
      "".join([self.lborder, self.lpad, self.wtime, self.spacer, self.winc, self.spacer, self.wate]),
      "".join([self.lborder, self.bar]),
      "".join([self.lborder, self.lpad, self.wname, self.wflair, self.spacer, self.wtitle, self.spacer, self.wrating]),
    ]
  
  def sync_gui_time(self, wtime:  datetime, btime: datetime):
    assert self.gui_initialized == True, "Stats not initialized with data"
    
    self.wtime = self._timems_to_timestring(to_millis(wtime))
    self.btime = self._timems_to_timestring(to_millis(btime))


  def _serialize_moves(self, board: Board):
    """ The board must at the position of the latest move"""
    # change formatted_moves list, change index list
    assert self.gui_initialized == True, "Stats not initialized with data"
    
    last6 = []
    moves_index = []
    _board = Board() #empty board because variation san plays the moves in sequence
    half_move_count = len(board.move_stack)
    offset = 3
    if half_move_count % 2 != 0:
      offset = 2
    _move_list = _board.variation_san(board.move_stack).split(" ")[-(6+offset):]
    for i, m in enumerate(_move_list):
      if i % 3 == 0:
        moves_index.append(m)
      else:
        last6.append(m)
      
      
    
    
    if len(moves_index) < 3:
      moves_index+= ["  " for i in range(3-len(moves_index))]   
    if len(last6) < 6:
      last6+= [ "----" for i in range(6-len(last6))]
    
    
    self.formatted_moves = last6
    self.index = moves_index

  
  def draw(self):
    buf_set_lines(nvim=self.session, buf=self.stats_buffer, text=self.stats_gui)
    force_redraw(nvim=self.session)
    
    
  def _set_current(self):
    self.session.current.buffer = self.stats_buffer
  
  
  @staticmethod
  def _timems_to_incstring(timems: int):
    assert timems <= 180*1000, "Increment cannot exceed 180s"
    m = timems//60000 % 60
    s = timems//1000 % 60
    return f"{m}:{ s if s > 9 else '0'+str(s)}"
    
    
  @staticmethod
  def _timems_to_timestring(timems: int):
    h = timems//3600000
    m = timems//60000 % 60
    s = timems//1000 % 60
    ms = timems % 3600000 #todo
    return f"{ str(h)+':' if h != 0 else '' }{ m if m > 9 else '0'+str(m) }:{ s if s > 9 else '0'+str(s) }"
