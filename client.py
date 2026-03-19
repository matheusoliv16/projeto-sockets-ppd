import socket
import threading
import tkinter as tk
from tkinter import messagebox

from protocol import send_json, recv_json

HOST = "127.0.0.1"
PORT = 5000

ROWS = 5
COLS = 6

EMPTY = 0
PLAYER_1 = 1
PLAYER_2 = 2

BOARD_MARGIN = 50
NODE_GAP = 85
PIECE_RADIUS = 22
NODE_RADIUS = 5


class DaraClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Dara - Cliente")
        self.root.configure(bg="#f5f1e8")
        self.root.resizable(False, False)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))

        self.player_id = None
        self.game_state = None
        self.selected_piece = None
        self.running = True
        self.buffer = ""
        self.endgame_shown = False

        self.canvas_width = BOARD_MARGIN * 2 + NODE_GAP * (COLS - 1)
        self.canvas_height = BOARD_MARGIN * 2 + NODE_GAP * (ROWS - 1)

        self.build_ui()
        self.draw_board()

        self.receiver_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receiver_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        container = tk.Frame(self.root, bg="#f5f1e8")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        self.title_label = tk.Label(
            container,
            text="Conectando...",
            font=("Arial", 18, "bold"),
            bg="#f5f1e8",
            fg="#111111",
        )
        self.title_label.pack(pady=(0, 8))

        self.phase_label = tk.Label(
            container,
            text="Fase: -",
            font=("Arial", 11, "bold"),
            bg="#f5f1e8",
            fg="#333333",
        )
        self.phase_label.pack()

        self.turn_label = tk.Label(
            container,
            text="Turno: -",
            font=("Arial", 11),
            bg="#f5f1e8",
            fg="#333333",
        )
        self.turn_label.pack(pady=(2, 4))

        self.status_label = tk.Label(
            container,
            text="Aguardando início da partida...",
            font=("Arial", 10),
            bg="#f5f1e8",
            fg="#555555",
            wraplength=700,
            justify="center",
        )
        self.status_label.pack(pady=(0, 12))

        self.canvas = tk.Canvas(
            container,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#f5f1e8",
            highlightthickness=0,
        )
        self.canvas.pack(pady=(0, 16))
        self.canvas.bind("<Button-1>", self.on_board_click)

        legend_frame = tk.Frame(container, bg="#f5f1e8")
        legend_frame.pack(pady=(0, 10))

        tk.Label(
            legend_frame,
            text="● Jogador 1",
            font=("Arial", 10, "bold"),
            fg="black",
            bg="#f5f1e8",
        ).pack(side="left", padx=12)

        tk.Label(
            legend_frame,
            text="○ Jogador 2",
            font=("Arial", 10, "bold"),
            fg="#1d4ed8",
            bg="#f5f1e8",
        ).pack(side="left", padx=12)

        chat_outer = tk.Frame(container, bg="#d9d4c7", bd=1, relief="solid")
        chat_outer.pack(fill="both", expand=True)

        chat_header = tk.Label(
            chat_outer,
            text="Chat / Eventos da partida",
            font=("Arial", 11, "bold"),
            bg="#d9d4c7",
            fg="#222222",
            anchor="w",
            padx=10,
            pady=6,
        )
        chat_header.pack(fill="x")

        self.chat_text = tk.Text(
            chat_outer,
            width=70,
            height=10,
            state="disabled",
            font=("Consolas", 10),
            bg="white",
            fg="#222222",
            bd=0,
            padx=10,
            pady=8,
        )
        self.chat_text.pack(fill="both", expand=True)

        send_frame = tk.Frame(container, bg="#f5f1e8")
        send_frame.pack(fill="x", pady=(10, 0))

        self.entry_message = tk.Entry(send_frame, font=("Arial", 10))
        self.entry_message.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_message.bind("<Return>", lambda event: self.send_chat())

        self.btn_send = tk.Button(
            send_frame,
            text="Enviar",
            command=self.send_chat,
            bg="#2563eb",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
        )
        self.btn_send.pack(side="left", padx=(0, 8))

        self.btn_resign = tk.Button(
            send_frame,
            text="Desistir",
            command=self.resign,
            bg="#dc2626",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
        )
        self.btn_resign.pack(side="left")

    def normalize_game_state(self, state: dict) -> dict:
        pieces_to_place = state.get("pieces_to_place", {})
        pieces_on_board = state.get("pieces_on_board", {})

        def normalize_player_dict(d):
            return {
                1: d.get(1, d.get("1", 0)),
                2: d.get(2, d.get("2", 0)),
            }

        state["pieces_to_place"] = normalize_player_dict(pieces_to_place)
        state["pieces_on_board"] = normalize_player_dict(pieces_on_board)

        for key in ("capture_pending_for", "winner", "current_turn"):
            value = state.get(key)
            if isinstance(value, str) and value.isdigit():
                state[key] = int(value)

        return state

    def receive_loop(self):
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break

                self.buffer += data.decode("utf-8")

                while True:
                    msg, self.buffer = recv_json(self.buffer)
                    if msg is None:
                        break
                    self.root.after(0, self.handle_message, msg)

            except Exception:
                break

        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass

    def handle_message(self, msg: dict):
        msg_type = msg.get("type")

        if msg_type == "welcome":
            self.player_id = msg.get("player_id")
            self.title_label.config(text=f"Você é o Jogador {self.player_id}")
            return

        if msg_type == "info":
            self.append_chat(msg.get("message", ""))
            return

        if msg_type == "chat":
            player = msg.get("player")
            text = msg.get("text", "")
            self.append_chat(f"Jogador {player}: {text}")
            return

        if msg_type == "state":
            state = msg.get("game")
            message = msg.get("message", "")

            if state:
                self.game_state = self.normalize_game_state(state)
                self.update_ui()

            if message:
                self.append_chat(message)

    def update_ui(self):
        if not self.game_state:
            return

        phase = self.game_state["phase"]
        current_turn = self.game_state["current_turn"]
        winner = self.game_state["winner"]
        pieces_to_place = self.game_state["pieces_to_place"]
        pieces_on_board = self.game_state["pieces_on_board"]
        capture_pending_for = self.game_state.get("capture_pending_for")

        phase_map = {
            "placement": "Colocação",
            "movement": "Movimentação",
            "capture": "Captura",
            "finished": "Encerrado",
        }

        self.phase_label.config(text=f"Fase: {phase_map.get(phase, phase)}")
        self.turn_label.config(text=f"Turno atual: Jogador {current_turn}")

        if phase == "placement":
            status = (
                f"Fase inicial: cada jogador ainda está colocando suas peças. "
                f"Restam para colocar — J1: {pieces_to_place[1]} | J2: {pieces_to_place[2]}."
            )
        elif phase == "movement":
            status = (
                f"Todas as peças já foram colocadas. Agora mova uma peça sua para uma interseção adjacente vazia."
            )
        elif phase == "capture":
            if capture_pending_for == self.player_id:
                status = "Você formou uma linha de 3. Clique em uma peça adversária para capturar."
            else:
                status = "O adversário formou uma linha de 3 e precisa capturar uma peça."
        else:
            status = (
                f"Partida encerrada. Peças no tabuleiro — J1: {pieces_on_board[1]} | J2: {pieces_on_board[2]}."
            )

        self.status_label.config(text=status)

        self.draw_board()

        if phase == "finished" and winner and not self.endgame_shown:
            self.endgame_shown = True
            if winner == self.player_id:
                messagebox.showinfo("Fim de jogo", "Você venceu!")
            else:
                messagebox.showinfo("Fim de jogo", "Você perdeu.")

    def grid_to_pixel(self, row, col):
        x = BOARD_MARGIN + col * NODE_GAP
        y = BOARD_MARGIN + row * NODE_GAP
        return x, y

    def pixel_to_grid(self, x, y):
        best = None
        best_dist = float("inf")

        for r in range(ROWS):
            for c in range(COLS):
                px, py = self.grid_to_pixel(r, c)
                dist = (px - x) ** 2 + (py - y) ** 2
                if dist < best_dist:
                    best_dist = dist
                    best = (r, c)

        if best_dist <= 30 ** 2:
            return best
        return None

    def draw_board(self):
        self.canvas.delete("all")

        line_color = "#202020"
        node_color = "#202020"

        for r in range(ROWS):
            x1, y = self.grid_to_pixel(r, 0)
            x2, _ = self.grid_to_pixel(r, COLS - 1)
            self.canvas.create_line(x1, y, x2, y, fill=line_color, width=3)

        for c in range(COLS):
            x, y1 = self.grid_to_pixel(0, c)
            _, y2 = self.grid_to_pixel(ROWS - 1, c)
            self.canvas.create_line(x, y1, x, y2, fill=line_color, width=3)

        for r in range(ROWS):
            for c in range(COLS):
                x, y = self.grid_to_pixel(r, c)
                self.canvas.create_oval(
                    x - NODE_RADIUS,
                    y - NODE_RADIUS,
                    x + NODE_RADIUS,
                    y + NODE_RADIUS,
                    fill=node_color,
                    outline=node_color,
                )

        if not self.game_state:
            return

        board = self.game_state["board"]

        for r in range(ROWS):
            for c in range(COLS):
                piece = board[r][c]
                if piece == EMPTY:
                    continue

                x, y = self.grid_to_pixel(r, c)

                if self.selected_piece == (r, c):
                    self.canvas.create_oval(
                        x - PIECE_RADIUS - 8,
                        y - PIECE_RADIUS - 8,
                        x + PIECE_RADIUS + 8,
                        y + PIECE_RADIUS + 8,
                        outline="#2563eb",
                        width=3,
                    )

                if piece == PLAYER_1:
                    self.canvas.create_oval(
                        x - PIECE_RADIUS,
                        y - PIECE_RADIUS,
                        x + PIECE_RADIUS,
                        y + PIECE_RADIUS,
                        fill="#111111",
                        outline="#111111",
                        width=2,
                    )
                elif piece == PLAYER_2:
                    self.canvas.create_oval(
                        x - PIECE_RADIUS,
                        y - PIECE_RADIUS,
                        x + PIECE_RADIUS,
                        y + PIECE_RADIUS,
                        fill="white",
                        outline="#1f2937",
                        width=2,
                    )

    def on_board_click(self, event):
        clicked = self.pixel_to_grid(event.x, event.y)
        if clicked is None:
            return

        row, col = clicked

        if not self.game_state or self.player_id is None:
            return

        phase = self.game_state["phase"]
        board = self.game_state["board"]
        current_turn = self.game_state["current_turn"]
        capture_pending_for = self.game_state.get("capture_pending_for")

        if phase == "finished":
            return

        if phase == "placement":
            if current_turn != self.player_id:
                self.append_chat("Não é seu turno.")
                return

            send_json(self.sock, {
                "type": "place_piece",
                "row": row,
                "col": col
            })
            return

        if phase == "movement":
            if current_turn != self.player_id:
                self.append_chat("Não é seu turno.")
                return

            if self.selected_piece is None:
                if board[row][col] == self.player_id:
                    self.selected_piece = (row, col)
                    self.draw_board()
                else:
                    self.append_chat("Selecione uma peça sua.")
            else:
                from_row, from_col = self.selected_piece
                self.selected_piece = None

                send_json(self.sock, {
                    "type": "move_piece",
                    "from_row": from_row,
                    "from_col": from_col,
                    "to_row": row,
                    "to_col": col
                })
                self.draw_board()
            return

        if phase == "capture":
            if capture_pending_for != self.player_id:
                self.append_chat("Aguarde o adversário concluir a captura.")
                return

            send_json(self.sock, {
                "type": "capture_piece",
                "row": row,
                "col": col
            })

    def send_chat(self):
        text = self.entry_message.get().strip()
        if not text:
            return

        send_json(self.sock, {
            "type": "chat",
            "text": text
        })
        self.entry_message.delete(0, "end")

    def resign(self):
        if messagebox.askyesno("Desistir", "Deseja realmente desistir da partida?"):
            try:
                send_json(self.sock, {"type": "resign"})
            except Exception:
                pass

    def append_chat(self, text: str):
        if not text:
            return

        self.chat_text.config(state="normal")
        self.chat_text.insert("end", text + "\n")
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")

    def on_close(self):
        self.running = False

        try:
            send_json(self.sock, {"type": "resign"})
        except Exception:
            pass

        try:
            self.sock.close()
        except Exception:
            pass

        self.root.destroy()


def main():
        root = tk.Tk()
        DaraClient(root)
        root.mainloop()


if __name__ == "__main__":
    main()