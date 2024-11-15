import json
import os
from flask import Flask, render_template, redirect, url_for, request, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'alemao'  # Chave para sessões

# Arquivos JSON
DATA_FILE = 'json/horarios.json'
NOTAS_FILE = 'json/notas.json'

# Horários iniciais
horarios = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00"]
dias_da_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sabado"]

# Função decoradora para proteger rotas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Você precisa fazer login para acessar esta página.", "info")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Página inicial
@app.route('/')
@login_required
def home():
    return render_template('home.html')  # Página inicial


# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'jao123':
            session['logged_in'] = True
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for('home'))
        else:
            flash("Credenciais inválidas. Tente novamente.", "danger")
    if 'logged_in' in session:
        return redirect(url_for('home'))
    return render_template('login.html')


# Página de logout
@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash("Você saiu da sua conta com sucesso!", "info")
    return redirect(url_for('login'))


# Página 404
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# ------------------- Gerenciamento de Horários -------------------
def load_schedule():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            flash("Erro ao carregar os horários! O arquivo pode estar corrompido.", "danger")
    return {dia: [""] * len(horarios) for dia in dias_da_semana}


def save_schedule(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)


@app.route('/horario', methods=['GET', 'POST'])
@login_required
def horario():
    schedule_data = load_schedule()
    if request.method == 'POST':
        for dia in dias_da_semana:
            for i in range(len(horarios)):
                materia = request.form.get(f"materia_{dia}_{i}")
                if materia:
                    schedule_data[dia][i] = materia
        save_schedule(schedule_data)
        flash("Horários atualizados com sucesso!", "success")
    return render_template('pages/horario.html', schedule_data=schedule_data, horarios=horarios, dias_da_semana=dias_da_semana)


# ------------------- Gerenciamento de Notas -------------------
def carregar_notas():
    if os.path.exists(NOTAS_FILE):
        try:
            with open(NOTAS_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            flash("Erro ao carregar as notas! O arquivo pode estar corrompido.", "danger")
    return []


def salvar_notas():
    with open(NOTAS_FILE, 'w') as file:
        json.dump(notas, file, indent=4)


notas = carregar_notas()


@app.route('/ifms', methods=['GET', 'POST'])
@login_required
def ifms():
    notas_concluidas = [nota for nota in notas if nota['concluido']]
    notas_nao_concluidas = [nota for nota in notas if not nota['concluido']]
    return render_template('pages/ifms.html', concluidas=notas_concluidas, nao_concluidas=notas_nao_concluidas)


@app.route('/add', methods=['POST'])
@login_required
def add():
    titulo = request.form['titulo']
    subtitulo = request.form['subtitulo']
    conteudo = request.form['conteudo']
    nova_nota = {
        'id': len(notas) + 1,
        'titulo': titulo,
        'subtitulo': subtitulo,
        'conteudo': conteudo,
        'concluido': False
    }
    notas.append(nova_nota)
    salvar_notas()
    flash("Nota adicionada com sucesso!", "success")
    return redirect(url_for('ifms'))


@app.route('/edit/<int:nota_id>', methods=['POST'])
@login_required
def edit(nota_id):
    for nota in notas:
        if nota['id'] == nota_id:
            nota['titulo'] = request.form['titulo']
            nota['subtitulo'] = request.form['subtitulo']
            nota['conteudo'] = request.form['conteudo']
            break
    salvar_notas()
    flash("Nota editada com sucesso!", "success")
    return redirect(url_for('ifms'))


@app.route('/delete/<int:nota_id>')
@login_required
def delete(nota_id):
    global notas
    notas = [nota for nota in notas if nota['id'] != nota_id]
    salvar_notas()
    flash("Nota excluída com sucesso!", "info")
    return redirect(url_for('ifms'))


@app.route('/toggle/<int:nota_id>')
@login_required
def toggle(nota_id):
    for nota in notas:
        if nota['id'] == nota_id:
            nota['concluido'] = not nota['concluido']
            break
    salvar_notas()
    return redirect(url_for('ifms'))


if __name__ == '__main__':
    app.run(debug=True)
