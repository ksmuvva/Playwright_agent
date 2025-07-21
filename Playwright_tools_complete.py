"""Combined Playwright tools.

This module exposes `PlaywrightToolsComplete`, a convenience class that
combines all helpers from `PlaywrightTools` and `PlaywrightAdvancedTools`.
"""

from .Playwright_tools import PlaywrightTools
from .playwright_advanced_newtools import PlaywrightAdvancedTools


class PlaywrightToolsComplete(PlaywrightTools, PlaywrightAdvancedTools):
    """Aggregate of all Playwright automation helpers."""

    def __init__(self):
        PlaywrightTools.__init__(self)
        PlaywrightAdvancedTools.__init__(self, playwright_tools_instance=self)


__all__ = ["PlaywrightToolsComplete"]

