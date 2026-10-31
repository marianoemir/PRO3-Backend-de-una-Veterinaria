from dotenv import load_dotenv
import os
import sys

load_dotenv()


class Settings:
    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        if not self.DATABASE_URL:
            print(
                "FATAL: DATABASE_URL no está definida. "
                "Copiá env.example a .env y configurá la conexión."
            )
            sys.exit(1)


settings = Settings()