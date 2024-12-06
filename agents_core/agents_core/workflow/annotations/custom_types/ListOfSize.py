from typing import TypeVar, Generic, List, Type

T = TypeVar('T')


class ListOfSize(Generic[T]):
    def __init__(self, items: List[T], required_size: int):
        if len(items) != required_size:
            raise ValueError(f"List must have exactly {required_size} items")
        self.items = items
        self.required_size = required_size

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def __repr__(self):
        return f"ListOfSize<{self.required_size}, {self.items}>"


def FixedList(type_: Type, size: int):
    """Factory function to create a fixed-size list type"""

    class _FixedSizeList(ListOfSize[type_]):
        _required_size = size

    return _FixedSizeList
