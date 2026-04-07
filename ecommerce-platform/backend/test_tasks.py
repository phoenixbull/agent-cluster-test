"""
任务 API 测试
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta


class TestCreateTask:
    """创建任务测试"""
    
    def test_create_task_success(self, authenticated_client):
        """测试正常创建任务"""
        response = authenticated_client.post(
            "/api/v1/tasks",
            json={
                "title": "测试任务",
                "description": "这是一个测试任务",
                "priority": "high",
                "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "测试任务"
        assert data["priority"] == "high"
        assert data["status"] == "pending"
        assert "id" in data
        assert "owner_id" in data
    
    def test_create_task_unauthorized(self, client):
        """测试未认证创建任务"""
        response = client.post(
            "/api/v1/tasks",
            json={"title": "测试任务"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_task_minimal(self, authenticated_client):
        """测试最小化创建任务"""
        response = authenticated_client.post(
            "/api/v1/tasks",
            json={"title": "简单任务"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "简单任务"
        assert data["priority"] == "medium"  # 默认值
        assert data["status"] == "pending"  # 默认值
    
    def test_create_task_empty_title(self, authenticated_client):
        """测试空标题"""
        response = authenticated_client.post(
            "/api/v1/tasks",
            json={"title": ""}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListTasks:
    """获取任务列表测试"""
    
    def test_list_tasks_success(self, authenticated_client, db_session, test_user):
        """测试正常获取任务列表"""
        from app.models.task import Task
        
        # 创建测试任务
        for i in range(5):
            task = Task(
                title=f"任务{i}",
                owner_id=test_user.id,
            )
            db_session.add(task)
        db_session.commit()
        
        response = authenticated_client.get("/api/v1/tasks")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["page_size"] == 20
    
    def test_list_tasks_pagination(self, authenticated_client, db_session, test_user):
        """测试分页"""
        from app.models.task import Task
        
        # 创建 25 个任务
        for i in range(25):
            task = Task(title=f"任务{i}", owner_id=test_user.id)
            db_session.add(task)
        db_session.commit()
        
        response = authenticated_client.get("/api/v1/tasks?page=1&page_size=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 25
        assert len(data["items"]) == 10
    
    def test_list_tasks_filter_status(self, authenticated_client, db_session, test_user):
        """测试按状态筛选"""
        from app.models.task import Task, TaskStatus
        
        task1 = Task(title="进行中", owner_id=test_user.id, status=TaskStatus.IN_PROGRESS)
        task2 = Task(title="已完成", owner_id=test_user.id, status=TaskStatus.COMPLETED)
        db_session.add_all([task1, task2])
        db_session.commit()
        
        response = authenticated_client.get("/api/v1/tasks?status=in_progress")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "in_progress"
    
    def test_list_tasks_unauthorized(self, client):
        """测试未认证访问"""
        response = client.get("/api/v1/tasks")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetTask:
    """获取单个任务测试"""
    
    def test_get_task_success(self, authenticated_client, db_session, test_user):
        """测试正常获取任务"""
        from app.models.task import Task
        
        task = Task(title="测试任务", owner_id=test_user.id)
        db_session.add(task)
        db_session.commit()
        
        response = authenticated_client.get(f"/api/v1/tasks/{task.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == task.id
        assert data["title"] == "测试任务"
    
    def test_get_task_not_found(self, authenticated_client):
        """测试任务不存在"""
        response = authenticated_client.get("/api/v1/tasks/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_task_not_owner(self, authenticated_client, db_session):
        """测试获取其他用户的任务"""
        from app.models.user import User
        from app.models.task import Task
        
        # 创建另一个用户
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed"
        )
        db_session.add(other_user)
        db_session.commit()
        
        # 创建属于其他用户的任务
        task = Task(title="别人的任务", owner_id=other_user.id)
        db_session.add(task)
        db_session.commit()
        
        response = authenticated_client.get(f"/api/v1/tasks/{task.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateTask:
    """更新任务测试"""
    
    def test_update_task_success(self, authenticated_client, db_session, test_user):
        """测试正常更新任务"""
        from app.models.task import Task
        
        task = Task(title="原任务", owner_id=test_user.id)
        db_session.add(task)
        db_session.commit()
        
        response = authenticated_client.patch(
            f"/api/v1/tasks/{task.id}",
            json={"title": "新任务", "priority": "urgent"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "新任务"
        assert data["priority"] == "urgent"
    
    def test_update_task_status_completed(self, authenticated_client, db_session, test_user):
        """测试完成任务"""
        from app.models.task import Task
        
        task = Task(title="任务", owner_id=test_user.id)
        db_session.add(task)
        db_session.commit()
        
        response = authenticated_client.patch(
            f"/api/v1/tasks/{task.id}",
            json={"status": "completed"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None
    
    def test_update_task_not_found(self, authenticated_client):
        """测试更新不存在的任务"""
        response = authenticated_client.patch(
            "/api/v1/tasks/99999",
            json={"title": "新标题"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteTask:
    """删除任务测试"""
    
    def test_delete_task_success(self, authenticated_client, db_session, test_user):
        """测试正常删除任务"""
        from app.models.task import Task
        
        task = Task(title="待删除任务", owner_id=test_user.id)
        db_session.add(task)
        db_session.commit()
        task_id = task.id
        
        response = authenticated_client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 验证已删除
        response = authenticated_client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_task_not_found(self, authenticated_client):
        """测试删除不存在的任务"""
        response = authenticated_client.delete("/api/v1/tasks/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTaskStatistics:
    """任务统计测试"""
    
    def test_get_statistics_success(self, authenticated_client, db_session, test_user):
        """测试获取统计信息"""
        from app.models.task import Task, TaskStatus, TaskPriority
        
        # 创建不同状态和优先级的任务
        tasks = [
            Task(title="任务 1", owner_id=test_user.id, status=TaskStatus.PENDING, priority=TaskPriority.HIGH),
            Task(title="任务 2", owner_id=test_user.id, status=TaskStatus.COMPLETED, priority=TaskPriority.MEDIUM),
            Task(title="任务 3", owner_id=test_user.id, status=TaskStatus.IN_PROGRESS, priority=TaskPriority.LOW),
        ]
        db_session.add_all(tasks)
        db_session.commit()
        
        response = authenticated_client.get("/api/v1/tasks/statistics")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert "by_status" in data
        assert "by_priority" in data
        assert data["by_status"]["pending"] == 1
        assert data["by_status"]["completed"] == 1
