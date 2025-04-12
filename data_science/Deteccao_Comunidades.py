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
    tx.run("""
        CALL gds.graph.project(
            'grafo_comunidades',
            'Cliente',
            {
                COMPROU: {
                    type: 'COMPROU',
                    orientation: 'UNDIRECTED'
                }
            }
        )
    """)

def deletar_grafo(tx, nome):
    tx.run(f"""
        CALL gds.graph.exists('{nome}')
        YIELD exists
        WITH exists
        WHERE exists
        CALL gds.graph.drop('{nome}', false)
        YIELD graphName
        RETURN graphName
    """)

def detectar_comunidades(tx):
    result = tx.run("""
        CALL gds.louvain.stream('grafo_comunidades')
        YIELD nodeId, communityId
        RETURN gds.util.asNode(nodeId).nome AS cliente, communityId
        ORDER BY communityId
    """)
    return result.data()

def escrever_similaridade(tx):
    tx.run("""
        CALL gds.nodeSimilarity.write(
            'clientes_produtos',
            {
                relationshipTypes: ['COMPROU'],
                similarityCutoff: 0.1,
                writeRelationshipType: 'PARECIDO_COM',
                writeProperty: 'score'
            }
        )
    """)

def recomendar_por_similaridade(tx, cliente_nome):
    result = tx.run("""
        MATCH (c:Cliente {nome: $cliente_nome})-[:PARECIDO_COM]->(sim:Cliente)-[:COMPROU]->(p:Produto)
        WHERE NOT (c)-[:COMPROU]->(p)
        RETURN DISTINCT p.nome AS produto
    """, cliente_nome=cliente_nome)
    return [record["produto"] for record in result]

def recomendar_por_comunidade(tx, cliente_nome):
    result_cliente = tx.run("""
        MATCH (c:Cliente {nome: $cliente_nome})
        RETURN c
    """, cliente_nome=cliente_nome)
    cliente_node = result_cliente.single()
    if not cliente_node:
        print("Cliente não encontrado.")
        return []

    comunidade_result = tx.run("""
        CALL gds.louvain.stream('grafo_comunidades')
        YIELD nodeId, communityId
        WITH nodeId, communityId WHERE gds.util.asNode(nodeId).nome = $cliente_nome
        RETURN communityId
    """, cliente_nome=cliente_nome)
    comunidade_info = comunidade_result.single()

    if not comunidade_info:
        print("Comunidade não encontrada.")
        return []

    cliente_comunidade = comunidade_info["communityId"]

    recomendacoes = tx.run("""
        MATCH (c:Cliente)-[:COMPROU]->(p:Produto)
        WHERE c.nome <> $cliente_nome
        WITH c, p
        CALL gds.louvain.stream('grafo_comunidades')
        YIELD nodeId, communityId
        WHERE gds.util.asNode(nodeId).nome = c.nome AND communityId = $comunidade
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
            print("\n--- Detecção de Comunidades ---")
            session.execute_write(lambda tx: deletar_grafo(tx, 'grafo_comunidades'))
            session.execute_write(criar_projecao_grafo_comunidades)
            session.execute_write(lambda tx: tx.run("CALL gds.louvain.write('grafo_comunidades', {writeProperty: 'louvain'})"))

            comunidades = session.execute_read(detectar_comunidades)
            for c in comunidades:
                print(f"Cliente: {c['cliente']}, Comunidade: {c['communityId']}")

            print("\n--- Recomendacao por Similaridade ---")
            cliente_sim = input("Cliente para similaridade: ")
            session.execute_write(lambda tx: deletar_grafo(tx, 'clientes_produtos'))
            session.execute_write(lambda tx: tx.run("""
                CALL gds.graph.project(
                    'clientes_produtos',
                    ['Cliente', 'Produto'],
                    {
                        COMPROU: {
                            type: 'COMPROU',
                            orientation: 'UNDIRECTED'
                        }
                    }
                )
            """))
            session.execute_write(escrever_similaridade)  # <== AQUI foi corrigido!
            recomendacoes_sim = session.execute_read(recomendar_por_similaridade, cliente_sim)
            for i, r in enumerate(recomendacoes_sim, 1):
                print(f"{i}. {r}")

            print("\n--- Recomendacao por Comunidade ---")
            cliente_com = input("Cliente para comunidade: ")
            recomendacoes_com = session.execute_read(recomendar_por_comunidade, cliente_com)
            for i, r in enumerate(recomendacoes_com, 1):
                print(f"{i}. {r}")

    finally:
        fechar_conexao(driver)

if __name__ == "__main__":
    main()

