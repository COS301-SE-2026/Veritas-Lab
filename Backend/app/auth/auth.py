from fastapi import APIRouter, HTTPException, Header, Response, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import re as regex
import bcrypt
import uuid as uuidlib
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from datetime import datetime, timedelta, timezone
import asyncpg # This is the library for communicating with Postgres
from app.core.env import ENVLoader

env = ENVLoader()

DB_USER= env.getRequiredEnv("DB_USER")
DB_PASSWORD= env.getRequiredEnv("DB_PASSWORD")
DB_HOST= env.getRequiredEnv("DB_HOST")
DB_PORT= env.getRequiredIntEnv("DB_PORT")
DB_NAME= env.getRequiredEnv("DB_NAME")
DB_SSL = env.getRequiredEnv("DB_SSL").strip().lower() in ("1", "true")
SECRET_KEY = env.getRequiredEnv("JWT_SECRET")
ALGORITHM = env.getRequiredEnv("HASH").replace("_", "").upper()
ACCESS_TOKEN_EXPIRE_MINUTES = env.getRequiredIntEnv("TOKEN_EXPIRE")
COOKIE_NAME = "JWT_token"
AMBIGUOUS_ERROR= "The email and/or passwordare invalid"
INVALID_TOKEN= "Invalid token"

async def getConnection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        ssl="require" if DB_SSL else None,
    )
router = APIRouter(
    prefix="/api",
    tags=["Auth"]
)

def verifyJWT(request: Request) -> dict:
    #if authorizationHeader is None or authorizationHeader.strip() == "":
    #    raise ValueError("Missing Authorization header")

    #if not authorizationHeader.startswith("Bearer "):
    #    raise ValueError("Invalid Authorization header format")

    ## token = authorizationHeader.replace("Bearer ", "", 1).strip()
    #token = 
    #if token == "":
    #    raise ValueError("Missing JWT token")

    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise ValueError("Not authenticated")

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except ExpiredSignatureError:
        raise ValueError("Token has expired")

    except JWTError:
        raise ValueError(INVALID_TOKEN)

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

#Validates that a string is a well-formed UUID
#The delete endpoint gets userId as  a arw string from the URL path
# Thus checking it before sending it to the db to avoid db level-error
def validateUUID(value: str) -> bool:
    if  not isinstance(value, str):
        return False
    try:
        uuidlib.UUID(value.strip())
        return True
    except ValueError:
        return False

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
    converted_string = input.encode("utf-8")
    salt =bcrypt.gensalt()
    hashed = bcrypt.hashpw(converted_string, salt)
    return hashed.decode("utf-8")

# utf-8 encodes both strings and uses bcrypt.checkpw to see if they are the same
def verifyPassword(password: str, hashed_password: str) ->bool:
    converted_password = password.encode("utf-8")
    converted_hash = hashed_password.encode("utf-8")
    return bcrypt.checkpw(converted_password,converted_hash)

# Reason for allowing None: FastAPI/Pydantic have their own error reponses which undesired.
# So we allow None and validate missing fields in the endpoint.
class LoginRequest(BaseModel):
    email: str | None=None
    password: str | None=None

class RegisterRequest(LoginRequest):
    username: str | None = None

class ChangeRoleRequest(BaseModel):
    userId: str | None = None
    NewRole: str | None = None

async def updateUserJWTIssued(email: str):
    connection = await getConnection()
    try:
        await connection.execute(
            """
            UPDATE "Users_DB"."Users"
            SET userjwtissued = NOW()
            WHERE useremail = $1
            """,
            email
        )
    finally:
        await connection.close()

async def update_user_jwt_issued_via_user(user: dict):
    connection = await getConnection()
    try:
        await connection.execute(
            """
            UPDATE "Users_DB"."Users"
            SET userjwtissued = NOW()
            WHERE userid = $1
            """,
            user["id"]
        )
    finally:
        await connection.close()

# Once the envs are setup this will need to be updated
async def searchUsersViaEmail(email:str):
    connection = await getConnection()
    try:
        row = await connection.fetchrow(
            """
            SELECT userid, useremail, username, userrole, userpassword
            FROM "Users_DB"."Users"
            WHERE useremail = $1
            """,
            email
        )

        if row is None:
            return None
        
        return {
            "id": str(row["userid"]),
            "email": row["useremail"],
            "username": row["username"],
            "role": row["userrole"],
            "password": row["userpassword"]
        }
    finally:
        await connection.close()
    
