import re
from typing import Any, Callable, Literal, Mapping, Sequence, cast

type ParamStyle = Literal['qmark', 'numeric', 'named', 'format', 'pyformat']

type Parameters = Sequence[Any] | Mapping[str, Any]

type ParamCategory = Literal['all', 'sequence', 'dict', 'token']

PARAMSTYLES: Mapping[ParamCategory, tuple[ParamStyle, ...]] = {
    'all': (
        'qmark', 'numeric', 'named', 'format', 'pyformat'
    ),
    'sequence': (
        'qmark', 'numeric', 'format'
    ),
    'dict': (
        'named', 'pyformat'
    ),
    'token': (
        'qmark', 'format'
    ),
}

_VALID_QUOTE_CHARS = ['"', "'"]  # " or '
_VALID_ESCAPE_CHARS = ['\\']


_PLACEHOLDER_EXPS: Mapping[ParamStyle, re.Pattern[str]] = {
    'qmark': re.compile(r'(\?)'),
    'numeric': re.compile(r'(:\d+)'),
    'named': re.compile(r'(:\w+)'),
    'format': re.compile(r'(%s)'),
    'pyformat': re.compile(r'(%\(\w+\)s)'),
}


_PARAM_TYPES: Mapping[ParamStyle, Callable[[], list[Any] | dict[str, Any]]] = {
    'qmark': lambda: list(),
    'numeric': lambda: list(),
    'named': lambda: dict(),
    'format': lambda: list(),
    'pyformat': lambda: dict(),
}


def _param_add(
        param_num: int,
        param_name: str,
        param: str,
        params: list[Any] | dict[str, Any]
) -> list[Any] | dict[str, Any]:
    if isinstance(params, list):
        params.append(param)
    else:
        params[param_name] = param

    return params


_PARAMNAME_EXPS: Mapping[ParamStyle, re.Pattern[str]] = {
    'named': re.compile(r':(\w+)'),
    'pyformat': re.compile(r'%\((\w+)\)s'),
}

_PARAMNAME_GENS: Mapping[ParamStyle, Callable[[int, str], str]] = {
    'qmark': lambda param_num, placeholder: f'param{param_num}',
    'numeric': lambda param_num, placeholder: f'param{param_num}',
    'named': lambda param_num, placeholder: _PARAMNAME_EXPS['named'].findall(placeholder)[0],
    'format': lambda param_num, placeholder: f'param{param_num}',
    'pyformat': lambda param_num, placeholder: _PARAMNAME_EXPS['pyformat'].findall(placeholder)[0],
}


def _param_by_index(param_num: int, _param_name: str, params: Parameters) -> Any:
    assert isinstance(params, Sequence)
    return params[param_num - 1]


def _param_by_name(_param_num: int, param_name: str, params: Parameters) -> Any:
    assert isinstance(params, Mapping)
    return params[param_name]


_PARAMVALUE_GENS: Mapping[ParamStyle, Callable[[int, str, Parameters], Any]] = {
    'qmark': _param_by_index,
    'numeric': _param_by_index,
    'named': _param_by_name,
    'format': _param_by_index,
    'pyformat': _param_by_name,
}


_PLACEHOLDER_SUBS: Mapping[ParamStyle, Callable[[int, str], str]] = {
    'qmark': lambda param_num, param_name: '?',
    'numeric': lambda param_num, param_name: ':%d' % (param_num),
    'named': lambda param_num, param_name: ':%s' % (param_name),
    'format': lambda param_num, param_name: '%s',
    'pyformat': lambda param_num, param_name: '%%(%s)s' % (param_name),
}


def _is_escaped(string: str, pos: int) -> bool:
    escape_chars = _VALID_ESCAPE_CHARS
    count = 0
    if pos > 0:
        pos -= 1
        if string[pos] in escape_chars:
            escape_char = string[pos]
            while string[pos] == escape_char and pos >= 0:
                count += 1
                pos -= 1

    return count % 2 == 1


def _is_quoted(string: str) -> bool:
    return string[0] in _VALID_QUOTE_CHARS and string[-1] == string[0]


def _segmentize(string: str) -> list[str]:
    """
    Split a string into quoted and non-quoted segments.
    """
    quote_chars = _VALID_QUOTE_CHARS
    segments: list[str] = []
    current_segment = ''
    previous_char: str | None = None
    quote_char: str | None = None
    quoted = False
    pos = 0
    for char in string:
        if quoted:
            if char == quote_char and not _is_escaped(string, pos):
                current_segment += char
                segments.append(current_segment)
                current_segment = ''
                previous_char = char
                quoted = False
            else:
                current_segment += char
                previous_char = char
        elif not quoted:
            if char in quote_chars and not _is_escaped(string, pos):
                if current_segment != '':
                    segments.append(current_segment)
                    current_segment = ''
                quoted = True
                quote_char = char
                current_segment += char
                previous_char = char
            else:
                current_segment += char
                previous_char = char
        pos += 1
    if current_segment != '':
        segments.append(current_segment)
    if quoted:
        raise ValueError('Unmatched quotes in string')

    return segments


def convert(
        from_paramstyle: ParamStyle,
        to_paramstyle: ParamStyle,
        query: str,
        params: Sequence[Any] | Mapping[str, Any]
) -> tuple[str, Sequence[Any] | Mapping[str, Any]]:
    if from_paramstyle == to_paramstyle:
        return query, params

    placeholder_exp = _PLACEHOLDER_EXPS[from_paramstyle]
    placeholder_sub = _PLACEHOLDER_SUBS[to_paramstyle]
    paramname_gen = _PARAMNAME_GENS[from_paramstyle]
    paramvalue_gen = _PARAMVALUE_GENS[from_paramstyle]
    new_query = ''
    segments = _segmentize(query)
    new_params = _PARAM_TYPES[to_paramstyle]()
    param_num = 0
    for segment in segments:
        #
        # If the segment is a quoted string, do not check for placeholders.
        #
        if _is_quoted(segment):
            new_query += segment
        else:
            #
            # ...otherwise, check for any placeholder matches.
            #
            pos = 0
            match = placeholder_exp.search(segment, pos)
            if match != None:
                #
                # If there are placeholders...
                #
                while match != None:
                    new_query += segment[pos:match.start()]
                    placeholder = segment[match.start():match.end()]
                    #
                    # Ignore the placeholder if it is escaped...
                    #
                    if _is_escaped(segment, match.start()):
                        new_query += placeholder
                    else:
                        #
                        # ...otherwise replace it.
                        #
                        param_num += 1
                        param_name = paramname_gen(param_num, placeholder)
                        param_value = paramvalue_gen(
                            param_num, param_name, params)
                        new_placeholder = placeholder_sub(
                            param_num, param_name)
                        new_query += new_placeholder
                        new_params = _param_add(
                            param_num, param_name, param_value, new_params)
                    pos = match.end()
                    match = placeholder_exp.search(segment, pos)
                #
                # Tack on the end of the string segment when there are no more matches.
                #
                if pos < len(segment):
                    new_query += segment[pos:]
            #
            # If there were no placeholders, just add the segment to our query.
            #
            else:
                new_query += segment

    return new_query, new_params
