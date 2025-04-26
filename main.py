from fastapi import FastAPI, Request, Form, HTTPException, Depends # type: ignore
from fastapi.templating import Jinja2Templates # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from fastapi.responses import HTMLResponse, RedirectResponse # type: ignore
from fastapi.security import APIKeyHeader # type: ignore
from typing import Optional
from database import Database
from bson import ObjectId # type: ignore
import os
from dotenv import load_dotenv # type: ignore

# Load environment variables
load_dotenv()

# Initialize database
db = Database()

# Initialize FastAPI
app = FastAPI(
    title="Doctor's Client Management System API",
    description="API for managing healthcare clients and programs",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# API Security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


def convert_objectid_to_str(data):
    if isinstance(data, list):
        return [{k: str(v) if isinstance(v, ObjectId) else v for k, v in item.items()} for item in data]
    elif isinstance(data, dict):
        return {k: str(v) if isinstance(v, ObjectId) else v for k, v in data.items()}
    else:
        return data 
    
async def get_api_key(api_key_header: str = Depends(api_key_header)):
    if api_key_header == os.getenv("API_KEY", "CEMAinternship2025"):
        return api_key_header
    raise HTTPException(status_code=403, detail="Invalid API key")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Fetch real data from database
    clients = db.get_all_clients()
    programs = db.get_all_programs()
    
    # Get active programs
    active_programs = [program for program in programs if program.get("status") == "Active"]
    
    # Count all enrollments
    enrollment_count = db.enrollments.count_documents({})
    
    # Get recent clients (last 3 added - assuming most recent are at the end of the list)
    recent_clients = clients[-3:] if len(clients) >= 3 else clients
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "client_count": len(clients),
            "program_count": len(programs),
            "enrollment_count": enrollment_count,
            "recent_clients": recent_clients,
            "active_programs": active_programs[:3]
        }
    )

# Program routes
@app.get("/programs", response_class=HTMLResponse)
async def list_programs(request: Request):
    programs = db.get_all_programs()
    return templates.TemplateResponse(
        "programs.html", {"request": request, "programs": programs}
    )

@app.get("/programs/new", response_class=HTMLResponse)
async def new_program_form(request: Request):
    return templates.TemplateResponse("program_form.html", {"request": request})

@app.post("/programs/new")
async def create_program(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    status: str = Form("Active"),
):
    program_data = {
        "name": name,
        "description": description,
        "status": status,
    }
    db.create_program(program_data)
    return RedirectResponse(url="/programs", status_code=303)

