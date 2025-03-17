# ================================================= User Verification =========================================================

# User Approval (Admin only)
class UserApprovalResource(Resource):
    @jwt_required()
    @role_required(["admin"])
    def get(self):
        users = User.query.filter_by(is_approved=False).all()
        return jsonify([user.serialize() for user in users])

    @jwt_required()
    @role_required(["admin"])
    def put(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"})
        
        user.is_approved = True
        db.session.commit()
        return jsonify({"message": "User approved successfully"})

    @jwt_required()
    @role_required(["admin"])
    def delete(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"})
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User rejected and removed"})

# ================================================= XXXXXXXXXXXXXXXXXX =========================================================


# ================================================= Task Management =========================================================


# Fetch all tasks, create a new task, update, delete tasks
class TaskResource(Resource):
    @jwt_required()
    @role_required(["admin", "manager"])
    def get(self, task_id=None):
        if task_id:
            task = Task.query.get(task_id)
            return jsonify(task.serialize() if task else {"message": "Task not found"})
        tasks = Task.query.all()
        return jsonify([task.serialize() for task in tasks])

    @jwt_required()
    @role_required(["manager", "admin"])
    def post(self):
        data = request.get_json()
        new_task = Task(
            title=data['title'],
            description=data.get('description'),
            deadline=datetime.strptime(data['deadline'], '%Y-%m-%d') if data.get('deadline') else None
        )
        db.session.add(new_task)
        db.session.commit()
        return jsonify({"message": "Task created successfully"})

    @jwt_required()
    @role_required(["manager", "admin"])
    def put(self, task_id):
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"message": "Task not found"})
        
        data = request.get_json()
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.status = data.get('status', task.status)
        db.session.commit()
        return jsonify({"message": "Task updated successfully"})

    @jwt_required()
    @role_required(["admin"])
    def delete(self, task_id):
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"message": "Task not found"})
        
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Task deleted successfully"})


# ================================================= XXXXXXXXXXXXXXXXXX =========================================================

# ================================================= XXXXXXXXXXXXXXXXXX =========================================================



# Assign Task to User
class AssignTaskResource(Resource):
    @jwt_required()
    @role_required(["manager"])
    def put(self, task_id):
        data = request.get_json()
        user_id = data.get("user_id")
        
        task = Task.query.get(task_id)
        user = User.query.get(user_id)

        if not task or not user:
            return jsonify({"message": "Task or User not found"})

        task.assigned_user_id = user.id
        db.session.commit()
        return jsonify({"message": "Task assigned successfully"})






# ================================================= XXXXXXXXXXXXXXXXXX =========================================================
# Stats API
class StatsResource(Resource):
    @jwt_required()
    @role_required(["admin", "manager"])
    def get(self):
        total_users = User.query.count()
        total_tasks = Task.query.count()
        completed_tasks = Task.query.filter_by(status="completed").count()
        
        return jsonify({
            "total_users": total_users,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks
        })




api.add_resource(TaskResource, '/tasks', '/task/<int:task_id>')
api.add_resource(UserApprovalResource, '/users/pending', '/users/<int:user_id>/approve', '/users/<int:user_id>/reject')
api.add_resource(StatsResource, '/stats')
api.add_resource(AssignTaskResource, '/task/<int:task_id>/assign')