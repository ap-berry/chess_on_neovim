from pynvim.api import Nvim, Buffer, Window
from utils import *
from berserk.utils import to_millis
from datetime import datetime
from typing import Literal, Dict, TypedDict, Optional, Union
from chess import Move, Board


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
        relative_to_win: Window,
        stats: Optional[StatsDict] = None,
        window_config: Optional[dict] = None,
    ):
        self.stats = stats
        self.session = session

        self.buffer = find_buf(session, "stats_buffer") or create_buf(
            session, "stats_buffer"
        )

        self.window = find_window_from_title(session, "StatsWindow") or create_window(
            self.session,
            self.buffer,
            False,
            window_config or config_gen(session, config="stats", win=relative_to_win),
            "StatsWindow",
        )

        self.augroup = self.session.api.create_augroup(
            "StatsWinAuGroup", {"clear": True}
        )
        self.window_namespace = namespace(self.session, "StatusWinNS")

        if stats:
            self.set_stats(stats=stats)
            self.gui_initialized = True
        else:
            global empty_stats
            self.displayable_stats = empty_stats
            self.gui_initialized = False

        self._set_window_highlights()
        self.redraw()

    def _set_window_highlights(self):
        self.session.api.win_set_hl_ns(self.window, self.window_namespace)
        self.session.api.set_hl(
            self.window_namespace,
            "NormalFloat",
            {"ctermbg": "Black", "ctermfg": "White"},
        )

    def destroy(self):
        self.session.api.win_close(self.window, True)
        self.session.api.buf_delete(self.buffer, {"force": True})

    def redraw(self):
        """Note: DOES NOT APPLY CHANGES TO GUI UNLESS self.displayable_stats IS UPDATED"""
        buf_set_lines(nvim=self.session, buf=self.buffer, text=self.displayable_stats)
        force_redraw(nvim=self.session)

    def set_ingame_displayable_stats(self):
        self.displayable_stats = self._create_displayable_stats_ingame()

    def set_winner_displayable_stats(
        self, winner: Literal["white", "black", "draw"], msg: str
    ):
        if winner == "white":
            self.score = "1-0"
        elif winner == "black":
            self.score = "0-1"
        else:
            self.score = "1/2-1/2"

        self.winner_msg = msg

        self.displayable_stats = self._create_displayable_stats_winner()

    def set_style(self, style: dict = None):
        self.lborder = "|"
        self.lpad = " "
        self.spacer = "  "
        self.bar = "=" * 28

    def set_gameFull_stats(self, gameFullEvent):
        black = gameFullEvent["black"]
        white = gameFullEvent["white"]
        state = gameFullEvent["state"]

        if "id" in black:
            self.bname = black["name"]
            self.bflair = "@"
            self.brating = str(black["rating"])
            self.btitle = black["title"] or "--"

        elif "aiLevel" in black:
            self.bname = "StockFish" + str(black["aiLevel"])
            self.bflair = "@"
            self.brating = ""
            self.btitle = ""

        else:
            self.bname = "Anonymous"
            self.bflair = " "
            self.brating = ""
            self.btitle = ""

        if "id" in white:
            self.wname = white["name"]
            self.wflair = "@"
            self.wrating = str(white["rating"])
            self.wtitle = white["title"] or "--"

        elif "aiLevel" in white:
            self.wname = "StockFish" + str(white["aiLevel"])
            self.wflair = "@"
            self.wrating = ""
            self.wtitle = ""

        else:
            self.wname = "Anonymous"
            self.wflair = " "
            self.wrating = ""
            self.wtitle = ""

        self.speed = gameFullEvent["speed"]

        if not self.gui_initialized:
            self.gui_initialized = True

    def set_pieces_ate(self):
        self.bate = "todo"
        self.wate = "todo"

    def set_stats(self, stats: StatsDict):
        self.wname = stats["wname"]
        self.wflair = stats["wflair"]
        self.wtime = self._timems_to_timestring(stats["wtime"])
        self.winc = self._timems_to_incstring(stats["winc"])
        self.wtitle = stats["wtitle"]
        self.wrating = str(stats["wrating"])
        self.wate = "todo"

        self.bname = stats["bname"]
        self.bflair = stats["bflair"]
        self.btime = self._timems_to_timestring(stats["btime"])
        self.binc = self._timems_to_incstring(stats["binc"])
        self.btitle = stats["btitle"]
        self.brating = str(stats["brating"])
        self.bate = "todo"

        if not self.gui_initialized:
            self.gui_initialized = True

    def set_ingame_displayable_stats(self):
        self.displayable_stats = self._create_displayable_stats_ingame()

    def set_autocmd(self, handle: int):
        self.session.api.create_autocmd(
            "BufEnter",
            {
                "group": self.augroup,
                "buffer": self.buffer.number,
                "command": f"call nvim_set_current_win({handle})",
            },
        )

    def set_times(
        self,
        wtime: Optional[Union[datetime, int]] = None,
        btime: Optional[Union[datetime, int]] = None,
        winc: Optional[int] = None,
        binc: Optional[int] = None,
    ):
        """at least one time needs to be given.
        time must be datetime obj or miliseconds
        Increments must be in miliseconds
        """
        assert wtime or btime, "at least one time needs to be given"

        if wtime:
            self.wtime = self._timems_to_timestring(
                to_millis(wtime) if type(wtime) is not int else wtime
            )
        if btime:
            self.btime = self._timems_to_timestring(
                to_millis(btime) if type(btime) is not int else btime
            )

        if winc != None:
            self.winc = str(winc // 1000)

        if binc != None:
            self.binc = str(binc // 1000)

    def _set_current(self):
        self.session.current.buffer = self.buffer

    @staticmethod
    def _timems_to_incstring(timems: int):
        assert timems <= 180 * 1000, "Increment cannot exceed 180s"
        m = timems // 60000 % 60
        s = timems // 1000 % 60
        return f"{m}:{ s if s > 9 else '0'+str(s)}"

    @staticmethod
    def _timems_to_timestring(timems: int):
        h = timems // 3600000
        m = timems // 60000 % 60
        s = timems // 1000 % 60
        ms = timems % 3600000  # todo
        return f"{ str(h)+':' if h != 0 else '' }{ m if m > 9 else '0'+str(m) }:{ s if s > 9 else '0'+str(s) }"

    def _create_displayable_stats_winner(self) -> list[str]:
        assert self.gui_initialized == True, "Stats not initialized with data"
        return [
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.bname,
                    self.bflair,
                    self.spacer,
                    self.btitle,
                    self.spacer,
                    self.brating,
                ]
            ),
            "".join([self.lborder, self.bar]),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.btime,
                    self.spacer,
                    self.binc,
                    self.spacer,
                    self.bate,
                ]
            ),
            "".join([self.lborder, self.bar]),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                ]
            ),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.spacer,
                    self.spacer,
                    "score:",
                    self.spacer,
                    self.score,
                ]
            ),
            "".join([self.lborder, self.lpad, self.winner_msg]),
            "".join([self.lborder, self.bar]),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.wtime,
                    self.spacer,
                    self.winc,
                    self.spacer,
                    self.wate,
                ]
            ),
            "".join([self.lborder, self.bar]),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.wname,
                    self.wflair,
                    self.spacer,
                    self.wtitle,
                    self.spacer,
                    self.wrating,
                ]
            ),
        ]

    def _create_displayable_stats_ingame(self) -> list[str]:
        assert self.gui_initialized == True, "Stats not initialized with data"
        return [
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.bname,
                    self.bflair,
                    self.spacer,
                    self.btitle,
                    self.spacer,
                    self.brating,
                ]
            ),
            "".join([self.lborder, self.bar]),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.btime,
                    self.spacer,
                    self.binc,
                    self.spacer,
                    self.bate,
                ]
            ),
            "".join([self.lborder, self.bar]),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.index[0],
                    " ",
                    self.formatted_moves[0],
                    self.spacer,
                    self.formatted_moves[1],
                ]
            ),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.index[1],
                    " ",
                    self.formatted_moves[2],
                    self.spacer,
                    self.formatted_moves[3],
                ]
            ),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.index[2],
                    " ",
                    self.formatted_moves[4],
                    self.spacer,
                    self.formatted_moves[5],
                ]
            ),
            "".join([self.lborder, self.bar]),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.wtime,
                    self.spacer,
                    self.winc,
                    self.spacer,
                    self.wate,
                ]
            ),
            "".join([self.lborder, self.bar]),
            "".join(
                [
                    self.lborder,
                    self.lpad,
                    self.wname,
                    self.wflair,
                    self.spacer,
                    self.wtitle,
                    self.spacer,
                    self.wrating,
                ]
            ),
        ]

    def set_moves(self, board: Board):
        """The board must at the position of the latest move"""
        # change formatted_moves list, change index list

        last6 = []
        moves_index = []
        _board = (
            Board()
        )  # empty board because variation san plays the moves in sequence
        half_move_count = len(board.move_stack)
        offset = 3
        if half_move_count % 2 != 0:
            offset = 2
        _move_list = _board.variation_san(board.move_stack).split(" ")[-(6 + offset) :]
        for i, m in enumerate(_move_list):
            if i % 3 == 0:
                moves_index.append(m)
            else:
                last6.append(m)

        if len(moves_index) < 3:
            moves_index += ["  " for i in range(3 - len(moves_index))]
        if len(last6) < 6:
            last6 += ["----" for i in range(6 - len(last6))]

        self.formatted_moves = last6
        self.index = moves_index

    def __str__(self) -> str:
        self.displayable_stats = self._create_displayable_stats_ingame()
        return "\n".join(self.displayable_stats)
