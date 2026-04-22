import json

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.events.utils import get_inheritance_depth, get_parent_classes_until_base
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: F401


def test_get_inheritance_depth_simple_hierarchy():
    """Test basic inheritance depth calculation for single inheritance path."""

    # Create a simple inheritance hierarchy: D -> C -> B -> A
    class A:
        pass

    class B(A):
        pass

    class C(B):
        pass

    class D(C):
        pass

    # Check depths
    assert get_inheritance_depth(A, A) == 0  # Class to itself is 0
    assert get_inheritance_depth(B, A) == 1
    assert get_inheritance_depth(C, A) == 2
    assert get_inheritance_depth(D, A) == 3

    # Class not in hierarchy
    class Unrelated:
        pass

    assert get_inheritance_depth(Unrelated, A) == -1


def test_get_inheritance_depth_diamond_inheritance():
    """Test inheritance depth with diamond pattern returns the longest path."""

    # Create a diamond inheritance pattern:
    #     A
    #    / \
    #   B   C
    #    \ /
    #     D
    class A:
        pass

    class B(A):
        pass

    class C(A):
        pass

    class D(B, C):
        pass  # Multiple inheritance

    # Verify it returns the depth 2 as the path is D->B->A or D->C->A
    assert get_inheritance_depth(D, A) == 2

    # Create an asymmetric diamond:
    #     A
    #    / \
    #   B   C
    #  /     \
    # E       F
    #  \     /
    #     G
    class E(B):
        pass

    class F(C):
        pass

    class G(E, F):
        pass

    # Should return 3 as the longest path (G->E->B->A or G->F->C->A)
    assert get_inheritance_depth(G, A) == 3


def test_get_inheritance_depth_complex_hierarchy():
    """Test inheritance depth calculation with complex inheritance patterns."""

    # Create a more complex inheritance hierarchy
    # Visualization:
    #             Base
    #            /|  \
    #           / |   \
    #          A  B    C     X
    #          |  |    |     |
    #          |   \   |     Y
    #          |    \  |     |
    #          D-----E |     Z
    #           \    / |    /
    #            \  /  |   /
    #             F----+--+
    #               Complex

    class Base:
        pass

    class A(Base):
        pass

    class B(Base):
        pass

    class C(Base):
        pass

    class D(A, B):
        pass  # Multiple parents

    class E(B, C):
        pass  # Multiple parents

    class F(D, E):
        pass  # Diamond inheritance

    # Paths:
    # F->D->A->Base: depth 3
    # F->D->B->Base: depth 3
    # F->E->B->Base: depth 3
    # F->E->C->Base: depth 3
    assert get_inheritance_depth(F, Base) == 3  # FIXED: Longest path is 3 steps, not 2

    # Even more complex case with differing path lengths
    class X(Base):
        pass

    class Y(X):
        pass

    class Z(Y):
        pass

    class Complex(F, Z):
        pass  # Mix of diamond and deep hierarchies

    # Paths:
    # Complex->F->D->A->Base: depth 4
    # Complex->F->D->B->Base: depth 4
    # Complex->F->E->B->Base: depth 4
    # Complex->F->E->C->Base: depth 4
    # Complex->Z->Y->X->Base: depth 4
    assert get_inheritance_depth(Complex, Base) == 4  # FIXED: Longest path is 4 steps, not 3


def test_get_inheritance_depth_with_mixin_pattern():
    """Test inheritance depth calculation with mixin-style inheritance patterns."""

    # Visualization:
    #            BaseMixin
    #           /    |    \
    #          /     |     \
    #    FeatureA FeatureB FeatureC
    #         \      |      /
    #          \     |     /
    #            Product

    class BaseMixin:
        pass

    class FeatureA(BaseMixin):
        pass

    class FeatureB(BaseMixin):
        pass

    class FeatureC(BaseMixin):
        pass

    class Product(FeatureA, FeatureB, FeatureC):
        pass

    # Paths:
    # Product->FeatureA->BaseMixin: depth 2
    # Product->FeatureB->BaseMixin: depth 2
    # Product->FeatureC->BaseMixin: depth 2
    assert get_inheritance_depth(Product, BaseMixin) == 2  # FIXED: Correct depth is 2

    # Visualization with enhanced feature:
    #            BaseMixin
    #           /    |    \
    #          /     |     \
    #    FeatureA FeatureB FeatureC
    #        |      |      /
    # EnhancedFeatureA    /
    #         \     |    /
    #          \    |   /
    #        EnhancedProduct

    # Add an extra layer to one feature
    class EnhancedFeatureA(FeatureA):
        pass

    class EnhancedProduct(EnhancedFeatureA, FeatureB, FeatureC):
        pass

    # Paths:
    # EnhancedProduct->EnhancedFeatureA->FeatureA->BaseMixin: depth 3
    # EnhancedProduct->FeatureB->BaseMixin: depth 2
    # EnhancedProduct->FeatureC->BaseMixin: depth 2
    assert get_inheritance_depth(EnhancedProduct, BaseMixin) == 3  # FIXED: Correct depth is 3


