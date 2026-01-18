import sqlite3
import time

def init_db():
    conn = sqlite3.connect("game.db")
    c = conn.cursor()

    # Territórios
    c.execute("""CREATE TABLE IF NOT EXISTS territories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT,
                    lat REAL,
                    lon REAL,
                    building TEXT,
                    poi TEXT, -- ponto de interesse (parque, restaurante, etc.)
                    defense INTEGER DEFAULT 0,
                    last_update REAL DEFAULT 0
                )""")

    # Usuários
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    gold INTEGER DEFAULT 100,
                    wood INTEGER DEFAULT 50,
                    stone INTEGER DEFAULT 50,
                    energy INTEGER DEFAULT 20
                )""")

    # Tropas
    c.execute("""CREATE TABLE IF NOT EXISTS troops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT,
                    type TEXT,
                    attack_bonus INTEGER
                )""")

    conn.commit()
    conn.close()

# ------------------ Usuários ------------------

def add_user(name):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def get_user_resources(user):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("SELECT gold, wood, stone, energy FROM users WHERE name=?", (user,))
    res = c.fetchone()
    conn.close()
    return {"gold": res[0], "wood": res[1], "stone": res[2], "energy": res[3]} if res else {}

# ------------------ Territórios ------------------

def can_afford(user, cost):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("SELECT gold, wood, stone, energy FROM users WHERE name=?", (user,))
    res = c.fetchone()
    conn.close()
    return res and res[0] >= cost.get("gold",0) and res[1] >= cost.get("wood",0) and res[2] >= cost.get("stone",0) and res[3] >= cost.get("energy",0)

def spend_resources(user, cost):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("UPDATE users SET gold=gold-?, wood=wood-?, stone=stone-?, energy=energy-? WHERE name=?",
              (cost.get("gold",0), cost.get("wood",0), cost.get("stone",0), cost.get("energy",0), user))
    conn.commit()
    conn.close()

def add_territory(user, lat, lon, poi=None):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()

    # custo para conquistar lote vazio
    cost = {"gold": 50, "wood": 20}

    # verifica se já existe território
    c.execute("SELECT id FROM territories WHERE lat=? AND lon=?", (lat, lon))
    if c.fetchone():
        conn.close()
        return False

    # verifica se o jogador tem recursos
    if not can_afford(user, cost):
        conn.close()
        return False

    # desconta recursos e conquista
    spend_resources(user, cost)
    c.execute("INSERT INTO territories (user, lat, lon, poi) VALUES (?, ?, ?, ?)", (user, lat, lon, poi))
    conn.commit()
    conn.close()
    return True

def build_on_territory(territory_id, building):
    defense_bonus = {"muralha": 5, "torre": 10}.get(building, 0)
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("UPDATE territories SET building=?, defense=defense+? WHERE id=?", (building, defense_bonus, territory_id))
    conn.commit()
    conn.close()

def build_with_cost(user, territory_id, building):
    costs = {
        "casa": {"wood":50, "stone":20},
        "fabrica": {"gold":100, "energy":50},
        "serraria": {"gold":80, "stone":30},
        "pedreira": {"gold":70, "wood":40},
        "usina": {"gold":120, "stone":50}
    }
    cost = costs.get(building, {})
    if can_afford(user, cost):
        spend_resources(user, cost)
        build_on_territory(territory_id, building)
        return True, f"{building} construída!"
    else:
        return False, "Recursos insuficientes!"

def update_resources(user):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("SELECT id, building, poi, last_update FROM territories WHERE user=?", (user,))
    territories = c.fetchall()

    for tid, building, poi, last_update in territories:
        now = time.time()
        elapsed = int(now - last_update) // 60  # minutos passados
        if elapsed > 0:
            # produção por construção
            if building == "fabrica":
                c.execute("UPDATE users SET gold=gold+? WHERE name=?", (elapsed * 10, user))
            elif building == "serraria":
                c.execute("UPDATE users SET wood=wood+? WHERE name=?", (elapsed * 5, user))
            elif building == "pedreira":
                c.execute("UPDATE users SET stone=stone+? WHERE name=?", (elapsed * 7, user))
            elif building == "usina":
                c.execute("UPDATE users SET energy=energy+? WHERE name=?", (elapsed * 3, user))

            # produção por ponto de interesse
            if poi == "parque":
                c.execute("UPDATE users SET energy=energy+? WHERE name=?", (elapsed * 2, user))
            elif poi == "restaurante":
                c.execute("UPDATE users SET gold=gold+? WHERE name=?", (elapsed * 5, user))
            elif poi == "pedreira_natural":
                c.execute("UPDATE users SET stone=stone+? WHERE name=?", (elapsed * 4, user))

            # atualizar timestamp
            c.execute("UPDATE territories SET last_update=? WHERE id=?", (now, tid))

    conn.commit()
    conn.close()

# ------------------ Tropas ------------------

def train_troop(user, troop_type):
    costs = {
        "soldado": {"gold":50, "wood":20},
        "arqueiro": {"gold":70, "wood":30},
        "cavaleiro": {"gold":100, "stone":50, "energy":30}
    }
    bonuses = {"soldado":5, "arqueiro":7, "cavaleiro":12}
    cost = costs.get(troop_type, {})
    if can_afford(user, cost):
        spend_resources(user, cost)
        conn = sqlite3.connect("game.db")
        c = conn.cursor()
        c.execute("INSERT INTO troops (user, type, attack_bonus) VALUES (?, ?, ?)", (user, troop_type, bonuses[troop_type]))
        conn.commit()
        conn.close()
        return True, f"{troop_type} treinado!"
    else:
        return False, "Recursos insuficientes!"