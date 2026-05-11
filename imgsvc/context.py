"""Server context for managing shared resources."""

import importlib


class ServerContext:
    """
    Central context holding shared server resources.

    Provides access to configuration, image engine, loaders,
    storage, and filter factory.
    """

    def __init__(self, config):
        """
        Initialize the server context.

        Args:
            config: Config instance
        """
        self.config = config
        self._engine_class = None
        self._loader = None
        self._storage = None
        self._filter_factory = None

    @property
    def engine_class(self):
        """Get the image engine class."""
        if self._engine_class is None:
            self._engine_class = self._import_class(self.config.ENGINE)
        return self._engine_class

    def create_engine(self):
        """Create a new engine instance."""
        return self.engine_class()

    @property
    def loader(self):
        """Get the image loader."""
        if self._loader is None:
            loader_class = self._import_class(self.config.LOADER)
            self._loader = loader_class(context=self)
        return self._loader

    @property
    def storage(self):
        """Get the storage backend."""
        if self._storage is None:
            storage_class = self._import_class(self.config.STORAGE)
            self._storage = storage_class(context=self)
        return self._storage

    @property
    def filter_factory(self):
        """Get the filter factory."""
        if self._filter_factory is None:
            self._filter_factory = self._create_filter_factory()
        return self._filter_factory

    def _create_filter_factory(self):
        """Create filter factory with all available filters."""
        from imgsvc.filters import FilterFactory
        from imgsvc.filters.blur import BlurFilter
        from imgsvc.filters.brightness import BrightnessFilter
        from imgsvc.filters.contrast import ContrastFilter
        from imgsvc.filters.grayscale import GrayscaleFilter
        from imgsvc.filters.quality import QualityFilter
        from imgsvc.filters.rotate import RotateFilter
        from imgsvc.filters.format import FormatFilter

        filter_classes = [
            BlurFilter,
            BrightnessFilter,
            ContrastFilter,
            GrayscaleFilter,
            QualityFilter,
            RotateFilter,
            FormatFilter,
        ]

        return FilterFactory(filter_classes)

    @staticmethod
    def _import_class(dotted_path):
        """
        Import a class from a dotted path.

        Args:
            dotted_path: Full path like 'module.submodule.ClassName'

        Returns:
            The imported class
        """
        module_path, class_name = dotted_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)


class RequestContext:
    """
    Per-request context holding request-specific state.

    Created for each incoming request to track state like
    output quality and format preferences.
    """

    def __init__(self, server_context, request_params=None):
        """
        Initialize request context.

        Args:
            server_context: ServerContext instance
            request_params: RequestParams from URL parsing
        """
        self.server = server_context
        self.config = server_context.config
        self.request = request_params
        self.engine = None

        self.quality = self.config.QUALITY
        self.format = None

    def create_engine(self):
        """Create an engine for this request."""
        self.engine = self.server.create_engine()
        return self.engine
