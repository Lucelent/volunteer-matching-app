from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120))
    skills = db.Column(db.String(300))

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    required_skills = db.Column(db.String(300))

class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteer.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

def match_volunteer_to_roles(volunteer_skills, roles):
    scored_roles = []
    volunteer_skills = [s.strip().lower() for s in volunteer_skills]
    for role in roles:
        required = [s.strip().lower() for s in role.required_skills.split(',')]
        overlap = 0
        for vs in volunteer_skills:
            for rs in required:
                if vs in rs or rs in vs:
                    overlap += 1
        scored_roles.append((role.name, overlap))
    scored_roles.sort(key=lambda x: x[1], reverse=True)
    return scored_roles[:3]
