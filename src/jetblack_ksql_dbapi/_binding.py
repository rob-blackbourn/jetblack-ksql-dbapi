from base64 import b64encode
from collections.abc import Sequence
from typing import Any, Mapping, cast

from ._utils import classname

from ._exceptions import ProgrammingError
from ._paramstyles import ParamStyle, convert
from ._types import FormatConfig, to_sql


_DEFAULT_FORMAT_CONFIG = FormatConfig()


def escape_parameter_sequence(
        parameters: Sequence[Any],
        config: FormatConfig | None
) -> Sequence[str]:
    if config is None:
        config = _DEFAULT_FORMAT_CONFIG
    return tuple(
        to_sql(parameter, config)
        for parameter in parameters
    )


def escape_parameter_dict(
        parameters: Mapping[str, Any],
        config: FormatConfig | None
) -> dict[str, str]:
    if config is None:
        config = _DEFAULT_FORMAT_CONFIG
    values = tuple(
        to_sql(parameter, config)
        for parameter in parameters.values()
    )
    return dict(zip(parameters.keys(), values))


def bind_parameters_sequence(
        query: str,
        params: Sequence[Any],
        param_style: ParamStyle,
        config: FormatConfig
) -> str:
    match param_style:

        case "qmark":
            query, params = cast(
                tuple[str, Sequence[Any]],
                convert('qmark', 'format', query, params)
            )

        case 'format':
            pass

        case other:
            raise ProgrammingError(f"Invalid param style {param_style}")

    escaped_params = escape_parameter_sequence(params, config)

    return query % escaped_params


def bind_parameters_dict(
        query: str,
        params: Mapping[str, Any],
        param_style: ParamStyle,
        config: FormatConfig
) -> str:
    match param_style:

        case 'numeric' | 'named':
            query, params = cast(
                tuple[str, Mapping[str, Any]],
                convert(param_style, 'pyformat', query, params)
            )

        case 'pyformat':
            pass

        case _:
            raise ProgrammingError(f"Invalid param style {param_style}")

    escaped_params = escape_parameter_dict(params, config)

    return query % escaped_params


def bind_parameters(
        query: str,
        params: Sequence[Any] | Mapping[str, Any] | None,
        param_style: ParamStyle,
        config: FormatConfig
) -> str:
    if params is None:
        return query
    elif isinstance(params, Sequence):
        return bind_parameters_sequence(query, params, param_style, config)
    else:
        return bind_parameters_dict(query, params, param_style, config)
