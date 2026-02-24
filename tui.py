# img2ascii TUI — interactive ASCII art viewer built with Textual

from pathlib import Path
from typing import Iterable

from rich.color import Color
from rich.style import Style
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import var
from textual.widgets import (
    Button,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Select,
    Static,
    Switch,
)

from img2ascii import (
    GSCALE_10,
    GSCALE_70,
    GSCALE_BLOCK,
    convert_image_to_ascii,
    load_image,
    render_html,
    render_image,
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}

PRESET_OPTIONS = [
    ("Custom", "custom"),
    ("HD", "hd"),
    ("Retro", "retro"),
    ("Minimal", "minimal"),
]

PRESET_SETTINGS = {
    "hd":      {"cols": 300, "block": True,  "color": True,  "morelevels": False, "invert": False},
    "retro":   {"cols": 80,  "block": False, "color": False, "morelevels": True,  "invert": False},
    "minimal": {"cols": 60,  "block": False, "color": False, "morelevels": False, "invert": False},
}


class ImageDirectoryTree(DirectoryTree):
    """DirectoryTree filtered to show only image files, no emoji icons."""

    ICON_NODE = "> "
    ICON_NODE_EXPANDED = "v "
    ICON_FILE = "  "

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [
            p for p in paths
            if p.is_dir() or p.suffix.lower() in IMAGE_EXTENSIONS
        ]


