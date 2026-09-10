import unittest
import json
from app import app
from database import seed_data

class PlatformFullStackTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_data(force=True)

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        # Log in test client
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'username': 'admin',
                'full_name': 'Lead System Administrator',
                'role': 'admin'
            }

    def test_01_all_html_pages_render_successfully(self):
        pages = [
            '/dashboard',
            '/resources',
            '/data-sources',
            '/insights',
            '/automation',
            '/analytics',
            '/alerts',
            '/recommendations',
            '/reports',
            '/settings',
            '/login'
        ]
        for p in pages:
            res = self.client.get(p)
            self.assertIn(res.status_code, [200, 302], f"Page {p} returned status {res.status_code}")

    def test_02_dashboard_api(self):
        res = self.client.get('/api/dashboard')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('total_resources', data)
        self.assertIn('efficiency', data)
        self.assertGreater(data['total_resources'], 0)
        self.assertIn('score', data['efficiency'])

    def test_03_resources_crud(self):
        # 1. GET
        res = self.client.get('/api/resources')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        initial_count = len(data['resources'])

        # 2. POST (Create)
        new_res = {
            'name': 'Test Solar Array Microgrid',
            'type': 'electricity',
            'capacity': 120.0,
            'current_usage': 45.0,
            'unit': 'kW',
            'status': 'Optimal',
            'location': 'Rooftop Section 4'
        }
        res = self.client.post('/api/resources', json=new_res)
        self.assertEqual(res.status_code, 201)
        r_id = json.loads(res.data)['id']

        # 3. GET Single
        res = self.client.get(f'/api/resources/{r_id}')
        self.assertEqual(res.status_code, 200)
        item = json.loads(res.data)['resource']
        self.assertEqual(item['name'], 'Test Solar Array Microgrid')

        # 4. PUT (Update)
        res = self.client.put(f'/api/resources/{r_id}', json={'current_usage': 80.0, 'status': 'Warning'})
        self.assertEqual(res.status_code, 200)

        # 5. DELETE
        res = self.client.delete(f'/api/resources/{r_id}')
        self.assertEqual(res.status_code, 200)

    def test_04_ai_insight_analysis(self):
        res = self.client.post('/api/insights/analyze')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('efficiency', data)
        self.assertIn('results', data)

    def test_05_smart_automation_run(self):
        res = self.client.post('/api/automation/run', json={'force_simulation': True})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('actions', data)
        self.assertGreater(len(data['actions']), 0)

    def test_06_predictive_analytics(self):
        res = self.client.get('/api/analytics')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('forecast', data)
        self.assertIn('predicted_values', data['forecast'])
        self.assertGreater(len(data['forecast']['predicted_values']), 0)

    def test_07_demo_mode_pipeline(self):
        res = self.client.post('/api/demo-mode')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('pipeline_steps', data)
        self.assertEqual(len(data['pipeline_steps']), 4)

    def test_08_reports_and_csv_download(self):
        res = self.client.post('/api/reports/generate')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('total_resources', data)

        res_csv = self.client.get('/api/reports/download-csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.mimetype, 'text/csv')
        self.assertIn(b'SMART RESOURCE INTELLIGENCE', res_csv.data)

    def test_09_settings_api(self):
        res = self.client.get('/api/settings')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('settings', data)

        update_payload = {'electricity_threshold': 88}
        res_post = self.client.post('/api/settings', json=update_payload)
        self.assertEqual(res_post.status_code, 200)

if __name__ == '__main__':
    unittest.main()
