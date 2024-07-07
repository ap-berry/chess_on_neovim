from boardWin import BoardWin
from statsWin import StatsWin
from inputWin import InputWin
from game_clock import GameClock

from chess import Board, Move
from pynvim import Nvim
from berserk import Client

from typing import Literal


class GameWinManager:
    def __init__(
        self,
        session: Nvim,
        gameId: str,
        client: Client,
        myside: Literal["black", "white"],
    ) -> None:
        self.session = session
        self.gameId = gameId
        self.client = client

        parent_window = self.session.current.window

        self.chessBoard = Board()
        self.boardWin = BoardWin(
            session=self.session,
            board=self.chessBoard,
            relative_to_win=parent_window,
            myside=myside,
        )
        self.statsWin = StatsWin(session=self.session, relative_to_win=parent_window)
        self.inputWin = InputWin(session=self.session, relative_to_win=parent_window)
        self.myside = myside
        self.gameClock = None

        self.boardWin.set_autocmd(self.inputWin.window.handle)
        self.statsWin.set_autocmd(self.inputWin.window.handle)

        self.session.api.set_current_win(self.inputWin.window)

    def flip_board(self):
        self.boardWin.flip_board()

    def client_make_move(self, move: str):
        # try
        side = self.myside == "white"
        if side != bool(self.boardWin.board.turn):
            self.inputWin.set_extmarks(
                "Not Your Turn          ", self.inputWin.hl_group_error
            )
            return
        else:
            self.inputWin.set_extmarks()

        try:
            move = self.boardWin.board.parse_san(move)
            self.client.board.make_move(self.gameId, move.uci())
        except:
            self.inputWin.set_extmarks(
                "An Error Occured         ", self.inputWin.hl_group_error
            )

    def client_resign(self):
        self.client.board.resign_game(self.gameId)

    def decrement_game_clock(self):
        if not self.gameClock or not self.gameClock.started:
            return
        elapsed_time = self.gameClock.player_and_time_ms()
        side = elapsed_time[0]
        time = elapsed_time[1]
        if time > 1000:
            if side == "black":
                self.gameClock.black_time = time
                self.statsWin.set_times(btime=time)
            else:
                self.gameClock.white_time = time
                self.statsWin.set_times(wtime=time)

            self.statsWin.set_ingame_displayable_stats()
            self.statsWin.redraw()

    def process_new_event(self, event):
        if event["type"] == "gameStart":
            gameFinished = False
            game = event["game"]
            self.boardWin.redraw_from_fen(game["fen"], game["lastMove"])

            if event["game"]["color"] == "black":
                self.current_playing_side = (
                    "black" if event["game"]["isMyTurn"] else "white"
                )
            if event["game"]["color"] == "white":
                self.current_playing_side = (
                    "white" if event["game"]["isMyTurn"] else "black"
                )

        elif event["type"] == "gameFull":
            self.configure_gameclock(event)
            # update board move stack for middle of match connections
            state = event["state"]
            moves = state["moves"].split(" ")

            if moves[0] != "":
                moves = list(map(Move.from_uci, moves))
                self.boardWin.board.move_stack = moves.copy()

            self.statsWin.set_gameFull_stats(event)
            self.statsWin.set_times(
                winc=event["state"]["winc"],
                wtime=event["state"]["wtime"],
                binc=event["state"]["binc"],
                btime=event["state"]["btime"],
            )
            self.statsWin.set_style()
            self.statsWin.set_pieces_ate()
            self.statsWin.set_moves(self.boardWin.board)
            self.statsWin.displayable_stats = (
                self.statsWin._create_displayable_stats_ingame()
            )
            self.statsWin.redraw()

        elif event["type"] == "gameState":
            self.process_gameState_event(event)

        elif event["type"] == "gameFinish":
            self.gameClock = None

            gameFinished = True  # will be useful when implementing input
            print("\nto do EVENT: " + event["type"] + "\n")

        else:
            print("\nto do EVENT: " + event["type"] + "\n")

    def destroy(self):
        self.chessBoard = None
        self.boardWin.destroy()
        self.statsWin.destroy()
        self.inputWin.destory()

    def configure_gameclock(self, event):
        assert event["type"] == "gameFull", "wrong event supplied, needs gameFull event"

        state = event["state"]

        wtime = state["wtime"]
        btime = state["btime"]
        winc = state["winc"]
        binc = state["binc"]

        self.gameClock = GameClock(
            wtime, winc, btime, binc, side=self.current_playing_side
        )
        if len(state["moves"].split(" ")) > 1:
            self.gameClock.start()

    def process_gameState_event(self, event):
        moves = event["moves"]
        status = event["status"]

        if status == "started":
            self.make_move(moves, event)
            self.sync_stats(event)
        elif status == "mate":
            self.make_move(moves, event)
            self.sync_stats(event)

            self.statsWin.set_winner_displayable_stats(
                event["winner"], self.win_msg("mate", event["winner"])
            )
            self.statsWin.redraw()

        elif status == "resign":
            self.statsWin.set_winner_displayable_stats(
                event["winner"], self.win_msg("resign", event["winner"])
            )
            self.statsWin.redraw()
        elif status == "outoftime":
            self.statsWin.set_times(wtime=event["wtime"], btime=event["btime"])
            self.statsWin.set_winner_displayable_stats(
                event["winner"], self.win_msg("outoftime", event["winner"])
            )
            self.statsWin.redraw()
        elif status == "aborted":
            pass
        else:
            print(event)
            raise Exception("\nIMPLEMENT GAMESTATE STATUS " + status + "\n")

    def make_move(self, moves: str, event: dict):
        # print(len(moves), len(self.boardWin.board.move_stack))
        if len(moves) > len(self.boardWin.board.move_stack):
            # make move
            latest_move = moves.rsplit(" ", 1)[-1]
            if latest_move == "":
                raise "something went terribly fucking wrong"

            self.boardWin.draw_push_move(Move.from_uci(latest_move))

        elif len(moves) < len(self.boardWin.board.move_stack):
            # takeback
            self.boardWin.draw_takeback_once()

        else:
            raise "WHAT THE FUCK"

    def sync_stats(self, event):
        self.statsWin.set_times(wtime=event["wtime"], btime=event["btime"])
        self.statsWin.set_ingame_displayable_stats()
        self.statsWin.set_moves(board=self.boardWin.board)
        self.statsWin.redraw()
        if not self.gameClock.started:
            self.gameClock.start()

        self.gameClock.change_sides()

    def win_msg(
        self,
        type: Literal["resign", "mate", "outoftime"],
        winner: Literal["white", "black"],
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
