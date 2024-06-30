import utils
from pynvim import Nvim, Window

empty_info = ["Nothing to display yet!", "O_o"]


class InfoWin:
    def __init__(
        self, session: Nvim, relative_to_win: Window, window_config: dict | None = None
    ):
        self.session = session

        self.buffer = utils.find_buf(session, "info_buffer") or utils.create_buf(
            session, "info_buffer"
        )

        self.window = utils.find_window_from_title(
            session, "InfoWindow"
        ) or utils.create_window(
            session,
            self.buffer,
            False,
            window_config
            or utils.config_gen(session, config="info", win=relative_to_win),
            "InfoWindow",
        )

        self.info = empty_info

    def set_info(self, text: list[str]):
        if len(text) > 2:
            raise "info buffer should not be more than 2 lines"
        self.info = text

    def redraw(self):
        utils.buf_set_lines(nvim=self.session, buf=self.buffer, text=self.info)
        utils.force_redraw(nvim=self.session)
