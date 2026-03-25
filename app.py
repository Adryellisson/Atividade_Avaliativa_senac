import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for

class BancoSistemaSimples:
    def __init__(self, nome_arquivo):
        self.nome_arquivo = nome_arquivo
        self.criar_tabelas()

    def conectar(self):
        conexao = sqlite3.connect(self.nome_arquivo)
        conexao.row_factory = sqlite3.Row
        return conexao

    def criar_tabelas(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            permission INTEGER NOT NULL DEFAULT 0,
            estado TEXT
        )"""

        sql_usuario_adm = """
        INSERT INTO users (nome, senha, cpf, permission)
        SELECT ?, ?, ?, 1
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE cpf = ?);
        """

        with self.conectar() as conexao:
            conexao.execute(sql)
            adicionar_adm = ('Lulu', 'Hyunjin123', '12345678901')
            conexao.execute(sql_usuario_adm, (*adicionar_adm, adicionar_adm[2]))
            conexao.commit()
        
    def adicionar_usuario(self, nome, senha, cpf):
        sql = "INSERT INTO users (nome, senha, cpf) VALUES (?, ?, ?)"
        with self.conectar() as conexao:
            conexao.execute(sql, (nome, senha, cpf))
            conexao.commit()

    def verificar_login(self, cpf, senha):
        sql = "SELECT * FROM users WHERE cpf = ? AND senha = ?"
        with self.conectar() as conexao:
            return conexao.execute(sql, (cpf, senha)).fetchone()
        
    def atualizar_estado(self, user_id ):
        estado_atual = self.verificar_estado(user_id)
        
        novo_estado = None
        
        if estado_atual is None or estado_atual == "":
            novo_estado = "Pendente"
        elif estado_atual == "Pendente":
            novo_estado = "Em Atendimento"
        elif estado_atual == "Em Atendimento":
            novo_estado = "Concluido"
       
        if novo_estado:
            sql = "UPDATE users SET estado = ? WHERE id = ? AND permission = 0"
            with self.conectar() as conexao:
                conexao.execute(sql, (novo_estado, user_id))
        
    def verificar_estado(self, user_id):
        sql = "SELECT * FROM users WHERE id = ?"
        with self.conectar() as conexao:
            resultado = conexao.execute(sql, (user_id,)).fetchone()
            return resultado["estado"] if resultado else None
        
app = Flask(__name__)
banco = BancoSistemaSimples("banco_de_dados.db")
app.secret_key = "Chave_segura"


@app.route("/", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"].strip()
        senha = request.form["senha"]
        cpf = request.form["cpf"].strip()

        if len(senha) < 8:
           return render_template("cadastro.html", erro="Senha deve ter pelo menos 8 digitos")

        if not cpf.isdigit():
            return render_template("cadastro.html", erro="CPF deve conter apenas números.")
        
        if len(cpf) != 11:
            return render_template("cadastro.html", erro="CPF deve ter 11 números.")

        if not nome.replace(" ", "").isalpha():
            return render_template("cadastro.html", erro="Nome deve conter apenas letras.")

        if nome and senha and cpf:
            try:
                banco.adicionar_usuario(nome, senha, cpf)
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                return render_template("cadastro.html", erro = "CPF já cadastrado. Tente novamente.") 
    return render_template("cadastro.html") 


@app.route("/login", methods=["GET", "POST"])
def login():
    mensagem_erro = request.args.get("erro")

    if request.method == "POST":
        cpf = request.form["cpf"].strip()
        senha = request.form["senha"]


        if len(senha) < 8:
           return render_template("login.html", erro="Senha deve ter pelo menos 8 digitos")
        if not cpf.isdigit():  
            return render_template("login.html", erro="CPF deve conter apenas números.")

        # Mantem CPF com 11 dígitos tambem no login.
        if len(cpf) != 11:
            return render_template("login.html", erro="CPF deve ter 11 números.")

        usuario = banco.verificar_login(cpf, senha)
        if usuario:
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            session["usuario_permission"] = usuario["permission"]
            if session["usuario_permission"] == 1:
                return redirect(url_for("estados_adm"))
            else:
                return redirect(url_for("filas"))
        else:
            return render_template("login.html", erro = "CPF ou senha inválidos. Tente novamente.")
    return render_template("login.html", erro = mensagem_erro)

@app.route("/estados_adm", methods=["GET", "POST"])
def estados_adm():
    user_id = session.get("usuario_id")
    if not user_id:
        return redirect(url_for("login", erro = "Faça login para acessar esta página."))

    if session.get("usuario_permission") != 1:
        return redirect(url_for("filas"))

    if request.method == "POST":
        usuario_id = request.form.get("user_id")
        if usuario_id:
            banco.atualizar_estado(usuario_id)
        return redirect(url_for("estados_adm"))

    with banco.conectar() as conexao:
        usuarios = conexao.execute( "SELECT id, cpf ,nome, estado  FROM users WHERE permission = 0 AND estado IS NOT NULL").fetchall()

    return render_template("estados_adm.html", usuarios=usuarios)

@app.route("/filas", methods=["GET", "POST"])
def filas():
    user_id = session.get("usuario_id")
    if not user_id:
        return redirect(url_for("login"))

    estado = banco.verificar_estado(user_id)
    em_fila = bool(estado)

    if request.method == "POST" and not em_fila:
        banco.atualizar_estado(user_id)
        return redirect(url_for("filas"))
    
    estado = banco.verificar_estado(user_id)
    em_fila = bool(estado)
    
    return render_template("filas.html", estado=estado, em_fila = em_fila)
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)