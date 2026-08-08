"""Constants"""

from ._paramstyles import ParamStyle


# DBAPI compliance
apilevel = "2.0"  # pylint: disable=invalid-name
threadsafety = 2  # pylint: disable=invalid-name
paramstyle: ParamStyle = "qmark"  # pylint: disable=invalid-name
