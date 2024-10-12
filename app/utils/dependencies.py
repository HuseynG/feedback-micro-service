# app/utils/dependencies.py
from fastapi import Request

def get_database(request: Request):
    return request.app.database
