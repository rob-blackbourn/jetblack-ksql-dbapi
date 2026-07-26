from base64 import b64encode
from collections.abc import Callable, Sequence
from datetime import date, datetime
from decimal import Decimal
import re
from typing import Any, NamedTuple

from ._exceptions import ProgrammingError
from ._types import ParamStyle
from ._utils import classname


class BindingConfig(NamedTuple):
    format_datetime: Callable[[datetime], str] = datetime.isoformat
    format_date: Callable[[date], str] = date.isoformat


_DEFAULT_BINDING_CONFIG = BindingConfig()


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


def escape_parameter(parameter: Any, config: BindingConfig) -> str:

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
        return config.format_datetime(parameter)

    elif isinstance(parameter, date):
        return config.format_date(parameter)

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
        config: BindingConfig | None
) -> Sequence[str]:
    if config is None:
        config = _DEFAULT_BINDING_CONFIG
    return tuple(
        escape_parameter(parameter, config)
        for parameter in parameters
    )


def escape_parameter_dict(
        parameters: dict[str, Any],
        config: BindingConfig | None
) -> dict[str, str]:
    if config is None:
        config = _DEFAULT_BINDING_CONFIG
    values = tuple(
        escape_parameter(parameter, config)
        for parameter in parameters.values()
    )
    return dict(zip(parameters.keys(), values))


_QMARK_CMP_REGEX = re.compile(r'(is|like|<|<=|=|>=|>)\s*\?', re.IGNORECASE)
_QMARK_BETWEEN_REGEX = re.compile(r'BETWEEN\s*\?\s*AND\s*\?', re.IGNORE_CASE)


def bind_parameters_sequence(
        sql: str,
        parameters: Sequence[Any],
        param_style: ParamStyle
) -> str:
    match param_style:

        case "qmark":
            sql = re.sub(_QMARK_CMP_REGEX, r'\1 %s', sql)
            sql = re.sub(_QMARK_BETWEEN_REGEX, 'BETWEEN %s AND %s')
    return sql


def bind_parameters_dict(
        sql: str,
        parameters: Sequence[Any],
        param_style: ParamStyle
) -> str:
    return sql


def bind_parameters(
        sql: str,
        parameters: Sequence[Any] | dict[str, Any] | None,
        param_style: ParamStyle
) -> str:
    if parameters is None:
        return sql
    elif isinstance(parameters, Sequence):
        args = escape_parameter_sequence(parameters)
    else:
        args = escape_parameter_dict(parameters)
