from models.base import BaseModel
from models.attackers import Attacker
from models.db_storage import PostgresStorage
from models.attacks import Attack
from models.attack_patterns import Pattern

storage = PostgresStorage()
storage.reload()
