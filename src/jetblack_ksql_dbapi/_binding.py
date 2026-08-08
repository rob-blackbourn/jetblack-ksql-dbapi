"""Code for binding parameters to queries.

All paramstyles are supported.

| paramstyle | Description                                               |
| ---------- | --------------------------------------------------------- |
| qmark      | Question mark style, e.g. ...WHERE name=?                 |
| numeric.   | Numeric, positional style, e.g. ...WHERE name=:1          |
| named.     | Named style, e.g. ...WHERE name=:name                     |
| format.    | ANSI C printf format codes, e.g. ...WHERE name=%s         |
| pyformat.  | Python extended format codes, e.g. ...WHERE name=%(name)s |
"""

from collections.abc import Sequence
from typing import Any, Mapping, NamedTuple, cast

from ._exceptions import ProgrammingError
from ._paramstyles import ParamStyle, convert
from ._types import FormatConfig, to_sql


class BindConfig(NamedTuple):
    paramstyle: ParamStyle
    format_config: FormatConfig


_DEFAULT_FORMAT_CONFIG = BindConfig('qmark', FormatConfig())


def _escape_parameter_sequence(
        parameters: Sequence[Any],
        config: FormatConfig
) -> Sequence[str]:
    return tuple(
        to_sql(parameter, config)
        for parameter in parameters
    )


def _escape_parameter_dict(
        parameters: Mapping[str, Any],
        config: FormatConfig
) -> dict[str, str]:
    values = tuple(
        to_sql(parameter, config)
        for parameter in parameters.values()
    )
    return dict(zip(parameters.keys(), values))


def _bind_parameters_sequence(
        query: str,
        params: Sequence[Any],
        config: BindConfig
) -> str:
    match config.paramstyle:

        case "qmark":
            query, params = cast(
                tuple[str, Sequence[Any]],
                convert('qmark', 'format', query, params)
            )

        case 'format':
            pass

        case _:
            raise ProgrammingError(f"Invalid param style {config.paramstyle}")

    escaped_params = _escape_parameter_sequence(params, config.format_config)

    return query % escaped_params


def _bind_parameters_dict(
        query: str,
        params: Mapping[str, Any],
        config: BindConfig
) -> str:
    match config.paramstyle:

        case 'numeric' | 'named':
            query, params = cast(
                tuple[str, Mapping[str, Any]],
                convert(config.paramstyle, 'pyformat', query, params)
            )

        case 'pyformat':
            pass

        case _:
            raise ProgrammingError(f"Invalid param style {config.paramstyle}")

    escaped_params = _escape_parameter_dict(params, config.format_config)

    return query % escaped_params


def bind(
        query: str,
        params: Sequence[Any] | Mapping[str, Any] | None,
        config: BindConfig
) -> str:
    """Bind parameters to query.

    Args:
        query (str): The query.
        params (Sequence[Any] | Mapping[str, Any] | None): The parameters to bind.
        config (BindConfig): Bind configuration.

    Returns:
        str: The query with the parameter markers replaced wit the parameters.
    """
    if params is None:
        return query
    elif isinstance(params, Sequence):
        return _bind_parameters_sequence(query, params, config)
    else:
        return _bind_parameters_dict(query, params, config)
