from fastapi.testclient import TestClient
from phoenix_core.http_api.app import create_app
from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.services import CoreFoundationService

def client(tmp_path):
    db=SQLiteDatabase(tmp_path/"core.db")
    core=CoreFoundationService(db); core.initialise()
    # Apply remaining migrations before using baseline platform field.
    from phoenix_core.migration_runner import apply_all
    apply_all(db)
    system=core.create_user("system.admin","System Admin","Phoenix-V1-System-2026!")
    db.execute("UPDATE users SET platform_level='SYSTEM_ADMIN' WHERE id=?",(str(system.id),))
    org=core.create_organisation("DEMO","Demo Company")
    admin=core.create_user("company.admin","Company Admin","Phoenix-V1-Company-2026!")
    db.execute("UPDATE users SET platform_level='COMPANY_ADMIN' WHERE id=?",(str(admin.id),))
    core.add_membership(admin.identity_id,org.id)
    mid=__import__("uuid").uuid4()
    db.execute("INSERT INTO modules(id,code,name,version,status,created_at) VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)",(str(mid),"sales_360","Sales 360","0.1.0","ENABLED"))
    core.grant_module_entitlement(org.id,mid); db.commit()
    return TestClient(create_app(CoreApi(db,core)),base_url="http://testserver"),org

def test_baseline_company_user_flow(tmp_path):
    c,org=client(tmp_path)
    assert c.post("/api/v1/auth/login",json={"username":"company.admin","password":"Phoenix-V1-Company-2026!"}).status_code==200
    ctx=c.get("/api/v1/baseline/context").json()["data"]
    assert ctx["company"]["code"]=="DEMO"
    assert ctx["user"]["platform_level"]=="COMPANY_ADMIN"
    assert ctx["modules"][0]["active"] is True

def test_baseline_system_can_create_company_and_activate_module(tmp_path):
    c,_=client(tmp_path)
    assert c.post("/api/v1/auth/login",json={"username":"system.admin","password":"Phoenix-V1-System-2026!"}).status_code==200
    new=c.post("/api/v1/baseline/companies",json={"code":"ACME","name":"Acme"})
    assert new.status_code==200
    cid=new.json()["data"]["id"]
    assert c.post(f"/api/v1/baseline/companies/{cid}/modules/sales_360/activate").status_code==200
    assert c.post(f"/api/v1/baseline/companies/{cid}/admin",json={"username":"acme.admin","display_name":"Acme Admin","password":"Acme-V1-Admin-2026!"}).status_code==200
