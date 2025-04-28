# tests/test_main.py
import pytest # type: ignore
import pytest_asyncio # type: ignore
from fastapi.testclient import TestClient # type: ignore
from bson import ObjectId # type: ignore
from unittest.mock import MagicMock, patch
import os
import sys
from datetime import datetime
from fastapi import HTTPException # type: ignore

# Ensure the main application directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import application components after path setup
from main import app, get_api_key, API_KEY_NAME

# --- Mock Database Class ---
# Provides a simplified in-memory simulation of the Database class
class MockDatabase:
    def __init__(self):
        """Initializes mock collections and internal data storage."""
        self.programs = MagicMock()
        self.clients = MagicMock()
        self.enrollments = MagicMock()

        self._programs_data = []
        self._clients_data = []
        self._enrollments_data = []

        # Assign mock implementations to collection methods
        self._setup_collection_mocks()

    def _setup_collection_mocks(self):
        """Sets up side effects for mock collection methods."""
        # Programs
        self.programs.find = MagicMock(side_effect=lambda query={}: [p for p in self._programs_data if self._matches(p, query)])
        self.programs.find_one = MagicMock(side_effect=lambda query={}: next((p for p in self._programs_data if self._matches(p, query)), None))
        self.programs.insert_one = MagicMock(side_effect=self._insert_one_program)
        self.programs.update_one = MagicMock(side_effect=self._update_one_program)
        self.programs.delete_one = MagicMock(side_effect=self._delete_one_program)
        self.programs.count_documents = MagicMock(side_effect=lambda query={}: len([p for p in self._programs_data if self._matches(p, query)]))

        # Clients
        self.clients.find = MagicMock(side_effect=lambda query={}: [c for c in self._clients_data if self._matches(c, query)])
        self.clients.find_one = MagicMock(side_effect=lambda query={}: next((c for c in self._clients_data if self._matches(c, query)), None))
        self.clients.insert_one = MagicMock(side_effect=self._insert_one_client)
        self.clients.update_one = MagicMock(side_effect=self._update_one_client)
        self.clients.delete_one = MagicMock(side_effect=self._delete_one_client_and_enrollments) # Uses helper
        self.clients.count_documents = MagicMock(side_effect=lambda query={}: len([c for c in self._clients_data if self._matches(c, query)]))

        # Enrollments
        self.enrollments.find = MagicMock(side_effect=lambda query={}: [e for e in self._enrollments_data if self._matches(e, query)])
        self.enrollments.find_one = MagicMock(side_effect=lambda query={}: next((e for e in self._enrollments_data if self._matches(e, query)), None))
        self.enrollments.insert_one = MagicMock(side_effect=self._insert_one_enrollment)
        self.enrollments.update_one = MagicMock(side_effect=self._update_one_enrollment)
        self.enrollments.delete_one = MagicMock(side_effect=self._delete_one_enrollment)
        self.enrollments.count_documents = MagicMock(side_effect=lambda query={}: len([e for e in self._enrollments_data if self._matches(e, query)]))


    def _matches(self, doc, query):
        """Helper for basic query matching (can be expanded)."""
        if not query:
            return True
        for key, value in query.items():
            doc_value = doc.get(key)
            if key == "_id" and isinstance(value, ObjectId):
                if doc_value != value: return False
            elif key == "$or":
                or_match = False
                for condition in value:
                    field = list(condition.keys())[0]
                    regex_data = condition[field]
                    term = regex_data["$regex"]
                    options = regex_data.get("$options", "")
                    doc_val_str = str(doc.get(field, ""))
                    if 'i' in options:
                        if term.lower() in doc_val_str.lower():
                            or_match = True; break
                    else:
                        if term in doc_val_str:
                            or_match = True; break
                if not or_match: return False
            elif key == "$ne" and isinstance(value, ObjectId):
                if doc.get("_id") == value: return False
            elif doc_value != value:
                return False
        return True

    def _add_id_str(self, doc):
        """Adds 'id' (string) field from '_id' (ObjectId)."""
        if doc and "_id" in doc:
            doc_copy = doc.copy()
            doc_copy["id"] = str(doc_copy["_id"])
            return doc_copy
        return doc

    # --- Internal Mock Implementations for collection methods ---
    def _insert_one_program(self, data):
        program_id = ObjectId()
        data["_id"] = program_id
        data["created_at"] = datetime.now()
        self._programs_data.append(data.copy()) # Store a copy
        return MagicMock(inserted_id=program_id)

    def _update_one_program(self, query, update_data):
        count = 0
        update_content = update_data.get('$set', {})
        for i, program in enumerate(self._programs_data):
            if self._matches(program, query):
                self._programs_data[i].update(update_content)
                count = 1
                break
        return MagicMock(modified_count=count)

    def _delete_one_program(self, query):
        initial_len = len(self._programs_data)
        self._programs_data = [p for p in self._programs_data if not self._matches(p, query)]
        deleted_count = initial_len - len(self._programs_data)
        return MagicMock(deleted_count=deleted_count)

    def _insert_one_client(self, data):
        client_id = ObjectId()
        data["_id"] = client_id
        data["registration_date"] = datetime.now()
        self._clients_data.append(data.copy()) # Store a copy
        return MagicMock(inserted_id=client_id)

    def _update_one_client(self, query, update_data):
        count = 0
        update_content = update_data.get('$set', {})
        for i, client in enumerate(self._clients_data):
            if self._matches(client, query):
                self._clients_data[i].update(update_content)
                count = 1
                break
        return MagicMock(modified_count=count)

    # --- FIX for SyntaxError and readability ---
    def _delete_one_client_and_enrollments(self, query):
        """Deletes a client matching query and their enrollments."""
        client_to_delete = next((c for c in self._clients_data if self._matches(c, query)), None)
        deleted_count = 0
        if client_to_delete:
            client_id_str = str(client_to_delete["_id"])
            initial_len = len(self._clients_data)

            # Filter out the client
            self._clients_data = [
                c for c in self._clients_data if not self._matches(c, query)
            ]
            # Filter out their enrollments
            self._enrollments_data = [
                e for e in self._enrollments_data if e.get("client_id") != client_id_str
            ]
            deleted_count = initial_len - len(self._clients_data)

        return MagicMock(deleted_count=deleted_count)
    # --- END FIX ---

    def _insert_one_enrollment(self, data):
        enrollment_id = ObjectId()
        data["_id"] = enrollment_id
        data["enrollment_date"] = datetime.now()
        self._enrollments_data.append(data.copy()) # Store a copy
        return MagicMock(inserted_id=enrollment_id)

    def _update_one_enrollment(self, query, update_data):
        count = 0
        update_content = update_data.get('$set', {})
        for i, enroll in enumerate(self._enrollments_data):
             if self._matches(enroll, query):
                 self._enrollments_data[i].update(update_content)
                 count = 1
                 break
        return MagicMock(modified_count=count)

    def _delete_one_enrollment(self, query):
        initial_len = len(self._enrollments_data)
        self._enrollments_data = [e for e in self._enrollments_data if not self._matches(e, query)]
        deleted_count = initial_len - len(self._enrollments_data)
        return MagicMock(deleted_count=deleted_count)

    # --- Public DB Methods (Mimicking database.py used by main.py) ---
    def create_program(self, program_data):
        result = self.programs.insert_one(program_data)
        return str(result.inserted_id)

    def get_all_programs(self):
        return [self._add_id_str(p) for p in self._programs_data]

    def get_program(self, program_id):
        try:
            oid = ObjectId(program_id)
            program = self.programs.find_one({"_id": oid})
            return self._add_id_str(program)
        except: # Handle potential invalid ObjectId string
            return None

    def update_program(self, program_id, program_data):
        try:
            result = self.programs.update_one({"_id": ObjectId(program_id)}, {"$set": program_data})
            return result.modified_count > 0 # Return Boolean
        except:
            return False

    def delete_program(self, program_id):
        try:
            result = self.programs.delete_one({"_id": ObjectId(program_id)})
            return result.deleted_count > 0 # Return Boolean
        except:
            return False

    def create_client(self, client_data):
        result = self.clients.insert_one(client_data)
        return str(result.inserted_id)

    def get_all_clients(self):
        return [self._add_id_str(c) for c in self._clients_data]

    def get_client(self, client_id):
        try:
            oid = ObjectId(client_id)
            client = self.clients.find_one({"_id": oid})
            return self._add_id_str(client)
        except:
            return None

    def search_clients(self, query):
        # Assumes query is like {"$or": [...]} from main.py
        results = self.clients.find(query)
        return [self._add_id_str(c) for c in results]

    def update_client(self, client_id, client_data):
        try:
            result = self.clients.update_one({"_id": ObjectId(client_id)}, {"$set": client_data})
            return result.modified_count > 0 # Return Boolean
        except:
            return False

    def delete_client(self, client_id):
        try:
            # This now calls the helper that handles enrollments too
            result = self.clients.delete_one({"_id": ObjectId(client_id)})
            return result.deleted_count > 0 # Return Boolean
        except:
            return False

    def create_enrollment(self, enrollment_data):
        result = self.enrollments.insert_one(enrollment_data)
        return str(result.inserted_id)

    def get_client_enrollments(self, client_id):
        # Mimic the join logic from main.py's view_client
        enrollment_docs = self.enrollments.find({"client_id": client_id})
        results = []
        for enroll_doc in enrollment_docs:
            enroll_copy = self._add_id_str(enroll_doc)
            program_id = enroll_copy.get("program_id")
            if program_id:
                 program = self.get_program(program_id)
                 if program:
                     enroll_copy["program"] = program # Add nested program details
            results.append(enroll_copy)
        return results

    def check_enrollment_exists(self, client_id, program_id):
        # Finds active enrollment
        existing = self.enrollments.find_one({
            "client_id": client_id,
            "program_id": program_id,
            "status": "Active"
        })
        return self._add_id_str(existing) # Returns doc or None

    def update_enrollment(self, enrollment_id, enrollment_data):
        try:
            result = self.enrollments.update_one({"_id": ObjectId(enrollment_id)}, {"$set": enrollment_data})
            return result.modified_count > 0 # Return Boolean
        except:
            return False

    def delete_enrollment(self, enrollment_id):
        try:
            result = self.enrollments.delete_one({"_id": ObjectId(enrollment_id)})
            return result.deleted_count > 0 # Return Boolean
        except:
            return False

