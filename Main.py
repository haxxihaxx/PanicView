import os
import subprocess
import glob
import tempfile
import tkinter as tk
from tkinter import scrolledtext, messagebox

# --- Panic Log Analyzer GUI for macOS ---
# Requirements: brew install libimobiledevice

def pull_panic_logs(output_dir):
    """Pull panic logs from connected iPhone using libimobiledevice."""
    try:
        subprocess.run(
            ["idevicepaniclog", output_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", "❌ Failed to pull panic logs.\n"
                             "Make sure iPhone is connected and trusted.")
        return False

def get_latest_panic_file(output_dir):
    """Return the newest panic-full file from pulled logs."""
    panic_files = glob.glob(os.path.join(output_dir, "panic-full*"))
    if not panic_files:
        return None
    return max(panic_files, key=os.path.getmtime)

def interpret_panic(file_path):
    """Interpret panic causes and suggest repair parts."""
    with open(file_path, "r", errors="ignore") as f:
        log = f.read()

    interpretations = []

    if "userspace watchdog" in log.lower():
        interpretations.append(("📱 Userspace Watchdog: iOS or app froze.",
                                "🔧 Likely software issue → DFU restore."))

    if "missingkeys.plist" in log.lower():
        interpretations.append(("🔑 Missing Keys: Hardware/software mismatch.",
                                "🔧 Logic board replacement or reflash."))

    if "aop panic" in log.lower():
        interpretations.append(("⚡ AOP Panic: Always-On Processor failure.",
                                "🔧 Replace/repair AOP IC (logic board)."))

    if "baseband" in log.lower():
        interpretations.append(("📡 Baseband Crash: Cellular/modem issue.",
                                "🔧 Replace/reball baseband IC."))

    if "thermalmonitord" in log.lower():
        interpretations.append(("🔥 Thermal Issue: Device overheated.",
                                "🔧 Replace thermal sensor / check PMU or battery."))

    if "pmgr" in log.lower():
        interpretations.append(("🔋 Power Manager Issue: PMU failure.",
                                "🔧 Replace PMU chip."))

    if "memory" in log.lower() or "page fault" in log.lower():
        interpretations.append(("💾 Memory Fault: RAM/NAND corruption.",
                                "🔧 Replace RAM/NAND chips."))

    if not interpretations:
        interpretations.append(("❔ Unknown panic cause.",
                                "🔧 Further manual board-level diagnosis required."))

    return log, interpretations

def analyze_logs():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_box.delete("1.0", tk.END)
        result_box.delete("1.0", tk.END)

        result_box.insert(tk.END, "🔌 Pulling panic logs from iPhone...\n")

        if not pull_panic_logs(tmpdir):
            return

        latest_file = get_latest_panic_file(tmpdir)
        if not latest_file:
            result_box.insert(tk.END, "⚠️ No panic-full files found.\n")
            return

        log, results = interpret_panic(latest_file)

        # Display log
        log_box.insert(tk.END, log[:5000])  # prevent overload: only first 5000 chars

        # Display interpretations
        result_box.insert(tk.END, f"📄 Latest log: {os.path.basename(latest_file)}\n\n")
        result_box.insert(tk.END, "=== Interpretation & Repair Suggestion ===\n\n")
        for cause, fix in results:
            result_box.insert(tk.END, cause + "\n" + fix + "\n\n")

# --- GUI ---
root = tk.Tk()
root.title("iDevice Panic Log Analyzer")
root.geometry("900x600")

btn = tk.Button(root, text="🔍 Analyze iPhone Panic Log", command=analyze_logs, bg="#2e86de", fg="white", font=("Arial", 12, "bold"))
btn.pack(pady=10)

frame = tk.Frame(root)
frame.pack(fill="both", expand=True)

# Panic log display
log_label = tk.Label(frame, text="📄 Panic Log (Raw):", font=("Arial", 11, "bold"))
log_label.pack(anchor="w")
log_box = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=15, bg="#f4f6f7")
log_box.pack(fill="both", expand=True, padx=5, pady=5)

# Results display
res_label = tk.Label(frame, text="🛠 Interpretation & Fix:", font=("Arial", 11, "bold"))
res_label.pack(anchor="w")
result_box = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=12, bg="#eaf2f8")
result_box.pack(fill="both", expand=True, padx=5, pady=5)

root.mainloop()
