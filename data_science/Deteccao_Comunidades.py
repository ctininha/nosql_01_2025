from neo4j import GraphDatabase

# Configurações de conexão
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password"

def conectar_neo4j():
    try:
        return GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    except Exception as e:
        print(f"Erro ao conectar ao Neo4j: {e}")
        return None

def fechar_conexao(driver):
    if driver:
        driver.close()

def criar_projecao_grafo_comunidades(tx):
    """Cria uma projeção de grafo para uso com o algoritmo de Comunidades Louvain."""
    tx.run("""
    CALL gds.graph.project(
        'grafo_comunidades',
        'Cliente',
        'COMPROU'
    )
    """)

def deletar_grafo_comunidades(tx):
    """Remove a projeção do grafo de comunidades se já existir."""
    tx.run("CALL gds.graph.drop('grafo_comunidades', false) YIELD graphName")

def detectar_comunidades(tx):
    """Executa o algoritmo de Comunidades Louvain."""
    result = tx.run("""
    CALL gds.louvain.stream('grafo_comunidades')
    YIELD nodeId, communityId
    RETURN gds.util.asNode(nodeId).nome AS cliente, communityId
    ORDER BY communityId
    """)
    return result.data()

def recomendar_por_comunidade(tx, cliente_nome):
    """Encontra a comunidade do cliente e recomenda produtos populares nessa comunidade."""
    # 1. Obtém a comunidade do cliente
    result_cliente = tx.run("""
    MATCH (c:Cliente {nome: $cliente_nome})
    CALL gds.louvain.stream('grafo_comunidades', {seedProperty: 'louvain'})
    YIELD nodeId, communityId
    WHERE gds.util.asNode(nodeId) = c
    RETURN communityId
    """, cliente_nome=cliente_nome)
    record_cliente = result_cliente.single()

    if not record_cliente:
        print("Cliente não encontrado ou comunidade não detectada.")
        return []

    cliente_comunidade = record_cliente["communityId"]

    # 2. Encontra os produtos mais comprados por outros clientes na mesma comunidade
    recomendacoes = tx.run("""
    MATCH (c:Cliente)-[:COMPROU]->(p:Produto)
    WHERE c <> (:Cliente {nome: $cliente_nome})
    WITH c
    CALL gds.louvain.stream('grafo_comunidades', {seedProperty: 'louvain'})
    YIELD nodeId, communityId
    WHERE gds.util.asNode(nodeId) = c AND communityId = $comunidade
    WITH p, count(*) AS quantidade
    ORDER BY quantidade DESC
    LIMIT 5
    RETURN p.nome AS produto
    """, cliente_nome=cliente_nome, comunidade=cliente_comunidade)

    return [record["produto"] for record in recomendacoes]

def main():
    driver = conectar_neo4j()
    if not driver:
        return

    try:
        with driver.session() as session:
            # Tarefa de Detecção de Comunidades
            print("\n--- Detecção de Comunidades ---")
            session.execute_write(deletar_grafo_comunidades)
            session.execute_write(criar_projecao_grafo_comunidades)
            session.execute_write(lambda tx: tx.run("CALL gds.louvain.mutate('grafo_comunidades', {mutateProperty: 'louvain'})"))
            comunidades = session.execute_read(detectar_comunidades)
            if comunidades:
                print("Comunidades de Clientes:")
                for cliente_comunidade in comunidades:
                    print(f"Cliente: {cliente_comunidade['cliente']}, Comunidade: {cliente_comunidade['communityId']}")
            else:
                print("Nenhuma comunidade detectada.")

            # Recomendação baseada em Similaridade (código original)
            print("\n--- Recomendação por Similaridade ---")
            cliente_nome_similaridade = input("Digite o nome do cliente para recomendação por similaridade: ")
            session.execute_write(lambda tx: tx.run("CALL gds.graph.drop('clientes_produtos', false) YIELD graphName"))
            session.execute_write(lambda tx: tx.run("""
                CALL gds.graph.project(
                    'clientes_produtos',
                    ['Cliente', 'Produto'],
                    {
                        COMPROU: {
                            orientation: 'UNDIRECTED'
                        }
                    }
                )
            """))
            recomendacoes_similaridade = session.execute_read(recomendar_por_similaridade, cliente_nome=cliente_nome_similaridade)
            if recomendacoes_similaridade:
                print("\nProdutos recomendados com base em clientes similares:")
                for i, r in enumerate(recomendacoes_similaridade, 1):
                    print(f"{i}. {r}")
            else:
                print("Nenhuma recomendação por similaridade encontrada.")

            # Recomendação baseada em Comunidade
            print("\n--- Recomendação por Comunidade ---")
            cliente_nome_comunidade = input("Digite o nome do cliente para recomendação por comunidade: ")
            recomendacoes_comunidade = session.execute_read(recomendar_por_comunidade, cliente_nome=cliente_nome_comunidade)
            if recomendacoes_comunidade:
                print(f"\nProdutos recomendados para clientes na mesma comunidade de '{cliente_nome_comunidade}':")
                for i, r in enumerate(recomendacoes_comunidade, 1):
                    print(f"{i}. {r}")
            else:
                print("Nenhuma recomendação por comunidade encontrada.")

    finally:
        fechar_conexao(driver)

if __name__ == "__main__":
    main()