# --- Fixtures ---
# Automatically patches main.db with a fresh MockDatabase for each test
@pytest.fixture(scope="function", autouse=True)
def mock_db_main():
    mock_instance = MockDatabase()
    with patch("main.db", mock_instance):
        yield mock_instance

# Provides the mock instance directly to tests if needed for setup/verification
@pytest.fixture
def mock_db(mock_db_main):
     return mock_db_main

# Sets the API_KEY environment variable for tests
@pytest.fixture
def mock_api_key_env():
    original_value = os.environ.get("API_KEY")
    # Use default from main.py if not set, for consistency
    test_key = os.getenv("API_KEY", "CEMAinternship2025")
    os.environ["API_KEY"] = test_key
    yield test_key
    # Teardown
    if original_value is None:
        if "API_KEY" in os.environ: del os.environ["API_KEY"]
    else:
        os.environ["API_KEY"] = original_value

# --- Test Client ---
# Created once for all tests
client = TestClient(app)

# --- Test Functions ---

@pytest.mark.asyncio
async def test_api_key_authentication(mock_api_key_env):
    """Tests the get_api_key dependency directly."""
    assert await get_api_key(mock_api_key_env) == mock_api_key_env
    with pytest.raises(HTTPException) as exc_info:
        await get_api_key("invalid_key")
    assert exc_info.value.status_code == 403

