# EndlessOpt

A comprehensive system optimization tool for Windows built in Rust. EndlessOpt combines memory monitoring, process optimization, and game mode features to help you get the most out of your system.

## Features

### 🚀 System Optimization
- **Memory Cleaning**: Free up RAM by cleaning process working sets
- **Process Priority Management**: Automatically optimize process priorities for better performance
- **Temporary File Cleaning**: Remove unnecessary temporary files to free disk space
- **Network Optimization**: Release network resources for better connectivity

### 🎮 Game Mode
- Automatically detect and prioritize game processes
- Optimize background processes to reduce CPU/usage interference
- Optional memory cleaning during gaming sessions
- Configurable game process list

### 📊 Real-time Monitoring
- Live CPU usage monitoring
- Memory usage tracking with detailed statistics
- Process list with filtering and management options

### ⚙️ Configuration
- Auto-optimization scheduling
- Customizable priority classes for games and background processes
- Process blacklist to exclude critical system processes
- Theme selection (Light/Dark/System)

## Installation

### Prerequisites
- Windows 10 or later
- Administrator rights (required for process priority changes)

### Build from Source
```bash
# Clone the repository
git clone https://github.com/yourusername/endlessopt.git
cd endlessopt

# Build the project
cargo build --release

# Run the application
./target/release/endlessopt.exe
```

## Usage

### Quick Start
1. Launch EndlessOpt
2. Click **"⚡ Full Optimize"** on the Dashboard for comprehensive optimization
3. Use the **Optimize** tab for individual optimization actions
4. Configure settings in the **Settings** tab

### Game Mode
1. Go to **Settings** → **Game Mode Settings**
2. Add your game processes (e.g., `minecraft.exe`, `steam.exe`)
3. Set desired priorities for games and background processes
4. Activate Game Mode manually or enable auto-activation

### Process Management
1. Go to the **Processes** tab
2. Browse running processes with filtering options
3. Right-click any process to:
   - Change priority
   - Kill process
   - Add to blacklist

## Configuration

EndlessOpt stores configuration in `~/.endlessopt/config.json`. Default settings include:

- **Auto-optimization**: Disabled
- **Game Mode**: High priority for games, Below Normal for background
- **Blacklisted Processes**: System processes protected from optimization

### Example Configuration
```json
{
  "auto_optimize": false,
  "auto_interval": 30,
  "auto_game_mode": false,
  "game_priority": "High",
  "bg_priority": "BelowNormal",
  "mem_clean": true,
  "net_optimize": true,
  "game_processes": [
    "minecraft.exe",
    "steam.exe",
    "javaw.exe"
  ],
  "blacklisted_processes": [
    "system",
    "svchost.exe",
    "explorer.exe"
  ],
  "theme": "Dark"
}
```

## System Requirements

- **OS**: Windows 10/11 (x64)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 50MB for installation
- **Permissions**: Administrator rights recommended for full functionality

## Architecture

EndlessOpt is built with:
- **Rust** - Core language for performance and safety
- **egui/eframe** - Fast and friendly GUI framework
- **windows-rs** - Windows API bindings for system operations
- **sysinfo** - Cross-platform system information

### Key Modules
- `memory/monitor.rs` - Memory status monitoring (inspired by PCL-CE)
- `memory/optimizer.rs` - Memory cleaning with EmptyWorkingSet API
- `process/manager.rs` - Process enumeration and priority management
- `process/gamemode.rs` - Game detection and optimization
- `utils/cleaner.rs` - Temporary file and network resource cleaning
- `gui/` - User interface with egui

## Safety and Permissions

**Note**: EndlessOpt requires administrator rights to modify process priorities and clean system memory. Always review the processes you're optimizing and avoid modifying critical system processes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **PCL-CE (PCL Community Edition)** - Memory monitoring patterns and Windows API usage
- **Process Optimizer (Python)** - Optimization logic and game mode inspiration
- **egui** - Excellent GUI framework for Rust

## Disclaimer

This software is provided as-is for educational and optimization purposes. Always create system backups before making significant changes to your system configuration. The authors are not responsible for any system instability or data loss.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.
