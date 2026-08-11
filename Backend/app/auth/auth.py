from fastapi import APIRouter, HTTPException, Header, Response, Request, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import re as regex
import bcrypt
import uuid as uuidlib
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from datetime import datetime, timedelta, timezone
import asyncpg # This is the library for communicating with Postgres
from app.core.env import Postgres_Settings, Auth_Settings
from fastapi.security import APIKeyCookie

COOKIE_NAME = "JWT_token"
AMBIGUOUS_ERROR= "The email and/or password are invalid"
INVALID_TOKEN= "Invalid token"
NOT_AUTH = "Not authenticated"
EXPIRED_TOKEN = "Token has expired"

COOKIE_SCHEME = APIKeyCookie(
    name=COOKIE_NAME,
    auto_error=False
)

postgres_settings = Postgres_Settings()
auth_settings = Auth_Settings()

SECRET_KEY = auth_settings.JWT_SECRET
ALGORITHM = auth_settings.HASH

async def get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=postgres_settings.DB_USER,
        password=postgres_settings.DB_PASSWORD,
        database=postgres_settings.DB_NAME,
        host=postgres_settings.DB_HOST,
        port=postgres_settings.DB_PORT,
        ssl="require" if postgres_settings.DB_SSL else None,
    )

router = APIRouter(
    prefix="/api",
    tags=["Auth"]
)

class success_response(BaseModel):
    status: str = Field(..., examples=["success"])

class error_response(BaseModel):
    status: str = Field(..., examples=["error"])
    message: str = Field(..., examples=["Invalid token or database failure"])

def verify_jwt(request: Request) -> dict:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": NOT_AUTH
            }
        )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": EXPIRED_TOKEN
            }
        ) 

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": INVALID_TOKEN
            }
        )

# Validates an email. 
# Regex: One or more valid pre-@ characters (0-9, a-z, A-z,.,_,+,-), 
# an "@", one or more valid post-@ pre. characters (0-9, a-z, A-z,.,-), a ".",
# and finally two or more valid post. characters (A-Z and a-z).
def validate_email(email: str) -> bool:
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
def validate_uuid(value: str) -> bool:
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
def validate_password(password: str) -> bool:
    if not isinstance(password,str):
        return False
    
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$"
    return regex.match(pattern, password) is not None

# utf-8 encode the input string because bcrypt uses this, generate a salt, use the encoded string and salt to make the hash
# the hash is also utf-8 encoded so it needs to be decoded before it is returned
def hash_password(input: str) -> str:
    converted_string = input.encode("utf-8")
    salt =bcrypt.gensalt()
    hashed = bcrypt.hashpw(converted_string, salt)
    return hashed.decode("utf-8")

# utf-8 encodes both strings and uses bcrypt.checkpw to see if they are the same
def verify_password(password: str, hashed_password: str) ->bool:
    converted_password = password.encode("utf-8")
    converted_hash = hashed_password.encode("utf-8")
    return bcrypt.checkpw(converted_password,converted_hash)

# Reason for allowing None: FastAPI/Pydantic have their own error reponses which undesired.
# So we allow None and validate missing fields in the endpoint.
class login_request(BaseModel):
    email: str | None=None
    password: str | None=None

class RegisterRequest(login_request):
    username: str | None = None

class ChangeRoleRequest(BaseModel):
    userId: str | None = None
    NewRole: str | None = None

async def update_user_jwt_issued(email: str):
    connection = await get_connection()
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
    connection = await get_connection()
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
async def search_users_via_email(email:str):
    connection = await get_connection()
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
    
async def search_users_via_username(username: str):
    connection = await get_connection()

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
async def delete_user_by_id(user_id: str) -> bool:
    connection = await get_connection()

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

async def insert_user(
    email : str, 
    username : str, 
    role : str, 
    hashed_password : str
):

    connection = await get_connection()

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

def create_token(user: dict) ->str:
    expiry_time = datetime.now(timezone.utc) + timedelta(minutes=auth_settings.TOKEN_EXPIRE)

    payload = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
        "exp": expiry_time
    }

    token = jwt.encode(payload, auth_settings.JWT_SECRET, algorithm=auth_settings.HASH) # the signature is made from SECRET_KEY and ALGORITHM
    return token

