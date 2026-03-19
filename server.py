import socket
import threading
import time

from game_logic import DaraGame, PLAYER_1, PLAYER_2
from protocol import send_json, recv_json

HOST = "0.0.0.0"
PORT = 5000

game = DaraGame()
clients = {}
clients_lock = threading.Lock()
game_lock = threading.Lock()


def broadcast(data: dict):
    disconnected = []

    with clients_lock:
        current_clients = list(clients.items())

    for player_id, conn in current_clients:
        try:
            send_json(conn, data)
        except Exception as e:
            print(f"[SERVIDOR] Falha ao enviar para jogador {player_id}: {e}")
            disconnected.append(player_id)

    if disconnected:
        with clients_lock:
            for player_id in disconnected:
                conn = clients.pop(player_id, None)
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass


def send_to_player(player_id: int, data: dict):
    with clients_lock:
        conn = clients.get(player_id)

    if conn is None:
        return

    try:
        send_json(conn, data)
    except Exception as e:
        print(f"[SERVIDOR] Erro ao enviar para jogador {player_id}: {e}")


def send_state(message: str = ""):
    payload = {
        "type": "state",
        "game": game.serialize(),
        "message": message,
    }
    broadcast(payload)


def connected_players_count() -> int:
    with clients_lock:
        return len(clients)


def handle_disconnect(player_id: int):
    with game_lock:
        if game.phase != "finished" and connected_players_count() >= 1:
            game.resign(player_id)
            winner = game.winner

            payload = {
                "type": "state",
                "game": game.serialize(),
                "message": f"Jogador {player_id} desconectou. Jogador {winner} venceu.",
            }

            broadcast(payload)


def process_message(player_id: int, msg: dict):
    global game

    print(f"[SERVIDOR] Recebido do jogador {player_id}: {msg}")

    msg_type = msg.get("type")

    with game_lock:
        if msg_type == "chat":
            text = str(msg.get("text", "")).strip()
            if text:
                broadcast({
                    "type": "chat",
                    "player": player_id,
                    "text": text
                })
            return

        if game.phase == "finished":
            send_to_player(player_id, {
                "type": "info",
                "message": "A partida já foi encerrada."
            })
            return

        if msg_type == "resign":
            game.resign(player_id)
            send_state(f"Jogador {player_id} desistiu. Jogador {game.winner} venceu.")
            return

        if msg_type == "place_piece":
            row = msg.get("row")
            col = msg.get("col")

            ok, feedback = game.place_piece(player_id, row, col)
            print(f"[SERVIDOR] place_piece -> ok={ok}, feedback={feedback}")
            send_state(feedback)
            return

        if msg_type == "move_piece":
            from_row = msg.get("from_row")
            from_col = msg.get("from_col")
            to_row = msg.get("to_row")
            to_col = msg.get("to_col")

            ok, feedback = game.move_piece(player_id, from_row, from_col, to_row, to_col)
            print(f"[SERVIDOR] move_piece -> ok={ok}, feedback={feedback}")
            send_state(feedback)
            return

        if msg_type == "capture_piece":
            row = msg.get("row")
            col = msg.get("col")

            ok, feedback = game.capture_piece(player_id, row, col)
            print(f"[SERVIDOR] capture_piece -> ok={ok}, feedback={feedback}")
            send_state(feedback)
            return

        send_to_player(player_id, {
            "type": "info",
            "message": "Mensagem desconhecida enviada ao servidor."
        })


def client_thread(conn: socket.socket, addr, player_id: int):
    print(f"[SERVIDOR] Jogador {player_id} conectado: {addr}")

    try:
        send_json(conn, {
            "type": "welcome",
            "player_id": player_id,
            "message": f"Você é o Jogador {player_id}."
        })

        if player_id == PLAYER_1:
            send_json(conn, {
                "type": "info",
                "message": "Aguardando o segundo jogador conectar..."
            })

        elif player_id == PLAYER_2:
            broadcast({
                "type": "info",
                "message": "Os dois jogadores conectaram. A partida começou."
            })
            send_state("Partida iniciada. Jogador 1 começa.")

        buffer = ""

        while True:
            data = conn.recv(4096)
            if not data:
                print(f"[SERVIDOR] Conexão encerrada pelo jogador {player_id}.")
                break

            buffer += data.decode("utf-8")

            while True:
                msg, buffer = recv_json(buffer)
                if msg is None:
                    break
                process_message(player_id, msg)

    except Exception as e:
        print(f"[SERVIDOR] Erro com jogador {player_id}: {e}")

    finally:
        print(f"[SERVIDOR] Finalizando conexão do jogador {player_id}.")

        with clients_lock:
            existing_conn = clients.pop(player_id, None)

        if existing_conn:
            try:
                existing_conn.close()
            except Exception:
                pass

        handle_disconnect(player_id)


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(2)

    print(f"[SERVIDOR] Servidor iniciado em {HOST}:{PORT}")
    print("[SERVIDOR] Aguardando até 2 jogadores...")

    player_order = [PLAYER_1, PLAYER_2]

    while True:
        with clients_lock:
            if len(clients) >= 2:
                pass

        if connected_players_count() < 2:
            conn, addr = server.accept()

            with clients_lock:
                if len(clients) >= 2:
                    try:
                        send_json(conn, {
                            "type": "info",
                            "message": "Partida já possui 2 jogadores conectados."
                        })
                    except Exception:
                        pass
                    conn.close()
                    continue

                player_id = player_order[len(clients)]
                clients[player_id] = conn

            t = threading.Thread(
                target=client_thread,
                args=(conn, addr, player_id),
                daemon=True
            )
            t.start()
        else:
            time.sleep(0.2)


if __name__ == "__main__":
    main()