def test_homepage(mock_db):
    """Tests the root path GET request."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Client Management System" in response.text

# --- Program Routes ---

def test_list_programs(mock_db):
    """Tests listing programs."""
    mock_db.create_program({"name": "List Program Test", "description": "D", "status": "Active"})
    response = client.get("/programs")
    assert response.status_code == 200
    assert "List Program Test" in response.text

def test_create_program(mock_db):
    """Tests creating a new program."""
    response = client.get("/programs/new") # Test form page
    assert response.status_code == 200

    program_data = {"name": "Create Program Test", "description": "D", "status": "Active"}
    response = client.post("/programs/new", data=program_data, follow_redirects=False)
    assert response.status_code == 303, f"Expected 303, got {response.status_code}. Response: {response.text[:200]}"
    assert response.headers["location"] == "/programs"
    # Verify data was added to the mock database
    assert any(p["name"] == "Create Program Test" for p in mock_db.get_all_programs())

def test_view_program(mock_db):
    """Tests viewing a specific program's detail page."""
    program_id = mock_db.create_program({"name": "View Program Test", "description": "D", "status": "Active"})
    response = client.get(f"/programs/{program_id}")
    assert response.status_code == 200
    assert "View Program Test" in response.text

def test_update_program(mock_db):
    """Tests updating an existing program."""
    program_id = mock_db.create_program({"name": "Update Program Test", "description": "D", "status": "Active"})
    response = client.get(f"/programs/{program_id}/edit") # Test edit form page
    assert response.status_code == 200

    updated_data = {"name": "Updated Program Name", "description": "Updated Desc", "status": "Inactive"}
    response = client.post(f"/programs/{program_id}/edit", data=updated_data, follow_redirects=False)
    assert response.status_code == 303, f"Expected 303, got {response.status_code}. Response: {response.text[:200]}"
    assert response.headers["location"] == "/programs"
    # Verify data was updated in the mock database
    program = mock_db.get_program(program_id)
    assert program is not None
    assert program["name"] == "Updated Program Name"
    assert program["status"] == "Inactive"

