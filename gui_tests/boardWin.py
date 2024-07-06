from pynvim.api import Nvim, Buffer, Window
import utils
from utils import BadFenError
from chess import Board, Move, Square, square_file, square_rank
from typing import Tuple, Optional, Literal
from pynvim import attach


default_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

PIECES = {
    "Light": {
        "K": "\u2654",
        "Q": "\u2655",
        "R": "\u2656",
        "B": "\u2657",
        "N": "\u2658",
        "P": "\u2659",
        "k": "\u265a",
        "q": "\u265b",
        "r": "\u265c",
        "b": "\u265d",
        "n": "\u265e",
        "p": "\u265f",
        "spacer": "\u2000",
    },
    "Dark": {
        "k": "\u2654",
        "q": "\u2655",
        "r": "\u2656",
        "b": "\u2657",
        "n": "\u2658",
        "p": "\u2659",
        "K": "\u265a",
        "Q": "\u265b",
        "R": "\u265c",
        "B": "\u265d",
        "N": "\u265e",
        "P": "\u265f",
        "spacer": "\u2000",
    },
}

PIECES_ASCII = {
    "K": "K",
    "Q": "Q",
    "R": "R",
    "B": "B",
    "N": "N",
    "P": "P",
    "k": "k",
    "q": "q",
    "r": "r",
    "b": "b",
    "n": "n",
    "p": "p",
    "spacer": " ",
}