class AsciiArtApp(App):
    CSS_PATH = "tui.tcss"
    TITLE = "img2ascii"
    BINDINGS = [
        Binding("f", "toggle_sidebar", "Toggle Sidebar"),
        Binding("e", "export_html", "Export HTML"),
        Binding("p", "export_image", "Export PNG"),
        Binding("q", "quit", "Quit"),
    ]

    show_sidebar = var(True)
    current_file: str | None = None
    _applying_preset = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="app-grid"):
            with Vertical(id="sidebar"):
                yield ImageDirectoryTree("./", id="file-tree")
                with VerticalScroll(id="settings"):
                    yield Label("Settings", id="settings-title")
                    with Horizontal(classes="setting-row"):
                        yield Label("Preset")
                        yield Select(PRESET_OPTIONS, value="custom", id="preset-select", allow_blank=False)
                    with Horizontal(classes="setting-row"):
                        yield Label("Columns")
                        yield Input(value="80", type="integer", id="cols-input")
                    with Horizontal(classes="setting-row"):
                        yield Label("Scale")
                        yield Input(value="0.43", type="number", id="scale-input")
                    with Horizontal(classes="setting-row"):
                        yield Label("Color")
                        yield Switch(value=True, id="color-switch")
                    with Horizontal(classes="setting-row"):
                        yield Label("Block chars")
                        yield Switch(value=False, id="block-switch")
                    with Horizontal(classes="setting-row"):
                        yield Label("More levels")
                        yield Switch(value=False, id="morelevels-switch")
                    with Horizontal(classes="setting-row"):
                        yield Label("Invert")
                        yield Switch(value=False, id="invert-switch")
                    with Horizontal(id="export-row"):
                        yield Button("Export HTML", id="export-html-btn", variant="primary")
                        yield Button("Export PNG", id="export-png-btn", variant="primary")
            with VerticalScroll(id="preview-area"):
                yield Static("Select an image from the file tree", id="placeholder")
                yield RichLog(id="ascii-preview", wrap=False, markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#ascii-preview").display = False

    # --- Sidebar toggle ---

    def watch_show_sidebar(self, value: bool) -> None:
        self.set_class(not value, "-hide-sidebar")

    def action_toggle_sidebar(self) -> None:
        self.show_sidebar = not self.show_sidebar

    # --- File selection ---

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        event.stop()
        self.current_file = str(event.path)
        self.refresh_preview()

    # --- Settings changes ---

    @on(Select.Changed, "#preset-select")
    def preset_changed(self, event: Select.Changed) -> None:
        if event.value == "custom" or event.value is Select.BLANK:
            return
        preset = PRESET_SETTINGS[event.value]
        self._applying_preset = True
        self.query_one("#cols-input", Input).value = str(preset["cols"])
        self.query_one("#color-switch", Switch).value = preset["color"]
        self.query_one("#block-switch", Switch).value = preset["block"]
        self.query_one("#morelevels-switch", Switch).value = preset["morelevels"]
        self.query_one("#invert-switch", Switch).value = preset["invert"]
        self._applying_preset = False
        self.refresh_preview()

    @on(Input.Changed, "#cols-input")
    @on(Input.Changed, "#scale-input")
    def input_changed(self, event: Input.Changed) -> None:
        if not self._applying_preset:
            self.query_one("#preset-select", Select).value = "custom"
            self.refresh_preview()

    @on(Switch.Changed)
    def switch_changed(self, event: Switch.Changed) -> None:
        if not self._applying_preset:
            self.query_one("#preset-select", Select).value = "custom"
            self.refresh_preview()

    # --- Export buttons ---

    @on(Button.Pressed, "#export-html-btn")
    def export_html(self, event: Button.Pressed) -> None:
        self.action_export_html()

    @on(Button.Pressed, "#export-png-btn")
    def export_png(self, event: Button.Pressed) -> None:
        self.action_export_image()

    def action_export_html(self) -> None:
        if not self.current_file:
            self.notify("No image loaded", severity="warning")
            return
        rows = self._convert()
        if rows is None:
            return
        html_path = str(Path(self.current_file).with_suffix(".html"))
        render_html(rows, html_path)
        self.notify(f"HTML exported to {html_path}")

    def action_export_image(self) -> None:
        if not self.current_file:
            self.notify("No image loaded", severity="warning")
            return
        rows = self._convert()
        if rows is None:
            return
        img_path = str(Path(self.current_file).with_suffix(".png"))
        render_image(rows, img_path)
        self.notify(f"PNG exported to {img_path}")

    # --- Preview rendering ---

    def _get_settings(self) -> dict | None:
        try:
            cols = int(self.query_one("#cols-input", Input).value)
        except (ValueError, TypeError):
            return None
        try:
            scale = float(self.query_one("#scale-input", Input).value)
        except (ValueError, TypeError):
            return None
        if cols < 10 or scale <= 0:
            return None
        return {
            "cols": cols,
            "scale": scale,
            "color": self.query_one("#color-switch", Switch).value,
            "block": self.query_one("#block-switch", Switch).value,
            "morelevels": self.query_one("#morelevels-switch", Switch).value,
            "invert": self.query_one("#invert-switch", Switch).value,
        }

    def _get_ramp(self, settings: dict) -> str:
        if settings["block"]:
            ramp = GSCALE_BLOCK
        elif settings["morelevels"]:
            ramp = GSCALE_70
        else:
            ramp = GSCALE_10
        if settings["invert"]:
            ramp = ramp[::-1]
        return ramp

    def _convert(self) -> list | None:
        if not self.current_file:
            return None
        settings = self._get_settings()
        if settings is None:
            return None
        ramp = self._get_ramp(settings)
        try:
            image = load_image(self.current_file)
            return convert_image_to_ascii(image, settings["cols"], settings["scale"], ramp)
        except Exception:
            return None

    def refresh_preview(self) -> None:
        if self.current_file:
            self._do_refresh()

    @work(thread=True)
    def _do_refresh(self) -> None:
        settings = self._get_settings()
        if settings is None:
            return
        ramp = self._get_ramp(settings)
        try:
            image = load_image(self.current_file)
            rows = convert_image_to_ascii(image, settings["cols"], settings["scale"], ramp)
        except Exception:
            self.app.call_from_thread(self._show_error, "Failed to convert image")
            return
        use_color = settings["color"]
        lines: list[Text] = []
        for row in rows:
            line = Text()
            for ch, (r, g, b) in row:
                if use_color:
                    line.append(ch, style=Style(color=Color.from_rgb(r, g, b)))
                else:
                    line.append(ch)
            lines.append(line)
        self.app.call_from_thread(self._update_preview, lines)

    def _show_error(self, msg: str) -> None:
        self.notify(msg, severity="error")

    def _update_preview(self, lines: list[Text]) -> None:
        placeholder = self.query_one("#placeholder")
        preview = self.query_one("#ascii-preview", RichLog)
        placeholder.display = False
        preview.display = True
        preview.clear()
        for line in lines:
            preview.write(line)


def run() -> None:
    app = AsciiArtApp()
    app.run()


if __name__ == "__main__":
    run()
