# tests/load/locustfile.py
# Load testing with Locust - Phase 8

from locust import HttpUser, task, between
import random


class CRMUser(HttpUser):
    """Simulated CRM user for load testing"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post("/api/auth/login/", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(3)
    def view_dashboard(self):
        """View dashboard - most common action"""
        self.client.get("/api/dashboard/", headers=self.headers)
    
    @task(2)
    def list_accounts(self):
        """List accounts"""
        self.client.get("/api/accounts/", headers=self.headers)
    
    @task(2)
    def list_leads(self):
        """List leads"""
        self.client.get("/api/leads/", headers=self.headers)
    
    @task(1)
    def create_lead(self):
        """Create a new lead"""
        lead_data = {
            "first_name": f"Test{random.randint(1, 1000)}",
            "last_name": "User",
            "email": f"test{random.randint(1, 1000)}@example.com",
            "status": "new"
        }
        self.client.post("/api/leads/", json=lead_data, headers=self.headers)
