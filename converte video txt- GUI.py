import os
import subprocess
import vosk
import json
import wave
from tqdm import tqdm
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory, asksaveasfilename
from tkinter import Label, Button, Entry


def convert_audio_to_wav(video_path):
    dir_path = os.path.dirname(video_path)
    audio_path = os.path.join(dir_path, 'temp_audio.wav')
    command = [
        'ffmpeg',
        '-y',
        '-i', video_path,
        '-ar', '16000',
        '-ac', '1',
        audio_path
    ]
    subprocess.run(command, check=True)
    return audio_path


def transcribe_audio(audio_path, model_path):
    model = vosk.Model(model_path)
    recognizer = vosk.KaldiRecognizer(model, 16000)
    
    with wave.open(audio_path, 'rb') as wf:
        total_frames = wf.getnframes()
    
    results = []
    with wave.open(audio_path, 'rb') as wf:
        with tqdm(total=total_frames, unit='frames') as pbar:
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    result = recognizer.Result()
                    results.append(result)
                pbar.update(len(data))
            final_result = recognizer.FinalResult()
            results.append(final_result)
            pbar.update(len(data))
    
    transcript = '\n'.join(result['text'] for result in (json.loads(r) for r in results))
    return transcript


def main():
    def select_video_file():
        video_path = askopenfilename(title='Selecione o arquivo de vídeo', filetypes=[('Arquivos de vídeo', '*.mp4')])
        if video_path:
            video_entry.delete(0, 'end')
            video_entry.insert(0, video_path)

    def select_model_path():
        model_path = askdirectory(title='Selecione a pasta do modelo Vosk')
        if model_path:
            model_entry.delete(0, 'end')
            model_entry.insert(0, model_path)

    def save_transcription():
        video_path = video_entry.get()
        model_path = model_entry.get()
        txt_path = asksaveasfilename(title='Salvar transcrição', defaultextension='.txt', filetypes=[('Arquivo de Texto', '*.txt')])
        
        if video_path and model_path and txt_path:
            audio_path = convert_audio_to_wav(video_path)
            transcript = transcribe_audio(audio_path, model_path)
            
            with open(txt_path, 'w') as f:
                f.write(transcript)
            
            os.remove(audio_path)
            print("Transcrição salva com sucesso!")

    root = Tk()
    root.title("Transcrição de Vídeo")

    Label(root, text="Caminho do Vídeo:").grid(row=0, column=0, padx=10, pady=10)
    video_entry = Entry(root, width=50)
    video_entry.grid(row=0, column=1, padx=10, pady=10)
    Button(root, text="Selecionar Vídeo", command=select_video_file).grid(row=0, column=2, padx=10, pady=10)

    Label(root, text="Caminho do Modelo:").grid(row=1, column=0, padx=10, pady=10)
    model_entry = Entry(root, width=50)
    model_entry.grid(row=1, column=1, padx=10, pady=10)
    Button(root, text="Selecionar Modelo", command=select_model_path).grid(row=1, column=2, padx=10, pady=10)

    Button(root, text="Salvar Transcrição", command=save_transcription).grid(row=2, column=1, padx=10, pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
