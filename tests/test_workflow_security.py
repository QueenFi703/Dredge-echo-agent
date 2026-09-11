from pathlib import Path
import unittest

class WorkflowSecurityTests(unittest.TestCase):
    def test_api_secrets_are_not_job_scoped(self):
        workflow = Path(".github/workflows/dredge-echo-research.yml").read_text()
        job_env = workflow.split("    steps:", 1)[0]
        self.assertNotIn("secrets.TAVILY_API_KEY", job_env)
        self.assertNotIn("secrets.NEBIUS_API_KEY", job_env)
        self.assertEqual(workflow.count("secrets.TAVILY_API_KEY"), 2)
        self.assertEqual(workflow.count("secrets.NEBIUS_API_KEY"), 2)

    def test_main_trigger_and_distinct_model_variables(self):
        workflow = Path(".github/workflows/dredge-echo-research.yml").read_text()
        self.assertIn("      - main", workflow)
        self.assertIn("NEBIUS_MODEL: ${{ vars.NEBIUS_MODEL }}", workflow)
        self.assertIn("NVIDIA_MODEL: ${{ vars.NVIDIA_MODEL }}", workflow)
