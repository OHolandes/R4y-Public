import sqlite3
from typing import Tuple, List


__db__ = "r4y.db"


def __execute(cmd: str) -> None:
    conn = sqlite3.connect(__db__)
    cur = conn.cursor()
    cur.execute(cmd)
    conn.commit()
    conn.close()


def __select(camp: str = "*") -> List[Tuple]:
    conn = sqlite3.connect(__db__)
    cur = conn.cursor()
    cur.execute(f"SELECT {camp} FROM servers")
    data = cur.fetchall()
    conn.commit()
    conn.close()
    return data


def __search_serv(_id: int) -> List[Tuple]:
    conn = sqlite3.connect(__db__)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM servers WHERE id={_id}")
    data = cur.fetchall()
    conn.commit()
    conn.close()
    return data


def create_table() -> None:
    __execute("CREATE TABLE servers (id integer, channel integer, voice integer)")


def add_serv(serv_id: int, id_channel: int, id_voice: int) -> None:
    __execute(f"INSERT INTO servers (id, channel, voice) VALUES ({serv_id}, {id_channel}, {id_voice})")


def get_all() -> List[Tuple]:
    return __select()


def get_serv(_id: int) -> List[Tuple]:
    return __search_serv(_id)


def get_ids() -> List[Tuple]:
    return __select("id")


def get_channels() -> List[Tuple]:
    return __select("channel")


def get_voices() -> List[Tuple]:
    return __select("voice")


def update(serv_id: int, chn_id: int, voice_id: int):
    __execute(f"UPDATE servers SET channel={chn_id} voice={voice_id} WHERE id={serv_id}")


def _del(serv_id:int):
    __execute(f"DELETE FROM servers WHERE id={serv_id}")


if __name__ == "__main__":
    ...