# tomasulo_engine.py
import copy

class Instrucao:
    def __init__(self, op, dest, s1, s2, id):
        self.id = id
        self.op = op        
        self.dest = dest    
        self.s1 = s1        
        self.s2 = s2        
        self.estado = "EMITIDO" 

    def __repr__(self):
        return f"{self.op} {self.dest}, {self.s1}, {self.s2}"

class EstacaoReserva:
    def __init__(self, nome, tipo):
        self.nome = nome
        self.tipo = tipo
        self.busy = False
        self.op = None
        self.vj = None
        self.vk = None
        self.qj = None
        self.qk = None
        self.dest = None
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
        self.latencias = {'ADD': 2, 'SUB': 2, 'MUL': 8, 'DIV': 10, 'BEQ': 1}
        self.regs_iniciais = {'R1': 10, 'R2': 20, 'R3': 30} 
        self.history = [] 
        self.prog_original = [] # Armazena o programa original para saltos
        self.reset()

    def set_config(self, latencias_novas, regs_novos):
        self.latencias.update(latencias_novas)
        self.regs_iniciais = regs_novos

    def reset(self):
        self.ciclo = 0
        self.log_msg = ""
        self.history = [] 
        
        # Métricas
        self.metricas = {
            'commits': 0,
            'bolhas': 0,
            'flushes': 0
        }

        self.rat = {f'R{i}': None for i in range(32)} 
        self.regs = {f'R{i}': 0 for i in range(32)}
        
        for reg, val in self.regs_iniciais.items():
            if reg in self.regs:
                self.regs[reg] = val
        
        self.fila_instrucoes = []
        self.tamanho_rob = 6
        self.rob = [EntradaROB(i) for i in range(self.tamanho_rob)]
        self.head = 0
        self.tail = 0
        self.itens_no_rob = 0
        
        self.rs_add = [EstacaoReserva(f'ADD_{i}', 'ADD') for i in range(3)]
        self.rs_mul = [EstacaoReserva(f'MUL_{i}', 'MUL') for i in range(2)]
        
        # Recria o prog_original no reset
        if hasattr(self, 'prog_original') and self.prog_original:
             pass

    def log(self, msg):
        self.log_msg += msg + "\n"

    def carregar_instrucoes(self, lista_instrucoes):
        self.fila_instrucoes = []
        self.prog_original = [] # Limpa e carrega o programa original
        for i, txt in enumerate(lista_instrucoes):
            if not txt.strip(): continue
            partes = txt.replace(',', '').split()
            if len(partes) >= 4:
                instr = Instrucao(partes[0], partes[1], partes[2], partes[3], i)
                self.fila_instrucoes.append(instr)
                self.prog_original.append(instr) # Salva no programa original

    def get_rs_livre(self, op):
        lista = self.rs_mul if op in ['MUL', 'DIV'] else self.rs_add
        for rs in lista:
            if not rs.busy:
                return rs
        return None

    def salvar_estado(self):
        estado_atual = copy.deepcopy(self.__dict__)
        del estado_atual['history']
        self.history.append(estado_atual)

    def voltar_ciclo(self):
        if not self.history:
            return "Já está no início."
        
        estado_anterior = self.history.pop()
        prog_original_temp = self.prog_original
        self.__dict__.update(estado_anterior)
        self.prog_original = prog_original_temp

        if not hasattr(self, 'history'):
            self.history = []
        return f"Voltou para Ciclo {self.ciclo}"

    def esta_terminado(self):
        return len(self.fila_instrucoes) == 0 and self.itens_no_rob == 0
    
    def limpar_estado_apos_rob(self, rob_id_commitado):
        """Limpa RS e RAT e resetta o ROB para o estado pós-BEQ."""
        
        self.log(f"--- [FLUSH DETECTADO] ---")

        # 1. Limpa entradas do RAT que apontam para o ROB/RS
        for reg in self.rat:
            rob_ref = self.rat[reg]
            if rob_ref is not None:
                # Se o ROB for posterior ou igual ao BEQ, o RAT precisa ser limpo
                # para que o próximo uso do registrador leia do Banco de Registradores
                if rob_ref != rob_id_commitado: # O BEQ no Head será limpo no commit
                     self.rat[reg] = None
        
        # 2. Limpa todas as Estações de Reserva (RS)
        todas_rs = self.rs_add + self.rs_mul
        for rs in todas_rs:
            rs.__init__(rs.nome, rs.tipo)
        
        # 3. Limpa entradas do ROB (exceto o que está no Head - que é o BEQ e será desocupado)
        self.rob = [EntradaROB(i) for i in range(self.tamanho_rob)]
        self.head = (rob_id_commitado + 1) % self.tamanho_rob
        self.tail = self.head
        self.itens_no_rob = 0
        self.log(f"Estado Especulativo (RS, RAT, ROB) Limpo.")

    def atualizar_fila_instrucoes(self, target_index):
        """Atualiza a fila de instruções para continuar a partir do alvo do desvio."""
        
        try:
            target_index = int(target_index)
            if 0 <= target_index < len(self.prog_original):
                self.fila_instrucoes = [copy.deepcopy(instr) for instr in self.prog_original[target_index:]]
                self.log(f"Fila de Instruções atualizada. Próxima instrução a ser emitida é: {self.fila_instrucoes[0]}")
            else:
                self.fila_instrucoes = []
                self.log("Fila de Instruções zerada. Alvo de salto fora do programa.")
        except ValueError:
            self.log(f"Erro: Alvo de salto inválido ({target_index}). Fila de Instruções não atualizada.")

    def executar_ciclo(self):
        if self.esta_terminado():
            return "Simulação Finalizada."

        self.salvar_estado()
        self.ciclo += 1
        self.log_msg = "" 
        
        # --- 1. COMMIT ---
        if self.itens_no_rob > 0:
            rob_entry = self.rob[self.head]
            if rob_entry.busy and rob_entry.pronto:
                instr = rob_entry.instrucao
                
                # --- LÓGICA DE ESPECULAÇÃO/FLUSH ---
                if instr.op == 'BEQ':                    
                    val_op1 = self.regs.get(instr.dest, 0)
                    val_op2 = self.regs.get(instr.s1, 0)
                    target_index = instr.s2 # Alvo de salto é o s2 da instrução BEQ
                    
                    condicao_verdadeira = (val_op1 == val_op2)
                    
                    if condicao_verdadeira:
                        # Erro de Predição (Predict Not Taken) -> FLUSH
                        self.log(f"[FLUSH] Erro de Especulação na {instr}. {instr.dest}({val_op1}) == {instr.s1}({val_op2}).")
                        self.metricas['flushes'] += 1
                        
                        # A. Limpar estado especulativo
                        self.limpar_estado_apos_rob(rob_entry.id)
                        
                        # B. Mudar o fluxo de controle (PC)
                        self.atualizar_fila_instrucoes(target_index)
                        
                    else:
                        # Sucesso de Predição (Predict Not Taken estava correto) -> Commit normal
                        self.log(f"[COMMIT] Sucesso na Especulação da {instr} (Não tomou desvio).")
                        self.metricas['commits'] += 1
                        rob_entry.busy = False
                        self.head = (self.head + 1) % self.tamanho_rob
                        self.itens_no_rob -= 1
                        instr.estado = "COMMITADO"
                        
                else:
                    # Instrução normal (ADD, MUL, etc)
                    self.log(f"[COMMIT] Instr {instr.id} ({instr.op}) no ROB {rob_entry.id} -> Regs")
                    self.metricas['commits'] += 1

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
                vj = int(rs.vj) if rs.vj is not None else 0
                vk = int(rs.vk) if rs.vk is not None else 0
                
                if rs.op == 'ADD': resultado = vj + vk
                elif rs.op == 'SUB': resultado = vj - vk
                elif rs.op == 'MUL': resultado = vj * vk
                elif rs.op == 'DIV': resultado = int(vj / vk) if vk != 0 else 0
                
                self.log(f"[WRITE] {rs.nome} terminou. Val={resultado} -> ROB {rs.dest}")
                
                # Se for BEQ, o valor não importa, apenas a sinalização de pronto.
                self.rob[rs.dest].valor = resultado
                self.rob[rs.dest].pronto = True
                
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
                if rs.qj is None and rs.qk is None:
                    if rs.tempo_restante > 0:
                        rs.tempo_restante -= 1

        # --- 4. ISSUE ---
        if self.fila_instrucoes:
            tem_espaco_rob = self.itens_no_rob < self.tamanho_rob
            instr = self.fila_instrucoes[0]
            rs_livre = self.get_rs_livre(instr.op)
            
            if not tem_espaco_rob or not rs_livre:
                self.metricas['bolhas'] += 1
            
            if tem_espaco_rob and rs_livre:
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

                if instr.s1 in self.rat and self.rat[instr.s1] is not None:
                    rob_produtor = self.rat[instr.s1]
                    if self.rob[rob_produtor].pronto:
                        rs_livre.vj = self.rob[rob_produtor].valor
                    else:
                        rs_livre.qj = rob_produtor
                else:
                    rs_livre.vj = self.regs.get(instr.s1, 0)

                # O segundo operando (s2) pode ser um registrador, um literal (para ADD/MUL, etc) 
                # ou o ALVO de salto (para BEQ).
                if instr.s2 in self.rat and self.rat[instr.s2] is not None:
                    rob_produtor = self.rat[instr.s2]
                    if self.rob[rob_produtor].pronto:
                        rs_livre.vk = self.rob[rob_produtor].valor
                    else:
                        rs_livre.qk = rob_produtor
                elif instr.s2 in self.regs:
                    rs_livre.vk = self.regs[instr.s2]
                else:
                    # Trata o s2 como um literal (valor) ou alvo de salto (para BEQ)
                    try: rs_livre.vk = int(instr.s2)
                    except: rs_livre.vk = 0

                if instr.op != 'BEQ':
                    self.rat[instr.dest] = rob_id
                
                self.log(f"[ISSUE] {instr.op} despachada p/ ROB {rob_id}")
                
        return self.log_msg