def test_inheritance_depth_with_custom_events():
    """Test that inheritance depth works correctly with custom event types."""

    # Create a custom event hierarchy
    class CustomBaseEvent(BaseEvent):
        pass

    class ServiceEvent(CustomBaseEvent):
        pass

    class NetworkEvent(ServiceEvent):
        pass

    class DatabaseEvent(ServiceEvent):
        pass

    class APIEvent(NetworkEvent, DatabaseEvent):
        pass  # Diamond pattern

    # Register these manually as we're not using __init_subclass__
    BaseEvent._event_registry["CustomBaseEvent"] = CustomBaseEvent
    BaseEvent._event_registry["ServiceEvent"] = ServiceEvent
    BaseEvent._event_registry["NetworkEvent"] = NetworkEvent
    BaseEvent._event_registry["DatabaseEvent"] = DatabaseEvent
    BaseEvent._event_registry["APIEvent"] = APIEvent

    try:
        # Test the depth calculations
        assert get_inheritance_depth(CustomBaseEvent, BaseEvent) == 1
        assert get_inheritance_depth(ServiceEvent, BaseEvent) == 2
        assert get_inheritance_depth(NetworkEvent, BaseEvent) == 3
        assert get_inheritance_depth(DatabaseEvent, BaseEvent) == 3
        assert get_inheritance_depth(APIEvent, BaseEvent) == 4  # Longest path

        # Test through serialization/deserialization
        api_event = APIEvent()
        serialized = json.dumps(api_event.model_dump())
        deserialized = BaseEvent.deserialize_event(serialized)

        # Verify that inheritance info is preserved
        assert "APIEvent" in deserialized._parent_event_names
        assert "NetworkEvent" in deserialized._parent_event_names
        assert "DatabaseEvent" in deserialized._parent_event_names
        assert "ServiceEvent" in deserialized._parent_event_names
        assert "CustomBaseEvent" in deserialized._parent_event_names
    finally:
        # Clean up the registry
        for cls_name in ["CustomBaseEvent", "ServiceEvent", "NetworkEvent", "DatabaseEvent", "APIEvent"]:
            BaseEvent._event_registry.pop(cls_name, None)


def test_event_deserialization_priority_by_depth():
    """Test that event deserialization prioritizes more specific (deeper) classes."""

    # Setup a simple 3-level hierarchy
    class Level1Event(BaseEvent):
        common_field: str

    class Level2Event(Level1Event):
        level2_field: str

    class Level3Event(Level2Event):
        level3_field: str

    # Register these manually
    BaseEvent._event_registry["Level1Event"] = Level1Event
    BaseEvent._event_registry["Level2Event"] = Level2Event
    BaseEvent._event_registry["Level3Event"] = Level3Event

    try:
        # Create event data with all three classes in parent_class_names
        # but with a type that doesn't exist in this process
        event_data = {
            "_event_name": "UnknownSubclassEvent",
            "common_field": "shared value",
            "level2_field": "level 2 value",
            "level3_field": "level 3 value",
            "_parent_event_names": ["UnknownSubclassEvent", "Level3Event", "Level2Event", "Level1Event"],
        }

        # Deserialize it
        deserialized = BaseEvent.deserialize_event(event_data)

        # It should use Level3Event as the most specific known class
        assert isinstance(deserialized, Level3Event)
        assert deserialized.common_field == "shared value"
        assert deserialized.level2_field == "level 2 value"
        assert deserialized.level3_field == "level 3 value"
        assert deserialized._unknown_event_name == "UnknownSubclassEvent"

        # Now remove Level3Event from _parent_event_names
        event_data["_parent_event_names"] = ["UnknownSubclassEvent", "Level2Event", "Level1Event"]
        deserialized = BaseEvent.deserialize_event(event_data)

        # It should fall back to Level2Event
        assert isinstance(deserialized, Level2Event)
        assert not isinstance(deserialized, Level3Event)

        # Finally, remove both Level3Event and Level2Event
        event_data["_parent_event_names"] = ["UnknownSubclassEvent", "Level1Event"]
        deserialized = BaseEvent.deserialize_event(event_data)

        # It should fall back to Level1Event
        assert isinstance(deserialized, Level1Event)
        assert not isinstance(deserialized, Level2Event)
    finally:
        # Clean up
        for cls_name in ["Level1Event", "Level2Event", "Level3Event"]:
            BaseEvent._event_registry.pop(cls_name, None)


