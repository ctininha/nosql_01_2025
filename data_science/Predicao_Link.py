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

def criar_projecao_grafo(tx):
    """Cria uma projeção de grafo para uso com nodeSimilarity."""
    tx.run("""
    CALL gds.graph.project(
        'clientes_produtos',
        ['Cliente', 'Produto'],
        {
            COMPROU: {
                orientation: 'UNDIRECTED'
            }
        }
    )
    """)

def deletar_grafo(tx):
    """Remove a projeção do grafo se já existir."""
    tx.run("CALL gds.graph.drop('clientes_produtos', false) YIELD graphName")

def recomendar_por_similaridade(tx, cliente_nome):
    """Usa nodeSimilarity para encontrar clientes semelhantes e recomenda produtos."""
    # 1. Obtem o ID do cliente
    result = tx.run("""
    MATCH (c:Cliente {nome: $cliente_nome})
    RETURN id(c) AS id
    """, cliente_nome=cliente_nome)
    record = result.single()
    if not record:
        print("Cliente não encontrado.")
        return []

    cliente_id = record["id"]

    # 2. Executa nodeSimilarity
    similar_result = tx.run("""
    CALL gds.nodeSimilarity.stream('clientes_produtos')
    YIELD node1, node2, similarity
    WHERE node1 = $id OR node2 = $id
    RETURN
        CASE WHEN node1 = $id THEN node2 ELSE node1 END AS similar_node_id,
        similarity
    ORDER BY similarity DESC
    LIMIT 5
    """, id=cliente_id)

    similar_ids = [record["similar_node_id"] for record in similar_result]

    if not similar_ids:
        print("Nenhum cliente similar encontrado.")
        return []

    # 3. Recomenda produtos comprados pelos similares que o cliente ainda não comprou
    recomendacoes = tx.run("""
    MATCH (c:Cliente {nome: $cliente_nome})-[:COMPROU]->(p:Produto)
    WITH collect(p) AS produtos_cliente

    MATCH (c2:Cliente)-[:COMPROU]->(p2:Produto)
    WHERE id(c2) IN $ids AND NOT p2 IN produtos_cliente
    RETURN DISTINCT p2.nome AS produto
    LIMIT 5
    """, cliente_nome=cliente_nome, ids=similar_ids)

    return [record["produto"] for record in recomendacoes]

def main():
    driver = conectar_neo4j()
    if not driver:
        return

    try:
        with driver.session() as session:
            cliente_nome = input("Digite o nome do cliente: ")

            # Deleta e recria a projeção do grafo para garantir dados atualizados
            session.execute_write(deletar_grafo)
            session.execute_write(criar_projecao_grafo)

            recomendacoes = session.execute_read(recomendar_por_similaridade, cliente_nome=cliente_nome)

            if recomendacoes:
                print("\nProdutos recomendados com base em clientes similares:")
                for i, r in enumerate(recomendacoes, 1):
                    print(f"{i}. {r}")
            else:
                print("Nenhuma recomendação foi encontrada.")

    finally:
        fechar_conexao(driver)

if __name__ == "__main__":
    main()
