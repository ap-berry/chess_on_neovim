from time import sleep
from pynvim import Nvim, attach
import utils
from typing import Optional

""" Input window where you can only have one line of input
    enter key is mapped to a lua callback function from the lua folder
    the callback function appends and input event to a global variable (lua table of tables) called 'g:app_events'
    """


class InputWin:
    def __init__(
        self,
        session: Nvim,
        window_config: Optional[dict] = None,
    ):
        self.neovim_session = session

            
        self.buffer = utils.find_buf(session, "input_buffer") or utils.create_buf(
            session, "input_buffer"
        )
        self.window = utils.find_window_from_title(
            session, "InputWindow"
        ) or utils.create_window(
            session,
            self.buffer,
            True,
            window_config
            or utils.config_gen(session, config="input"),
            "InputWindow",
        )
        self.namespace = self.neovim_session.api.create_namespace("info_namespace")
        utils.win_set_local_winhighlight(self.neovim_session, self.window, "Normal:InputBackground")

            
        self.buffer[:] = [""]
        self.sign_text_hl_group = "Directory"
        self.hl_group_error = "InputWinError"
        self.hl_group_placeholder = "InputWinPlaceHolder"
        self.sign_text = "> "
        self.set_extmarks()
        self._set_buffer_keymaps()
        self.neovim_session.command("startinsert")

    def set_extmarks(
        self,
        text: str = " Type action and Enter",
        hl: str = "InputWinPlaceHolder",
    ):
        # self.session.command("highlight InputWinHelpText guifg=Blue guibg=Red")
        extmark_opts = utils.ExtmarksOptions(
            end_col=0,
            end_row=0,
            sign_text=self.sign_text,
            sign_hl_group=self.sign_text_hl_group,
            spell=False,
            id=1,
            virt_text=[[text, hl]],
            virt_text_pos="overlay",
        )
        utils.buf_set_extmark(
            nvim=self.neovim_session,
            buffer=self.buffer,
            ns_id=self.namespace,
            line=0,
            col=0,
            opts=extmark_opts,
        )

    def _set_buffer_keymaps(self):
        utils.load_lua_file(self.neovim_session, "./gui_tests/lua/inputWinCallback.lua")
        utils.buf_set_keymap(self.neovim_session, "<CR>", "<cmd>lua inputWinCallback()<CR>", insertmodeaswell=True)

    def empty(self):
        utils.buf_set_lines(nvim=self.neovim_session, buf=self.buffer, text=[""])
        utils.force_redraw(nvim=self.neovim_session)

    def kill_window(self):
        utils.win_del_force(self.neovim_session, self.window)
        utils.buf_del_force(self.neovim_session, self.buffer)
    def resize(self):
        self.neovim_session.api.win_set_config(
            self.window,
            {
                "relative": "editor",
                "row": (utils.workspace_height(self.neovim_session) - 1 - 20) // 2,
                "col": (utils.workspace_width(self.neovim_session) - 25) // 2, 
            }
        )

def test():
    nvim = attach("tcp", "127.0.0.1", 6789)
    inputwin = InputWin(nvim, nvim.current.window, theme_dir="themes/ayu_dark/.input")
    while True:
        inputwin.set_highlights_from_file()
        sleep(0.5)
