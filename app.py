from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
import json
import os
import matplotlib.pyplot as plt
import networkx as nx
import io
import base64

app = Flask(__name__)
app.secret_key = 'clave_secreta'

NAMES = [
    "ANDRADE REYES JUSTINO JUAN CARLOS", "ANZURES CAMPOS OMAR", "BAUTISTA ARROYO DAVID",
    "CAMACHO SANTANA BRENDA SOFIA", "COYOTL  MARCELINO  ANGEL HOMAR", "DOMINGUEZ CASTILLO SALVADOR ESTEBAN",
    "GAYOSSO MARTINEZ CARLOS JAVIER", "GOIZ SARMIENTO MAURICIO", "GONZALEZ   HERRERA LUIS GABRIEL",
    "HERNANDEZ GARZA JHONNATAN", "HERNANDEZ VELEZ LIZETH", "JIMENEZ ROSAS ALBERTO", "JUAREZ SUAREZ RAUL",
    "MARTINEZ CALLEJO BRANDON", "MARTINEZ MANZANO LEONARDO", "MERINO LUNA JUAN CARLOS", "MORENO TELLEZ  KAREN",
    "NEGRETE AGUILAR DANIEL ESAU", "ORTEGA  SANCHEZ FERNANDO", "PEREZ JIMENEZ FATIMA", "POPOCA COATL MAURICIO",
    "PORTADA GONZALEZ MARICRUZ", "RAMIREZ CLEMENTE JESUS", "ROJAS CORTES RODRIGO ZURIEL",
    "ROQUE  CRUZ  ALDRIN JAFET", "TRUJILLO ALVAREZ ERIK"
]

QUESTIONS = [
    "¿A quién elegirías para realizar un proyecto de programación?",
    "¿A quién descartarías para que te diera asesorías de programación?",
    "¿Si se descompone tu computadora a quién recurrirías para que te ayude a repararla?",
    "¿A cuál de tus compañeros evitarías si tu equipo de cómputo tuviera alguna falla?",
    "Si vas a presentar un proyecto a tu cliente, ¿a quién elegirías para que lo exponga?",
    "Si un cliente llega  a tu empresa y pide que le expliquen su método de trabajo, ¿a quién no le pedirías que hablara con él?",
    "¿A cuál de tus compañeros elegirías para documentar un trabajo?",
    "¿A quién evitarías preguntarle cuando tienes dudas de ortografía o redacción?",
    "¿A quién elegirías para que te apoye en un trabajo como freelance?",
    "¿A quién evitarías recomendar en un puesto de trabajo?",
    "Si vas a un congreso fuera de tu estado,  ¿Con quién te gustaría compartir habitación?",
    "Si vas a un evento fuera de tu ciudad,  ¿Con quién evitarías compartir habitación?",
    "¿A quién le pedirías que te ayude a organizar una fiesta?",
    "¿Quién sería la persona menos adecuada para organizar un evento?",
    "¿A quién le compartirías un secreto?",
    "¿A quién evitarías contarle algo importante para ti?",
    "¿A quién le contraerías un secreto pero con la seguridad de que se enteraría todo el salón?",
    "¿A quién recurres cuando necesitas un consejo?",
    "Si tuvieras un conflicto legal, ¿A quién le pedirías que te ayude a resolver tu caso?",
    "Si tuvieras un problema con la policía, ¿a quién NO le pedirías ayuda?"
]

RESPUESTAS_FILE = "respuestas.json"

@app.route('/')
def index():
    return render_template('formulario.html', names=NAMES, questions=QUESTIONS)

