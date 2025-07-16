from flask import Flask, render_template, request, redirect, url_for
from models import db, Volunteer, Role, Placement, match_volunteer_to_roles

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize DB
with app.app_context():
    db.create_all()

# ✅ NEW: Homepage redirects to Volunteer Portal
@app.route('/')
def home():
    return redirect('/volunteer')

@app.route('/volunteer', methods=['GET', 'POST'])
def volunteer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        selected_skills = request.form.getlist('skills')
        skills = ', '.join(selected_skills)
        volunteer = Volunteer(name=name, email=email, skills=skills)
        db.session.add(volunteer)
        db.session.commit()
        return redirect(url_for('volunteer'))
    volunteers = Volunteer.query.all()
    return render_template('volunteer.html', volunteers=volunteers)

@app.route('/edit-volunteer/<int:volunteer_id>', methods=['GET', 'POST'])
def edit_volunteer(volunteer_id):
    volunteer = Volunteer.query.get_or_404(volunteer_id)
    if request.method == 'POST':
        volunteer.name = request.form['name']
        volunteer.email = request.form['email']
        selected_skills = request.form.getlist('skills')
        volunteer.skills = ', '.join(selected_skills)
        db.session.commit()
        return redirect(url_for('volunteer'))
    
    all_skills = [
        "event planning", "logistics", "social media", "marketing",
        "data entry", "excel", "public speaking", "networking"
    ]
    selected_skills = [s.strip() for s in volunteer.skills.split(',')]
    return render_template('edit_volunteer.html',
                           volunteer=volunteer,
                           all_skills=all_skills,
                           selected_skills=selected_skills)

@app.route('/delete-volunteer/<int:volunteer_id>')
def delete_volunteer(volunteer_id):
    volunteer = Volunteer.query.get_or_404(volunteer_id)
    db.session.delete(volunteer)
    db.session.commit()
    return redirect(url_for('volunteer'))

@app.route('/hr-dashboard')
def hr_dashboard():
    volunteers = Volunteer.query.all()
    roles = Role.query.all()
    matches = {}
    for v in volunteers:
        top_roles = match_volunteer_to_roles(v.skills.split(','), roles)
        matches[v.id] = top_roles
    return render_template('hr_dashboard.html', volunteers=volunteers, matches=matches)

@app.route('/analytics')
def analytics():
    volunteers = Volunteer.query.all()
    roles = Role.query.all()
    total_volunteers = len(volunteers)
    total_roles = len(roles)
    all_skills = []
    for v in volunteers:
        all_skills += v.skills.split(',')
    skill_count = {s.strip(): all_skills.count(s.strip()) for s in all_skills}
    return render_template('analytics.html',
                           total_volunteers=total_volunteers,
                           total_roles=total_roles,
                           skill_count=skill_count)

@app.route('/seed-roles')
def seed_roles():
    sample_roles = [
        ("Event Coordinator", "event planning, logistics"),
        ("Social Media Manager", "social media, marketing"),
        ("Data Entry Volunteer", "data entry, excel, accuracy"),
        ("Community Outreach", "public speaking, networking, social media")
    ]
    for r in sample_roles:
        db.session.add(Role(name=r[0], required_skills=r[1]))
    db.session.commit()
    return "Roles seeded! Go back to /hr-dashboard"

if __name__ == "__main__":
    app.run(debug=True)
