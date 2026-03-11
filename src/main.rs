#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")] // Hide console in release builds

mod config;
mod gui;
mod memory;
mod process;
mod utils;

use eframe::egui;

fn main() -> eframe::Result<()> {
    // Initialize options
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([800.0, 600.0])
            .with_min_inner_size([600.0, 400.0]),
        ..Default::default()
    };

    // Run the application
    eframe::run_native(
        "EndlessOpt - System Optimizer",
        options,
        Box::new(|cc| {
            setup_fonts(&cc.egui_ctx);
            Box::new(gui::EndlessOptApp::new(cc))
        }),
    )
}

fn setup_fonts(ctx: &egui::Context) {
    // Start with the default fonts (we will add more to the default)
    let mut fonts = egui::FontDefinitions::default();

    // Install our own font (maybe supporting non-latin characters).
    // .ttf and .otf files supported.

    // Try to load a system font for better character support
    #[cfg(target_os = "windows")]
    {
        // Use Segoe UI on Windows
        if let Ok(font_data) = std::fs::read("C:\\Windows\\Fonts\\segoeui.ttf") {
            fonts.font_data.insert(
                "SegoeUI".to_owned(),
                egui::FontData::from_owned(font_data),
            );
            fonts
                .families
                .entry(egui::FontFamily::Proportional)
                .or_default()
                .insert(0, "SegoeUI".to_owned());
            fonts
                .families
                .entry(egui::FontFamily::Monospace)
                .or_default()
                .push("SegoeUI".to_owned());
        }
    }

    ctx.set_fonts(fonts);
}
