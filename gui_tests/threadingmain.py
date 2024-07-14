from time import sleep
from threading import Thread, Lock

from pynvim import attach
import berserk
from berserk import Client

import utils
from utils import AppEvent
from menuWin import MenuWinManager
from gameWin import GameWinManager
from errorwin import ErrorWin


def read_incoming_events_stream(events: list, client: Client, lock: Lock, unique_stop_flag):
    for e in client.board.stream_incoming_events():
        with lock:
            if unique_stop_flag["stop"]:
                return      
            events.append(e)
            
def read_game_events_stream(gameId:str, game_events: list, client: Client, lock: Lock, unique_stop_flag: any):
    for ge in client.board.stream_game_state(game_id=gameId):
        with lock:
            if unique_stop_flag["stop"]:
                return
            game_events.append(ge)
            
class Main:
    def __init__(self) -> None:        
        self.config_file_path = ".config"
        utils.find_or_create_config_file()
        
        try:
            self.neovim_session = attach("tcp", "127.0.0.1", 6789)
        except:
            raise Exception("Oops! Could not connect to a neovim instance. Please try to start it up using `nvim --listen 127.0.0.1:6789`")
            
        self.theme_dir = utils.get_theme_dir()
        self.app_namespace = 0
        self.set_theme(self.theme_dir)        
        
        self.lock = Lock()
        self.incoming_events: list = []
        self.read_incoming_events : Thread = None
        
        self.read_game_events: Thread = None
        self.game_events: list = []

        self.berserk_client: Client = None
        self.try_to_login()
        
        self.gameWinManager: GameWinManager = None
        self.menuWinManager: MenuWinManager = MenuWinManager(self.neovim_session, self.berserk_client)
        
        
        utils.load_lua_file(self.neovim_session, "./gui_tests/lua/main.lua")
        self.autocmd_group = self.neovim_session.api.create_augroup(
            "chess_on_neovim_au_group", {"clear": True}
        )
        self.neovim_session.api.create_autocmd(
            "VimResized",
            {
                "group": self.autocmd_group,
                "command": "lua ResizeWindows()",
            }
        )

        """app_events will the be the global variable that will have all the gui related events"""
        utils.set_global_var(self.neovim_session, "app_events", [])
    
    def run(self):
        try: 
            self.route_events()
        except Exception as e:
            if self.gameWinManager:
                self.gameWinManager.kill_window()
            if self.menuWinManager:
                self.menuWinManager.kill_window()
            raise e
            
    def route_events(self):
        while True:
            app_events = utils.get_global_var(self.neovim_session, "app_events")
            utils.set_global_var(self.neovim_session, "app_events", [])
            with self.lock:
                if self.gameWinManager:
                    self.gameWinManager.decrement_game_clock()
                
                for game_event in self.game_events:
                    
                    self.gameWinManager.handle_game_event(game_event)
                    self.game_events.remove(game_event)


                for app_event in app_events:
                    print(app_event)
                    app_event: AppEvent = app_event
                    
                    #Events from main menu
                    if app_event["page"] == "Menu":
                        if not self.menuWinManager:
                            continue
                        if app_event["event"] == "enter":
                            self.menuWinManager.handle_enter_event(app_event["opts"]['line'])
                        
                        elif app_event['event'] == "create_seek":
                            gamefound = False
                            for event in self.incoming_events[::-1]:
                                if event['type'] != "gameStart":
                                    continue
                                
                                gameId = event['game']['gameId']
                                side = event['game']['color']
                                
                                utils.add_app_events(
                                    self.neovim_session,
                                    {
                                        "page": "Menu",
                                        "event": "join_game",
                                        "opts": {
                                            "gameId": gameId,
                                            "color": side
                                        }
                                    }
                                )
                                gamefound = True
                            if not gamefound:
                                utils.add_app_events(self.neovim_session, {"page": "Menu", "event": "create_seek", "opts": {}})

                        elif app_event['event'] == "start_game_ai":

                            self.menuWinManager.kill_window()
                            self.menuWinManager = None
                            
                            game = app_event['opts']['response']
                            side = app_event['opts']['side']
                            self.gameWinManager = GameWinManager(self.neovim_session, game['id'], self.berserk_client, side)
                            
                            self.game_events = []
                            self.stop_flag = {'stop': False} 
                            self.read_game_events = Thread(target=read_game_events_stream, args=[game['id'], self.game_events, self.berserk_client, self.lock, self.stop_flag], daemon=True)
                            self.read_game_events.start()
                            
                            
                        elif app_event['event'] == "join_game":
                            
                            gameId = app_event['opts']['gameId']
                            side = app_event['opts']['color']
                            self.gameWinManager = GameWinManager(self.neovim_session, gameId, self.berserk_client, side)
                            if not self.gameWinManager.game:
                                ErrorWin(self.neovim_session, f" Game not found \n Game id: {app_event['opts']['gameId']} \n The game might have ended or \n you entered on nothing :|")    
                                continue
                                                        
                            self.menuWinManager.kill_window()
                            self.menuWinManager = None
                            
                            self.game_events = []
                            self.stop_flag = {'stop': False}
                            self.read_game_events = Thread(target=read_game_events_stream, args=[gameId, self.game_events, self.berserk_client, self.lock, self.stop_flag], daemon=True)
                            self.read_game_events.start()
                        elif app_event['event'] == "refresh":
                            self.menuWinManager.refresh()
                    #Events from game window
                    
                    elif app_event['page'] == "Game":
                        if not self.gameWinManager:
                            continue
                        if app_event['event'] == "internal":
                            self.gameWinManager.handle_game_event(app_event)
                        elif app_event['event'] == "pass_control":
                            action = app_event['opts']['action']
                            if action == "kill_game_window":
                                if self.read_game_events and self.read_game_events.is_alive():
                                    self.stop_flag['stop'] = True
                                    #move reference to avoid garbage collection
                                    self.temp_thread = self.read_game_events
                                    self.temps_stop_flag = self.stop_flag
                                
                                self.gameWinManager.kill_window()
                                self.gameWinManager = None
                                
                                
                                self.menuWinManager = MenuWinManager(self.neovim_session, self.berserk_client)
                            
                        
                    # Global Events. Does not matter which window it comes from
                    elif app_event["page"] == "Global":
                        self.handle_global_event(app_event['event'], app_event["opts"])
            sleep(0.1)
                                    
    def handle_global_event(self, event: str, options: dict):
        if event == "exit":
            if self.menuWinManager:
                self.menuWinManager.kill_window()
            if self.gameWinManager:
                self.gameWinManager.kill_window()
            
            exit()
        elif event == "set_api_key":
            self.try_to_login(options['token'])
        elif event == "change_theme":
            self.set_theme(options['theme'])
            utils.set_theme_dir(options['theme'])            
        elif event == "resize":
            if self.menuWinManager:
                self.menuWinManager.resize()
            if self.gameWinManager:
                self.gameWinManager.resize()
        
    def set_theme(self, theme_dir_name: str):
        utils.set_highlights_from_file(self.neovim_session, self.app_namespace, theme_dir_name)
        self.theme_dir = theme_dir_name
        
    
    def try_to_login(self, token:str = None):
        _token = token or utils.get_api_key(self.config_file_path)
        try:
            _session = berserk.TokenSession(_token)
            _client = Client(_session)
            _account = _client.account.get()
            self.berserk_client = _client
            
            if self.read_incoming_events and self.read_incoming_events.is_alive():
                self.read_incoming_events_stop_flag['stop'] = True

            self.read_incoming_events_stop_flag = { "stop" : False }
            self.read_incoming_events = Thread(
                target=read_incoming_events_stream, 
                args=[self.incoming_events, self.berserk_client, self.lock, self.read_incoming_events_stop_flag],
                daemon=True)
            self.read_incoming_events.start()
        except:
            self.berserk_client = None
        
        
    
            
if __name__ == "__main__":
    main = Main()
    main.run()


