from typing import Literal, Tuple, Union
from time import time
from datetime import datetime
from berserk.utils import to_millis


class GameClock:
    def __init__(
        self,
        white_time: Union[datetime, int],
        white_inc: Union[datetime, int],
        black_time: Union[datetime, int],
        black_inc: Union[datetime, int],
        side: Literal["black", "white"],
    ):
        """Must call .start() in order to get times"""
        self.white_time = (
            to_millis(white_time) if not isinstance(white_time, int) else white_time
        )
        self.white_inc = (
            to_millis(white_inc) if not isinstance(white_inc, int) else round(white_inc)
        )

        self.black_time = (
            to_millis(black_time) if not isinstance(black_time, int) else black_time
        )
        self.black_inc = (
            to_millis(black_inc) if not isinstance(black_inc, int) else round(black_inc)
        )

        self.side = side
        self.started = False

    def start(self):
        self.started_time = round(time() * 1000)
        self.started = True

    def stop(self):
        self.started = False

    
    def change_sides(self):
        self.side = "black" if self.side == "white" else "white"

    def player_and_time_ms(self):
        """returns which player is playing and their remaining time in milliseconds (int) [player, time]"""
        assert self.started, "Clock Not Started"

        current_time = round(time() * 1000)
        time_passed = current_time - self.started_time
        self.started_time = current_time
        if self.side == "black":
            self.black_time -= time_passed
            return ["black", self.black_time]

        else:
            self.white_time -= time_passed
            return ["white", self.white_time]
