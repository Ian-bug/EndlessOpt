use eframe::egui;
use egui::{Color32, RichText};
use std::time::Instant;
use crate::config::{Config, PriorityClass, Theme};
use crate::memory::monitor::MemoryStatus;
use crate::process::manager::{ProcessInfo, get_all_processes, set_process_priority, kill_process};
use crate::process::manager::PriorityClass as WinPriorityClass;
use crate::process::gamemode::GameMode;

/// Main application tabs
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Tab {
    Dashboard,
    Optimize,
    Processes,
    Settings,
}

/// Main application state
pub struct EndlessOptApp {
    // Tab management
    current_tab: Tab,

    // System monitoring
    cpu_usage: f32,
    memory_usage: f32,
    memory_status: Option<MemoryStatus>,
    last_update: Instant,

    // Process list
    processes: Vec<ProcessInfo>,
    selected_process: Option<usize>,
    process_filter: String,
    show_blacklisted: bool,

    // Settings
    config: Config,
    config_modified: bool,

    // UI state
    status_message: String,
    status_color: Color32,
    optimization_in_progress: bool,
    game_mode_active: bool,

    // Optimization results
    last_optimization_result: Option<String>,
}

impl EndlessOptApp {
    /// Create a new application instance
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        // Load configuration
        let config = Config::load().unwrap_or_default();

        // Set initial theme
        setup_theme(&cc.egui_ctx, &config.theme);

        Self {
            current_tab: Tab::Dashboard,
            cpu_usage: 0.0,
            memory_usage: 0.0,
            memory_status: None,
            last_update: Instant::now(),
            processes: Vec::new(),
            selected_process: None,
            process_filter: String::new(),
            show_blacklisted: false,
            config,
            config_modified: false,
            status_message: "Ready".to_string(),
            status_color: Color32::GRAY,
            optimization_in_progress: false,
            game_mode_active: false,
            last_optimization_result: None,
        }
    }

    /// Update system monitoring data
    fn update_monitoring(&mut self) {
        let now = Instant::now();
        if now.duration_since(self.last_update).as_secs() >= 1 {
            // Update memory status
            if let Ok(status) = MemoryStatus::get() {
                self.memory_usage = status.memory_load as f32;
                self.memory_status = Some(status);
            }

            // Update CPU usage using sysinfo
            let mut sys = sysinfo::System::new_all();
            sys.refresh_cpu();
            self.cpu_usage = sys.cpus().iter()
                .map(|c| c.cpu_usage())
                .sum::<f32>() / sys.cpus().len() as f32;

            // Update process list occasionally
            if now.duration_since(self.last_update).as_secs() >= 5 {
                if let Ok(processes) = get_all_processes(&self.config.blacklisted_processes) {
                    self.processes = processes;
                }
            }

            self.last_update = now;
        }
    }

    /// Show status message
    fn show_status(&mut self, message: &str, color: Color32) {
        self.status_message = message.to_string();
        self.status_color = color;
    }

    /// Perform full optimization
    fn perform_full_optimization(&mut self) {
        self.optimization_in_progress = true;
        self.show_status("Performing full optimization...", Color32::YELLOW);

        let mut results = Vec::new();

        // Clean memory
        if let Ok(stats) = crate::memory::optimizer::clean_system_memory() {
            results.push(format!("Memory: {}", stats.summary()));
        }

        // Optimize processes
        if let Ok(stats) = crate::process::manager::optimize_processes(
            &self.config.game_processes,
            &self.config.blacklisted_processes,
            self.config.game_priority.clone().into(),
            self.config.bg_priority.clone().into(),
        ) {
            results.push(format!("Processes: {}", stats.summary()));
        }

        // Clean temp files
        if let Ok(stats) = crate::utils::cleaner::clean_temp_files() {
            results.push(format!("Temp Files: {}", stats.summary()));
        }

        // Release network resources
        if self.config.net_optimize {
            if let Ok(stats) = crate::utils::cleaner::release_network_resources() {
                results.push(format!("Network: {}", stats.summary()));
            }
        }

        self.last_optimization_result = Some(results.join("\n"));
        self.optimization_in_progress = false;
        self.show_status("Full optimization complete!", Color32::GREEN);
    }

    /// Activate game mode
    fn activate_game_mode(&mut self) {
        let mut game_mode = GameMode::new(
            self.config.game_processes.clone(),
            self.config.game_priority.clone().into(),
            self.config.bg_priority.clone().into(),
            self.config.mem_clean,
            self.config.net_optimize,
        );

        match game_mode.activate() {
            Ok(result) => {
                self.game_mode_active = true;
                self.show_status(
                    &format!("Game mode activated! {}", result.summary()),
                    Color32::GREEN
                );
            }
            Err(e) => {
                self.show_status(
                    &format!("Failed to activate game mode: {}", e),
                    Color32::RED
                );
            }
        }
    }

    /// Deactivate game mode
    fn deactivate_game_mode(&mut self) {
        let mut game_mode = GameMode::new(
            self.config.game_processes.clone(),
            self.config.game_priority.clone().into(),
            self.config.bg_priority.clone().into(),
            false,
            false,
        );

        match game_mode.deactivate() {
            Ok(result) => {
                self.game_mode_active = false;
                self.show_status(
                    &format!("Game mode deactivated! {}", result.summary()),
                    Color32::GREEN
                );
            }
            Err(e) => {
                self.show_status(
                    &format!("Failed to deactivate game mode: {}", e),
                    Color32::RED
                );
            }
        }
    }
}

