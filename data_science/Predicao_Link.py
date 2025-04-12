from neo4j import GraphDatabase

# Conexão com o Neo4j
uri = "bolt://localhost:7687"
usuario = "neo4j"
senha = "password"  # <- Substitua pela sua senha real
driver = GraphDatabase.driver(uri, auth=(usuario, senha))

def recomendar_produtos(nome_cliente):
    with driver.session() as session:
        # Remove grafo existente (se houver)
        session.run("""
            CALL gds.graph.exists('cliente_similaridade') YIELD exists
            WITH exists WHERE exists
            CALL gds.graph.drop('cliente_similaridade', false)
            YIELD graphName RETURN graphName
        """)

        # Criação do grafo com cliente e produto conectados por COMPROU
        session.run("""
            CALL gds.graph.project(
                'cliente_similaridade',
                ['Cliente', 'Produto'],
                {
                    COMPROU: {
                        type: 'COMPROU',
                        orientation: 'UNDIRECTED'
                    }
                }
            )
        """)

# Link Prediction por similaridade

        # Algoritmo de similaridade (corrigido)
        session.run("""
            CALL gds.nodeSimilarity.write(
                'cliente_similaridade',
                {
                    relationshipTypes: ['COMPROU'],
                    similarityCutoff: 0.1,
                    writeRelationshipType: 'PARECIDO_COM',
                    writeProperty: 'score'
                }
            )
        """)

        # Recomendação de produtos comprados por clientes similares
        result = session.run("""
            MATCH (c:Cliente {nome: $nome_cliente})-[:PARECIDO_COM]->(sim:Cliente)-[:COMPROU]->(p:Produto)
            WHERE NOT (c)-[:COMPROU]->(p)
            RETURN DISTINCT p.nome AS produto
        """, nome_cliente=nome_cliente)

        return [record["produto"] for record in result]

def listar_clientes():
    with driver.session() as session:
        result = session.run("MATCH (c:Cliente) RETURN DISTINCT c.nome AS nome ORDER BY nome")
        return [record["nome"] for record in result]

# Execução principal
if __name__ == "__main__":
    print("\n📋 Clientes disponíveis:")
    clientes = listar_clientes()
    for nome in clientes:
        print(f"- {nome}")

    nome_input = input("\nDigite o nome do cliente: ").strip()

    if nome_input not in clientes:
        print("⚠️ Cliente não encontrado.")
    else:
        recomendados = recomendar_produtos(nome_input)
        print(f"\n🔮 Produtos recomendados para {nome_input}:")
        if recomendados:
            for p in recomendados:
                print(f"- {p}")
        else:
            print("Nenhuma recomendação disponível no momento.")

    driver.close()

