import sqlite3
from flask import Flask, redirect, render_template, request, session, url_for

class BancoDeDados:

    def __init__(self, nome_arquivo):
        self.nome_arquivo = nome_arquivo
        self.criar_tabelas()
        
    def conectar(self):
        conexao = sqlite3.connect(self.nome_arquivo)
        conexao.row_factory = sqlite3.Row
        return conexao
    
    def criar_tabelas(self):
        sql = """
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            preco REAL NOT NULL 
        )        
        """
        with self.conectar() as conexao:
            conexao.execute(sql)
            conexao.commit() 

    def adicionar_produto(self, nome, descricao, preco):
        sql = "INSERT INTO produtos (nome, descricao, preco) VALUES (?, ?, ?)"
        with self.conectar() as conexao:
            conexao.execute(sql, (nome, descricao, preco))
            conexao.commit()

    def listar_produtos(self):
        sql = """
        SELECT * FROM produtos 
        ORDER BY nome
        """
        with self.conectar() as conexao:
            resultados = conexao.execute(sql).fetchall()
            return [dict(linha) for linha in resultados]
    
    def buscar_por_id(self, id):
        sql = "SELECT * FROM produtos WHERE id = ?" 
        with self.conectar() as conexao:
            retorno = conexao.execute(sql, (id,)).fetchone()
            if retorno:
                return dict(retorno)
            else: 
                return "Vazio" 

app = Flask(__name__)
banco = BancoDeDados("produtos.db")

@app.route("/")
def index(): 
    produtos = banco.listar_produtos()
    return render_template("index.html", produtos=produtos)

@app.route("/cadastro", methods=["POST", "GET"])
def cadastro(): 
     
    if request.method == "POST":
        nome = request.form.get("nome")
        descricao = request.form.get("descricao")
        preco = request.form.get("preco")
        
        if not preco.isdigit():
            return render_template("cadastro.html", erro = "Por favor digite um preço válido! ")
        
        if (len(nome) > 100) and not nome.isalpha():
            return render_template("cadastro.html", erro = "Por favor digite um nome com até 100 caracteres e se lembre que não pode ter números!") 
        
        if len(descricao) >= 350:
            return render_template("cadastro.html", erro = "Por favor digite uma descrição com até 350 caracteres!")

        banco.adicionar_produto(nome, descricao, preco)
        return redirect(url_for('index'))
    
    return render_template("cadastro.html") 

@app.route("/detalhes/<int:id_produto>")
def detalhes(id_produto):
  
    produto = banco.buscar_por_id(id_produto)
  
    if produto == "Vazio":
        return redirect(url_for('index', erro = "Produto não encotrado"))
    
    return render_template("detalhe.html", produto=produto)

if __name__ == "__main__":
    app.run(debug=True)