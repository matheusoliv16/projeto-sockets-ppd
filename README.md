# Projeto Sockets - Jogo Dara em Python

Projeto desenvolvido para a disciplina de **Programação Paralela e Distribuída (PPD)**.

## 1. Descrição

Este projeto implementa o jogo **Dara** utilizando **Python**, **sockets TCP** e **interface gráfica com Tkinter**, permitindo a comunicação entre dois jogadores em máquinas diferentes.

A aplicação segue o modelo **cliente-servidor**, em que:

- o **servidor** controla o estado oficial da partida;
- os **clientes** exibem a interface gráfica, enviam jogadas e recebem atualizações do jogo.

Além da lógica principal do Dara, o sistema também oferece:

- controle de turno;
- validação das jogadas;
- chat em tempo real;
- desistência;
- indicação automática de vencedor.

---

## 2. Objetivo do projeto

O objetivo do projeto é demonstrar, na prática, conceitos da disciplina de **Programação Paralela e Distribuída**.

---

## 3. Sobre o jogo Dara

O **Dara** é um jogo de estratégia para dois jogadores, jogado em um tabuleiro com **5 linhas e 6 colunas**, totalizando **30 interseções**.

Cada jogador possui **12 peças**.

### Fases do jogo

#### Fase 1 — Colocação
Os jogadores posicionam suas peças alternadamente no tabuleiro.

**Regra importante:** durante a fase de colocação, **não é permitido formar uma linha de 3 peças**.

#### Fase 2 — Movimentação
Depois que todas as peças forem colocadas, os jogadores passam a mover suas peças para interseções adjacentes vazias.

A movimentação é permitida apenas:
- na horizontal;
- na vertical.

#### Captura
Se, na fase de movimentação, um jogador formar uma linha de 3 peças consecutivas, ele pode capturar uma peça do adversário.

#### Vitória
O jogo termina quando um jogador fica com apenas **2 peças no tabuleiro**.  
Nesse caso, o adversário é declarado vencedor.

#### Desistência
Se um jogador desistir da partida, o outro vence automaticamente.

---

## 4. Funcionalidades implementadas

- Conexão de dois jogadores ao servidor
- Controle de turno
- Fase de colocação
- Regra que impede formar linha de 3 na colocação
- Fase de movimentação
- Captura de peças
- Desistência
- Chat em tempo real
- Interface gráfica com tabuleiro 
- Indicação de vencedor
- Tratamento básico de desconexão

---

## 5. Arquitetura do sistema

O sistema utiliza uma arquitetura **cliente-servidor**.

### Servidor
O servidor é responsável por:
- aceitar conexões de até 2 jogadores;
- definir os identificadores dos jogadores;
- manter o estado oficial da partida;
- validar jogadas;
- controlar turnos;
- tratar capturas e fim de jogo;
- sincronizar o estado entre os clientes;
- retransmitir mensagens de chat.

### Cliente
O cliente é responsável por:
- conectar ao servidor;
- exibir a interface gráfica;
- desenhar o tabuleiro;
- capturar cliques do usuário;
- enviar comandos ao servidor;
- receber atualizações;
- mostrar mensagens e eventos da partida.

---

## 6. Conceitos de PPD aplicados

Este projeto aborda diversos conceitos importantes de Programação Paralela e Distribuída.

### 6.1 Arquitetura cliente-servidor
Foi adotado um modelo centralizado, no qual o servidor mantém o estado oficial da partida. Isso evita inconsistências entre os clientes.

### 6.2 Comunicação por sockets
A comunicação entre cliente e servidor foi implementada com **sockets TCP**.

### 6.3 Protocolo de transporte
Foi utilizado o protocolo **TCP**, pois ele oferece:
- conexão confiável;
- entrega ordenada;
- retransmissão em caso de falha;
- integridade básica da comunicação.

Essas características são importantes para um jogo por turnos, onde a perda de mensagens poderia corromper a partida.

### 6.4 Protocolo de aplicação
Sobre o TCP, foi criado um protocolo próprio utilizando:
- mensagens em **JSON**;
- delimitadas por **quebra de linha (`\n`)**.

Exemplo de mensagem enviada pelo cliente:

```json
{
  "type": "place_piece",
  "row": 1,
  "col": 2
}