impl eframe::App for EndlessOptApp {
    fn update(&mut self, ctx: &egui::Context, frame: &mut eframe::Frame) {
        // Update monitoring data
        self.update_monitoring();

        // Set window properties
        ctx.input(|i| {
            let _ = i.viewport().close_requested();
        });

        // Top panel with tabs
        egui::TopBottomPanel::top("top_panel").show(ctx, |ui| {
            ui.horizontal(|ui| {
                ui.heading(RichText::new("EndlessOpt").size(24.0));
                ui.separator();

                ui.selectable_value(&mut self.current_tab, Tab::Dashboard, "Dashboard");
                ui.selectable_value(&mut self.current_tab, Tab::Optimize, "Optimize");
                ui.selectable_value(&mut self.current_tab, Tab::Processes, "Processes");
                ui.selectable_value(&mut self.current_tab, Tab::Settings, "Settings");

                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    if self.game_mode_active {
                        ui.colored_label(Color32::GREEN, RichText::new("🎮 Game Mode Active").size(14.0));
                    }
                });
            });
        });

        // Status bar
        egui::TopBottomPanel::bottom("status_bar").show(ctx, |ui| {
            ui.horizontal(|ui| {
                ui.label(RichText::new(format!("CPU: {:.1}%", self.cpu_usage)).size(12.0));
                ui.separator();
                ui.label(RichText::new(format!("Memory: {:.1}%", self.memory_usage)).size(12.0));
                ui.separator();
                ui.colored_label(self.status_color, RichText::new(&self.status_message).size(12.0));
            });
        });

        // Main content
        egui::CentralPanel::default().show(ctx, |ui| {
            match self.current_tab {
                Tab::Dashboard => self.show_dashboard(ui, ctx),
                Tab::Optimize => self.show_optimize(ui),
                Tab::Processes => self.show_processes(ui),
                Tab::Settings => self.show_settings(ui),
            }
        });
    }
}

