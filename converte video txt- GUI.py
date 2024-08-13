import os
import json
import wave
import subprocess
import threading
from tkinter import Tk, filedialog, Button, Label, Entry, StringVar, Listbox, Menu, messagebox, DoubleVar, Scrollbar
from tkinter.ttk import Progressbar, Treeview
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
    for index, video_path in enumerate(video_paths):
        audio_path = os.path.join(output_dir, 'temp_audio.wav')
        video_name = os.path.basename(video_path)
        update_status(index, "Processando")

        convert_audio(video_path, audio_path)

        transcript = []
        for text in transcribe_audio(audio_path, model_path, progress_var):
            transcript.append(text)

        os.remove(audio_path)

        output_path = os.path.join(output_dir, video_name.replace('.mp4', '.txt'))
        with open(output_path, 'w') as f:
            f.write('\n'.join(transcript))

        update_status(index, "Concluído")

def update_status(index, status):
    for item in video_list.get_children():
        if video_list.item(item, 'values')[2] == index:
            video_list.item(item, values=(video_list.item(item, 'values')[0], status, index))
            break

def start_processing():
    video_paths = [video_list.item(item, 'values')[0] for item in video_list.get_children()]
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
        for index, path in enumerate(video_paths):
            video_list.insert("", "end", values=(path, "Não Processado", index))

def select_model():
    model_path = filedialog.askdirectory(title="Selecione o diretório do modelo")
    if model_path:
        model_var.set(model_path)

def select_output_dir():
    output_dir = filedialog.askdirectory(title="Selecione o diretório de saída")
    if output_dir:
        output_path.set(output_dir)

def clear_list():
    video_list.delete(*video_list.get_children())

def remove_selected_video():
    selected_items = video_list.selection()
    for item in selected_items:
        video_list.delete(item)

def setup_right_click_menu():
    menu = Menu(root, tearoff=0)
    menu.add_command(label="Remover vídeo selecionado", command=remove_selected_video)
    def show_menu(event):
        menu.post(event.x_root, event.y_root)
    video_list.bind("<Button-3>", show_menu)

def main():
    global video_list, model_var, output_path, progress_var, root

    root = Tk()
    root.title("Conversor de Vídeo para Texto")

    # Botão "Selecionar vídeos"
    Button(root, text="Selecionar vídeos", command=select_videos).pack(pady=5)

    # Configura lista de vídeos com colunas
    video_list = Treeview(root, columns=("Caminho", "Status", "Índice"), show='headings', selectmode="none")
    video_list.heading("Caminho", text="Caminho")
    video_list.heading("Status", text="Status")
    video_list.heading("Índice", text="Índice")
    video_list.pack(pady=5, fill='both', expand=True)

    # Barra de rolagem
    scrollbar = Scrollbar(root, orient="vertical", command=video_list.yview)
    scrollbar.pack(side='right', fill='y')
    video_list.configure(yscrollcommand=scrollbar.set)

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

    # Botão "Limpar lista"
    Button(root, text="Limpar lista", command=clear_list).pack(pady=5)

    # Barra de progresso
    progress_var = DoubleVar()
    progress = Progressbar(root, orient="horizontal", length=400, mode="determinate", variable=progress_var)
    progress.pack(pady=10)

    # Botão "Executar"
    Button(root, text="Executar", command=start_processing).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
