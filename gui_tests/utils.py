from pynvim import Nvim, attach
from pynvim.api import Buffer, Window
from typing import Literal, Tuple


Buffers = {
  "mb" : "menu_buffer",
  "sb" : "stats_buffer",
  "bb" : "board_buffer"
}




def create_buf(nvim: Nvim, bufname: str) -> Buffer:
  """Listed by default, No scratch buffer"""
  buf =  nvim.api.create_buf(True, False)
  buf.name = bufname
  return buf

def list_buf_names(nvim: Nvim) -> any:
  return [buf.name for buf in nvim.buffers]

def find_buf(nvim: Nvim, bufname) -> Buffer | None:
  b = nvim.buffers._fetch_buffers()
  for buf in b:
    if buf.name.endswith(bufname):
      return buf
  return None

def buf_set_text(nvim: Nvim, buf: Buffer | int, start_row: int, start_col: int, end_row: int, end_col: int, text):
  """ {start_row} First line index
      {start_col} Starting column (byte offset) on first line
      {end_row} Last line index, inclusive
      {end_col} Ending column (byte offset) on last line, exclusive """
  nvim.api.buf_set_text(buf, start_row, start_col, end_row, end_col, text)

def buf_set_lines(nvim: Nvim, buf: Buffer | int,  text: list[str], start_line: int = 0, end_line: int = -1, strict_indexing: bool = True):
  """ clears everything if startline and endline not set
      Strict_indexing is on by default. To change set strict_indexing=False"""
  nvim.api.buf_set_lines(buf, start_line, end_line, strict_indexing, text)
    
#nvim_buf_set_text({buffer}, {start_row}, {start_col}, {end_row}, {end_col}, {replacement}) 

def create_window(nvim: Nvim, buf: Buffer, enter: bool, config: dict) -> Window:
  return nvim.api.open_win(buf, enter, config)

def hide_window(nvim: Nvim, window: Window):
  """ Closes window, Hides buffer"""
  nvim.api.win_hide(window)

class BadFenError(Exception):
  pass

def config_gen(nvim: Nvim, 
               relative_to: Literal['editor', 'win', 'cursor', 'mouse'] = "editor",
               win: Window | None = None,
               width: int | None = None,
               height: int | None = None,
               row: int | None = None,
               col: int | None = None,
               z_index: int = 300,
               config: Literal["center", "menu", "board"] | dict = False,
               minimal: bool = False,
               border: Literal["none", "single", "double", "rounded", "solid", "shadow"] = "none",
               ):
  
  _config = {
    'border' : border,
  }
  
  if minimal:
    _config['style'] = 'minimal'
  
  
  if config == 'menu':
    _config.update({
      'relative' : 'win',
      'win' : win.handle,
      'width' : 30 ,
      'height' : 20,
      'focusable' : True,
      'zindex' : z_index,
    })
    
    _config.update({
      'row' : (nvim.current.window.height - _config['height'])//2,
      'col' : (nvim.current.window.width - _config['width'])//2,
    })
  elif config == 'board':
    _config.update({
      'relative' : 'win',
      'win' : 0,
      'width' : 8*3,
      'height' : 8,
      'focusable': True,
      'zindex' : z_index,
      'row' : 0,
      'col' : 0
    })
  elif config == "stats":
    _config.update({
      "relative"  : "win",
      "win"       : 0 ,
      "width"     : 30,
      "height"    : 11,
      "focusable" : False,
      "row"       : 0,
      "col"       : 28,
      "external"  : False,
      "zindex"    : z_index,
      "style"     : "minimal",
      "border"    : "none"
    })
  
    
  print(_config['row'], _config['col'])
  
  return _config

def set_cursor(nvim: Nvim, win: Window, pos: Tuple[int, int] = (0, 0)):
 nvim.api.win_set_cursor(win, pos)
 
def window_set_title(nvim: Nvim, win: Window, title: str):
  nvim.api.win_set_var(win, "window_title", title)
  
def window_get_title(nvim: Nvim, win: Window) -> str | None:
  try:
    return nvim.api.win_get_var(win, "window_title")
  except:
    return None

def window_set_var(nvim: Nvim, win: Window, key: str, value: str):
  nvim.api.win_set_var(win, key, value)
  
def window_get_var(nvim: Nvim, win: Window, key: str) -> str | None:
  try:
    return nvim.api.win_get_var(win, key)
  except:
    return None

def find_window_from_title(nvim: Nvim, title: str) -> Window | None:
  for w in nvim.windows:
    wt = window_get_title(nvim, w)
    if wt == title:
      return wt
  return None






def noremap_lua_callback(nvim: Nvim, lua_file_path: str, lhs: str, rhs: str, silent: bool = True, current_buffer_specific: bool = False):
  with open(lua_file_path, 'r') as luafile:
    lua = luafile.read()
    nvim.exec_lua(lua)
    
    mapcommand = "noremap "
    
    if current_buffer_specific:
      mapcommand+=" <buffer> "
    
    mapcommand+=lhs
    mapcommand+=" "
    mapcommand+=rhs
    
    nvim.api.command(mapcommand)


def force_redraw(nvim: Nvim):
  nvim.command("redraw!")



def get_global_var(nvim: Nvim, key: str) -> str | None:
  try:
    return nvim.api.get_var(key)
  except:
    return None

def set_global_var(nvim: Nvim, key: str, value: str):
  nvim.api.set_var(key, value)

def add_events(nvim: Nvim, events: list[str] | str):
  if type(events) == list:
    for e in events:
      add_events(nvim, e)
  else:
    nvim.command(f"let g:events ..= '{events}'")

def test():
  nvim = attach("tcp", "127.0.0.1", 6789)
  
  noremap_lua_callback(nvim, "./lua/callback.lua", "<CR>", "<cmd>:lua myfunc()<CR>")

