from pynvim.api import Nvim, Buffer
from utils import create_buf, buf_set_lines, create_window, find_buf, config_gen, set_cursor, noremap_lua_callback
from berserk.utils import to_millis
from typing import Literal


from pynvim import attach
    


class MenuWin:
  def __init__(self, session: Nvim, menu_buffer: Buffer) -> None:
    self.session = session
    self.menu_buffer = menu_buffer if menu_buffer else create_buf(session, "menu_buffer")
    self.menu_window_config = config_gen(session, config='menu', border='shadow', win=session.current.window, minimal=True)
    self.menu_window = create_window(session, menu_buffer, True, config=self.menu_window_config)
    
    self.menu_buffer[:] = ["    Speaking from the past    ", "", " Option 1", " Option 2", " Kill"]
    self.options = [ 0, 0, self.kill_window ]
    
    self._set_current()
    set_cursor(session, self.menu_window, (2, 0))
    self._set_buffer_local_keymap()
    
    
  def _set_buffer_local_keymap(self):
    noremap_lua_callback(self.session, "./lua/callback.lua", "<CR>", "<cmd>:lua myfunc()<CR>")
    
  def _parse_pressed(self, pressed: str):
    return pressed.split(":")[1] - 2
  
  def _set_current(self):
    self.session.current.buffer = self.menu_buffer
    
  def kill_window(self):
    self.menu_buffer[:] = []
    self.session.api.win_close(self.menu_window, True)
    self.session.api.buf_delete(self.menu_buffer, { "force": True })
 
 
 
# def test():
#   nvim = attach("tcp", "127.0.0.1", 6789)
#   mb = find_buf(nvim, "menu_buffer")
#   m = MenuWin(nvim, mb)

# test()