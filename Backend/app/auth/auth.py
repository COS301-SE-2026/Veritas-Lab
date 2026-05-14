from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import re as regex
import bcrypt

router = APIRouter(
    prefix="/api",
    tags=["Auth"]
)

# Validates an email. 
# Regex: One or more valid pre-@ characters (0-9, a-z, A-z,.,_,+,-), 
# an "@", one or more valid post-@ pre. characters (0-9, a-z, A-z,.,-), a ".",
# and finally two or more valid post. characters (A-Z and a-z).
def validateEmail(email: str) -> bool:
    if not isinstance(email,str):
        return False

    email = email.strip()

    if len(email) == 0:
        return False
    
    pattern = r"^[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return regex.match(pattern, email) is not None

# Validates a password. 
# Password must contain a special character, number, lower case char, upper case char and be longer than 12 characters in length.
# Regex : At least 1 lower case, At least 1 upper case, At least 1 number number, At least 1 special char, must be 12 chars long
def validatePassword(password: str) -> bool:
    if not isinstance(password,str):
        return False
    
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$"
    return regex.match(pattern, password) is not None




class loginRequest(BaseModel):
    email: str
    password: str


