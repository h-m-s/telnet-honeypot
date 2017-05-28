from postgres_db.models.base import BaseModel
from postgres_db.models.attackers import Attacker
from postgres_db.models.db_storage import PostgresStorage
from postgres_db.models.attacks import Attack
from postgres_db.models.attack_patterns import Pattern

storage = PostgresStorage()
storage.reload()