# POST /api/login
@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Logs the user in and produces a JWT for the authorization of the user.",
    responses={
        200: {
            "description": "User successfully logged in",
            "model": success_response,
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Logged in successfully"
                    }
                }
            }
        },
        400:{
            "model" : error_response,
            "description": "Validation Error (Invalid email or failed password rules)",
            "content": {
                "application/json": {
                    "examples": {
                        "InvalidEmail": {
                            "summary": "Invalid or Missing Email",
                            "description": "Triggered when the email fails format validation.",
                            "value": {
                                "detail":{
                                    "status": "error",
                                    "message": "Invalid or missing email field. E.g of a valid email: veritas@lab.com"
                                }
                            }
                        },
                        "InvalidPassword": {
                            "summary": "Invalid or Missing Password",
                            "description": "Triggered when the password fails the rule validation.",
                            "value": {
                                "detail":{
                                    "status": "error",
                                    "message": "Invalid or missing password. Password must be atleast 12 characters, have an upper and lower case char and a special character"
                                }
                            }
                        }
                    }
                }
            }
        },
        401: {
            "model": error_response,
            "summary": "Password and/or Email were not found",
            "description": "Trigger when credentials used in the login were not found.",
            "content": {
                "application/json": {
                    "example": {
                        "detail":{
                            "status": "error",
                            "message": AMBIGUOUS_ERROR
                        }
                    }
                }
            }
        },
    }

)
async def login(request: login_request, response: Response):
    if not validate_email(request.email):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Invalid or missing email field. E.g of a valid email: veritas@lab.com"
            }
        )

    if not validate_password(request.password):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Invalid or missing password. Password must be atleast 12 characters, have an upper and lower case char and a special character"
            }
        )

    user = await search_users_via_email(request.email.strip())

    if user is None:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": AMBIGUOUS_ERROR
            }
        )
    
    if not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": AMBIGUOUS_ERROR
            }
        )

    token = create_token(user)

    await update_user_jwt_issued(user["email"])

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
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register User",
    description="Registers a new user account and produces a JWT for the authorization of the user.",
    responses={
        201: {
            "description": "Account successfully created",
            "model": success_response,
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Account created successfully"
                    }
                }
            }
        },

        400: {
            "description": "Invalid registration information",
            "model": error_response,
            "content": {
                "application/json": {
                    "examples": {
                        "InvalidEmail": {
                            "summary": "Invalid or missing email",
                            "description": "Triggered when the provided email address fails email validation.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Invalid or missing email field. E.g of a valid email: veritas@lab.com"
                                }
                            }
                        },

                        "InvalidPassword": {
                            "summary": "Invalid or missing password",
                            "description": "Triggered when the provided password does not meet the password requirements.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Invalid or missing password. Password must be atleast 12 characters, have an upper and lower case char and a special character"
                                }
                            }
                        },

                        "InvalidUsername": {
                            "summary": "Invalid or missing username",
                            "description": "Triggered when the username is missing, empty, or contains only whitespace.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Invalid or missing username"
                                }
                            }
                        }
                    }
                }
            }
        },

        409: {
            "description": "Email or username already exists",
            "content": {
                "application/json": {
                    "examples": {
                        "EmailAlreadyExists": {
                            "summary": "Email already registered",
                            "description": "Triggered when the provided email address is already associated with an account.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": AMBIGUOUS_ERROR
                                }
                            }
                        },

                        "UsernameAlreadyExists": {
                            "summary": "Username already registered",
                            "description": "Triggered when the provided username is already associated with an account.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": AMBIGUOUS_ERROR
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
async def register(request: RegisterRequest, response: Response):
    if not validate_email(request.email):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Invalid or missing email field. E.g of a valid email: veritas@lab.com"
            }
        )

    if not validate_password(request.password):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Invalid or missing password. Password must be atleast 12 characters, have an upper and lower case char and a special character"
            }
        )

    if not request.username or not request.username.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Invalid or missing username"
            }
        )

    existing_user = await search_users_via_email(request.email.strip())

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "status": "error",
                "message": AMBIGUOUS_ERROR
            }
        )
    
    existing_username = await search_users_via_username(request.username.strip())
    
    if existing_username is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "status": "error",
                "message": AMBIGUOUS_ERROR
            }
        )

    hashed_password = hash_password(request.password)
    new_user = await insert_user(
        request.email.strip(), 
        request.username.strip(), 
        "USER", 
        hashed_password
    )

    token = create_token(new_user)

    await update_user_jwt_issued(new_user["email"])

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

