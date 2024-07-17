from pynvim.api import Nvim 
from utils import *
from berserk.utils import to_millis
from typing import Literal, TypedDict, Optional, Union
from chess import Board
from stats_utils import timems_to_incstring, timems_to_timestring, white_pieces_taken, black_pieces_taken
from game_clock import GameClock
class StatsDict(TypedDict, total=False):
    wname: str
    wflair: str
    wtitle: str
    wrating: Union[int, str]
    wtime: int
    winc: int
    bname: str
    bflair: str
    btitle: str
    brating: Union[int, str]
    btime: int
    binc: int
    speed: str


empty_stats = [
    "/ / / Waiting For Stats / / /",
    "/ / / / / / / / / / / / / / /",
    "/ / / / / / / / / / / / / / /",
    "/ / / / / / / / / / / / / / /",
    "/ / / / / / / / / / / / / / /",
    "/ / / / / / / / / / / / / / /",
    "/ / / / / / / / / / / / / / /",
    "/ / / / / / / / / / / / / / /",
    "/ / / / / / / / / / / / / / /",
    "/ / / / / / / / / / / / / / /",
    "/ / / / / / / / / / / / / / /",
]


class StatsWin:
    """time and increment must be in ms"""

    def __init__(
        self,
        session: Nvim,
        window_config: Optional[dict] = None,
        myside: Literal['white', 'black'] = "white"
    ):
        self.neovim_session = session

        
        self.buffer = find_buf(session, "stats_buffer") or create_buf(
            session, "stats_buffer"
        )

        self.window = find_window_from_title(session, "StatsWindow") or create_window(
            self.neovim_session,
            self.buffer,
            False,
            window_config or config_gen(session, config="stats"),
            "StatsWindow",
        )
        self.namespace = namespace(self.neovim_session, "StatusWinExtmarkNS")
        win_set_local_winhighlight(self.neovim_session, self.window, "Normal:StatsWinBackground,FloatBorder:StatsWinFloatBorder")
        
        self.augroup = self.neovim_session.api.create_augroup(
            "StatsWinAuGroup", {"clear": True}
        )

        self.flip = myside != "white"


        self.gameclock = None

        
    def handle_gameFull_event(self, event, board):
        self.gameclock = self._create_gameclock(event)
        if " " in event['state']['moves']:
            self.gameclock.start()
        self.virt_lines = self._create_stats_extmark_virt_lines(event, board)
        self.redraw()
    
    def _create_gameclock(self, event):
        state = event
        if event['type'] == "gameFull":
            state = event['state']
            
        current_playing_side = "white"
        if state['moves'] != "":
            current_playing_side = "white" if len(state['moves'].split(" ")) % 2 == 0 else "black"
        return GameClock(state['wtime'], state['winc'], state['btime'], state['binc'], current_playing_side)

    def update_times(self):
        self.virt_lines[0][0][0] = timems_to_timestring(self.gameclock.black_time)
        self.virt_lines[0][2][0] = timems_to_incstring(self.gameclock.black_inc)
        
        self.virt_lines[-1][0][0] = timems_to_timestring(self.gameclock.white_time)
        self.virt_lines[-1][2][0] = timems_to_incstring(self.gameclock.white_inc)
        self.redraw()
    
    def flip_stats(self):
        self.flip = not self.flip
        self.redraw()
    
    def redraw(self):
        """ Redraws from self.virt_lines If self.virt_lines is unchanged so is the buffer"""
        _virt_lines = self.virt_lines
        if self.flip:
            _virt_lines = self.virt_lines[::-1][:2:] + self.virt_lines[2:-2] + self.virt_lines[:2:][::-1]
        buf_set_extmark(self.neovim_session, self.buffer, self.namespace, 0, 0, ExtmarksOptions(
                id=1,
                virt_lines=_virt_lines
        ))
        force_redraw(self.neovim_session)
    
    def handle_gameState_event(self, gameState, board):
        if not self.gameclock.started:
            self.gameclock.start()
        
        status = gameState["status"]
        spacer = [" ", ""]
        
        self.gameclock = self._create_gameclock(gameState)
        if " " in gameState['moves']:
            self.gameclock.start()
        
        #lines
        
        self.virt_lines[0] =  [[timems_to_timestring(to_millis(gameState['btime'])), ""], spacer, [timems_to_incstring(to_millis(gameState['binc'])), ""]]

        moves = split_list(self.last_6_moves_in_san(board), 3)
        new_move_lines = []
        for ln in moves:            
            line = []
            for move in ln:
                line.append([move, ""])
                line.append(spacer)
            new_move_lines.append(line)
        
        if status != "started":
            self.gameclock.stop()
            score = ""
            if "winner" in gameState:
                score = self.get_score(gameState['winner'])
            elif status != "aborted":
                score = self.get_score("draw")
                
            new_status_line =  [spacer, [score, ""], spacer, [status, ""]]
            self.virt_lines[-3] = new_status_line
        
        
        self.virt_lines = self.virt_lines[:2] + new_move_lines + self.virt_lines[-3:]
        
        self.virt_lines[-1] = [[timems_to_timestring(to_millis(gameState['wtime'])), ""], spacer, [timems_to_incstring(to_millis(gameState['winc'])), ""]]
            
        self.redraw()

            
    def kill_window(self):
        self.neovim_session.api.win_close(self.window, True)
        self.neovim_session.api.buf_delete(self.buffer, {"force": True})

    def resize(self):
        self.neovim_session.api.win_set_config(
            self.window,
            {
                "relative": "editor",
                "row": (workspace_height(self.neovim_session) - 11) // 2,
                "col": (workspace_width(self.neovim_session) - 30 - 32) // 2, 
            }
        )

    def _create_stats_extmark_virt_lines(self, gameFull, board):        
        self.gameFull = gameFull
        self.gameState = gameFull['state']
        white = self.gameFull['white']
        black = self.gameFull["black"]
        
        spacer = [" ", ""]
        virt_lines = []
        virt_lines.append(
            [[timems_to_timestring(self.gameState['btime']), ""], spacer, [timems_to_incstring(self.gameState['binc']), ""]]
        )

        if "aiLevel" in black:
            virt_lines.append(
                [[f"StockFish Level {black['aiLevel']}", ""]]
            )
        else:
            virt_lines.append(
                [[black['name'], ""], spacer, [black['title'] or "", ""], spacer, [str(black['rating']), ""]]
            )
        
        # # wpt = white_pieces_taken(board)
        # # bpt = black_pieces_taken(board)        
        
        
        moves = split_list(self.last_6_moves_in_san(board), 3)
        line = []
        for ln in moves:            
            line = []
            for move in ln:
                line.append([move, ""])
                line.append(spacer)
            virt_lines.append(line)
            
        virt_lines.append(
            [spacer, ["", ""]]
        )
        
        
        if "aiLevel" in white:
            virt_lines.append(
                [[f"StockFish Level {white['aiLevel']}", ""]]
            )
        else:
            virt_lines.append(
                [[white['name'], ""], spacer, [white['title'] or "", ""], spacer, [str(white['rating']), ""]]
            )        
        virt_lines.append(
            [[timems_to_timestring(self.gameState['wtime']), ""], spacer, [timems_to_incstring(self.gameState['winc']), ""]]
        )
        return virt_lines

    def get_score(
        self, winner: Literal["white", "black", "draw"]
    ):
        if winner == "white":
            return "1-0"
        elif winner == "black":
            return "0-1"
        else:
            return "1/2-1/2"

    def set_autocmd(self, handle: int):
        self.neovim_session.api.create_autocmd(
            "BufEnter",
            {
                "group": self.augroup,
                "buffer": self.buffer.number,
                "command": f"call nvim_set_current_win({handle})",
            },
        )

    def _set_current(self):
        self.neovim_session.current.buffer = self.buffer

    def last_6_moves_in_san(self, board: Board):
        """Returns the last 6 moves in SAN notation with their corresponding numbers in the list e.g `["1.", "e4", "e5", "2.", "Nf3" ...]`"""
        # change formatted_moves list, change index list
        last_movestack = board.move_stack[-6:]
        _board = board.copy()
        for i in range(len(last_movestack)):
            _board.pop()
        _move_list = _board.variation_san(last_movestack).split(" ")
        if "..." in _move_list[0]:
            _move_list.pop(0)
        
        moves_len = len(_move_list)
        if  moves_len < 9:
            _move_list+=[" " for i in range(9-moves_len)]
            
        return _move_list