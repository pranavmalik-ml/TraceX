from fastapi.testclient import TestClient
from backend.main import app

client_context = TestClient(app)
client_context.__enter__()
client = client_context

def test_health():
    assert client.get('/api/health').json()['status'] == 'ok'

def test_dashboard_has_demo_data():
    data = client.get('/api/dashboard').json()
    assert data['transaction_count'] >= 12
    assert data['account_count'] >= 12

def test_trace_returns_bounded_network_and_attribution():
    response = client.post('/api/trace', json={
        'origin_account':'A', 'origin_amount':70000, 'source_id':'TEST-CASE', 'max_hops':8
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['summary']['accounts_traced'] >= 2
    assert data['summary']['highest_hop'] <= 8
    assert data['summary']['tainted_funds_currently_traced'] == '70000'
    assert all(float(x['tainted_amount']) <= float(x['amount']) for x in data['transactions'])

def test_trace_rejects_unknown_origin():
    response = client.post('/api/trace', json={'origin_account':'NO_SUCH_ACCOUNT','origin_amount':100})
    assert response.status_code == 404

def test_trace_rejects_more_than_eight_hops():
    response = client.post('/api/trace', json={'origin_account':'A','origin_amount':100,'max_hops':9})
    assert response.status_code == 422

def test_case_creation_and_listing():
    response = client.post('/api/cases', json={
        'case_id':'API-TEST-CASE', 'title':'API test', 'origin_account':'A', 'origin_amount':70000
    })
    assert response.status_code == 200
    assert any(x['case_id'] == 'API-TEST-CASE' for x in client.get('/api/cases').json())

def test_frontend_assets_are_served():
    assert client.get('/').status_code == 200
    assert client.get('/static/app.js').status_code == 200
    assert client.get('/static/styles.css').status_code == 200
