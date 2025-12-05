from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.expert.ExpertGroupEntity import ExpertGroupEntity

from aihub_api.routes.expert_group.dto.CreateExpertGroupRequest import CreateExpertGroupRequest
from aihub_api.routes.expert_group.dto.ExpertGroupResponse import ExpertGroupResponse
from aihub_api.routes.expert_group.dto.UpdateExpertGroupRequest import UpdateExpertGroupRequest


class ExpertGroupService:
    @staticmethod
    @trace_fn
    def create_group(data: CreateExpertGroupRequest) -> ExpertGroupResponse:
        """
        Creates a new expert group.
        Raises NotUniqueError if a group with the same name already exists.
        """
        group = ExpertGroupEntity(
            name=data.name,
            description=data.description,
            member_user_ids=data.member_user_ids,
        )
        group.save()
        return ExpertGroupResponse.from_entity(group)

    @staticmethod
    @trace_fn
    def list_groups() -> list[ExpertGroupResponse]:
        """Lists all expert groups in the database."""
        groups = ExpertGroupEntity.list_all()
        return [ExpertGroupResponse.from_entity(group) for group in groups]

    @staticmethod
    @trace_fn
    def get_group_by_id(group_id: str) -> ExpertGroupResponse:
        """
        Retrieves a single expert group by its ID.
        Raises DoesNotExist if the group is not found.
        """
        group = ExpertGroupEntity.objects.get(id=group_id)
        return ExpertGroupResponse.from_entity(group)

    @staticmethod
    @trace_fn
    def get_group_by_name(name: str) -> ExpertGroupResponse | None:
        """
        Retrieves an expert group by its name.
        Returns None if not found.
        """
        group = ExpertGroupEntity.get_by_name(name)
        return ExpertGroupResponse.from_entity(group) if group else None

    @staticmethod
    @trace_fn
    def update_group(group_id: str, data: UpdateExpertGroupRequest) -> ExpertGroupResponse:
        """
        Updates an existing expert group's fields.
        Raises DoesNotExist if the group is not found.
        Raises NotUniqueError if the new name conflicts with an existing group.
        """
        group = ExpertGroupEntity.objects.get(id=group_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return ExpertGroupResponse.from_entity(group)

        for key, value in update_data.items():
            setattr(group, key, value)
        group.save()
        return ExpertGroupResponse.from_entity(group)

    @staticmethod
    @trace_fn
    def delete_group(group_id: str) -> None:
        """
        Deletes an expert group by its ID.
        Raises DoesNotExist if the group is not found.
        """
        group = ExpertGroupEntity.objects.get(id=group_id)
        group.delete()

    @staticmethod
    @trace_fn
    def add_member(group_id: str, user_id: str) -> ExpertGroupResponse:
        """
        Adds a member to an expert group.
        Raises DoesNotExist if the group is not found.
        """
        group = ExpertGroupEntity.objects.get(id=group_id)
        if user_id not in group.member_user_ids:
            group.member_user_ids.append(user_id)
            group.save()
        return ExpertGroupResponse.from_entity(group)

    @staticmethod
    @trace_fn
    def remove_member(group_id: str, user_id: str) -> ExpertGroupResponse:
        """
        Removes a member from an expert group.
        Raises DoesNotExist if the group is not found.
        """
        group = ExpertGroupEntity.objects.get(id=group_id)
        if user_id in group.member_user_ids:
            group.member_user_ids.remove(user_id)
            group.save()
        return ExpertGroupResponse.from_entity(group)