def test_delete_program(mock_db):
    """Tests deleting a program without enrollments."""
    program_id = mock_db.create_program({"name": "Delete Program Test", "description": "D", "status": "Active"})
    response = client.post(f"/programs/{program_id}/delete", follow_redirects=False)
    assert response.status_code == 303, f"Expected 303, got {response.status_code}. Response: {response.text[:200]}"
    assert response.headers["location"] == "/programs"
    # Verify data was deleted from the mock database
    assert mock_db.get_program(program_id) is None

def test_delete_program_with_enrollment(mock_db):
    """Tests that deleting a program with enrollments fails."""
    program_id = mock_db.create_program({"name": "Enrolled Program", "description": "D", "status": "Active"})
    client_id = mock_db.create_client({"first_name": "E", "last_name": "C", "date_of_birth": "2000-01-01", "gender": "O", "contact_number": "5", "email": "e@e.com", "address": "A"})
    mock_db.create_enrollment({"client_id": client_id, "program_id": program_id, "status": "Active"})

    response = client.post(f"/programs/{program_id}/delete", follow_redirects=False)
    assert response.status_code == 400
    assert "Cannot delete program" in response.text
    # Verify program still exists
    assert mock_db.get_program(program_id) is not None

# --- Client Routes ---

def test_list_clients(mock_db):
    """Tests listing clients."""
    mock_db.create_client({"first_name": "List", "last_name": "Client Test", "date_of_birth": "1990-01-01", "gender":"M", "contact_number":"1", "email": "l@c.com", "address":"A"})
    response = client.get("/clients")
    assert response.status_code == 200
    assert "List Client Test" in response.text

def test_create_client(mock_db):
    """Tests creating a new client."""
    response = client.get("/clients/new") # Test form page
    assert response.status_code == 200

    client_data = {"first_name": "Create", "last_name": "Client Test", "date_of_birth": "1990-01-01", "gender": "F", "contact_number": "123", "email": "t@e.com", "address": "A"}
    response = client.post("/clients/new", data=client_data, follow_redirects=False)
    assert response.status_code == 303, f"Expected 303, got {response.status_code}. Response: {response.text[:200]}"
    assert response.headers["location"] == "/clients"
    # Verify data was added
    assert any(c["last_name"] == "Client Test" for c in mock_db.get_all_clients())

def test_view_client(mock_db):
    """Tests viewing a specific client's detail page."""
    client_id = mock_db.create_client({"first_name": "View", "last_name": "Client Test", "date_of_birth": "1990-01-01", "gender": "F", "contact_number": "123", "email": "v@e.com", "address": "A"})
    response = client.get(f"/clients/{client_id}")
    assert response.status_code == 200
    assert "View Client Test" in response.text

