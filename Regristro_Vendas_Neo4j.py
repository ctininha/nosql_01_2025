import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from neo4j import GraphDatabase

# Configurações de conexão com o Neo4j
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password"


# Função para salvar um nó no Neo4j (genérica)
def salvar_no_neo4j(driver, label, propriedades):
    def create_node(tx, label, props):
        query = f"""
        CREATE (n:{label} $props)
        RETURN id(n) AS id
        """
        result = tx.run(query, props=props)
        record = result.single()
        return record["id"] if record else None

    try:
        # Tenta usar a forma do driver 5.x
        try:
            return driver.execute_write(create_node, label, propriedades)
        # Se falhar (atributo não existe), tenta a forma do driver 4.x
        except AttributeError:
            with driver.session() as session:
                return session.write_transaction(create_node, label, propriedades)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar {label}: {e}")
        return None


# Função para salvar dados da Venda no Neo4j
def salvar_venda(driver, dados_venda, cliente_id, pagamento_id, fornecedor_id, loja_id, funcionario_id):
    def criar_venda_relacionamentos(tx, dados, cliente_id, pagamento_id, fornecedor_id, loja_id, funcionario_id):
        query = """
        MATCH (c:Cliente) WHERE id(c) = $cliente_id
        MATCH (p:Pagamento) WHERE id(p) = $pagamento_id
        MATCH (f:Fornecedor) WHERE id(f) = $fornecedor_id
        MATCH (l:Loja) WHERE id(l) = $loja_id
        MATCH (func:Funcionario) WHERE id(func) = $funcionario_id
        CREATE (v:Venda $dados)
        CREATE (v)-[:PERTENCE_A_CLIENTE]->(c)
        CREATE (v)-[:FOI_PAGO_COM]->(p)
        CREATE (v)-[:FORNECIDO_POR]->(f)
        CREATE (v)-[:VENDIDO_NA_LOJA]->(l)
        CREATE (v)-[:VENDIDO_POR]->(func)
        """
        tx.run(query, dados=dados, cliente_id=cliente_id, pagamento_id=pagamento_id,
               fornecedor_id=fornecedor_id, loja_id=loja_id, funcionario_id=funcionario_id)

    try:
        # Tenta usar a forma do driver 5.x
        try:
            driver.execute_write(criar_venda_relacionamentos, dados_venda, cliente_id, pagamento_id, fornecedor_id,
                                 loja_id, funcionario_id)
        # Se falhar (atributo não existe), tenta a forma do driver 4.x
        except AttributeError:
            with driver.session() as session:
                session.write_transaction(criar_venda_relacionamentos, dados_venda, cliente_id, pagamento_id,
                                          fornecedor_id, loja_id, funcionario_id)
        messagebox.showinfo("Sucesso", "Venda registrada com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar a venda: {e}")


