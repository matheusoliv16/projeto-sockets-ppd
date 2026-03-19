# Projeto Sockets - Jogo Dara em Python

Projeto desenvolvido para a disciplina de Programação Paralela e Distribuída.

## Descrição
Este projeto implementa o jogo Dara utilizando sockets TCP em Python, permitindo a comunicação entre dois jogadores em máquinas diferentes.

## Funcionalidades
- Controle de turno
- Fase de colocação
- Fase de movimentação
- Captura de peças
- Desistência
- Chat em tempo real
- Indicação de vencedor

## Estrutura
- `server.py`: servidor da aplicação
- `client.py`: cliente com interface gráfica
- `game_logic.py`: regras do jogo
- `protocol.py`: troca de mensagens JSON

## Como executar

### 1. Iniciar o servidor
```bash
python server.py