// Implement tab rendering methods
impl EndlessOptApp {
    fn show_dashboard(&mut self, ui: &mut egui::Ui, ctx: &egui::Context) {
        ui.vertical_centered(|ui| {
            ui.heading(RichText::new("System Dashboard").size(28.0));
            ui.add_space(20.0);

            // System status cards
            ui.horizontal(|ui| {
                // CPU card
                ui.group(|ui| {
                    ui.vertical(|ui| {
                        ui.label(RichText::new("CPU Usage").size(16.0));
                        ui.label(RichText::new(format!("{:.1}%", self.cpu_usage)).size(32.0).color(get_usage_color(self.cpu_usage)));
                    });
                });

                ui.add_space(10.0);

                // Memory card
                ui.group(|ui| {
                    ui.vertical(|ui| {
                        ui.label(RichText::new("Memory Usage").size(16.0));
                        ui.label(RichText::new(format!("{:.1}%", self.memory_usage)).size(32.0).color(get_usage_color(self.memory_usage)));
                        if let Some(ref status) = self.memory_status {
                            ui.label(RichText::new(format!(
                                "{} / {}",
                                MemoryStatus::format_bytes(status.total_phys - status.avail_phys),
                                MemoryStatus::format_bytes(status.total_phys)
                            )).size(12.0));
                        }
                    });
                });

                ui.add_space(10.0);

                // Game mode card
                ui.group(|ui| {
                    ui.vertical(|ui| {
                        ui.label(RichText::new("Game Mode").size(16.0));
                        ui.label(RichText::new(if self.game_mode_active { "Active" } else { "Inactive" }).size(24.0)
                            .color(if self.game_mode_active { Color32::GREEN } else { Color32::GRAY }));
                    });
                });
            });

            ui.add_space(30.0);

            // Quick optimize button
            if ui.add_sized(
                [200.0, 50.0],
                egui::Button::new(
                    RichText::new("⚡ Full Optimize").size(18.0)
                )
            ).clicked() {
                self.perform_full_optimization();
            }

            ui.add_space(20.0);

            // Show last optimization result
            if let Some(ref result) = self.last_optimization_result {
                ui.group(|ui| {
                    ui.label(RichText::new("Last Optimization Result").size(14.0));
                    ui.label(RichText::new(result).size(12.0));
                });
            }
        });
    }

    fn show_optimize(&mut self, ui: &mut egui::Ui) {
        ui.vertical_centered(|ui| {
            ui.heading(RichText::new("System Optimization").size(28.0));
            ui.add_space(20.0);

            if self.optimization_in_progress {
                ui.spinner();
                ui.label("Optimizing...");
                return;
            }

            ui.horizontal(|ui| {
                // Clean Memory button
                if ui.add_sized(
                    [150.0, 80.0],
                    egui::Button::new(RichText::new("🧹\nClean Memory").size(14.0))
                ).clicked() {
                    match crate::memory::optimizer::clean_system_memory() {
                        Ok(stats) => {
                            self.show_status(&format!("Memory cleaned: {}", stats.summary()), Color32::GREEN);
                        }
                        Err(e) => {
                            self.show_status(&format!("Failed to clean memory: {}", e), Color32::RED);
                        }
                    }
                }

                // Optimize Processes button
                if ui.add_sized(
                    [150.0, 80.0],
                    egui::Button::new(RichText::new("⚙️\nOptimize Processes").size(14.0))
                ).clicked() {
                    match crate::process::manager::optimize_processes(
                        &self.config.game_processes,
                        &self.config.blacklisted_processes,
                        self.config.game_priority.clone().into(),
                        self.config.bg_priority.clone().into(),
                    ) {
                        Ok(stats) => {
                            self.show_status(&format!("Processes optimized: {}", stats.summary()), Color32::GREEN);
                        }
                        Err(e) => {
                            self.show_status(&format!("Failed to optimize processes: {}", e), Color32::RED);
                        }
                    }
                }

                // Clean Temp Files button
                if ui.add_sized(
                    [150.0, 80.0],
                    egui::Button::new(RichText::new("🗑️\nClean Temp Files").size(14.0))
                ).clicked() {
                    match crate::utils::cleaner::clean_temp_files() {
                        Ok(stats) => {
                            self.show_status(&format!("Temp files cleaned: {}", stats.summary()), Color32::GREEN);
                        }
                        Err(e) => {
                            self.show_status(&format!("Failed to clean temp files: {}", e), Color32::RED);
                        }
                    }
                }

                // Release Network button
                if ui.add_sized(
                    [150.0, 80.0],
                    egui::Button::new(RichText::new("🌐\nRelease Network").size(14.0))
                ).clicked() {
                    match crate::utils::cleaner::release_network_resources() {
                        Ok(stats) => {
                            self.show_status(&format!("Network released: {}", stats.summary()), Color32::GREEN);
                        }
                        Err(e) => {
                            self.show_status(&format!("Failed to release network: {}", e), Color32::RED);
                        }
                    }
                }
            });

            ui.add_space(30.0);

            // Game Mode section
            ui.group(|ui| {
                ui.vertical(|ui| {
                    ui.heading(RichText::new("Game Mode").size(18.0));

                    if self.game_mode_active {
                        if ui.button("Deactivate Game Mode").clicked() {
                            self.deactivate_game_mode();
                        }
                    } else {
                        if ui.button("Activate Game Mode").clicked() {
                            self.activate_game_mode();
                        }
                    }

                    ui.label(RichText::new("Optimizes system for gaming by prioritizing game processes and cleaning resources.").size(12.0).color(Color32::GRAY));
                });
            });
        });
    }

