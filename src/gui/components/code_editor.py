"""
PyRestForge - Syntax Highlighted Code Editor with Line Numbers
"""

from typing import Optional
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QTextCharFormat, QTextCursor, QTextFormat
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QTextEdit, QPlainTextEdit, QVBoxLayout, QWidget

from src.utils.formatters import minify_json, pretty_print_json, pretty_print_xml
from src.utils.syntax_highlighter import PygmentsSyntaxHighlighter
from src.gui.theme import ThemeColors


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Rich Code Editor with line numbers and syntax highlighting."""

    def __init__(self, parent=None, language: str = "json"):
        super().__init__(parent)
        self.language = language

        # Font configuration
        font = QFont("JetBrains Mono", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setTabStopDistance(24)

        self.line_number_area = LineNumberArea(self)
        self.highlighter = PygmentsSyntaxHighlighter(self.document(), language=language)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def set_language(self, language: str) -> None:
        self.language = language
        self.highlighter.set_language(language)

    def line_number_area_width(self) -> int:
        digits = 1
        max_val = max(1, self.blockCount())
        while max_val >= 10:
            max_val //= 10
            digits += 1
        space = 14 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self) -> None:
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(ThemeColors.BG_HOVER)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(ThemeColors.BG_PANEL))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        painter.setFont(self.font())
        painter.setPen(QColor(ThemeColors.TEXT_MUTED))

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def prettify(self) -> None:
        """Auto formats content based on active language."""
        text = self.toPlainText()
        if self.language == "json":
            self.setPlainText(pretty_print_json(text))
        elif self.language in ("xml", "html"):
            self.setPlainText(pretty_print_xml(text))

    def minify(self) -> None:
        """Minifies JSON content."""
        if self.language == "json":
            self.setPlainText(minify_json(self.toPlainText()))
