from flask import Flask, request, render_template, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# A chave secreta deve ser uma string longa e complexa, gerada aleatoriamente
# e mantida em segredo. NUNCA use 'segredo' em produção!
app.secret_key = 'segredo1234567890'

# Configurações do banco de dados
DB_HOST = "localhost"
DB_USER = "patrick"
DB_PASSWORD = "rush211275"
DB_NAME = "clinica_cris_moro"

def conectar_db():
    """Tenta conectar ao banco de dados MySQL e retorna o objeto de conexão."""
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if mydb.is_connected():
            print("Conexão com o MySQL estabelecida com sucesso.")
        return mydb
    except Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        return None

def fechar_db(mydb):
    """Fecha a conexão com o banco de dados se estiver aberta."""
    if mydb and mydb.is_connected():
        mydb.close()
        print("Conexão com o MySQL fechada.")

def obter_id(mydb, tabela, coluna, valor):
    """
    Obtém o ID de um valor em uma tabela específica, ou None se não existir.
    Evita a criação de múltiplos registros duplicados.
    """
    mycursor = mydb.cursor()
    sql = f"SELECT id FROM {tabela} WHERE {coluna} = %s"
    mycursor.execute(sql, (valor,))
    resultado = mycursor.fetchone()
    mycursor.close()
    return resultado[0] if resultado else None

def inserir_e_obter_id(mydb, tabela, coluna, valor):
    """
    Insere um valor em uma tabela se não existir e retorna o ID.
    Útil para tabelas de lookup como 'Motivacao' ou 'AreaInteresse'.
    """
    if not valor:  # Evita inserir valores vazios/nulos
        return None
    id_existente = obter_id(mydb, tabela, coluna, valor)
    if id_existente:
        return id_existente
    else:
        mycursor = mydb.cursor()
        try:
            sql = f"INSERT INTO {tabela} ({coluna}) VALUES (%s)"
            mycursor.execute(sql, (valor,))
            mydb.commit()
            return mycursor.lastrowid
        except Error as err:
            print(f"Erro ao inserir '{valor}' na tabela '{tabela}': {err}")
            mydb.rollback() # Garante que a transação seja desfeita em caso de erro
            return None
        finally:
            mycursor.close()

