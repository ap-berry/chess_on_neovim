from pynvim import attach
from pynvim.api import Nvim, Buffer
from utils import create_buf, buf_set_lines
from berserk.utils import to_millis




class DisplayInfoWin:
  def __init__(self, session: Nvim, stats_buffer: Buffer | None) -> None:
    self.stats_buffer = stats_buffer if stats_buffer else create_buf(session, "stats_buffer")
    self.session = session
    self.current_stats = None

  def draw_stats(self, stats: list[str]):
    buf_set_lines(nvim=self.session, buf=self.stats_buffer, text=stats)
    self.current_stats = stats
    
  def set_current(self):
    self.session.current.buffer = self.stats_buffer
  