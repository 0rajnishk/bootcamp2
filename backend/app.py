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


app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type, Authorization'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["JWT_SECRET_KEY"] = "aStrongSecretKey"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

api = Api(app)
jwt = JWTManager(app)
db = SQLAlchemy(app)

CORS(app)



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
# ##############################################################  Routes  ############################################################################### #
api.add_resource(Hello, '/')
api.add_resource(SignupResource, '/signup')
api.add_resource(LoginResource, '/login')
api.add_resource(UserApprovalResource, '/users/pending', '/users/<int:user_id>/approve', '/users/<int:user_id>/reject')


# ######################################################################################################################################################## #
# ##############################################################  Run  ################################################################################### #

if __name__ == '__main__':
    create_admin()
    app.run(debug=True)