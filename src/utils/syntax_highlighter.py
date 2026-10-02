"""
PyRestForge - Syntax Highlighter for PySide6 using Pygments
"""

from typing import Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from pygments.formatter import Formatter
from pygments.lexers import (
    get_lexer_by_name,
    JsonLexer,
    YamlLexer,
    XmlLexer,
    HtmlLexer,
    PythonLexer,
    JavascriptLexer,
    TextLexer,
)
from pygments.styles import get_style_by_name
from pygments.token import Token


class PygmentsSyntaxHighlighter(QSyntaxHighlighter):
    """Universal syntax highlighter for PySide6 QTextDocument using Pygments."""

    def __init__(self, parent_document, language: str = "json", theme_name: str = "dracula"):
        super().__init__(parent_document)
        self.language = language
        self.lexer = self._get_lexer(language)
        self.formats: Dict[Any, QTextCharFormat] = {}
        self._init_formats()

    def _get_lexer(self, language: str):
        lang = language.lower().strip()
        if lang == "json":
            return JsonLexer()
        elif lang in ("yaml", "yml"):
            return YamlLexer()
        elif lang == "xml":
            return XmlLexer()
        elif lang == "html":
            return HtmlLexer()
        elif lang in ("python", "py"):
            return PythonLexer()
        elif lang in ("javascript", "js"):
            return JavascriptLexer()
        elif lang == "graphql":
            try:
                return get_lexer_by_name("graphql")
            except Exception:
                return TextLexer()
        return TextLexer()

    def set_language(self, language: str) -> None:
        """Dynamically switches active language lexer."""
        self.language = language
        self.lexer = self._get_lexer(language)
        self.rehighlight()

    def _init_formats(self) -> None:
        """Initializes dark theme color palette for syntax tokens."""
        # Curated Dark Theme Colors (Insomnia / Dracula Aesthetic)
        color_map = {
            Token.Keyword: "#FF79C6",            # Pink
            Token.Keyword.Constant: "#BD93F9",   # Purple
            Token.Name: "#F8F8F2",               # White
            Token.Name.Tag: "#FF79C6",           # Pink
            Token.Name.Attribute: "#50FA7B",     # Green
            Token.Name.Variable: "#8BE9FD",      # Cyan
            Token.Name.Builtin: "#8BE9FD",       # Cyan
            Token.Literal.String: "#F1FA8C",     # Yellow
            Token.Literal.String.Double: "#F1FA8C",
            Token.Literal.String.Single: "#F1FA8C",
            Token.Literal.Number: "#BD93F9",     # Purple
            Token.Literal.Number.Integer: "#BD93F9",
            Token.Literal.Number.Float: "#BD93F9",
            Token.Operator: "#FF79C6",           # Pink
            Token.Punctuation: "#F8F8F2",        # White
            Token.Comment: "#6272A4",            # Muted Gray-Blue
            Token.Comment.Single: "#6272A4",
            Token.Comment.Multiline: "#6272A4",
        }

        for token_type, hex_color in color_map.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(hex_color))
            if token_type in (Token.Keyword, Token.Keyword.Constant):
                fmt.setFontWeight(QFont.Weight.Bold)
            self.formats[token_type] = fmt

    def highlightBlock(self, text: str) -> None:
        """Applies syntax highlighting on a block of text using Pygments lexer tokens."""
        if not text or not self.lexer:
            return

        tokens = self.lexer.get_tokens(text)
        current_index = 0

        for token_type, value in tokens:
            length = len(value)
            # Find best matching format by traversing parent token types
            fmt = None
            t = token_type
            while t:
                if t in self.formats:
                    fmt = self.formats[t]
                    break
                t = t.parent

            if fmt:
                self.setFormat(current_index, length, fmt)

            current_index += length
