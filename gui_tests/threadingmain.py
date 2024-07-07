from threading import Thread, Lock
from time import sleep
from typing import Literal, Optional, TypedDict
from dotenv import load_dotenv
import os

from pynvim import attach
import berserk

import utils
from menuWin import MenuWin
from gameWin import GameWinManager

load_dotenv()


API_TOKEN = os.getenv("API_TOKEN")
session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)

events = []
lock = Lock()


nvim = attach("tcp", "127.0.0.1", 6789)
app_page = "HomePage"


menuWin = MenuWin(nvim, client)
gameWinManager: GameWinManager = None


def read_stream():
    print("reading stream")
    global events
    stream = client.board.stream_incoming_events()

    for event in stream:
        if event["type"] == "gameStart":
            game_events = client.board.stream_game_state(event["game"]["gameId"])

            events.append(event)
            print("Now reading game events")
            for game_event in game_events:
                with lock:
                    events.append(game_event)
        else:
            with lock:
                events.append(event)


class AppEvent(TypedDict):
    page: Literal["Home", "Game"]
    event: str
    opts: dict


"""app_events will the be the global variable that will have all the gui related events"""

utils.set_global_var(nvim, "app_events", [])


def read_events():
    print("reading events")
    global events, nvim, menuWin, gameWinManager, client
    while True:
        app_events = utils.get_global_var(nvim, "app_events")
        utils.set_global_var(nvim, "app_events", [])
        if gameWinManager:
            with lock:
                if events:
                    for event in events:
                        print(event)
                        gameWinManager.process_new_event(event)
                    events = []
                else:
                    pass
                    gameWinManager.decrement_game_clock()
        for app_event in app_events:
            app_event: AppEvent = app_event
            opts = app_event["opts"]
            if app_event["page"] == "Home":
                print(app_event)
                if app_event["event"] == "menu":
                    menuWin.process_menu_event(opts["line"] - 1)

                elif app_event["event"] == "startgame":
                    print("game is starting")
                    menuWin.kill_window()
                    menuWin = None
                    gameWinManager = GameWinManager(
                        nvim, opts["gameId"], client, opts["color"]
                    )

            elif app_event["page"] == "Game":
                if app_event["event"] == "make_move":
                    gameWinManager.client_make_move(opts["move"])
                elif app_event["event"] == "resign":
                    gameWinManager.client_resign()
                elif app_event["event"] == "kill_game_window":
                    gameWinManager.destroy()
                    gameWinManager = None
                    menuWin = MenuWin(nvim, client)
                elif app_event["event"] == "flip":
                    gameWinManager.flip_board()
                else:
                    raise Exception(f"APP EVENT {app_event} CASE NOT IMPLEMENTED")

            elif app_event["page"] == "Global":
                if app_event["event"] == "exit":
                    try:
                        if menuWin:
                            menuWin.kill_window()
                        if gameWinManager:
                            gameWinManager.destroy()
                    except:
                        pass
                    exit()
            elif app_event["page"] == "Board":
                print(app_event)
        sleep(0.1)


thread1 = Thread(target=read_stream)
thread2 = Thread(target=read_events)

thread1.setDaemon(True)
thread1.start()
thread2.start()
