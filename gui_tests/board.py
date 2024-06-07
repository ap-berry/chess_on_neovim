from pynvim.api import Nvim, Buffer
from utils import buf_set_text, buf_set_lines, create_buf, create_window, find_buf, config_gen, force_redraw
from utils import BadFenError
from chess import Move, Square, square_file, square_rank
from typing import Tuple


fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
fen = fen.split("/")

PIECES = {
    "K" : "\u2654",
    "Q" : "\u2655",
    "R" : "\u2656",
    "B" : "\u2657",
    "N" : "\u2658",
    "P" : "\u2659",

    "k" : "\u265A",
    "q" : "\u265B",
    "r" : "\u265C",
    "b" : "\u265D",
    "n" : "\u265E",
    "p" : "\u265F",
    "spacer" : "\u2000"
}

PIECES_ASCII = {
    "K" : "K",
    "Q" : "Q",
    "R" : "R",
    "B" : "B",
    "N" : "N",
    "P" : "P",

    "k" : "k",
    "q" : "q",
    "r" : "r",
    "b" : "b",
    "n" : "n",
    "p" : "p",
    "spacer" : " "
}
 
        
class BoardWin():
  def __init__(self, session: Nvim, window_config: dict | None = None, fen: str = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'):
    self.session = session
    self.fen = fen
    self.board_buffer = find_buf(session, "board_buffer") or create_buf(session, "board_buffer")
    self.board_win = create_window(self.session, self.board_buffer, True, window_config or config_gen(session, config='board'))
    self.displayable_board = self._displayable()
    
    
  def draw_board(self):
    buf_set_lines(nvim=self.session, buf=self.board_buffer, text=self.displayable_board)
    force_redraw(nvim=self.session)
    
  def _set_current(self):
    self.session.current.buffer = self.board_buffer
  
  def kill_window(self):
    self.board_buffer[:] = []
    self.session.api.win_close(self.board_win, True)
    self.session.api.buf_delete(self.board_buffer, { "force": True })
    
  #should only run at init
  def _displayable(self):
    _fen = self.fen.split(" ")[0]
    _fen = _fen.split("/")
    if len(_fen) != 8:
      raise BadFenError
    _board = []
    for ln in _fen:
      line = ''
      for c in ln:
        if c.isnumeric():
          line+= PIECES["spacer"] * int(c) * 3
        else:
          line+= PIECES["spacer"] + PIECES[c] + PIECES["spacer"]
          # if (i+j) % 2 != 0:
              # hl.append(("BlackSquare", i+border_gap, j*cell_width*3+border_gap, j*cell_width*3+cell_width*3+border_gap))
      _board.append(line)
    return _board
  
  def display_push_move(self, uci_move: str):
    move = Move.from_uci(uci_move)
        
    startingpos = move.from_square
    endingpos = move.to_square
    
    
    startingpos = self._square_to_cell_index(startingpos)
    endingpos = self._square_to_cell_index(endingpos)
    
    moved_piece = self.displayable_board[startingpos["row"]][startingpos['col']]
    
    newstartingline = self.displayable_board[startingpos['row']]
    newstartingline = self._edit_string_partial(newstartingline, startingpos['col'], PIECES["spacer"])
    
    
    newendingline = self.displayable_board[endingpos['row']]
    newendingline = self._edit_string_partial(newendingline, endingpos['col'], moved_piece)
    
    
    buf_set_lines(self.session, self.board_buffer, [newstartingline], startingpos['row'], startingpos['row']+1)
    buf_set_lines(self.session, self.board_buffer, [newendingline], endingpos['row'], endingpos['row']+1)
    
    self.displayable_board[:] = self.board_buffer[:]
    
    
  def _square_to_cell_index(self, square: Square):
    """accounts for spacer between squares"""
    return { 'row' : 7 - square_rank(square), 'col': (square_file(square)+1)*3 -2} #square_file return is 0 based index > convert to 1 based for multiplication > convert back to 0 based
    #rank is row, file is column
    
  def _edit_string_partial(self, ogstring: str, index: int, replacement: str):
    assert len(replacement) == 1, "FUCK"
    ogstring = list(ogstring)
    ogstring[index] = replacement
    return "".join(ogstring)
    
    
    
