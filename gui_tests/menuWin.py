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
        " -> Join Ongoing Game",
        " -> Seek Opponent",
        " -> Challenge open",
        " -> Challenge ai",
        " <- Exit chess_on_neovim",
    ],
    "ongoing": [" Ongoing Games~", "", "Loading...    ", " <- Back"],
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
        " Level           : 1",
        " Time control(s) : 600",
        " Increment(s)    : 0",
        " Color           : Random",  # enter function
        " Start Game ->",
        " <- Back",
    ],
    "challenge_open": [" not done yet", " <- Back"],
}

page_actions = {
    "home": [
        None,
        None,
        "switchpage_to_ongoing",
        "switchpage_to_seek",
        "switchpage_to_challenge_open",
        "switchpage_to_challenge_ai",
        "kill_main_process",
    ],
    "ongoing": [None, None, None, "switchpage_to_home"],
    "seek": [None, None, None, None, None, "create_seek", "switchpage_to_home"],
    "challenge_open": [
        None,
        "switchpage_to_home",
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
the menu has buffer specific keymaps that update a global variable in neovim with the row position of the cursor when Enter/<CR>/Return is pressed
call the MenuWin.updateMenu method with a single cursor row position to update the gui according to the page_action defined for that pressing Return on that line.
the first two lines should be actionless and only contain info about the current page.


the menu has pages which are essentially a collection of buffer text and window configs (such as create challenge page)
the menu window should not be hidden/deleted unless a game is started
you can extract the events from the events variable by reading it from neovim using the get_global_var from the utils module, the variable name is g:app_events 

`utils.get_global_var(neovim_session, "app_events")`
the variable is automatically set to and empty list when a MenuWin instance is created.

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

        self.namespace = self.session.api.create_namespace("MenuWinNS")
        self.page = "home"
        self.buffer[:] = pages[self.page]
        self.options = [0, 0, self.kill_window]

        # Workflow
        self._clear_events()
        self._set_highlights()
        self._set_locals()
        utils.set_cursor(session, self.window, (3, 0))
        self._set_buffer_local_keymap()

    def _set_locals(self):
        self.session.command("setlocal cursorline")

    def _set_highlights(self):
        self.session.command(
            "highlight CursorLine ctermbg=White ctermfg=Black cterm=None"
        )
        self.session.command("highlight NormalFloat ctermbg=Red")
        self.session.api.win_set_hl_ns(self.window, self.namespace)
        self.session.api.set_hl(
            self.namespace,
            "NormalFloat",
            {"ctermbg": "DarkBlue", "ctermfg": "White"},
        )

    def process_menu_event(self, event: int):
        if self.page == "home":
            self.do_action_home(page_actions["home"][event])
        elif self.page == "challenge_ai":
            self.do_action_challenge_ai(page_actions["challenge_ai"][event])
        elif self.page == "seek":
            self.do_action_seek(page_actions["seek"][event])
        elif self.page == "ongoing":
            self.do_action_ongoing(page_actions["ongoing"][event])
        elif self.page == "challenge_open":
            self.do_action_challenge_open(page_actions["challenge_open"][event])
        else:
            print("CASE NOT IMPLEMENTED")

    def _switch_page(
        self,
        next_page: Literal["home", "challenge_ai", "challenge_open", "seek", "ongoing"],
    ):
        self.page = next_page
        self.buffer[:] = pages[next_page]

    def do_action_ongoing(self, action: str):
        if action == "switchpage_to_home":
            self._switch_page("home")
            page_actions["ongoing"] = [None, None, None, "switchpage_to_home"]
        elif action is not None:
            """action can be gameId"""
            print("joining game ")

            app_events = utils.get_global_var(self.session, "app_events")
            app_events.append(
                {"page": "Home", "event": "startgame", "opts": {"gameId": action}}
            )
            utils.set_global_var(self.session, "app_events", app_events)

    def do_action_home(self, action: str):
        if action == "switchpage_to_ongoing":
            self._switch_page("ongoing")
            self._fill_ongoing_page()
        elif action == "switchpage_to_seek":
            self._switch_page("seek")
        elif action == "switchpage_to_challenge_open":
            self._switch_page("challenge_open")
        elif action == "switchpage_to_challenge_ai":
            self._switch_page("challenge_ai")

        elif action == "kill_main_process":
            utils.set_global_var(
                self.session,
                "app_events",
                [{"page": "Global", "event": "kill_main_process", "opts": {}}],
            )

    def _fill_ongoing_page(self):
        ongoing_games = self.client.games.get_ongoing()
        self.ongoing_games = []

        screen = self.buffer[:]
        if len(ongoing_games) == 0:
            screen[2] = " No Ongoing Games Found"
            self.buffer[:] = screen
            return

        for game in ongoing_games:
            if screen[2].startswith("Loading"):
                screen[2] = " vs " + game["opponent"]["username"]
                page_actions["ongoing"][2] = game["gameId"]

            else:
                screen.insert(-1, (" vs " + game["opponent"]["username"]))
                page_actions["ongoing"].insert(-1, game["gameId"])

            self.buffer[:] = screen

    def do_action_seek(self, action: str):
        if action == "create_seek":
            assert self.page == "seek", "Page is not seek so wrong action"
            time = self._find_numbers_from_string(self.buffer[2])[0]
            inc = self._find_numbers_from_string(self.buffer[3])[0]
            rated = True if self.buffer[4].lower().find("true") != -1 else False

            newgame = self.client.board.seek(time, inc, rated)

        elif action == "switchpage_to_home":
            self._switch_page("home")

    def do_action_challenge_open(self, action: str):
        if action == "switchpage_to_home":
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
            app_events = utils.get_global_var(self.session, "app_events")
            app_events.append(
                {
                    "page": "Home",
                    "event": "startgame",
                    "opts": {"gameId": response["id"]},
                }
            )
            utils.set_global_var(self.session, "app_events", app_events)

        elif action == "switchpage_to_home":
            self._switch_page("home")

    def _clear_events(self):
        utils.set_global_var(self.session, "app_events", [])

    def _set_buffer_local_keymap(self):
        utils.noremap_lua_callback(
            self.session,
            "./gui_tests/lua/MenuWinCallback.lua",
            "<CR>",
            "<cmd>:lua MenuWinCallback()<CR>",
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
