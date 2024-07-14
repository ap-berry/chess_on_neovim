import json
from pynvim import Nvim, attach
from pynvim.api import Buffer, Window
from typing import Literal, Tuple, Optional, Union, TypedDict, NamedTuple
import os

class ExtmarksOptions(TypedDict, total=False):
    id: int
    end_row: int
    end_col: int
    hl_group: str
    hl_eol: bool
    virt_text: list[Tuple[str, str]]
    virt_text_pos: Literal["eol", "overlay", "right_align", "inline"]
    virt_text_win_col: int
    virt_text_hide: bool
    virt_text_repeat_linebreak: bool
    hl_mode: Literal["replace", "combine", "blend"]
    virt_lines: list[list[Tuple[str, str]]]
    virt_lines_above: bool
    virt_lines_leftcol: bool
    right_gravity: bool
    end_right_gravity: bool
    undo_restore: bool
    invalidate: bool
    priority: int
    strict: bool
    sign_text: str
    sign_hl_group: str
    number_hl_group: str
    line_hl_group: str
    cursorline_hl_group: str
    conceal: bool
    spell: bool
    ui_watched: bool
    url: str


def buf_del_extmark(nvim: Nvim, buffer: Buffer, ns_id: int, id: int):
    "returns true if extmark was found, false otherwise"
    return nvim.api.buf_del_extmark(buffer, ns_id, id)


def win_del_force(nvim: Nvim, win: Window):
    nvim.api.win_close(win, True)


def win_is_valid(nvim: Nvim, win: Window):
    return nvim.api.win_is_valid(win)

def win_set_local_winhighlight(nvim: Nvim, win: Window, winhighlight: str):
    """ example usage `win_set_local_winhighlight(nvim, nvim.current.window, "Normal:MyBackground,CursorLine:MyCursorLine")`"""
    nvim.command(f"call win_execute({win.handle}, 'setlocal winhighlight={winhighlight}')")

def buf_set_extmark(
    nvim: Nvim, buffer: Buffer, ns_id: int, line: int, col: int, opts: ExtmarksOptions
):
    """
    line, 0-based inclusive
    col, 0-based inclusive
    end_row, 0-based inclusive,
    end_col, 0-baed exclusive

    returns the extmark id
    """
    return nvim.api.buf_set_extmark(buffer, ns_id, line, col, opts)


def split_list(lst, n):
    """Splits the list `lst` into sublists of `n` elements each."""
    return [lst[i:i + n] for i in range(0, len(lst), n)]

class Highlight(TypedDict):
    hl_group: str
    line: int
    col_start: int
    col_end: int


def buf_add_hl(nvim: Nvim, buffer: Buffer, ns_id: int, hl: list):
    nvim.api.buf_add_highlight(buffer, ns_id, hl[0], hl[1], hl[2], hl[3])


def buf_set_hls(nvim: Nvim, buffer: Buffer, ns_id: int, hls: list):
    for hl in hls:
        buf_add_hl(nvim, buffer, ns_id, hl)


def buf_clear_namespace(
    nvim: Nvim, buffer: Buffer, ns_id: int, start_line: int = 0, end_line: int = -1
):
    nvim.api.buf_clear_namespace(buffer, ns_id, start_line, end_line)


def buf_del_all_extmarks(
    nvim: Nvim, buffer: Optional[Buffer] = 0, ns_id: Optional[int] = -1
):
    extmarks = nvim.api.buf_get_extmarks(buffer, ns_id, [0, 0], [-1, -1], {})
    for extmark in extmarks:
        nvim.api.buf_del_extmark(buffer, ns_id, extmark[0])


def workspace_width(nvim: Nvim) -> int:
    return int(nvim.command_output("echo &columns"))


def workspace_height(nvim: Nvim) -> int:
    return int(nvim.command_output("echo &lines"))


def buf_set_var(nvim: Nvim, key: str, value: any, buffer: Optional[Buffer] = 0):
    """will be applied to current buffer if buffer not specified"""
    nvim.api.buf_set_var(buffer, key, value)


def buf_get_var(nvim: Nvim, key: str, buffer: Optional[Buffer] = 0):
    """will be applied to current buffer if buffer not specified"""
    return nvim.api.buf_get_var(buffer, key)


def message_neovim(nvim: Nvim, message: str):
    nvim.out_write(msg=message + "\n")