@app.get("/programs/{program_id}", response_class=HTMLResponse)
async def view_program(request: Request, program_id: str):
    program = db.get_program(program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Get all enrollments for this program
    enrollments = list(db.enrollments.find({"program_id": program_id}))
    for enrollment in enrollments:
        enrollment["id"] = str(enrollment["_id"])
        # Fetch client details for each enrollment
        client = db.get_client(enrollment["client_id"])
        if client:
            enrollment["client_name"] = f"{client['first_name']} {client['last_name']}"
            enrollment["client_id"] = client["id"]
    
    return templates.TemplateResponse(
        "program_detail.html", 
        {
            "request": request, 
            "program": program,
            "enrollments": enrollments
        }
    )

@app.get("/programs/{program_id}/edit", response_class=HTMLResponse)
async def edit_program_form(request: Request, program_id: str):
    program = db.get_program(program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    return templates.TemplateResponse(
        "program_form.html", {"request": request, "program": program, "edit": True}
    )

@app.post("/programs/{program_id}/edit")
async def update_program(
    request: Request,
    program_id: str,
    name: str = Form(...),
    description: str = Form(...),
    status: str = Form("Active"),
):
    program_data = {
        "name": name,
        "description": description,
        "status": status,
    }
    
    success = db.update_program(program_id, program_data)
    if not success:
        raise HTTPException(status_code=404, detail="Program not found")
    
    return RedirectResponse(url="/programs", status_code=303)

@app.post("/programs/{program_id}/delete")
async def delete_program(program_id: str):
    # Check if any clients are enrolled in this program
    enrollments = db.enrollments.find_one({"program_id": program_id})
    if enrollments:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete program with active enrollments"
        )
    
    success = db.delete_program(program_id)
    if not success:
        raise HTTPException(status_code=404, detail="Program not found")
    
    return RedirectResponse(url="/programs", status_code=303)

# Client routes
@app.get("/clients", response_class=HTMLResponse)
async def list_clients(request: Request):
    clients = db.get_all_clients()
    return templates.TemplateResponse(
        "clients.html", {"request": request, "clients": clients}
    )

@app.get("/clients/new", response_class=HTMLResponse)
async def new_client_form(request: Request):
    return templates.TemplateResponse("client_form.html", {"request": request})

@app.post("/clients/new")
async def create_client(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: str = Form(...),
    gender: str = Form(...),
    contact_number: str = Form(...),
    email: Optional[str] = Form(None),
    address: str = Form(...),
):
    client_data = {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": date_of_birth,
        "gender": gender,
        "contact_number": contact_number,
        "email": email,
        "address": address,
    }
    db.create_client(client_data)
    return RedirectResponse(url="/clients", status_code=303)

@app.get("/clients/{client_id}", response_class=HTMLResponse)
async def view_client(request: Request, client_id: str):
    client = db.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get enrollments for this client
    enrollments = db.get_client_enrollments(client_id)
    
    # Get all programs for enrollment options
    all_programs = db.get_all_programs()
    
    return templates.TemplateResponse(
        "client_detail.html", 
        {
            "request": request, 
            "client": client, 
            "enrollments": enrollments,
            "programs": all_programs
        }
    )

@app.get("/clients/{client_id}/edit", response_class=HTMLResponse)
async def edit_client_form(request: Request, client_id: str):
    client = db.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return templates.TemplateResponse(
        "client_form.html", {"request": request, "client": client, "edit": True}
    )

@app.post("/clients/{client_id}/edit")
async def update_client(
    request: Request,
    client_id: str,
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: str = Form(...),
    gender: str = Form(...),
    contact_number: str = Form(...),
    email: Optional[str] = Form(None),
    address: str = Form(...),
):
    client_data = {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": date_of_birth,
        "gender": gender,
        "contact_number": contact_number,
        "email": email,
        "address": address,
    }
    
    success = db.update_client(client_id, client_data)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return RedirectResponse(url=f"/clients/{client_id}", status_code=303)

@app.post("/clients/{client_id}/delete")
async def delete_client(client_id: str):
    success = db.delete_client(client_id)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return RedirectResponse(url="/clients", status_code=303)

@app.get("/search/clients", response_class=HTMLResponse)
async def search_clients_form(request: Request):
    return templates.TemplateResponse("client_search.html", {"request": request})

@app.post("/search/clients", response_class=HTMLResponse)
async def search_clients(
    request: Request,
    search_term: str = Form(...),
):
    # Search by first name, last name, or contact number
    query = {
        "$or": [
            {"first_name": {"$regex": search_term, "$options": "i"}},
            {"last_name": {"$regex": search_term, "$options": "i"}},
            {"contact_number": {"$regex": search_term, "$options": "i"}},
        ]
    }
    clients = db.search_clients(query)
    
    return templates.TemplateResponse(
        "clients.html", 
        {
            "request": request, 
            "clients": clients,
            "search_term": search_term
        }
    )

# Enrollment routes
from datetime import datetime

@app.get("/enrollments/{client_id}/new", response_class=HTMLResponse)
async def new_enrollment_form(request: Request, client_id: str):
    client = db.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    programs = db.get_all_programs()
    programs = convert_objectid_to_str(programs)
    
    # QUICK: convert datetime fields to strings
    for program in programs:
        for key, value in program.items():
            if isinstance(value, datetime):
                program[key] = value.isoformat()

    return templates.TemplateResponse(
        "program_enrollment_form.html", 
        {
            "request": request, 
            "client": client,
            "programs": programs
        }
    )

@app.post("/enrollments/new")
async def create_enrollment(
    request: Request,
    client_id: str = Form(...),
    program_id: str = Form(...),
):
    # Check if client and program exist
    client = db.get_client(client_id)
    program = db.get_program(program_id)
    
    if not client or not program:
        raise HTTPException(status_code=404, detail="Client or program not found")
    
    # Check if enrollment already exists
    existing = db.check_enrollment_exists(client_id, program_id)
    
    if existing:
        raise HTTPException(status_code=400, detail="Client already enrolled in this program")
    
    enrollment_data = {
        "client_id": client_id,
        "program_id": program_id,
        "status": "Active"
    }
    
    db.create_enrollment(enrollment_data)
    return RedirectResponse(url=f"/clients/{client_id}", status_code=303)

@app.get("/enrollments/{enrollment_id}/edit", response_class=HTMLResponse)
async def edit_enrollment_form(request: Request, enrollment_id: str):
    enrollment = db.enrollments.find_one({"_id": ObjectId(enrollment_id)})
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    enrollment["id"] = str(enrollment["_id"])
    
    # Get client and program details
    client = db.get_client(enrollment["client_id"])
    program = db.get_program(enrollment["program_id"])
    
    if not client or not program:
        raise HTTPException(status_code=404, detail="Client or program not found")
    
    # Get all programs for dropdown
    all_programs = db.get_all_programs()
    
    return templates.TemplateResponse(
        "enrollment_form.html", 
        {
            "request": request, 
            "enrollment": enrollment, 
            "client": client,
            "current_program": program,
            "programs": all_programs,
            "edit": True
        }
    )

@app.post("/enrollments/{enrollment_id}/edit")
async def update_enrollment(
    request: Request,
    enrollment_id: str,
    program_id: str = Form(...),
    status: str = Form("Active"),
):
    enrollment = db.enrollments.find_one({"_id": ObjectId(enrollment_id)})
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    client_id = enrollment["client_id"]
    
    # If program is changing, check if client is already enrolled in new program
    if program_id != enrollment["program_id"]:
        existing = db.enrollments.find_one({
            "client_id": client_id,
            "program_id": program_id,
            "status": "Active",
            "_id": {"$ne": ObjectId(enrollment_id)}
        })
        
        if existing:
            raise HTTPException(status_code=400, detail="Client already enrolled in this program")
    
    enrollment_data = {
        "program_id": program_id,
        "status": status,
    }
    
    success = db.update_enrollment(enrollment_id, enrollment_data)
    if not success:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    return RedirectResponse(url=f"/clients/{client_id}", status_code=303)

@app.post("/enrollments/{enrollment_id}/delete")
async def delete_enrollment(enrollment_id: str):
    enrollment = db.enrollments.find_one({"_id": ObjectId(enrollment_id)})
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    client_id = enrollment["client_id"]
    
    success = db.delete_enrollment(enrollment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    return RedirectResponse(url=f"/clients/{client_id}", status_code=303)

# API Endpoints
# @app.get("/api/docs", response_class=HTMLResponse, tags=["Documentation"])
# async def api_documentation(request: Request):
#     """Serves the API documentation HTML page from the templates directory."""
#     context = {"request": request}
#     return templates.TemplateResponse("api_docs.html", context)

@app.get("/api/dashboard-data")
async def dashboard_data(api_key: str = Depends(get_api_key)):
    """API endpoint to get dashboard data for real-time updates"""
    clients = db.get_all_clients()
    programs = db.get_all_programs()
    active_programs = [program for program in programs if program.get("status") == "Active"]
    enrollment_count = db.enrollments.count_documents({})
    
    return {
        "client_count": len(clients),
        "program_count": len(programs),
        "enrollment_count": enrollment_count
    }

@app.get("/api/clients")
async def api_list_clients(api_key: str = Depends(get_api_key)):
    clients = db.get_all_clients()
    for client in clients:
        if "_id" in client:
            del client["_id"]
    return clients

@app.get("/api/clients/{client_id}")
async def api_get_client(client_id: str, api_key: str = Depends(get_api_key)):
    client = db.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if "_id" in client:
        del client["_id"]
    
    # Get enrollments for this client
    enrollments = db.get_client_enrollments(client_id)
    client_enrollments = []
    
    for enrollment in enrollments:
        program = db.get_program(enrollment["program_id"])
        if program:
            if "_id" in program:
                del program["_id"]
            enrollment_data = {
                "id": enrollment["id"],
                "enrollment_date": enrollment["enrollment_date"],
                "status": enrollment["status"],
                "program": program
            }
            client_enrollments.append(enrollment_data)
    
    client["enrollments"] = client_enrollments
    return client

if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)