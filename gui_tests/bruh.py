import chess
from board import BoardWin
from pynvim import attach
from dynamic_stats import StatsWin

nvim = attach("tcp", '127.0.0.1', 6789)
b = chess.Board()

sw = StatsWin(nvim)
sw.draw()