class BoardWin:
    def __init__(
        self,
        session: Nvim,
        relative_to_win: Window,
        board: Board = Board(),
        window_config: Optional[dict] = None,
        myside: Literal["black", "white"] = "white",
        theme: Literal["Light", "Dark"] = "Light",
    ):
        self.session = session
        self.board = board

        self.buffer = utils.find_buf(session, "board_buffer") or utils.create_buf(
            session, "board_buffer"
        )

        self.window = utils.find_window_from_title(
            session, "BoardWindow"
        ) or utils.create_window(
            self.session,
            self.buffer,
            True,
            window_config
            or utils.config_gen(session, config="board", win=relative_to_win),
            "BoardWindow",
        )

        self.namespace = utils.namespace(self.session, "BoardSquaresNs")
        self.window_namespace = utils.namespace(self.session, "BoardWinNS")

        self.flip = myside != "white"
        self.theme = theme
        self.hl_group_white_sq = "WhiteSquare"
        self.hl_group_black_sq = "BlackSquare"
        self.hl_group_move_from = "MovedFrom"
        self.hl_group_move_to = "MovedTo"
        self.hl_group_checker = "Checker"
        self.hl_group_checked = "Checked"

        self.displayable_board = self._create_displayable_board()
        self.hls_matrix = self._create_default_hls()
        self._set_window_highlights()
        self.redraw()

        self.autocmd_group = self.session.api.create_augroup(
            "BoardWinAuGroup", {"clear": True}
        )

        self.prev_editted_lines = set()

    def _set_window_highlights(self):
        self.session.api.win_set_hl_ns(self.window, self.window_namespace)
        self.session.api.set_hl(
            self.window_namespace,
            "NormalFloat",
            {"ctermbg": "None", "ctermfg": "White"},
        )
        self.session.api.set_hl(
            self.window_namespace,
            "WhiteSquare",
            {
                "ctermbg": "White",
                "ctermfg": "Black",
                "bold": True,
                "blend": 0,
                "standout": False,
            },
        )
        self.session.api.set_hl(
            self.window_namespace,
            "BlackSquare",
            {
                "ctermbg": "DarkBlue",
                "ctermfg": "Black",
                "bold": True,
                "blend": 0,
                "standout": False,
            },
        )
        self.session.api.set_hl(
            self.window_namespace,
            "MovedTo",
            {"ctermbg": "Green", "ctermfg": "Black", "bold": True, "blend": 0},
        )
        self.session.api.set_hl(
            self.window_namespace,
            "MovedFrom",
            {"ctermbg": "LightGreen", "ctermfg": "Black", "bold": True, "blend": 0},
        )
        self.session.api.set_hl(
            self.window_namespace,
            "Checker",
            {"ctermbg": "LightRed", "ctermfg": "Black", "bold": True, "blend": 0},
        )
        self.session.api.set_hl(
            self.window_namespace,
            "Checked",
            {"ctermbg": "Red", "ctermfg": "Black", "bold": True, "blend": 0},
        )

    def set_autocmd(self, handle: int):
        self.session.api.create_autocmd(
            "BufEnter",
            {
                "group": self.autocmd_group,
                "buffer": (self.buffer.number),
                "command": f"call nvim_set_current_win({handle})",
            },
        )

    def toggle_theme(self):
        self.theme = "Dark" if self.theme == "Light" else "Light"

    def toggle_flip(self):
        self.flip = not self.flip

    def redraw_from_fen(self, fen: str):
        self.board.set_fen(fen)
        self.displayable_board = self._create_displayable_board()
        self.redraw()

    def redraw(self):
        utils.buf_set_lines(
            nvim=self.session, buf=self.buffer, text=self.displayable_board
        )
        for hl_row in self.hls_matrix:
            utils.buf_set_hls(
                nvim=self.session,
                buffer=self.buffer,
                ns_id=self.namespace,
                hls=hl_row,
            )
        utils.force_redraw(nvim=self.session)

    def is_legal_move(self, move: Move):
        if move in self.board.legal_moves:
            return True
        else:
            return False

    def _set_current(self):
        self.session.current.buffer = self.buffer

    def destroy(self):
        self.session.api.win_close(self.window, True)
        self.session.api.buf_delete(self.buffer, {"force": True})

    # should only run at init
    def _create_displayable_board(self):
        _fen = self.board.fen().split(" ")[0]
        _fen = _fen.split("/")
        if self.flip:
            _fen = self._flip_board_fen(_fen)
        if len(_fen) != 8:
            raise BadFenError
        _board = []
        for ln in _fen:
            line = ""
            for c in ln:
                if c.isnumeric():
                    line += PIECES[self.theme]["spacer"] * int(c) * 3
                else:
                    line += (
                        PIECES[self.theme]["spacer"]
                        + PIECES[self.theme][c]
                        + PIECES[self.theme]["spacer"]
                    )
            _board.append(line)

        return _board

    def _create_default_hls(self):
        _hls_matrix = []
        for i in range(8):
            _row = []
            for j in range(8):
                _row.append(
                    [
                        self.hl_group_white_sq
                        if (i + j) % 2 == 0
                        else self.hl_group_black_sq,
                        i,
                        j * 9,
                        j * 9 + 9,
                    ]
                )
            _hls_matrix.append(_row)
        return _hls_matrix

    @staticmethod
    def _flip_board_fen(fen: list[str]):
        _f = [l[::-1] for l in fen]
        _f.reverse()
        return _f

    def draw_takeback_once(self):
        self.board.pop()

        self.displayable_board = self._create_displayable_board()

        self.redraw()

    def draw_push_move(self, move: Move):
        if self.prev_editted_lines:
            for row in self.prev_editted_lines:
                self.session.api.buf_clear_namespace(
                    self.buffer,
                    self.namespace,
                    row,
                    row + 1,
                )
                utils.buf_set_hls(
                    self.session,
                    self.buffer,
                    self.namespace,
                    self.hls_matrix[row],
                )

        self.prev_editted_lines = set()

        if self._is_weird_move(move):
            self.board.push(move)

            self.displayable_board = self._create_displayable_board()

            self.redraw()
            return

        self.board.push(move)

        startingpos = move.from_square
        endingpos = move.to_square

        startingpos = self._square_to_cell_index(startingpos)
        endingpos = self._square_to_cell_index(endingpos)

        moved_piece = self.displayable_board[startingpos["row"]][startingpos["col"]]

        newstartingline = self.displayable_board[startingpos["row"]]
        newstartingline = self._edit_string_partial(
            newstartingline, startingpos["col"], PIECES[self.theme]["spacer"]
        )

        utils.buf_set_lines(
            self.session,
            self.buffer,
            [newstartingline],
            startingpos["row"],
            startingpos["row"] + 1,
        )

        self.displayable_board[startingpos["row"]] = self.buffer[startingpos["row"]]

        newendingline = self.displayable_board[endingpos["row"]]
        newendingline = self._edit_string_partial(
            newendingline, endingpos["col"], moved_piece
        )

        utils.buf_set_lines(
            self.session,
            self.buffer,
            [newendingline],
            endingpos["row"],
            endingpos["row"] + 1,
        )

        self.displayable_board[endingpos["row"]] = self.buffer[endingpos["row"]]

        self.displayable_board[:] = self.buffer[:]

        # hls

        utils.buf_set_hls(
            self.session,
            self.buffer,
            self.namespace,
            self.hls_matrix[startingpos["row"]],
        )
        utils.buf_set_hls(
            self.session,
            self.buffer,
            self.namespace,
            self.hls_matrix[endingpos["row"]],
        )

        # utils.buf_clear_namespace(self.session, self.buffer, self.namespace)

        # for line in self.hls_matrix:
        #     for hl in line:
        #         _hl = hl.copy()
        #         if (
        #             _hl[1] == startingpos["row"]
        #             and _hl[2] == (startingpos["col"] - 1) * 3
        #         ):
        #             _hl[0] = self.hl_group_move_from
        #         elif _hl[1] == endingpos["row"] and hl[2] == (endingpos["col"] - 1) * 3:
        #             _hl[0] = self.hl_group_move_to

        #         utils.buf_add_hl(self.session, self.buffer, self.namespace, _hl)

        utils.buf_set_hls(
            self.session,
            self.buffer,
            self.namespace,
            [
                [
                    self.hl_group_move_from,
                    startingpos["row"],
                    (startingpos["col"] - 1) * 3,
                    (startingpos["col"] + 2) * 3,
                ],
                [
                    self.hl_group_move_to,
                    endingpos["row"],
                    (endingpos["col"] - 1) * 3,
                    (endingpos["col"] + 2) * 3,
                ],
            ],
        )

        self.prev_editted_lines.add(startingpos["row"])
        self.prev_editted_lines.add(endingpos["row"])
        if self.board.is_check():
            checkers = self.board.checkers()
            for chkr in checkers:
                chkrrow = 7 - chkr // 8
                utils.buf_add_hl(
                    self.session,
                    self.buffer,
                    self.namespace,
                    ["Checker", chkrrow, (chkr % 8) * 9, (chkr % 8 + 1) * 9],
                )
                self.prev_editted_lines.add(chkrrow)

            checked = self._find_king(self.board.turn)

            utils.buf_add_hl(
                self.session,
                self.buffer,
                self.namespace,
                ["Checked", checked[0], checked[1] * 9, (checked[1] + 1) * 9],
            )

            self.prev_editted_lines.add(checked[0])

    def _is_weird_move(self, move: Move):
        if (
            self.board.is_castling(move)
            or self.board.is_en_passant(move)
            or move.promotion
        ):
            return True
        else:
            return False

    def _find_king(self, side: Literal["white", "black"]):
        king = "K" if side == "white" else "k"
        rows = self.board.board_fen().split("/")
        row = 0
        for r in rows:
            col = 0
            for c in r:
                if c.isdigit():
                    col += int(c)
                elif c == king:
                    return [row, col]
                else:
                    col += 1
            row += 1
        return None

    def _square_to_cell_index(self, square: Square):
        """accounts for spacer between squares"""
        return {
            "row": 7 - square_rank(square),
            "col": (square_file(square) + 1) * 3 - 2,
        }  # square_file return is 0 based index > convert to 1 based for multiplication > convert back to 0 based
        # rank is row, file is column

    def _edit_string_partial(self, ogstring: str, index: int, replacement: str):
        assert len(replacement) == 1, "FUCK"
        ogstring = list(ogstring)
        ogstring[index] = replacement
        return "".join(ogstring)

    def _set_buffer_local_keymap(self):
        utils.noremap_lua_callback(
            self.session,
            "./gui_tests/lua/BoardWinClickCallback.lua",
            "<leftmouse>",
            "<cmd>lua BoardWinLeftClickCallback()<CR>",
            current_buffer_specific=True,
            insertmodeaswell=True,
        )

    def _set_hls(self):  # needs work for special hls
        self.hls_matrix = self._create_default_hls()

    def _set_extmarks(self):
        self.extmark_list = []

        ns = utils.namespace(self.session, "BoardWinNs")
        for i in range(8):
            for j in range(8):
                extmark = utils.buf_set_extmark(
                    self.session,
                    self.buffer,
                    ns,
                    i,
                    j,
                    utils.ExtmarksOptions(
                        end_row=i,
                        end_col=j + 1,
                        hl_group="StatusLine" if (i + j) % 2 == 0 else "ErrorMsg",
                        strict=False,
                        hl_mode="replace",
                    ),
                )

                self.extmark_list.append(extmark)
