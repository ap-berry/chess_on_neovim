from boardWin import BoardWin
from statsWin import StatsWin
from inputWin import InputWin
from game_clock import GameClock

from chess.variant import find_variant
from chess import Board, Move
from pynvim import Nvim
from berserk import Client

from typing import Literal
import utils

from pynvim.api import Window
class GameWinManager:
    def __init__(
        self,
        session: Nvim,
        gameId: str,
        client: Client,
        myside: Literal["black", "white"],        
    ) -> None:
        self.neovim_session = session
        self.gameId = gameId
        self.client = client

        self.game = None
        games = self.client.games.get_ongoing()
        for game in games:
            if self.gameId == game['gameId']:
                self.game = game
        
        if not self.game:
            return
                
        self.variant = self.game['variant']['key']
        

        if self.variant != "fromPosition": 
            self.chessBoard = find_variant(self.variant)()
        else:
            self.chessBoard = Board()
         
         
        self.boardWin = BoardWin(
            session=self.neovim_session,
            board=self.chessBoard,
            myside=myside,
            variant=self.variant,
        )
        
        self.statsWin = StatsWin(
            session=self.neovim_session,
            myside=myside
        )
        
        self.inputWin = InputWin(
            session=self.neovim_session,
        )
        
        # self.dummy_buffer = utils.find_buf(self.neovim_session, "dummy_buf") or utils.create_buf(self.neovim_session, "dummy_buf", False)
        # self.dummy_window = self.neovim_session.api.open_win(self.dummy_buffer, False, {"relative": "editor", "row": 0, "col": 0, "width": 10, "height": 5, "style": "minimal", "border": "single"})
        self.myside = myside
        self.gameClock = None

        self.boardWin.set_autocmd(self.inputWin.window.handle)

        if self.statsWin:
            self.statsWin.set_autocmd(self.inputWin.window.handle)

        self.neovim_session.api.set_current_win(self.inputWin.window)

    def flip_board(self):
        self.boardWin.flip_board()
        if self.statsWin:
            self.statsWin.flip_stats()
        self.inputWin.set_extmarks()
        

    def client_make_move(self, move: str):
        self.inputWin.set_extmarks(" move:"+move)
        side = self.myside == "white"
        if side != bool(self.boardWin.board.turn):
            self.inputWin.set_extmarks(
                " Not Your Turn          ", self.inputWin.hl_group_error
            )
            return
        try:
            move = self.boardWin.board.parse_san(move)
        except:
            self.inputWin.set_extmarks(
                " Illeagal Move         ", self.inputWin.hl_group_error
            )
            return
        
        try:
            self.client.board.make_move(self.gameId, move.uci())
        except Exception as e:
            self.inputWin.set_extmarks(
                " Something Went Wrong         ", self.inputWin.hl_group_error
            )

    def client_resign(self):
        self.client.board.resign_game(self.gameId)
        self.inputWin.set_extmarks(" resigned")
        

    def decrement_game_clock(self, update_interval: int = 1000):
        """update interval must be in milliseconds"""
        if not self.statsWin or not self.statsWin.gameclock or not self.statsWin.gameclock.started:
            return
        remaining = self.statsWin.gameclock.player_and_time_ms()
        side = remaining[0]
        time = remaining[1]
        if time > update_interval:
            if side == "black":
                self.statsWin.gameclock.black_time = time
            else:
                self.statsWin.gameclock.white_time = time
                
            self.statsWin.update_times()

    def handle_game_event(self, event):
        if "page" in event:
            options = event['opts']
            action = options['action']
            if action == "make_move":
                self.client_make_move(event['opts']["move"])
            elif action == "flip":
                self.flip_board()
            elif action == "resign":
                self.client_resign()
            elif action == "abort":
                self.client_resign()
            else:
                raise Exception("input action not implemented"+ action)
        elif event['type'] == "gameFull":
            
            if event['variant']['key'] == "fromPosition":
                self.boardWin.board.set_fen(event['initialFen']) 
            
            state = event["state"]
            moves = state["moves"].split(" ")
            if moves[0] != "":
                for move in moves:
                    self.boardWin.board.push(Move.from_uci(move))
                            
                self.boardWin.redraw(lastMove=self.boardWin.board.move_stack[-1])
            else:
                self.boardWin.redraw(lastMove="")
                
            if self.statsWin:
                self.statsWin.handle_gameFull_event(event, self.boardWin.board)
            
        elif event['type'] == "gameState":
            self.handle_gameState_event(event)
            
            pass
        elif event['type'] == "chatLine":
            pass
        elif event['type'] == "opponentGone":
            pass
    def kill_window(self):
        self.chessBoard = None
        self.boardWin.kill_window()
        if self.statsWin:
            self.statsWin.kill_window()
        self.inputWin.kill_window()

    def resize(self):
        if self.statsWin:
            self.statsWin.resize()
        if self.boardWin:
            self.boardWin.resize()
        if self.inputWin:
            self.inputWin.resize()
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

    def handle_gameState_event(self, event):
        moves = event["moves"]
        status = event["status"]

        # Board Window Updating
        if self.boardWin:
            if status == "started" or status == "mate" or status == "variantEnd":
                self.make_move(moves, event)

        # Status Window Updating
        if self.statsWin:
            if self.statsWin:
                self.statsWin.handle_gameState_event(event, self.boardWin.board)

    def make_move(self, moves: str, event: dict):
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
            raise "THAT'S IMPOSSIBLE"