from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

from django.conf import settings

class Neo4jDriver:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            uri = getattr(settings, "NEO4J_URI", "bolt://localhost:7687")
            user = getattr(settings, "NEO4J_USER", "neo4j")
            password = getattr(settings, "NEO4J_PASSWORD", "")
            
            print(f"DEBUG: Connecting to Neo4j at {uri} with user {user}")
            
            try:
                cls._driver = GraphDatabase.driver(uri, auth=(user, password))
                cls._driver.verify_connectivity()
                print("DEBUG: Neo4j Connection Successful from Driver!")
            except Exception as e:
                print(f"DEBUG: Neo4j Connection FAILED: {e}")
                raise e
        return cls._driver

    @classmethod
    def close_driver(cls):
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None