    fn show_processes(&mut self, ui: &mut egui::Ui) {
        ui.vertical(|ui| {
            ui.heading(RichText::new("Process Manager").size(28.0));
            ui.add_space(10.0);

            // Filter and controls
            ui.horizontal(|ui| {
                ui.label("Filter:");
                ui.text_edit_singleline(&mut self.process_filter);
                ui.checkbox(&mut self.show_blacklisted, "Show Blacklisted");

                if ui.button("Refresh").clicked() {
                    if let Ok(processes) = get_all_processes(&self.config.blacklisted_processes) {
                        self.processes = processes;
                        self.show_status("Process list refreshed", Color32::GREEN);
                    }
                }
            });

            ui.add_space(10.0);

            // Process table
            egui::ScrollArea::vertical().show(ui, |ui| {
                // Header
                ui.horizontal(|ui| {
                    ui.label(RichText::new("PID").strong());
                    ui.label(RichText::new("Name").strong());
                    ui.label(RichText::new("CPU %").strong());
                    ui.label(RichText::new("Memory").strong());
                    ui.label(RichText::new("Priority").strong());
                });
                ui.separator();

                // Process rows
                for (idx, process) in self.processes.iter().enumerate() {
                    // Apply filter
                    if !self.process_filter.is_empty()
                        && !process.name.to_lowercase().contains(&self.process_filter.to_lowercase())
                    {
                        continue;
                    }

                    // Skip blacklisted if not showing
                    if process.is_blacklisted && !self.show_blacklisted {
                        continue;
                    }

                    ui.horizontal(|ui| {
                        ui.label(format!("{}", process.pid));
                        ui.label(&process.name);
                        ui.label(format!("{:.1}%", process.cpu_usage));
                        ui.label(format!("{:.1} MB", process.memory_usage as f32 / 1024.0));
                        ui.label(process.priority.as_str());

                        // Context menu
                        if ui.button("⋮").clicked() {
                            self.selected_process = Some(idx);
                        }
                    });
                }
            });

            // Process context menu
            if let Some(idx) = self.selected_process {
                if idx < self.processes.len() {
                    // Clone the process data to avoid borrow issues
                    let process_clone = self.processes[idx].clone();

                    egui::Window::new(format!("Process: {}", process_clone.name))
                        .collapsible(false)
                        .resizable(false)
                        .show(ui.ctx(), |ui| {
                            ui.vertical(|ui| {
                                ui.label(format!("PID: {}", process_clone.pid));
                                ui.label(format!("CPU: {:.1}%", process_clone.cpu_usage));
                                ui.label(format!("Memory: {:.1} MB", process_clone.memory_usage as f32 / 1024.0));
                                ui.label(format!("Priority: {}", process_clone.priority.as_str()));

                                ui.separator();

                                ui.label("Set Priority:");
                                let pid = process_clone.pid;
                                if ui.button("Idle").clicked() {
                                    let _ = set_process_priority(pid, WinPriorityClass::Idle);
                                }
                                ui.horizontal(|ui| {
                                    if ui.button("Below Normal").clicked() {
                                        let _ = set_process_priority(pid, WinPriorityClass::BelowNormal);
                                    }
                                    if ui.button("Normal").clicked() {
                                        let _ = set_process_priority(pid, WinPriorityClass::Normal);
                                    }
                                });
                                ui.horizontal(|ui| {
                                    if ui.button("Above Normal").clicked() {
                                        let _ = set_process_priority(pid, WinPriorityClass::AboveNormal);
                                    }
                                    if ui.button("High").clicked() {
                                        let _ = set_process_priority(pid, WinPriorityClass::High);
                                    }
                                });

                                ui.separator();

                                if ui.button(RichText::new("Kill Process").color(Color32::RED)).clicked() {
                                    match kill_process(pid) {
                                        Ok(_) => {
                                            self.show_status(&format!("Process {} killed", process_clone.name), Color32::GREEN);
                                            self.selected_process = None;
                                        }
                                        Err(e) => {
                                            self.show_status(&format!("Failed to kill process: {}", e), Color32::RED);
                                        }
                                    }
                                }

                                if ui.button("Close").clicked() {
                                    self.selected_process = None;
                                }
                            });
                        });
                }
            }
        });
    }

