# database.py
from pymongo import MongoClient # type: ignore
from bson import ObjectId # type: ignore
from datetime import datetime
import os
from dotenv import load_dotenv # type: ignore

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URI") or "mongodb+srv://cnjmtechnologiesinc:Fink-Hoes-73@cluster0.lnxkd.mongodb.net/D-C-MS")
        self.db = self.client.health_system
        self.programs = self.db.programs
        self.clients = self.db.clients
        self.enrollments = self.db.enrollments
    
    def create_program(self, program_data):
        program_data["created_at"] = datetime.now()
        result = self.programs.insert_one(program_data)
        return str(result.inserted_id)
    
    def get_all_programs(self):
        programs = list(self.programs.find())
        for program in programs:
            program["id"] = str(program["_id"])
        return programs
    
    def get_program(self, program_id):
        program = self.programs.find_one({"_id": ObjectId(program_id)})
        if program:
            program["id"] = str(program["_id"])
        return program
    
    def create_client(self, client_data):
        client_data["registration_date"] = datetime.now()
        result = self.clients.insert_one(client_data)
        return str(result.inserted_id)
    
    def get_all_clients(self):
        clients = list(self.clients.find())
        for client in clients:
            client["id"] = str(client["_id"])
        return clients
    
    def get_client(self, client_id):
        client = self.clients.find_one({"_id": ObjectId(client_id)})
        if client:
            client["id"] = str(client["_id"])
        return client
    
    def search_clients(self, query):
        clients = list(self.clients.find(query))
        for client in clients:
            client["id"] = str(client["_id"])
        return clients
    
    def create_enrollment(self, enrollment_data):
        enrollment_data["enrollment_date"] = datetime.now()
        result = self.enrollments.insert_one(enrollment_data)
        return str(result.inserted_id)
    
    def get_client_enrollments(self, client_id):
        enrollments = list(self.enrollments.find({"client_id": client_id}))
        for enrollment in enrollments:
            enrollment["id"] = str(enrollment["_id"])
            # Get program details
            program = self.get_program(enrollment["program_id"])
            if program:
                enrollment["program"] = program
        return enrollments
    
    def check_enrollment_exists(self, client_id, program_id):
        return self.enrollments.find_one({
            "client_id": client_id,
            "program_id": program_id,
            "status": "Active"
        })
    def update_program(self, program_id, program_data):
        result = self.programs.update_one(
            {"_id": ObjectId(program_id)},
            {"$set": program_data}
        )
        return result.modified_count > 0

    def delete_program(self, program_id):
        result = self.programs.delete_one({"_id": ObjectId(program_id)})
        return result.deleted_count > 0

    def update_client(self, client_id, client_data):
        result = self.clients.update_one(
            {"_id": ObjectId(client_id)},
            {"$set": client_data}
        )
        return result.modified_count > 0

    def delete_client(self, client_id):
        # First delete all enrollments for this client
        self.enrollments.delete_many({"client_id": client_id})
        # Then delete the client
        result = self.clients.delete_one({"_id": ObjectId(client_id)})
        return result.deleted_count > 0

    def update_enrollment(self, enrollment_id, enrollment_data):
        result = self.enrollments.update_one(
            {"_id": ObjectId(enrollment_id)},
            {"$set": enrollment_data}
        )
        return result.modified_count > 0

    def delete_enrollment(self, enrollment_id):
        result = self.enrollments.delete_one({"_id": ObjectId(enrollment_id)})
        return result.deleted_count > 0