@app.route('/')
def index():
    """Renderiza a página inicial (formulário de cadastro)."""
    return render_template('index.html')

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    """Processa o formulário de cadastro de paciente."""
    if request.method == 'POST':
        # Coleta de dados do formulário
        nome = request.form.get('nome')
        endereco = request.form.get('endereco')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        motivo_consulta = request.form.get('motivo_consulta')
        tratamento_previo = request.form.get('tratamento_previo')
        motivos = request.form.getlist('motivos[]')
        area_interesse = request.form.getlist('area_interesse[]')
        historico_saude = request.form.get('historico_saude')
        tipo_sanguineo = request.form.get('tipo_sanguineo')
        teve_covid = request.form.get('teve-covid')
        vacina_covid = request.form.get('vacina-covid')
        historico_doencas = request.form.getlist('historico-doencas[]')
        situacao_saude_radio = request.form.get('situacao_saude')
        cansaco_excessivo_radio = request.form.get('cansaco_excessivo')
        pratica_fisica = request.form.get('pratica_fisica')
        alimentacao_radio = request.form.get('alimentacao')
        dieta_radio = request.form.get('dieta')
        bebida_radio = request.form.get('bebida')
        alimentacao_rotina = request.form.get('alimentacao_rotina')
        idade_menarca = request.form.get('idade_menarca')
        ciclo_menstrual = request.form.get('ciclo_menstrual')
        contraceptivo_radio = request.form.get('contraceptivo')
        tipo_contraceptivo = request.form.get('tipo-contraceptivo')

        mydb = conectar_db()
        if not mydb:
            flash("Erro ao conectar ao banco de dados. Tente novamente mais tarde.", "error")
            return redirect(url_for('index'))

        mycursor = mydb.cursor()

        try:
            # Converte 'sim'/'não' para booleano ou None para o banco de dados
            teve_covid_db = 1 if teve_covid == 'sim' else (0 if teve_covid == 'nao' else None)
            vacina_covid_db = 1 if vacina_covid == 'sim' else (0 if vacina_covid == 'nao' else None)
            usa_contraceptivo_db = 1 if contraceptivo_radio == 'sim' else (0 if contraceptivo_radio == 'nao' else None)
            retencao_liquidos_db = 1 if situacao_saude_radio == 'sim' else (0 if situacao_saude_radio == 'nao' else None)
            cansaco_excessivo_db = 1 if cansaco_excessivo_radio == 'sim' else (0 if cansaco_excessivo_radio == 'nao' else None)
            ja_seguiu_dieta_db = 1 if dieta_radio == 'sim' else (0 if dieta_radio == 'nao' else None)
            bebe_liquidos_refeicoes_db = 1 if bebida_radio == 'sim' else (0 if bebida_radio == 'nao' else None)

            # Inserir Paciente
            sql_paciente = """
                INSERT INTO Paciente (nome, endereco, email, telefone, tipo_sanguineo,
                                      teve_covid, vacina_covid, idade_menarca, ciclo_menstrual,
                                      usa_contraceptivo, tipo_contraceptivo, tratamento_previo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            val_paciente = (nome, endereco, email, telefone, tipo_sanguineo,
                            teve_covid_db, vacina_covid_db,
                            int(idade_menarca) if idade_menarca else None, ciclo_menstrual,
                            usa_contraceptivo_db, tipo_contraceptivo, tratamento_previo)
            mycursor.execute(sql_paciente, val_paciente)
            paciente_id = mycursor.lastrowid

            if not paciente_id:
                raise Error("Não foi possível obter o ID do paciente recém-inserido.")

            # Inserir HistoricoSaude
            sql_historico_saude = "INSERT INTO HistoricoSaude (paciente_id, condicao_saude, motivo_consulta) VALUES (%s, %s, %s)"
            val_historico_saude = (paciente_id, historico_saude, motivo_consulta)
            mycursor.execute(sql_historico_saude, val_historico_saude)

            # Relacionar com a tabela Motivacao
            for motivo in motivos:
                motivacao_id = inserir_e_obter_id(mydb, 'Motivacao', 'descricao', motivo)
                if motivacao_id:
                    sql_paciente_motivacao = "INSERT INTO PacienteMotivacao (paciente_id, motivacao_id) VALUES (%s, %s)"
                    val_paciente_motivacao = (paciente_id, motivacao_id)
                    mycursor.execute(sql_paciente_motivacao, val_paciente_motivacao)

            # Relacionar com a tabela AreaInteresse
            for area in area_interesse:
                area_interesse_id = inserir_e_obter_id(mydb, 'AreaInteresse', 'descricao', area)
                if area_interesse_id:
                    sql_paciente_area_interesse = "INSERT INTO PacienteAreaInteresse (paciente_id, area_interesse_id) VALUES (%s, %s)"
                    val_paciente_area_interesse = (paciente_id, area_interesse_id)
                    mycursor.execute(sql_paciente_area_interesse, val_paciente_area_interesse)

            # Relacionar com a tabela DoencaFamiliar
            for doenca in historico_doencas:
                doenca_familiar_id = inserir_e_obter_id(mydb, 'DoencaFamiliar', 'nome_doenca', doenca)
                if doenca_familiar_id:
                    sql_paciente_doenca_familiar = "INSERT INTO PacienteDoencaFamiliar (paciente_id, doenca_familiar_id) VALUES (%s, %s)"
                    val_paciente_doenca_familiar = (paciente_id, doenca_familiar_id)
                    mycursor.execute(sql_paciente_doenca_familiar, val_paciente_doenca_familiar)

            # Inserir dados em SaudeBemEstar
            sql_saude_bem_estar = """
                INSERT INTO SaudeBemEstar (paciente_id, retencao_liquidos, cansaco_excessivo, pratica_atividade_fisica)
                VALUES (%s, %s, %s, %s)
            """
            val_saude_bem_estar = (paciente_id, retencao_liquidos_db, cansaco_excessivo_db, pratica_fisica)
            mycursor.execute(sql_saude_bem_estar, val_saude_bem_estar)

            # Inserir dados em AlimentacaoRotina
            sql_alimentacao_rotina = """
                INSERT INTO AlimentacaoRotina (paciente_id, definicao_alimentacao, ja_seguiu_dieta,
                                               bebe_liquidos_refeicoes, aversao_alimentar)
                VALUES (%s, %s, %s, %s, %s)
            """
            val_alimentacao_rotina = (paciente_id, alimentacao_radio,
                                      ja_seguiu_dieta_db,
                                      bebe_liquidos_refeicoes_db,
                                      alimentacao_rotina)
            mycursor.execute(sql_alimentacao_rotina, val_alimentacao_rotina)

            mydb.commit()
            flash("Dados do paciente cadastrados com sucesso!", "success")
            return redirect(url_for('index'))

        except Error as err:
            print(f"Erro ao inserir dados do paciente: {err}")
            mydb.rollback()
            flash(f"Erro ao salvar os dados: {err}", "error")
            return redirect(url_for('index'))
        finally:
            mycursor.close()
            fechar_db(mydb)

    return redirect(url_for('index'))

@app.route('/relatorio')
def relatorio():
    """
    Renderiza a página de relatório, buscando e exibindo dados de pacientes
    com base em um filtro de pesquisa, incluindo informações de outras tabelas.
    """
    if 'usuario_logado' not in session:
        flash("Você precisa estar logado para acessar esta página.", "info")
        return redirect(url_for('login'))

    filtro = request.args.get('filtro')
    resultados = []

    print(f"DEBUG: Filtro recebido: '{filtro}'")

    mydb = conectar_db()
    if not mydb:
        flash("Erro ao conectar ao banco de dados para gerar relatório.", "error")
        print("DEBUG: ERRO - Falha na conexão com o banco de dados.")
        return render_template('relatorio.html', resultados=resultados, filtro=filtro)

    mycursor = mydb.cursor(dictionary=True)

    try:
        # A consulta SQL agora usará JOINs para trazer dados de outras tabelas
        sql_base = """
            SELECT
                p.id, p.nome, p.email, p.telefone, p.endereco, p.data_cadastro,
                p.tipo_sanguineo, p.teve_covid, p.vacina_covid,
                p.idade_menarca, p.ciclo_menstrual, p.usa_contraceptivo, p.tipo_contraceptivo,
                p.tratamento_previo,
                hs.condicao_saude, hs.motivo_consulta,
                sbe.retencao_liquidos, sbe.cansaco_excessivo, sbe.pratica_atividade_fisica,
                ar.definicao_alimentacao, ar.ja_seguiu_dieta, ar.bebe_liquidos_refeicoes, ar.aversao_alimentar
            FROM
                Paciente p
            LEFT JOIN
                HistoricoSaude hs ON p.id = hs.paciente_id
            LEFT JOIN
                SaudeBemEstar sbe ON p.id = sbe.paciente_id
            LEFT JOIN
                AlimentacaoRotina ar ON p.id = ar.paciente_id
            -- LEFT JOINs para outras tabelas como PacienteMotivacao, PacienteAreaInteresse, PacienteDoencaFamiliar
            -- são mais complexos de exibir em uma tabela plana diretamente.
            -- Para essas tabelas N:M (muitos para muitos), geralmente é melhor buscar separadamente
            -- ou em uma página de detalhes do paciente.
        """

        if filtro:
            # Adiciona a cláusula WHERE para filtrar
            sql = sql_base + """
                WHERE p.nome LIKE %s OR p.telefone LIKE %s
                ORDER BY p.nome
            """
            mycursor.execute(sql, (f"%{filtro}%", f"%{filtro}%"))
            print(f"DEBUG: SQL Executado (com filtro): {sql} com filtro '{filtro}'")
        else:
            # Se não houver filtro, busca todos
            sql = sql_base + """
                ORDER BY p.nome
            """
            mycursor.execute(sql)
            print(f"DEBUG: SQL Executado (sem filtro): {sql}")

        resultados = mycursor.fetchall()
        print(f"DEBUG: Resultados do DB ({len(resultados)} linhas): {resultados}")

        # Opcional: Converter valores booleanos e formatar datas/nulls
        for cliente in resultados:
            # Converte 1/0 para Sim/Não ou similar para melhor exibição
            cliente['teve_covid'] = 'Sim' if cliente['teve_covid'] == 1 else ('Não' if cliente['teve_covid'] == 0 else 'N/A')
            cliente['vacina_covid'] = 'Sim' if cliente['vacina_covid'] == 1 else ('Não' if cliente['vacina_covid'] == 0 else 'N/A')
            cliente['usa_contraceptivo'] = 'Sim' if cliente['usa_contraceptivo'] == 1 else ('Não' if cliente['usa_contraceptivo'] == 0 else 'N/A')
            cliente['retencao_liquidos'] = 'Sim' if cliente['retencao_liquidos'] == 1 else ('Não' if cliente['retencao_liquidos'] == 0 else 'N/A')
            cliente['cansaco_excessivo'] = 'Sim' if cliente['cansaco_excessivo'] == 1 else ('Não' if cliente['cansaco_excessivo'] == 0 else 'N/A')
            cliente['ja_seguiu_dieta'] = 'Sim' if cliente['ja_seguiu_dieta'] == 1 else ('Não' if cliente['ja_seguiu_dieta'] == 0 else 'N/A')
            cliente['bebe_liquidos_refeicoes'] = 'Sim' if cliente['bebe_liquidos_refeicoes'] == 1 else ('Não' if cliente['bebe_liquidos_refeicoes'] == 0 else 'N/A')

            # Trata campos None ou vazios para exibição
            for key in cliente:
                if cliente[key] is None or cliente[key] == '':
                    cliente[key] = 'Não informado'

    except Error as err:
        print(f"DEBUG: ERRO - Erro ao buscar dados para o relatório: {err}")
        flash(f"Erro ao carregar dados do relatório: {err}", "error")
    finally:
        mycursor.close()
        fechar_db(mydb)

    print(f"DEBUG: Renderizando relatorio.html com resultados: {len(resultados)} itens.")
    return render_template('relatorio.html', resultados=resultados, filtro=filtro)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Lida com o processo de login de usuários, buscando credenciais no banco de dados."""
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        mydb = conectar_db()
        if not mydb:
            mensagem_erro = "Erro ao conectar ao banco de dados. Tente novamente mais tarde."
            return redirect(url_for('login', erro=mensagem_erro))

        mycursor = mydb.cursor(dictionary=True)

        try:
            sql = "SELECT id, usuario, senha_hash FROM Usuarios WHERE usuario = %s"
            mycursor.execute(sql, (usuario,))
            user_data = mycursor.fetchone()

            if user_data:
                if check_password_hash(user_data['senha_hash'], senha):
                    session['usuario_logado'] = user_data['usuario']
                    session['usuario_id'] = user_data['id']
                    # flash(f"Bem-vindo, {user_data['usuario']}!", "success") # Remova se preferir apenas o alert
                    return redirect(url_for('relatorio'))
                else:
                    mensagem_erro = "Usuário ou senha inválidos."
                    return redirect(url_for('login', erro=mensagem_erro))
            else:
                mensagem_erro = "Usuário ou senha inválidos."
                return redirect(url_for('login', erro=mensagem_erro))

        except Error as err:
            print(f"Erro ao buscar usuário no banco de dados: {err}")
            mensagem_erro = "Erro interno do servidor. Tente novamente mais tarde."
            return redirect(url_for('login', erro=mensagem_erro))
        finally:
            mycursor.close()
            fechar_db(mydb)

    erro_mensagem = request.args.get('erro')
    if erro_mensagem:
        # Se quiser que a mensagem de erro também apareça no HTML (além do pop-up)
        flash(erro_mensagem, "error")

    return render_template('login.html')

