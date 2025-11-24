# tomasulo_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from tomasulo_engine import SimuladorTomasulo

class TomasuloGUI:
    def __init__(self, root):
        self.sim = SimuladorTomasulo()
        self.root = root
        self.root.title("Simulador Tomasulo - Visual Pro")
        self.root.geometry("1200x750")
        
        self.setup_ui()
        self.update_view()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", font=('Arial', 9), rowheight=22)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background="#ddd")

        # --- Frames ---
        top_frame = tk.Frame(self.root, pady=10, padx=10)
        top_frame.pack(fill=tk.X)
        
        center_frame = tk.Frame(self.root, padx=10)
        center_frame.pack(expand=True, fill=tk.BOTH)
        
        bottom_frame = tk.Frame(self.root, height=150, padx=10, pady=10)
        bottom_frame.pack(fill=tk.X)

        # --- Botões ---
        tk.Button(top_frame, text="⚙ Configurar", command=self.open_config_window, bg="#ddddff").pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Resetar", command=self.reset_sim, bg="#ffcccc").pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="<< Voltar Ciclo", command=self.prev_step, bg="#ffebcd").pack(side=tk.LEFT, padx=20)
        
        self.btn_step = tk.Button(top_frame, text="Próximo Ciclo >>", command=self.next_step, bg="#ccffcc", font=('Arial', 11, 'bold'))
        self.btn_step.pack(side=tk.LEFT, padx=5)
        
        # Botão extra para ver métricas a qualquer momento
        tk.Button(top_frame, text="Relatório", command=self.mostrar_relatorio, bg="#eeeeee").pack(side=tk.LEFT, padx=5)

        self.lbl_ciclo = tk.Label(top_frame, text="Ciclo: 0", font=("Arial", 16, "bold"), fg="blue")
        self.lbl_ciclo.pack(side=tk.RIGHT, padx=20)

        # --- TABELAS ---
        # 1. RS
        frame_rs = tk.LabelFrame(center_frame, text="Estações de Reserva (Reservation Stations)", font=('Arial', 10, 'bold'))
        frame_rs.pack(fill=tk.X, pady=5)
        cols_rs = ("Nome", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "Dest (ROB)", "Tempo")
        self.tree_rs = ttk.Treeview(frame_rs, columns=cols_rs, show='headings', height=6)
        for col in cols_rs:
            self.tree_rs.heading(col, text=col)
            self.tree_rs.column(col, width=80, anchor=tk.CENTER)
        self.tree_rs.pack(fill=tk.X)

        # 2. ROB
        frame_rob = tk.LabelFrame(center_frame, text="Reorder Buffer (ROB)", font=('Arial', 10, 'bold'))
        frame_rob.pack(fill=tk.X, pady=5)
        cols_rob = ("ID", "Tipo", "Destino", "Valor", "Pronto?", "Instrução Original")
        self.tree_rob = ttk.Treeview(frame_rob, columns=cols_rob, show='headings', height=6)
        for col in cols_rob:
            self.tree_rob.heading(col, text=col)
            self.tree_rob.column(col, width=100, anchor=tk.CENTER)
        self.tree_rob.pack(fill=tk.X)

        # 3. Dados
        frame_data = tk.Frame(center_frame)
        frame_data.pack(fill=tk.BOTH, expand=True, pady=5)
        
        frame_rat = tk.LabelFrame(frame_data, text="RAT")
        frame_rat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.tree_rat = ttk.Treeview(frame_rat, columns=("Reg", "ROB Ref"), show='headings')
        self.tree_rat.heading("Reg", text="Reg")
        self.tree_rat.heading("ROB Ref", text="ROB")
        self.tree_rat.pack(fill=tk.BOTH, expand=True)

        frame_reg = tk.LabelFrame(frame_data, text="Registradores")
        frame_reg.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.tree_reg = ttk.Treeview(frame_reg, columns=("Reg", "Valor"), show='headings')
        self.tree_reg.heading("Reg", text="Reg")
        self.tree_reg.heading("Valor", text="Valor")
        self.tree_reg.pack(fill=tk.BOTH, expand=True)

        # --- LOG ---
        frame_log = tk.LabelFrame(bottom_frame, text="Log de Execução")
        frame_log.pack(fill=tk.BOTH, expand=True)
        self.txt_log = tk.Text(frame_log, height=5, bg="#f4f4f4", font=("Consolas", 10))
        self.txt_log.pack(fill=tk.BOTH, expand=True)

    # =========================================================================
    # JANELA DE CONFIGURAÇÃO
    # =========================================================================
    def open_config_window(self):
        top = tk.Toplevel(self.root)
        top.title("Configurações do Simulador")
        top.geometry("600x600")

        # 1. Latências
        lbl_frame_lat = tk.LabelFrame(top, text="Latências (Ciclos)", padx=10, pady=10)
        lbl_frame_lat.pack(fill=tk.X, padx=10, pady=5)
        
        self.entries_lat = {}
        row = 0
        col = 0
        for op, val in self.sim.latencias.items():
            tk.Label(lbl_frame_lat, text=op).grid(row=row, column=col, sticky="e")
            entry = tk.Entry(lbl_frame_lat, width=5)
            entry.insert(0, str(val))
            entry.grid(row=row, column=col+1, padx=5, pady=5)
            self.entries_lat[op] = entry
            col += 2
            if col > 4: 
                col = 0
                row += 1

        # 2. Valores Iniciais dos Registradores
        lbl_frame_regs = tk.LabelFrame(top, text="Registradores Iniciais (Ex: R1=10, R2=50)", padx=10, pady=10)
        lbl_frame_regs.pack(fill=tk.X, padx=10, pady=5)
        
        self.txt_regs = tk.Text(lbl_frame_regs, height=3)
        self.txt_regs.pack(fill=tk.X)
        regs_str = ", ".join([f"{k}={v}" for k,v in self.sim.regs_iniciais.items()])
        self.txt_regs.insert(tk.END, regs_str)

        # 3. Código do Programa
        lbl_frame_prog = tk.LabelFrame(top, text="Código do Programa (Instruções)", padx=10, pady=10)
        lbl_frame_prog.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.txt_prog = tk.Text(lbl_frame_prog, height=10)
        self.txt_prog.pack(fill=tk.BOTH, expand=True)
        
        prog_text = ""
        for inst in self.sim.fila_instrucoes:
            prog_text += f"{inst.op} {inst.dest}, {inst.s1}, {inst.s2}\n"
        if not prog_text:
            prog_text = "ADD R1, R2, R3\nMUL R4, R1, R2\nSUB R5, R3, R1\nDIV R6, R4, R2"
        self.txt_prog.insert(tk.END, prog_text)

        btn_save = tk.Button(top, text="Salvar Configurações e Reiniciar", bg="#88ff88", 
                             command=lambda: self.save_config(top))
        btn_save.pack(pady=10)

    def save_config(self, window):
        novas_latencias = {}
        for op, entry in self.entries_lat.items():
            try: novas_latencias[op] = int(entry.get())
            except ValueError: pass

        novos_regs = {}
        raw_regs = self.txt_regs.get("1.0", tk.END).replace("\n", "").split(",")
        for item in raw_regs:
            parts = item.split("=")
            if len(parts) == 2:
                reg = parts[0].strip().upper()
                try: novos_regs[reg] = int(parts[1].strip())
                except ValueError: pass

        prog_txt = self.txt_prog.get("1.0", tk.END).strip().split("\n")

        self.sim.set_config(novas_latencias, novos_regs)
        self.sim.reset()
        self.sim.carregar_instrucoes(prog_txt)
        
        self.log_msg("Novas configurações aplicadas!")
        self.update_view()
        window.destroy()

    # =========================================================================
    # CONTROLES E MÉTRICAS
    # =========================================================================
    def next_step(self):
        # Verifica se já acabou antes de rodar
        if self.sim.esta_terminado():
            self.mostrar_relatorio()
            return

        msg = self.sim.executar_ciclo()
        if msg:
            self.log_msg(msg)
        self.update_view()
        
        # Verifica se acabou LOGO APÓS rodar o ciclo
        if self.sim.esta_terminado():
            self.mostrar_relatorio()

    def mostrar_relatorio(self):
        m = self.sim.metricas
        ciclos = self.sim.ciclo
        ipc = m['commits'] / cycles if (cycles := ciclos) > 0 else 0
        
        relatorio = (
            f"--- SIMULAÇÃO FINALIZADA ---\n\n"
            f"Ciclos Totais: {ciclos}\n"
            f"Instruções Commitadas: {m['commits']}\n"
            f"IPC (Instr/Ciclo): {ipc:.2f}\n"
            f"Ciclos de Bolha (Stalls): {m['bolhas']}\n"
            f"Flushes (Desvios): {m['flushes']}\n"
        )
        messagebox.showinfo("Métricas de Desempenho", relatorio)

    def prev_step(self):
        msg = self.sim.voltar_ciclo()
        if msg:
            self.txt_log.delete(1.0, tk.END)
            self.log_msg("<< " + msg)
        self.update_view()

    def load_example(self):
        self.reset_sim()
        prog = ["ADD R1, R2, R3", "MUL R4, R1, R2", "SUB R5, R3, R1", "DIV R6, R4, R2"]
        self.sim.carregar_instrucoes(prog)
        self.log_msg("Exemplo Padrão carregado.")
        self.update_view()

    def reset_sim(self):
        self.sim.reset()
        self.txt_log.delete(1.0, tk.END)
        self.update_view()

    def log_msg(self, msg):
        self.txt_log.insert(tk.END, msg)
        self.txt_log.see(tk.END)

    def update_view(self):
        self.lbl_ciclo.config(text=f"Ciclo: {self.sim.ciclo}")

        # RS
        for item in self.tree_rs.get_children(): self.tree_rs.delete(item)
        todas_rs = self.sim.rs_add + self.sim.rs_mul
        for rs in todas_rs:
            qj = rs.qj if rs.qj is not None else ""
            qk = rs.qk if rs.qk is not None else ""
            dest = rs.dest if rs.busy else ""
            self.tree_rs.insert("", "end", values=(
                rs.nome, "SIM" if rs.busy else "", rs.op if rs.op else "",
                rs.vj if rs.vj is not None else "", rs.vk if rs.vk is not None else "",
                qj, qk, dest, rs.tempo_restante
            ))

        # ROB
        for item in self.tree_rob.get_children(): self.tree_rob.delete(item)
        for rob in self.sim.rob:
            if rob.busy:
                pronto = "SIM" if rob.pronto else "NÃO"
                self.tree_rob.insert("", "end", values=(
                    rob.id, rob.tipo, rob.dest, rob.valor, pronto, str(rob.instrucao)
                ))

        # RAT e REGS
        for item in self.tree_rat.get_children(): self.tree_rat.delete(item)
        for item in self.tree_reg.get_children(): self.tree_reg.delete(item)
        for i in range(10):
            r = f"R{i}"
            rat = self.sim.rat[r] if self.sim.rat[r] is not None else ""
            self.tree_rat.insert("", "end", values=(r, rat))
            self.tree_reg.insert("", "end", values=(r, self.sim.regs[r]))

if __name__ == "__main__":
    root = tk.Tk()
    app = TomasuloGUI(root)
    root.mainloop()