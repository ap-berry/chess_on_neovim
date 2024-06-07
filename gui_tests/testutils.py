from utils import *


from pynvim import attach

nvim = attach("tcp", "127.0.0.1", 6789)
buf = find_buf(nvim, "main_window")
if not buf:
  buf = create_buf(nvim=nvim, bufname="main_window")





