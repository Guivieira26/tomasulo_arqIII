# tomasulo_gui.py
import tkinter as tk
from tkinter import ttk, messagebox, font
from tomasulo_engine import SimuladorTomasulo

# --- PALETA DE CORES (Modern UI) ---
COLORS = {
    'bg_app': '#F0F2F5',        
    'bg_card': '#FFFFFF',       
    'primary': '#1877F2',       
    'secondary': '#E4E6EB',     
    'success': '#42B72A',       
    'danger': '#DC3545',        
    'text': '#050505',          
    'text_light': '#65676B',    
    'header_table': '#F7F8FA',  
    'border': '#DCDFE3'         
}

class TomasuloGUI:
    def __init__(self, root):
        self.sim = SimuladorTomasulo()
        self.root = root
        self.root.title("Simulador Tomasulo - Architecture View")
        self.root.geometry("1280x850")
        self.root.configure(bg=COLORS['bg_app'])
        
        self.font_title = font.Font(family="Segoe UI", size=14, weight="bold")
        self.font_subtitle = font.Font(family="Segoe UI", size=11, weight="bold")
        self.font_ui = font.Font(family="Segoe UI", size=10)
        self.font_mono = font.Font(family="Consolas", size=10)

        self.apply_styles()
        self.setup_ui()
        self.update_view()

    def apply_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="white", foreground=COLORS['text'], fieldbackground="white", rowheight=28, font=self.font_ui, borderwidth=0)
        style.configure("Treeview.Heading", background=COLORS['header_table'], foreground=COLORS['text'], font=self.font_subtitle, relief="flat")
        style.map("Treeview", background=[('selected', COLORS['primary'])])
        style.configure("Card.TFrame", background=COLORS['bg_card'], relief="flat")

    def setup_ui(self):
        main_container = tk.Frame(self.root, bg=COLORS['bg_app'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # HEADER
        header_frame = tk.Frame(main_container, bg=COLORS['bg_app'])
        header_frame.pack(fill=tk.X, pady=(0, 15))

        info_frame = tk.Frame(header_frame, bg=COLORS['bg_app'])
        info_frame.pack(side=tk.LEFT)
        tk.Label(info_frame, text="Simulador Tomasulo", font=("Segoe UI", 18, "bold"), bg=COLORS['bg_app'], fg=COLORS['text']).pack(anchor="w")
        self.lbl_ciclo = tk.Label(info_frame, text="Ciclo: 0", font=("Segoe UI", 12), bg=COLORS['bg_app'], fg=COLORS['text_light'])
        self.lbl_ciclo.pack(anchor="w")

        btn_frame = tk.Frame(header_frame, bg=COLORS['bg_app'])
        btn_frame.pack(side=tk.RIGHT)
        self.create_button(btn_frame, "⚙ Config", self.open_config_window, COLORS['secondary'], COLORS['text'])
        self.create_button(btn_frame, "↺ Reset", self.reset_sim, COLORS['secondary'], COLORS['danger'])
        self.create_button(btn_frame, "📊 Relatório", self.mostrar_relatorio, COLORS['secondary'], COLORS['text'])
        tk.Frame(btn_frame, width=20, bg=COLORS['bg_app']).pack(side=tk.LEFT)
        self.create_button(btn_frame, "❮ Voltar", self.prev_step, "#FFC107", "#333") 
        self.create_button(btn_frame, "Avançar ❯", self.next_step, COLORS['primary'], "white", bold=True)

        # DATA AREA
        top_section = tk.Frame(main_container, bg=COLORS['bg_app'])
        top_section.pack(fill=tk.BOTH, expand=True)

        self.frame_rs = self.create_card(top_section, "Estações de Reserva (Reservation Stations)")
        self.frame_rs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        cols_rs = ("Nome", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "Dest", "Tempo")
        self.tree_rs = self.create_table(self.frame_rs, cols_rs, height=8)

        self.frame_rob = self.create_card(top_section, "Reorder Buffer (ROB)")
        self.frame_rob.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        cols_rob = ("ID", "Tipo", "Dest", "Valor", "Pronto?", "Instrução")
        self.tree_rob = self.create_table(self.frame_rob, cols_rob, height=8)

        # BOTTOM AREA
        bottom_section = tk.Frame(main_container, bg=COLORS['bg_app'])
        bottom_section.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        left_bottom = tk.Frame(bottom_section, bg=COLORS['bg_app'])
        left_bottom.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.frame_rat = self.create_card(left_bottom, "RAT (Alias Table)")
        self.frame_rat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.tree_rat = self.create_table(self.frame_rat, ("Reg", "ROB Ref"), height=6)

        self.frame_reg = self.create_card(left_bottom, "Banco de Registradores")
        self.frame_reg.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.tree_reg = self.create_table(self.frame_reg, ("Reg", "Valor"), height=6)

        self.frame_log = self.create_card(bottom_section, "Event Log")
        self.frame_log.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        log_scroll = ttk.Scrollbar(self.frame_log)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5, padx=(0, 5))
        self.txt_log = tk.Text(self.frame_log, height=6, bg="white", fg=COLORS['text'], font=self.font_mono, relief="flat", state="normal", yscrollcommand=log_scroll.set)
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        log_scroll.config(command=self.txt_log.yview)
        self.txt_log.tag_config("ISSUE", foreground="#E67E22", font=("Consolas", 10, "bold")) 
        self.txt_log.tag_config("COMMIT", foreground=COLORS['success'], font=("Consolas", 10, "bold")) 
        self.txt_log.tag_config("FLUSH", foreground=COLORS['danger'], font=("Consolas", 10, "bold")) 
        self.txt_log.tag_config("WRITE", foreground=COLORS['primary']) 

    def create_card(self, parent, title):
        card = tk.Frame(parent, bg=COLORS['bg_card'], highlightbackground=COLORS['border'], highlightthickness=1, padx=10, pady=10)
        lbl_title = tk.Label(card, text=title, font=self.font_subtitle, bg=COLORS['bg_card'], fg=COLORS['primary'])
        lbl_title.pack(anchor="w", pady=(0, 10))
        return card

    def create_button(self, parent, text, command, bg, fg, bold=False):
        f = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
        btn = tk.Button(parent, text=text, command=command, bg=bg, fg=fg, font=f, relief="flat", activebackground=bg, cursor="hand2", padx=15, pady=5, borderwidth=0)
        btn.pack(side=tk.LEFT, padx=5)
        return btn

    def create_table(self, parent, columns, height):
        frame = tk.Frame(parent, bg=COLORS['bg_card'])
        frame.pack(fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=height, yscrollcommand=scroll.set)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=tree.yview)
        return tree

    def log_msg(self, msg):
        self.txt_log.config(state="normal")
        lines = msg.split("\n")
        for line in lines:
            if not line: continue
            tag = "NORMAL"
            if "[ISSUE]" in line: tag = "ISSUE"
            elif "[COMMIT]" in line: tag = "COMMIT"
            elif "[FLUSH]" in line: tag = "FLUSH"
            elif "[WRITE]" in line: tag = "WRITE"
            self.txt_log.insert(tk.END, line + "\n", tag)
        self.txt_log.see(tk.END)
        self.txt_log.config(state="disabled")

    def next_step(self):
        if self.sim.esta_terminado():
            self.mostrar_relatorio()
            return
        msg = self.sim.executar_ciclo()
        if msg: self.log_msg(msg)
        self.update_view()
        if self.sim.esta_terminado(): self.mostrar_relatorio()

    def prev_step(self):
        msg = self.sim.voltar_ciclo()
        if msg:
            self.txt_log.config(state="normal")
            self.txt_log.delete(1.0, tk.END) 
            self.txt_log.insert(tk.END, f"--- {msg} ---\n", "WRITE")
            self.txt_log.config(state="disabled")
        self.update_view()

    def reset_sim(self):
        self.sim.reset()
        self.txt_log.config(state="normal")
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.config(state="disabled")
        self.update_view()

    def load_example(self):
        self.reset_sim()
        prog = ["ADD R1, R2, R3", "MUL R4, R1, R2", "SUB R5, R3, R1", "DIV R6, R4, R2"]
        self.sim.carregar_instrucoes(prog)
        self.log_msg("Exemplo carregado.")
        self.update_view()

    def update_view(self):
        self.lbl_ciclo.config(text=f"Ciclo Atual: {self.sim.ciclo}")
        for t in [self.tree_rs, self.tree_rob, self.tree_rat, self.tree_reg]:
            for item in t.get_children(): t.delete(item)

        todas_rs = self.sim.rs_add + self.sim.rs_mul
        for rs in todas_rs:
            qj = rs.qj if rs.qj is not None else ""
            qk = rs.qk if rs.qk is not None else ""
            dest = rs.dest if rs.busy else ""
            status_busy = "🔴 Busy" if rs.busy else "🟢 Free"
            self.tree_rs.insert("", "end", values=(rs.nome, status_busy, rs.op if rs.op else "-", rs.vj if rs.vj is not None else "-", rs.vk if rs.vk is not None else "-", qj, qk, dest, rs.tempo_restante))

        for rob in self.sim.rob:
            if rob.busy:
                pronto_icon = "✅ Sim" if rob.pronto else "⏳ Não"
                self.tree_rob.insert("", "end", values=(rob.id, rob.tipo, rob.dest, rob.valor, pronto_icon, str(rob.instrucao)))

        for i in range(16):
            r = f"R{i}"
            rat_val = self.sim.rat[r] if self.sim.rat[r] is not None else "-"
            self.tree_rat.insert("", "end", values=(r, rat_val))
            self.tree_reg.insert("", "end", values=(r, self.sim.regs[r]))

    def open_config_window(self):
        top = tk.Toplevel(self.root)
        top.title("Configurações")
        top.geometry("500x600")
        top.configure(bg=COLORS['bg_app'])
        
        def section_lbl(text):
            return tk.Label(top, text=text, font=self.font_subtitle, bg=COLORS['bg_app'], fg=COLORS['primary'])

        section_lbl("Latências (Ciclos)").pack(pady=(15, 5))
        frame_lat = tk.Frame(top, bg="white", padx=10, pady=10)
        frame_lat.pack(padx=20, fill=tk.X)
        self.entries_lat = {}
        r, c = 0, 0
        for op, val in self.sim.latencias.items():
            tk.Label(frame_lat, text=op, bg="white").grid(row=r, column=c, padx=5, sticky="e")
            entry = tk.Entry(frame_lat, width=5, relief="solid", bd=1)
            entry.insert(0, str(val))
            entry.grid(row=r, column=c+1, padx=5, pady=5)
            self.entries_lat[op] = entry
            c += 2
            if c > 2: c = 0; r += 1

        section_lbl("Registradores Iniciais").pack(pady=(15, 5))
        self.txt_regs = tk.Text(top, height=2, font=("Consolas", 10), relief="flat", bd=1)
        self.txt_regs.pack(padx=20, fill=tk.X)
        regs_str = ", ".join([f"{k}={v}" for k,v in self.sim.regs_iniciais.items()])
        self.txt_regs.insert(tk.END, regs_str)

        section_lbl("Código do Programa").pack(pady=(15, 5))
        self.txt_prog = tk.Text(top, height=8, font=("Consolas", 10), relief="flat", bd=1)
        self.txt_prog.pack(padx=20, fill=tk.BOTH, expand=True)
        prog_text = ""
        for inst in self.sim.fila_instrucoes:
            prog_text += f"{inst.op} {inst.dest}, {inst.s1}, {inst.s2}\n"
        if not prog_text: prog_text = "ADD R1, R2, R3\nMUL R4, R1, R2\nSUB R5, R3, R1\nDIV R6, R4, R2"
        self.txt_prog.insert(tk.END, prog_text)

        tk.Button(top, text="Salvar e Reiniciar", command=lambda: self.save_config(top), bg=COLORS['success'], fg="white", font=("Segoe UI", 11, "bold"), relief="flat", pady=8).pack(fill=tk.X, padx=20, pady=20)

    def save_config(self, window):
        novas_lat = {}
        for op, entry in self.entries_lat.items():
            try: novas_lat[op] = int(entry.get())
            except: pass
        novos_regs = {}
        raw = self.txt_regs.get("1.0", tk.END).replace("\n", "").split(",")
        for item in raw:
            parts = item.split("=")
            if len(parts)==2:
                try: novos_regs[parts[0].strip().upper()] = int(parts[1])
                except: pass
        prog = self.txt_prog.get("1.0", tk.END).strip().split("\n")
        self.sim.set_config(novas_lat, novos_regs)
        self.sim.reset()
        self.sim.carregar_instrucoes(prog)
        window.destroy()
        self.log_msg("Configuração atualizada.")
        self.update_view()

    def mostrar_relatorio(self):
        m = self.sim.metricas
        ciclos = self.sim.ciclo
        ipc = m['commits'] / ciclos if ciclos > 0 else 0
        relatorio = (
            f"Ciclos Totais: {ciclos}\n"
            f"Instruções Commitadas: {m['commits']}\n"
            f"IPC: {ipc:.2f}\n"
            f"Bolhas (Stalls): {m['bolhas']}\n"
            f"Flushes (Desvios): {m['flushes']}\n"
        )
        messagebox.showinfo("Resultados", relatorio)

if __name__ == "__main__":
    root = tk.Tk()
    app = TomasuloGUI(root)
    root.mainloop()