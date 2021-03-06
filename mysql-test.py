from flask import Flask, render_template, request, url_for, flash, redirect
from forms import UserInsertForm, ProblemInsertForm, SubmissionForm, ELOSelectionForm
from py_scripts import ACR_Plots as pl
from py_scripts import DB_Functions as db

app = Flask(__name__)
app.config['SECRET_KEY'] = '5404d19eaf645951b91dae10a842be5b'
db.ELO_TYPE()

### Dashes

@app.route('/')
@app.route('/stats')
def dash_general():
	bar_submissions_per_month = pl.GRAPH_SUBMISSIONS_PER_MONTHS()				# Submissions per month / year (in HTML code)
	hist_users_elo_distribution = pl.GRAPH_ELO_DISTRIBUTION('Usuarios')		# Users ELO distribution histogram (in HTML code)
	hist_problems_elo_distribution = pl.GRAPH_ELO_DISTRIBUTION('Problemas')	# Problems ELO distribution histogram (in HTML code)
	bars_tries_till_solved = pl.GRAPH_TRIES_AVERAGE()

	return render_template('db_stats.html', subm_per_month=bar_submissions_per_month, user_distribution=hist_users_elo_distribution, 
		problem_distribution=hist_problems_elo_distribution, tries_average=bars_tries_till_solved)

@app.route('/problem_list')
def list_problems():
	problems, stats, categories = db.problem_list()
	return render_template('problem_list.html', item_list=problems, stats=stats, categories=categories)

@app.route('/user_list')
def list_users():
	users = db.user_list()
	return render_template('user_list.html', item_list=users)

@app.route('/user/<user_id>')
def dash_user(user_id):
	user_submissions = db.user_submissions(user_id)									# List of the user's latest submissions
	plot_user_evolution = pl.GRAPH_USERS_EVOLUTION(user_id)		# User ELO evolution plot (in HTML code)
	plot_user_progress = pl.GRAPH_USER_PROBLEM_PROGRESS(user_id) 	# user problem completion pie chart (in HTML code)
	plot_user_categories = pl.GRAPH_USER_CATEGORIES(user_id) 		# User ELOs per category (in HTML code)
	user_recommendations = db.RECOMMENDATIONS(user_id)

	return render_template('user_dash.html', id=user_id ,evolution=plot_user_evolution, progress=plot_user_progress, 
		categories=plot_user_categories, user_id=user_id, user_submissions=user_submissions, user_recommendations=user_recommendations)

@app.route('/problem/<problem_id>')
def dash_problems(problem_id):
	last_submissions = db.problem_latest_submissions(problem_id)						# Latest submissions
	fav_language = pl.GRAPH_PROBLEM_LANGUAGES(problem_id)
	plot_problem_evolution = pl.GRAPH_PROBLEMS_EVOLUTION(problem_id)	# Problem ELO evolution plot (in HTML code)
	plot_user_progress = pl.GRAPH_PROBLEM_SOLVE_RATIO(problem_id)  		# problem completion pie chart (in HTML code)
	plot_problem_tries = pl.TRIES_PER_PROBLEM(problem_id)  		# problem completion pie chart (in HTML code)
	return render_template('problem_dash.html',id=problem_id , evolution=plot_problem_evolution, problem_tries=plot_problem_tries,
		progress=plot_user_progress, problem_id=problem_id, last_submissions=last_submissions, fav_language=fav_language)

### Inserts

@app.route("/insert_user", methods=['GET', 'POST'])
def insert_user():
	form = UserInsertForm()

	if form.validate_on_submit():
		try:
			db.insert_user(form.user.data, form.elo.data)
			flash(f'Usuario con ID {form.user.data} añadido!', 'success')
		except RuntimeError as err:
			flash("ERROR: {}".format(err.args[0]), 'danger')
		finally:
			return redirect(url_for('insert_user'))

	return render_template('insert_user.html', form=form)

@app.route("/insert_problem", methods=['GET', 'POST'])
def insert_problem():
	form = ProblemInsertForm()
	if form.validate_on_submit():
		try:
			db.insert_problem(form.problem.data, form.elo.data, form.title.data, form.categories.data)
			flash(f'Problema con ID {form.problem.data} añadido!', 'success')
		except RuntimeError as err:
			flash("ERROR: {}".format(err.args[0]), 'danger')
		finally:
			return redirect(url_for('insert_problem'))
	return render_template('insert_problem.html', form=form)

### Simulation

@app.route("/submission", methods=['GET', 'POST'])
def simulate_submission():
	form = SubmissionForm()

	if form.validate_on_submit():
		try:
			db.insert_submission(form.user.data, form.problem.data, form.language.data, form.status.data)
			flash(f'Envio realizado con exito!', 'success')
		except RuntimeError as err:
			flash("ERROR: {}".format(err.args[0]), 'danger')
		finally:
			return redirect(url_for('simulate_submission'))

	return render_template('submission.html', form=form)

### Other

@app.route("/change", methods=['GET', 'POST'])
def elo_change():
	form = ELOSelectionForm()
	if form.validate_on_submit():
		try:
			db.RE_CALCULATE_ELOS(form.elo_type.data)
			flash(f'Se ha cambiado la fórmula de ELO al Tipo {form.elo_type.data}!', 'success')
		except RuntimeError as err:
			flash("ERROR: {}".format(err.args[0]), 'danger')
		finally:
			return redirect(url_for('elo_change'))
	return render_template('elo_change.html', form=form, elo_type=db.__elo_type)

@app.route("/easiest", methods=['GET', 'POST'])
def list_easiest_problems():
	easiest, stats = db.get_easiest_problems()
	return render_template('easiest_list.html', item_list=easiest, stats=stats)

if __name__ == '__main__':
	app.run(port=8181, host="0.0.0.0")
	#app.run(host='127.0.0.1')