# Função para exibir os dados inseridos e salvar no banco de dados
def exibir_dados():
    try:
        data_hora_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        descricao = descricao_entry.get()
        quantidade = quantidade_entry.get()
        valor_venda = valor_venda_entry.get()
        metodo_pagamento = metodo_pagamento_combobox.get()
        unidade = unidade_entry.get()
        valor_custo = valor_custo_entry.get()
        grupo_produto = grupo_produto_entry.get()
        fornecedor_nome = fornecedor_entry.get()
        nome_funcionario = nome_funcionario_entry.get()
        loja_nome = loja_entry.get()
        status_venda = status_venda_combobox.get()
        nome_cliente = cliente_nome_entry.get()
        email_cliente = cliente_email_entry.get()
        valor_pago = valor_pago_entry.get()
        data_pagamento = data_pagamento_entry.get()

        # Validar campos obrigatórios (adapte conforme necessário)
        if not descricao or not quantidade or not valor_venda or not nome_cliente or not metodo_pagamento:
            messagebox.showerror("Erro",
                                 "Os campos Descrição, Quantidade, Valor de Venda, Nome do Cliente e Método de Pagamento são obrigatórios.")
            return

        dados_venda = {
            "data_hora_venda": data_hora_venda,
            "descricao": descricao,
            "quantidade": quantidade,
            "valor_venda": float(valor_venda),
            "unidade": unidade,
            "valor_custo": float(valor_custo) if valor_custo else None,
            "grupo_produto": grupo_produto,
            "status_venda": status_venda
        }

        dados_cliente = {
            "nome": nome_cliente,
            "email": email_cliente if email_cliente else None
        }

        dados_pagamento = {
            "metodo": metodo_pagamento,
            "valor_pago": float(valor_pago) if valor_pago else float(valor_venda),
            "data_pagamento": data_pagamento if data_pagamento else data_hora_venda
        }

        dados_fornecedor = {
            "nome": fornecedor_nome
        }

        dados_loja = {
            "nome": loja_nome
        }

        dados_funcionario = {
            "nome": nome_funcionario
        }

        try:
            with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
                cliente_id = salvar_no_neo4j(driver, "Cliente", dados_cliente)
                pagamento_id = salvar_no_neo4j(driver, "Pagamento", dados_pagamento)
                fornecedor_id = salvar_no_neo4j(driver, "Fornecedor", dados_fornecedor)
                loja_id = salvar_no_neo4j(driver, "Loja", dados_loja)
                funcionario_id = salvar_no_neo4j(driver, "Funcionario", dados_funcionario)

                if cliente_id is not None and pagamento_id is not None and fornecedor_id is not None and loja_id is not None and funcionario_id is not None:
                    salvar_venda(driver, dados_venda, cliente_id, pagamento_id, fornecedor_id, loja_id, funcionario_id)
                    limpar_campos()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar os dados: {e}")

        dados_venda_texto = f""" "VENDA REALIZADA"\n
        Data e Hora da Venda: {data_hora_venda}\n
        Descrição: {descricao}
        Quantidade: {quantidade}
        Valor de Venda: {valor_venda}
        Método de Pagamento: {metodo_pagamento}
        Unidade: {unidade}
        Valor de Custo: {valor_custo}
        Grupo do Produto: {grupo_produto}
        Fornecedor: {fornecedor_nome}
        Nome do Funcionário: {nome_funcionario}
        Loja: {loja_nome}
        Status da Venda: {status_venda}\n
        "CLIENTE"\n
        Nome: {nome_cliente}
        Email: {email_cliente}\n
        "PAGAMENTO"\n
        Valor Pago: {valor_pago}
        Data do Pagamento: {data_pagamento}
        """
        messagebox.showinfo("Dados da Venda", dados_venda_texto)

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao exibir os dados: {e}")


# Função para limpar os campos após o registro
def limpar_campos():
    descricao_entry.delete(0, tk.END)
    quantidade_entry.delete(0, tk.END)
    valor_venda_entry.delete(0, tk.END)
    metodo_pagamento_combobox.set("")
    unidade_entry.delete(0, tk.END)
    valor_custo_entry.delete(0, tk.END)
    grupo_produto_entry.delete(0, tk.END)
    fornecedor_entry.delete(0, tk.END)
    nome_funcionario_entry.delete(0, tk.END)
    loja_entry.delete(0, tk.END)
    status_venda_combobox.set("")
    cliente_nome_entry.delete(0, tk.END)
    cliente_email_entry.delete(0, tk.END)
    valor_pago_entry.delete(0, tk.END)
    data_pagamento_entry.delete(0, tk.END)


