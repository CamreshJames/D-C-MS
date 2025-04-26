# Health Information System

A modern web application for managing healthcare clients and programs. Built with FastAPI, MongoDB, and a responsive UI.

## D-C-MS = Doctor's Client Management System

![Project Dashboard](https://github.com/CamreshJames/D-C-MS/blob/main/static/img/Dashboard.png)
*Caption: Overview of the main dashboard.*

## Features

- Create and manage health programs (TB, Malaria, HIV, etc.)
- Register and track clients
- Enroll clients in multiple health programs
- Search client database
- View comprehensive client profiles
- Access client data via RESTful API
- Responsive UI with dark/light theme toggle

## Technology Stack

- **Backend**: FastAPI
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Vercel-ready
- **Authentication**: API Key for external access

## Installation

### Prerequisites

- Python 3.8+
- MongoDB Atlas account or local MongoDB instance
- Git

### Step 1: Clone the repository

```bash
git clone https://github.com/CamreshJames/D-C-MS.git
cd D-C-MS
```

### Step 2: Set up a virtual environment

```bash
python -m venv venv
```

Activate it:

- On Windows:
  ```bash
  venv\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables

1. Rename `.env.example` to `.env`
2. Update the MongoDB connection string and API key in the `.env` file

# The following are the once I used incase you dont have access to mongo you can use mine
```
MONGODB_URI=MONGODB_URI=mongodb+srv://cnjmtechnologiesinc:Fink-Hoes-73@cluster0.lnxkd.mongodb.net/D-C-MS

API_KEY=CEMAinternship2025
```

## Running the Application

### Development Server

```bash
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

### Production Deployment

#### Deploying to Vercel

Deployed to vercel:
   Link: 

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Authentication

All API endpoints are protected with API key authentication. Include the API key in your request headers:

```
X-API-Key: CEMAinternship2025
```

### Sample API Requests

#### Get all clients

```bash
curl -X GET "http://localhost:8000/api/clients" -H "X-API-Key: CEMAinternship2025"
```

#### Get specific client with their programs

```bash
curl -X GET "http://localhost:8000/api/clients/client-id-here" -H "X-API-Key: CEMAinternship2025"
```

## Contributing

Welcome to:---...

## License

Public

## Contact

James Mwangi - [Portfolio](https://james-mwangi-njenga.vercel.app/)

Project Link After Hosting : [D-C-MS](https://doctor-client-management-system.vercel.app/)