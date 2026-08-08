from base64 import b64encode
from collections.abc import Callable, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping, NamedTuple, cast

from .._utils import classname

from ._exceptions import ProgrammingError
from ._paramstyles import ParamStyle, convert
from ._types import FormatConfig


_DEFAULT_BINDING_CONFIG = FormatConfig()


def raise_if_not_type(value: Any, type_: type | tuple[type]) -> bool:
    if not isinstance(value, type_):
        raise ProgrammingError("Invalid type")
    return True


_ESCAPE_TABLE = [chr(x) for x in range(128)]
_ESCAPE_TABLE[0] = "\\0"
_ESCAPE_TABLE[ord("\\")] = "\\\\"
_ESCAPE_TABLE[ord("\n")] = "\\n"
_ESCAPE_TABLE[ord("\r")] = "\\r"
_ESCAPE_TABLE[ord("\032")] = "\\Z"
_ESCAPE_TABLE[ord('"')] = '\\"'
_ESCAPE_TABLE[ord("'")] = "\\'"


def escape_parameter(parameter: Any, config: FormatConfig) -> str:

    if isinstance(parameter, str):
        return "'%s'" % parameter.translate(_ESCAPE_TABLE)

    if isinstance(parameter, bytes):
        return "'%s'" % b64encode(parameter).decode('ascii')

    elif isinstance(parameter, int):
        return str(parameter)

    elif isinstance(parameter, float):
        s = repr(parameter)
        if s in ("inf", "-inf", "nan"):
            raise ProgrammingError(f"Invalid float: {s}")
        if "e" not in s:
            s += "e0"
        return s

    elif isinstance(parameter, Decimal):
        return str(parameter)

    elif isinstance(parameter, bool):
        return "true" if parameter else "false"

    elif isinstance(parameter, datetime):
        return config.datetime_to_str(parameter)

    elif isinstance(parameter, date):
        return config.date_to_str(parameter)

    elif isinstance(parameter, dict):
        args = ", ".join(
            f"{k} := {escape_parameter(v, config)}"
            for k, v in parameter.items()
            if raise_if_not_type(k, str)
        )
        return f"STRUCT({args})"

    elif isinstance(parameter, Sequence):
        args = ", ".join(
            escape_parameter(v, config)
            for v in parameter
        )
        return f"ARRAY[{args}]"

    raise TypeError(f"Type {classname(parameter)} not supported: {parameter}")


def escape_parameter_sequence(
        parameters: Sequence[Any],
        config: FormatConfig | None
) -> Sequence[str]:
    if config is None:
        config = _DEFAULT_BINDING_CONFIG
    return tuple(
        escape_parameter(parameter, config)
        for parameter in parameters
    )


def escape_parameter_dict(
        parameters: Mapping[str, Any],
        config: FormatConfig | None
) -> dict[str, str]:
    if config is None:
        config = _DEFAULT_BINDING_CONFIG
    values = tuple(
        escape_parameter(parameter, config)
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