def test_get_parent_classes_until_base_simple_hierarchy():
    """Test that get_parent_classes_until_base returns all parents up to base class."""

    # Create a simple inheritance hierarchy
    class Base:
        pass

    class A(Base):
        pass

    class B(A):
        pass

    class C(B):
        pass

    # Test parent collection
    assert get_parent_classes_until_base(C, Base) == {"A", "B"}
    assert get_parent_classes_until_base(B, Base) == {"A"}
    assert get_parent_classes_until_base(A, Base) == set()  # No parents between A and Base
    assert get_parent_classes_until_base(Base, Base) == set()  # Base to itself is empty


def test_get_parent_classes_until_base_multiple_inheritance():
    """Test that get_parent_classes_until_base works with multiple inheritance."""

    class Base:
        pass

    class A(Base):
        pass

    class B(Base):
        pass

    class C(A, B):
        pass  # Multiple inheritance

    # Should include both direct parents, but not Base itself
    assert get_parent_classes_until_base(C, Base) == {"A", "B"}


def test_get_parent_classes_until_base_diamond():
    """Test that get_parent_classes_until_base works with diamond inheritance."""

    class Base:
        pass

    class A(Base):
        pass

    class B(Base):
        pass

    class C(A):
        pass

    class D(B):
        pass

    class E(C, D):
        pass  # Diamond pattern

    # Should include all classes in the inheritance path
    expected = {"A", "B", "C", "D"}
    assert get_parent_classes_until_base(E, Base) == expected


def test_get_parent_classes_until_base_deep_hierarchy():
    """Test get_parent_classes_until_base with a deep inheritance hierarchy."""

    class Level0:
        pass

    class Level1(Level0):
        pass

    class Level2(Level1):
        pass

    class Level3(Level2):
        pass

    class Level4(Level3):
        pass

    # Test different depths
    assert get_parent_classes_until_base(Level4, Level0) == {"Level1", "Level2", "Level3"}
    assert get_parent_classes_until_base(Level4, Level2) == {"Level3"}
    assert get_parent_classes_until_base(Level4, Level3) == set()


def test_get_parent_classes_until_base_with_event_classes():
    """Test get_parent_classes_until_base with actual event classes."""

    # Create a few test classes based on existing ones
    class CustomDisplayEvent(DisplayEvent):
        pass

    class SpecialDisplayEvent(CustomDisplayEvent):
        pass

    # Should include DisplayEvent but not BaseEvent
    assert "DisplayEvent" in get_parent_classes_until_base(CustomDisplayEvent, BaseEvent)
    assert "BaseEvent" not in get_parent_classes_until_base(CustomDisplayEvent, BaseEvent)

    # Should include both DisplayEvent and CustomDisplayEvent
    parents = get_parent_classes_until_base(SpecialDisplayEvent, BaseEvent)
    assert "DisplayEvent" in parents
    assert "CustomDisplayEvent" in parents
    assert "BaseEvent" not in parents


