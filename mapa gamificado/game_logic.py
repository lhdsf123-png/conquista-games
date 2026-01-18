import sqlite3
import random

def get_attack_bonus(user):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("SELECT SUM(attack_bonus) FROM troops WHERE user=?", (user,))
    res = c.fetchone()
    conn.close()
    return res[0] if res and res[0] else 0

def get_defense_bonus(territory_id):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("SELECT defense FROM territories WHERE id=?", (territory_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

def battle(attacker, defender, territory_id):
    attack_power = 10 + get_attack_bonus(attacker)
    defense_power = get_defense_bonus(territory_id) + get_attack_bonus(defender)

    attack_roll = attack_power + random.randint(0, 5)
    defense_roll = defense_power + random.randint(0, 5)

    if attack_roll > defense_roll:
        conn = sqlite3.connect("game.db")
        c = conn.cursor()
        c.execute("UPDATE territories SET user=? WHERE id=?", (attacker, territory_id))
        conn.commit()
        conn.close()
        return {"result": f"{attacker} venceu e conquistou o território!"}
    else:
        return {"result": f"{defender} defendeu com sucesso o território!"}