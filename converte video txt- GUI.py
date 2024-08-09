import os
import json
import wave
import subprocess
import threading
from tkinter import Tk, filedialog, Button, Label, Entry, StringVar, Listbox, Menu, messagebox, DoubleVar
from tkinter.ttk import Progressbar
import vosk

def convert_audio(video_path, audio_path):
    command = [
        'ffmpeg', '-i', video_path, '-ar', '16000', '-ac', '1', audio_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def transcribe_audio(audio_path, model_path, progress_var):
    model = vosk.Model(model_path)
    recognizer = vosk.KaldiRecognizer(model, 16000)

    with wave.open(audio_path, 'rb') as wf:
        frames = wf.getnframes()
        chunk_size = 4000
        num_chunks = frames // chunk_size
        for i in range(num_chunks + 1):
            data = wf.readframes(chunk_size)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                yield json.loads(result)['text']
            progress_var.set((i + 1) / (num_chunks + 1) * 100)
            root.update_idletasks()  # Atualiza a interface gráfica

    final_result = recognizer.FinalResult()
    yield json.loads(final_result)['text']
    progress_var.set(100)
    root.update_idletasks()

def process_videos(video_paths, model_path, output_dir, progress_var):
    for video_path in video_paths:
        audio_path = os.path.join(output_dir, 'temp_audio.wav')
        convert_audio(video_path, audio_path)

        transcript = []
        for text in transcribe_audio(audio_path, model_path, progress_var):
            transcript.append(text)

        os.remove(audio_path)

        output_path = os.path.join(output_dir, os.path.basename(video_path).replace('.mp4', '.txt'))
        with open(output_path, 'w') as f:
            f.write('\n'.join(transcript))

def start_processing():
    video_paths = video_list.get(0, "end")
    model_path = model_var.get()
    output_dir = output_path.get()

    if not video_paths or not model_path or not output_dir:
        messagebox.showwarning("Aviso", "Por favor, preencha todos os campos.")
        return

    progress_var.set(0)  # Reseta a barra de progresso
    def worker():
        try:
            process_videos(video_paths, model_path, output_dir, progress_var)
            messagebox.showinfo("Concluído", "O processamento dos vídeos foi concluído com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

    threading.Thread(target=worker, daemon=True).start()
    messagebox.showinfo("Início", "O processamento dos vídeos foi iniciado.")

def select_videos():
    video_paths = filedialog.askopenfilenames(title="Selecione os vídeos", filetypes=[("Vídeo", "*.mp4")])
    if video_paths:
        for path in video_paths:
            video_list.insert("end", path)

def select_model():
    model_path = filedialog.askdirectory(title="Selecione o diretório do modelo")
    if model_path:
        model_var.set(model_path)

def select_output_dir():
    output_dir = filedialog.askdirectory(title="Selecione o diretório de saída")
    if output_dir:
        output_path.set(output_dir)

def clear_videos():
    video_list.delete(0, "end")

def remove_selected_video(event):
    selected = video_list.curselection()
    if selected:
        video_list.delete(selected)

def setup_right_click_menu():
    menu = Menu(root, tearoff=0)
    menu.add_command(label="Remover vídeo selecionado", command=lambda: remove_selected_video(None))
    def show_menu(event):
        menu.post(event.x_root, event.y_root)
    video_list.bind("<Button-3>", show_menu)

def main():
    global video_list, model_var, output_path, progress_var, root

    root = Tk()
    root.title("Conversor de Vídeo para Texto")

    # Botão "Selecionar vídeos"
    Button(root, text="Selecionar vídeos", command=select_videos).pack(pady=5)
    
    # Lista de vídeos selecionados
    video_list = Listbox(root, selectmode="multiple", width=50, height=10)
    video_list.pack(pady=5)

    # Configura menu de clique direito
    setup_right_click_menu()

    # Botão "Selecionar modelo"
    Label(root, text="Selecionar diretório do modelo:").pack(pady=5)
    model_var = StringVar()
    Entry(root, textvariable=model_var, state='readonly').pack(pady=5)
    Button(root, text="Selecionar pasta do modelo", command=select_model).pack(pady=5)

    # Campo "Caminho de saída"
    Label(root, text="Caminho de saída:").pack(pady=5)
    output_path = StringVar()
    Entry(root, textvariable=output_path).pack(pady=5)
    Button(root, text="Selecionar pasta de saída", command=select_output_dir).pack(pady=5)

    # Botão "Limpar Vídeos"
    Button(root, text="Limpar vídeos selecionados", command=clear_videos).pack(pady=5)

    # Barra de progresso
    progress_var = DoubleVar()
    progress = Progressbar(root, orient="horizontal", length=400, mode="determinate", variable=progress_var)
    progress.pack(pady=10)

    # Botão "Executar"
    Button(root, text="Executar", command=start_processing).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
