from pynvim import attach
from time import sleep
import berserk
from dotenv import load_dotenv
import datetime
import os
load_dotenv()


nvim =  attach("tcp", "127.0.0.1", 6789)

buf = nvim.api.create_buf(True, False)
win = nvim.api.open_win(buf, True, {
    "relative" : "win",
    "win" : nvim.current.window,
    "row" : 0,
    "col" : 8*3+6,
    "width": 20,
    "height" : 8,
    "anchor" : "NW",
    "style" : "minimal"
})


API_TOKEN = os.getenv("API_TOKEN")
session  = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)

# client.challenges.create_ai(level=1, clock_increment=5, clock_limit=10*60, variant="standard")
ongoing_game = client.games.get_ongoing()
incoming_events = client.board.stream_game_state(ongoing_game[0]['gameId'])


for e in incoming_events:
    print("haha")
    print(e)
    if e['type'] != "gameState":
        continue
    wtime = e["wtime"] - datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)
    btime = e["btime"] - datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)
    
    nvim.api.buf_set_lines(buf, 0, 2, False, [ f"White H:{wtime.seconds//3600} M:{wtime.seconds//60} S:{wtime.seconds%60}", 
                                              f"Black H:{btime.seconds//3600} M:{btime.seconds//60} S:{btime.seconds%60}"])

    

