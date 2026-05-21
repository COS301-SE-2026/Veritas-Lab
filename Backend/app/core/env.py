import os
from dotenv import load_dotenv

load_dotenv()

class ENVLoader:

    def getRequiredEnv(self, name: str) -> str:
        value = os.getenv(name)

        if value is None or value.strip() == "":
            raise RuntimeError(f"Missing required environment variable: {name}")

        return value

    def getOptionalEnv(self, name: str, default: str) -> str:
        value = os.getenv(name)

        if value is None or value.strip() == "":
            return default

        return value

    def getRequiredIntEnv(self, name: str) -> int:
        value = self.getRequiredEnv(name)

        try:
            return int(value)
        except ValueError:
            raise RuntimeError(f"{name} must be a valid integer")