async def searchUsersViaUsername(username: str):
    connection = await getConnection()

    try:
        row = await connection.fetchrow(
            """
            SELECT userid, useremail, username, userrole, userpassword
            FROM "Users_DB"."Users"
            WHERE username = $1
            """,
            username
        )

        if row is None:
            return None
        
        return {
            "id": str(row["userid"]),
            "email": row["useremail"],
            "username": row["username"],
            "role": row["userrole"],
            "password": row["userpassword"]
        }
    finally:
        await connection.close()

#Delete functionaslity hard deletes the user row by UUID in the db
#Returns True if found and False if not found
async def deleteUserById(userId: str) -> bool:
    connection = await getConnection()

    try:
        row = await connection.fetchrow(
            """
            DELETE FROM "Users_DB"."Users"
            WHERE userid = $1::uuid
            RETURNING userid
            """,
            user_id
        )

        return row is not None # when the specified user is not found in the Db
    finally:
        await connection.close()

async def insertUser(email: str, username: str, role: str, hashedPassword: str):
    connection = await getConnection()

    try:
        row = await connection.fetchrow(
            """
            INSERT INTO "Users_DB"."Users"
            (useremail, username, userrole, userpassword)
            VALUES ($1, $2, $3, $4)
            RETURNING userid, useremail, username, userrole
            """,
            email, username, role, hashed_password
        )

        return {
            "id": str(row["userid"]),
            "email": row["useremail"],
            "username": row["username"],
            "role": row["userrole"]
        }
    finally:
        await connection.close()

def createToken(user: dict) ->str:
    expiry_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
        "exp": expiry_time
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM) # the signature is made from SECRET_KEY and ALGORITHM
    return token

# POST /api/login
@router.post("/login")
async def login(request: LoginRequest, response: Response):
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
                "message": "Invalid or missing password. Password must be atleast 12 characters, have an upper and lower case char and a special character"
            }
        )

    user = await searchUsersViaEmail(request.email.strip())

    if user is None:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": AMBIGUOUS_ERROR
            }
        )
    
    if not verifyPassword(request.password, user["password"]):
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": AMBIGUOUS_ERROR
            }
        )

    token = createToken(user)

    await updateUserJWTIssued(user["email"])

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=1800
    )

    return {
        "status" : "success",
        "message" : "Logged in successfully"
    }

# POST /api/register
@router.post("/register", status_code=201)
async def register(request: RegisterRequest, response: Response):
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
                "message": "Invalid or missing password. Password must be atleast 12 characters, have an upper and lower case char and a special character"
            }
        )

    if not request.username or not request.username.strip():
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Invalid or missing username"
            }
        )

    existingUser = await searchUsersViaEmail(request.email.strip())

    if existingUser is not None:
        return JSONResponse(
            status_code=409,
            content={
                "status": "error",
                "message": AMBIGUOUS_ERROR
            }
        )
    
    existingUsername = await searchUsersViaUsername(request.username.strip())
    
    if existingUsername is not None:
        return JSONResponse(
            status_code=409,
            content={
                "status": "error",
                "message": AMBIGUOUS_ERROR
            }
        )

    hashed_password = hashPassword(request.password)
    new_user = await insertUser(request.email.strip(), request.username.strip(), "USER", hashed_password)

    token = createToken(new_user)

    await updateUserJWTIssued(new_user["email"])

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=1800
    )

    return {
            "status": "success",
            "message": "Account created successfully"
    }

@router.post("/fetchUsers")
async def fetchUsers(request: Request):
    connection = None

    try:
        payload = verifyJWT(request)

        if payload.get("role") != "ADMIN":
            return JSONResponse(
                status_code=403,
                content={
                    "status":"error",
                    "message": "User unauthorized"
                }
            )
        
        connection = await getConnection()

        rows = await connection.fetch(
            """
            SELECT userid, username, userrole
            FROM "Users_DB"."Users"
            """
        )

        users = []

        for row in rows:
            users.append({
                "id":str(row["userid"]),
                "username":row["username"],
                "role": row["userrole"]
            })

        return JSONResponse(
            status_code=200,
            content={
                "status":"success",
                "users": users
            }
        )
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    finally:
        if connection is not None:
            await connection.close()

