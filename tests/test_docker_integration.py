#!/usr/bin/env python3
"""
Test Docker integration for the Multi-Agent Lead Processing System.
This test validates that the Docker environment is properly configured
and can run the application.
"""

import os
import sys
import unittest
import subprocess
import time
import requests
from pathlib import Path
import psycopg2

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

class TestDockerIntegration(unittest.TestCase):
    """Test that Docker integration is working properly."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Docker containers for testing."""
        cls.docker_compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        
        # Check if Docker is available
        try:
            subprocess.check_call(["docker", "--version"], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
        except (subprocess.SubprocessError, FileNotFoundError):
            raise unittest.SkipTest("Docker is not available on this system")
            
        # Check if docker-compose file exists
        if not cls.docker_compose_file.exists():
            raise unittest.SkipTest("docker-compose.yml not found")
            
        # Start the containers
        print("Starting Docker containers for testing...")
        subprocess.check_call(
            ["docker-compose", "-f", str(cls.docker_compose_file), "up", "-d"],
            stdout=subprocess.DEVNULL
        )
        
        # Wait for containers to be ready
        cls._wait_for_services()
    
    @classmethod
    def tearDownClass(cls):
        """Tear down Docker containers after testing."""
        print("Stopping Docker containers...")
        subprocess.check_call(
            ["docker-compose", "-f", str(cls.docker_compose_file), "down"],
            stdout=subprocess.DEVNULL
        )
    
    @classmethod
    def _wait_for_services(cls, max_attempts=30, delay=2):
        """Wait for services to be ready."""
        print("Waiting for services to be ready...")
        
        # Wait for API to be responsive
        api_ready = False
        db_ready = False
        attempts = 0
        
        while (not api_ready or not db_ready) and attempts < max_attempts:
            attempts += 1
            
            # Check API
            if not api_ready:
                try:
                    response = requests.get("http://localhost:8000/api/status", timeout=2)
                    if response.status_code == 200:
                        api_ready = True
                        print("API is ready")
                except requests.exceptions.RequestException:
                    pass
            
            # Check Database
            if not db_ready:
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        port=5432,
                        database="multiagent_db",
                        user="multiagent",
                        password=os.environ.get("DB_PASSWORD", "multiagent_password"),
                        connect_timeout=3
                    )
                    conn.close()
                    db_ready = True
                    print("Database is ready")
                except (psycopg2.OperationalError, psycopg2.Error):
                    pass
            
            if not api_ready or not db_ready:
                time.sleep(delay)
        
        if not api_ready:
            print("Warning: API did not become ready in time")
        if not db_ready:
            print("Warning: Database did not become ready in time")
            
        # Always provide some time for services to stabilize
        time.sleep(2)
    
    def test_api_status_endpoint(self):
        """Test that the API status endpoint responds correctly."""
        try:
            response = requests.get("http://localhost:8000/api/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("status", data)
            self.assertIn("system_status", data)
            self.assertIn("database_status", data)
        except requests.exceptions.RequestException as e:
            self.fail(f"API request failed: {e}")
    
    def test_database_connection(self):
        """Test that we can connect to the database."""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="multiagent_db",
                user="multiagent",
                password=os.environ.get("DB_PASSWORD", "multiagent_password")
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
            cursor.close()
            conn.close()
        except (psycopg2.OperationalError, psycopg2.Error) as e:
            self.fail(f"Database connection failed: {e}")


if __name__ == "__main__":
    unittest.main() 