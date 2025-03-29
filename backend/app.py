from datetime import datetime, timedelta
from flask import Flask, jsonify, make_response, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask_mail import Mail, Message
from celery.schedules import crontab
import os
from celery import Celery
import redis
from dotenv import load_dotenv
from celery.schedules import crontab


app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type, Authorization'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["JWT_SECRET_KEY"] = "aStrongSecretKey"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

api = Api(app)
jwt = JWTManager(app)
db = SQLAlchemy(app)

CORS(app)




# ==========================
# Flask-Mail Configuration
# ==========================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '0rajnishk@gmail.com'
app.config['MAIL_PASSWORD'] = 'mjqt keqs rbjg oeni'
app.config['MAIL_DEFAULT_SENDER'] = '0rajnishk@gmaail.com'

mail = Mail(app)




# ==========================
# Celery Configuration (Updated)
# ==========================
app.config['broker_url'] = os.getenv('BROKER_URL', 'redis://localhost:6379/0')
app.config['result_backend'] = os.getenv('RESULT_BACKEND', 'redis://localhost:6379/0')

celery = Celery(app.name, broker=app.config['broker_url'], backend=app.config['result_backend'])
celery.conf.broker_connection_retry_on_startup = True  # Fix Celery 6.0 deprecation warning

# ==========================
# Redis Cache Setup
# ==========================
cache = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# ==========================
# Celery Initialization
# ==========================
def init_celery(flask_app):
    celery_app = Celery(
        flask_app.import_name,
        broker=flask_app.config['broker_url'],
        backend=flask_app.config['result_backend']
    )
    celery_app.conf.update(flask_app.config)
    celery_app.conf.broker_connection_retry_on_startup = True  # Ensure retry on startup

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return super().__call__(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app

celery = init_celery(app)



# ==========================
# Celery Beat Configuration
# ==========================
celery.conf.timezone = 'Asia/Kolkata'
celery.conf.beat_schedule = {
    'send_reminders': {
        'task': 'tasks.send_reminders',
        'schedule': crontab(minute='*/1'),  # Runs every minute
        'args': ()
    },
    'monthly_report': {
        'task': 'tasks.monthly_report',
        'schedule': crontab(minute=0, hour=10, day_of_month=1),  # Runs at midnight on the 1st of every month
        'args': ()
    },
}




# ######################################################################################################################################################## #
# ##############################################################  Models  ################################################################################ #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="employee")  # Roles: employee, manager, admin
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_approved": self.is_approved,
            "created_at": self.created_at
        }

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="pending")
    deadline = db.Column(db.DateTime, nullable=True)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "deadline": self.deadline,
            "assigned_user_id": self.assigned_user_id
        }
    

with app.app_context():
    db.create_all() 




# ######################################################################################################################################################## #
# ##############################################################  decorator  ############################################################################# #


def get_current_user():
    username = get_jwt_identity()
    return User.query.filter_by(username=username).first()