@router.post(
    "/fetchUsers",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Fetch Users",
    description="Returns all registered users if the user is an admin.",
    responses={
        200: {
            "description": "Users successfully fetched",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "users": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "username": "example_user",
                                "role": "USER"
                            },
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "username": "example_investigator",
                                "role": "INVESTIGATOR"
                            }
                        ]
                    }
                }
            }
        },

        401: {
            "description": "Authentication failed",
            "content": {
                "application/json": {
                    "examples": {
                        "InvalidToken": {
                            "summary": "Invalid JWT",
                            "description": "Triggered when JWT verification fails.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": INVALID_TOKEN
                                }
                            }
                        },

                        "MissingToken": {
                            "summary": "Missing JWT",
                            "description": "Triggered when the request does not contain a valid authentication token.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": NOT_AUTH
                                }
                            }
                        },

                        "ExpiredToken": {
                            "summary": "Expired JWT",
                            "description": "Triggered when the provided JWT has expired.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": EXPIRED_TOKEN
                                }
                            }
                        }
                    }
                }
            }
        },

        403: {
            "description": "User does not have permission to access this endpoint",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "User unauthorized"
                        }
                    }
                }
            }
        }
    }

)
async def fetch_users(request: Request):
    connection = None

    try:
        payload = verify_jwt(request)

        if payload.get("role") != "ADMIN":
            raise HTTPException(
                status_code=403,
                detail={
                    "status":"error",
                    "message": "User unauthorized"
                }
            )
        
        connection = await get_connection()

        rows = await connection.fetch(
            """
            SELECT userid, username, userrole
            FROM "Users_DB"."Users"
            """
        )

        users = []

        for row in rows:
            users.append(
                {
                    "id":str(row["userid"]),
                    "username":row["username"],
                    "role": row["userrole"]
                }
            )

        return {
            "status":"success",
            "users": users
        }
    finally:
        if connection is not None:
            await connection.close()

@router.post(
    "/changeUserRole",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Change User Role",
    description="Changes the role of a registered user. The endpoint requires a valid JWT and can only be accessed by an ADMIN user. An admin cannot change their own role.",
    responses={
        200: {
            "description": "User role successfully updated",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "User role updated to INVESTIGATOR successfully"
                    }
                }
            }
        },

        400: {
            "description": "Invalid role change request",
            "content": {
                "application/json": {
                    "examples": {
                        "MissingFields": {
                            "summary": "Missing user ID or role",
                            "description": "Triggered when userId or NewRole is missing.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Missing userId or NewRole field."
                                }
                            }
                        },

                        "InvalidUserId": {
                            "summary": "Invalid user ID",
                            "description": "Triggered when userID is not a valid UUID.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Invalid userId format."
                                }
                            }
                        },

                        "InvalidRole": {
                            "summary": "Invalid new role",
                            "description": "Triggered when NewRole is not USER, ADMIN, or INVESTIGATOR.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Invalid or missing NewRole field."
                                }
                            }
                        }
                    }
                }
            }
        },

        401: {
            "description": "Authentication failed",
            "content": {
                "application/json": {
                    "examples": {
                        "MissingToken": {
                            "summary": "Missing JWT",
                            "description": "Triggered when no JWT authentication cookie is provided.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": NOT_AUTH
                                }
                            }
                        },

                        "ExpiredToken": {
                            "summary": "Expired JWT",
                            "description": "Triggered when the provided JWT has expired.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": EXPIRED_TOKEN
                                }
                            }
                        },

                        "InvalidToken": {
                            "summary": "Invalid Token",
                            "description": "Triggered when JWT verification fails.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": INVALID_TOKEN
                                }
                            }
                        }
                    }
                }
            }
        },

        403: {
            "description": "User does not have permission to perform this action",
            "content": {
                "application/json": {
                    "examples": {
                        "UnauthorizedUser": {
                            "summary": "User is not an admin",
                            "description": "Triggered when the authenticated user is not an ADMIN.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "User unauthorized"
                                }
                            }
                        },

                        "ChangeOwnRole": {
                            "summary": "Attempt to change own role",
                            "description": "Triggered when an admin tries to change their own role.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Not allowed to change own role"
                                }
                            }
                        }
                    }
                }
            }
        },

        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "No user found with the provided user ID"
                        }
                    }
                }
            }
        },

        500: {
            "description": "Database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "Database error"
                        }
                    }
                }
            }
        }
    }
)
async def change_user_role(change_role_request: ChangeRoleRequest, request: Request):
    payload = verify_jwt(request)

    if payload.get("role") != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail={
                "status":"error",
                "message": "User unauthorized"
            }
        )

    user_id = change_role_request.userId
    new_role = change_role_request.NewRole

    if not user_id or not new_role:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Missing userId or NewRole field."
            }
        )
    
    if payload.get("sub") == user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "status": "error",
                "message": "Not allowed to change own role"
            }
        )

    try:
        user_id = uuidlib.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "status":"error",
                "message":"Invalid userId format."
            }
        )

    if new_role not in ["USER", "ADMIN", "INVESTIGATOR"]:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Invalid or missing NewRole field."
            }
        )
    
    try:
        connection = await get_connection()

        result = await connection.execute(
            """
            UPDATE "Users_DB"."Users"
            SET userrole = $1
            WHERE userid = $2
            """,
            new_role, user_id
        )

        if result == "UPDATE 0":
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": "No user found with the provided user ID"
                }
            )

        return {
            "status":"success",
            "message": f"User role updated to {new_role} successfully"
        }
    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status":"error",
                "message":"Database error"
            }
        )
    finally:
        if connection is not None:
            await connection.close()

