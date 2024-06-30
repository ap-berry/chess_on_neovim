from threading import Thread, Lock
from time import sleep
import berserk
from berserk.utils import to_millis
import os
from dotenv import load_dotenv, set_key
from pynvim import attach
from chess import Board, Move
from statsWin import StatsWin
from boardWin import BoardWin
from utils import find_buf, config_gen
from game_clock import GameClock
from typing import Literal, Optional

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)

events = []
lock = Lock()


nvim = attach("tcp", "127.0.0.1", 6789)


boardWin: Optional[BoardWin] = None
statsWin: Optional[StatsWin] = None
gameClock: Optional[GameClock] = None
gameFinished: bool = False
CurrentSide: Literal["black", "white"]


def read_stream():
    print("reading stream")
    global events, gameClock
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


def read_events():
    print("reading events")
    global events, gameClock
    while True:
        with lock:
            if events:
                for event in events:
                    print(event)
                    process_new_event(event)
                events = []
            else:
                sync_stats_clock()
        sleep(0.1)


def sync_stats_clock():
    global gameClock, statsWin
    if not gameClock or not gameClock.started:
        return
    elapsed_time = gameClock.player_and_time_ms()
    side = elapsed_time[0]
    time = elapsed_time[1]
    if time > 1000:
        if side == "black":
            gameClock.black_time = time
            statsWin.set_times(btime=time)
        else:
            gameClock.white_time = time
            statsWin.set_times(wtime=time)

        statsWin.set_ingame_displayable_stats()
        statsWin.redraw()


def process_new_event(event):
    global boardWin, statsWin, gameClock, gameFinished, CurrentSide
    if event["type"] == "gameStart":
        gameFinished = False
        current_Win = nvim.current.window
        game = event["game"]
        board = Board(fen=game["fen"])
        boardWin = BoardWin(nvim, board=board, relative_to_win=current_Win)
        boardWin.redraw()
        statsWin = StatsWin(nvim, relative_to_win=current_Win)

        if event["game"]["color"] == "black":
            CurrentSide = "black" if event["game"]["isMyTurn"] else "white"
        if event["game"]["color"] == "white":
            CurrentSide = "white" if event["game"]["isMyTurn"] else "black"

    elif event["type"] == "gameFull":
        configure_gameclock(event)
        # update board move stack for middle of match connections
        state = event["state"]
        moves = state["moves"].split(" ")

        if moves[0] != "":
            moves = list(map(Move.from_uci, moves))
            boardWin.board.move_stack = moves.copy()

        statsWin.set_gameFull_stats(event)
        statsWin.set_style()
        statsWin.set_pieces_ate()
        statsWin.set_moves(boardWin.board)
        statsWin.redraw()

    elif event["type"] == "gameState":
        process_gameState_event(event)

    elif event["type"] == "gameFinish":
        gameFinished = True  # will be useful when implementing input
        print("\nto do EVENT: " + event["type"] + "\n")
    else:
        print("\nto do EVENT: " + event["type"] + "\n")


def configure_gameclock(event):
    assert event["type"] == "gameFull", "wrong event supplied, needs gameFull event"
    global gameClock, CurrentSide

    state = event["state"]

    wtime = state["wtime"]
    btime = state["btime"]
    winc = state["winc"]
    binc = state["binc"]

    gameClock = GameClock(wtime, winc, btime, binc, side=CurrentSide)
    if len(state["moves"].split(" ")) > 1:
        gameClock.start()


def process_gameState_event(event):
    global boardWin, statsWin
    moves = event["moves"]
    status = event["status"]

    if status == "started":
        make_move(moves, event)
        sync_stats(event)
    elif status == "mate":
        make_move(moves, event)
        sync_stats(event)

        statsWin.set_winner_displayable_stats(
            event["winner"], win_msg("mate", event["winner"])
        )
        statsWin.redraw()

    elif status == "resign":
        statsWin.set_winner_displayable_stats(
            event["winner"], win_msg("resign", event["winner"])
        )
        statsWin.redraw()
    elif status == "outoftime":
        statsWin.set_times(wtime=event["wtime"], btime=event["btime"])
        statsWin.set_winner_displayable_stats(
            event["winner"], win_msg("outoftime", event["winner"])
        )
        statsWin.redraw()

    else:
        print(event)
        raise Exception("\nIMPLEMENT GAMESTATE STATUS " + status + "\n")


def make_move(moves: str, event: dict):
    # print(len(moves), len(boardWin.board.move_stack))
    if len(moves) > len(boardWin.board.move_stack):
        # make move
        latest_move = moves.rsplit(" ", 1)[-1]
        if latest_move == "":
            raise "something went terribly fucking wrong"

        boardWin.draw_push_move(latest_move)

    elif len(moves) < len(boardWin.board.move_stack):
        # takeback
        boardWin.draw_takeback_once()

    else:
        raise "WHAT THE FUCK"


def sync_stats(event):
    global statsWin, boardWin
    statsWin.set_times(wtime=event["wtime"], btime=event["btime"])
    statsWin.set_ingame_displayable_stats()
    statsWin.set_moves(board=boardWin.board)
    statsWin.redraw()
    if not gameClock.started:
        gameClock.start()

    gameClock.change_sides()


def win_msg(
    type: Literal["resign", "mate", "outoftime"], winner: Literal["white", "black"]
):
    loser = "white"
    if winner == "white":
        loser = "black"

    if type == "mate":
        return f"{winner} won. {loser} got mated"
    elif type == "resign":
        return f"{winner} won. {loser} resigned XD"
    elif type == "outoftime":
        return f"{winner} won. {loser} timed out"


thread1 = Thread(target=read_stream)
thread2 = Thread(target=read_events)

thread1.start()
thread2.start()
