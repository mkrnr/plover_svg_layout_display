from xml.sax.saxutils import escape

from plover import log
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtSvgWidgets import QSvgWidget

from typing import List

from plover_svg_layout_display.svg_parser import SVGParser
from plover_svg_layout_display.qt_utils import load_qt_text


PLACEHOLDER_PATH = ":/svgld/resources/placeholder.svg"

try:
    from plover.i18n import Translator
    _ = Translator("plover_svg_layout_display")
except Exception:
    def _(message: str) -> str:
        return message

# Message box geometry in placeholder.svg viewBox units (0 0 148 105)
MESSAGE_CENTER_X = 74
MESSAGE_CENTER_Y = 49.5
MESSAGE_LINE_HEIGHT = 7
MESSAGE_RECT_TEMPLATE = (
    '<rect x="17" y="{y}" width="114" height="{height}" rx=".5" ry=".5"'
    ' fill="#e9d9f2" stroke="#7109aa" stroke-linecap="round"'
    ' stroke-linejoin="round" stroke-width=".5"/>'
)
MESSAGE_TEXT_TEMPLATE = (
    '<text x="{x}" y="{y}" font-family="sans-serif" font-size="4.6px"'
    ' fill="#7109aa" text-anchor="middle">{line}</text>'
)


def insert_message(svg_text: str, message: str) -> str:
    lines = message.split("\n")
    rect_height = MESSAGE_LINE_HEIGHT * len(lines) + 3.5
    rect_y = MESSAGE_CENTER_Y - rect_height / 2

    markup = [MESSAGE_RECT_TEMPLATE.format(y=rect_y, height=rect_height)]
    for index, line in enumerate(lines):
        markup.append(MESSAGE_TEXT_TEMPLATE.format(
            x=MESSAGE_CENTER_X,
            y=rect_y + 7.25 + MESSAGE_LINE_HEIGHT * index,
            line=escape(line)
        ))

    return svg_text.replace("</svg>", "\n".join(markup) + "\n</svg>")


class LayoutWidget(QSvgWidget):

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setObjectName("layout_widget")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("border:0px; background:transparent;")
        self.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.is_invalid = False
        self.svg_size = None

        self.svg_parser = SVGParser()

    def update_groups(self, group_ids: List[str]) -> None:
        if self.is_invalid:
            svg_str = self.svg_parser.svg_raw
        else:
            svg_str = self.svg_parser.get_svg_content(group_ids)

        self.load(QByteArray(str.encode(svg_str, "utf-8")))
        self.update()

    def load_invalid(self, scale: int = 100) -> None:
        self.load_placeholder(_("Invalid SVG path or file."), scale)

    def load_unconfigured(self, scale: int = 100) -> None:
        self.load_placeholder(_(
            "No layout configured for this system.\n"
            "Click this window, then press Ctrl+S\n"
            "(Cmd+S on macOS) to open settings."
        ), scale)

    def load_placeholder(self, message: str, scale: int) -> None:
        try:
            svg_str = insert_message(load_qt_text(PLACEHOLDER_PATH), message)
            self.svg_parser.load_string(svg_str)
            self.show_svg(svg_str, scale, True)
        except Exception as e:
            log.error("Failed to load placeholder SVG: %s", e, exc_info=True)

    def load_svg(self, path: str, scale: int) -> None:
        if not path.strip():
            self.load_unconfigured(scale)
            return
        try:
            self.svg_parser.load_file(path)
            self.show_svg(self.svg_parser.get_whole_svg(), scale, False)
        except Exception as e:
            log.error("Failed to load SVG from %s: %s", path, e, exc_info=True)
            self.load_invalid(scale)

    def show_svg(self, svg_str: str, scale: int, invalid: bool) -> None:
        self.load(QByteArray(str.encode(svg_str, "utf-8")))

        scale_ratio = scale / 100
        new_size = self.renderer().defaultSize()
        new_size.scale(
            int(new_size.width() * scale_ratio),
            int(new_size.height() * scale_ratio),
            Qt.AspectRatioMode.KeepAspectRatio
        )

        self.resize(new_size)
        self.svg_size = new_size
        self.is_invalid = invalid