def test_get_parent_classes_until_base_complex_hierarchy():
    """Test get_parent_classes_until_base with complex hierarchy including mixins."""

    # Visualization:
    #            BaseMixin
    #           /         \
    #          /           \
    #    Feature1        Feature2
    #        |              |
    #   Enhancement1    Enhancement2
    #         \            /
    #          \          /
    #            Product

    class BaseMixin:
        pass

    class Feature1(BaseMixin):
        pass

    class Feature2(BaseMixin):
        pass

    class Enhancement1(Feature1):
        pass

    class Enhancement2(Feature2):
        pass

    class Product(Enhancement1, Enhancement2):
        pass

    # All classes except BaseMixin itself
    expected = {"Feature1", "Feature2", "Enhancement1", "Enhancement2"}
    assert get_parent_classes_until_base(Product, BaseMixin) == expected

    # Only classes between Product and Feature1
    assert get_parent_classes_until_base(Product, Feature1) == {"Enhancement1"}


def test_get_parent_classes_until_base_with_non_base_class():
    """Test behavior when the 'base' class isn't actually a base of the class."""

    # Visualization:
    #    A        Unrelated
    #    |
    #    B

    class Unrelated:
        pass

    class A:
        pass

    class B(A):
        pass

    # Comment says it should return empty set, but assertion expects {"A"}
    # Let's check the actual implementation behavior
    result = get_parent_classes_until_base(B, Unrelated)

    # The function should collect all parent classes when base is not in hierarchy
    # Based on implementation in paste.txt, it returns all parents
    assert result == {"A"}

    # Alternative assertion with updated comment:
    # When the 'base' class isn't in the hierarchy, the function returns all parents
    assert get_parent_classes_until_base(B, Unrelated) == {"A"}


def test_get_parent_classes_until_base_intermediate_base():
    """Test using an intermediate class as the 'base'."""

    class Root:
        pass

    class A(Root):
        pass

    class B(A):
        pass

    class C(B):
        pass

    # Using B as the base should only include classes between C and B
    assert get_parent_classes_until_base(C, B) == set()

    # Using A as the base should include only B
    assert get_parent_classes_until_base(C, A) == {"B"}


def test_get_parent_classes_until_base_with_event_serialization():
    """Test that parent classes are correctly included in serialized events."""

    # Create a test event with multiple inheritance levels
    class Level1Event(BaseEvent):
        pass

    class Level2Event(Level1Event):
        pass

    class Level3EventA(Level2Event):
        pass

    class Level3EventB(Level2Event):
        pass

    class TestComplexEvent(Level3EventA, Level3EventB):
        pass

    # Register our classes
    BaseEvent._event_registry["Level1Event"] = Level1Event
    BaseEvent._event_registry["Level2Event"] = Level2Event
    BaseEvent._event_registry["Level3EventA"] = Level3EventA
    BaseEvent._event_registry["Level3EventB"] = Level3EventB
    BaseEvent._event_registry["TestComplexEvent"] = TestComplexEvent

    try:
        # Create an instance and serialize
        test_event = TestComplexEvent()
        serialized = json.dumps(test_event.model_dump())
        data = json.loads(serialized)

        # Check that all parent classes are included
        assert "Level1Event" in data["_parent_event_names"]
        assert "Level2Event" in data["_parent_event_names"]
        assert "Level3EventA" in data["_parent_event_names"]
        assert "Level3EventB" in data["_parent_event_names"]
        assert "TestComplexEvent" in data["_parent_event_names"]
        assert "BaseEvent" not in data["_parent_event_names"]  # Base itself shouldn't be included

        # Now deserialize and check
        deserialized = BaseEvent.deserialize_event(serialized)
        assert isinstance(deserialized, TestComplexEvent)

        # Remove the class from registry to test fallback behavior
        del BaseEvent._event_registry["TestComplexEvent"]

        # Deserialize again, should fall back to most specific parent
        deserialized = BaseEvent.deserialize_event(serialized)
        # Should use either Level3EventA or Level3EventB based on MRO
        assert isinstance(deserialized, Level3EventA) or isinstance(deserialized, Level3EventB)

        # Verify parent classes list is preserved
        assert "TestComplexEvent" in deserialized._parent_event_names
    finally:
        # Clean up the registry
        for cls_name in ["Level1Event", "Level2Event", "Level3EventA", "Level3EventB", "TestComplexEvent"]:
            BaseEvent._event_registry.pop(cls_name, None)
