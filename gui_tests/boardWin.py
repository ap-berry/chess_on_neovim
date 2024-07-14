from time import sleep
from pynvim import attach
from pynvim.api import Nvim
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
        board: Board = Board(),
        window_config: Optional[dict] = None,
        myside: Literal["black", "white"] = "white",
        variant: str = "standard",
        theme: Literal["Light", "Dark"] = "Light",
        app_ns: int = None,
    ):
        self.neovim_session = session
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
            self.neovim_session,
            self.buffer,
            False,
            window_config
            or utils.config_gen(session, config="board"),
            "BoardWindow",
        )
        self.neovim_session.api.win_set_option(self.window, "winhighlight", 'Normal:BoardWindowBackground,FloatBorder:BoardWindowFloatBorder')        


        self.namespace = app_ns or utils.namespace(self.neovim_session, "BoardSquaresNs")


        self.variant = variant
        self.flip = myside != "white"
        if self.variant == "racingKings":
            self.flip = False
            
        self.theme = theme
        self.hl_group_white_sq = "ChessBoardWhiteSquare"
        self.hl_group_black_sq = "ChessBoardBlackSquare"
        self.hl_group_move_from = "ChessBoardMovedFrom"
        self.hl_group_move_to = "ChessBoardMovedTo"
        self.hl_group_checked = "ChessBoardChecked"
        self.hl_group_board_border = "ChessBoardBorder"
        self.hl_group_special_white_sq = "ChessBoardSpecialWhiteSquare"
        self.hl_group_special_black_sq = "ChessBoardSpecialBlackSquare"
        self.hl_group_special_move_from = "ChessBoardSpecialMovedFrom"
        self.hl_group_special_move_to = "ChessBoardSpecialMovedTo"
            
        self.redraw("")

        self.autocmd_group = self.neovim_session.api.create_augroup(
            "BoardWinAuGroup", {"clear": True}
        )

        utils.buf_add_hl(
            self.neovim_session,
            self.buffer,
            self.namespace,
            [self.hl_group_board_border, 0, 0, -1],
        )

    def flip_board(self):
        self.flip = not self.flip
        self.redraw(self.board.peek() if len(self.board.move_stack) != 0 else "")

    def set_autocmd(self, handle: int):
        self.neovim_session.api.create_autocmd(
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

    def redraw(self, lastMove: Union[str, Move]):
        utils.buf_set_extmark(self.neovim_session, *self._create_board_extmark(lastMove))
        utils.force_redraw(nvim=self.neovim_session)

    def is_legal_move(self, move: Move):
        if move in self.board.legal_moves:
            return True
        else:
            return False

    def _set_current(self):
        self.neovim_session.current.buffer = self.buffer

    def kill_window(self):
        self.neovim_session.api.win_close(self.window, True)
        self.neovim_session.api.buf_delete(self.buffer, {"force": True})

    def resize(self):
        self.neovim_session.api.win_set_config(
            self.window,
            {
                "relative": "editor",
                "row": (utils.workspace_height(self.neovim_session) - 10) // 2,
                "col": (utils.workspace_width(self.neovim_session) - 28 + 32) // 2, 
            }
        )
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

        if self.variant != "standard":
            # +1 to account for the border
            if self.variant == "racingKings":
                for i in range(8):
                    virt_lines[0][i+1][1] = self.hl_group_special_white_sq if i % 2 == 0 else self.hl_group_special_black_sq
            elif self.variant == "kingOfTheHill":
                virt_lines[3][3+1][1] = self.hl_group_special_white_sq 
                virt_lines[3][4+1][1] = self.hl_group_special_black_sq
                virt_lines[4][3+1][1] = self.hl_group_special_black_sq
                virt_lines[4][4+1][1] = self.hl_group_special_white_sq
    

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

            if self.variant == "kingOfTheHill":
                if from_sq_row == 0:
                    virt_lines[from_sq_row][from_sq_col][1] = self.hl_group_special_move_from
                if to_sq_row == 0:
                    virt_lines[to_sq_row][to_sq_col][1] = self.hl_group_special_move_to
            elif self.variant == "racingKings":
                if from_sq_row == 3 or from_sq_row == 4:
                    if from_sq_col == 4 or from_sq_col == 5:
                        virt_lines[from_sq_row][from_sq_col][1] = self.hl_group_special_move_from                    
                elif to_sq_row == 3 or to_sq_row == 4:
                    if to_sq_col == 4 or to_sq_col == 5:
                        virt_lines[to_sq_row][to_sq_col][1] = self.hl_group_special_move_to
            else:
                virt_lines[from_sq_row][from_sq_col][1] = self.hl_group_move_from
                virt_lines[to_sq_row][to_sq_col][1] = self.hl_group_move_to

        if self.board.is_check():
            king_in_check_sq = self._find_king_square(self.board.turn)
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

def test():
    nvim = attach("tcp", "127.0.0.1", 6789)

    b = BoardWin(
        nvim,
        nvim.current.window,
        theme_file_path="themes/ayu_dark/.board"
    )

    b.draw_push_move(Move.from_uci("e2e4"))
    b.draw_push_move(Move.from_uci("e7e5"))
    b.draw_push_move(Move.from_uci("d1f3"))
    b.draw_push_move(Move.from_uci("d7d5"))
    b.draw_push_move(Move.from_uci("f3f7"))

    while True:
        try:
            b._set_highlights_from_file()
            sleep(1)
        except:
            pass
