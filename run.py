# Import library dan module yang diperlukan
import openai
import winsound
import sys
import time
import pyaudio
import keyboard
import wave
import json
from component.translate import *
from component.TTS import *
from component.subtitle import *
from component.promptMaker import *
import os

# Mengatur sys.stdout agar dapat menulis karakter unicode ke terminal
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

# Menggunakan kunci API OpenAI, pastikan untuk mengganti dengan kunci API yang valid
openai.api_key = "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"

# Inisialisasi variabel dan list
conversation = []
history = {"history": conversation}
mode = 0
total_characters = 0
chat = ""
chat_now = ""
chat_prev = ""
is_Speaking = False
owner_name = "Dhavin"
blacklist = ["Nightbot", "streamelements"]

# Fungsi untuk memilih mesin TTS
def choose_tts_engine():
    print("Choose TTS Engine:")
    print("1. Voicevox (Japanese)")
    print("2. Silero TTS (English)")

    user_choice = input("Enter your choice (1-2): ")

    if user_choice == "1":
        return "voicevox"
    elif user_choice == "2":
        return "silero_en"
    else:
        print("Invalid choice. Defaulting to Voicevox.")
        return "voicevox"

# Memilih mesin TTS
selected_tts_engine = choose_tts_engine()


# Fungsi untuk merekam audio pengguna
def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    WAVE_OUTPUT_FILENAME = "input.wav"
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    print("Recording...")
    while keyboard.is_pressed('RIGHT_SHIFT'):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Stopped recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    transcribe_audio("input.wav")

# Fungsi untuk mentranskripsi audio pengguna
def transcribe_audio(file):
    global chat_now
    audio_file = open(file, "rb")
    # Transkripsi audio ke dalam bahasa yang terdeteksi
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    chat_now = transcript.text
    print("Question: " + chat_now)
    result = owner_name + " said " + chat_now
    conversation.append({'role': 'user', 'content': result})
    openai_answer()

# Fungsi untuk mendapatkan jawaban dari OpenAI
def openai_answer():
    global total_characters, conversation, chat_now, chat
    total_characters = sum(len(d['content']) for d in conversation)

    # Memastikan total karakter tidak melebihi batas yang ditetapkan
    while total_characters > 4000:
        try:
            conversation.pop(2)
            total_characters = sum(len(d['content']) for d in conversation)
        except Exception as e:
            print("Error removing old messages: {0}".format(e))

    # Menulis data pesan ke file JSON
    with open("conversation.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

    # Mendapatkan prompt untuk digunakan pada OpenAI
    prompt = getPrompt()

    # Mendapatkan jawaban dari OpenAI menggunakan model gpt-3.5-turbo
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt,
        max_tokens=400,
        temperature=1,
        top_p=0.9
    )
    message = response['choices'][0]['message']['content']
    conversation.append({'role': 'assistant', 'content': message})

    # Menerjemahkan dan menyintesis suara jawaban
    translate_text(message)
    
    # Mengecek apakah pengguna meminta untuk membuka aplikasi
    open_application(chat_now)

# Fungsi untuk menerjemahkan teks dan menyintesis suara
def translate_text(text):
    global is_Speaking

    # Deteksi bahasa teks
    detect = detect_google(text)

    # Menerjemahkan teks ke bahasa tertentu
    tts = translate_google(text, f"{detect}", "JA")
    tts_en = translate_google(text, f"{detect}", "EN")

    try:
        if tts is not None and tts_en is not None:
            print("JP Answer: " + tts)
            print("EN Answer: " + tts_en)
    except Exception as e:
        print(f"Error printing text: {e}")

    # Memilih mesin TTS yang tersedia
    if selected_tts_engine == "voicevox":
        voicevox_tts(tts)
    elif selected_tts_engine == "silero_en":
        silero_tts(tts_en, "en", "v3_en", "en_21")

    # Memainkan suara
    is_Speaking = True
    winsound.PlaySound("test.wav", winsound.SND_FILENAME)
    is_Speaking = False

    # Menghapus file teks setelah suara selesai diputar
    time.sleep(1)
    with open("output.txt", "w") as f:
        f.truncate(0)
    with open("chat.txt", "w") as f:
        f.truncate(0)


# Fungsi untuk persiapan dan menjalankan loop utama
def preparation():
    global conversation, chat_now, chat, chat_prev
    while True:
        # Jika asisten tidak sedang berbicara dan chat tidak kosong, dan chat tidak sama dengan chat sebelumnya
        chat_now = chat
        if is_Speaking == False and chat_now != chat_prev:
            # Menyimpan sejarah percakapan
            conversation.append({'role': 'user', 'content': chat_now})
            chat_prev = chat_now
            openai_answer()
        time.sleep(1)
        
# Fungsi untuk membuka aplikasi berdasarkan perintah pengguna
def open_application(command):
    if "buka steam" in command.lower():
        os.system("start D:\Steam\steam.exe")
    elif "buka musik" in command.lower():
        os.system('start "" "C:\\Users\\fasuyaaa\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Brave Apps\\YouTube Music.lnk"')

# Program utama
if __name__ == "__main__":
    try:
        print("Press and Hold Right Shift to record audio")
        while True:
            if keyboard.is_pressed('RIGHT_SHIFT'):
                record_audio()
    except KeyboardInterrupt:
        print("Stopped")