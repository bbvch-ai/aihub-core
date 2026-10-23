class MissingTranslationError(ValueError):
    """The model answered without a usable <translation> block, typically by echoing the instruction back as prose.

    The only failure a translation degrades on: it is a verdict on one generation, so the other locales are still
    worth keeping. Gateway and configuration errors are not, and propagate so the caller sees what to fix.
    """
