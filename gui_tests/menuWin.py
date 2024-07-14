from time import sleep
from pynvim import attach
from random import choice

from pynvim.api import Nvim, Window
import utils
import re
import os

from threading import Lock
from berserk import Client
from errorwin import ErrorWin
from typing import Literal
from dotenv import set_key, load_dotenv
from os import getenv
from berserk import TokenSession
from gameWin import GameWinManager,GameClock


pages = {
    "home": [
        " Main Menu ~",
        "",
        " -> Join Ongoing Game",
        " -> Seek Opponent",
        " -> Challenge ai",
        " -> Settings",
        " <- Exit chess_on_neovim",
        "",
        " [Enter], Up, Down to navigate",
        "",
        " Ctrl + R in normal mode will",
        " refresh the buffer text",
        " It wont refresh everything",

    ],
    "ongoing": [" Ongoing Games~", "", "Loading...    ", " <- Back"],
    "challenge_ai": [
        " Challenge Ai ~ ",
        "",
        " Level           : 1",
        " Time control(s) : 600",
        " Increment(s)    : 0",
        " Color           : Random",  # <CR> to change color functionalit in the future?
        " Varient         : standard",
        " Start Game ->",
        " <- Back",
    ],
    "seek": [
        " Seek Opponent ~ ",
        "",
        " Time control(s) : 600",
        " Increment(s)    : 0",
        " Variant         : standard",
        " Rated [yes/no]  : no",
        " Color           : Random",
        " Start Game ->",
        " <- Back",
        "",
        "info for later"
        ],
    "settings": [
        " Settings ~",
        "",
        " detecting account...",
        " -> set api key",
        " -> set theme",
        " <- Back",
    ],
    "set_api_key": [
        " Set API TOKEN ~",
        "",
        " loading...",
        " -> Ok",
        " <- Back/Cancel",
    ],
    "themes": [
        " Themes ~",
        "",
        " [Press Enter to select]",
        " <- Back",
        " Loading Themes...",
    ],
}