    fn show_settings(&mut self, ui: &mut egui::Ui) {
        ui.vertical(|ui| {
            ui.heading(RichText::new("Settings").size(28.0));
            ui.add_space(20.0);

            egui::ScrollArea::vertical().show(ui, |ui| {
                // Auto-optimization
                ui.group(|ui| {
                    ui.heading(RichText::new("Auto-Optimization").size(16.0));
                    ui.checkbox(&mut self.config.auto_optimize, "Enable Auto-Optimization");

                    if self.config.auto_optimize {
                        ui.add(egui::Slider::new(&mut self.config.auto_interval, 1..=60)
                            .text("Interval (minutes)"));
                    }

                    self.config_modified = true;
                });

                ui.add_space(10.0);

                // Game Mode Settings
                ui.group(|ui| {
                    ui.heading(RichText::new("Game Mode Settings").size(16.0));
                    ui.checkbox(&mut self.config.auto_game_mode, "Auto-activate Game Mode");

                    ui.horizontal(|ui| {
                        ui.label("Game Priority:");
                        egui::ComboBox::from_id_source("game_priority")
                            .selected_text(format!("{:?}", self.config.game_priority))
                            .show_ui(ui, |ui| {
                                ui.selectable_value(&mut self.config.game_priority, PriorityClass::Idle, "Idle");
                                ui.selectable_value(&mut self.config.game_priority, PriorityClass::BelowNormal, "Below Normal");
                                ui.selectable_value(&mut self.config.game_priority, PriorityClass::Normal, "Normal");
                                ui.selectable_value(&mut self.config.game_priority, PriorityClass::AboveNormal, "Above Normal");
                                ui.selectable_value(&mut self.config.game_priority, PriorityClass::High, "High");
                                ui.selectable_value(&mut self.config.game_priority, PriorityClass::Realtime, "Realtime");
                            });
                    });

                    ui.horizontal(|ui| {
                        ui.label("Background Priority:");
                        egui::ComboBox::from_id_source("bg_priority")
                            .selected_text(format!("{:?}", self.config.bg_priority))
                            .show_ui(ui, |ui| {
                                ui.selectable_value(&mut self.config.bg_priority, PriorityClass::Idle, "Idle");
                                ui.selectable_value(&mut self.config.bg_priority, PriorityClass::BelowNormal, "Below Normal");
                                ui.selectable_value(&mut self.config.bg_priority, PriorityClass::Normal, "Normal");
                                ui.selectable_value(&mut self.config.bg_priority, PriorityClass::AboveNormal, "Above Normal");
                                ui.selectable_value(&mut self.config.bg_priority, PriorityClass::High, "High");
                                ui.selectable_value(&mut self.config.bg_priority, PriorityClass::Realtime, "Realtime");
                            });
                    });

                    ui.checkbox(&mut self.config.mem_clean, "Clean Memory in Game Mode");
                    ui.checkbox(&mut self.config.net_optimize, "Optimize Network in Game Mode");

                    self.config_modified = true;
                });

                ui.add_space(10.0);

                // Game Processes
                ui.group(|ui| {
                    ui.heading(RichText::new("Game Processes").size(16.0));
                    ui.label("Enter game process names (comma-separated, e.g., minecraft.exe, steam.exe):");

                    let game_processes_str = self.config.game_processes.join(", ");
                    let mut game_processes_text = game_processes_str;

                    if ui.text_edit_multiline(&mut game_processes_text).changed() {
                        self.config.game_processes = game_processes_text
                            .split(',')
                            .map(|s| s.trim().to_string())
                            .filter(|s| !s.is_empty())
                            .collect();
                        self.config_modified = true;
                    }

                    ui.label(format!("{} game processes configured", self.config.game_processes.len()));
                });

                ui.add_space(10.0);

                // Process Blacklist
                ui.group(|ui| {
                    ui.heading(RichText::new("Process Blacklist").size(16.0));
                    ui.label("Enter process names to exclude from optimization (comma-separated):");

                    let blacklist_str = self.config.blacklisted_processes.join(", ");
                    let mut blacklist_text = blacklist_str;

                    if ui.text_edit_multiline(&mut blacklist_text).changed() {
                        self.config.blacklisted_processes = blacklist_text
                            .split(',')
                            .map(|s| s.trim().to_string())
                            .filter(|s| !s.is_empty())
                            .collect();
                        self.config_modified = true;
                    }

                    ui.label(format!("{} processes blacklisted", self.config.blacklisted_processes.len()));
                });

                ui.add_space(10.0);

                // Theme
                ui.group(|ui| {
                    ui.heading(RichText::new("Appearance").size(16.0));

                    ui.horizontal(|ui| {
                        ui.label("Theme:");
                        if ui.selectable_value(&mut self.config.theme, Theme::Light, "Light").changed() {
                            setup_theme(ui.ctx(), &Theme::Light);
                            self.config_modified = true;
                        }
                        if ui.selectable_value(&mut self.config.theme, Theme::Dark, "Dark").changed() {
                            setup_theme(ui.ctx(), &Theme::Dark);
                            self.config_modified = true;
                        }
                        if ui.selectable_value(&mut self.config.theme, Theme::System, "System").changed() {
                            setup_theme(ui.ctx(), &Theme::System);
                            self.config_modified = true;
                        }
                    });
                });

                ui.add_space(20.0);

                // Save button
                ui.horizontal(|ui| {
                    if ui.button("Save Configuration").clicked() {
                        match self.config.save() {
                            Ok(_) => {
                                self.show_status("Configuration saved", Color32::GREEN);
                                self.config_modified = false;
                            }
                            Err(e) => {
                                self.show_status(&format!("Failed to save: {}", e), Color32::RED);
                            }
                        }
                    }

                    if ui.button("Reset to Defaults").clicked() {
                        self.config = Config::default();
                        setup_theme(ui.ctx(), &self.config.theme);
                        self.config_modified = true;
                        self.show_status("Configuration reset to defaults", Color32::YELLOW);
                    }
                });
            });
        });
    }
}

