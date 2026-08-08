"""Abstract implementations of the DBAPI objects"""

from abc import ABCMeta, abstractmethod
from typing import Any, AsyncIterator, Mapping, Sequence

from .._description import Description


class Cursor(metaclass=ABCMeta):
    """A PEP-294 style cursor class.

    Note: there is no actual specification for an asyncio cursor.
    """

    @property
    @abstractmethod
    def description(self) -> Sequence[Description] | None:
        """A description of the data returned by the last invocation, if any.

        Returns:
            Sequence[Description] | None: A sequence of the column descriptions.
        """

    @property
    @abstractmethod
    def rowcount(self) -> int:
        """The number of rows effected by the last invocation, if known.

        This is currently not supported.

        Returns:
            int: The number of rows, or -1 if not known.
        """

    @abstractmethod
    async def callproc(self, procname: str, parameters: Sequence[Any] | None = None) -> None:
        """Call a stored database procedure with the given name.

        Args:
            procname (str): The procedure name
            parameters (Sequence[Any] | None, optional): The parameters of the procedure. Defaults to None.

        Raises:
            NotSupportedError: The ksql database does not support this.
        """

    @abstractmethod
    async def close(self) -> None:
        """Close a running cursor.

        Raises:
            Error: If the close fails.
        """

    @abstractmethod
    async def execute(
            self,
            query: str,
            params: Sequence[Any] | Mapping[str, Any] | None = None
    ) -> None:
        """Prepare and execute a database operation (query or command).

        Args:
            query (str): The query or command to execute.
            params (Sequence[Any] | Mapping[str, Any] | None, optional):
                Optional parameters to bind to variables. Defaults to None.
        """

    @abstractmethod
    async def executemany(
            self,
            query: str,
            param_seq: Sequence[Sequence[Any]] | Sequence[Mapping[str, Any]]
    ) -> None:
        """Prepare a database operation (query or command) and then execute it
        against all parameter sequences or mappings found in the sequence
        param_seq.

        Args:
            query (str): The command.
            params (Sequence[Sequence[Any]] | Sequence[Mapping[str, Any]]): A sequence of parameters to bind.

        Raises:
            ProgrammingError: If the sequence of parameters are empty, or the
               statement is not a command.
            ValueError: _description_
        """

    @abstractmethod
    async def fetchone(self) -> Sequence[Any] | None:
        """Fetch the next row of a query result set, returning a single sequence, or None when no more data is available.

        Raises:
            Error: If no results are available.

        Returns:
            Sequence[Any]: _description_
        """

    @abstractmethod
    async def fetchmany(self, size: int | None = None) -> Sequence[Sequence[Any]]:
        """Fetch the next set of rows of a query result, returning a sequence of sequences (e.g. a list of tuples). An empty sequence is returned when no more rows are available.

        Args:
            size (int | None, optional): The maximum number of rows to fetch. Defaults to None.

        Raises:
            Error: If no results are available.

        Returns:
            Sequence[Sequence[Any]]: A sequence of rows.
        """

    @abstractmethod
    async def fetchall(self) -> Sequence[Sequence[Any]]:
        """Fetch all (remaining) rows of a query result, returning them as a
        sequence of sequences (e.g. a list of tuples). Note that the cursor's
        arraysize attribute can affect the performance of this operation.

        Raises:
            Error: If there are no results.

        Returns:
            Sequence[Sequence[Any]]: A sequence of the rows.
        """

    @abstractmethod
    async def nextset(self) -> bool | None:
        """This method will make the cursor skip to the next available set,
        discarding any remaining rows from the current set.

        Returns:
            bool | None:  there are no more sets, the method returns None.
                Otherwise, it returns a true value and subsequent calls to the
                fetch() methods will return rows from the next result set.
        """
        return None

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[Sequence[Any]]:
        ...


class Connection(metaclass=ABCMeta):
    """A PEP-294 style connection class.

    Note: there is no actual specification for an asyncio connection.
    """

    @abstractmethod
    def cursor(self) -> Cursor:
        """Return a new Cursor Object using the connection.

        Returns:
            DBAPICursor: The cursor object.
        """

    @abstractmethod
    async def close(self) -> None:
        """Close the connection now (rather than whenever .__del__() is called).
        """

    @abstractmethod
    async def commit(self) -> None:
        """Commit any pending transaction to the database.
        """

    @abstractmethod
    async def rollback(self) -> None:
        """This method is optional since not all databases provide transaction
        support. 
        """
