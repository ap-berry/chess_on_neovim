from pynvim.api import Nvim
import utils
from pynvim import attach


class ErrorWin:
    def __init__(
        self,
        session: Nvim,
        error_msg: str,
    ):
        self.error_text = [" ERROR MESSAGE ", ""]
        self.error_text += [line for line in error_msg.split("\n")]
        self.error_text += ["", "", " OK~"]

        self.session = session

        self.buffer = utils.find_buf(session, "error_buffer") or utils.create_buf(
            session, "error_buffer", False, True
        )

        self.window = utils.find_window_from_title(
            session, "ErrorWindow"
        ) or utils.create_window(
            nvim=session,
            buf=self.buffer,
            enter=True,
            config=utils.config_gen(session, config="error", width=40, height=7),
            title="ErrorWindow",
        )

        self._set_end_line_number()
        utils.noremap_lua_callback(
            self.session,
            "/mnt/Study And Code/project/chess_on_neovim/gui_tests/lua/errorcallback.lua",
            "<CR>",
            "<cmd>lua ErrorWinCallBack()<CR>",
            insertmodeaswell=True,
        )
        self.redraw()

    def _set_end_line_number(self):
        utils.buf_set_var(
            self.session, "end_line_number", len(self.error_text)
        )  # lua has one based indexing!!?1/!?!?/!/f7&k

    def _set_nomodifiable(
        self,
    ):  # should be called after _set_current and as its buffer specific
        self.session.command("setlocal nomodifiable")

    def _set_modifiable(
        self,
    ):  # should be called after _set_current as its buffer specific
        self.session.command("setlocal modifiable")

    def redraw(self):
        self._set_modifiable()
        utils.buf_set_lines(nvim=self.session, buf=self.buffer, text=self.error_text)
        self._set_nomodifiable()
        utils.force_redraw(nvim=self.session)


def test():
    nvim = attach("tcp", "127.0.0.1", 6789)

    errwin = ErrorWin(nvim, "JUDGEMENT\n NEAHHHHHHHHHHHHHHH")