def test_update_client(mock_db):
    """Tests updating an existing client."""
    client_id = mock_db.create_client({"first_name": "Update", "last_name": "Client Test", "date_of_birth": "1990-01-01", "gender": "M", "contact_number": "123", "email": "u@e.com", "address": "A"})
    response = client.get(f"/clients/{client_id}/edit") # Test edit form
    assert response.status_code == 200

    updated_data = {"first_name": "Updated Name", "last_name": "Client Test", "date_of_birth": "1990-01-01", "gender": "F", "contact_number": "987", "email": "up@e.com", "address": "B"}
    response = client.post(f"/clients/{client_id}/edit", data=updated_data, follow_redirects=False)
    assert response.status_code == 303, f"Expected 303, got {response.status_code}. Response: {response.text[:200]}"
    assert response.headers["location"] == f"/clients/{client_id}" # Redirects to client detail
    # Verify update
    client_data = mock_db.get_client(client_id)
    assert client_data is not None
    assert client_data["first_name"] == "Updated Name"
    assert client_data["contact_number"] == "987"

def test_delete_client(mock_db):
    """Tests deleting a client and their enrollments."""
    client_id = mock_db.create_client({"first_name": "Delete", "last_name": "Client Test", "date_of_birth": "1990-01-01", "gender": "M", "contact_number": "123", "email": "d@e.com", "address": "A"})
    program_id = mock_db.create_program({"name": "Prog Del Client", "description": "D", "status": "Active"})
    # Keep track of the ObjectId to verify enrollment deletion from internal list
    enrollment_id_str = mock_db.create_enrollment({"client_id": client_id, "program_id": program_id, "status": "Active"})
    enrollment_id_obj = ObjectId(enrollment_id_str)

    response = client.post(f"/clients/{client_id}/delete", follow_redirects=False)
    assert response.status_code == 303, f"Expected 303, got {response.status_code}. Response: {response.text[:200]}"
    assert response.headers["location"] == "/clients"
    # Verify client deletion
    assert mock_db.get_client(client_id) is None
    # Verify associated enrollment deletion
    assert not any(e["_id"] == enrollment_id_obj for e in mock_db._enrollments_data)

def test_search_clients(mock_db):
    """Tests searching for clients."""
    # Setup data
    mock_db.create_client({"first_name": "Search", "last_name": "Alpha", "contact_number": "111111"})
    mock_db.create_client({"first_name": "Another", "last_name": "SearchBeta", "contact_number": "222222"})

    response = client.get("/search/clients") # Test form page
    assert response.status_code == 200

    # Test search (case-insensitive last name)
    response = client.post("/search/clients", data={"search_term": "alpha"})
    assert response.status_code == 200
    assert "Search Alpha" in response.text
    assert "SearchBeta" not in response.text

    # Test search (contact number)
    response = client.post("/search/clients", data={"search_term": "222222"})
    assert response.status_code == 200
    assert "Another SearchBeta" in response.text
    assert "Search Alpha" not in response.text

# --- Enrollment Routes ---

def test_enrollment_workflow(mock_db):
    """Tests the full enrollment lifecycle: create, duplicate check, update, delete."""
    # Setup client and programs
    client_id = mock_db.create_client({"first_name": "Enroll", "last_name": "Client", "date_of_birth": "1990-01-01", "gender": "M", "contact_number": "1", "email": "e@e.com", "address": "A"})
    program1_id = mock_db.create_program({"name": "Program Alpha", "description": "A", "status": "Active"})
    program2_id = mock_db.create_program({"name": "Program Beta", "description": "B", "status": "Active"})

    # 1. Create Enrollment
    response = client.get(f"/enrollments/{client_id}/new") # Test form page
    assert response.status_code == 200

    enrollment_data = {"client_id": client_id, "program_id": program1_id}
    response = client.post("/enrollments/new", data=enrollment_data, follow_redirects=False)
    assert response.status_code == 303, f"Expected 303 Create, got {response.status_code}. Response: {response.text[:200]}"
    assert response.headers["location"] == f"/clients/{client_id}"
    # Verify creation and get enrollment ID
    enrollments = mock_db.get_client_enrollments(client_id)
    assert len(enrollments) == 1
    assert enrollments[0]["program_id"] == program1_id
    enrollment_id = enrollments[0]["id"]

    # 2. Test Duplicate Enrollment Block
    response = client.post("/enrollments/new", data=enrollment_data, follow_redirects=False)
    assert response.status_code == 400 # Expect Bad Request
    assert "Client already enrolled" in response.text

    # 3. Update Enrollment
    response = client.get(f"/enrollments/{enrollment_id}/edit") # Test edit form page
    assert response.status_code == 200

    update_data = {"program_id": program2_id, "status": "Inactive"}
    response = client.post(f"/enrollments/{enrollment_id}/edit", data=update_data, follow_redirects=False)
    assert response.status_code == 303, f"Expected 303 Update, got {response.status_code}. Response: {response.text[:200]}"
    assert response.headers["location"] == f"/clients/{client_id}"
    # Verify update
    enrollments = mock_db.get_client_enrollments(client_id)
    assert len(enrollments) == 1
    assert enrollments[0]["program_id"] == program2_id
    assert enrollments[0]["status"] == "Inactive"

    # 4. Delete Enrollment
    response = client.post(f"/enrollments/{enrollment_id}/delete", follow_redirects=False)
    assert response.status_code == 303, f"Expected 303 Delete, got {response.status_code}. Response: {response.text[:200]}"
    assert response.headers["location"] == f"/clients/{client_id}"
    # Verify deletion
    assert len(mock_db.get_client_enrollments(client_id)) == 0

