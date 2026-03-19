import json

def send_json(sock, data: dict):
    message = json.dumps(data, ensure_ascii=False) + "\n"
    sock.sendall(message.encode("utf-8"))


def recv_json(buffer: str):
    """
    Recebe dados acumulados em string e retorna:
    - objeto json (ou None se ainda incompleto)
    - buffer restante
    """
    if "\n" not in buffer:
        return None, buffer

    line, buffer = buffer.split("\n", 1)
    if not line.strip():
        return None, buffer

    return json.loads(line), buffer