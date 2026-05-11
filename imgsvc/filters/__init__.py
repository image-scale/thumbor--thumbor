"""Filter system for image transformations."""

import re
from collections import defaultdict


STRIP_QUOTE = re.compile(r"^'(.+)'$")


class ParamTypes:
    """Parameter type definitions for filters."""

    PositiveNumber = {"regex": r"[\d]+", "parse": int}
    PositiveNonZeroNumber = {"regex": r"[\d]*[1-9][\d]*", "parse": int}
    NegativeNumber = {"regex": r"[-][\d]+", "parse": int}
    Number = {"regex": r"[-]?[\d]+", "parse": int}
    DecimalNumber = {
        "regex": r"[-]?(?:(?:[\d]+\.?[\d]*)|(?:[\d]*\.?[\d]+))",
        "parse": float
    }
    Boolean = {
        "regex": r"[Tt]rue|[Ff]alse|1|0",
        "parse": lambda v: v.lower() in ("true", "1")
    }
    String = {
        "regex": r"(?:'.+?')|(?:[^,]+?)",
        "parse": lambda v: STRIP_QUOTE.sub(r"\1", v)
    }


def filter_method(*param_types):
    """
    Decorator to mark a method as a filter method.

    Args:
        *param_types: Parameter type definitions (from ParamTypes)
    """
    def decorator(func):
        def wrapper(self, *args):
            return func(self, *args)

        has_default = [False] * len(param_types)
        if func.__defaults__:
            num_defaults = len(func.__defaults__)
            for i in range(num_defaults):
                has_default[len(param_types) - num_defaults + i] = True

        wrapper.filter_data = {
            "name": func.__name__,
            "params": param_types,
            "has_default": has_default,
        }
        return wrapper
    return decorator


class BaseFilter:
    """Base class for image filters."""

    regex = None
    regex_str = None
    parsers = None
    runnable_method = None

    @classmethod
    def pre_compile(cls):
        """Compile the regex pattern for this filter."""
        methods = [
            m for m in cls.__dict__.values()
            if hasattr(m, "filter_data")
        ]
        if not methods:
            return None

        cls.runnable_method = methods[0]
        filter_data = cls.runnable_method.filter_data
        cls._compile_regex(filter_data)
        return filter_data["name"]

    @classmethod
    def _compile_regex(cls, filter_data):
        """Build regex pattern from parameter types."""
        params = filter_data["params"]
        has_default = filter_data.get("has_default", [])
        regexes = []
        parsers = []

        for i, param in enumerate(params):
            if isinstance(param, dict):
                regex = param["regex"]
                parser = param["parse"]
            else:
                regex = param
                parser = None

            is_optional = i < len(has_default) and has_default[i]

            if i == 0:
                if is_optional:
                    regexes.append(f"(?:\\s*({regex})\\s*)?")
                else:
                    regexes.append(f"\\s*({regex})\\s*")
            else:
                if is_optional:
                    regexes.append(f"(?:,\\s*({regex})\\s*)?")
                else:
                    regexes.append(f",\\s*({regex})\\s*")

            parsers.append(parser)

        cls.parsers = parsers
        cls.regex_str = f"{filter_data['name']}\\({''.join(regexes)}\\)"
        cls.regex = re.compile(cls.regex_str)

    @classmethod
    def init_if_valid(cls, param_string, context):
        """Create a filter instance if the parameter string matches."""
        instance = cls(param_string, context)
        if instance.params is not None:
            return instance
        return None

    def __init__(self, params_string, context=None):
        """
        Initialize filter from parameter string.

        Args:
            params_string: String like "blur(5)" or "brightness(-10)"
            context: Context object with engine and other state
        """
        self.context = context
        self.engine = None
        self.params = None

        if context is not None and hasattr(context, "engine"):
            self.engine = context.engine

        if self.regex:
            match = self.regex.match(params_string)
            if match:
                self.params = [
                    parser(param) if parser else param
                    for parser, param in zip(self.parsers, match.groups())
                    if param is not None
                ]

    def run(self):
        """Execute the filter on the image."""
        if self.params is None or type(self).runnable_method is None:
            return None
        method = type(self).runnable_method
        return method(self, *self.params)


class FilterFactory:
    """Factory for creating filter instances from filter strings."""

    def __init__(self, filter_classes):
        """
        Initialize the factory with available filter classes.

        Args:
            filter_classes: List of filter classes
        """
        self.filter_map = {}
        for cls in filter_classes:
            name = cls.pre_compile()
            if name:
                self.filter_map[name] = cls

    def create_instances(self, filter_string, context):
        """
        Create filter instances from a filter string.

        Args:
            filter_string: String like "blur(5):brightness(-10)"
            context: Context object to pass to filters

        Returns:
            FilterRunner with created filter instances
        """
        instances = []
        if not filter_string:
            return FilterRunner(instances)

        parts = filter_string.split("):")
        for i, part in enumerate(parts):
            if i != len(parts) - 1:
                part = part + ")"

            filter_name = part.split("(")[0]
            cls = self.filter_map.get(filter_name)
            if cls is None:
                continue

            instance = cls.init_if_valid(part, context)
            if instance:
                instances.append(instance)

        return FilterRunner(instances)


class FilterRunner:
    """Runs a list of filter instances."""

    def __init__(self, filter_instances):
        """
        Initialize with filter instances.

        Args:
            filter_instances: List of filter instances
        """
        self.instances = filter_instances

    def run(self, engine):
        """
        Execute all filters on the engine.

        Args:
            engine: Image engine to apply filters to
        """
        results = {}
        for instance in self.instances:
            instance.engine = engine
            result = instance.run()
            if result is not None:
                results[type(instance).__name__] = result
        return results

    def __len__(self):
        return len(self.instances)
