import asyncio
from lion.logger.exception_logger import log_exception

class BaseTranslator:
    _cache = {}

    def __init__(self, engine):
        self.engine = engine

    def clear_cache(self):
        self._cache = {}

    def sync_translate(self, text, src='en'):
        if not text:
            return text

        if text in self._cache:
            return self._cache[text]

        try:
            translated = self.engine.translate(text, src=src)
            self._cache[text] = translated
            return translated
        except Exception:
            log_exception(f"[Translation Error] Sync mode for '{text}'")
            return text

    async def async_translate(self, text, src='en'):
        return await asyncio.to_thread(self.sync_translate, text, src)


    def sync_translate_many(self, texts, src='en'):
        return [self.sync_translate(text, src) for text in texts]
