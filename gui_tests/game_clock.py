from typing import Literal, Tuple
from time import time
from datetime import datetime
from berserk.utils import to_millis



class GameClock:
  
  def __init__(self, 
               white_time: datetime, white_inc: int,
               black_time: datetime, black_inc: int,
               side: Literal["black", "white"]):
    """increment must be in miliseconds"""
    self.white_time = to_millis(white_time)
    self.white_inc = round(white_inc)
    
    self.black_time = to_millis(black_time)
    self.black_inc = round(black_inc)
    
    self.side = side
    self.started = False
    
    self.start()
    
  def start(self):
    self.started = True

  def change_sides(self):
    self.side = "black" if self.side == "white" else "white"
  def player_and_time_ms(self) -> Tuple[str, int]:
    """returns which player is playing and their remaining time in miliseconds (int) [player, time]"""
    assert self.started, "Clock Not Started"
    if self.side == "black":
      return Tuple(["black", round(time()*1000) - self.black_time])
    
    else:
      return Tuple(["white", round(time()*1000) - self.white_time])
    