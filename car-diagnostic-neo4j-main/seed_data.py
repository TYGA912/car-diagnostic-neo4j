import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")

def seed_data():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    with driver.session() as session:
        print("Nettoyage de la base de données...")
        session.run("MATCH (n) DETACH DELETE n")

        print("Création de la Voiture et des Pièces...")
        # Cars
        session.run("CREATE (c1:Car {brand: 'Toyota', model: 'Corolla', year: 2020, engine_type: 'Hybrid'})")
        session.run("CREATE (c2:Car {brand: 'BMW', model: 'X5', year: 2022, engine_type: 'Diesel'})")
        
        # Parts with Visual Coordinates (French Names)
        session.run("""
            MATCH (c:Car {model: 'Corolla'})
            CREATE (p1:Part {name: 'Système de Freinage', x_pos: 15, y_pos: 65}), (p2:Part {name: 'Batterie', x_pos: 20, y_pos: 20})
            CREATE (c)-[:HAS_PART]->(p1), (c)-[:HAS_PART]->(p2)
        """)
        
        session.run("""
            MATCH (c:Car {model: 'X5'})
            CREATE (p3:Part {name: 'Turbocompresseur', x_pos: 45, y_pos: 30})
            CREATE (c)-[:HAS_PART]->(p3)
        """)

        # Mechanics
        print("Création des Mécaniciens...")
        session.run("CREATE (m1:Mechanic {name: 'Ahmed', location: 'Casablanca', rating: 4.8})")
        session.run("CREATE (m2:Mechanic {name: 'Karim', location: 'Rabat', rating: 4.5})")
        session.run("CREATE (m3:Mechanic {name: 'AutoFix Center', location: 'Marrakech', rating: 3.9})")

        # Expertise
        session.run("""
            MATCH (m:Mechanic {name: 'Ahmed'}), (p:Part {name: 'Système de Freinage'})
            CREATE (m)-[:EXPERT_IN]->(p)
        """)
        session.run("""
            MATCH (m:Mechanic {name: 'Karim'}), (p:Part {name: 'Batterie'})
            CREATE (m)-[:EXPERT_IN]->(p)
        """)
        session.run("""
            MATCH (m:Mechanic {name: 'AutoFix Center'}), (p:Part {name: 'Turbocompresseur'})
            CREATE (m)-[:EXPERT_IN]->(p)
        """)

        # Problems & Solutions (Corolla Brakes)
        session.run("""
            MATCH (p:Part {name: 'Système de Freinage'})
            MATCH (m:Mechanic {name: 'Ahmed'})
            CREATE (pr:Problem {description: 'Bruit de grincement', severity: 'Faible'})
            CREATE (s1:Solution {description: 'Nettoyer la poussière de frein', cost_range: '50 MAD', type: 'DIY'})
            CREATE (s2:Solution {description: 'Remplacer les plaquettes', cost_range: '300 MAD', type: 'Professional'})
            
            CREATE (p)-[:HAS_PROBLEM]->(pr)
            CREATE (pr)-[:HAS_SOLUTION]->(s1)
            CREATE (pr)-[:HAS_SOLUTION]->(s2)
            CREATE (m)-[:POSTED]->(s2)
        """)

        # Problems & Solutions (Corolla Battery)
        session.run("""
            MATCH (p:Part {name: 'Batterie'})     
            MATCH (m:Mechanic {name: 'Karim'})
            CREATE (pr:Problem {description: 'La voiture ne démarre pas', severity: 'Élevée'})
            CREATE (s1:Solution {description: 'Démarrer avec des câbles', cost_range: '0 MAD', type: 'DIY'})
            CREATE (s2:Solution {description: 'Remplacer la batterie', cost_range: '1500 MAD', type: 'Professional'})
            
            CREATE (p)-[:HAS_PROBLEM]->(pr)
            CREATE (pr)-[:HAS_SOLUTION]->(s1)
            CREATE (pr)-[:HAS_SOLUTION]->(s2)
            CREATE (m)-[:POSTED]->(s2)
        """)
        
        # Users (Authentication)
        print("Création des Utilisateurs...")
        # Users (Authentication) linked to Domain Nodes
        print("Création des Utilisateurs...")
        session.run("""
            MATCH (c:Car {model: 'Corolla'})
            CREATE (u1:User:Driver {username: 'driver', password: '123', name: 'Karim'})
            CREATE (u1)-[:OWNS]->(c)
        """)
        
        # Merge 'meca' user into the existing 'Ahmed' mechanic
        session.run("""
            MATCH (m:Mechanic {name: 'Ahmed'})
            SET m:User, m.username = 'meca', m.password = '123'
        """)
        
        # Admin user remains separate
        session.run("""
            CREATE (u3:User:Admin {username: 'admin', password: '123', name: 'Directeur Qualité'})
        """)

    print("Données initialisées ! Utilisateurs (driver/123, meca/123).")
    driver.close()

if __name__ == "__main__":
    seed_data()
