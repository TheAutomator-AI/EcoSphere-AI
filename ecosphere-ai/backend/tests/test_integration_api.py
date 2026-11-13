"""End-to-end API smoke test with a completely isolated temporary SQLite database."""
from datetime import date
from io import BytesIO
from pathlib import Path
import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app


def test_local_api_end_to_end(tmp_path, monkeypatch):
    from app.config import settings
    from app.routers import evidence
    monkeypatch.setattr(settings, 'dev_auth_mode', True)
    monkeypatch.setattr(settings, 'upload_dir', str(tmp_path / 'uploads'))
    monkeypatch.setattr(settings, 'supabase_url', '')
    monkeypatch.setattr(settings, 'supabase_service_role_key', '')
    engine = create_engine(f'sqlite:///{tmp_path / "isolated.sqlite"}', connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def isolated_db():
        with Session() as db:
            yield db

    app.dependency_overrides[get_db] = isolated_db
    try:
        with TestClient(app) as client:
            created = client.post('/api/campuses', json={'name': 'Integration Test University'})
            assert created.status_code == 201, created.text
            ws = client.get('/api/workspace').json()
            assert len(ws['categories']) == 9
            department = client.post('/api/departments', json={'name': 'Computer Science'})
            zone = client.post('/api/zones', json={'name': 'Library', 'threshold_low_kg': 1, 'threshold_high_kg': 3})
            assert department.status_code == zone.status_code == 201
            payload = {
                'submission_id': 'TEST-001', 'audit_date': date.today().isoformat(),
                'department_id': department.json()['id'], 'zone_id': zone.json()['id'],
                'category_id': ws['categories'][0]['id'], 'auditor_name': 'Raja',
                'item_type': 'Sample PET bottle', 'item_count': 2, 'weight_kg': '2.5',
                'single_use': True, 'recyclable': True, 'disposal_method': 'segregated',
            }
            posted = client.post('/api/audits', json=payload)
            assert posted.status_code == 201, posted.text
            assert client.post('/api/audits', json=payload).status_code == 409
            aid = posted.json()['id']
            audit = client.get(f'/api/audits/{aid}').json()
            assert audit['submission_id'] == 'TEST-001'
            assert audit['weight_kg'] == 2.5
            metrics = client.get('/api/analytics').json()['metrics']
            assert metrics['total_kg'] == 2.5 and metrics['recycling_rate'] == 0.0
            assert metrics['reduction_kg'] is None
            recycled = client.post('/api/recycling', json={'audit_item_id': audit['item_id'], 'confirmed_weight_kg': '1.0'})
            assert recycled.status_code == 201, recycled.text
            assert client.get('/api/analytics').json()['metrics']['recycling_rate'] == 40.0

            csv_data = ('submission_id,audit_date,department,zone,auditor_name,category,item_type,item_count,weight_kg,single_use,recyclable,disposal_method\n'
                        f'TEST-002,{date.today()},Computer Science,Library,Raja,{audit["category"]},Food wrapper,3,0.8,true,false,mixed_waste\n')
            import_result = client.post('/api/audits/import', files={'file': ('audit.csv', csv_data.encode(), 'text/csv')})
            assert import_result.status_code == 201, import_result.text
            assert client.get('/api/analytics').json()['metrics']['total_kg'] == 3.3
            goal = client.post('/api/goals', json={'name': 'Reduce recorded waste by 1 kg', 'target_kg': 1, 'target_date': date.today().isoformat()})
            assert goal.status_code == 201, goal.text
            assert len(client.get('/api/goals').json()) == 1
            assert client.get('/api/reports/csv').status_code == 200
            pdf = client.get('/api/reports/pdf')
            assert pdf.status_code == 200 and pdf.content.startswith(b'%PDF-')
            assert len(client.get('/api/audits').json()) == 2

            # Use a real PNG payload: evidence verification never auto-approves it.
            from PIL import Image
            image = BytesIO()
            Image.new('RGB', (8, 8), (15, 115, 82)).save(image, format='PNG')
            uploaded = client.post(f'/api/evidence?audit_id={aid}&stage=before',
                                   files={'file': ('scale.png', image.getvalue(), 'image/png')})
            assert uploaded.status_code == 201, uploaded.text
            ev = uploaded.json()
            assert ev['status'] == 'pending'
            assert client.get(ev['download_url']).content.startswith(b'\x89PNG')
            verified = client.post(f'/api/evidence/{ev["id"]}/review', json={'status': 'approved', 'notes': 'Manually reviewed'})
            assert verified.status_code == 200 and verified.json()['status'] == 'approved'
            assert client.get(f'/api/audits/{aid}/history').status_code == 200
            assert client.delete(f'/api/audits/{aid}').json()['archived'] is True
            assert client.get(f'/api/audits/{aid}').status_code == 404
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
