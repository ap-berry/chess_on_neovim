from time import sleep
from pynvim import Nvim, attach
from pynvim.api import Window
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
        relative_to_win: Window,
        window_config: Optional[dict] = None,
    ):
        self.session = session
        self.namespace = self.session.api.create_namespace("info_namespace")
        self.window_namespace = utils.namespace(self.session, "InputWinNS")
        self.buffer = utils.find_buf(session, "input_buffer") or utils.create_buf(
            session, "input_buffer"
        )
        self.buffer[:] = [" "]
        self.sign_text = "> "
        self.sign_text_hl_group = "SpellRare"
        self.window = utils.find_window_from_title(
            session, "InputWindow"
        ) or utils.create_window(
            session,
            self.buffer,
            True,
            window_config
            or utils.config_gen(session, config="input", win=relative_to_win),
            "InputWindow",
        )

        self._set_extmarks()
        self._set_buffer_keymaps()
        self._set_window_highlights()

    def _set_window_highlights(self):
        self.session.api.win_set_hl_ns(self.window, self.window_namespace)
        self.session.api.set_hl(
            self.window_namespace,
            "NormalFloat",
            {"ctermbg": "Black", "ctermfg": "White"},
        )

    def _set_extmarks(self):
        # self.session.command("highlight InputWinHelpText guifg=Blue guibg=Red")
        extmark_opts = utils.ExtmarksOptions(
            end_row=0,
            end_col=0,
            sign_text=self.sign_text,
            sign_hl_group=self.sign_text_hl_group,
            id=1,
        )
        utils.buf_set_extmark(
            nvim=self.session,
            buffer=self.buffer,
            ns_id=self.namespace,
            line=0,
            col=0,
            opts=extmark_opts,
        )

    def _set_buffer_keymaps(self):
        utils.noremap_lua_callback(
            self.session,
            "./gui_tests/lua/inputWinCallback.lua",
            "<CR>",
            "<cmd>lua inputWinCallback()<CR>",
            insertmodeaswell=True,
        )

    def empty(self):
        utils.buf_set_lines(nvim=self.session, buf=self.buffer, text=[""])
        utils.force_redraw(nvim=self.session)

    def destory(self):
        utils.win_del_force(self.session, self.window)
        utils.buf_del_force(self.session, self.buffer)