# Criando a interface gráfica com Scrollbar
try:
    root = tk.Tk()
    root.title("Auto Posto Trevão - Registro Completo das Vendas")

    # Criar um Canvas para conter os widgets roláveis
    canvas = tk.Canvas(root)
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Criar um frame dentro do Canvas para conter todos os seus widgets
    form_frame = ttk.Frame(canvas)

    # Adicionar todos os seus widgets (Labels, Entry, Combobox) ao form_frame
    tk.Label(form_frame, text="").pack(fill='x')
    tk.Label(form_frame, text="--- Dados da Venda ---").pack(fill='x')
    tk.Label(form_frame, text="Descrição do Item:").pack(fill='x')
    descricao_entry = tk.Entry(form_frame)
    descricao_entry.pack(fill='x')
    tk.Label(form_frame, text="Quantidade:").pack(fill='x')
    quantidade_entry = tk.Entry(form_frame)
    quantidade_entry.pack(fill='x')
    tk.Label(form_frame, text="Valor de Venda:").pack(fill='x')
    valor_venda_entry = tk.Entry(form_frame)
    valor_venda_entry.pack(fill='x')
    tk.Label(form_frame, text="Método de Pagamento:").pack(fill='x')
    metodo_pagamento_combobox = ttk.Combobox(form_frame, values=["Dinheiro", "Crédito", "Débito", "Pix"])
    metodo_pagamento_combobox.pack(fill='x')
    tk.Label(form_frame, text="Unidade do Item:").pack(fill='x')
    unidade_entry = tk.Entry(form_frame)
    unidade_entry.pack(fill='x')
    tk.Label(form_frame, text="Valor de Custo:").pack(fill='x')
    valor_custo_entry = tk.Entry(form_frame)
    valor_custo_entry.pack(fill='x')
    tk.Label(form_frame, text="Grupo do Produto:").pack(fill='x')
    grupo_produto_entry = tk.Entry(form_frame)
    grupo_produto_entry.pack(fill='x')
    tk.Label(form_frame, text="Fornecedor:").pack(fill='x')
    fornecedor_entry = tk.Entry(form_frame)
    fornecedor_entry.pack(fill='x')
    tk.Label(form_frame, text="Nome do Funcionário:").pack(fill='x')
    nome_funcionario_entry = tk.Entry(form_frame)
    nome_funcionario_entry.pack(fill='x')
    tk.Label(form_frame, text="Loja da Venda:").pack(fill='x')
    loja_entry = tk.Entry(form_frame)
    loja_entry.pack(fill='x')
    tk.Label(form_frame, text="Status da Venda:").pack(fill='x')
    status_venda_combobox = ttk.Combobox(form_frame, values=["Finalizada", "Cancelada", "Pendente"])
    status_venda_combobox.pack(fill='x')

    tk.Label(form_frame, text="--- Dados do Cliente ---").pack(fill='x')
    tk.Label(form_frame, text="Nome do Cliente:").pack(fill='x')
    cliente_nome_entry = tk.Entry(form_frame)
    cliente_nome_entry.pack(fill='x')
    tk.Label(form_frame, text="Email do Cliente:").pack(fill='x')
    cliente_email_entry = tk.Entry(form_frame)
    cliente_email_entry.pack(fill='x')

    tk.Label(form_frame, text="--- Dados do Pagamento ---").pack(fill='x')
    tk.Label(form_frame, text="Valor Pago:").pack(fill='x')
    valor_pago_entry = tk.Entry(form_frame)
    valor_pago_entry.pack(fill='x')
    tk.Label(form_frame, text="Data do Pagamento (AAAA-MM-DD HH:MM:SS):").pack(fill='x')
    data_pagamento_entry = tk.Entry(form_frame)
    data_pagamento_entry.pack(fill='x')

    tk.Label(form_frame, text="").pack(fill='x')
    tk.Button(form_frame, text="Salvar Venda Completa", command=exibir_dados).pack(fill='x')

    # Configurar a rolagem do Canvas para o tamanho do frame interno
    form_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=form_frame, anchor="nw")

    root.mainloop()

except Exception as e:
    print(f"Ocorreu um erro ao iniciar a interface gráfica: {e}")
