import io
import csv
import base64
from itertools import combinations
from flask import Flask, render_template, request, redirect, url_for, Response
from models import db, Volunteer, Role, match_volunteer_to_roles
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize DB
with app.app_context():
    db.create_all()

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
    return redirect(url_for('hr_dashboard'))

@app.route('/analytics/')
@app.route('/analytics')
def analytics():
    volunteers = Volunteer.query.all()
    roles = Role.query.all()
    total_volunteers = len(volunteers)
    total_roles = len(roles)
    all_skills = []
    volunteer_skills_list = []

    for v in volunteers:
        skills = [s.strip() for s in v.skills.split(',') if s.strip()]
        volunteer_skills_list.append(skills)
        all_skills.extend(skills)

    skill_count = {s: all_skills.count(s) for s in set(all_skills)}
    unique_skills = sorted(skill_count.keys())

    # --- Histogram plot (skill counts) ---
    fig1, ax1 = plt.subplots(figsize=(8,4))
    skills = list(skill_count.keys())
    counts = list(skill_count.values())
    ax1.bar(skills, counts, color='steelblue')
    ax1.set_xlabel('Skills')
    ax1.set_ylabel('Number of Volunteers')
    ax1.set_title('Volunteer Skill Distribution')
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
    plt.tight_layout()

    img1 = io.BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plot_url_histogram = base64.b64encode(img1.getvalue()).decode()
    plt.close(fig1)

    # --- Skill Co-occurrence Heatmap ---

    skill_idx = {skill: i for i, skill in enumerate(unique_skills)}
    n = len(unique_skills)
    matrix = np.zeros((n, n), dtype=int)

    for skills in volunteer_skills_list:
        unique_vol_skills = sorted(set(skills))
        for s in unique_vol_skills:
            matrix[skill_idx[s], skill_idx[s]] += 1
        for a, b in combinations(unique_vol_skills, 2):
            i, j = skill_idx[a], skill_idx[b]
            matrix[i, j] += 1
            matrix[j, i] += 1

    fig2, ax2 = plt.subplots(figsize=(8, 8))
    cax = ax2.imshow(matrix, cmap='YlGnBu')
    ax2.set_xticks(range(n))
    ax2.set_yticks(range(n))
    ax2.set_xticklabels(unique_skills, rotation=90)
    ax2.set_yticklabels(unique_skills)
    ax2.set_title('Skill Co-occurrence Heatmap')
    plt.colorbar(cax, ax=ax2, fraction=0.046, pad=0.04)
    plt.tight_layout()

    img2 = io.BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)
    plot_url_heatmap = base64.b64encode(img2.getvalue()).decode()
    plt.close(fig2)

    return render_template('analytics.html',
                           total_volunteers=total_volunteers,
                           total_roles=total_roles,
                           skill_count=skill_count,
                           plot_url_histogram=plot_url_histogram,
                           plot_url_heatmap=plot_url_heatmap)

@app.route('/analytics/download_csv')
def download_csv():
    volunteers = Volunteer.query.all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Volunteer Name', 'Email', 'Skills'])
    for v in volunteers:
        writer.writerow([v.name, v.email, v.skills])

    writer.writerow([])

    all_skills = []
    volunteer_skills_list = []
    for v in volunteers:
        skills = [s.strip() for s in v.skills.split(',') if s.strip()]
        volunteer_skills_list.append(skills)
        all_skills.extend(skills)
    unique_skills = sorted(set(all_skills))

    pair_counts = {}
    for skills in volunteer_skills_list:
        for pair in combinations(sorted(set(skills)), 2):
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

    writer.writerow(['Skill A', 'Skill B', 'Count'])
    for (skill_a, skill_b), count in sorted(pair_counts.items()):
        writer.writerow([skill_a, skill_b, count])

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=volunteers_with_heatmap.csv"}
    )


if __name__ == "__main__":
    app.run(debug=True)