@router.post("/changeUserRole")
async def changeUserRole(
    changeRoleRequest: ChangeRoleRequest,
    request: Request
):
    connection = None
    try:
        payload = verifyJWT(request)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )

    if payload.get("role") != "ADMIN":
        return JSONResponse(
            status_code=403,
            content={
                "status":"error",
                "message": "User unauthorized"
            }
        )

    user_id = changeRoleRequest.userId
    newRole = changeRoleRequest.NewRole

    if not user_id or not newRole:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Missing userId or NewRole field."
            }
        )
    
    if payload.get("sub") == user_id:
        return JSONResponse(
            status_code=403,
            content={
                "status": "error",
               "message": "Not allowed to change own role"
           }
        )

    try:
        user_id = uuidlib.UUID(user_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={
                "status":"error",
                "message":"Invalid userId format."
            }
        )

    if newRole not in ["USER", "ADMIN", "INVESTIGATOR"]:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Invalid or missing NewRole field."
            }
        )
    
    try:
        connection = await getConnection()

        result = await connection.execute(
            """
            UPDATE "Users_DB"."Users"
            SET userrole = $1
            WHERE userid = $2
            """,
            newRole, user_id
        )

        if result == "UPDATE 0":
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "No user found with the provided user ID"
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "status":"success",
                "message": f"User role updated to {newRole} successfully"
            }
        )
    except asyncpg.PostgresError:
        return JSONResponse(
            status_code=500,
            content={
                "status":"error",
                "message":"Database error"
            }
        )
    finally:
        if connection is not None:
            await connection.close()

@router.delete("/users/{user_id}")
async def deleteUser(user_id: str, request: Request):
    try:
        #Verify the JWT for security
        payload = verifyJWT(request)
        user_id = user_id.strip()

        #Authorization. Only Admins can delete
        if payload.get("role") != "ADMIN":
            return JSONResponse(
                status_code = 403,
                content = {"status": "error", "message": "User is unauthorized."}
            )

        #Validate input. This rejects improper UUIDs before touching the DB
        if not validateUUID(user_id):
            return JSONResponse(
                status_code = 400,
                content = {"status": "error", "message": "Invalid User ID format."}
            )

        #An admin cannot delete themselves
        callerId = payload.get("sub")
        if callerId == user_id:
            return JSONResponse(
                status_code = 400,
                content = {"status": "error", "message": "Admins cannot delete themselves."}
            )

        #Now delete
        try:
            deleted = await deleteUserById(user_id)
        except asyncpg.PostgresError:
            return JSONResponse(
                status_code=500,
                content={
                    "status":"error",
                    "message":"Database error"
                }
            )
        
        #did the delete actually remove someone or quitly did nothing (no existing user or role was admin)
        if not deleted:
            return JSONResponse(
                status_code = 404,
                content = {
                    "status": "error", 
                    "message": "No user found with the provided ID."
                    }
            )

        return JSONResponse(
            status_code = 200,
            content = {
                "status": "success", 
                "message": "User deleted successfully."
                }
        )

        #safety net for unexpected errors
    except ValueError as e:
        #Errors from Jwt.
        return JSONResponse(
            status_code = 401,
            content = {
                "status": "error", 
                "message": str(e)
                }
        )

@router.post("/refreshToken")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error", 
                "message": "Not authenticated"
                }
        )

    if token == "":
        return JSONResponse(
            status_code=401,
            content={
                "status": "error", 
                "message": "Missing JWT token"
                }
        )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except ExpiredSignatureError:
        #I can make a new token here
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": False}
            )
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error", 
                    "message": INVALID_TOKEN
                    }
            )

    except JWTError:
        return JSONResponse(
                status_code=401,
                content={
                    "status": "error", 
                    "message": INVALID_TOKEN
                    }
            )
    
    expiry = payload.get("exp")

    if expiry is None:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error", 
                "message": "Token missing expiry"
                }
        )

    current_time = datetime.now(timezone.utc).timestamp()
    seconds_until_expiry = expiry - current_time

    if seconds_until_expiry > 60:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Token does not need refreshing"
            }
        )
    
    if "sub" not in payload or "username" not in payload or "role" not in payload:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": "Token missing required fields"
            }
        )
    
    user = {
        "id":payload["sub"],
        "username": payload["username"],
        "role": payload["role"]
    }

    new_token = createToken(user)

    try:
        await update_user_jwt_issued_via_user(user)
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status":"error",
                "message": "Failed to update token issue time"
            }
        )

    final_response = JSONResponse(
        status_code=200,
        content={
            "status":"success",
            "message": "Token refreshed"
        }
    )

    final_response.set_cookie(
        key=COOKIE_NAME,
        value=new_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=1800
    )
    
    return final_response