// Helper functions

fn get_usage_color(usage: f32) -> Color32 {
    if usage < 50.0 {
        Color32::GREEN
    } else if usage < 80.0 {
        Color32::YELLOW
    } else {
        Color32::RED
    }
}

fn setup_theme(ctx: &egui::Context, theme: &Theme) {
    match theme {
        Theme::Light => {
            ctx.set_visuals(egui::Visuals::light());
        }
        Theme::Dark => {
            ctx.set_visuals(egui::Visuals::dark());
        }
        Theme::System => {
            // Check system preference
            let is_dark = ctx.style().visuals.dark_mode;
            if is_dark {
                ctx.set_visuals(egui::Visuals::dark());
            } else {
                ctx.set_visuals(egui::Visuals::light());
            }
        }
    }
}

// Conversion implementations

impl From<PriorityClass> for crate::process::manager::PriorityClass {
    fn from(p: PriorityClass) -> Self {
        match p {
            PriorityClass::Idle => crate::process::manager::PriorityClass::Idle,
            PriorityClass::BelowNormal => crate::process::manager::PriorityClass::BelowNormal,
            PriorityClass::Normal => crate::process::manager::PriorityClass::Normal,
            PriorityClass::AboveNormal => crate::process::manager::PriorityClass::AboveNormal,
            PriorityClass::High => crate::process::manager::PriorityClass::High,
            PriorityClass::Realtime => crate::process::manager::PriorityClass::Realtime,
        }
    }
}
