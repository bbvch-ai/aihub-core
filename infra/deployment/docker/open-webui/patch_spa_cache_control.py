from pathlib import Path

MAIN_PY = Path('/app/backend/open_webui/main.py')

SPA_STATIC_FILES_ANCHOR = """class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
"""

SPA_STATIC_FILES_WITH_CACHE_CONTROL = """class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await self._get_spa_response(path, scope)
        if not path.startswith('_app/immutable/'):
            response.headers['Cache-Control'] = 'no-cache'
        return response

    async def _get_spa_response(self, path: str, scope):
"""


class SpaCacheControlPatcher:
    """Without Cache-Control, browsers cache OpenWebUI's index.html heuristically for days and keep booting the
    previous frontend after an upgrade; only the content-hashed `_app/immutable/` files may be reused unchecked."""

    @staticmethod
    def patch(main_py: Path) -> None:
        source = main_py.read_text()
        occurrences = source.count(SPA_STATIC_FILES_ANCHOR)
        if occurrences != 1:
            raise SystemExit(f'Expected one SPAStaticFiles.get_response in {main_py}, found {occurrences}')
        main_py.write_text(source.replace(SPA_STATIC_FILES_ANCHOR, SPA_STATIC_FILES_WITH_CACHE_CONTROL))


if __name__ == '__main__':
    SpaCacheControlPatcher.patch(MAIN_PY)