def role_required(required_roles):
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user is None or user.role not in required_roles:
                return jsonify({"message": "Unauthorized access"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator



# ######################################################################################################################################################## #
# #########################################################  Authentication  ############################################################################# #


class SignupResource(Resource):
    def post(self):
        data = request.get_json()

        username = data['username']
        email = data['email']
        password = data['password']

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            res = jsonify({'message': 'Username or Email already exists'})
            make_response(res, 409)

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, email=email, password_hash=hashed_password)

        db.session.add(new_user)
        db.session.commit()
        res = jsonify({"msg": "user created"})
        return make_response(res, 201)


class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        email = data['email']
        password = data['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            access_token = create_access_token(identity=user.username)
            print(access_token)
            return jsonify({"msg":"successfully logged in", "token": access_token, "role": user.role})
            # return make_response(response, 200)
        
        response = jsonify({"msg": "email or password incorrect."})
        return make_response(response, 401)




# ######################################################################################################################################################## #
# ##############################################################  Resources  ############################################################################# #
class Hello(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        return {"msg": f"hello world from backend! {current_user}"}
    
    def post(self):
        name = request.json.get("name")
        return f"hello from post, name - {name}"
    
    def put(self):
        user_id = request.json.get("user_id")
        return f"hello from put, user id - {user_id}"

    def delete(self):
        return "hello from delete"
    



# ######################################################################################################################################################## #

# User Approval (Admin only)
class UserApprovalResource(Resource):
    @jwt_required()
    @role_required(["admin"])
    # @cache.cached(timeout=60)

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
        # cache.clear()

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

class UserManagementResource(Resource):
    @jwt_required()
    @role_required(["admin", "manager"])
    def get(self):
        Users = User.query.all()
        users = []
        for user in Users:
            users.append(user.serialize())
        return jsonify(users)





# create admin user if already not there in the db
def create_admin():
    with app.app_context():
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            hashed_password = generate_password_hash("admin")
            new_admin = User(username="admin", email="admin@mail.com", password_hash=hashed_password, role="admin", is_approved=True)
            db.session.add(new_admin)
            db.session.commit()
            print("Admin user created successfully")



# ######################################################################################################################################################## #
# ######################################################################################################################################################## #
# ######################################################################################################################################################## #
# ######################################################################################################################################################## #
# ================================================= User Verification =========================================================


# ================================================= Task Management =========================================================



# Fetch all tasks, create a new task, update, delete tasks
class TaskResource(Resource):
    @jwt_required()
    @role_required(["admin", "manager"])
    def get(self, task_id=None):
        if task_id is not None:
            task = Task.query.get(task_id)
            tasks = { 'title': task.title,
            'description': task.description,
            'status': task.status,
            'deadline': task.deadline,
            'assigned_user_id': task.assigned_user_id
            }
            return jsonify(task.serialize() if task else {"message": "Task not found"})
        tasks = Task.query.all()
        task_to_return = []

        for task in tasks:
            task_to_return.append(task.serialize())

        return jsonify(task_to_return)
    
    @jwt_required()
    @role_required(["manager", "admin"])
    def post(self):
        data = request.get_json()
        new_task = Task(
            title=data['title'],
            assigned_user_id=data.get('user_id'),
            deadline=datetime.strptime(data['deadline'], '%Y-%m-%d') if data.get('deadline') else None
        )
        db.session.add(new_task)
        db.session.commit()
        return {"message": "Task created successfully"}

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


class UserTaskResource(Resource):
    @jwt_required()
    @role_required(["employee"])
    def get(self):

        username = get_jwt_identity()
        print("Username", username)
        print("=====================================", username)
        user = User.query.filter_by(username=username).first()
        print(user.id)


        tasks = Task.query.filter_by(assigned_user_id=user.id).all()

        tasks_to_return = []

        for task in tasks:
            tasks_to_return.append(task.serialize())

        return make_response(jsonify(tasks_to_return), 200)



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



# ######################################################################################################################################################## #
# ######################################################################################################################################################## #


@celery.task(name="tasks.send_reminders")
def send_reminders():
    email = ["jeevanbidgar@gmail.com", "gumapathee@gmail.com", "contact.rajnishk@gmail.com"]
    for mail in email:
        msg = Message(
            subject="Test Email from Flask",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[mail],
            body="This is a test email sent via Flask and SMTP."
        )
        mail.send(msg)
    print("Reminder sent at 7:00 AM IST!")
    return "Reminder sent successfully!"





# ######################################################################################################################################################## #
# ##############################################################  Routes  ############################################################################### #
api.add_resource(Hello, '/')
api.add_resource(SignupResource, '/signup')
api.add_resource(LoginResource, '/login')
api.add_resource(UserApprovalResource, '/users/pending', '/users/<int:user_id>/approve', '/users/<int:user_id>/reject')


api.add_resource(TaskResource, '/tasks', '/task/<int:task_id>')
api.add_resource(StatsResource, '/stats')
api.add_resource(AssignTaskResource, '/task/<int:task_id>/assign')
api.add_resource(UserManagementResource, '/users')
api.add_resource(UserTaskResource, '/my-tasks')

# ######################################################################################################################################################## #
# ##############################################################  Run  ################################################################################### #

# Register API routes
api.add_resource(SendEmail, '/send-email')
api.add_resource(CacheDemo, '/cache')
api.add_resource(DeleteCache, '/delete-cache')
api.add_resource(QueuedTask, '/queued-task')





if __name__ == '__main__':
    create_admin()
    app.run(debug=True)