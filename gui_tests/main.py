from pynvim import *
from menu import MenuWin
from utils import *
from time import sleep

nvim = attach("tcp", "127.0.0.1", 6789)


mb = find_buf(nvim, Buffers["mb"])
menu = MenuWin(nvim, mb)

set_global_var(nvim, "events", "")
#mainloop
while True:
    global_events = get_global_var(nvim, "events"       )
    if not global_events:
        continue
    
    global_events = global_events.split(" ")
    for e in global_events:
        if e == "":
            continue
        
        if e.startswith("pressed"):
            print(e)
            menu.options[menu._parse_pressed(e)]()
            
    set_global_var(nvim, "events", "")
    
    sleep(0.1)
    