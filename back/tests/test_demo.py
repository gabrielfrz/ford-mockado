import unittest
from io import BytesIO
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from app.main import app

client=TestClient(app)
class DemoTests(unittest.TestCase):
    def test_program_flow(self):
        self.assertEqual(client.get('/search/program-names',params={'query':'orion'}).json(),['Orion Hybrid'])
        r=client.get('/vehicle-line/',params={'model_year':'2026','program_codes':'OR-02'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['gi_code'],'DEMO-002')

    def test_metric_filters_and_snapshots(self):
        path='/fede-status/metrics/conf-state'
        total=client.get(path).json()['conf_state_summary']
        subset=client.get(path,params={'pmt_code':'100'}).json()['conf_state_summary']
        older=client.get(path,params={'snapshot_date':'2026-07-01'}).json()['conf_state_summary']
        self.assertEqual(sum(total.values()),6*sum(subset.values()))
        self.assertGreater(total['Meet'],older['Meet'])
        self.assertEqual(sum(total.values()),sum(older.values()))

    def test_cost_totals(self):
        r=client.get('/cost/metrics/combined',params={'cpsc':'CPSC-001','pmt_code':'100'}).json()
        for kind in ['tooling','piece']:
            group=r[f'{kind}_cost']
            self.assertEqual(group['total_records'],1)
            self.assertEqual(group['total_cost'],sum(row[f'actual_{kind}_cost'] for row in group['data']))

    def test_exports_contain_only_synthetic_records(self):
        r=client.get('/export/cae-status',params={'gi_id':'DEMO-002','pmt_code':'100'})
        self.assertEqual(r.status_code,200)
        book=load_workbook(BytesIO(r.content),read_only=True)
        rows=list(book.active.values)
        self.assertGreater(len(rows),1)
        self.assertTrue(all(row[0]=='DEMO-002' for row in rows[1:]))
        self.assertIn('synthetic',book['About']['A1'].value)

    def test_all_dashboard_routes(self):
        paths=['/pmt/list','/dpa5/summary','/dpa5/cpsc-list','/dpa5/snapshots',
        '/api/v1/dvp-glidepath/pmts','/api/v1/dvp-glidepath/milestones','/api/v1/dvp-glidepath/data',
        '/api/v1/dvp-glidepath/snapshots','/api/v1/milestone-readiness/DEMO-001',
        '/fede-status/dvp-teams/autocomplete/by-gi-code','/fede-status/metrics/dvp-team-list',
        '/fede-status/by-dvp-team/row','/fede-status/metrics/conf-state-by-dvp-team',
        '/fede-status/metrics/cpsc-conf-state-breakdown','/api/v1/fede-status/dvp-classification',
        '/api/v1/fede-status/hir-completion','/metrics/cae-graph',
        '/fede-status/metrics/cae-total-assessments','/fede-status/cpsc/list',
        '/fede-status/metrics/design-rule-classification','/fede-status/metrics/dr-evidences-by-assessment',
        '/cost/cpsc/list','/cost/cpsc/autocomplete','/cost/pmt/list','/cost/metrics/tooling',
        '/cost/metrics/piece','/cost/partnumber/list','/cost/commodity/list','/cost/vehicleline/list','/cost/dropdowns']
        for path in paths:
            with self.subTest(path=path): self.assertEqual(client.get(path).status_code,200)
        self.assertEqual(client.get('/not-a-real-route').status_code,404)

if __name__=='__main__': unittest.main()
