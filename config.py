import os

class Config:
    FLASK_DEBUG=os.getenv("FLASK_DEBUG")
    OPENAI_KEY = os.getenv('sk-bwxeC3PkS0-1IneRoWS4xdKsBRyry4eGxgE3Mmbp0DT3BlbkFJ_o2Wo03n1e7715oV5RS4I0kI_pNQ8P3kdAJr_b9OAA')

