import unittest
import os
import sys
import json
import time


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from backend.app import app as flask_app

class AppFunctionalTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        This is executed once before all the tests are run.
        Here we're using Flask's test client, which allows us to send requests to the Flask application directly from within the Python code, without having to start an actual HTTP server.
        without having to start an actual HTTP server.This is ideal for Docker test commands.
        """
        cls.flask_client = flask_app.test_client()
        cls.flask_client.testing = True 

    def test_1_frontend_loads(self):
        """
        Test that the root path on the front end loads successfully.
        This will check if the index.html file is returned.
        """
        print("\n--- Running test_1_frontend_loads ---")
        response = self.flask_client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI Document Insight Extractor", response.data)
        print("Frontend loads successfully.")

    def test_2_api_chat_success(self):
        """
        Tests whether the /api/chat endpoint successfully returns a response with valid input.
        This is a basic integration test that verifies that the backend API works and returns LLM generated content.
        """
        print("\n--- Running test_2_api_chat_success ---")
        test_data = {
            "document_text": "Dropout is a regularization technique for neural networks. It randomly sets a fraction of neurons to zero during training, preventing overfitting. It helps to reduce co-adaptation among neurons.",
            "user_query": "Explain dropout and its benefit."
        }
        # Sending POST Requests with the Flask Test Client
        response = self.flask_client.post('/api/chat', data=json.dumps(test_data),
                                          content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertGreater(len(data["response"]), 10) 
        print(f"API chat success. Response sample: '{data['response'][:50]}...'")

    def test_3_api_chat_missing_fields(self):
        """
        Tests if the /api/chat endpoint returns a 400 error when a required field is missing.
        """
        print("\n--- Running test_3_api_chat_missing_fields ---")
        # missing user_query
        test_data = {
            "document_text": "Some text."
        }
        response = self.flask_client.post('/api/chat', data=json.dumps(test_data),
                                          content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertIn("Missing", data["error"])
        print("API handled missing fields correctly.")

    def test_4_api_chat_empty_json(self):
        """
        Test if the /api/chat endpoint returns a 400 error on an empty JSON request.
        """
        print("\n--- Running test_4_api_chat_empty_json ---")
        response = self.flask_client.post('/api/chat', data=json.dumps({}),
                                          content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        print("API handled empty JSON correctly.")

    def test_5_p95_latency_single_request(self):
        """
        Initial test of latency for a single request.
        Note: A true P95 latency test requires multiple runs and statistics, this is only a rough validation.
        """
        print("\n--- Running test_5_p95_latency_single_request ---")
        start_time = time.time()
        test_data = {
            "document_text": "This is a short test document for latency measurement. It contains some text that the AI can process.",
            "user_query": "Summarize this document in one sentence."
        }
        response = self.flask_client.post('/api/chat', data=json.dumps(test_data),
                                          content_type='application/json')
        end_time = time.time()
        latency = end_time - start_time
        print(f"Single request latency: {latency:.2f} seconds")
        self.assertLess(latency, 3, "Single request latency exceeded 3 seconds.")
        self.assertEqual(response.status_code, 200, "Latency test failed due to API error.")
        print("Single request latency test passed.")

    def test_6_stability_multiple_queries(self):
        """
        Test the stability of the application by sending multiple queries in succession to make sure there are no crashes or errors.
        """
        print("\n--- Running test_6_stability_multiple_queries ---")
        num_queries = 20 
        errors = 0
        test_data = {
            "document_text": "This is a document for stability test. It should be processed repeatedly without issues.",
            "user_query": "What is the main idea?"
        }
        for i in range(num_queries):
            try:
                response = self.flask_client.post('/api/chat', data=json.dumps(test_data),
                                                  content_type='application/json')
                if response.status_code != 200:
                    errors += 1
                    print(f"Error on query {i+1}/{num_queries}: Status {response.status_code}, Error: {response.get_json().get('error', 'N/A')}")
            except Exception as e:
                errors += 1
                print(f"Exception on query {i+1}/{num_queries}: {e}")
        self.assertEqual(errors, 0, f"{errors} errors found in {num_queries} queries.")
        print(f"Stability test passed with 0 errors for {num_queries} queries.")


if __name__ == '__main__':
    print("Starting AI Document Analyzer Application Tests...")
    unittest.main()