from diagnosis.neo4j_driver import Neo4jDriver

def test_connection():
    driver = Neo4jDriver.get_driver()

    with driver.session() as session:
        result = session.run("RETURN 1 AS test")
        record = result.single()
        print("Neo4j test result:", record["test"])

    Neo4jDriver.close_driver()

if __name__ == "__main__":
    test_connection()
