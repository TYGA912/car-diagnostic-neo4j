from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "liondatlas93") # Hardcoded for test as we know it

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def test_login(u, p):
    print(f"Testing login for {u}...")
    query = """
    MATCH (u:User {username: $u, password: $p})
    RETURN u.name AS name, labels(u) AS labels, elementId(u) as id
    """
    with driver.session() as session:
        try:
            result = session.run(query, u=u, p=p).single()
            if result:
                print(f"Login success! Name: {result['name']}, ID: {result['id']}, Labels: {result['labels']}")
                
                # Test the car query too if login succeeds
                car_query = "MATCH (u:User)-[:OWNS]->(c:Car) WHERE elementId(u) = $uid RETURN c.model AS model"
                car_res = session.run(car_query, uid=result['id']).single()
                print(f"Car result: {car_res}")
            else:
                print("Login failed: User not found or wrong credentials.")
        except Exception as e:
            print(f"ERROR: {e}")

test_login("driver", "123")
driver.close()
