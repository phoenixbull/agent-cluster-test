"""
用户 API 测试
"""
import pytest
from fastapi import status


class TestGetCurrentUser:
    """获取当前用户测试"""
    
    def test_get_current_user_success(self, authenticated_client, test_user):
        """测试正常获取当前用户信息"""
        response = authenticated_client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert "hashed_password" not in data
    
    def test_get_current_user_unauthorized(self, client):
        """测试未认证访问"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateCurrentUser:
    """更新当前用户测试"""
    
    def test_update_user_success(self, authenticated_client, db_session, test_user):
        """测试正常更新用户信息"""
        response = authenticated_client.patch(
            "/api/v1/users/me",
            json={"username": "newusername"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "newusername"
        assert data["email"] == test_user.email
    
    def test_update_user_email(self, authenticated_client, db_session, test_user):
        """测试更新邮箱"""
        response = authenticated_client.patch(
            "/api/v1/users/me",
            json={"email": "newemail@example.com"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newemail@example.com"
    
    def test_update_user_duplicate_email(self, authenticated_client, db_session):
        """测试更新为已存在的邮箱"""
        from app.models.user import User
        from app.core.security import get_password_hash
        
        # 创建另一个用户
        other_user = User(
            email="existing@example.com",
            username="existinguser",
            hashed_password=get_password_hash("TestPass123")
        )
        db_session.add(other_user)
        db_session.commit()
        
        response = authenticated_client.patch(
            "/api/v1/users/me",
            json={"email": "existing@example.com"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "已被使用" in response.json()["detail"]
    
    def test_update_user_password(self, authenticated_client, db_session, test_user):
        """测试更新密码"""
        response = authenticated_client.patch(
            "/api/v1/users/me",
            json={"password": "NewPass456"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 验证新密码可以登录
        from app.core.security import verify_password
        db_session.refresh(test_user)
        assert verify_password("NewPass456", test_user.hashed_password)
    
    def test_update_user_weak_password(self, authenticated_client):
        """测试弱密码更新"""
        response = authenticated_client.patch(
            "/api/v1/users/me",
            json={"password": "123"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
