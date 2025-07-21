# Playwright Agent

This package provides a collection of Playwright-based automation tools. It includes a core
`PlaywrightTools` class with common browser automation helpers as well as
`PlaywrightAdvancedTools` for more advanced functionality.

The project is intended to be imported as a Python module:

```python
from Playwright_agent import PlaywrightTools, PlaywrightAdvancedTools
```

The tools require Playwright to be installed with the browser binaries:

```bash
pip install playwright
playwright install
```

All modules are designed for asynchronous use with `asyncio`.