page_actions = {
    "home": [
        None,
        None,
        "switchpage_to_ongoing",
        "switchpage_to_seek",
        "switchpage_to_challenge_ai",
        "switchpage_to_settings",
        "exit",
        None,
        None,
        None,
        None,

    ],
    "ongoing": [None, None, None, "switchpage_to_home"],
    "seek": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "create_seek",
        "switchpage_to_home",
        None,
        None
    ],
    "challenge_ai": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "create_challenge_ai",
        "switchpage_to_home",
    ],
    "settings": [
        None,
        None,
        None,
        "switchpage_to_set_api_key",
        "switchpage_to_change_themes",
        "switchpage_to_home",
    ],
    "set_api_key": [None, None, None, "set_api_key", "switchpage_to_settings"],
    "themes": [
        None,
        None,
        None,
        "switchpage_to_settings",
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


class MenuWinManager:
    def __init__(self, session: Nvim, berserk_client: Client = None, config_file_path = ".config") -> None:
        self.neovim_session = session
            
        self.buffer = utils.find_buf(session, "menu_buffer") or utils.create_buf(
            session, "menu_buffer"
        )

        self.window_config = utils.config_gen(
            session,
            config="menu",
            minimal=True,
        )
        self.window = utils.find_window_from_title(
            session, "menu"
        ) or utils.create_window(
            session, self.buffer, True, config=self.window_config, title="menu"
        )
        utils.win_set_local_winhighlight(self.neovim_session, self.window, "Normal:MenuBackground,CursorLine:MenuCursorLine")

        self.page = "home"
        self.buffer[:] = pages[self.page]
        utils.set_cursor(session, self.window, (3, 0))



        self.config_file_path = config_file_path
        if berserk_client is not None:
            self.berserk_client = berserk_client
        else:
            self.berserk_client = None
             
        self._set_locals()
        self._set_buffer_local_keymap()
        self.neovim_session.command("stopinsert")
        
        
        
    def _set_locals(self):
        self.neovim_session.command("setlocal cursorline")

    def handle_enter_event(self, event: int):
        if self.page == "home":
            self.do_action_home(page_actions[self.page][event])
        elif self.page == "challenge_ai":
            self.do_action_challenge_ai(page_actions[self.page][event])
        elif self.page == "ongoing":
            self.do_action_ongoing(page_actions[self.page][event])
        elif self.page == "seek":
            self.do_action_seek(page_actions[self.page][event])
        elif self.page == "settings":
            self.do_action_settings(page_actions[self.page][event])
        elif self.page == "set_api_key":
            self.do_action_set_api_key(page_actions[self.page][event])
        elif self.page == "themes":
            self.do_action_themes(page_actions[self.page][event])

        else:
            print("CASE NOT IMPLEMENTED")

    def switch_page(
        self,
        next_page: Literal[
            "home",
            "challenge_ai",
            "seek",
            "ongoing",
            "settings",
            "set_api_key",
            "themes",
        ],
    ):
        self.page = next_page
        self.buffer[:] = pages[next_page]

    def do_action_ongoing(self, action: str):
        if action == "switchpage_to_home":
            self.switch_page("home")
            page_actions["ongoing"] = [None, None, None, "switchpage_to_home"]
        elif action is not None:
            """action is most likely [gameId, color]"""
            print("Joingng Game "+ str(action))

            app_events = utils.get_global_var(self.neovim_session, "app_events")
            app_events.append(
                {
                    "page": "Menu",
                    "event": "join_game",
                    "opts": {"gameId": action[0], "color": action[1]},
                }
            )
            utils.set_global_var(self.neovim_session, "app_events", app_events)

    def do_action_home(self, action: str):
        if action == "switchpage_to_ongoing":
            self.switch_page("ongoing")
            self._fill_ongoing_page()
        elif action == "switchpage_to_seek":
            self.switch_page("seek")
        elif action == "switchpage_to_challenge_ai":
            self.switch_page("challenge_ai")
        elif action == "switchpage_to_settings":
            self.switch_page("settings")
            self._fill_settings_page()
        elif action == "exit":
            utils.set_global_var(
                self.neovim_session,
                "app_events",
                [{"page": "Global", "event": "exit", "opts": {}}],
            )

    def _fill_settings_page(self):
        screen = self.buffer[:]
        if not self.berserk_client:
            token = utils.get_api_key(self.config_file_path)
            try:
                session = TokenSession(token)
                self.berserk_client = Client(session)
                self.account = self.berserk_client.account.get()

                screen[2] = f" Acc:{self.account['username']}"
                
                utils.add_app_events(self.neovim_session, {"page": "Global", "event": "set_api_key", "opts": {
                    "token" : token
                }})
            except:
                self.berserk_client = None
                screen[2] = " Login Failed. Try setting api key"
            self.buffer[:] = screen
        else:
            self.account = self.berserk_client.account.get()
            screen[2] = f" Acc:{self.account['username']}"
            self.buffer[:] = screen

    def do_action_set_api_key(self, action: str):
        if action == "switchpage_to_settings":
            self.switch_page("settings")
            self._fill_settings_page()
        elif action == "set_api_key":
            screen = self.buffer[:]
            token = screen[2].replace("Token:", "", 1).strip()
            _temp = screen[2]
            screen[2] = " please wait.."
            self.buffer[:] = screen
            _temp_client = self.berserk_client
            try:
                session = TokenSession(token)
                self.berserk_client = Client(session=session)
                self.account = self.berserk_client.account.get()
                screen[2] = " Successfuly logged in"
                self.buffer[:] = screen
                sleep(0.4)
                utils.write_api_key(token)
                self._fill_api_key_page()
                
                utils.add_app_events(self.neovim_session, {"page": "Global", "event": "set_api_key", "opts": {
                    "token" : token
                }})
                
            except Exception as e:
                self.berserk_client = _temp_client
                screen.append("")
                screen.append(str(e))
                screen[2] = _temp
                self.buffer[:] = screen

                print(e)  

    def _fill_api_key_page(self):
        assert self.page == "set_api_key", "method called when page not set_api_key"
        screen = self.buffer[:]

        token = utils.get_api_key(self.config_file_path)
        if token:
            screen[2] = " Token:" + token
        else:
            screen[2] = " Token:"
        self.buffer[:] = screen

    def do_action_themes(self, action: str):
        if action == "switchpage_to_settings":
            self.switch_page("settings")
            page_actions['themes'] = page_actions['themes'][:4]
        elif action is not None:
            print('Setting Theme '+ action['theme'])            
            
            utils.add_app_events(self.neovim_session, {
                "page": "Global",
                "event" : "change_theme",
                "opts": {
                    "theme": action["theme"]
                }
            })
            
    def _fill_themes_page(self):
        assert self.page == "themes", "Function must be called with themes as current page"
        dirnames = [name for name in os.listdir("themes/")]

        screen = self.buffer[:]
        screen.pop()
        self.buffer[:] = screen
        for name in dirnames:
            screen.append(" "+name)
            self.buffer[:] = screen
            page_actions['themes'].append({ "theme": name })
        
    
    def do_action_settings(self, action: str):
        if action == "switchpage_to_set_api_key":
            self.switch_page("set_api_key")
            self._fill_api_key_page()
        elif action == "switchpage_to_change_themes":
            self.switch_page("themes")
            self._fill_themes_page()
        elif action == "switchpage_to_home":
            self.switch_page("home")
    
    def _fill_ongoing_page(self):
        screen = self.buffer[:]

        if not self.berserk_client:
            ErrorWin(
                self.neovim_session,
                "You are not connected to lichess, try adding your api token/key",
            )
            screen[2] = " Not Connected"
            self.buffer[:] = screen

            return

        ongoing_games = []
        try:
            ongoing_games = self.berserk_client.games.get_ongoing(count=50)
        except:
            screen[2] = " Could Not Connect"
            self.buffer[:] = screen
            return
            
        if len(ongoing_games) == 0:
            screen[2] = " No Ongoing Games Found"
            self.buffer[:] = screen
            return

        for game in ongoing_games:
            if screen[2].startswith("Loading"):
                screen[2] = " vs " + game["opponent"]["username"]
                page_actions["ongoing"][2] = [game["gameId"], game["color"]]

            else:
                screen.insert(-1, (" vs " + game["opponent"]["username"]))
                page_actions["ongoing"].insert(-1, [game["gameId"], game["color"]])

            self.buffer[:] = screen

    def do_action_seek(self, action: str):
        if action == "switchpage_to_home":
            self.switch_page("home")
        elif action == "create_seek":
            if not self.berserk_client:
                ErrorWin(
                    self.neovim_session,
                    "You are not connected to lichess, try adding your api token/key",
                )
                return


            current_games = self.berserk_client.games.get_ongoing()
            if len(current_games) > 0:
                ErrorWin(self.neovim_session, "You already have an ongoing game.")
                return
            
            buffer_text = self.buffer[:]
            clock_limit_seconds = self._find_numbers_from_string(buffer_text[2])
            if len(clock_limit_seconds) == 0:
                ErrorWin(self.neovim_session, "Invalid Time Control, cannot go below 600 seconds")
            clock_limit_seconds = clock_limit_seconds[0]
            
            clock_inc = self._find_numbers_from_string(buffer_text[3])
            if len(clock_inc) == 0:
                ErrorWin(self.neovim_session, "Invalid Increment. must be between 0 and 180 seconds")
            clock_inc = clock_inc[0]


            variant = self._get_variant_from_string(buffer_text[4])
            if variant is None:
                ErrorWin(self.neovim_session, "Variation must be one of the following: \nstandard, \natomic, \nantichess, \nthreecheck, \nracingkings, \nkingofthehill, \nhorde, \ncrazyhouse, \nchess960")
                return
            rated = self._get_rated_or_not(buffer_text[5])
            
            # custom_fen = self._get_custom_fen(buffer_text[6])
            
            time = clock_limit_seconds//60
            inc = clock_inc // 60
            
            self.buffer[:] = ["", " Searching for opponent..."]
            
            self.berserk_client.board.seek(
                time=time,
                increment=inc,
                variant=variant,
                rated=rated,
            )
            
            self.buffer[:] = ["", " Game Created!"]
            utils.set_global_var(self.neovim_session, "app_events", [])
            utils.add_app_events(
                self.neovim_session,
                {
                    "page": "Menu",
                    "event": "create_seek",
                    "opts":{}
                })    
        
    def _get_rated_or_not(self, string: str):
        string = string.lower().split(":")[1]
        if "yes" in string or "y" in string:
            return True
        
        return False
        
        
    def _get_variant_from_string(self, string: str):
        string = string.lower().replace(" ", "")
        varients = ["standard", "atomic", "antichess", "chess960", "crazyhouse", "threeCheck", "racingKings", "kingOfTheHill", "horde"]
        for varient in varients:
            if varient.lower() in string:
                return varient
        
        return None
    
    def do_action_challenge_ai(self, action: str):
        if action == "create_challenge_ai":
            if not self.berserk_client:
                ErrorWin(
                    self.neovim_session,
                    "You have not set an API token yet and are thus not connected to lichess",
                )
                return
            current_games = self.berserk_client.games.get_ongoing()

            if len(current_games) > 0:
                ErrorWin(self.neovim_session, "You already have an ongoing game.")
                return

            buffer_text = self.buffer[:]
            level = self._find_numbers_from_string(buffer_text[2])[0]
            if level > 8 or level < 1:
                ErrorWin(self.neovim_session, "Ai Level must be between 1 and 8")
                return
            clock_limit_seconds = self._find_numbers_from_string(buffer_text[3])[0]
            if clock_limit_seconds < 600:
                ErrorWin(self.neovim_session, "Cannot play game under 10 minute time control due to api restrictions")
                return
                
            clock_inc = self._find_numbers_from_string(buffer_text[4])[0]
            if clock_inc < 0 or clock_inc > 180:
                ErrorWin(self.neovim_session, "Increment must be between 0 and 180 seconds")
                return

            if buffer_text[5].lower().find("black") != -1:
                color = "black"
            elif buffer_text[5].lower().find("white") != -1:
                color = "white"
            else:
                color = choice(["black", "white"])
                
            variation = self._get_variant_from_string(buffer_text[6])
            if variation is None:
                ErrorWin(self.neovim_session, "Variation must be one of the following: \nstandard, \natomic, \nantichess, \nthreecheck, \nracingkings, \nkingofthehill, \nhorde, \ncrazyhouse, \nchess960")
                return

            response = self.berserk_client.challenges.create_ai(
                level=level,
                clock_increment=clock_inc,
                clock_limit=clock_limit_seconds,
                color=color,
                variant=variation
            )
            
            utils.add_app_events(self.neovim_session, {
                    "page": "Menu",
                    "event": "start_game_ai",
                    "opts": { "response" : response , "side": color},
                })

        elif action == "switchpage_to_home":
            self.switch_page("home")

    def _set_buffer_local_keymap(self):
        utils.load_lua_file(self.neovim_session, "./gui_tests/lua/MenuWinCallback.lua")
        utils.buf_set_keymap(self.neovim_session, "<CR>", "<cmd>lua MenuWinCallback()<CR>", insertmodeaswell=True)
        utils.buf_set_keymap(self.neovim_session, "<C-r>", "<cmd>lua RefreshMenu()<CR>")
        

    def _find_numbers_from_string(self, string: str):
        return [int(n) for n in re.findall(r"\d+", string)]

    def _parse_pressed(self, pressed: str):
        return pressed.split(":")[1] - 2

    def _set_current(self):
        self.neovim_session.current.buffer = self.buffer

    def kill_window(self):
        """ emptys buffer, closes the window and force deletes the buffer """
        self.buffer[:] = []
        self.neovim_session.api.win_close(self.window, True)
        self.neovim_session.api.buf_delete(self.buffer, {"force": True})

    def refresh(self):
        self.switch_page(self.page)
    
    def resize(self):
        self.neovim_session.api.win_set_config(
            self.window,
            {
                "relative": "editor",
                "row": (utils.workspace_height(self.neovim_session) - 20) // 2,
                "col": (utils.workspace_width(self.neovim_session) - 34) // 2, 
            }
        )