@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Delete User",
    description="Deletes a registered user by their user ID. Only an admin can use this endpoint and they cannot delete themselves.",
    responses={
        200: {
            "description": "User successfully deleted",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "User deleted successfully."
                    }
                }
            }
        },

        400: {
            "description": "Invalid delete request",
            "content": {
                "application/json": {
                    "examples": {
                        "InvalidUserId": {
                            "summary": "Invalid user ID",
                            "description": "Triggered when the provided user ID is not a valid UUID.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Invalid User ID format."
                                }
                            }
                        },

                        "DeleteSelf": {
                            "summary": "Admin tries to delete themselves",
                            "description": "Triggered when an admin tries to delete their own account.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Admins cannot delete themselves."
                                }
                            }
                        }
                    }
                }
            }
        },

        401: {
            "description": "Authentication failed",
            "content": {
                "application/json": {
                    "examples": {
                        "MissingToken": {
                            "summary": "Missing JWT",
                            "description": "Triggered when no JWT authentication cookie is provided.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": NOT_AUTH
                                }
                            }
                        },

                        "ExpiredToken": {
                            "summary": "Expired JWT",
                            "description": "Triggered when the provided JWT has expired.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": EXPIRED_TOKEN
                                }
                            }
                        },

                        "InvalidToken": {
                            "summary": "Invalid JWT",
                            "description": "Triggered when JWT verification fails.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": INVALID_TOKEN
                                }
                            }
                        }
                    }
                }
            }
        },

        403: {
            "description": "User does not have permission to delete users",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "User is unauthorized."
                        }
                    }
                }
            }
        },

        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "No user found with the provided ID."
                        }
                    }
                }
            }
        },

        500 : {
            "description": "Database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "Database error"
                        }
                    }
                }
            }
        }
    }
)
async def delete_user(user_id: str, request: Request): 
    #Verify the JWT for security
    payload = verify_jwt(request)
    user_id = user_id.strip()

    #Authorization. Only Admins can delete
    if payload.get("role") != "ADMIN":
        raise HTTPException(
            status_code = 403,
            detail= {
                "status": "error", 
                "message": "User is unauthorized."
            }
        )

    #Validate input. This rejects improper UUIDs before touching the DB
    if not validate_uuid(user_id):
        raise HTTPException(
            status_code = 400,
            detail= {
                "status": "error",
                "message": "Invalid User ID format."
            }
        )

    #An admin cannot delete themselves
    caller_id = payload.get("sub")
    if caller_id == user_id:
        raise HTTPException(
            status_code = 400,
            detail= {
                "status": "error",
                "message": "Admins cannot delete themselves."
            }
        )

    #Now delete
    try:
        deleted = await delete_user_by_id(user_id)
    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status":"error",
                "message":"Database error"
            }
        )
        
    #did the delete actually remove someone or quitly did nothing (no existing user or role was admin)
    if not deleted:
        raise HTTPException(
            status_code = 404,
            detail= {
                "status": "error", 
                "message": "No user found with the provided ID."
            }
        )

    return {
        "status": "success", 
        "message": "User deleted successfully."
    }

