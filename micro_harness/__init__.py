"""micro-harness: a minimal agent harness.

Importing the package is cheap on purpose: backends (Anthropic, OpenAI, Gemini)
are imported only when they are used, so ``mh --help`` works without any of
the optional SDKs installed.
"""

__version__ = "0.2.0"
