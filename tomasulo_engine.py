# tomasulo_engine.py

class Instrucao:
    def __init__(self, op, dest, s1, s2, id):
        self.id = id
        self.op = op        # Ex: ADD, MUL, SUB
        self.dest = dest    # Ex: R1
        self.s1 = s1        # Ex: R2
        self.s2 = s2        # Ex: R3 ou 100
        self.estado = "EMITIDO" 

    def __repr__(self):
        return f"{self.op} {self.dest}, {self.s1}, {self.s2}"

class EstacaoReserva:
    def __init__(self, nome, tipo):
        self.nome = nome
        self.tipo = tipo    # ADD ou MUL
        self.busy = False
        self.op = None
        self.vj = None      # Valor Operando 1
        self.vk = None      # Valor Operando 2
        self.qj = None      # ROB ID produzindo Operando 1
        self.qk = None      # ROB ID produzindo Operando 2
        self.dest = None    # ROB ID de destino (quem eu vou atualizar)
        self.tempo_restante = 0

class EntradaROB:
    def __init__(self, id):
        self.id = id
        self.tipo = None
        self.dest = None
        self.valor = None
        self.pronto = False
        self.instrucao = None
        self.busy = False

class SimuladorTomasulo:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ciclo = 0
        self.log_msg = ""
        
        # Arquitetura
        self.rat = {f'R{i}': None for i in range(32)} 
        self.regs = {f'R{i}': 0 for i in range(32)}
        
        # Valores Iniciais (Hardcoded para teste)
        self.regs['R1'] = 10
        self.regs['R2'] = 20
        self.regs['R3'] = 30
        
        # Filas
        self.fila_instrucoes = []
        self.tamanho_rob = 6
        self.rob = [EntradaROB(i) for i in range(self.tamanho_rob)]
        self.head = 0
        self.tail = 0
        self.itens_no_rob = 0
        
        # Estações de Reserva
        self.rs_add = [EstacaoReserva(f'ADD_{i}', 'ADD') for i in range(3)]
        self.rs_mul = [EstacaoReserva(f'MUL_{i}', 'MUL') for i in range(2)]
        
        # Configuração de Latência
        self.latencias = {'ADD': 2, 'SUB': 2, 'MUL': 10, 'DIV': 40, 'BEQ': 1}

    def log(self, msg):
        """Armazena mensagens para a GUI exibir"""
        self.log_msg += msg + "\n"

    def carregar_instrucoes(self, lista_instrucoes):
        self.fila_instrucoes = []
        for i, txt in enumerate(lista_instrucoes):
            partes = txt.replace(',', '').split()
            if len(partes) >= 4:
                self.fila_instrucoes.append(Instrucao(partes[0], partes[1], partes[2], partes[3], i))

    def get_rs_livre(self, op):
        lista = self.rs_mul if op in ['MUL', 'DIV'] else self.rs_add
        for rs in lista:
            if not rs.busy:
                return rs
        return None

    def executar_ciclo(self):
        self.ciclo += 1
        self.log_msg = "" # Limpa log do ciclo anterior
        
        # --- 1. COMMIT ---
        if self.itens_no_rob > 0:
            rob_entry = self.rob[self.head]
            if rob_entry.busy and rob_entry.pronto:
                instr = rob_entry.instrucao
                self.log(f"[COMMIT] Instr {instr.id} ({instr.op}) no ROB {rob_entry.id} -> Regs")
                
                if instr.op != 'BEQ':
                    if self.rat[rob_entry.dest] == rob_entry.id:
                        self.rat[rob_entry.dest] = None
                    self.regs[rob_entry.dest] = rob_entry.valor
                
                rob_entry.busy = False
                self.head = (self.head + 1) % self.tamanho_rob
                self.itens_no_rob -= 1
                instr.estado = "COMMITADO"

        # --- 2. WRITE RESULT ---
        todas_rs = self.rs_add + self.rs_mul
        for rs in todas_rs:
            if rs.busy and rs.tempo_restante == 0 and rs.op is not None:
                resultado = 0
                # ALU Simples
                vj = int(rs.vj) if rs.vj is not None else 0
                vk = int(rs.vk) if rs.vk is not None else 0
                
                if rs.op == 'ADD': resultado = vj + vk
                elif rs.op == 'SUB': resultado = vj - vk
                elif rs.op == 'MUL': resultado = vj * vk
                elif rs.op == 'DIV': resultado = int(vj / vk) if vk != 0 else 0
                
                self.log(f"[WRITE] {rs.nome} terminou. Val={resultado} -> ROB {rs.dest}")
                
                # Atualiza ROB
                self.rob[rs.dest].valor = resultado
                self.rob[rs.dest].pronto = True
                
                # CDB Broadcast (Avisa quem está esperando nas estações)
                for outra_rs in todas_rs:
                    if outra_rs.busy:
                        if outra_rs.qj == rs.dest:
                            outra_rs.vj = resultado
                            outra_rs.qj = None
                        if outra_rs.qk == rs.dest:
                            outra_rs.vk = resultado
                            outra_rs.qk = None
                
                rs.busy = False
                rs.op = None

        # --- 3. EXECUTE ---
        for rs in todas_rs:
            if rs.busy:
                # Só executa se tem os operandos (Qj e Qk nulos)
                if rs.qj is None and rs.qk is None:
                    if rs.tempo_restante > 0:
                        rs.tempo_restante -= 1

        # --- 4. ISSUE ---
        if self.fila_instrucoes and self.itens_no_rob < self.tamanho_rob:
            instr = self.fila_instrucoes[0]
            rs_livre = self.get_rs_livre(instr.op)
            
            if rs_livre:
                self.fila_instrucoes.pop(0)
                
                rob_id = self.tail
                self.rob[rob_id].busy = True
                self.rob[rob_id].instrucao = instr
                self.rob[rob_id].dest = instr.dest
                self.rob[rob_id].pronto = False
                self.rob[rob_id].tipo = instr.op
                
                self.tail = (self.tail + 1) % self.tamanho_rob
                self.itens_no_rob += 1

                rs_livre.busy = True
                rs_livre.op = instr.op
                rs_livre.dest = rob_id
                rs_livre.tempo_restante = self.latencias.get(instr.op, 1)

                # Resolve Operando 1
                if instr.s1 in self.rat and self.rat[instr.s1] is not None:
                    rob_produtor = self.rat[instr.s1]
                    if self.rob[rob_produtor].pronto:
                        rs_livre.vj = self.rob[rob_produtor].valor
                    else:
                        rs_livre.qj = rob_produtor
                else:
                    rs_livre.vj = self.regs.get(instr.s1, 0)

                # Resolve Operando 2
                if instr.s2 in self.rat and self.rat[instr.s2] is not None:
                    rob_produtor = self.rat[instr.s2]
                    if self.rob[rob_produtor].pronto:
                        rs_livre.vk = self.rob[rob_produtor].valor
                    else:
                        rs_livre.qk = rob_produtor
                else:
                    if instr.s2 in self.regs:
                        rs_livre.vk = self.regs[instr.s2]
                    else:
                        # Tenta converter imediato
                        try: rs_livre.vk = int(instr.s2)
                        except: rs_livre.vk = 0

                # Atualiza RAT
                if instr.op != 'BEQ':
                    self.rat[instr.dest] = rob_id
                
                self.log(f"[ISSUE] {instr.op} despachada p/ ROB {rob_id}")
                
        return self.log_msg