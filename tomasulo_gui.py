# tomasulo_gui.py
import tkinter as tk
from tkinter import ttk
# Importa a classe do nosso outro arquivo
from tomasulo_engine import SimuladorTomasulo

class TomasuloGUI:
    def __init__(self, root):
        self.sim = SimuladorTomasulo()
        self.root = root
        self.root.title("Simulador Tomasulo - Visual")
        self.root.geometry("1200x750")
        
        self.setup_ui()
        self.update_view()

    def setup_ui(self):
        # Estilo das tabelas
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", font=('Arial', 9), rowheight=22)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background="#ddd")

        # --- Containers Principais ---
        top_frame = tk.Frame(self.root, pady=10, padx=10)
        top_frame.pack(fill=tk.X)
        
        center_frame = tk.Frame(self.root, padx=10)
        center_frame.pack(expand=True, fill=tk.BOTH)
        
        bottom_frame = tk.Frame(self.root, height=150, padx=10, pady=10)
        bottom_frame.pack(fill=tk.X)

        # --- Botões ---
        tk.Button(top_frame, text="Carregar Exemplo", command=self.load_example).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Resetar", command=self.reset_sim, bg="#ffcccc").pack(side=tk.LEFT, padx=5)
        
        self.btn_step = tk.Button(top_frame, text="Próximo Ciclo >>", command=self.next_step, bg="#ccffcc", font=('Arial', 11, 'bold'))
        self.btn_step.pack(side=tk.LEFT, padx=20)
        
        self.lbl_ciclo = tk.Label(top_frame, text="Ciclo: 0", font=("Arial", 16, "bold"), fg="blue")
        self.lbl_ciclo.pack(side=tk.RIGHT, padx=20)

        # --- TABELAS ---
        
        # 1. Estações de Reserva
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

        # 3. Dados (RAT e Regs lado a lado)
        frame_data = tk.Frame(center_frame)
        frame_data.pack(fill=tk.BOTH, expand=True, pady=5)

        # RAT
        frame_rat = tk.LabelFrame(frame_data, text="RAT (Register Alias Table)")
        frame_rat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.tree_rat = ttk.Treeview(frame_rat, columns=("Reg", "ROB Ref"), show='headings')
        self.tree_rat.heading("Reg", text="Registrador")
        self.tree_rat.heading("ROB Ref", text="ROB ID")
        self.tree_rat.column("Reg", anchor=tk.CENTER)
        self.tree_rat.column("ROB Ref", anchor=tk.CENTER)
        self.tree_rat.pack(fill=tk.BOTH, expand=True)

        # Regs
        frame_reg = tk.LabelFrame(frame_data, text="Banco de Registradores (Valores Reais)")
        frame_reg.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.tree_reg = ttk.Treeview(frame_reg, columns=("Reg", "Valor"), show='headings')
        self.tree_reg.heading("Reg", text="Registrador")
        self.tree_reg.heading("Valor", text="Valor")
        self.tree_reg.column("Reg", anchor=tk.CENTER)
        self.tree_reg.column("Valor", anchor=tk.CENTER)
        self.tree_reg.pack(fill=tk.BOTH, expand=True)

        # --- LOG ---
        frame_log = tk.LabelFrame(bottom_frame, text="Log de Execução")
        frame_log.pack(fill=tk.BOTH, expand=True)
        self.txt_log = tk.Text(frame_log, height=5, bg="#f4f4f4", font=("Consolas", 10))
        self.txt_log.pack(fill=tk.BOTH, expand=True)

    def load_example(self):
        self.reset_sim()
        prog = [
            "ADD R1, R2, R3",
            "MUL R4, R1, R2",
            "SUB R5, R3, R1",
            "DIV R6, R4, R2"
        ]
        self.sim.carregar_instrucoes(prog)
        self.log_msg("Programa Exemplo carregado.")
        self.update_view()

    def next_step(self):
        msg = self.sim.executar_ciclo()
        if msg:
            self.log_msg(msg)
        self.update_view()

    def reset_sim(self):
        self.sim.reset()
        self.txt_log.delete(1.0, tk.END)
        self.update_view()

    def log_msg(self, msg):
        self.txt_log.insert(tk.END, msg)
        self.txt_log.see(tk.END)

    def update_view(self):
        # 1. Atualiza Label Ciclo
        self.lbl_ciclo.config(text=f"Ciclo: {self.sim.ciclo}")

        # 2. Limpa e Preenche RS
        for item in self.tree_rs.get_children(): self.tree_rs.delete(item)
        todas_rs = self.sim.rs_add + self.sim.rs_mul
        for rs in todas_rs:
            qj = rs.qj if rs.qj is not None else ""
            qk = rs.qk if rs.qk is not None else ""
            dest = rs.dest if rs.busy else ""
            self.tree_rs.insert("", "end", values=(
                rs.nome,
                "SIM" if rs.busy else "",
                rs.op if rs.op else "",
                rs.vj if rs.vj is not None else "",
                rs.vk if rs.vk is not None else "",
                qj, qk, dest, rs.tempo_restante
            ))

        # 3. Limpa e Preenche ROB
        for item in self.tree_rob.get_children(): self.tree_rob.delete(item)
        for rob in self.sim.rob:
            if rob.busy:
                pronto = "SIM" if rob.pronto else "NÃO"
                self.tree_rob.insert("", "end", values=(
                    rob.id, rob.tipo, rob.dest, rob.valor, pronto, str(rob.instrucao)
                ))

        # 4. Limpa e Preenche RAT e REGS (Apenas os primeiros 10 para não poluir)
        for item in self.tree_rat.get_children(): self.tree_rat.delete(item)
        for item in self.tree_reg.get_children(): self.tree_reg.delete(item)
        
        for i in range(10):
            reg_name = f"R{i}"
            rat_val = self.sim.rat[reg_name]
            rat_str = rat_val if rat_val is not None else ""
            reg_val = self.sim.regs[reg_name]
            
            self.tree_rat.insert("", "end", values=(reg_name, rat_str))
            self.tree_reg.insert("", "end", values=(reg_name, reg_val))

if __name__ == "__main__":
    root = tk.Tk()
    app = TomasuloGUI(root)
    root.mainloop()