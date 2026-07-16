from __future__ import annotations

import io
import logging
import unittest

from app import main


class OperationalLoggingTests(unittest.TestCase):
    def test_access_logger_forwards_info_to_uvicorn_error_handler(self) -> None:
        access_logger = logging.getLogger("app.access")
        uvicorn_logger = logging.getLogger("uvicorn.error")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)

        access_handlers = list(access_logger.handlers)
        access_level = access_logger.level
        access_propagate = access_logger.propagate
        uvicorn_handlers = list(uvicorn_logger.handlers)
        uvicorn_level = uvicorn_logger.level
        uvicorn_propagate = uvicorn_logger.propagate

        try:
            access_logger.handlers = []
            access_logger.setLevel(logging.NOTSET)
            access_logger.propagate = True
            uvicorn_logger.handlers = [handler]
            uvicorn_logger.setLevel(logging.INFO)
            uvicorn_logger.propagate = False

            configure_logger = getattr(main, "_configure_access_logger", None)
            if configure_logger is not None:
                configure_logger()

            access_logger.info(
                "public_cache_warmup_complete warmed=1 failed=0 duration_ms=1.0 "
                "slowest=GET /api/risk/latest:1.0ms"
            )

            self.assertIn("public_cache_warmup_complete", stream.getvalue())
        finally:
            access_logger.handlers = access_handlers
            access_logger.setLevel(access_level)
            access_logger.propagate = access_propagate
            uvicorn_logger.handlers = uvicorn_handlers
            uvicorn_logger.setLevel(uvicorn_level)
            uvicorn_logger.propagate = uvicorn_propagate
            handler.close()

    def test_access_logger_uses_uvicorn_parent_handler_when_error_logger_propagates(self) -> None:
        access_logger = logging.getLogger("app.access")
        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_error_logger = logging.getLogger("uvicorn.error")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)

        access_handlers = list(access_logger.handlers)
        access_level = access_logger.level
        access_propagate = access_logger.propagate
        uvicorn_handlers = list(uvicorn_logger.handlers)
        uvicorn_level = uvicorn_logger.level
        uvicorn_propagate = uvicorn_logger.propagate
        uvicorn_error_handlers = list(uvicorn_error_logger.handlers)
        uvicorn_error_level = uvicorn_error_logger.level
        uvicorn_error_propagate = uvicorn_error_logger.propagate

        try:
            access_logger.handlers = []
            access_logger.setLevel(logging.NOTSET)
            access_logger.propagate = True
            uvicorn_logger.handlers = [handler]
            uvicorn_logger.setLevel(logging.INFO)
            uvicorn_logger.propagate = False
            uvicorn_error_logger.handlers = []
            uvicorn_error_logger.setLevel(logging.INFO)
            uvicorn_error_logger.propagate = True

            main._configure_access_logger()
            access_logger.info("api_request method=GET path=/api/risk/latest status=200")

            self.assertIn("api_request method=GET", stream.getvalue())
        finally:
            access_logger.handlers = access_handlers
            access_logger.setLevel(access_level)
            access_logger.propagate = access_propagate
            uvicorn_logger.handlers = uvicorn_handlers
            uvicorn_logger.setLevel(uvicorn_level)
            uvicorn_logger.propagate = uvicorn_propagate
            uvicorn_error_logger.handlers = uvicorn_error_handlers
            uvicorn_error_logger.setLevel(uvicorn_error_level)
            uvicorn_error_logger.propagate = uvicorn_error_propagate
            handler.close()

    def test_access_logger_preserves_propagation_without_uvicorn_handlers(self) -> None:
        access_logger = logging.getLogger("app.access")
        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_error_logger = logging.getLogger("uvicorn.error")

        access_handlers = list(access_logger.handlers)
        access_level = access_logger.level
        access_propagate = access_logger.propagate
        uvicorn_handlers = list(uvicorn_logger.handlers)
        uvicorn_level = uvicorn_logger.level
        uvicorn_propagate = uvicorn_logger.propagate
        uvicorn_error_handlers = list(uvicorn_error_logger.handlers)
        uvicorn_error_level = uvicorn_error_logger.level
        uvicorn_error_propagate = uvicorn_error_logger.propagate

        try:
            access_logger.handlers = []
            access_logger.setLevel(logging.NOTSET)
            access_logger.propagate = True
            uvicorn_logger.handlers = []
            uvicorn_logger.setLevel(logging.INFO)
            uvicorn_logger.propagate = False
            uvicorn_error_logger.handlers = []
            uvicorn_error_logger.setLevel(logging.INFO)
            uvicorn_error_logger.propagate = False

            main._configure_access_logger()

            self.assertEqual(access_logger.handlers, [])
            self.assertTrue(access_logger.propagate)
            self.assertEqual(access_logger.level, logging.INFO)
        finally:
            access_logger.handlers = access_handlers
            access_logger.setLevel(access_level)
            access_logger.propagate = access_propagate
            uvicorn_logger.handlers = uvicorn_handlers
            uvicorn_logger.setLevel(uvicorn_level)
            uvicorn_logger.propagate = uvicorn_propagate
            uvicorn_error_logger.handlers = uvicorn_error_handlers
            uvicorn_error_logger.setLevel(uvicorn_error_level)
            uvicorn_error_logger.propagate = uvicorn_error_propagate

    def test_access_logger_configuration_is_idempotent_for_same_handler(self) -> None:
        access_logger = logging.getLogger("app.access")
        uvicorn_logger = logging.getLogger("uvicorn.error")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)

        access_handlers = list(access_logger.handlers)
        access_level = access_logger.level
        access_propagate = access_logger.propagate
        uvicorn_handlers = list(uvicorn_logger.handlers)
        uvicorn_level = uvicorn_logger.level
        uvicorn_propagate = uvicorn_logger.propagate

        try:
            access_logger.handlers = []
            access_logger.setLevel(logging.NOTSET)
            access_logger.propagate = True
            uvicorn_logger.handlers = [handler]
            uvicorn_logger.setLevel(logging.INFO)
            uvicorn_logger.propagate = False

            main._configure_access_logger()
            main._configure_access_logger()

            self.assertEqual(access_logger.handlers.count(handler), 1)
            self.assertFalse(access_logger.propagate)
        finally:
            access_logger.handlers = access_handlers
            access_logger.setLevel(access_level)
            access_logger.propagate = access_propagate
            uvicorn_logger.handlers = uvicorn_handlers
            uvicorn_logger.setLevel(uvicorn_level)
            uvicorn_logger.propagate = uvicorn_propagate
            handler.close()


class LifespanLoggingTests(unittest.IsolatedAsyncioTestCase):
    async def test_lifespan_configures_access_logger_before_public_cache_warmup(self) -> None:
        events: list[str] = []

        async def connect() -> None:
            events.append("connect")

        def configure_access_logger() -> logging.Logger:
            events.append("configure")
            return logging.getLogger("app.access")

        async def warmup() -> None:
            events.append("warmup")

        async def disconnect() -> None:
            events.append("disconnect")

        patches = {
            "connect": connect,
            "_configure_access_logger": configure_access_logger,
            "warm_public_read_cache_on_startup": warmup,
            "disconnect": disconnect,
        }
        originals = {name: getattr(main, name) for name in patches}
        for name, value in patches.items():
            setattr(main, name, value)
        self.addCleanup(lambda: [setattr(main, name, value) for name, value in originals.items()])

        async with main.lifespan(main.app):
            events.append("yield")

        self.assertEqual(events, ["connect", "configure", "warmup", "yield", "disconnect"])
