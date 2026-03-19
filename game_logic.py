from dataclasses import dataclass, field
from typing import List, Optional, Tuple

ROWS = 5
COLS = 6
EMPTY = 0
PLAYER_1 = 1
PLAYER_2 = 2

@dataclass
class DaraGame:
    board: List[List[int]] = field(default_factory=lambda: [[EMPTY for _ in range(COLS)] for _ in range(ROWS)])
    current_turn: int = PLAYER_1
    phase: str = "placement"  
    pieces_to_place: dict = field(default_factory=lambda: {PLAYER_1: 12, PLAYER_2: 12})
    pieces_on_board: dict = field(default_factory=lambda: {PLAYER_1: 0, PLAYER_2: 0})
    winner: Optional[int] = None
    capture_pending_for: Optional[int] = None
    last_alignment: List[Tuple[int, int]] = field(default_factory=list)

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < ROWS and 0 <= col < COLS

    def get_opponent(self, player: int) -> int:
        return PLAYER_1 if player == PLAYER_2 else PLAYER_2

    def is_adjacent(self, r1: int, c1: int, r2: int, c2: int) -> bool:
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def count_player_pieces(self, player: int) -> int:
        return sum(cell == player for row in self.board for cell in row)

    def forms_line_of_three(self, player: int, row: int, col: int) -> List[Tuple[int, int]]:
        aligned = []

        # horizontal
        count = 1
        horiz = [(row, col)]

        c = col - 1
        while c >= 0 and self.board[row][c] == player:
            horiz.append((row, c))
            count += 1
            c -= 1

        c = col + 1
        while c < COLS and self.board[row][c] == player:
            horiz.append((row, c))
            count += 1
            c += 1

        if count >= 3:
            aligned = horiz[:]

        # vertical
        count = 1
        vert = [(row, col)]

        r = row - 1
        while r >= 0 and self.board[r][col] == player:
            vert.append((r, col))
            count += 1
            r -= 1

        r = row + 1
        while r < ROWS and self.board[r][col] == player:
            vert.append((r, col))
            count += 1
            r += 1

        if count >= 3:
            if len(vert) > len(aligned):
                aligned = vert[:]

        return aligned

    def can_place(self, player: int, row: int, col: int) -> Tuple[bool, str]:
        if self.phase != "placement":
            return False, "O jogo não está na fase de colocação."

        if player != self.current_turn:
            return False, "Não é seu turno."

        if not self.in_bounds(row, col):
            return False, "Posição fora do tabuleiro."

        if self.board[row][col] != EMPTY:
            return False, "Esta casa já está ocupada."

        # Na fase de colocação não pode formar linha de 3
        self.board[row][col] = player
        aligned = self.forms_line_of_three(player, row, col)
        self.board[row][col] = EMPTY

        if aligned:
            return False, "Na fase de colocação não é permitido formar linha de 3."

        return True, "Jogada válida."

    def place_piece(self, player: int, row: int, col: int) -> Tuple[bool, str]:
        ok, msg = self.can_place(player, row, col)
        if not ok:
            return False, msg

        self.board[row][col] = player
        self.pieces_to_place[player] -= 1
        self.pieces_on_board[player] += 1

        if self.pieces_to_place[PLAYER_1] == 0 and self.pieces_to_place[PLAYER_2] == 0:
            self.phase = "movement"

        self.current_turn = self.get_opponent(player)
        return True, "Peça posicionada com sucesso."

    def can_move(self, player: int, from_row: int, from_col: int, to_row: int, to_col: int) -> Tuple[bool, str]:
        if self.phase != "movement":
            return False, "O jogo não está na fase de movimentação."

        if player != self.current_turn:
            return False, "Não é seu turno."

        if not self.in_bounds(from_row, from_col) or not self.in_bounds(to_row, to_col):
            return False, "Movimento fora do tabuleiro."

        if self.board[from_row][from_col] != player:
            return False, "A peça de origem não pertence a você."

        if self.board[to_row][to_col] != EMPTY:
            return False, "A casa de destino não está vazia."

        if not self.is_adjacent(from_row, from_col, to_row, to_col):
            return False, "Você só pode mover para uma casa adjacente horizontal ou vertical."

        return True, "Movimento válido."

    def move_piece(self, player: int, from_row: int, from_col: int, to_row: int, to_col: int) -> Tuple[bool, str]:
        ok, msg = self.can_move(player, from_row, from_col, to_row, to_col)
        if not ok:
            return False, msg

        self.board[from_row][from_col] = EMPTY
        self.board[to_row][to_col] = player

        aligned = self.forms_line_of_three(player, to_row, to_col)

        if aligned:
            self.phase = "capture"
            self.capture_pending_for = player
            self.last_alignment = aligned
            return True, "Você formou uma linha de 3. Escolha uma peça adversária para capturar."

        self.current_turn = self.get_opponent(player)
        return True, "Movimento realizado com sucesso."

    def can_capture(self, player: int, row: int, col: int) -> Tuple[bool, str]:
        if self.phase != "capture":
            return False, "Não há captura pendente."

        if self.capture_pending_for != player:
            return False, "Não é você quem deve capturar agora."

        if not self.in_bounds(row, col):
            return False, "Posição fora do tabuleiro."

        opponent = self.get_opponent(player)
        if self.board[row][col] != opponent:
            return False, "Você deve capturar uma peça do oponente."

        return True, "Captura válida."

    def capture_piece(self, player: int, row: int, col: int) -> Tuple[bool, str]:
        ok, msg = self.can_capture(player, row, col)
        if not ok:
            return False, msg

        opponent = self.get_opponent(player)
        self.board[row][col] = EMPTY
        self.pieces_on_board[opponent] -= 1

        if self.pieces_on_board[opponent] <= 2:
            self.phase = "finished"
            self.winner = player
            return True, "Captura realizada. Fim de jogo."

        self.phase = "movement"
        self.capture_pending_for = None
        self.last_alignment = []
        self.current_turn = opponent
        return True, "Captura realizada com sucesso."

    def resign(self, player: int):
        self.phase = "finished"
        self.winner = self.get_opponent(player)

    def serialize(self) -> dict:
        return {
            "board": self.board,
            "current_turn": self.current_turn,
            "phase": self.phase,
            "pieces_to_place": self.pieces_to_place,
            "pieces_on_board": self.pieces_on_board,
            "winner": self.winner,
            "capture_pending_for": self.capture_pending_for,
            "last_alignment": self.last_alignment,
        }