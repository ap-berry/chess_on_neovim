from pynvim.api import Nvim, Buffer, Window
from utils import *
from utils import BadFenError
from chess import Board, Move, Square, square_file, square_rank
from typing import Tuple, Optional

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
    "spacer": "\u2000",
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
    ):
        self.session = session
        self.board = board

        self.buffer = find_buf(session, "board_buffer") or create_buf(
            session, "board_buffer"
        )

        self.window = find_window_from_title(session, "BoardWindow") or create_window(
            self.session,
            self.buffer,
            True,
            window_config or config_gen(session, config="board", win=relative_to_win),
            "BoardWindow",
        )
        self.displayable_board = self._create_displayable_board()

        self.redraw()

    def redraw(self):
        buf_set_lines(nvim=self.session, buf=self.buffer, text=self.displayable_board)
        force_redraw(nvim=self.session)

    def _set_current(self):
        self.session.current.buffer = self.buffer

    def destroy(self):
        self.buffer[:] = []
        self.session.api.win_close(self.window, True)
        self.session.api.buf_delete(self.buffer, {"force": True})

    # should only run at init
    def _create_displayable_board(self):
        _fen = self.board.fen().split(" ")[0]
        _fen = _fen.split("/")
        # if self.flip:
        # _fen = self._flip_board_fen(_fen)

        if len(_fen) != 8:
            raise BadFenError
        _board = []
        for ln in _fen:
            line = ""
            for c in ln:
                if c.isnumeric():
                    line += PIECES["spacer"] * int(c) * 3
                else:
                    line += PIECES["spacer"] + PIECES[c] + PIECES["spacer"]
                    # if (i+j) % 2 != 0:
                    # hl.append(("BlackSquare", i+border_gap, j*cell_width*3+border_gap, j*cell_width*3+cell_width*3+border_gap))
            _board.append(line)

        return _board

    @staticmethod
    def _flip_board_fen(fen: list[str]):
        _f = [l[::-1] for l in fen]
        _f.reverse()
        return _f

    def draw_takeback_once(self):
        self.board.pop()

        self.displayable_board = self._create_displayable_board()

        self.redraw()

    def draw_push_move(self, uci_move: str):
        move = Move.from_uci(uci_move)

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
            newstartingline, startingpos["col"], PIECES["spacer"]
        )

        buf_set_lines(
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

        buf_set_lines(
            self.session,
            self.buffer,
            [newendingline],
            endingpos["row"],
            endingpos["row"] + 1,
        )

        self.displayable_board[endingpos["row"]] = self.buffer[endingpos["row"]]

        self.displayable_board[:] = self.buffer[:]

    def _is_weird_move(self, move: Move):
        if (
            self.board.is_castling(move)
            or self.board.is_en_passant(move)
            or move.promotion
        ):
            return True
        else:
            return False

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
