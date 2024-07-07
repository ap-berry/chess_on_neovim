from pynvim.api import Nvim, Buffer, Window
import utils
from utils import BadFenError
from chess import Board, Move
from typing import Optional, Literal, Union


default_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

PIECES = {
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
    "s": "\u2000",
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
    "s": " ",
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

        self.buffer[:] = [
            " " * 28,
        ]
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
        self.hl_group_board_border = "Border"

        self._set_window_highlights()
        self.redraw("")

        self.autocmd_group = self.session.api.create_augroup(
            "BoardWinAuGroup", {"clear": True}
        )

        utils.buf_add_hl(
            self.session,
            self.buffer,
            self.namespace,
            [self.hl_group_board_border, 0, 0, -1],
        )

    def flip_board(self):
        self.flip = not self.flip
        self.redraw(self.board.peek() if len(self.board.move_stack) != 0 else "")

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
                "bg": "White",
                "fg": "Black",
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
                "bg": "LightGreen",
                "fg": "Black",
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
            {
                "bg": "LightBlue",
                "fg": "Black",
                "ctermbg": "LightGreen",
                "ctermfg": "Black",
                "bold": True,
                "blend": 0,
            },
        )
        self.session.api.set_hl(
            self.window_namespace,
            "MovedFrom",
            {
                "bg": "Blue",
                "fg": "Black",
                "ctermbg": "Green",
                "ctermfg": "Black",
                "bold": True,
                "blend": 0,
            },
        )
        self.session.api.set_hl(
            self.window_namespace,
            "Checker",
            {
                "bg": "LightRed",
                "fg": "Black",
                "ctermbg": "LightRed",
                "ctermfg": "Black",
                "bold": True,
                "blend": 0,
            },
        )
        self.session.api.set_hl(
            self.window_namespace,
            "Checked",
            {
                "bg": "LightRed",
                "fg": "Black",
                "ctermbg": "Red",
                "ctermfg": "Black",
                "bold": True,
                "blend": 0,
            },
        )
        self.session.api.set_hl(
            self.window_namespace,
            "Border",
            {
                "fg": "White",
                "ctermbg": "Black",
                "ctermfg": "White",
                "bold": True,
                "blend": 0,
            },
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
        # TODO
        pass

    def redraw_from_fen(self, fen: str, lastMove: str):
        self.board.set_fen(fen)
        self.redraw(lastMove)

        pass

    def redraw(self, lastMove: Union[str, Move]):
        utils.buf_set_extmark(self.session, *self._create_board_extmark(lastMove))
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

    @staticmethod
    def _flip_board_fen(fen: list[str]):
        _f = [l[::-1] for l in fen]
        _f.reverse()
        return _f

    def _create_board_extmark(self, lastMove: Union[str, Move]):
        """if you dont want to use last move highlighting pass in an empty string
        as lastMove"""

        _fen = self.board.board_fen().split("/")

        border_line = [[" " * 2, self.hl_group_board_border]]
        for i in range(8):
            border_line.append([f" {chr(97+i)} ", self.hl_group_board_border])
        border_line.append([" " * 2, self.hl_group_board_border])

        if len(_fen) != 8:
            raise BadFenError

        formatted_fen = []
        for row in _fen:
            formatted_row = ""
            for sq in row:
                if sq.isdigit():
                    formatted_row += "s" * int(sq)
                else:
                    formatted_row += sq
            formatted_fen.append(formatted_row)

        virt_lines = []
        for i in range(8):
            virt_line = [
                [
                    str(8 - i) + " ",
                    self.hl_group_board_border,
                ]
            ]
            for j in range(8):
                virt_line.append(
                    [
                        PIECES["s"] + PIECES[formatted_fen[i][j]] + PIECES["s"],
                        self.hl_group_white_sq
                        if (i + j) % 2 == 0
                        else self.hl_group_black_sq,
                    ]
                )
            virt_line.append([" " * 2, self.hl_group_board_border])

            virt_lines.append(virt_line)

        if lastMove and lastMove != "":
            if isinstance(lastMove, str):
                lastMove = Move.from_uci(lastMove)
            from_sq = lastMove.from_square
            to_sq = lastMove.to_square

            # from square er kaj
            from_sq_row = 7 - from_sq // 8
            from_sq_col = (from_sq % 8) + 1

            to_sq_row = 7 - to_sq // 8
            to_sq_col = (to_sq % 8) + 1

            virt_lines[from_sq_row][from_sq_col][1] = self.hl_group_move_from
            virt_lines[to_sq_row][to_sq_col][1] = self.hl_group_move_to

        if self.board.is_check():
            king_in_check_sq = self._find_king_square(self.board.turn)
            print(king_in_check_sq, "\n\n\n")
            assert king_in_check_sq, "King In Check Not Found"

            checked_row = king_in_check_sq[0]
            checked_col = king_in_check_sq[1] + 1

            virt_lines[checked_row][checked_col][1] = self.hl_group_checked

        if self.flip:
            virt_lines = [virt_line[::-1] for virt_line in virt_lines[::-1]]
            border_line.reverse()

            for i in range(8):
                _temp = virt_lines[i][0]
                virt_lines[i][0] = virt_lines[i][-1]
                virt_lines[i][-1] = _temp

        virt_lines.append(border_line)

        _board_extmark = [
            self.buffer,
            self.namespace,
            0,
            0,
            utils.ExtmarksOptions(id=1, virt_lines=virt_lines, virt_lines_leftcol=True),
        ]
        return _board_extmark

    def draw_takeback_once(self):
        # TODO
        pass

    def draw_push_move(self, move: Move):
        self.board.push(move)
        self.redraw(lastMove=move)

    def _find_king_square(self, side: bool) -> int:
        """returns 0-based [row, col]"""
        king = "K" if side else "k"
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

    def _set_buffer_local_keymap(self):
        utils.noremap_lua_callback(
            self.session,
            "./gui_tests/lua/BoardWinClickCallback.lua",
            "<leftmouse>",
            "<cmd>lua BoardWinLeftClickCallback()<CR>",
            current_buffer_specific=True,
            insertmodeaswell=True,
        )
