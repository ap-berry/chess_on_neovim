from time import sleep
from pynvim.api import Nvim, Buffer
import utils
import re
from pynvim import attach
import berserk
from berserk import Client
import os
from dotenv import load_dotenv
from errorwin import ErrorWin
from typing import Literal

load_dotenv()

pages = {
    "home": [
        " Main Menu~",
        "",
        " -> Seek Opponent",
        " -> Challenge open",
        " -> Challenge ai",
        " <- Exit chess_on_neovim",
    ],
    "seek": [
        " Seek Random Opponent~ ",
        "",
        " Time control(m) : 10",
        " Increment(s)    : 0",
        " Rated?          : true",
        " Start Game ->",
        " <- Back",
    ],
    "challenge_ai": [
        " Challenge Ai~ ",
        "",
        " Level           : 8",
        " Time control(s) : 600",
        " Increment(s)    : 0",
        " Color           : Random",  # enter function
        " Start Game ->",
        " <- Back",
    ],
    "challenge_open": [" not done yet"],
}

page_actions = {
    "home": [
        None,
        None,
        "switchpage_seek",
        "switchpage_to_challenge_open",
        "switchpage_to_challenge_ai",
        "kill_main_process",
    ],
    "seek": [None, None, None, None, None, "create_seek", "switchpage_to_home"],
    "challenge_open": [
        None,
        None,
    ],
    "challenge_ai": [
        None,
        None,
        None,
        None,
        None,
        None,
        "create_challenge_ai",
        "switchpage_to_home",
    ],
}
# todo : figure out a better way to implement the logic for button actions in different pages, maybe split the logic part between lua and python????

"""
the menu has buffer specific keymaps that update a global variable in neovim with space separated events that indicate on which line the enter key was pressed
it does not read, it only write to it.
call the MenuWin.updateMenu method with a single event to update the gui accordingly.
the first two lines must be actionless and only contain info about the current page.


the menu has pages which are essentially a collection of buffer text and window configs (such as create challenge page)
the menu window should not be hidden/deleted unless a game is started
you can extract the events from the events variable by reading it from neovim using the get_global_var from the utils module, the variable name is g:menu_events 
the variable is automatically set to '' when a MenuWin instance is created.

"""


class MenuWin:
    def __init__(self, session: Nvim, client: Client) -> None:
        self.session = session
        self.client = client
        self.buffer = utils.find_buf(session, "menu_buffer") or utils.create_buf(
            session, "menu_buffer"
        )

        self.window_config = utils.config_gen(
            session,
            config="menu",
            border="single",
            win=session.current.window,
            minimal=True,
        )
        self.window = utils.find_window_from_title(
            session, "menu"
        ) or utils.create_window(
            session, self.buffer, True, config=self.window_config, title="menu"
        )
        self.page = "home"
        self.buffer[:] = pages[self.page]
        self.options = [0, 0, self.kill_window]

        self._set_current()
        utils.set_cursor(session, self.window, (2, 0))
        self._set_buffer_local_keymap()

    def process_menu_event(self, event: int):
        if self.page == "home":
            self.do_action_home(page_actions["home"][event])
        elif self.page == "challenge_ai":
            self.do_action_challenge_ai(page_actions["challenge_ai"][event])
        elif self.page == "seek":
            self.do_action_seek(page_actions["seek"][event])

    def _switch_page(
        self, next_page: Literal["home", "challenge_ai", "challenge_open", "seek"]
    ):
        self.page = next_page
        self.buffer[:] = pages[next_page]

    def do_action_home(self, action: str):
        if action == "switchpage_seek":
            self._switch_page("seek")
        elif action == "switchpage_to_challenge_open":
            self._switch_page("challenge_open")
        elif action == "switchpage_to_challenge_ai":
            self._switch_page("challenge_ai")

        elif action == "kill_main_process":
            self.kill_window()
            exit()

    def do_action_seek(self, action: str):
        if action == "create_seek":
            assert self.page == "seek", "Page is not seek so wrong action"
            time = self._find_numbers_from_string(self.buffer[2])[0]
            inc = self._find_numbers_from_string(self.buffer[3])[0]
            rated = True if self.buffer[4].lower().find("true") != -1 else False

            newgame = self.client.board.seek(time, inc, rated)
        elif action == "switchpage_to_home":
            self._switch_page("home")

    def do_action_challenge_ai(self, action: str):
        if action == "create_challenge_ai":
            current_games = self.client.games.get_ongoing()

            if len(current_games) > 0:
                ErrorWin(self.session, "You already have an ongoing game.")
                return

            buffer_text = self.buffer[:]
            level = self._find_numbers_from_string(buffer_text[2])[0]
            clock_limit_seconds = self._find_numbers_from_string(buffer_text[3])[0]
            clock_inc = self._find_numbers_from_string(buffer_text[4])[0]
            color = "black" if buffer_text[4].lower().find("black") != -1 else "white"

            response = self.client.challenges.create_ai(
                level=level,
                clock_increment=clock_inc,
                clock_limit=clock_limit_seconds,
                color=color,
            )

            print(response)

        elif action == "switchpage_to_home":
            self._switch_page("home")

    def _set_buffer_local_keymap(self):
        self.session.command("let g:menu_events = ''")
        utils.noremap_lua_callback(
            self.session,
            "/mnt/Study And Code/project/chess_on_neovim/gui_tests/lua/callback.lua",
            "<CR>",
            "<cmd>:lua whichbutton()<CR>",
            current_buffer_specific=True,
            insertmodeaswell=True,
        )

    def _find_numbers_from_string(self, string: str):
        return [int(n) for n in re.findall(r"\d+", string)]

    def _parse_pressed(self, pressed: str):
        return pressed.split(":")[1] - 2

    def _set_current(self):
        self.session.current.buffer = self.buffer

    def kill_window(self):
        self.buffer[:] = []
        self.session.api.win_close(self.window, True)
        self.session.api.buf_delete(self.buffer, {"force": True})


def test():
    API_TOKEN = os.getenv("API_TOKEN")
    session = berserk.TokenSession(API_TOKEN)
    client = berserk.Client(session=session)

    nvim = attach("tcp", "127.0.0.1", 6789)

    m = MenuWin(nvim, client)

    while True:
        events = utils.get_global_var(nvim, "menu_events")
        if not events:
            continue

        for e in events.split(" "):
            if e != "":
                m.process_menu_event(
                    int(e) - 1
                )  # since lua has 1 based index not 0 based !!!!!!!!!!!!!!!!!!!!!!!!!

        utils.set_global_var(nvim, "menu_events", "")

        sleep(0.1)


test()


# create_open(clock_limit=None, clock_increment=None, variant=None, position=None)[source]
# Create a challenge that any two players can join.

# Parameters
# clock_limit (int) – clock initial time (in seconds)

# clock_increment (int) – clock increment (in seconds)

# variant (Variant) – game variant to use

# position (str) – custom intial position in FEN (variant must be standard and the game cannot be rated)

# Returns
# challenge data

# Return type
# dict
