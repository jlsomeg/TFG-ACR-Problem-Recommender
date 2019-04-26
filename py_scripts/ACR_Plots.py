from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from py_scripts import ELO

import plotly.graph_objs as go
import math

__DB_SPLITTER = 129010

### Plotly Functions

def PLOTLY_BAR_PLOT(x,y, title="", x_label="", y_label=""):
	trace = go.Bar(
		x=x,
		y=y,
		name='Secondary Product',
		marker=dict(
			color='rgb(59, 67, 219)',
		)
	)

	data = [trace]
	layout = go.Layout(
		title=title,
		xaxis=dict(title=x_label, type='category'),
		yaxis=dict(title=y_label)
	)

	#fig = go.Figure(data=data, layout=layout)
	#plot(fig, filename="PLOTLY_BAR_PLOT.html")
	return plot(data, include_plotlyjs=False, output_type='div')

def PLOTLY_LINE_PLOT(x,y, x_range, title="", x_label="", y_label=""):
	trace = go.Scatter(
		x=x,
		y=y,
		mode = "lines+markers")

	layout = go.Layout(
		title=title,
		xaxis=dict(title=x_label, range=x_range),
		yaxis=dict(title=y_label)
	)

	data = [trace]
	fig = go.Figure(data=data, layout=layout)
	#plot(fig, filename="PLOTLY_LINE_PLOT.html")
	return plot(fig, include_plotlyjs=False, output_type='div')

def PLOTLY_SPIDER_PLOT(values, axes, chart_range, title=""):
	data = [go.Scatterpolar(
	  r = values,
	  theta = axes,
	  fill = 'toself'
	)]

	layout = go.Layout(
	title=title,
	polar = dict(
		radialaxis = dict(
		  visible = True,
		  range = chart_range
		)
	  ),
	  showlegend = False
	)

	fig = go.Figure(data=data, layout=layout)
	#plot(fig, filename="PLOTLY_SPIDER_PLOT.html")
	return plot(fig, include_plotlyjs=False, output_type='div')

def PLOTLY_HISTOGRAM_PLOT(x, title="", x_label="", y_label=""):
	data = [
		go.Histogram(
		x = x,
		histnorm="percent",
		xbins = dict(
			end=16, 
		    size=1, 
		    start=0)
		)
	]

	layout = go.Layout(
		title=title,
		xaxis=dict(title=x_label, range=[0,16]),
		yaxis=dict(title=y_label)
	)

	fig = go.Figure(data=data, layout=layout)
	#plot(fig, filename="PLOTLY_HISTOGRAM_PLOT.html")
	return plot(fig, include_plotlyjs=False, output_type='div')
	#plot(data, filename='binning function')

def PLOTLY_PIE_CHART(labels, values, title=""):
	trace = go.Pie(labels=labels, values=values)
	data = [trace]

	layout = go.Layout(
		title=title
	)

	fig = go.Figure(data=data, layout=layout)
	#fig = go.Figure(data=data)
	#plot(fig, filename="PLOTLY_PIE_CHART.html")

	return plot(fig, include_plotlyjs=False, output_type='div')

###  DB Queries

# Done
def GRAPH_ELO_DISTRIBUTION(db_cursor, items):
	db_cursor.execute("""SELECT elo_global FROM {} WHERE elo_global != 8.0""".format('user_scores' if items=='Users' else 'problem_scores'))
	x = []
	for row in db_cursor.fetchall():
		x.append(row[0])

	return PLOTLY_HISTOGRAM_PLOT(x, title="", x_label="", y_label="")

# Done
def GRAPH_ELO_DIFFERENCES(db_cursor, half):
	x = []
	# We get the user/problem couples
	db_cursor.execute("""SELECT s.user_id as u_id, s.problem_id as p_id, u.elo_global as u_elo, p.elo_global as p_elo 
		FROM submission s, user_scores u, problem_scores p
		WHERE s.user_id = u.user_id and s.problem_id = p.problem_id
		AND s.id {} {}
		AND (s.status='AC' OR s.status='PE')
		GROUP BY s.user_id, s.problem_id
		ORDER BY s.id""".format('<=' if half=='fh' else '>', __DB_SPLITTER))
	
	for row in db_cursor.fetchall():
		x.append(abs(row[2] - row[3]))

	return PLOTLY_HISTOGRAM_PLOT(x,title="", x_label="Diferencia de ELOs", y_label="% de Enfrentamientos")

