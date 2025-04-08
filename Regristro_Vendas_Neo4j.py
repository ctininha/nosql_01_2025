import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from neo4j import GraphDatabase

# Configurações de conexão com o Neo4j
URI = "bolt://localhost:7687"  # Sua URI do Neo4j (pode variar)
USER = "neo4j"  # Seu nome de usuário do Neo4j (padrão: neo4j)
PASSWORD = "password"  # Sua senha do Neo4j (padrão: password - ALTERE SE VOCÊ MUDOU)

# Função para salvar dados no Neo4j (Adaptada para driver Neo4j 4.x e 5.x)
def salvar_no_banco(dados_venda):
    try:
        with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
            def criar_venda(tx, dados):
                query = """
                CREATE (v:Venda {
                    data_hora: $data_hora_venda,
                    descricao: $descricao,
                    quantidade: toInteger($quantidade),
                    valor_venda: toFloat($valor_venda),
                    metodo_pagamento: $metodo_pagamento,
                    unidade: $unidade,
                    valor_custo: toFloat($valor_custo),
                    grupo_produto: $grupo_produto,
                    fornecedor: $fornecedor,
                    nome_funcionario: $nome_funcionario,
                    loja: $loja,
                    status_venda: $status_venda
                })
                """
                tx.run(query, dados)

            # Tenta usar a forma do driver 5.x
            try:
                driver.execute_write(criar_venda, dados_venda)
            # Se falhar (atributo não existe), tenta a forma do driver 4.x
            except AttributeError:
                with driver.session() as session:
                    session.write_transaction(criar_venda, dados_venda)

            messagebox.showinfo("Sucesso", "Dados da venda salvos com sucesso no Neo4j!")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar no Neo4j: {e}")


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
        fornecedor = fornecedor_entry.get()
        nome_funcionario = nome_funcionario_entry.get()
        loja = loja_entry.get()
        status_venda = status_venda_combobox.get()

        # Validar se os campos obrigatórios estão preenchidos
        if not descricao or not quantidade or not valor_venda:
            messagebox.showerror("Erro", "Os campos Descrição, Quantidade e Valor de Venda são obrigatórios.")
            return

        # Criando o dicionário de dados para ser salvo no Neo4j
        dados_venda = {
            "data_hora_venda": data_hora_venda,
            "descricao": descricao,
            "quantidade": quantidade,
            "valor_venda": valor_venda,
            "metodo_pagamento": metodo_pagamento,
            "unidade": unidade,
            "valor_custo": valor_custo,
            "grupo_produto": grupo_produto,
            "fornecedor": fornecedor,
            "nome_funcionario": nome_funcionario,
            "loja": loja,
            "status_venda": status_venda
        }

        # Salvar dados no banco de dados Neo4j
        salvar_no_banco(dados_venda)

        # Exibir os dados na tela
        dados_venda_texto = f""" "VENDA REALIZADA"\n
        Data e Hora da Venda: {data_hora_venda}\n
        Descrição: {descricao}
        Quantidade: {quantidade}
        Valor de Venda: {valor_venda}
        Método de Pagamento: {metodo_pagamento}
        Unidade: {unidade}
        Valor de Custo: {valor_custo}
        Grupo do Produto: {grupo_produto}
        Fornecedor: {fornecedor}
        Nome do Funcionário: {nome_funcionario}
        Loja: {loja}
        Status da Venda: {status_venda}
        """

        messagebox.showinfo("Dados da Venda", dados_venda_texto)
        limpar_campos()

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


# Criando a interface gráfica
try:
    root = tk.Tk()

    # Adiciona uma linha em branco antes do título
    tk.Label(root, text="").pack()  # Linha em branco

    root.title("Auto Posto Trevão - Registro das Vendas")
    root.geometry("400x650")

    # Labels e Campos de Entrada
    tk.Label(root, text="Descrição do Item:").pack()
    descricao_entry = tk.Entry(root)
    descricao_entry.pack()

    tk.Label(root, text="Quantidade:").pack()
    quantidade_entry = tk.Entry(root)
    quantidade_entry.pack()

    tk.Label(root, text="Valor de Venda:").pack()
    valor_venda_entry = tk.Entry(root)
    valor_venda_entry.pack()

    tk.Label(root, text="Método de Pagamento:").pack()
    metodo_pagamento_combobox = ttk.Combobox(root, values=["Dinheiro", "Crédito", "Débito", "Pix"])
    metodo_pagamento_combobox.pack()

    tk.Label(root, text="Unidade do Item:").pack()
    unidade_entry = tk.Entry(root)
    unidade_entry.pack()

    tk.Label(root, text="Valor de Custo:").pack()
    valor_custo_entry = tk.Entry(root)
    valor_custo_entry.pack()

    tk.Label(root, text="Grupo do Produto:").pack()
    grupo_produto_entry = tk.Entry(root)
    grupo_produto_entry.pack()

    tk.Label(root, text="Fornecedor:").pack()
    fornecedor_entry = tk.Entry(root)
    fornecedor_entry.pack()

    tk.Label(root, text="Nome do Funcionário:").pack()
    nome_funcionario_entry = tk.Entry(root)
    nome_funcionario_entry.pack()

    tk.Label(root, text="Loja da Venda:").pack()
    loja_entry = tk.Entry(root)
    loja_entry.pack()

    tk.Label(root, text="Status da Venda:").pack()
    status_venda_combobox = ttk.Combobox(root, values=["Finalizada", "Cancelada", "Pendente"])
    status_venda_combobox.pack()

    # Adiciona duas linhas em branco
    tk.Label(root, text="").pack()  # Primeira linha em branco

    # Botão de Salvar dados
    tk.Button(root, text="Salvar Venda", command=exibir_dados).pack()

    # Inicia o loop principal da interface gráfica
    root.mainloop()

except Exception as e:
    print(f"Ocorreu um erro ao iniciar a interface gráfica: {e}")
