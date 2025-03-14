"""
Test module for Docker configuration.

This module contains tests to verify that the Docker configuration is correct.
"""

import unittest
import os
import sys
import re

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDockerConfiguration(unittest.TestCase):
    """Test cases for Docker configuration."""

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists in the project root."""
        dockerfile_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Dockerfile")
        self.assertTrue(os.path.exists(dockerfile_path), "Dockerfile should exist in project root")

    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists in the project root."""
        docker_compose_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docker-compose.yml")
        self.assertTrue(os.path.exists(docker_compose_path), "docker-compose.yml should exist in project root")

    def test_dockerignore_exists(self):
        """Test that .dockerignore exists in the project root."""
        dockerignore_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".dockerignore")
        self.assertTrue(os.path.exists(dockerignore_path), ".dockerignore should exist in project root")

    def test_dockerfile_content(self):
        """Test that Dockerfile contains necessary components."""
        dockerfile_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Dockerfile")
        with open(dockerfile_path, 'r') as f:
            content = f.read()
            
            # Check for base image
            self.assertIn("FROM python", content, "Dockerfile should specify a Python base image")
            
            # Check for working directory
            self.assertIn("WORKDIR /app", content, "Dockerfile should set working directory to /app")
            
            # Check for requirements installation
            self.assertIn("COPY requirements.txt", content, "Dockerfile should copy requirements.txt")
            self.assertIn("RUN pip install", content, "Dockerfile should install requirements")
            
            # Check for TA-Lib installation
            self.assertIn("ta-lib", content.lower(), "Dockerfile should install TA-Lib")
            
            # Check for application code copy
            self.assertIn("COPY . .", content, "Dockerfile should copy application code")
            
            # Check for CMD
            self.assertIn("CMD", content, "Dockerfile should specify a CMD instruction")

    def test_docker_compose_content(self):
        """Test that docker-compose.yml contains necessary components."""
        docker_compose_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docker-compose.yml")
        with open(docker_compose_path, 'r') as f:
            content = f.read()
            
            # Check for version
            self.assertIn("version:", content, "docker-compose.yml should specify a version")
            
            # Check for services
            self.assertIn("services:", content, "docker-compose.yml should define services")
            
            # Check for trading bot service
            self.assertIn("trading-bot:", content, "docker-compose.yml should define a trading-bot service")
            
            # Check for volumes
            self.assertIn("volumes:", content, "docker-compose.yml should define volumes")
            self.assertIn("./data:/app/data", content, "docker-compose.yml should mount data directory")
            self.assertIn("./logs:/app/logs", content, "docker-compose.yml should mount logs directory")
            
            # Check for environment variables
            self.assertIn("environment:", content, "docker-compose.yml should define environment variables")
            
            # Check for command
            self.assertIn("command:", content, "docker-compose.yml should specify a command")
            
            # Check for restart policy
            self.assertIn("restart:", content, "docker-compose.yml should specify a restart policy")

if __name__ == '__main__':
    unittest.main()
