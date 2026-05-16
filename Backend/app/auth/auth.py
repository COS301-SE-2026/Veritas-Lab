from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import re as regex
import bcrypt
from jose import jwt
from datetime import datetime, timedelta, timezone
import asyncpg # This is the library for communicating with Postgres

SECRET_KEY = "change when the env is ready"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

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

# utf-8 encode the input string because bcrypt uses this, generate a salt, use the encoded string and salt to make the hash
# the hash is also utf-8 encoded so it needs to be decoded before it is returned
def hashPassword(input: str) -> str:
    convertedString = input.encode("utf-8")
    salt =bcrypt.gensalt()
    hashed = bcrypt.hashpw(convertedString, salt)
    return hashed.decode("utf-8")

# utf-8 encodes both strings and uses bcrypt.checkpw to see if they are the same
def verifyPassword(password: str, hashedPassword: str) ->bool:
    convertedPassword = password.encode("utf-8")
    convertedHash = hashedPassword.encode("utf-8")
    return bcrypt.checkpw(convertedPassword,convertedHash)

# Reason for allowing None: FastAPI/Pydantic have their own error reponses which undesired.
# So we allow None and validate missing fields in the endpoint.
class LoginRequest(BaseModel):
    email: str | None=None
    password: str | None=None

class RegisterRequest(BaseModel):
    email: str | None = None
    password: str | None = None
    username: str | None = None

async def updateUserJWTIssued(email: str):
    connection = await asyncpg.connect(
        user="postgres",
        password="",
        database="",
        host="localhost",
        port=8001
    )

    await connection.execute(
        """
        UPDATE "Users_DB"."Users"
        SET "UserJWTIssued" = NOW()
        WHERE "UserEmail" = $1
        """,
        email
    )

    await connection.close()

# Once the envs are setup this will need to be updated
async def searchUsersViaEmail(email:str):
    connection = await asyncpg.connect(
        user="postgres_username_here",
        password="some password here",
        database="database name here",
        host="localhost",
        port=8001
    )

    row = await connection.fetchrow(
         """
        SELECT "UserId", "UserEmail", "UserName", "UserRole", "UserPassword"
        FROM "Users"
        WHERE "UserEmail" = $1
        """,
        email
    )

    await connection.close

    if row is None:
        return None
    
    return {
        "id": str(row["UserId"]),
        "email": row["UserEmail"],
        "username": row["UserName"],
        "role": row["UserRole"],
        "password": row["UserPassword"]
    }

async def insertUser(email: str, username: str, role: str, hashedPassword: str):
    connection = await asyncpg.connect(
        user="postgres_username_here",
        password="some password here",
        database="database name here",
        host="localhost",
        port=8001
    )

    row = await connection.fetchrow(
        """
        INSERT INTO "Users" ("UserEmail", "UserName", "UserRole", "UserPassword")
        VALUES ($1, $2, $3, $4)
        RETURNING "UserId", "UserEmail", "UserName", "UserRole"
        """,
        email, username, role, hashedPassword
    )

    await connection.close()

    return {
        "id": str(row["UserId"]),
        "email": row["UserEmail"],
        "username": row["UserName"],
        "role": row["UserRole"]
    }

def createToken(user: dict) ->str:
    expiryTime = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
        "exp": expiryTime
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM) # the signature is made from SECRET_KEY and ALGORITHM
    return token

# POST /api/login
@router.post("/login")
async def login(request: LoginRequest):
    if not validateEmail(request.email):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Invalid or missing email field. E.g of a valid email: veritas@lab.com"
            }
        )

    if not validatePassword(request.password):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Invalid or missing password. Password must be longer than 11 characters, have an upper and lower case char and a special character"
            }
        )

    user = await searchUsersViaEmail(request.email.strip())

    if user is None:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": "A User with this email does not exist. Please register"
            }
        )
    
    if not verifyPassword(request.password, user["password"]):
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": "Invalid email or password"
            }
        )

    token = createToken(user)

    await updateUserJWTIssued(user["email"])

    return {
        "status" : "success",
        "token" : token
    }

        
    