# --- Funções para registrar usuários admin (para teste, não para produção) ---
# Você pode usar esta rota temporariamente para adicionar um usuário admin
# REMOVA OU PROTEJA ESTA ROTA EM PRODUÇÃO!
@app.route('/registrar_admin')
def registrar_admin():
    mydb = conectar_db()
    if not mydb:
        return "Erro ao conectar ao banco de dados para registrar admin."

    mycursor = mydb.cursor()
    try:
        senha_pura = "123"
        senha_hash = generate_password_hash(senha_pura)

        mycursor.execute("SELECT COUNT(*) FROM Usuarios WHERE usuario = 'admin'")
        if mycursor.fetchone()[0] == 0:
            sql = "INSERT INTO Usuarios (usuario, senha_hash) VALUES (%s, %s)"
            val = ("admin", senha_hash)
            mycursor.execute(sql, val)
            mydb.commit()
            fechar_db(mydb)
            return f"Usuário 'admin' com senha '{senha_pura}' (hasheada) registrado com sucesso!"
        else:
            fechar_db(mydb)
            return "Usuário 'admin' já existe no banco de dados."
    except Error as err:
        mydb.rollback()
        fechar_db(mydb)
        return f"Erro ao registrar admin: {err}"

@app.route('/registrar_novo_usuario')
def registrar_novo_usuario():
    novo_usuario = "cristiane"
    nova_senha_pura = "minhasenhaforte"

    mydb = conectar_db()
    if not mydb:
        return "Erro ao conectar ao banco de dados para registrar novo usuário."

    mycursor = mydb.cursor()
    try:
        senha_hash = generate_password_hash(nova_senha_pura)
        mycursor.execute("SELECT COUNT(*) FROM Usuarios WHERE usuario = %s", (novo_usuario,))
        if mycursor.fetchone()[0] == 0:
            sql = "INSERT INTO Usuarios (usuario, senha_hash) VALUES (%s, %s)"
            val = (novo_usuario, senha_hash)
            mycursor.execute(sql, val)
            mydb.commit()
            fechar_db(mydb)
            return f"Usuário '{novo_usuario}' com senha '{nova_senha_pura}' (hasheada) registrado com sucesso!"
        else:
            fechar_db(mydb)
            return f"Usuário '{novo_usuario}' já existe no banco de dados."
    except Error as err:
        mydb.rollback()
        fechar_db(mydb)
        return f"Erro ao registrar novo usuário: {err}"


@app.route('/logout')
def logout():
    """Desloga o usuário."""
    session.pop('usuario_logado', None)
    session.pop('usuario_id', None)
    flash("Você foi desconectado.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)