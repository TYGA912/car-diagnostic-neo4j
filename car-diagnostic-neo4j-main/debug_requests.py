import os
import django
from neo4j import GraphDatabase

# Setup Django environment to reuse settings if needed, but strict neo4j is easier here
# actually let's just use the direct driver logic since we know creds are in .env or default
# We'll use the .env or hardcoded defaults from settings (usually neo4j/password)

uri = "bolt://localhost:7687"
auth = ("neo4j", "password") 

# Try to read .env
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith("NEO4J_URI"):
                uri = line.strip().split('=')[1]
            elif line.startswith("NEO4J_USER"):
                auth_user = line.strip().split('=')[1]
            elif line.startswith("NEO4J_PASSWORD"):
                auth_pass = line.strip().split('=')[1]
        if 'auth_user' in locals():
            auth = (auth_user, auth_pass)
except:
    pass

driver = GraphDatabase.driver(uri, auth=auth)

def debug_requests():
    with driver.session() as session:
        # 1. Check all requests
        print("--- ALL REQUESTS ---")
        query_all = """
        MATCH (r:Request)
        OPTIONAL MATCH (u:User)-[:REQUESTED]->(r)
        OPTIONAL MATCH (r)-[:TO]->(m)
        RETURN elementId(r) as req_id, r.status as status, r.issue as issue, u.name as client, m.name as mechanic_name, labels(m) as mech_labels, elementId(m) as mech_id
        """
        result = session.run(query_all)
        count = 0
        for record in result:
            count += 1
            print(f"Request {record['req_id']}: {record['issue']} (Status: {record['status']})")
            print(f"  From: {record['client']}")
            print(f"  To: {record['mechanic_name']} (ID: {record['mech_id']})")
            print(f"  Labels: {record['mech_labels']}")
            print("-" * 20)
        
        if count == 0:
            print("No requests found in database.")

        # 2. Check Mechanics
        print("\n--- ALL MECHANICS ---")
        query_mech = """
        MATCH (m:User:Mechanic)
        RETURN m.name as name, m.username as username, elementId(m) as id
        """
        result = session.run(query_mech)
        for record in result:
            print(f"Mechanic: {record['name']} (User: {record['username']}) - ID: {record['id']}")

if __name__ == "__main__":
    debug_requests()
    driver.close()
