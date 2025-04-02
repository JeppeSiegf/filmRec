import pytest
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from api import db
from api.models.user import User
from api.repositories.user_repository import UserRepository


class TestUserRepository:

    def test_get_all_users(self, test_db, test_user):
        users = UserRepository.get_all_users()
        assert isinstance(users, list)
        assert len(users) > 0
        assert test_user in users

    def test_get_user_by_profile_ref(self, test_db, test_user):
        """Test fetching a user by profile reference."""
        user = UserRepository.get_user_by_profile_ref(test_user.profile_ref)
        assert user is not None
        assert user.username == test_user.username

    def test_create_user(self, test_db):
        unique_suffix = datetime.utcnow().timestamp()
        new_user = User(
            username=f"TestUser_{unique_suffix}",
            profile_ref=f"user_{unique_suffix}",
            last_updated=datetime.utcnow().date()
        )
        created_user = UserRepository.create_user(new_user)

        assert created_user is not None
        assert created_user.username == new_user.username
        assert created_user.profile_ref == new_user.profile_ref

    def test_update_user(self, test_db, test_user):
        """Test updating an existing user."""
        updated_user = UserRepository.update_user(test_user.profile_ref, {"username": "UpdatedUser"})
        assert updated_user is not None
        assert updated_user.username == "UpdatedUser"

    def test_update_nonexistent_user(self, test_db):
        """Test updating a user that does not exist."""
        updated_user = UserRepository.update_user("nonexistent_ref", {"username": "UpdatedUser"})
        assert updated_user is None

    def test_delete_user(self, test_db, test_user):
        """Test deleting a user."""
        success = UserRepository.delete_user(test_user.profile_ref)
        assert success is True
        assert UserRepository.get_user_by_profile_ref(test_user.profile_ref) is None

    def test_delete_nonexistent_user(self, test_db):
        """Test deleting a user that does not exist."""
        success = UserRepository.delete_user("nonexistent_ref")
        assert success is False

    def test_create_user_db_error(self, mocker, test_db):
        """Simulate a database error when creating a user."""
        mocker.patch.object(db.session, "add", side_effect=SQLAlchemyError)
        new_user = User(username="ErrorUser", profile_ref="error123", last_updated=datetime.utcnow().date())
        assert UserRepository.create_user(new_user) is None

    def test_update_user_db_error(self, mocker, test_db, test_user):
        """Simulate a database error when updating a user."""
        mocker.patch.object(db.session, "commit", side_effect=SQLAlchemyError)
        updated_user = UserRepository.update_user(test_user.profile_ref, {"username": "ShouldFail"})
        assert updated_user is None

    def test_delete_user_db_error(self, mocker, test_db, test_user):
        """Simulate a database error when deleting a user."""
        mocker.patch.object(db.session, "commit", side_effect=SQLAlchemyError)
        success = UserRepository.delete_user(test_user.profile_ref)
        assert success is False