def create_buf(
    nvim: Nvim, bufname: str, listed: bool = True, scratch: bool = True
) -> Buffer:
    """Listed by default, scratch buffer by default"""
    buf = nvim.api.create_buf(listed, scratch)
    buf.name = bufname
    return buf


def list_buf_names(nvim: Nvim) -> any:
    return [buf.name for buf in nvim.buffers]


def find_buf(nvim: Nvim, bufname) -> Optional[Buffer]:
    b = nvim.buffers._fetch_buffers()
    for buf in b:
        if buf.name.endswith(bufname):
            return buf
    return None


def buf_set_text(
    nvim: Nvim,
    buf: Union[Buffer, int],
    start_row: int,
    start_col: int,
    end_row: int,
    end_col: int,
    text: list[str],
):
    """{start_row} First line index
    {start_col} Starting column (byte offset) on first line
    {end_row} Last line index, inclusive
    {end_col} Ending column (byte offset) on last line, exclusive"""
    nvim.api.buf_set_text(buf, start_row, start_col, end_row, end_col, text)


def buf_set_lines(
    nvim: Nvim,
    buf: Union[Buffer, int],
    text: list[str],
    start_line: int = 0,
    end_line: int = -1,
    strict_indexing: bool = True,
):
    """clears everything if startline and endline not set
    Strict_indexing is on by default. To change set strict_indexing=False"""
    nvim.api.buf_set_lines(buf, start_line, end_line, strict_indexing, text)


# nvim_buf_set_text({buffer}, {start_row}, {start_col}, {end_row}, {end_col}, {replacement})


def create_window(
    nvim: Nvim, buf: Buffer, enter: bool, config: dict, title: str
) -> Window:
    _w = nvim.api.open_win(buf, enter, config)
    if title:
        window_set_title(nvim, _w, title)

    return _w


def hide_window(nvim: Nvim, window: Window):
    """Closes window, Hides buffer"""
    nvim.api.win_hide(window)


class BadFenError(Exception):
    pass


def config_gen(
    nvim: Nvim,
    win: Optional[Window] = None,
    relative_to: Literal["editor", "win", "cursor", "mouse"] = "editor",
    width: Optional[int] = None,
    height: Optional[int] = None,
    row: Optional[int] = None,
    col: Optional[int] = None,
    z_index: int = 50,
    config: Union[Literal["center", "menu", "board", "info", "error"], dict] = False,
    minimal: bool = False,
    border: Literal["none", "single", "double", "rounded", "solid", "shadow"] = "none",
):
    _config = {
        "border": border,
    }

    if minimal:
        _config["style"] = "minimal"

    if config == "menu":
        _config.update(
            {
                "relative": "editor",
                "width": 34,
                "height": 20,
                "focusable": True,
                "zindex": z_index,
                "border": "rounded"
            }
        )

        _config.update(
            {
                "row": (workspace_height(nvim) - _config["height"]) // 2,
                "col": (workspace_width(nvim) - _config["width"]) // 2,
            }
        )
    elif config == "board":
        _config.update(
            {
                "relative": "editor",
                "width": 8 * 3 + 2 + 2,  # left pad + right pad
                "height": 8 + 1 + 1,
                "focusable": True,
                "zindex": z_index,
                "border": "rounded"                
            }
        )

        _config.update(
            {
                "row": (workspace_height(nvim) - _config["height"]) // 2,
                "col": (workspace_width(nvim) - _config["width"] + 32) // 2,
            }
        )
    elif config == "stats":
        _config.update(
            {
                "relative": "editor",
                "width": 30,
                "height": 11,
                "focusable": True,
                "external": False,
                "zindex": z_index,
                "style": "minimal",
                "border": "rounded"                
                
            }
        )

        _config.update(
            {
                "row": (workspace_height(nvim) - _config["height"]) // 2,
                "col": (workspace_width(nvim) - _config["width"] - 32) // 2,
            }
        )
    elif config == "info":
        _config.update(
            {
                "relative": "win",
                "win": win.handle,
                "width": 58,
                "height": 2,
                "focusable": True,
                "row": 13,
                "col": 0,
                "external": False,
                "zindex": z_index,
                "style": "minimal",
                "border": "rounded",
            }
        )

    elif config == "error":
        _config.update(
            {
                "relative": "editor",
                "width": width,
                "height": height,
                "focusable": True,
                "external": False,
                "zindex": 900,
                "style": "minimal",
                "border": "rounded",
            }
        )

        _config.update(
            {
                "row": (workspace_height(nvim) - _config["height"]) // 2,
                "col": (workspace_width(nvim) - _config["width"]) // 2,
            }
        )
    elif config == "input":
        _config.update(
            {
                "relative": "editor",
                "width": 25,
                "height": 1,
                "focusable": True,
                "external": False,
                "zindex": z_index,
                "style": "minimal",
                "border": "rounded"           
                
            }
        )
        _config.update(
            {
                "row": (workspace_height(nvim) - _config["height"] - 20) // 2,
                "col": (workspace_width(nvim) - _config["width"]) // 2,
            }
        )

    return _config


