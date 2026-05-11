"""Tests for server context."""

import pytest

from imgsvc.config import Config
from imgsvc.context import ServerContext, RequestContext
from imgsvc.engines.pil_engine import PilEngine
from imgsvc.loaders.http_loader import HttpLoader
from imgsvc.storage.file_storage import FileStorage
from imgsvc.filters import FilterFactory


class TestServerContext:
    """Tests for ServerContext."""

    def test_create_with_config(self):
        config = Config()
        ctx = ServerContext(config)
        assert ctx.config is config

    def test_engine_class_import(self):
        config = Config()
        ctx = ServerContext(config)
        assert ctx.engine_class is PilEngine

    def test_create_engine(self):
        config = Config()
        ctx = ServerContext(config)
        engine = ctx.create_engine()
        assert isinstance(engine, PilEngine)

    def test_create_multiple_engines(self):
        config = Config()
        ctx = ServerContext(config)
        engine1 = ctx.create_engine()
        engine2 = ctx.create_engine()
        assert engine1 is not engine2

    def test_loader_default(self):
        config = Config()
        ctx = ServerContext(config)
        assert isinstance(ctx.loader, HttpLoader)

    def test_loader_cached(self):
        config = Config()
        ctx = ServerContext(config)
        loader1 = ctx.loader
        loader2 = ctx.loader
        assert loader1 is loader2

    def test_storage_default(self):
        config = Config()
        ctx = ServerContext(config)
        assert isinstance(ctx.storage, FileStorage)

    def test_storage_cached(self):
        config = Config()
        ctx = ServerContext(config)
        storage1 = ctx.storage
        storage2 = ctx.storage
        assert storage1 is storage2

    def test_filter_factory(self):
        config = Config()
        ctx = ServerContext(config)
        assert isinstance(ctx.filter_factory, FilterFactory)

    def test_filter_factory_cached(self):
        config = Config()
        ctx = ServerContext(config)
        factory1 = ctx.filter_factory
        factory2 = ctx.filter_factory
        assert factory1 is factory2

    def test_import_class(self):
        cls = ServerContext._import_class("imgsvc.engines.pil_engine.PilEngine")
        assert cls is PilEngine


class TestRequestContext:
    """Tests for RequestContext."""

    def test_create_with_server_context(self):
        config = Config(QUALITY=75)
        server = ServerContext(config)
        req = RequestContext(server)

        assert req.server is server
        assert req.config is config
        assert req.quality == 75

    def test_create_engine(self):
        config = Config()
        server = ServerContext(config)
        req = RequestContext(server)

        engine = req.create_engine()
        assert isinstance(engine, PilEngine)
        assert req.engine is engine

    def test_default_format_is_none(self):
        config = Config()
        server = ServerContext(config)
        req = RequestContext(server)
        assert req.format is None

    def test_request_params(self):
        from imgsvc.request_params import RequestParams

        config = Config()
        server = ServerContext(config)
        params = RequestParams(width=300, height=200)
        req = RequestContext(server, request_params=params)

        assert req.request is params
        assert req.request.width == 300
