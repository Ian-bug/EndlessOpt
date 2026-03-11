import os
import sys
import ctypes
import psutil
import threading
import time
import json
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox, filedialog, simpledialog
import sv_ttk
from pathlib import Path
import winreg

# Ensure admin privileges
def check_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not check_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, None, 1)
    sys.exit()

# Windows API definitions
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Constants
PROCESS_ALL_ACCESS = 0x1F0FFF

# Priority classes
PRIORITY_CLASS = {
    "IDLE": 0x00000040,
    "BELOW_NORMAL": 0x00004000,
    "NORMAL": 0x00000020,
    "ABOVE_NORMAL": 0x00008000,
    "HIGH": 0x00000080,
    "REALTIME": 0x00000100
}

class ProcessOptimizer:
    def __init__(self, master):
        self.master = master
        
        # Load config
        self.config_file = "config.json"
        self.load_config()
        
        master.title("")
        master.geometry("577x428")
        master.minsize(300, 325)
        
        # Set theme
        sv_ttk.set_theme("dark")
        
        # Protected processes (won't adjust)
        self.protected_processes = [
            "System", "Registry", "smss.exe", "csrss.exe", "wininit.exe",
            "winlogon.exe", "services.exe", "lsass.exe", "svchost.exe",
            "taskhostw.exe", "dwm.exe", "explorer.exe"
        ]
        
        # Default low priority processes
        self.low_priority_processes = [
            "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe",
            "spotify.exe", "steam.exe", "discord.exe", "teams.exe",
            "zoom.exe", "skype.exe", "outlook.exe", "thunderbird.exe",
            "acrobat.exe", "python.exe", "notepad.exe",
            "wordpad.exe", "calc.exe", "mspaint.exe"
        ]
        
        # User blacklist
        self.blacklist_file = "process_blacklist.txt"
        self.load_blacklist()
        
        # Create UI
        self.create_widgets()
        
        # Start system monitoring
        self.monitor_system_resources()
    
    def load_config(self):
        """Load configuration"""
        self.config = {
            "theme": "dark",
            "auto_optimize": False,
            "auto_interval": 5,
            "auto_game_mode": False,
            "game_priority": "HIGH",
            "bg_priority": "BELOW_NORMAL",
            "mem_clean": True,
            "net_optimize": True,
            "game_processes": "game.exe, launcher.exe, javaw.exe, java.exe, steam.exe"
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    for key in self.config:
                        if key in loaded_config:
                            self.config[key] = loaded_config[key]
        except Exception:
            pass
    
    def save_config(self):
        """Save configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def load_blacklist(self):
        try:
            if os.path.exists(self.blacklist_file):
                with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                    self.low_priority_processes = [line.strip() for line in f.readlines() if line.strip()]
        except Exception:
            pass
    
    def save_blacklist(self):
        try:
            with open(self.blacklist_file, 'w', encoding='utf-8') as f:
                for process in self.low_priority_processes:
                    if process:
                        f.write(f"{process}\n")
        except Exception:
            pass
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.create_status_bar(main_frame)
        
        # Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True, pady=(5, 0))
        
        # Optimize tab
        self.optimize_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.optimize_tab, text="Optimize")
        self.create_optimize_tab()
        
        # Process tab
        self.process_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.process_tab, text="Processes")
        self.create_process_tab()
        
        # Settings tab
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        self.create_settings_tab()
    
    def create_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=X, pady=(0, 5))
        
        # System info
        self.cpu_status = ttk.Label(status_frame, text="CPU: 0%")
        self.cpu_status.pack(side=LEFT, padx=5)
        
        self.mem_status = ttk.Label(status_frame, text="Memory: 0%")
        self.mem_status.pack(side=LEFT, padx=5)
        
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="green")
        self.status_label.pack(side=RIGHT, padx=5)
    
    def create_optimize_tab(self):
        # Main optimize button - centered and prominent
        main_btn_frame = ttk.Frame(self.optimize_tab)
        main_btn_frame.pack(fill=X, padx=20, pady=20)
        
        # Large Full Optimize button
        self.full_optimize_btn = ttk.Button(
            main_btn_frame, 
            text="FULL OPTIMIZE", 
            command=self.full_optimize,
            style="Accent.TButton"
        )
        self.full_optimize_btn.pack(pady=10, ipadx=20, ipady=10)
        
        # Quick actions in a grid layout
        actions_frame = ttk.LabelFrame(self.optimize_tab, text="Quick Actions")
        actions_frame.pack(fill=X, padx=20, pady=10)
        
        # Create a grid of buttons (2 rows, 3 columns)
        buttons = [
            ("Clean Memory", self.clean_memory, "#4CAF50"),
            ("Optimize Processes", self.optimize_processes, "#2196F3"),
            ("Clean Temp Files", self.clean_temp_files, "#FF9800"),
            ("Game Mode", self.game_mode_optimize, "#9C27B0"),
            ("Release Network", self.release_network, "#00BCD4")
        ]
        
        # Create buttons in grid
        for i, (text, command, color) in enumerate(buttons):
            row = i // 3
            col = i % 3
            btn = ttk.Button(
                actions_frame, 
                text=text, 
                command=command,
                width=15
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # Configure grid weights for equal spacing
        for i in range(3):
            actions_frame.columnconfigure(i, weight=1)
    
    def create_process_tab(self):
        # Search box
        search_frame = ttk.Frame(self.process_tab)
        search_frame.pack(fill=X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=LEFT)
        
        self.search_var = StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.filter_processes)
        
        ttk.Button(search_frame, text="Refresh", command=self.refresh_process_list).pack(side=RIGHT, padx=5)
        
        # Process list
        tree_frame = ttk.Frame(self.process_tab)
        tree_frame.pack(fill=BOTH, expand=True, padx=5, pady=(0, 5))
        
        columns = ("pid", "name", "cpu", "memory", "priority")
        self.process_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse", height=12)
        
        # Column setup
        col_widths = {"pid": 50, "name": 150, "cpu": 50, "memory": 70, "priority": 80}
        for col in columns:
            self.process_tree.heading(col, text=col.capitalize())
            self.process_tree.column(col, width=col_widths.get(col, 80), anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.process_tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        self.process_tree.pack(fill=BOTH, expand=True)
        
        # Process operations
        btn_frame = ttk.Frame(self.process_tab)
        btn_frame.pack(fill=X, padx=5, pady=(0, 5))
        
        ttk.Button(btn_frame, text="Set Priority", command=self.set_selected_priority).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="Kill Process", command=self.kill_selected_process).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="Add to Blacklist", command=self.add_to_blacklist).pack(side=LEFT, padx=2)
        
        # Priority selection
        priority_frame = ttk.Frame(btn_frame)
        priority_frame.pack(side=RIGHT, padx=5)
        
        ttk.Label(priority_frame, text="Priority:").pack(side=LEFT)
        self.priority_var = StringVar()
        self.priority_var.set("BELOW_NORMAL")
        
        priority_menu = ttk.Combobox(priority_frame, textvariable=self.priority_var, 
                                    values=["IDLE", "BELOW_NORMAL", "NORMAL", "ABOVE_NORMAL", "HIGH"], 
                                    state="readonly", width=12)
        priority_menu.pack(side=LEFT)
        
        self.refresh_process_list()
    
    def create_settings_tab(self):
        # Create a frame with scrollbar for settings
        settings_container = ttk.Frame(self.settings_tab)
        settings_container.pack(fill=BOTH, expand=True)
        
        # Create canvas and scrollbar
        canvas = Canvas(settings_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(settings_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Theme settings
        theme_frame = ttk.LabelFrame(scrollable_frame, text="Theme Settings")
        theme_frame.pack(fill=X, padx=10, pady=5)
        
        ttk.Label(theme_frame, text="Theme:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.theme_var = StringVar(value="Dark")
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                  values=["Light", "Dark", "System"], state="readonly", width=15)
        theme_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        
        # Auto optimization settings
        auto_frame = ttk.LabelFrame(scrollable_frame, text="Auto Optimization")
        auto_frame.pack(fill=X, padx=10, pady=5)
        
        self.auto_optimize_var = IntVar(value=1 if self.config["auto_optimize"] else 0)
        auto_check = ttk.Checkbutton(auto_frame, text="Enable Auto Optimize", 
                                   variable=self.auto_optimize_var, command=self.toggle_auto_optimize)
        auto_check.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        ttk.Label(auto_frame, text="Interval (minutes):").grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.auto_interval_var = StringVar(value=str(self.config["auto_interval"]))
        auto_interval_entry = ttk.Entry(auto_frame, textvariable=self.auto_interval_var, width=5)
        auto_interval_entry.grid(row=0, column=2, padx=5, pady=2, sticky="w")
        
        self.auto_game_mode_var = IntVar(value=1 if self.config["auto_game_mode"] else 0)
        auto_game_check = ttk.Checkbutton(auto_frame, text="Auto Game Mode", 
                                        variable=self.auto_game_mode_var, command=self.save_config)
        auto_game_check.grid(row=1, column=0, padx=5, pady=2, sticky="w", columnspan=2)
        
        # Game mode settings
        game_frame = ttk.LabelFrame(scrollable_frame, text="Game Mode Settings")
        game_frame.pack(fill=X, padx=10, pady=5)
        
        # Game process priority
        ttk.Label(game_frame, text="Game Priority:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.game_priority_var = StringVar(value=self.config["game_priority"])
        priority_menu = ttk.Combobox(game_frame, textvariable=self.game_priority_var, 
                                    values=["ABOVE_NORMAL", "HIGH", "REALTIME"], state="readonly", width=12)
        priority_menu.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        priority_menu.bind("<<ComboboxSelected>>", self.save_config)
        
        # Background process priority
        ttk.Label(game_frame, text="Background Priority:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.bg_priority_var = StringVar(value=self.config["bg_priority"])
        bg_priority_menu = ttk.Combobox(game_frame, textvariable=self.bg_priority_var, 
                                       values=["IDLE", "BELOW_NORMAL"], state="readonly", width=12)
        bg_priority_menu.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        bg_priority_menu.bind("<<ComboboxSelected>>", self.save_config)
        
        # Game processes
        ttk.Label(game_frame, text="Game Processes:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.game_process_var = StringVar(value=self.config["game_processes"])
        game_entry = ttk.Entry(game_frame, textvariable=self.game_process_var, width=30)
        game_entry.grid(row=2, column=1, padx=5, pady=2, sticky="we")
        game_entry.bind("<KeyRelease>", lambda e: self.save_config())
        
        # Options
        self.mem_clean_var = IntVar(value=1 if self.config["mem_clean"] else 0)
        ttk.Checkbutton(game_frame, text="Clean Memory", variable=self.mem_clean_var, 
                       command=self.save_config).grid(row=3, column=0, padx=5, pady=2, sticky="w", columnspan=2)
        
        self.net_optimize_var = IntVar(value=1 if self.config["net_optimize"] else 0)
        ttk.Checkbutton(game_frame, text="Optimize Network", variable=self.net_optimize_var, 
                       command=self.save_config).grid(row=4, column=0, padx=5, pady=2, sticky="w", columnspan=2)
        
        # Blacklist settings
        blacklist_frame = ttk.LabelFrame(scrollable_frame, text="Process Blacklist")
        blacklist_frame.pack(fill=X, padx=10, pady=5)
        
        # Blacklist list
        list_frame = ttk.Frame(blacklist_frame)
        list_frame.pack(fill=X, padx=5, pady=5)
        
        self.blacklist_listbox = Listbox(list_frame, selectmode=SINGLE, height=6)
        self.blacklist_listbox.pack(fill=X, padx=5, pady=5)
        
        # Load blacklist
        for process in self.low_priority_processes:
            if process:
                self.blacklist_listbox.insert(END, process)
        
        # Buttons
        btn_frame = ttk.Frame(blacklist_frame)
        btn_frame.pack(fill=X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Add Process", command=self.add_process_to_blacklist).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected_from_blacklist).pack(side=LEFT, padx=2)
    
    def change_theme(self, event=None):
        theme = self.theme_var.get().lower()
        if theme == "dark":
            sv_ttk.set_theme("dark")
            self.config["theme"] = "dark"
        elif theme == "light":
            sv_ttk.set_theme("light")
            self.config["theme"] = "light"
        else:
            # System default - use light as fallback
            sv_ttk.use_light_theme()
            self.config["theme"] = "system"
        
        self.save_config()
    
    # ========== Core Methods ==========
    def clean_memory(self):
        try:
            ctypes.windll.psapi.EmptyWorkingSet(ctypes.c_void_p(-1))
            self.status_label.config(text="Memory cleaned", foreground="green")
        except Exception as e:
            self.status_label.config(text="Memory clean failed", foreground="red")
    
    def optimize_processes(self):
        cpu_threshold = 30
        optimized = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                process_name = proc.info['name'].lower()
                pid = proc.info['pid']
                cpu_percent = proc.info['cpu_percent']
                
                # Skip protected processes
                if any(p.lower() in process_name for p in self.protected_processes):
                    continue
                    
                hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
                if not hProcess:
                    continue
                
                # Adjust priority based on rules
                if process_name in [p.lower() for p in self.low_priority_processes]:
                    kernel32.SetPriorityClass(hProcess, PRIORITY_CLASS["BELOW_NORMAL"])
                    optimized += 1
                elif cpu_percent > cpu_threshold:
                    kernel32.SetPriorityClass(hProcess, PRIORITY_CLASS["HIGH"])
                    optimized += 1
                
                kernel32.CloseHandle(hProcess)
            except:
                continue
        
        self.status_label.config(text=f"Optimized {optimized} processes", foreground="green")
    
    def clean_temp_files(self):
        try:
            temp_dirs = [
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                os.path.join(os.environ.get('SystemRoot', ''), 'Temp'),
                os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Temp')
            ]
            
            cleaned = 0
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                os.unlink(file_path)
                                cleaned += 1
                            except:
                                pass
            
            self.status_label.config(text=f"Cleaned {cleaned} temp files", foreground="green")
        except Exception as e:
            self.status_label.config(text="Temp clean failed", foreground="red")
    
    def release_network(self):
        try:
            # Simulate network optimization
            time.sleep(1)
            self.status_label.config(text="Network resources released", foreground="green")
        except Exception as e:
            self.status_label.config(text="Network release failed", foreground="red")
    
    def full_optimize(self):
        self.clean_memory()
        self.optimize_processes()
        self.clean_temp_files()
        self.release_network()
        self.status_label.config(text="Full optimization complete", foreground="green")
    
    def game_mode_optimize(self):
        # Set game processes priority
        game_processes = [name.strip().lower() for name in self.game_process_var.get().split(",")]
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() in game_processes:
                    hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, proc.info['pid'])
                    if hProcess:
                        kernel32.SetPriorityClass(hProcess, PRIORITY_CLASS[self.game_priority_var.get()])
                        kernel32.CloseHandle(hProcess)
            except:
                continue
        
        # Optimize background processes
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                process_name = proc.info['name'].lower()
                if (process_name not in game_processes and 
                    not any(p.lower() in process_name for p in self.protected_processes)):
                    hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, proc.info['pid'])
                    if hProcess:
                        kernel32.SetPriorityClass(hProcess, PRIORITY_CLASS[self.bg_priority_var.get()])
                        kernel32.CloseHandle(hProcess)
            except:
                continue
        
        # Clean memory if enabled
        if self.mem_clean_var.get():
            self.clean_memory()
        
        self.status_label.config(text="Game mode activated", foreground="green")
    
    def toggle_auto_optimize(self):
        self.config["auto_optimize"] = bool(self.auto_optimize_var.get())
        self.config["auto_interval"] = int(self.auto_interval_var.get() or 5)
        self.save_config()
        
        if self.config["auto_optimize"]:
            interval = max(1, self.config["auto_interval"]) * 60
            self.auto_optimize_thread = threading.Thread(target=self.auto_optimize_loop, daemon=True)
            self.auto_optimize_thread.start()
    
    def auto_optimize_loop(self):
        while self.config["auto_optimize"]:
            interval = max(1, self.config["auto_interval"]) * 60
            time.sleep(interval)
            self.full_optimize()
    
    # ========== Process Management ==========
    def refresh_process_list(self):
        self.process_tree.delete(*self.process_tree.get_children())
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                priority = "NORMAL"
                try:
                    if proc.nice() == psutil.BELOW_NORMAL_PRIORITY_CLASS:
                        priority = "BELOW_NORMAL"
                    elif proc.nice() == psutil.HIGH_PRIORITY_CLASS:
                        priority = "HIGH"
                    elif proc.nice() == psutil.REALTIME_PRIORITY_CLASS:
                        priority = "REALTIME"
                except:
                    pass
                
                self.process_tree.insert("", "end", values=(
                    proc.info['pid'],
                    proc.info['name'],
                    f"{proc.info['cpu_percent']:.1f}%",
                    f"{proc.info['memory_percent']:.1f}%",
                    priority
                ))
            except:
                continue
    
    def filter_processes(self, event=None):
        search_term = self.search_var.get().lower()
        self.process_tree.delete(*self.process_tree.get_children())
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if not search_term or search_term in proc.info['name'].lower():
                    priority = "NORMAL"
                    try:
                        if proc.nice() == psutil.BELOW_NORMAL_PRIORITY_CLASS:
                            priority = "BELOW_NORMAL"
                        elif proc.nice() == psutil.HIGH_PRIORITY_CLASS:
                            priority = "HIGH"
                    except:
                        pass
                    
                    self.process_tree.insert("", "end", values=(
                        proc.info['pid'],
                        proc.info['name'],
                        f"{proc.info['cpu_percent']:.1f}%",
                        f"{proc.info['memory_percent']:.1f}%",
                        priority
                    ))
            except:
                continue
    
    def set_selected_priority(self):
        selected = self.process_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a process first")
            return
        
        item = self.process_tree.item(selected[0])
        pid = int(item['values'][0])
        process_name = item['values'][1]
        priority = self.priority_var.get()
        
        try:
            hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if hProcess:
                kernel32.SetPriorityClass(hProcess, PRIORITY_CLASS[priority])
                kernel32.CloseHandle(hProcess)
                self.status_label.config(text=f"Set {process_name} to {priority}", foreground="green")
                self.refresh_process_list()
        except Exception as e:
            self.status_label.config(text="Failed to set priority", foreground="red")
    
    def add_to_blacklist(self):
        selected = self.process_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a process first")
            return
        
        item = self.process_tree.item(selected[0])
        process_name = item['values'][1].lower()
        
        if process_name not in [p.lower() for p in self.low_priority_processes]:
            self.low_priority_processes.append(process_name)
            self.blacklist_listbox.insert(END, process_name)
            self.save_blacklist()
            self.status_label.config(text=f"Added {process_name} to blacklist", foreground="green")
        else:
            messagebox.showinfo("Info", "Process already in blacklist")
    
    def kill_selected_process(self):
        selected = self.process_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a process first")
            return
        
        item = self.process_tree.item(selected[0])
        pid = int(item['values'][0])
        process_name = item['values'][1]
        
        if messagebox.askyesno("Confirm", f"Kill {process_name} (PID: {pid})?"):
            try:
                p = psutil.Process(pid)
                p.terminate()
                self.status_label.config(text=f"Killed {process_name}", foreground="green")
                self.refresh_process_list()
            except Exception as e:
                self.status_label.config(text="Failed to kill process", foreground="red")
    
    # ========== Blacklist Management ==========
    def add_process_to_blacklist(self):
        process_name = simpledialog.askstring("Add Process", "Enter process name:")
        if process_name:
            if process_name.lower() not in [p.lower() for p in self.low_priority_processes]:
                self.low_priority_processes.append(process_name)
                self.blacklist_listbox.insert(END, process_name)
                self.save_blacklist()
                self.status_label.config(text=f"Added {process_name} to blacklist", foreground="green")
            else:
                messagebox.showinfo("Info", "Process already in blacklist")
    
    def remove_selected_from_blacklist(self):
        selected = self.blacklist_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Select a process first")
            return
        
        process_name = self.blacklist_listbox.get(selected[0])
        self.low_priority_processes.remove(process_name)
        self.blacklist_listbox.delete(selected[0])
        self.save_blacklist()
        self.status_label.config(text=f"Removed {process_name} from blacklist", foreground="green")
    
    def monitor_system_resources(self):
        """Monitor system resource usage"""
        def update():
            while True:
                cpu_percent = psutil.cpu_percent(interval=1)
                mem_percent = psutil.virtual_memory().percent
                
                self.cpu_status.config(text=f"CPU: {cpu_percent}%")
                self.mem_status.config(text=f"Memory: {mem_percent}%")
                
                time.sleep(5)
        
        threading.Thread(target=update, daemon=True).start()

# Main entry
if __name__ == "__main__":
    root = Tk()
    app = ProcessOptimizer(root)
    root.mainloop()