def set_cursor(nvim: Nvim, win: Window, pos: Tuple[int, int] = (0, 0)):
    nvim.api.win_set_cursor(win, pos)


def window_set_title(nvim: Nvim, win: Window, title: str):
    nvim.api.win_set_var(win, "window_title", title)


def window_get_title(nvim: Nvim, win: Window) -> Optional[str]:
    try:
        return nvim.api.win_get_var(win, "window_title")
    except:
        return None


def window_set_var(nvim: Nvim, win: Window, key: str, value: str):
    nvim.api.win_set_var(win, key, value)


def window_get_var(nvim: Nvim, win: Window, key: str) -> Optional[str]:
    try:
        return nvim.api.win_get_var(win, key)
    except:
        return None


def find_window_from_title(nvim: Nvim, title: str) -> Optional[Window]:
    for w in nvim.windows:
        wt: str = window_get_title(nvim, w)
        if wt == title:
            return w
    return None


def load_lua_file(nvim: Nvim, lua_file_path: str):
    with open(lua_file_path, "r") as luafile:
        lua = luafile.read()
        nvim.exec_lua(lua) 

def buf_set_keymap(nvim: Nvim, lhs: str, rhs: str, silent: bool = True, insertmodeaswell: bool = False):
    mapcommand = "noremap <buffer>"
    mapcommand += lhs
    mapcommand += " "
    mapcommand += rhs
    
    nvim.api.command(mapcommand)

    if insertmodeaswell:
        mapcommand = "i" + mapcommand
        nvim.api.command(mapcommand)


def noremap_lua_callback(
    nvim: Nvim,
    lua_file_path: str,
    lhs: str,
    rhs: str,
    silent: bool = True,
    current_buffer_specific: bool = False,
    insertmodeaswell: bool = False,
):
    with open(lua_file_path, "r") as luafile:
        lua = luafile.read()
        nvim.exec_lua(lua)

        mapcommand = "noremap "

        if current_buffer_specific:
            mapcommand += " <buffer> "

        mapcommand += lhs
        mapcommand += " "
        mapcommand += rhs

        nvim.api.command(mapcommand)

        if insertmodeaswell:
            mapcommand = "i" + mapcommand
            nvim.api.command(mapcommand)


def force_redraw(nvim: Nvim):
    nvim.command("redraw!")


def get_global_var(nvim: Nvim, key: str) -> Optional[any]:
    """do NOT include the g: at the begining of the variable key"""
    try:
        return nvim.api.get_var(key)
    except:
        return None


def set_global_var(nvim: Nvim, key: str, value: any):
    """do NOT include the g: at the begining of the variable key"""
    nvim.api.set_var(key, value)


def add_app_events(nvim: Nvim, events: Union[list[dict], dict]):
    app_events: list = get_global_var(nvim, "app_events")
    if isinstance(events, list):
        for e in events:
            app_events.append(e)
        
        set_global_var(nvim, "app_events", app_events)
    else:
        app_events.append(events)
        set_global_var(nvim, "app_events", app_events)
        
def buf_del_force(nvim: Nvim, buffer: Buffer):
    nvim.api.buf_delete(buffer.handle, {"force": True})


def namespace(nvim: Nvim, ns_name: str):
    """creates or finds a namepsace"""
    return nvim.api.create_namespace(ns_name)

def get_theme_dir(config_file_path = ".config"):
    with open(config_file_path, "r") as file:
        lines = file.readlines()
        for line in lines:
            pairs = line.strip().split("=")
            if pairs[0] == "THEME_DIR":
                return pairs[1].removesuffix("\n").replace("\"", "").replace("\'", "")


