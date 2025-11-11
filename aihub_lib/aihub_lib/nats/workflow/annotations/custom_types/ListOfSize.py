from typing import Annotated, TypeVar

T = TypeVar("T")


class ListOfSize[T]:
    """
    A generic container that enforces a fixed size on a list of items.

    ### Why This Class?
    Some workflow steps or functions may require a fixed number of events or inputs.
    `ListOfSize` ensures that the provided list has exactly the required length,
    raising a ValueError otherwise. This makes the contract between code components explicit
    and helps detect configuration errors early.

    ### Features
    - Fixed-size enforcement at instantiation.
    - Behaves like a normal list afterward (indexing, iteration).
    """

    def __init__(
        self,
        items: Annotated[list[T], "The list of items to wrap"],
        required_size: Annotated[int, "The exact size that the list must have"],
    ):
        if len(items) != required_size:
            raise ValueError(f"List must have exactly {required_size} items (got {len(items)})")
        self.items = items
        self.required_size = required_size

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index: int) -> T:
        return self.items[index]

    def __repr__(self):
        return f"ListOfSize<{self.required_size}, {self.items}>"


def FixedList[T](
    type_: Annotated[type[T], "The type of items in the fixed-size list"],
    size: Annotated[int, "The fixed size of the list"],
) -> type[ListOfSize[T]]:
    """
    A factory function to create a specialized fixed-size list type.

    ### Why This Factory?
    Instead of manually defining each fixed-size list type,
    `FixedList` allows you to programmatically produce a `ListOfSize` subclass
    that includes a `_required_size` attribute. This can be used by the event extraction logic
    (or any other type inspection tools) to understand that a parameter or return type expects
    a fixed number of items.

    ### Example
    If you need a list of exactly 3 `SomeEvent` items:
    ```python
    My3EventList = FixedList(SomeEvent, 3)
    ```
    Now `My3EventList` is a type that, when instantiated, must have exactly three `SomeEvent`s.
    """

    class _FixedSizeList(ListOfSize[type_]):
        _required_size = size
        _item_type = type_

    return _FixedSizeList
