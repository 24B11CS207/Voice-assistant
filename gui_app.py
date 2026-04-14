"""Tkinter GUI for the personal voice assistant."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog

from assistant_core import VoiceAssistant


class AssistantGUI:
    """Simple desktop interface for the voice assistant."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Personal Voice Assistant")
        self.root.geometry("720x520")
        self.root.minsize(640, 460)

        self.assistant = VoiceAssistant()
        self.listening = False
        self.listen_thread: threading.Thread | None = None

        self._build_interface()
        self._log("Assistant ready. Use the text box or click Start Listening.")

    def _build_interface(self) -> None:
        header = tk.Label(
            self.root,
            text="Personal Voice Assistant",
            font=("Segoe UI", 20, "bold"),
            pady=12,
        )
        header.pack()

        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=18, font=("Segoe UI", 10))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))
        self.log_area.configure(state=tk.DISABLED)

        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        self.command_entry = tk.Entry(input_frame, font=("Segoe UI", 11))
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.command_entry.bind("<Return>", lambda _event: self.handle_text_command())

        send_button = tk.Button(input_frame, text="Send", command=self.handle_text_command, width=10)
        send_button.pack(side=tk.LEFT, padx=(8, 0))

        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

        self.listen_button = tk.Button(button_frame, text="Start Listening", command=self.toggle_listening)
        self.listen_button.pack(side=tk.LEFT)

        clear_button = tk.Button(button_frame, text="Clear Chat", command=self.clear_chat)
        clear_button.pack(side=tk.LEFT, padx=8)

        threshold_button = tk.Button(button_frame, text="Mic Sensitivity", command=self.set_threshold)
        threshold_button.pack(side=tk.LEFT)

    def _log(self, message: str) -> None:
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state=tk.DISABLED)

    def clear_chat(self) -> None:
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete("1.0", tk.END)
        self.log_area.configure(state=tk.DISABLED)

    def handle_text_command(self) -> None:
        command = self.command_entry.get().strip()
        if not command:
            return

        self.command_entry.delete(0, tk.END)
        self._process_command(command)

    def toggle_listening(self) -> None:
        if self.listening:
            self.listening = False
            self.listen_button.configure(text="Start Listening")
            self._log("Assistant stopped listening.")
            return

        if self.assistant.recognizer is None:
            messagebox.showwarning(
                "Voice Input Unavailable",
                "SpeechRecognition is not installed.",
            )
            return

        try:
            self.assistant.calibrate_microphone()
        except RuntimeError as exc:
            messagebox.showerror("Microphone Error", str(exc))
            return

        self.listening = True
        self.listen_button.configure(text="Stop Listening")
        self._log("Assistant is now listening.")

        if self.listen_thread is None or not self.listen_thread.is_alive():
            self.listen_thread = threading.Thread(target=self._listen_in_background, daemon=True)
            self.listen_thread.start()

    def set_threshold(self) -> None:
        value = simpledialog.askinteger(
            "Mic Sensitivity",
            "Enter a sensitivity value (example: 300):",
            initialvalue=self.assistant.threshold,
            minvalue=50,
            maxvalue=5000,
        )
        if value is None:
            return

        self.assistant.threshold = value
        if self.assistant.recognizer is not None:
            self.assistant.recognizer.energy_threshold = value
        self._log(f"Microphone sensitivity set to {value}.")

    def _listen_in_background(self) -> None:
        while self.listening:
            try:
                command = self.assistant.listen()
            except RuntimeError as exc:
                self.root.after(0, lambda error=str(exc): self._handle_listen_error(error))
                break

            if not self.listening:
                break

            if not command:
                self.root.after(0, self._speak_message, "I did not catch that. Please try again.")
                continue

            response = self.assistant.process_command(command)

            self.root.after(0, self._deliver_turn, command, response)

    def _process_command(self, command: str) -> None:
        response = self.assistant.process_command(command)
        self._deliver_turn(command, response)

        if response.should_exit:
            self.listening = False
            self.root.after(0, self.root.destroy)

    def _deliver_turn(self, command: str, response) -> None:
        self._log_turn(command, response.text)
        self._speak_message(response.text)

        if response.should_exit:
            self.listening = False
            self._reset_listening_state()
            self.root.after(0, self.root.destroy)

    def _speak_message(self, message: str) -> None:
        self.assistant.speak(message)

    def _log_turn(self, command: str, response_text: str) -> None:
        self._log(f"You: {command}")
        self._log(f"Assistant: {response_text}")

    def _reset_listening_state(self) -> None:
        self.listen_button.configure(text="Start Listening")

    def _handle_listen_error(self, error: str) -> None:
        self.listening = False
        self._reset_listening_state()
        messagebox.showerror("Microphone Error", error)


def main() -> None:
    root = tk.Tk()
    AssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
