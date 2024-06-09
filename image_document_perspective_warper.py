import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps
import numpy as np
import cv2

class ImageEditor:
    def __init__(self, root):
        """
        Inicializa la interfaz gráfica y los componentes del editor de imágenes.
        
        # Args:
        - root (Tk): La ventana principal de la aplicación.
        """
        self.root = root
        self.root.title("Editor de Imágenes")
        self.root.geometry("1200x800")

        # Configuración de estilo para ttk
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Helvetica", 10), padding=5)
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 12))

        # Inicialización de variables
        self.image_paths = []
        self.images = []
        self.current_image_index = -1
        self.image = None
        self.tk_image = None
        self.history = []
        self.points = []
        self.point_handles = []
        self.line_handles = []
        self.selected_point_index = None

        # Configuración del marco principal
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

        # Configuración del canvas para mostrar la imagen
        self.canvas = tk.Canvas(self.main_frame, background="white")
        self.canvas.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Configuración del marco lateral
        self.side_frame = ttk.Frame(root, width=300)
        self.side_frame.pack(fill=tk.Y, side=tk.RIGHT, padx=10, pady=10)

        # Botones de la interfaz
        self.load_button = ttk.Button(self.side_frame, text="Cargar Imágenes", command=self.load_images)
        self.load_button.pack(pady=5)

        self.rotate_button = ttk.Button(self.side_frame, text="Rotar 90°", command=self.rotate_image)
        self.rotate_button.pack(pady=5)

        self.confirm_button = ttk.Button(self.side_frame, text="Confirmar Puntos", command=self.warp_image, state=tk.DISABLED)
        self.confirm_button.pack(pady=5)

        self.save_folder_1_button = ttk.Button(self.side_frame, text="Guardar en FRONTAL", command=lambda: self.save_image("FRONTAL"))
        self.save_folder_1_button.pack(pady=5)

        self.save_folder_2_button = ttk.Button(self.side_frame, text="Guardar en TRASERAS", command=lambda: self.save_image("TRASERAS"))
        self.save_folder_2_button.pack(pady=5)

        # Frame para navegación y previsualizaciones
        self.nav_frame = ttk.Frame(self.side_frame)
        self.nav_frame.pack(fill=tk.X, padx=10, pady=10)

        # Botones y etiquetas de previsualización de imágenes
        self.prev_button = ttk.Button(self.nav_frame, text="←", command=self.show_prev_image, state=tk.DISABLED, width=2)
        self.prev_button.grid(row=0, column=0, padx=5)

        self.prev_image_label = ttk.Label(self.nav_frame)
        self.prev_image_label.grid(row=0, column=1, padx=5)

        self.current_image_label = ttk.Label(self.nav_frame, borderwidth=2, relief="solid")
        self.current_image_label.grid(row=0, column=2, padx=5)

        self.next_image_label = ttk.Label(self.nav_frame)
        self.next_image_label.grid(row=0, column=3, padx=5)

        self.next_button = ttk.Button(self.nav_frame, text="→", command=self.show_next_image, state=tk.DISABLED, width=2)
        self.next_button.grid(row=0, column=4, padx=5)

        self.index_label = ttk.Label(self.side_frame, text="")
        self.index_label.pack(pady=5)

        # Configuración para arrastrar y soltar archivos
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop)

        # Vinculación de teclas y eventos del ratón
        self.root.bind("<Control-z>", self.undo)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Configure>", self.on_resize)

    def load_images(self):
        """
        Abre un cuadro de diálogo para seleccionar múltiples imágenes y las carga en el editor.
        """
        self.image_paths = filedialog.askopenfilenames()
        if self.image_paths:
            self.images = [self.scale_image(Image.open(path)) for path in self.image_paths]
            self.current_image_index = 0
            self.history = [self.images[0].copy()]
            self.adjust_canvas_size(self.images[0])
            self.display_image(self.images[0])
            self.update_navigation_buttons()
            self.update_previews()
            self.update_index_label()

    def drop(self, event):
        """
        Carga imágenes arrastradas y soltadas en el editor.

        # Args:
        - event (Event): El evento de arrastrar y soltar.
        """
        self.image_paths = self.root.tk.splitlist(event.data)
        if self.image_paths:
            self.images = [self.scale_image(Image.open(path)) for path in self.image_paths]
            self.current_image_index = 0
            self.history = [self.images[0].copy()]
            self.adjust_canvas_size(self.images[0])
            self.display_image(self.images[0])
            self.update_navigation_buttons()
            self.update_previews()
            self.update_index_label()

    def update_navigation_buttons(self):
        """
        Actualiza el estado de los botones de navegación (previo y siguiente).
        """
        self.prev_button.config(state=tk.NORMAL if self.current_image_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_image_index < len(self.images) - 1 else tk.DISABLED)

    def show_prev_image(self):
        """
        Muestra la imagen anterior en la lista de imágenes cargadas.
        """
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.history = [self.images[self.current_image_index].copy()]
            self.adjust_canvas_size(self.images[self.current_image_index])
            self.display_image(self.images[self.current_image_index])
            self.update_navigation_buttons()
            self.update_previews()
            self.update_index_label()

    def show_next_image(self):
        """
        Muestra la siguiente imagen en la lista de imágenes cargadas.
        """
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.history = [self.images[self.current_image_index].copy()]
            self.adjust_canvas_size(self.images[self.current_image_index])
            self.display_image(self.images[self.current_image_index])
            self.update_navigation_buttons()
            self.update_previews()
            self.update_index_label()

    def update_previews(self):
        """
        Actualiza las previsualizaciones de las imágenes (anterior, actual y siguiente).
        """
        self.update_preview(self.prev_image_label, self.current_image_index - 1)
        self.update_preview(self.current_image_label, self.current_image_index, highlight=True)
        self.update_preview(self.next_image_label, self.current_image_index + 1)

    def update_preview(self, label, index, highlight=False):
        """
        Actualiza la previsualización de una imagen específica.

        # Args:
        - label (ttk.Label): La etiqueta donde se mostrará la previsualización.
        - index (int): El índice de la imagen en la lista de imágenes.
        - highlight (bool): Indica si la imagen debe resaltarse.
        """
        if 0 <= index < len(self.images):
            preview_image = self.images[index].copy()
            preview_image = self.crop_to_square(preview_image)
            preview_image.thumbnail((50, 50))
            tk_preview_image = ImageTk.PhotoImage(preview_image)
            label.config(image=tk_preview_image)
            label.image = tk_preview_image
            if highlight:
                label.config(borderwidth=2, relief="solid")
            else:
                label.config(borderwidth=0, relief="flat")
        else:
            label.config(image='', borderwidth=0, relief="flat")

    def update_index_label(self):
        """
        Actualiza el índice de la imagen actual y el total de imágenes cargadas.
        """
        if len(self.images) > 0:
            self.index_label.config(text=f"{self.current_image_index + 1}/{len(self.images)}")
        else:
            self.index_label.config(text="")

    def crop_to_square(self, image):
        """
        Recorta una imagen para que sea cuadrada.

        # Args:
        - image (Image): La imagen que se va a recortar.

        # Returns:
        - Image: La imagen recortada.
        """
        min_dimension = min(image.width, image.height)
        left = (image.width - min_dimension) / 2
        top = (image.height - min_dimension) / 2
        right = (image.width + min_dimension) / 2
        bottom = (image.height + min_dimension) / 2
        return image.crop((left, top, right, bottom))

    def adjust_canvas_size(self, image):
        """
        Ajusta el tamaño del lienzo para que coincida con el tamaño de la imagen.

        # Args:
        - image (Image): La imagen que se está mostrando.
        """
        self.canvas.config(width=image.width, height=image.height)

    def display_image(self, image):
        """
        Muestra una imagen en el lienzo.

        # Args:
        - image (Image): La imagen que se va a mostrar.
        """
        self.image = image
        self.canvas.delete("all")
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.draw_points_and_lines()

    def scale_image(self, image):
        """
        Escala una imagen si alguna de sus dimensiones excede los 1100 píxeles.

        # Args:
        - image (Image): La imagen que se va a escalar.

        # Returns:
        - Image: La imagen escalada.
        """
        max_dimension = 1100
        if image.width > max_dimension or image.height > max_dimension:
            scale_factor = 0.9
            while image.width * scale_factor > max_dimension or image.height * scale_factor > max_dimension:
                scale_factor *= 0.9
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            image = image.resize((new_width, new_height), Image.LANCZOS)
        return image

    def on_resize(self, event):
        """
        Maneja el evento de redimensionamiento de la ventana.

        # Args:
        - event (Event): El evento de redimensionamiento.
        """
        if self.image:
            self.display_image(self.image)

    def on_button_press(self, event):
        """
        Maneja el evento de presionar el botón del ratón.

        # Args:
        - event (Event): El evento de presionar el botón.
        """
        x, y = event.x, event.y
        if len(self.points) < 4:
            self.points.append((x, y))
            handle = self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill='red')
            self.point_handles.append(handle)
            if len(self.points) == 4:
                self.confirm_button.config(state=tk.NORMAL)
            self.draw_points_and_lines()
        else:
            self.select_point(x, y)

    def on_mouse_drag(self, event):
        """
        Maneja el evento de arrastrar el ratón.

        # Args:
        - event (Event): El evento de arrastrar el ratón.
        """
        if self.selected_point_index is not None:
            x, y = event.x, event.y
            self.points[self.selected_point_index] = (x, y)
            self.canvas.coords(self.point_handles[self.selected_point_index], x - 3, y - 3, x + 3, y + 3)
            self.draw_points_and_lines()

    def on_button_release(self, event):
        """
        Maneja el evento de soltar el botón del ratón.

        # Args:
        - event (Event): El evento de soltar el botón.
        """
        self.selected_point_index = None

    def select_point(self, x, y):
        """
        Selecciona un punto cercano al clic del ratón para moverlo.

        # Args:
        - x (int): La coordenada x del clic.
        - y (int): La coordenada y del clic.
        """
        for i, (px, py) in enumerate(self.points):
            if abs(x - px) < 5 and abs(y - py) < 5:
                self.selected_point_index = i
                break

    def draw_points_and_lines(self):
        """
        Dibuja los puntos y las líneas de conexión en el lienzo.
        """
        for handle in self.line_handles:
            self.canvas.delete(handle)
        self.line_handles.clear()
        if len(self.points) > 1:
            for i in range(len(self.points)):
                j = (i + 1) % len(self.points)
                line = self.canvas.create_line(self.points[i][0], self.points[i][1], self.points[j][0], self.points[j][1], fill='blue')
                self.line_handles.append(line)

    def order_points(self, points):
        """
        Ordena los puntos para formar un rectángulo.

        El algoritmo encuentra el punto superior izquierdo, superior derecho,
        inferior derecho e inferior izquierdo basado en las sumas y diferencias
        de las coordenadas.

        # Args:
        - points (list): Lista de puntos (x, y).

        # Returns:
        - np.ndarray: Puntos ordenados.
        """
        points = np.array(points)
        rect = np.zeros((4, 2), dtype="float32")

        # La suma de las coordenadas x e y encuentra los puntos top-left (mínimo)
        # y bottom-right (máximo).
        s = points.sum(axis=1)
        rect[0] = points[np.argmin(s)]
        rect[2] = points[np.argmax(s)]

        # La diferencia entre las coordenadas x e y encuentra los puntos top-right (mínimo)
        # y bottom-left (máximo).
        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)]
        rect[3] = points[np.argmax(diff)]

        return rect

    def warp_image(self):
        """
        Aplica una transformación de perspectiva a la imagen basada en los puntos seleccionados.

        Utiliza los puntos seleccionados para calcular una transformación de perspectiva (matriz de transformación).
        Luego, aplica esta transformación a la imagen original para obtener una vista corregida de la misma,
        simulando un escaneo.
        """
        points = self.points
        ordered_points = self.order_points(points)

        (tl, tr, br, bl) = ordered_points
        width_a = np.linalg.norm(br - bl)  # Distancia entre br y bl (ancho abajo)
        width_b = np.linalg.norm(tr - tl)  # Distancia entre tr y tl (ancho arriba)
        max_width = max(int(width_a), int(width_b))  # Máximo ancho

        height_a = np.linalg.norm(tr - br)  # Distancia entre tr y br (altura derecha)
        height_b = np.linalg.norm(tl - bl)  # Distancia entre tl y bl (altura izquierda)
        max_height = max(int(height_a), int(height_b))  # Máxima altura

        # Asegurar que la imagen resultante esté en formato horizontal
        if max_width < max_height:
            max_width, max_height = max_height, max_width

        # Puntos destino para la transformación
        dst_pts = np.array([[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]], dtype="float32")

        # Calcular la matriz de transformación de perspectiva
        M = cv2.getPerspectiveTransform(ordered_points, dst_pts)

        # Aplicar la transformación a la imagen
        warped = cv2.warpPerspective(np.array(self.image), M, (max_width, max_height))
        
        self.image = Image.fromarray(warped)
        self.images[self.current_image_index] = self.image
        self.history.append(self.image.copy())
        self.points = []
        self.point_handles = []
        self.line_handles = []
        self.confirm_button.config(state=tk.DISABLED)
        self.image = self.scale_image(self.image)
        self.adjust_canvas_size(self.image)
        self.display_image(self.image)
        self.update_previews()
        self.update_index_label()

    def rotate_image(self):
        """
        Rota la imagen 90 grados en sentido horario.
        """
        if self.image:
            self.history.append(self.image.copy())
            self.image = self.image.rotate(90, expand=True)
            self.images[self.current_image_index] = self.image
            self.image = self.scale_image(self.image)
            self.adjust_canvas_size(self.image)
            self.display_image(self.image)
            self.update_previews()
            self.update_index_label()

    def undo(self, event):
        """
        Deshace la última acción realizada en la imagen.

        # Args:
        - event (Event): El evento de deshacer.
        """
        if len(self.history) > 1:
            self.history.pop()
            self.image = self.history[-1].copy()
            self.images[self.current_image_index] = self.image
            self.adjust_canvas_size(self.image)
            self.display_image(self.image)
            self.update_previews()
            self.update_index_label()

    def save_image(self, folder):
        """
        Guarda la imagen actual en el folder especificado.

        # Args:
        - folder (str): La carpeta donde se guardará la imagen.
        """
        if self.image and self.image_paths:
            filename = self.image_paths[self.current_image_index].split("/")[-1]
            save_path = f"{folder}/{filename}"
            if self.image.mode == 'RGBA':
                self.image = self.image.convert('RGB')
            self.image.save(save_path)
            print(f"Imagen guardada en {save_path}")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageEditor(root)
    root.mainloop()