# Done
def GRAPH_TRIES_AVERAGE(db_cursor):
	db_cursor.execute("""SELECT user_id, SUM(CASE 
		WHEN status = 'AC' THEN 1 
		WHEN status = 'PE' THEN 1 
		ELSE 0 END), COUNT(id) FROM submission GROUP BY user_id""")

	num_subm = {}
	for i in range(1,21): num_subm[str(i)] = 0
	num_subm['Más de 20'] = 0
	num_subm['Cero Aciertos'] = 0

	for row in db_cursor.fetchall():
		if row[1] != 0:
			average = math.floor(row[2] / row[1])
			if average < 21:  num_subm[str(average)] += 1
			else: num_subm['Más de 20'] += 1
		else:
			num_subm['Cero Aciertos'] += 1

	x = []
	y1 = []
	y2 = []
	for k,v in num_subm.items():
		x.append(k)
		y1.append(v)

	perc_sum = 0
	for i in y1:
		perc_sum += i
		y2.append((perc_sum/sum(y1))*100)

	return PLOTLY_BAR_PLOT(x,y1, title="", x_label="", y_label="")

# Done - Not for web
def GRAPH_EXPECTATION_DIFF():
	subject_elos = [16,8,0] # ELO values to test (as users)
	testing_elos = [round(i*0.1,1) for i in range(0,161)] # ELOs from 0 to 16 (as problems)
	expectations = []

	for i,usr_elo in enumerate(subject_elos):
		for prb_elo in testing_elos:
			expectations.append(ELO.EXPECTATION(usr_elo,prb_elo))

		return PLOTLY_LINE_PLOT(testing_elos,expectations,[0,16],title=f"Expectation for a user with ELO {usr_elo}")
		expectations.clear()

# Done
def GRAPH_SUBMISSIONS_PER_MONTHS(db_cursor):
	months_data = {}
	[months_data.update({k:0}) for k in range(1,13)]
	db_cursor.execute("SELECT submissionDate FROM submission ORDER BY submissionDate ASC")

	for r in db_cursor.fetchall():
		months_data[int(str(r[0]).split('-')[1])] += 1

	months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
	values = []

	for k,v in months_data.items(): values.append(v)
	return PLOTLY_BAR_PLOT(months,values)

# Done
def GRAPH_USERS_EVOLUTION(db_cursor, user_id):
	db_cursor.execute("""SELECT * FROM submission 
	WHERE user_id = {}
	AND user_elo IS NOT NULL 
	ORDER BY id""".format(user_id))
	
	y = [x[7] for x in db_cursor.fetchall()]
	y.insert(0,8)

	return PLOTLY_LINE_PLOT([x for x in range(len(y))], y, [0,len(y)], title="Evolución de tu Puntuación ELO", x_label="", y_label="Puntuación ELO")

# Done
def GRAPH_PROBLEMS_EVOLUTION(db_cursor, problem_id):
	db_cursor.execute("""SELECT * FROM submission 
		WHERE problem_id = {}
		AND problem_elo IS NOT NULL 
		ORDER BY id""".format(problem_id))

	y = [x[8] for x in db_cursor.fetchall()]
	y.insert(0,8)

	return PLOTLY_LINE_PLOT([x for x in range(len(y))], y, [0,len(y)])

# Done
def GRAPH_USER_CATEGORIES(db_cursor, user_id):
	db_cursor.execute("""SELECT * FROM User_Scores WHERE user_id = {}""".format(user_id))
	row = db_cursor.fetchall()[0]
	values = [i for i in row[2:]]
	values.append(values[0])
	axes = ['Ad-hoc', 'Recorridos', 'Búsqueda', 'Búsqueda Binaria', 'Ordenación', 'Algoritmos voraces','Programación dinámica',
	'Divide y vencerás','Búsqueda exhaustiva, vuelta atrás','Búsqueda en el espacio de soluciones','Grafos','Geometría','Ad-hoc']
	return PLOTLY_SPIDER_PLOT(values, axes, [0,16], title="ELO por Categoría")

# Done
def GRAPH_USER_PROBLEM_PROGRESS(db_cursor, user_id):
	
	values = []

	# Problems solved by the user
	db_cursor.execute("""SELECT user_id, SUM(CASE 
		WHEN status = 'AC' THEN 1 
		WHEN status = 'PE' THEN 1 
		ELSE 0 END) FROM submission 
		WHERE user_id = {}
		GROUP BY user_id""".format(user_id))

	values.append(db_cursor.fetchone()[1])

	# Problems tried by the user
	db_cursor.execute("""SELECT user_id, COUNT(DISTINCT(problem_id)) FROM submission 
		WHERE user_id = {}
		GROUP BY user_id""".format(user_id))
	
	values.append(db_cursor.fetchone()[1] - values[0])

	# Nº of problems
	db_cursor.execute("""SELECT COUNT(*) FROM problem_scores""")

	values.append(db_cursor.fetchone()[0] - values[1] - values[0])

	labels=['Resueltos', 'Intentados', 'Por Hacer']

	return PLOTLY_PIE_CHART(labels, values, title="Progreso Total")
