import re
from typing import Any, Callable, Literal, Mapping, Sequence

from ._types import ParamStyle


type Parameters = Sequence[Any] | Mapping[str, Any]

type ParamCategory = Literal['all', 'sequence', 'dict', 'token']

PARAMSTYLES: dict[ParamCategory, tuple[ParamStyle, ...]] = {
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

VALID_QUOTE_CHARS = ['"', "'"]  # " or '
VALID_ESCAPE_CHARS = ['\\']

PLACEHOLDER_TOKENS: dict[ParamStyle, str] = {
    'qmark': '?',
    'format': '%s',
}


PLACEHOLDER_EXPS: dict[ParamStyle, re.Pattern[str]] = {
    'qmark': re.compile(r'(\?)'),
    'numeric': re.compile(r'(:\d+)'),
    'named': re.compile(r'(:\w+)'),
    'format': re.compile(r'(%s)'),
    'pyformat': re.compile(r'(%\(\w+\)s)'),
}


PARAM_TYPES: dict[ParamStyle, Callable[[], list[Any] | dict[str, Any]]] = {
    'qmark': lambda: list(),
    'numeric': lambda: list(),
    'named': lambda: dict(),
    'format': lambda: list(),
    'pyformat': lambda: dict(),
}


def param_add(param_num: int, param_name: str, param: str, params: list[Any] | dict[str, Any]) -> list[Any] | dict[str, Any]:
    if isinstance(params, list):
        params.append(param)
    else:
        params[param_name] = param
    return params


PARAMNAME_EXPS: dict[ParamStyle, re.Pattern[str]] = {
    'named': re.compile(r':(\w+)'),
    'pyformat': re.compile(r'%\((\w+)\)s'),
}


##
# Parameter name generators.
##
PARAMNAME_GENS: dict[ParamStyle, Callable[[int, str], str]] = {
    'qmark': lambda param_num, placeholder: 'param%d' % (param_num),
    'numeric': lambda param_num, placeholder: 'param%d' % (param_num),
    'named': lambda param_num, placeholder: PARAMNAME_EXPS['named'].findall(placeholder)[0],
    'format': lambda param_num, placeholder: 'param%d' % (param_num),
    'pyformat': lambda param_num, placeholder: PARAMNAME_EXPS['pyformat'].findall(placeholder)[0],
}


def param_by_index(param_num: int, param_name: str, params: Sequence[Any] | Mapping[str, Any]) -> Any:
    assert isinstance(params, Sequence)
    return params[param_num - 1]


def param_by_name(param_num: int, param_name: str, params: Sequence[Any] | Mapping[str, Any]) -> Any:
    assert isinstance(params, Mapping)
    return params[param_name]


##
# Parameter value generators.
##
PARAMVALUE_GENS: dict[ParamStyle, Callable[[int, str, Parameters], Any]] = {
    'qmark': param_by_index,
    'numeric': param_by_index,
    'named': param_by_name,
    'format': param_by_index,
    'pyformat': param_by_name,
}


##
# This dictionary contains lambda functions that return the appropriate replacement
# string given the parameter's sequence number.
##
PLACEHOLDER_SUBS: dict[ParamStyle, Callable[[int, str], str]] = {
    'qmark': lambda param_num, param_name: '?',
    'numeric': lambda param_num, param_name: ':%d' % (param_num),
    'named': lambda param_num, param_name: ':%s' % (param_name),
    'format': lambda param_num, param_name: '%s',
    'pyformat': lambda param_num, param_name: '%%(%s)s' % (param_name),
}


##
# The following conversion matrix was inspired by similar code in Wichert Akkerman's dhm
# module at http://www.wiggy.net/code/python-dhm.
##
# The primary reason for listing conversion algorithms in a lookup table like this is that
# it allows for individual conversions to be overridden as additional, possibly experimental,
# algorithms are developed without breaking the functionality of the entire module.
##
CONVERSION_MATRIX: dict[ParamStyle, dict[ParamStyle, Callable[[str, Parameters], tuple[str, Parameters]]]] = {
    'qmark': {
        'qmark': lambda query, params: (query, params),
        'numeric': lambda query, params: paramstyle_to_paramstyle('qmark', 'numeric', query, params),
        'named': lambda query, params: paramstyle_to_paramstyle('qmark', 'named', query, params),
        'format': lambda query, params: paramstyle_to_paramstyle('qmark', 'format', query, params),
        'pyformat': lambda query, params: paramstyle_to_paramstyle('qmark', 'pyformat', query, params),
    },
    'numeric': {
        'qmark': lambda query, params: paramstyle_to_paramstyle('numeric', 'qmark', query, params),
        'numeric': lambda query, params: (query, params),
        'named': lambda query, params: paramstyle_to_paramstyle('numeric', 'named', query, params),
        'format': lambda query, params: paramstyle_to_paramstyle('numeric', 'format', query, params),
        'pyformat': lambda query, params: paramstyle_to_paramstyle('numeric', 'pyformat', query, params),
    },
    'named': {
        'qmark': lambda query, params: paramstyle_to_paramstyle('named', 'qmark', query, params),
        'numeric': lambda query, params: paramstyle_to_paramstyle('named', 'numeric', query, params),
        'named': lambda query, params: (query, params),
        'format': lambda query, params: paramstyle_to_paramstyle('named', 'format', query, params),
        'pyformat': lambda query, params: paramstyle_to_paramstyle('named', 'pyformat', query, params),
    },
    'format': {
        'qmark': lambda query, params: paramstyle_to_paramstyle('format', 'qmark', query, params),
        'numeric': lambda query, params: paramstyle_to_paramstyle('format', 'numeric', query, params),
        'named': lambda query, params: paramstyle_to_paramstyle('format', 'named', query, params),
        'format': lambda query, params: (query, params),
        'pyformat': lambda query, params: paramstyle_to_paramstyle('format', 'pyformat', query, params),
    },
    'pyformat': {
        'qmark': lambda query, params: paramstyle_to_paramstyle('pyformat', 'qmark', query, params),
        'numeric': lambda query, params: paramstyle_to_paramstyle('pyformat', 'numeric', query, params),
        'named': lambda query, params: paramstyle_to_paramstyle('pyformat', 'named', query, params),
        'format': lambda query, params: paramstyle_to_paramstyle('pyformat', 'format', query, params),
        'pyformat': lambda query, params: (query, params),
    },
}

##
# Return True if the character at pos in string is escaped.
##


def escaped(string: str, pos: int) -> bool:
    escape_chars = VALID_ESCAPE_CHARS
    count = 0
    if pos > 0:
        pos -= 1
        if string[pos] in escape_chars:
            escape_char = string[pos]
            while string[pos] == escape_char and pos >= 0:
                count += 1
                pos -= 1
    if count % 2 == 1:
        return True
    else:
        return False

##
# Return True if the string is quoted.
##


def quoted(string: str) -> bool:
    if string[0] in VALID_QUOTE_CHARS and string[-1] == string[0]:
        return True
    else:
        return False

##
##
##


class SegmentizeError(Exception):
    """
    Error associated with string segmentization.
    """


##
# Parse a string into quoted and non-quoted segments.  We do this so that it is easy to tell
# which segments of a string to look for placeholders in and which to ignore.
##
def segmentize(string: str) -> list[str]:
    """
    Split a string into quoted and non-quoted segments.
    """
    quote_chars = VALID_QUOTE_CHARS
    segments: list[str] = []
    current_segment = ''
    previous_char: str | None = None
    quote_char: str | None = None
    quoted = False
    pos = 0
    for char in string:
        if quoted:
            if char == quote_char and not escaped(string, pos):
                current_segment += char
                segments.append(current_segment)
                current_segment = ''
                previous_char = char
                quoted = False
            else:
                current_segment += char
                previous_char = char
        elif not quoted:
            if char in quote_chars and not escaped(string, pos):
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
        raise SegmentizeError('Unmatched quotes in string')

    return segments


##
# Universal paramstyle converter.  This is the initial conversion algorithm supplied with PyDAL.
# It is intended to complete, but may not offer optimal performance in all cases.
##
# --PLB 2004-09-08
##
def paramstyle_to_paramstyle(
        from_paramstyle: ParamStyle,
        to_paramstyle: ParamStyle,
        query: str,
        params: Parameters
) -> tuple[str, list[Any] | dict[str, Any]]:
    placeholder_exp = PLACEHOLDER_EXPS[from_paramstyle]
    placeholder_sub = PLACEHOLDER_SUBS[to_paramstyle]
    paramname_gen = PARAMNAME_GENS[from_paramstyle]
    paramvalue_gen = PARAMVALUE_GENS[from_paramstyle]
    new_query = ''
    segments = segmentize(query)
    new_params = PARAM_TYPES[to_paramstyle]()
    param_num = 0
    for segment in segments:
        #
        # If the segment is a quoted string, do not check for placeholders.
        #
        if quoted(segment):
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
                    if escaped(segment, match.start()):
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
                        new_params = param_add(
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


##
# Convert from any paramstyle to any other paramstyle.
##
def convert(
        from_paramstyle: ParamStyle,
        to_paramstyle: ParamStyle,
        query: str,
        params: Parameters
) -> tuple[str, Parameters]:

    try:
        convert_function = CONVERSION_MATRIX[from_paramstyle][to_paramstyle]
    except KeyError:
        raise NotImplementedError(
            f'Unsupported paramstyle conversion: {from_paramstyle} to {to_paramstyle}'
        )

    new_query, new_params = convert_function(query, params)

    return new_query, new_params


##
# Unit Tests
##
# Need to move these to the python unit testing framework...
##
if __name__ == '__main__':
    sequence_params = ['a', 'b', 'c', 'd']
    dict_params = {
        'foo': 'a',
        'bar': 'b',
        'baz': 'c',
        'quux': 'd',
    }
    tests: dict[ParamStyle, tuple[str, Parameters]] = {
        'qmark': ('SELECT * FROM ? WHERE ? > ? OR ? IS NOT NULL', sequence_params),
        'numeric': ('SELECT * FROM :1 WHERE :2 > :3 OR :4 IS NOT NULL', sequence_params),
        'named': ('SELECT * FROM :foo WHERE :bar > :baz OR :quux IS NOT NULL', dict_params),
        'format': ('SELECT * FROM %s WHERE %s > %s OR %s IS NOT NULL', sequence_params),
        'pyformat': ('SELECT * FROM %(foo)s WHERE %(bar)s > %(baz)s OR %(quux)s IS NOT NULL', dict_params),
    }
    indent = 4
    width = 16
    print('')
    print('[ PARAMSTYLE TRANSLATIONS ]')
    print('')
    for from_paramstyle in PARAMSTYLES['all']:
        query = tests[from_paramstyle][0]
        params = tests[from_paramstyle][1]
        print('')
        print('%s[ %s ]' % (' ' * indent, from_paramstyle.upper()))
        print('')
        label = 'query'
        print('%s%s%s: %s' % (' ' * indent, label, '.' *
              (width + indent - len(label)), query))
        label = 'paramstyle'
        print('%s%s%s: %s' % (' ' * indent, label, '.' *
              (width + indent - len(label)), from_paramstyle))
        print('')
        for to_paramstyle in PARAMSTYLES['all']:
            converted_query, converted_params = convert(
                from_paramstyle, to_paramstyle, query, params)
            label = '%s_query' % (to_paramstyle)
            print('%s%s%s: %s' % (' ' * indent * 2, label,
                  '.' * (width - len(label)), converted_query))
            label = '%s_params' % (to_paramstyle)
            print('%s%s%s: %s' % (' ' * indent * 2, label,
                  '.' * (width - len(label)), converted_params))
        print('')
