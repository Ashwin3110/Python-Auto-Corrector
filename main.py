from pynput import keyboard
from pynput.keyboard import Key, Controller
import pyperclip
import httpx
from string import Template
import time

class TypeCorrector:
    def __init__(self):
        self.controller = Controller()
        self.OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
        self.OLLAMA_CONFIG = {
            "model": "llama3.2",
            "keep_alive": "5m",
            "stream": False
        }
        self.PROMPT_TEMPLATE = Template(
            """Fix all typos and casing and punctuation in this text, but preserve all new line characters:

            $text

            Return only the corrected text, don't include a preamble.
            """
        )

    def fix(self, text):
        prompt = self.PROMPT_TEMPLATE.substitute(text=text)
        response = httpx.post(self.OLLAMA_ENDPOINT,
                              json={"prompt": prompt, **self.OLLAMA_CONFIG},
                              headers={"Content-Type": "application/json"},
                              timeout=10
                              )
        if response.status_code != 200:
            return "API Failure"
        return response.json()['response'].strip()

    def fix_current_sentence(self):
        # Move cursor to the start of the sentence (simulate many Ctrl+Left)
        for _ in range(20):
            with self.controller.pressed(Key.ctrl):
                self.controller.tap(Key.left)
        # Now select to the end of the sentence (simulate many Ctrl+Shift+Right)
        with self.controller.pressed(Key.shift):
            for _ in range(40):
                with self.controller.pressed(Key.ctrl):
                    self.controller.tap(Key.right)
        self.fix_selection()

    def fix_selection(self):
        # Step 1: Copy the selected text
        prev_clip = pyperclip.paste()
        print("prev_clip :", prev_clip)
        with self.controller.pressed(Key.ctrl):
            self.controller.tap('c')

        # Step 2: Wait for clipboard to update (max 1s)
        timeout = time.time() + 1.0
        while True:
            text = pyperclip.paste()
            if text != prev_clip or time.time() > timeout:
                break
            time.sleep(0.05)
        print("text :", text)

        # Step 3: Fix the text
        fixed_text = self.fix(text)

        # Step 4: Copy back to clipboard
        pyperclip.copy(fixed_text)
        time.sleep(0.1)

        # Step 5: Replace the selected text
        with self.controller.pressed(Key.ctrl):
            self.controller.tap('v')

    def on_f9(self):
        self.fix_current_sentence()

    def on_f10(self):
        self.fix_selection()

def main():
    corrector = TypeCorrector()
    with keyboard.GlobalHotKeys({
        '<120>': corrector.on_f9,
        '<121>': corrector.on_f10,
    }) as h:
        h.join()

if __name__ == "__main__":
    main()