@app.route('/enviar', methods=['POST'])
def enviar():
    alumno_idx = request.form.get('student_number')
    if alumno_idx is None:
        flash("Debes seleccionar tu nombre.")
        return render_template('formulario.html', names=NAMES, questions=QUESTIONS, previous=request.form)
    alumno_idx = int(alumno_idx)

    respuestas = {'student_number': alumno_idx}
    for i in range(len(QUESTIONS)):
        opciones = [
            request.form.get(f"q{i+1}_opt1"),
            request.form.get(f"q{i+1}_opt2"),
            request.form.get(f"q{i+1}_opt3"),
        ]
        if None in opciones or "" in opciones:
            flash(f"Completa todas las opciones en la pregunta {i+1}.")
            return render_template('formulario.html', names=NAMES, questions=QUESTIONS, previous=request.form)
        if len(set(opciones)) < 3:
            flash(f"En la pregunta {i+1}, las opciones deben ser diferentes.")
            return render_template('formulario.html', names=NAMES, questions=QUESTIONS, previous=request.form)
        if str(alumno_idx) in opciones:
            flash(f"No puedes elegirte a ti mismo en la pregunta {i+1}.")
            return render_template('formulario.html', names=NAMES, questions=QUESTIONS, previous=request.form)

        respuestas[f"q{i+1}"] = opciones

    nombre = NAMES[alumno_idx]

    if os.path.exists(RESPUESTAS_FILE):
        with open(RESPUESTAS_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    if nombre in data:
        flash("Ya has enviado tus respuestas anteriormente.")
        return redirect(url_for('index'))

    data[nombre] = respuestas

    with open(RESPUESTAS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    return render_template('gracias.html')

@app.route('/admin')
def admin():
    pw = request.args.get('pw')
    if pw != 'admin':
        return "Acceso denegado"
    if not os.path.exists(RESPUESTAS_FILE):
        return "Aún no hay respuestas registradas."
    with open(RESPUESTAS_FILE, 'r') as f:
        data = json.load(f)
    return render_template('admin.html', data=data)

@app.route('/borrar')
def borrar():
    pw = request.args.get('pw')
    if pw == 'admin' and os.path.exists(RESPUESTAS_FILE):
        os.remove(RESPUESTAS_FILE)
        return "Respuestas eliminadas."
    return "Acceso denegado."

@app.route('/resultados', methods=['GET', 'POST'])
def resultados():
    PASSWORD = 'babis2175'

    if request.method == 'POST':
        if request.form.get('password') != PASSWORD:
            return render_template('login.html', error='Contraseña incorrecta')
        session['logged_in'] = True
        return redirect(url_for('resultados'))

    if not session.get('logged_in'):
        return render_template('login.html', error=None)

    if not os.path.exists(RESPUESTAS_FILE):
        return 'No hay respuestas guardadas.'

    with open(RESPUESTAS_FILE, 'r') as f:
        data = json.load(f)

    resultados_por_pregunta = []
    for i, pregunta in enumerate(QUESTIONS, start=1):
        puntos_por_persona = {name: 0 for name in NAMES}
        for respuestas in data.values():
            seleccionados = respuestas.get(f"q{i}", [])
            if len(seleccionados) == 3:
                nombre1 = NAMES[int(seleccionados[0])]
                nombre2 = NAMES[int(seleccionados[1])]
                nombre3 = NAMES[int(seleccionados[2])]
                puntos_por_persona[nombre1] += 3
                puntos_por_persona[nombre2] += 2
                puntos_por_persona[nombre3] += 1
        ordenado = sorted(puntos_por_persona.items(), key=lambda x: x[1], reverse=True)
        resultados_por_pregunta.append((pregunta, ordenado))

    return render_template('resultados.html', resultados=resultados_por_pregunta)

@app.route('/grafo')
def grafo():
    if not session.get('logged_in'):
        return redirect(url_for('resultados'))

    if not os.path.exists(RESPUESTAS_FILE):
        return 'No hay respuestas guardadas.'

    with open(RESPUESTAS_FILE, 'r') as f:
        data = json.load(f)

    G = nx.DiGraph()

    for respuestas in data.values():
        alumno_idx = int(respuestas['student_number'])
        for i in range(1, len(QUESTIONS)+1):
            seleccionados = respuestas.get(f'q{i}', [])
            pesos = [3, 2, 1]
            for seleccionado, peso in zip(seleccionados, pesos):
                if seleccionado and seleccionado != str(alumno_idx):
                    seleccionado_idx = int(seleccionado)
                    if G.has_edge(alumno_idx, seleccionado_idx):
                        G[alumno_idx][seleccionado_idx]['weight'] += peso
                    else:
                        G.add_edge(alumno_idx, seleccionado_idx, weight=peso)

    pos = nx.spring_layout(G, seed=42)

    # Personalización del gráfico
    plt.figure(figsize=(12, 10))
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]

    # Dibujar nodos más grandes con color vivo
    nx.draw_networkx_nodes(
        G,
        pos,
        node_color="#796B81",    # color de relleno del nodo
        edgecolors="#2A11CE",      # color del contorno
        linewidths=6.5,           # grosor del contorno
        node_size=2000
    )

    # Dibujar aristas más gruesas
    nx.draw_networkx_edges(G, pos, width=3, arrows=True, arrowstyle='->', edge_color='gray')

    # Dibujar etiquetas de los nodos con tipografía decorativa (si está disponible)
    nx.draw_networkx_labels(G, pos, font_size=20, font_family='Segoe Print', font_weight='bold', font_color='white')

    # No mostrar etiquetas de los pesos en las aristas
    # nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): w for u, v, w in G.edges(data='weight')})

    plt.axis('off')
    plt.title("Sociograma - Gráfica de Relaciones", fontsize=16, fontweight='bold')

    # Convertir a imagen base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()

    return render_template('grafo.html', image_data=img_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

