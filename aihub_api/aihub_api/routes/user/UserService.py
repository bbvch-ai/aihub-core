from datetime import UTC, datetime, timedelta

from aihub_lib.auth.identity.IdentityProvider import IdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.user.UserEntity import Dashboard, DashboardItem, UserEntity
from mongoengine import DoesNotExist

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.MyUserDTO import MyUserDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO


class UserService:
    """
    A service layer that encapsulates user-related logic:
    - Converting an authenticated user object to a UserDTO.
    - Retrieving user information from Azure AD or another identity provider.

    ### Why UserService?
    By separating user logic from controllers, the code remains organized and testable.
    `UserService`:
    - Uses `AzureIdentityProvider` to fetch user details by OID.
    - Converts `UserIdentity` objects into `UserDTO`s for consistent responses.

    ### Methods
    - `get_logged_in_user`: Converts the currently authenticated user into a `UserDTO`.
    - `get_user_by_oid`: Retrieves a user's info by their OID (Object ID),
      useful for building responses that include user details.
    """

    @staticmethod
    async def get_logged_in_user(user: UserIdentity, identity_provider: IdentityProvider) -> MyUserDTO:
        """
        Convert the `UserIdentity` (provided by the auth layer) into a MyUserDTO,
        including information from the UserEntity like dashboard settings, favorite modules, and roles.
        """
        await UserService.get_user_by_oid(
            user.id, identity_provider
        )  # Ensures that the UserEntity exists and is up to date.
        user_entity = UserEntity.by_oid(user.id)

        dashboard_data = user_entity.dashboard.to_mongo()
        dashboard_dto = DashboardDTO(**dashboard_data)

        return MyUserDTO(
            id=user_entity.id,
            name=user_entity.name,
            email=user_entity.email,
            profile_image=user_entity.profile_image,
            dashboard=dashboard_dto,
            favorite_modules=user_entity.favorite_modules,
            roles=user_entity.roles,
        )

    @staticmethod
    async def get_user_by_oid(user_oid: str, identity_provider: IdentityProvider) -> UserDTO:
        """
        Retrieve user info by OID (id, name, email, profile_image) as a UserDTO.
        It first checks a db (UserEntity). If recent and essential data is present,
        it's returned from the db. Otherwise, it fetches from the identity provider,
        ensures the UserEntity is created/updated (including roles and defaults for new users),
        and then returns basic info as a UserDTO.
        """
        try:
            user_entity = UserEntity.by_oid(user_oid)
            last_updated_from_db = user_entity.last_updated

            if last_updated_from_db.tzinfo is None:
                last_updated_aware = last_updated_from_db.replace(tzinfo=UTC)
            else:
                last_updated_aware = last_updated_from_db

            if (datetime.now(UTC) - last_updated_aware) < timedelta(hours=24):
                return UserDTO.from_user_entity(user_entity)
        except DoesNotExist:
            pass

        user_identity = await identity_provider.get_user_identity_by_oid(user_oid)
        UserEntity.ensure_user_exists(
            oid=user_oid,
            name=user_identity.name,
            email=user_identity.email,
            roles=user_identity.roles,
            profile_image=user_identity.profile_image,
        )

        return UserDTO.from_user_identity(user_identity)

    @staticmethod
    def get_user_dashboard(user: UserIdentity) -> DashboardDTO | None:
        """
        Retrieves the dashboard settings for the given authenticated user.
        """
        try:
            user_entity = UserEntity.by_oid(user.id)
        except DoesNotExist:
            return None

        if user_entity.dashboard:
            dashboard_data = user_entity.dashboard.to_mongo()
            return DashboardDTO(**dashboard_data)
        return None

    @staticmethod
    async def update_user_dashboard(
        user: UserIdentity, dashboard_dto: DashboardDTO, identity_provider: IdentityProvider
    ) -> None:
        """
        Updates or creates the dashboard settings for the given authenticated user.
        """
        try:
            user_entity = UserEntity.by_oid(user.id)
        except DoesNotExist:
            user_identity = await identity_provider.get_user_identity_by_oid(user.id)
            user_entity = UserEntity.ensure_user_exists(
                oid=user.id,
                name=user_identity.name,
                email=user_identity.email,
                roles=user_identity.roles,
                profile_image=user_identity.profile_image,
            )

        dashboard_data_dict = dashboard_dto.model_dump()

        children_data = dashboard_data_dict.pop("children", [])
        dashboard_items = []
        if children_data:
            for item_data in children_data:
                dashboard_items.append(DashboardItem(**item_data))

        user_entity.dashboard = Dashboard(children=dashboard_items, **dashboard_data_dict)
        user_entity.save()