def write_api_key(token: str, config_file_path: str = ".config"):
        lines = None
        with open(config_file_path, "r") as file:
            lines = file.readlines()

            
        with open(config_file_path, "w") as file:
            index = 0
            found = False
            for line in lines:
                pairs = line.split("=")
                if pairs[0].strip() == "API_TOKEN":
                    found=True
                    lines[index] = "API_TOKEN=" + token + "\n"
                    file.writelines(lines)
            if not found:
                lines.append(f"API_TOKEN={token}\n")
                
                file.writelines(lines)
                
def set_theme_dir(theme_dir: str, config_file_path: str = ".config"):
        lines = None
        with open(config_file_path, "r") as file:
            lines = file.readlines()

            
        with open(config_file_path, "w") as file:
            index = 0
            found = False
            for line in lines:
                pairs = line.split("=")
                if pairs[0].strip() == "THEME_DIR":
                    found=True
                    lines[index] = "THEME_DIR=\"" + theme_dir + "\"\n"
                    file.writelines(lines)
                index+=1
            if not found:
                lines.append(f"THEME_DIR=\"{theme_dir}\"\n")
                file.writelines(lines)


def write_api_key(token: str, config_file_path: str = ".config"):
        lines = None
        with open(config_file_path, "r") as file:
            lines = file.readlines()

            
        with open(config_file_path, "w") as file:
            index = 0
            found = False
            for line in lines:
                pairs = line.split("=")
                if pairs[0].strip() == "API_TOKEN":
                    found=True
                    lines[index] = "API_TOKEN=\"" + token + "\"\n"
                    file.writelines(lines)
                index+=1
            if not found:
                lines.append(f"API_TOKEN=\"{token}\"\n")
                file.writelines(lines)

def get_api_key(config_file_path = ".config"):
    with open(config_file_path, "r") as file:
        lines = file.readlines()
        for line in lines:
            pairs = line.strip().split("=")
            if pairs[0] == "API_TOKEN":
                return pairs[1].removesuffix("\n").replace("\"", "").replace("\'", "")


class ThemeFileKeyValuePairError(Exception):
    def __init__(self, theme_file_path, key, val):
        self.message = f"Your Theme File : {theme_file_path} Is Corrupted With Wrong Key Value Pair,  '{key}' = '{val}'"
        super().__init__(self.message)

class ThemeFileNotFound(Exception):
    def __init__(self, theme_file_path):
        self.message = f"{theme_file_path} Does Not Exist"
        super().__init__(self.message)

def set_highlights_from_file(nvim: Nvim, hl_ns: int, theme_dir: str, file_name: Optional[str] = ".theme"):
    """Use 0 as highlight namespace for setting to global namespace"""
    theme_file_path = f"./themes/{theme_dir}/{file_name}"
    # nvim.api.win_set_hl_ns(window, window_namespace)
    if not os.path.exists(theme_file_path):
        raise ThemeFileNotFound(theme_file_path)
    
    with open(theme_file_path, "r") as file:
        lines = file.readlines()

        hl_group_name: str = None
        opts: dict = {}

        for l in lines:
            if l.lstrip().startswith("#"):
                continue

            line = l.removesuffix("\n").replace(" ", "")

            if line == "":
                continue

            if line.startswith("[") or line == "{endfile}":
                if hl_group_name:
                    nvim.api.set_hl(
                        hl_ns, hl_group_name, opts
                    )

                hl_group_name = line.replace("[", "").replace("]", "")
                opts = {}

                continue

            key_value = line.split("=")
            if len(key_value) == 2:
                key = key_value[0]
                val = key_value[1]
                _val = val.lower()
                if _val == "true":
                    val = True
                elif _val == "false":
                    val = False
                elif val.isdigit():
                    val = int(val)
                opts[key] = val
            else:
                raise ThemeFileKeyValuePairError(theme_file_path, key, val)

def find_or_create_config_file():
    if not os.path.exists(".config"):
        with open(".config", "a") as configfile:
            configfile.write("THEME_DIR=\"ayu_dark\"")
        
def test():
    nvim = attach("tcp", "127.0.0.1", 6789)
    w = workspace_width(nvim)
    h = workspace_height(nvim)
    print(w, h)


class AppEvent(TypedDict):
    page: Literal["Home", "Game"]
    event: str
    opts: dict