# --- API Endpoints ---

def test_api_dashboard_data(mock_db, mock_api_key_env):
    """Tests the API endpoint for dashboard stats."""
    mock_db.create_client({"first_name": "Api", "last_name": "Dash", "date_of_birth":"1990-01-01", "gender":"X", "contact_number":"1", "email":"a@d.com","address":"A"})
    mock_db.create_program({"name": "Api Prog", "description": "D", "status": "Active"})
    headers = {API_KEY_NAME: mock_api_key_env}

    response = client.get("/api/dashboard-data", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "client_count" in data and data["client_count"] >= 1
    assert "program_count" in data and data["program_count"] >= 1
    # Note: enrollment_count might be 0 if none created in this specific test's mock_db

def test_api_list_clients(mock_db, mock_api_key_env):
    """Tests the API endpoint for listing all clients."""
    client_id = mock_db.create_client({"first_name": "APIList", "last_name": "C1", "date_of_birth":"1990-01-01", "gender":"M", "contact_number":"1", "email":"a@l.com","address":"A"})
    headers = {API_KEY_NAME: mock_api_key_env}

    response = client.get("/api/clients", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and len(data) >= 1
    # Verify format of returned client data
    list_client = next((c for c in data if c.get("id") == client_id), None)
    assert list_client is not None
    assert "first_name" in list_client
    assert "_id" not in list_client # Should be removed
    assert "id" in list_client # String ID should be present

def test_api_get_client(mock_db, mock_api_key_env):
    """Tests the API endpoint for getting a single client with enrollments."""
    client_id = mock_db.create_client({"first_name": "APIGet", "last_name": "CX", "date_of_birth":"1990-01-01", "gender":"M", "contact_number":"1", "email":"a@g.com","address":"A"})
    program_id = mock_db.create_program({"name": "APIGet Program", "description": "D", "status": "Active"})
    mock_db.create_enrollment({"client_id": client_id, "program_id": program_id, "status": "Active"})
    headers = {API_KEY_NAME: mock_api_key_env}

    response = client.get(f"/api/clients/{client_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # Verify client data format
    assert data.get("id") == client_id
    assert data.get("first_name") == "APIGet"
    assert "_id" not in data
    # Verify enrollments format
    assert "enrollments" in data and len(data["enrollments"]) == 1
    enrollment = data["enrollments"][0]
    assert "id" in enrollment and "_id" not in enrollment # Check enrollment IDs
    assert enrollment["status"] == "Active"
    assert "program" in enrollment
    program_data = enrollment["program"]
    assert program_data["name"] == "APIGet Program"
    assert "id" in program_data and "_id" not in program_data # Check nested program IDs

def test_api_authentication_required(mock_db):
    """Tests that API endpoints return 403 without a valid API key."""
    response = client.get("/api/dashboard-data")
    assert response.status_code == 403

    response = client.get("/api/clients")
    assert response.status_code == 403

    dummy_id = str(ObjectId()) # Need a valid ObjectId format for path param
    response = client.get(f"/api/clients/{dummy_id}")
    assert response.status_code == 403