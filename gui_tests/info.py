from pynvim import Nvim, attach
from utils import *
from time import sleep

from dynamic_stats import StatsWin
from board import BoardWin

from dotenv import set_key, get_key

nvim = attach("tcp", "127.0.0.1", 6789)

empty_info = [ 
              "Nothing to display yet!",
              "O_o"
              ]

class InfoWin():
  
  def __init__(self, 
               session: Nvim,
               relative_to_win: Window,
               window_config: dict | None = None):
    self.session = session
    
    self.buffer = find_buf(session, "info_buffer") or create_buf(session, "info_buffer")
    
    self.window = find_window_from_title(session, "InfoWindow") or create_window(session, self.buffer, False, window_config or config_gen(session, config="info",win=relative_to_win), "InfoWindow")
    
    self.info = empty_info
    
    
    
  def set_info(self, text: list[str]):
    if len(text) > 2:
      raise "info buffer should not be more than 2 lines"
    self.info = text

  def redraw(self):
    buf_set_lines(nvim=self.session, buf=self.buffer, text=self.info)
    force_redraw(nvim=self.session)
    

  

def test():
  current_w = nvim.current.window
  b = BoardWin(nvim, current_w)
  s = StatsWin(nvim, current_w)
  info = InfoWin(nvim, current_w)
  
  
  dummy_info = [
    '',
  ]
  
  b.redraw()
  s.redraw()  
  info.set_info(dummy_info)
  info.redraw()
  
  while True:
    if info.buffer[:] != dummy_info:
      dummy_info = info.buffer[:].copy()
      if len(dummy_info) > 1:
        # move = dummy_info[0].replace(" ", "")
        # b.draw_push_move(move)
        print(dummy_info[0])
        info.buffer[:] = []
    
test()