@router.post(
    "/refreshToken",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Refresh JWT Token",
    description="Refreshes the user's JWT when the token has expired or has 1 minute left. Otherwise, no token is created.",
    responses={
        200: {
            "description": "Token is valid or successfully refreshed",
            "content": {
                "application/json": {
                    "examples": {
                        "TokenNotRefreshed": {
                            "summary": "Token does not need refreshing",
                            "description": "Triggered when the current JWT has more than 1 minute left before expiry.",
                            "value": {
                                "status": "success",
                                "message": "Token does not need refreshing"
                            }
                        },

                        "TokenRefreshed": {
                            "summary": "Token successfully refreshed",
                            "description": "Triggered when a new JWT is generated and stored in the authentication cookie.",
                            "value": {
                                "status": "success",
                                "message": "Token refreshed"
                            }
                        }

                    }
                }
            }
        },

        401: {
            "description": "Token authentication or validation failed",
            "content": {
                "application/json": {
                    "examples": {
                        "MissingToken": {
                            "summary": "Missing JWT token",
                            "description": "Triggered when the authentication cookie exists but contains an empty JWT.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Missing JWT token"
                                }
                            }
                        },

                        "NotAuthenticated": {
                            "summary": "Not authenticated",
                            "description": "Triggered when the authentication cookie is not provided.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Not authenticated"
                                }
                            }
                        },

                        "InvalidToken": {
                            "summary": "Invalid JWT",
                            "description": "Triggered when the JWT cannot be decoded or fails validation.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": INVALID_TOKEN
                                }
                            }
                        },

                        "MissingExpiry": {
                            "summary": "Token missing expiry",
                            "description": "Triggered when the JWT does not contain an exp field.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Token missing expiry"
                                }
                            }
                        },

                        "MissingRequiredFields": {
                            "summary": "Token missing required fields",
                            "description": "Triggered when the JWT does not contain sub, username, or role.",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Token missing required fields"
                                }
                            }
                        }
                    }
                }
            }
        },

        500: {
            "description": "Failed to update token issue time",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "Failed to update token issue time"
                        }
                    }
                }
            }
        }
    }
)
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get(COOKIE_NAME)

    if token == "":
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error", 
                "message": "Missing JWT token"
            }
        )

    if not token:
        raise HTTPException (
            status_code=401,
            detail={
                "status": "error", 
                "message": "Not authenticated"
            }
        )


    try:
        payload = jwt.decode(
            token,
            auth_settings.JWT_SECRET,
            algorithms=[auth_settings.HASH]
        )

    except ExpiredSignatureError:
        #I can make a new token here
        try:
            payload = jwt.decode(
                token,
                auth_settings.JWT_SECRET,
                algorithms=[auth_settings.HASH],
                options={"verify_exp": False}
            )
        except JWTError:
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "error", 
                    "message": INVALID_TOKEN
                }
            )

    except JWTError:
        raise HTTPException(
                status_code=401,
                detail={
                    "status": "error", 
                    "message": INVALID_TOKEN
                }
            )
    
    expiry = payload.get("exp")

    if expiry is None:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error", 
                "message": "Token missing expiry"
            }
        )

    current_time = datetime.now(timezone.utc).timestamp()
    seconds_until_expiry = expiry - current_time

    if seconds_until_expiry > 60:
        return {
            "status": "success",
            "message": "Token does not need refreshing"
        }
        
    
    if "sub" not in payload or "username" not in payload or "role" not in payload:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": "Token missing required fields"
            }
        )
    
    user = {
        "id":payload["sub"],
        "username": payload["username"],
        "role": payload["role"]
    }

    new_token = create_token(user)

    try:
        await update_user_jwt_issued_via_user(user)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "status":"error",
                "message": "Failed to update token issue time"
            }
        )

    response.set_cookie(
        key=COOKIE_NAME,
        value=new_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=1800
    )

    return {
        "status":"success",
        "message": "Token refreshed"
    }
