#---------------------------------------------------------------------------//
# SCSV3213 - Fundemental of Image Processing                                //
# Assignment: 1 - Arithmetic and Logic Operation for Image Manipulation     //
# Section: 02                                                               //
# Semester: 2025/2026                                                       //
# Lecturer's Name: Dr. Md Sah Bin Hj Salam                                  //
# Group Members:                                                            //
# 1. Erika binti Hawapi - A23CS0076                                         //
# 2. Loh Hui Yi - A23CS0106                                                  //
# 3. Nur Farhanah Husni Binti Nor Faizal - A23CS0155                        //
#---------------------------------------------------------------------------//

import customtkinter as ctk
from tkinter import filedialog, messagebox # Tkinter for GUI
from PIL import Image # Image processing library
import numpy as np # NumPy for numerical operations
import cv2 as cv # OpenCV library for image processing
import copy

#----------------------------- Theme Setup -----------------------------------//
ctk.set_appearance_mode("Dark") # Set appearance to dark mode
ctk.set_default_color_theme("dark-blue") # Default color theme
#-----------------------------------------------------------------------------//

#--------------------------------------------- Layer Class ---------------------------------------------//
class Layer:
    def __init__(self, name, image):
        self.name = name
        self.original_image = image.copy()
        self.image = image.copy()
        
        self.opacity = 100 # Layer transparency
        self.visible = True 
        self.position = [0, 0] # Layer position coordinates
        self.scale = 1.0 # Scaling factor
        self.x_offset = 0
        self.y_offset = 0
        
        self.mask = None
        
    def apply_cutout(self, mask):
        if len(self.original_image.shape) == 3:
            if self.original_image.shape[2] == 3:
                self.original_image = cv.cvtColor(self.original_image, cv.COLOR_RGB2RGBA)
                self.image = cv.cvtColor(self.image, cv.COLOR_RGB2RGBA)
            
            if mask.shape[:2] != self.original_image.shape[:2]:
                mask = cv.resize(mask, (self.original_image.shape[1], self.original_image.shape[0]))
            
            self.original_image[:, :, 3] = mask
            self.image[:, :, 3] = mask
            self.mask = mask
        
    def get_preview(self, size=(40, 40)):
        if self.image is None:
            return None
            
        h, w = self.image.shape[:2]
        scale = min(size[0] / w, size[1] / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        if new_w > 0 and new_h > 0:
            resized = cv.resize(self.image, (new_w, new_h))
            return Image.fromarray(resized)
        return None
    
    def get_transformed_image(self, base_width, base_height):
        if self.image is None:
            return None
            
        h, w = self.image.shape[:2] # Original dimension
        new_w = int(w * self.scale) # Width
        new_h = int(h * self.scale) # Height
        
        if new_w > 0 and new_h > 0:
            resized = cv.resize(self.image, (new_w, new_h))
            return resized
        return self.image
#-------------------------------------------------------------------------------------------------------//

#------------------------------------------------- Main Class -------------------------------------------------//
class PhotoEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__() # Parent class

        self.title("Pixieboo") # Window title
        self.geometry("1100x700") # Window dimension
        self.minsize(900, 600) #  Min window size

        self.image = None 
        self.history = []
        self.history_index = -1
        
        self.layers = [] # List of layer objects
        self.selected_layer_index = -1  # Index current selected layer
        self.editing_layer_index = -1  # Index current edited layer
        self.dragging = False
        self.last_mouse_pos = None
        self.resizing = False # Store last mouse position
        
        self.ov_rect = (0, 0, 0, 0) # Overlay rectangle coordinate
        self.handle_size = 20
        
        self.floating_layer_panel = None
        self.layer_panel_visible = False
        
        self.floating_layer_controls_panel = None
        self.layer_controls_panel_visible = False

        self.current_noise_pattern = None  # Store current noise pattern

        try: # Arithemetic topic implementation (Addition of another image for vignette effect)
            self.vignette_img = cv.imread('ImageBlurV2.jpg') 
            if self.vignette_img is not None:
                self.vignette_img = cv.cvtColor(self.vignette_img, cv.COLOR_BGR2RGB)
                print("Vignette image loaded successfully") # Print successfull message
            else:
                print("Warning: Could not load ImageBlurV2.jpg") # Print error load image message
                self.vignette_img = None
        except Exception as e:
            print(f"Error loading vignette image: {e}")
            self.vignette_img = None

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        self.show_upload_page()
#-----------------------------------------------------------------------------------------------------------------//

#------------------------------------- Function to Remove Widgets---------------------------------------//
    def clear_container(self): 
        for widget in self.container.winfo_children():
            widget.destroy() # Remove all widgets from container
#-------------------------------------------------------------------------------------------------------//

#--------------------------------------------------------------- Function to Upload Page ----------------------------------------------------------------------//
    def show_upload_page(self):
        self.clear_container() # Clear existing content

        page = ctk.CTkFrame(self.container)
        page.pack(fill="both", expand=True)

        logo = Image.open("logo.ico") # Load and display logo
        self.logo_ctk = ctk.CTkImage(light_image=logo, dark_image=logo, size=(150, 120))
        
        logo_label = ctk.CTkLabel(page, image=self.logo_ctk,text="")
        logo_label.pack(pady=(170, 10))

        title = ctk.CTkLabel(page, text="Pixieboo", font=("Segoe UI", 40, "bold")) # Application title
        title.pack(pady = 10)

        upload_button = ctk.CTkButton(page, text="Upload Image", width=150, height=40, font=("Segoe UI", 18), command=self.open_image) # Upload button
        upload_button.pack(pady=10)
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------//

#---------------------------------------------------------------------- Function to Load Image ---------------------------------------------------------------------//
    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]) # Open file dialog for image selection
        if file_path: 
            img = cv.imread(file_path) # Read image
            img = cv.cvtColor(img, cv.COLOR_BGR2RGB) # Convert BGR to RGB

            self.image = img # Initialize image and history
            self.history = [img.copy()]
            self.history_index = 0
            
            base_layer = Layer("Background", img) # Create base layer
            self.layers = [base_layer]
            self.selected_layer_index = 0
            self.editing_layer_index = -1 

            self.show_editor_page() # Switch to editor interface
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------//

#---------------------------------------------------------------------- Function to Editor Page --------------------------------------------------------------------//
    def show_editor_page(self):
        self.clear_container()

        top_bar = ctk.CTkFrame(self.container, height=50) # Create top bar
        top_bar.pack(fill="x")
        self.top_bar = top_bar

        back_btn = ctk.CTkButton(top_bar, text="Back", width=80, font=("Segoe UI", 14, "bold"), command=self.show_upload_page) # Back button
        back_btn.pack(side="left", padx=15, pady=10)

        center_frame = ctk.CTkFrame(top_bar, fg_color="transparent") # Center fame for undo/redo/reset buttons
        center_frame.pack(side="left", expand=True, fill="both")
        
        button_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        button_frame.pack(expand=True)
        
        undo_btn = ctk.CTkButton(button_frame, text="Undo", width=80, font=("Segoe UI", 14, "bold"), command=self.undo) # Undo control buttons
        redo_btn = ctk.CTkButton(button_frame, text="Redo", width=80, font=("Segoe UI", 14, "bold"), command=self.redo) # Redo control buttons
        reset_btn = ctk.CTkButton(button_frame, text="Reset", width=80, font=("Segoe UI", 14, "bold"), command=self.reset) # Reset control buttons
        
        undo_btn.pack(side="left", padx=(0, 5))
        redo_btn.pack(side="left", padx=5)
        reset_btn.pack(side="left", padx=(5, 0))

        save_btn = ctk.CTkButton(top_bar, text="Save", width=80, font=("Segoe UI", 14, "bold"), command=self.save_image) # Save button
        save_btn.pack(side="right", padx=15, pady=10)

        layer_btn = ctk.CTkButton( # Layers button
        top_bar, 
        text="Layers",
        width=80, 
        font=("Segoe UI", 14, "bold"),
        command=self.toggle_layer_panel # Open layers panel
        )
        layer_btn.pack(side="right", padx=5, pady=10)
        self.layer_toggle_btn = layer_btn

        main = ctk.CTkFrame(self.container) # Main content area
        main.pack(fill="both", expand=True)

        tools = ctk.CTkFrame(main, width=250, fg_color="#1a1a1a") # Tools panel (left side)
        tools.pack(side="left", fill="y", padx=10, pady=10)
        tools.pack_propagate(False) #Prevent frame from shrinking

        ctk.CTkLabel(tools, text="Tools", font=("Segoe UI", 18, "bold"), text_color="white").pack(pady=10) # Tools title
        self.create_crop_section(tools) # Crop section
        self.create_overlay_section(tools) # Overlay section
        self.create_effects_section(tools) # Effects section
        self.create_adjust_section(tools) # Adjust section
        self.tools_var = ctk.StringVar(value="")  

        self.middle_frame = ctk.CTkFrame(main, fg_color="transparent") # For image canvas
        self.middle_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10) 

        self.image_frame = ctk.CTkFrame(self.middle_frame, fg_color="gray10", corner_radius=8) 
        self.image_frame.pack(fill="both", expand=True)
        
        self.image_label = ctk.CTkLabel(self.image_frame, text="")
        self.image_label.place(relx=0.5, rely=0.5, anchor="center") # Make the image center
        
        self.image_label.bind("<ButtonPress-1>", self.start_drag) # Mouse down
        self.image_label.bind("<B1-Motion>", self.drag_overlay) # Mouse drag
        self.image_label.bind("<ButtonRelease-1>", self.stop_drag) # Mouse up
        self.image_label.bind("<MouseWheel>", self.zoom_overlay) # To zoom the overlay image

        self.compose_layers()
        self.update_image_display()
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------//

#--------------------------------------------------------------------------- Fuction to Show Layer Panel -----------------------------------------------------------------------------------//
    def show_layer_controls_panel(self):
        if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists():
            self.floating_layer_controls_panel.lift() # Bring the overlay image infront
            return
        
        self.floating_layer_controls_panel = ctk.CTkToplevel(self) # Create another floating window
        self.floating_layer_controls_panel.title("Layer Controls") # Window title
        self.after(200, lambda: self.floating_layer_controls_panel.iconbitmap("logo.ico") if self.floating_layer_panel.winfo_exists() else None) # Logo
        self.floating_layer_controls_panel.geometry("200x350") # Window size
        self.floating_layer_controls_panel.resizable(False, False)
        self.floating_layer_controls_panel.transient(self)
        self.floating_layer_controls_panel.attributes('-topmost', True)
        
        self.floating_layer_controls_panel.bind('<Button-1>', self.start_move_layer_controls)
        self.floating_layer_controls_panel.bind('<B1-Motion>', self.on_move_layer_controls)
        
        if self.floating_layer_panel and self.floating_layer_panel.winfo_exists():
            x = self.floating_layer_panel.winfo_x() + self.floating_layer_panel.winfo_width() + 10
            y = self.floating_layer_panel.winfo_y()
        else:
            x = self.winfo_x() + self.middle_frame.winfo_x() + 100
            y = self.winfo_y() + 150
            
        self.floating_layer_controls_panel.geometry(f"+{x}+{y}")
        self.floating_layer_controls_panel.protocol("WM_DELETE_WINDOW", self.hide_both_panels) # Handle windo close
        
        self.create_layer_controls_panel_content()
        self.update_layer_controls_panel()
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------//

#------------------------- Function to Hide and Destroy Layer Control Panel ----------------------------//
    def hide_layer_controls_panel(self):
        if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists():
            self.floating_layer_controls_panel.destroy() # Destroy window

        self.floating_layer_controls_panel = None # Clear reference
        self.layer_controls_panel_visible = False # Update visibility state
#-------------------------------------------------------------------------------------------------------//

#----------------------------------------------------- Function to Create Content of Layer Control Panel -----------------------------------------------------------//
    def create_layer_controls_panel_content(self):
        if not self.floating_layer_controls_panel:
            return
        
        for widget in self.floating_layer_controls_panel.winfo_children():
            widget.destroy()
        
        container = ctk.CTkFrame(self.floating_layer_controls_panel) # Main container
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        drag_handle = ctk.CTkFrame(container, height=30, fg_color="#2a2a2a") # Handle moving window
        drag_handle.pack(fill="x", pady=(0, 10))
        drag_handle.bind('<Button-1>', self.start_move_layer_controls)
        drag_handle.bind('<B1-Motion>', self.on_move_layer_controls)
        
        title = ctk.CTkLabel(drag_handle, text="LAYER CONTROLS", font=("Segoe UI", 12, "bold")) # Panel title
        title.pack(pady=5)
        title.bind('<Button-1>', self.start_move_layer_controls) # Draggable
        title.bind('<B1-Motion>', self.on_move_layer_controls)
        
        buttons_frame = ctk.CTkFrame(container, fg_color="transparent") # Frame to control buttons
        buttons_frame.pack(fill="both", expand=True)
        
        button_height = 40 # Style for button
        button_font = ("Segoe UI", 14, "bold")
        
        self.move_up_btn = ctk.CTkButton( # Move Up button
            buttons_frame, 
            text="Move Up", 
            height=button_height,
            font=button_font,
            command=self.move_layer_up,
            state="disabled"
        )
        self.move_up_btn.pack(fill="x", pady=5)
        
        self.move_down_btn = ctk.CTkButton( # Move down button
            buttons_frame,  
            text="Move Down", 
            height=button_height,
            font=button_font,
            command=self.move_layer_down,
            state="disabled"
        )
        self.move_down_btn.pack(fill="x", pady=5)
        
        self.duplicate_btn = ctk.CTkButton( # Duplicate button
            buttons_frame, 
            text="Duplicate", 
            height=button_height,
            font=button_font,
            command=self.duplicate_layer,
            state="disabled"
        )
        self.duplicate_btn.pack(fill="x", pady=5)
        
        self.delete_btn = ctk.CTkButton( # Delete button
            buttons_frame, 
            text="Delete", 
            height=button_height,
            font=button_font,
            command=self.delete_layer,
            state="disabled",
            fg_color="#8B0000", 
            hover_color="#A52A2A"
        )
        self.delete_btn.pack(fill="x", pady=5)
        
        info_frame = ctk.CTkFrame(container, height=40) 
        info_frame.pack(fill="x", pady=(10, 0))
        
        self.current_layer_label = ctk.CTkLabel( # To show selected layer info
            info_frame, 
            text="No layer selected", 
            font=("Segoe UI", 11),
            wraplength=180
        )
        self.current_layer_label.pack(pady=5)
#----------------------------------------------------------------------------------------------------------------------------------------------------------------//

#---------------------------------- Function to Store Movement Mouse ------------------------------------//
    def start_move_layer_controls(self, event): # Store initial mouse position for dragging
        self.floating_layer_controls_panel.x = event.x
        self.floating_layer_controls_panel.y = event.y
#--------------------------------------------------------------------------------------------------------//

#-----------------------------------  Function to Store Movement Mouse  -------------------------------------//
    def on_move_layer_controls(self, event): # Handle window dragging
        if hasattr(self.floating_layer_controls_panel, 'x'): 
            deltax = event.x - self.floating_layer_controls_panel.x # Calculate movement delta
            deltay = event.y - self.floating_layer_controls_panel.y # Calculate movement delta

            x = self.floating_layer_controls_panel.winfo_x() + deltax # Calculate new position
            y = self.floating_layer_controls_panel.winfo_y() + deltay # Calculate new position
            self.floating_layer_controls_panel.geometry(f"+{x}+{y}") # Move window to new position
#------------------------------------------------------------------------------------------------------------//

#------------------------------------ Function to Update Layer Controls Panel -------------------------------------//
    def update_layer_controls_panel(self): # Update layer controls panel based on current selection
        if not self.floating_layer_controls_panel or not self.floating_layer_controls_panel.winfo_exists():
            return
        
        has_selection = self.selected_layer_index >= 0 # Determine button states based on selection
        can_move_up = has_selection and self.selected_layer_index < len(self.layers) - 1  
        can_move_down = has_selection and self.selected_layer_index > 0 
        can_delete = has_selection and self.selected_layer_index > 0  
        
        # Update button states
        self.move_up_btn.configure(state="normal" if can_move_up else "disabled") 
        self.move_down_btn.configure(state="normal" if can_move_down else "disabled")
        self.duplicate_btn.configure(state="normal" if has_selection else "disabled")
        self.delete_btn.configure(state="normal" if can_delete else "disabled")
        
        if has_selection: # Update layer info label
            layer = self.layers[self.selected_layer_index]
            self.current_layer_label.configure(
                text=f"Selected: {layer.name}\nOpacity: {layer.opacity}%"
            )
        else:
            self.current_layer_label.configure(text="No layer selected")
#----------------------------------------------------------------------------------------------------------------//

#------------------------------------------------------------- Function to Update Layer Controls Panel --------------------------------------------------------------//
    def show_layer_panel(self): # Show layers panel floating window
        if self.floating_layer_panel and self.floating_layer_panel.winfo_exists():
            self.floating_layer_panel.lift() # Bring to front if exists
            if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists(): # Also bring controls panel to front
                self.floating_layer_controls_panel.lift()
            return
        
        # Create new floating window
        self.floating_layer_panel = ctk.CTkToplevel(self)
        self.floating_layer_panel.title("Layers Panel")
        self.after(200, lambda: self.floating_layer_panel.iconbitmap("logo.ico") 
                   if self.floating_layer_panel.winfo_exists() else None)
        self.floating_layer_panel.geometry("300x350")
        self.floating_layer_panel.resizable(False, False)
        self.floating_layer_panel.transient(self)
        self.floating_layer_panel.attributes('-topmost', True)
        
        # Bind mouse events for dragging
        self.floating_layer_panel.bind('<Button-1>', self.start_move_layer_panel)
        self.floating_layer_panel.bind('<B1-Motion>', self.on_move_layer_panel)
        
        x = self.winfo_x() + self.middle_frame.winfo_x() + 50  # Position window
        y = self.winfo_y() + 100
        self.floating_layer_panel.geometry(f"+{x}+{y}")
        
        self.floating_layer_panel.protocol("WM_DELETE_WINDOW", self.hide_both_panels) # Handle window close
        
        self.create_layer_panel_content() # Create panel content
        
        self.update_layer_panel() # Update panel with current layers
        
        self.show_layer_controls_panel()
#----------------------------------------------------------------------------------------------------------------------------------------------------------------//

#------------------------------------- Function to Hide Both Panels -------------------------------------------//
    def hide_both_panels(self):
        self.hide_layer_panel() # Hide both layers and controls panels
        self.hide_layer_controls_panel()
        
        if hasattr(self, 'layer_toggle_btn'): # Update toggle button text
            self.layer_toggle_btn.configure(text="Layers")
#--------------------------------------------------------------------------------------------------------------//

#---------------------------------------- Function to Destroy Layers Panels----------------------------------//
    def hide_layer_panel(self): # Hide and destroy layers panel
        if self.floating_layer_panel and self.floating_layer_panel.winfo_exists():
            self.floating_layer_panel.destroy()
        self.floating_layer_panel = None
        self.layer_panel_visible = False
        
        self.hide_layer_controls_panel() # Hide control panels
#------------------------------------------------------------------------------------------------------------//

#------------------------------- Function to Open Layer Panel ------------------------------------------//
    def toggle_layer_panel(self): # Toggle visibility of layers panel
        if self.floating_layer_panel and self.floating_layer_panel.winfo_exists():
            self.hide_both_panels() # Hide if it visible
        else:
            self.show_layer_panel() # Show if hidden
#-------------------------------------------------------------------------------------------------------//

#------------------------------ Function to Store Mouse Position Dragging ------------------------------------------//
    def start_move_layer_panel(self, event): # Store initial mouse position for dragging
        self.floating_layer_panel.x = event.x
        self.floating_layer_panel.y = event.y
#-------------------------------------------------------------------------------------------------------------------//

#-------------------------------- Function to Handle Window Dragging------------------------------------//
    def on_move_layer_panel(self, event): 
        if hasattr(self.floating_layer_panel, 'x'): # Handle window dragging
            deltax = event.x - self.floating_layer_panel.x # Calculate movement delta
            deltay = event.y - self.floating_layer_panel.y

            x = self.floating_layer_panel.winfo_x() + deltax # Calculate new position
            y = self.floating_layer_panel.winfo_y() + deltay
            self.floating_layer_panel.geometry(f"+{x}+{y}") # Move window to new position
#-------------------------------------------------------------------------------------------------------//

#-------------------------------------------- Function to Create Layer Content --------------------------------------------------------//
    def create_layer_panel_content(self):
        if not self.floating_layer_panel: # Create content for layers panel
            return
        
        for widget in self.floating_layer_panel.winfo_children():
            widget.destroy()

        container = ctk.CTkFrame(self.floating_layer_panel) # Main container
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        drag_handle = ctk.CTkFrame(container, height=30, fg_color="#2a2a2a")
        drag_handle.pack(fill="x", pady=(0, 10))
        drag_handle.bind('<Button-1>', self.start_move_layer_panel)
        drag_handle.bind('<B1-Motion>', self.on_move_layer_panel)
        
        title = ctk.CTkLabel(drag_handle, text="LAYERS", font=("Segoe UI", 12, "bold")) # Panel title
        title.pack(pady=5)
        title.bind('<Button-1>', self.start_move_layer_panel) 
        title.bind('<B1-Motion>', self.on_move_layer_panel)
        
        self.layers_container = ctk.CTkScrollableFrame(container, height=350) # Scrollable frame for layer list
        self.layers_container.pack(fill="both", expand=True, pady=(0, 10))        
#-----------------------------------------------------------------------------------------------------------------------------------//

#--------------------------------------------------------- Function to Update Layer Panel -------------------------------------------------------------//
    def update_layer_panel(self):
        if not self.floating_layer_panel or not self.floating_layer_panel.winfo_exists(): # Update layers panel with current layer information
            return
        
        self.update_layer_list()  # Update layer list display
        
        if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists(): # Update controls panel if visible
            self.update_layer_controls_panel()
#------------------------------------------------------------------------------------------------------------------------------------------------------//

#----------------------------------------------------------------------------- Function to Update Layer List ---------------------------------------------------------------------------//
    def update_layer_list(self):   # Update the display of layers in the layers panel
        if not hasattr(self, 'layers_container'):
            return
        
        for widget in self.layers_container.winfo_children(): # Clear existing layer widgets
            widget.destroy()
        
        for i, layer in enumerate(reversed(self.layers)):  # Display layers in reverse order (top layer first)
            idx = len(self.layers) - 1 - i 
            
            layer_frame = ctk.CTkFrame(self.layers_container, height=50) # Create frame for each layer
            layer_frame.pack(fill="x", pady=2, padx=5)
            
            if idx == self.selected_layer_index:  # Highlight selected layer
                layer_frame.configure(border_width=2, border_color="#3a7ebf")
            
            if idx == self.editing_layer_index and idx > 0:
                layer_frame.configure(fg_color="#2a4d69") 
                
            thumb_size = 40 # Create thumbnail preview
            preview = layer.get_preview((thumb_size, thumb_size))
            
            if preview: # Convert PIL Image to CTkImage
                thumb_tk = ctk.CTkImage(light_image=preview, dark_image=preview, size=(preview.width, preview.height))
                thumb_label = ctk.CTkLabel(layer_frame, image=thumb_tk, text="", width=thumb_size, height=thumb_size)
                thumb_label.pack(side="left", padx=5)
            
            name_frame = ctk.CTkFrame(layer_frame, fg_color="transparent") # Frame for layer name
            name_frame.pack(side="left", fill="both", expand=True, padx=5)
            
            name_label = ctk.CTkLabel(name_frame, text=layer.name, font=("Segoe UI", 11)) # Layer name label
            name_label.pack(anchor="w")
        
            if idx == self.editing_layer_index and idx > 0:
                edit_label = ctk.CTkLabel(name_frame, text="(Active for editing)", font=("Segoe UI", 9, "italic"), text_color="#90caf9")
                edit_label.pack(anchor="w")
        
            visibility_text = "●" if layer.visible else "○" # Visibility toggle button
            visibility_btn = ctk.CTkButton(layer_frame, text=visibility_text, width=30, font=("Segoe UI", 12), command=lambda idx=idx: self.toggle_layer_visibility(idx))
            visibility_btn.pack(side="right", padx=2)
            
            select_btn = ctk.CTkButton(layer_frame, text="Select", width=50, font=("Segoe UI", 10), command=lambda idx=idx: self.select_layer(idx)) # Select button
            select_btn.pack(side="right", padx=2)
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------//

#-------------------------------------- Function to Select Layer for Editing -------------------------------------//
    def select_layer(self, index): # Select a layer for editing
        self.selected_layer_index = index
        
        if index > 0: # Set editing layer (can't edit base layer)
            self.editing_layer_index = index
        else:
            self.editing_layer_index = -1
        
        if self.editing_layer_index > 0: # Update opacity slider if editing a layer
            layer = self.layers[self.editing_layer_index]
            if hasattr(self, 'opacity_slider'):
                self.opacity_slider.set(layer.opacity)
            if hasattr(self, 'opacity_value_label'):
                self.opacity_value_label.configure(text=f"{int(layer.opacity)}%")
        
        self.update_layer_panel() # Update UI
        if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists():
            self.update_layer_controls_panel()
        
        self.compose_layers()
#----------------------------------------------------------------------------------------------------------------//

#----------------------------- Function to Update Layer Opacity ----------------------------------------//
    def update_layer_opacity(self, value): # Update opacity of selected layer
        if 0 <= self.selected_layer_index < len(self.layers):
            layer = self.layers[self.selected_layer_index]
            layer.opacity = float(value) # Set new opacity
            if hasattr(self, 'opacity_value_label'): # Update opacity display
                self.opacity_value_label.configure(text=f"{int(value)}%")
            
            self.compose_layers() # Update image
            self.update_layer_panel()
            if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists():
                self.update_layer_controls_panel()
#-------------------------------------------------------------------------------------------------------//

#-------------------------------- Function to Open Layer Visibility ---------------------------------------//
    def toggle_layer_visibility(self, index): # Toggle visibility of a layer
        if 0 <= index < len(self.layers):
            layer = self.layers[index]
            layer.visible = not layer.visible
            
            self.compose_layers() # Update image and UI
            self.update_layer_panel()
#----------------------------------------------------------------------------------------------------------//

#------------------------------------ Function to Move the Layer Up -----------------------------------------------------//
    def move_layer_up(self): # Move selected layer up in the stack
        if self.selected_layer_index < len(self.layers) - 1:
            idx = self.selected_layer_index
            self.layers[idx], self.layers[idx + 1] = self.layers[idx + 1], self.layers[idx] # Swap with layer above
            self.selected_layer_index = idx + 1
            
            self.compose_layers()
            self.update_layer_panel()
            if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists():
                self.update_layer_controls_panel()
#------------------------------------------------------------------------------------------------------------------------//

#---------------------------------------- Function to Move the Layer Down ---------------------------------------------------//
    def move_layer_down(self):
        if self.selected_layer_index > 0: # Move selected layer down in the stack
            idx = self.selected_layer_index
            
            self.layers[idx], self.layers[idx - 1] = self.layers[idx - 1], self.layers[idx] # Swap with layer below
            self.selected_layer_index = idx - 1 # Update selection index
            
            self.compose_layers() # Update image and UI
            self.update_layer_panel()
            if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists():
                self.update_layer_controls_panel()
#---------------------------------------------------------------------------------------------------------------------------//

#-------------------------------------------- Function to Duplicate Overlay -------------------------------------------//
    def duplicate_layer(self):
        if 0 <= self.selected_layer_index < len(self.layers): # Create a copy of the selected layer
            original = self.layers[self.selected_layer_index]
            
            
            duplicate = Layer(f"{original.name} Copy", original.original_image) # Create new layer with "Copy" suffix
            duplicate.opacity = original.opacity # Copy properties from original
            duplicate.visible = original.visible
            duplicate.scale = original.scale
            duplicate.x_offset = original.x_offset + 20  # Offset for visibility
            duplicate.y_offset = original.y_offset + 20
            
            self.layers.insert(self.selected_layer_index + 1, duplicate) # Insert duplicate after original
            self.selected_layer_index += 1
            
            self.compose_layers() # Update image and UI
            self.update_layer_panel()
            if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists():
                self.update_layer_controls_panel()
#----------------------------------------------------------------------------------------------------------------------//

#----------------------------------------------- Function to Delete Layer --------------------------------------------------//
    def delete_layer(self): # Delete selected layer (can't delete base layer)
        if 0 <= self.selected_layer_index < len(self.layers) and self.selected_layer_index > 0:
            
            del self.layers[self.selected_layer_index] # Remove layer from list
            self.selected_layer_index = max(0, self.selected_layer_index - 1) # Select previous layer (or base if first)
            self.editing_layer_index = -1 # Reset editing layer
            
            self.compose_layers() # Update image and UI
            self.update_layer_panel()
            if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists():
                self.update_layer_controls_panel()
#--------------------------------------------------------------------------------------------------------------------------//

#--------------------------------------------------------- Function to Add Overlay as Layer -----------------------------------------------------------------//
    def add_overlay_as_layer(self, image, name="Overlay"): # Add an overlay image as a new layer
        if image is None:
            return
        
        overlay_count = len([l for l in self.layers if "Overlay" in l.name]) # Count existing overlays for naming
        layer_name = f"{name} {overlay_count + 1}"
        new_layer = Layer(layer_name, image)
        
        self.layers.append(new_layer) # Add layer and select it
        self.selected_layer_index = len(self.layers) - 1
        
        self.editing_layer_index = self.selected_layer_index # Set as editing layer
        
        if not self.layer_panel_visible:
            self.show_layer_panel()
            self.layer_panel_visible = True
        
        self.update_overlay_rect_for_layer(self.selected_layer_index)  # Update overlay rectangle for this layer
         
        self.compose_layers() # Update image and UI
        self.update_layer_panel()
        
        if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists(): # Update controls panel if visible
            self.update_layer_controls_panel()
#-----------------------------------------------------------------------------------------------------------------------------------------------------------//

#------------------------------------------------ Function to Update Overlay Rectangle ---------------------------------------------------//
    def update_overlay_rect_for_layer(self, layer_index):  # Update the overlay rectangle for a specific layer
        if 0 <= layer_index < len(self.layers) and layer_index > 0:
            layer = self.layers[layer_index]
            
            
            if self.image is not None: # Get base image dimensions
                bh, bw = self.image.shape[:2]
                
                # Get scaled overlay dimensions
                oh, ow = layer.image.shape[:2]
                nw = int(ow * layer.scale)
                nh = int(oh * layer.scale)
                
                
                if nw > 0 and nh > 0:  # Calculate position with offset
                    x = (bw - nw) // 2 + layer.x_offset
                    y = (bh - nh) // 2 + layer.y_offset
                     
                    x = max(0, min(x, bw - nw)) # Clamp to image bounds
                    y = max(0, min(y, bh - nh))
                    
                    self.ov_rect = (x, y, x + nw, y + nh) # Store rectangle coordinates (x1, y1, x2, y2)
                else:
                    self.ov_rect = (0, 0, 0, 0)
#------------------------------------------------------------------------------------------------------------------------------------------//
    
#--------------------------------------------------- Function to Combine All Layers into One Image -----------------------------------------------------------//
    def compose_layers(self): # Composite all visible layers into a single image
        if not self.layers or self.image is None:
            return
        
        if self.layers[0].visible: # Start with base layer (or transparent if invisible)
            composite = self.layers[0].image.copy()
        else: # Create transparent background
            h, w = self.image.shape[:2]
            composite = np.zeros((h, w, 3), dtype=np.uint8)
        
        for i in range(1, len(self.layers)): # Blend all other layers
            layer = self.layers[i]
            
            if not layer.visible or layer.image is None:
                continue
            
            overlay_img = layer.get_transformed_image(composite.shape[1], composite.shape[0]) # Get transformed overlay image
            if overlay_img is None:
                continue
            
            # Calculate position with offset
            bh, bw = composite.shape[:2]
            oh, ow = overlay_img.shape[:2]
            x = (bw - ow) // 2 + layer.x_offset
            y = (bh - oh) // 2 + layer.y_offset
            
            x = max(0, min(x, bw - ow))
            y = max(0, min(y, bh - oh))
            
            if x < bw and y < bh and x + ow > 0 and y + oh > 0:  # Check if overlay is within composite bounds
                x1, x2 = max(0, x), min(bw, x + ow) # Calculate crop regions
                y1, y2 = max(0, y), min(bh, y + oh)
                
                if x1 < x2 and y1 < y2:
                    roi = composite[y1:y2, x1:x2]  # Get region of interest in composite
                    overlay_crop = overlay_img[max(0, -y):max(0, -y) + (y2-y1), max(0, -x):max(0, -x) + (x2-x1)]
                    
                    if overlay_crop.shape[2] == 4: # Handle RGBA (with alpha channel)
                        overlay_color = overlay_crop[:, :, :3]
                        overlay_alpha = overlay_crop[:, :, 3] / 255.0
                        overlay_alpha = overlay_alpha * (layer.opacity / 100.0)
                        
                        for c in range(3): # Alpha blending for each channel
                            roi[:, :, c] = roi[:, :, c] * (1 - overlay_alpha) + overlay_color[:, :, c] * overlay_alpha
                    else:
                        alpha = layer.opacity / 100.0
                        blended = cv.addWeighted(roi, 1 - alpha, overlay_crop, alpha, 0)
                        composite[y1:y2, x1:x2] = blended
        
        if self.editing_layer_index > 0 and self.editing_layer_index < len(self.layers): # Draw editing rectangle if a layer is being edited
            layer = self.layers[self.editing_layer_index]
            if layer.visible:
                
                self.update_overlay_rect_for_layer(self.editing_layer_index) # Update overlay rectangle
                
                x1, y1, x2, y2 = self.ov_rect  # Get rectangle coordinates
                
                if x1 < x2 and y1 < y2: # Draw rectangle if valid
                    cv.rectangle(composite, (x1, y1), (x2, y2), (255, 255, 255), 2)
                    button_radius = 15 # Draw delete button (X) in top-left corner
                    cv.circle(composite, (x1, y1), button_radius, (255, 255, 255), -1)
                    cv.line(composite, (x1-5, y1-5), (x1+5, y1+5), (0, 0, 0), 2)
                    cv.line(composite, (x1+5, y1-5), (x1-5, y1+5), (0, 0, 0), 2)
        
        self.image = composite # Update main image and display
        self.update_image_display()
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------//

#------------------------------------------------- Function to Drag Layer (Overlay) ------------------------------------------------------------------//
    def start_drag(self, event): # Handle mouse press on image
        if self.editing_layer_index > 0 and self.editing_layer_index < len(self.layers):
            layer = self.layers[self.editing_layer_index]

            if layer.visible:
                self.update_overlay_rect_for_layer(self.editing_layer_index) # Update overlay rectangle
                
                x1, y1, x2, y2 = self.ov_rect # Get rectangle coordinates
                
                if x1 < x2 and y1 < y2:  # Check if delete button was clicked
                    dist_to_x = np.sqrt((event.x - x1)**2 + (event.y - y1)**2) # Calculate distance to delete button
                    if dist_to_x < 20:  
                        del self.layers[self.editing_layer_index]
                        self.selected_layer_index = max(0, self.selected_layer_index - 1)
                        self.editing_layer_index = -1
                        self.compose_layers()
                        self.update_layer_panel()
                        return
        
        clicked_layer_index = -1  # Determine which layer was clicked
        for i in range(1, len(self.layers)): # Calculate layer bounds
            layer = self.layers[i]
            if not layer.visible:
                continue
                
            if self.image is not None:
                bh, bw = self.image.shape[:2]
                oh, ow = layer.image.shape[:2]
                nw = int(ow * layer.scale)
                nh = int(oh * layer.scale)
                
                if nw <= 0 or nh <= 0:
                    continue
                    
                x = (bw - nw) // 2 + layer.x_offset  # Calculate position
                y = (bh - nh) // 2 + layer.y_offset
                
                x1, y1, x2, y2 = x, y, x + nw, y + nh
                
                if x1 <= event.x <= x2 and y1 <= event.y <= y2: # Check if click is within layer bounds
                    clicked_layer_index = i
                    break
        
        if clicked_layer_index > 0: # Handle layer selection
            self.editing_layer_index = clicked_layer_index # Select and edit this layer
            self.selected_layer_index = clicked_layer_index
            
            self.update_overlay_rect_for_layer(clicked_layer_index)
            
            layer = self.layers[clicked_layer_index]
            x1, y1, x2, y2 = self.ov_rect
            
            if x1 < x2 and y1 < y2:  # Check if resize handle was clicked
                if np.sqrt((event.x - x2)**2 + (event.y - y2)**2) < 25:
                    self.resizing = True
                    self.last_mouse_pos = (event.x, event.y)
                    return
                    
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:  # Check if layer body was clicked for dragging
                self.dragging = True
                self.last_mouse_pos = (event.x, event.y)
                
                if hasattr(self, 'opacity_slider'): # Update opacity slider
                    self.opacity_slider.set(layer.opacity)
                if hasattr(self, 'opacity_value_label'):
                    self.opacity_value_label.configure(text=f"{int(layer.opacity)}%")
                
                self.update_layer_panel() # Update UI
                return
        
        self.dragging = False # No layer clicked, reset dragging states
        self.resizing = False
#----------------------------------------------------------------------------------------------------------------------------------------------------//

#------------------------------------------------------------ Function to Drag Overlay ---------------------------------------------------------------//
    def drag_overlay(self, event):
        if self.editing_layer_index <= 0 or self.editing_layer_index >= len(self.layers): # Handle mouse drag for moving/resizing layers
            return
            
        layer = self.layers[self.editing_layer_index] # Handle resizing
        
        if self.resizing: # Get current rectangle
            x1, y1, _, _ = self.ov_rect
            
            new_width = max(30, event.x - x1)  # Calculate new width based on mouse position
            orig_width = layer.image.shape[1]
            
            layer.scale = new_width / orig_width # Update scale based on width change
            
            self.compose_layers() # Update display
            
        elif self.dragging:
            dx = event.x - self.last_mouse_pos[0] # Calculate movement delta
            dy = event.y - self.last_mouse_pos[1]
            
            layer.x_offset += dx  # Update layer offset
            layer.y_offset += dy
            
            self.last_mouse_pos = (event.x, event.y) # Update mouse position
            self.compose_layers()
#--------------------------------------------------------------------------------------------------------------------------------------------------//

#------------------------------------ Function to Reset Dragging ---------------------------------------//
    def stop_drag(self, event): # Reset dragging states on mouse release
        self.dragging = False
        self.resizing = False
#-------------------------------------------------------------------------------------------------------//

#--------------------------------- Function to Zoom The Overlay Image ----------------------------------//
    def zoom_overlay(self, event): # Handle mouse wheel zoom for layers
        if self.editing_layer_index <= 0 or self.editing_layer_index >= len(self.layers):
            return
            
        layer = self.layers[self.editing_layer_index]
        
        if event.delta > 0:  # Zoom in or out based on wheel direction
            layer.scale *= 1.05 # Zoom In
        else:
            layer.scale *= 0.95 # Zoom Out

        layer.scale = max(0.1, min(layer.scale, 3.0))
        self.compose_layers() # Update display
#-------------------------------------------------------------------------------------------------------//

#--------------------------------------------------------------------------------------------- Function to Create Crop Section -------------------------------------------------------------------------------------------------------------//
    def create_crop_section(self, parent):
        crop_panel = ctk.CTkFrame(parent, fg_color="#2b2b2b")  # Create crop tools section
        crop_panel.pack(fill="x", padx=10, pady=5)
        
        self.crop_open = False
        self.crop_arrow = "▶"
        
        header_btn = ctk.CTkButton( # Header button
            crop_panel, 
            text=f"{self.crop_arrow} Crop",
            height=40,  
            font=("Segoe UI", 16, "bold"),
            command=self.toggle_crop,
            fg_color="#2b2b2b",
            hover_color="#2b2b2b"  
        )
        header_btn.pack(fill="x", pady=(5, 10)) 
        
        self.header_btn = header_btn
        
        self.crop_content = ctk.CTkFrame(crop_panel, fg_color="#2b2b2b") # Content frame (initially hidden)
        
        custom_frame = ctk.CTkFrame(self.crop_content, fg_color="#2b2b2b") # Custom dimensions input
        custom_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(custom_frame, text="Width:", font=("Segoe UI", 14, "bold"), text_color="white").pack(side="left", padx=(10, 3))
        self.crop_width = ctk.CTkEntry(custom_frame, width=40)
        self.crop_width.pack(side="left", padx=(0, 5))
        
        ctk.CTkLabel(custom_frame, text="Height:", font=("Segoe UI", 14, "bold"), text_color="white").pack(side="left", padx=(0, 3)) # Width input
        self.crop_height = ctk.CTkEntry(custom_frame, width=40)
        self.crop_height.pack(side="left")
        
        aspect_ratios = [ # Aspect ratio buttons
            ("1:1", 1/1),
            ("16:9", 16/9),
            ("5:4", 5/4)
        ]

        for name, ratio in aspect_ratios: # Create buttons for each aspect ratio
            btn = ctk.CTkButton(
                self.crop_content, 
                text=name, 
                height=35,
                font=("Segoe UI", 14, "bold"),
                command=lambda r=ratio: self.set_aspect_ratio(r),
                fg_color="#1f538d",
                text_color="white",  
                hover_color="#2a63a5" 
            )
            btn.pack(fill="x", padx=10, pady=2)
        
        apply_crop = ctk.CTkButton(self.crop_content, height=35, text="Apply Crop", font=("Segoe UI", 14, "bold"), command=self.apply_crop, fg_color="#1f538d", text_color="white", hover_color="#2a63a5") # Apply crop button
        apply_crop.pack(fill="x", padx=10, pady=(2, 10))
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------//

#--------------------------------- Function to Open Crop Section -------------------------------------------//
    def toggle_crop(self, event=None): # Toggle crop section visibility
        self.crop_open = not self.crop_open
        arrow = "▼" if self.crop_open else "▶" # Change arrow direction
        self.header_btn.configure(text=f"{arrow} Crop")
        
        if self.crop_open: # Show/hide content
            self.crop_content.pack(fill="x", padx=10, pady=(5, 10))
        else:
            self.crop_content.pack_forget()
#-----------------------------------------------------------------------------------------------------------//

#---------------------------------- Function to Set Aspect Ratio --------------------------------------//
    def set_aspect_ratio(self, ratio):
        if self.image is not None: # Set crop dimensions based on aspect ratio
            h, w = self.image.shape[:2] # Landscape aspect ratio
            if w/h > ratio: # Image is wider than target aspect ratio
                new_w = int(h * ratio)
                new_h = h
            else: # Image is taller than target aspect ratio
                new_h = int(w / ratio)
                new_w = w
            
            # Ensure dimensions don't exceed original
            new_w = min(new_w, w)
            new_h = min(new_h, h)
            
            self.crop_width.delete(0, "end")
            self.crop_width.insert(0, str(new_w))
            self.crop_height.delete(0, "end")
            self.crop_height.insert(0, str(new_h))
#------------------------------------------------------------------------------------------------------//

#---------------------------------- Function to Apply Crop ------------------------------------//
    def apply_crop(self): # Apply crop to image
        try: # Get dimensions from input fields
            width = int(self.crop_width.get())
            height = int(self.crop_height.get())
            
            if width > 0 and height > 0 and self.image is not None: # Validate dimensions
                h, w = self.image.shape[:2]
                if width <= w and height <= h: # Calculate center crop
                    x = (w - width) // 2
                    y = (h - height) // 2
                    
                    cropped = self.image[y:y+height, x:x+width] # Perform crop
                    self.add_to_history(cropped) # Add to history

                    if self.layers:# Update base layer
                        self.layers[0].image = cropped.copy()
                        self.layers[0].original_image = cropped.copy()
        except ValueError:
            pass
#----------------------------------------------------------------------------------------------//

#----------------------------------------------------------------------------------------------- Function to Create Overlay Section ---------------------------------------------------------------------------------------------------------------------//
    def create_overlay_section(self, parent): # Create overlay tools section
        overlay_panel = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        overlay_panel.pack(fill="x", padx=10, pady=5)
        
        self.overlay_open = False
        self.overlay_arrow = "▶"
        
        header_btn = ctk.CTkButton( # Header button
            overlay_panel, 
            text=f"{self.overlay_arrow} Overlay",
            height=40, 
            font=("Segoe UI", 16, "bold"),
            command=self.toggle_overlay,
            fg_color="#2b2b2b",
            hover_color="#2b2b2b"
        )
        header_btn.pack(fill="x", pady=5)
        
        self.overlay_header_btn = header_btn
        
        self.overlay_content = ctk.CTkFrame(overlay_panel, fg_color="transparent")

        add_photo_btn = ctk.CTkButton(self.overlay_content, height=35, text="Add Photo", font=("Segoe UI", 14, "bold"), command=self.load_overlay_image) # Add photo button
        add_photo_btn.pack(fill="x", padx=10, pady=2)

        opacity_frame = ctk.CTkFrame(self.overlay_content, fg_color="transparent")
        opacity_frame.pack(fill="x", padx=10, pady=5)

        opacity_control_frame = ctk.CTkFrame(opacity_frame, fg_color="transparent") # Opacity control frame
        opacity_control_frame.pack(fill="x")
        
        ctk.CTkLabel(opacity_control_frame, text="Opacity:", font=("Segoe UI", 12)).pack(side="left")

        self.opacity_slider = ctk.CTkSlider( # Opacity slider
            opacity_control_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            width=150,
            command=self.update_opacity
        ) 
        self.opacity_slider.set(100) # Default to 100%
        self.opacity_slider.pack(side="left", padx=(10, 0))

        self.opacity_value = ctk.CTkLabel(opacity_control_frame, text="100%", font=("Segoe UI", 12)) # Opacity value display
        self.opacity_value.pack(side="left", padx=(10, 0))

        self.cutout_frame = ctk.CTkFrame(self.overlay_content, fg_color="#1f538d") # Cutout section frame
        self.cutout_frame.pack(fill="x", padx=10, pady=2)
        
        self.cutout_open = False # Cutout state variables
        self.cutout_arrow = "▶" 
        
        self.cutout_header_btn = ctk.CTkButton( # Cutout header button
            self.cutout_frame,
            text=f"{self.cutout_arrow} Cutout",
            height=35,
            font=("Segoe UI", 14, "bold"),
            command=self.toggle_cutout,
            fg_color="#1f538d",
            hover_color="#1f538d"
        )
        self.cutout_header_btn.pack(fill="x", padx=3)
        
        self.cutout_content = ctk.CTkFrame(self.cutout_frame, fg_color="#1f538d")
        
        region_btn = ctk.CTkButton( # Region selection button
            self.cutout_content, 
            text="Region Selection", 
            height=35,
            font=("Segoe UI", 14, "bold"),
            fg_color="#2b2b2b",  
            text_color="white",
            hover_color="#333333",
            command=self.select_roi_with_cv2  
        )
        region_btn.pack(fill="x", padx=10, pady=2)
        
        auto_btn = ctk.CTkButton( # Auto selection button
            self.cutout_content, 
            text="Auto Selection", 
            height=35,
            font=("Segoe UI", 14, "bold"),
            fg_color="#2b2b2b",  
            text_color="white",
            hover_color="#333333",
            command=self.apply_auto_cutout
        )
        auto_btn.pack(fill="x", padx=10, pady=2)
        
        outline_btn = ctk.CTkButton( # Outline button
            self.cutout_content, 
            text="Outline", 
            height=35,
            font=("Segoe UI", 14, "bold"),
            fg_color="#2b2b2b",  
            text_color="white",
            hover_color="#333333",
            command=self.apply_outline_cutout 
        )
        outline_btn.pack(fill="x", padx=10, pady=(2, 10))

        apply_overlay = ctk.CTkButton(self.overlay_content, height=35, text="Apply Overlay", font=("Segoe UI", 14, "bold"), command=self.apply_overlay, fg_color="#1f538d", text_color="white", hover_color="#2a63a5") # Apply overlay button
        apply_overlay.pack(fill="x", padx=10, pady=(2, 10))
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------//

#----------------------------------------------------------- Function to Apply Auto Cutout --------------------------------------------------------------//
    def apply_auto_cutout(self): # Apply automatic cutout using thresholding
        if self.editing_layer_index <= 0 or self.editing_layer_index >= len(self.layers):
            messagebox.showwarning("No Layer", "Please select an overlay layer first.")
            return
        
        layer = self.layers[self.editing_layer_index]
        
        if len(layer.original_image.shape) == 3: # Convert to grayscale for thresholding
            if layer.original_image.shape[2] == 4:
                rgb_img = layer.original_image[:, :, :3]
                gray = cv.cvtColor(rgb_img, cv.COLOR_RGB2GRAY)
            else:
                gray = cv.cvtColor(layer.original_image, cv.COLOR_RGB2GRAY)
        else:
            gray = layer.original_image.copy()
        
        _, mask = cv.threshold(gray, 240, 255, cv.THRESH_BINARY_INV) # Threshold to create binary mask (invert: white becomes transparent)
        
        kernel = np.ones((3, 3), np.uint8) # Morphological operations to clean up mask
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel) # Dilation to erosion to fills holes
        mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel) # Erosion to dilation to removes noise
        
        mask = cv.GaussianBlur(mask, (5, 5), 0) # Apply Gaussian Blur (removes morphological)
        
        layer.apply_cutout(mask) # Apply mask to layer
        
        self.compose_layers() # Update display
        messagebox.showinfo("Success", "Auto cutout applied successfully!")
#-------------------------------------------------------------------------------------------------------------------------------------------------------//

#----------------------------------------------------- Function to Apply Outline Cutout ----------------------------------------------------------//
    def apply_outline_cutout(self): # Create cutout mask based on image outlines
        if self.editing_layer_index <= 0 or self.editing_layer_index >= len(self.layers):
            messagebox.showwarning("No Layer", "Please select an overlay layer first.")
            return
        
        layer = self.layers[self.editing_layer_index]
        
        
        if len(layer.original_image.shape) == 3: # Convert to grayscale
            if layer.original_image.shape[2] == 4:
                rgb_img = layer.original_image[:, :, :3] # RGBA image
                gray = cv.cvtColor(rgb_img, cv.COLOR_RGB2GRAY)
            else:
                gray = cv.cvtColor(layer.original_image, cv.COLOR_RGB2GRAY) # RGB image
        else:
            gray = layer.original_image.copy() # Already grayscale
        
        th2 = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 11, 2) # Adaptive thresholding to detect edges
    
        # Invert to get outlines as white
        mask = cv.bitwise_not(th2)
        layer.apply_cutout(mask)
        
        self.compose_layers() # Update display
        messagebox.showinfo("Success", "Outline cutout applied successfully!")
#------------------------------------------------------------------------------------------------------------------------------------------------//

#----------------------------------------------------------------- Function to Open Overlay Section --------------------------------------------------------------------------------------//
    def select_roi_with_cv2(self): # Select region of interest using OpenCV
        image_to_select_from = None
        layer_name = "Base Image"
        
        if self.editing_layer_index > 0 and self.editing_layer_index < len(self.layers): # Determine which image to select from
            layer = self.layers[self.editing_layer_index]
            image_to_select_from = layer.original_image
            layer_name = layer.name
        
        elif self.image is not None:
            image_to_select_from = self.image
        else:
            messagebox.showwarning("No Image", "Please load an image first.")
            return
        
        if len(image_to_select_from.shape) == 3 and image_to_select_from.shape[2] == 4:
            image_bgr = cv.cvtColor(image_to_select_from[:, :, :3], cv.COLOR_RGB2BGR) # RGBA to BGR (discard alpha)
        else:
            image_bgr = cv.cvtColor(image_to_select_from, cv.COLOR_RGB2BGR) # RGB to BGR
        
        
        messagebox.showinfo("Region Selection", # Show instructions
                          f"Select region from: {layer_name}\n\n"
                          "Drag a rectangle from top-left to bottom-right, then press ENTER or SPACE.\n"
                          "Press ESC to cancel.")
        
        roi = cv.selectROI(f"Select Region from {layer_name} - Press ENTER/SPACE when done, ESC to cancel", image_bgr, showCrosshair=True, fromCenter=False) # OpenCV ROI selector
        
        cv.destroyWindow(f"Select Region from {layer_name} - Press ENTER/SPACE when done, ESC to cancel") # Close ROI window
        
        if roi[2] > 0 and roi[3] > 0: # Check if ROI was selected
            x, y, w, h = roi
            roi_image = image_to_select_from[y:y+h, x:x+w].copy() # Extract ROI coordinates
            
            self.add_overlay_as_layer(roi_image, f"ROI from {layer_name}") # Add as new layer
            
            messagebox.showinfo("Success", # Show success message
                              f"Region selection added as new layer.\n"
                              f"Source: {layer_name}\n"
                              f"Size: {w}x{h} pixels")
        else:
            messagebox.showinfo("Cancelled", "Region selection was cancelled or no region was selected.") # Selection was cancelled
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------//

#--------------------------------- Function to Open Overlay Section --------------------------------------//
    def toggle_overlay(self): # Toggle overlay section visibility
        self.overlay_open = not self.overlay_open
        arrow = "▼" if self.overlay_open else "▶"
        self.overlay_header_btn.configure(text=f"{arrow} Overlay")
        
        if self.overlay_open: # Show/hide content
            self.overlay_content.pack(fill="x", padx=10, pady=(5, 10))
        else:
            self.overlay_content.pack_forget()
#---------------------------------------------------------------------------------------------------------//

#--------------------------------------- Function to Add Overlay Photo -----------------------------------//
    def add_overlay_photo(self): # Load and add overlay image
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            img = cv.imread(file_path)
            if img is None:
                return
                
            img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
            
            if self.image is not None: # Resize to match base image
                h, w = self.image.shape[:2]
                img = cv.resize(img, (w, h))
            
            
            self.add_overlay_as_layer(img, "Overlay") # Add as new layer
            
            
            if self.selected_layer_index > 0: # Set as editing layer
                self.editing_layer_index = self.selected_layer_index
            
            if self.editing_layer_index > 0: # Update opacity controls
                layer = self.layers[self.editing_layer_index]
                if hasattr(self, 'opacity_slider'):
                    self.opacity_slider.set(layer.opacity)
                if hasattr(self, 'opacity_value_label'):
                    self.opacity_value_label.configure(text=f"{int(layer.opacity)}%")
            
            self.compose_layers() # Update display
#-------------------------------------------------------------------------------------------------------//

#--------------------------------------------------------------- Function to Update Opacity ----------------------------------------------------------//
    def update_opacity(self, value): # Update layer opacity when slider changes
        if self.editing_layer_index > 0 and self.editing_layer_index < len(self.layers):
            layer = self.layers[self.editing_layer_index]
            layer.opacity = float(value) # Update layer opacity
            self.opacity_value.configure(text=f"{int(float(value))}%")
            self.compose_layers() # Update image

            if self.floating_layer_controls_panel and self.floating_layer_controls_panel.winfo_exists(): # Update controls panel if visible
                self.update_layer_controls_panel()
#------------------------------------------------------------------------------------------------------------------------------------------------------//

#------------------------------------ Function to Load Overlay Image -------------------------------------//
    def load_overlay_image(self): # Load overlay image from file
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        )
        if not path or self.image is None:  
            return

        img = cv.imread(path)
        if img is None:
            return
            
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        
        self.add_overlay_as_layer(img, "Overlay") # Add as new layer
        
        if self.selected_layer_index > 0: # Set as editing layer
            self.editing_layer_index = self.selected_layer_index
        
        if self.editing_layer_index > 0: # Update opacity controls
            layer = self.layers[self.editing_layer_index]
            self.opacity_slider.set(layer.opacity)
            self.opacity_value.configure(text=f"{int(layer.opacity)}%")
            
        self.compose_layers() # Update display
#-------------------------------------------------------------------------------------------------------//

#-------------------------------- Function to Open Cutout Section -------------------------------------------//
    def toggle_cutout(self): # Toggle cutout section visibility
        self.cutout_open = not self.cutout_open
        arrow = "▼" if self.cutout_open else "▶"
        self.cutout_header_btn.configure(text=f"{arrow} Cutout")
        
        if self.cutout_open: # Show/hide content
            self.cutout_content.pack(fill="x", pady=(0, 5))
        else:
            self.cutout_content.pack_forget()
#------------------------------------------------------------------------------------------------------------//

#----------------------------------------------------------- Function to Apply Overlay --------------------------------------------------------------------//
    def apply_overlay(self): # Apply overlay operations and merge layers
        if self.image is None:
            messagebox.showwarning("No Image", "Please load an image first.")
            return
        
        original_editing_index = self.editing_layer_index # Store current editing index
        self.editing_layer_index = -1  
        
        self.compose_layers() # Compose final image
        
        self.add_to_history(self.image.copy()) # Add to history
        
        if self.layers: # Update base layer
            self.layers[0].image = self.image.copy()
            self.layers[0].original_image = self.image.copy()
        
        if len(self.layers) > 1: # Remove overlay layers (keep only base)
            self.layers = [self.layers[0]] # Keep only base layer
            self.selected_layer_index = 0
            self.editing_layer_index = -1
            
            
            if self.floating_layer_panel and self.floating_layer_panel.winfo_exists(): # Update layers panel
                self.update_layer_panel()
            
            self.compose_layers() # Update display
        else:
            
            self.editing_layer_index = original_editing_index # Restore editing state
            self.compose_layers()  
#---------------------------------------------------------------------------------------------------------------------------------------------------------//

#-------------------------------------- Function to Apply Overlay ----------------------------------------------------//
    def apply_overlay_immediately(self): # Apply overlay immediately to current image
        if self.display_image is not None:
            self.add_to_history(self.display_image)
#---------------------------------------------------------------------------------------------------------------------//

#---------------------------------------------------------------  Function to Create Effects Section -------------------------------------------------------//
    def create_effects_section(self, parent): # Create effects tools section
        effects_panel = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        effects_panel.pack(fill="x", padx=10, pady=5)
        
        self.effects_open = False
        self.effects_arrow = "▶"
        
        header_btn = ctk.CTkButton( # Header button
            effects_panel, 
            text=f"{self.effects_arrow} Effects",
            height=40,
            font=("Segoe UI", 16, "bold"),
            command=self.toggle_effects,
            fg_color="#2b2b2b",
            hover_color="#2b2b2b"
        )
        header_btn.pack(fill="x", pady=(5, 10))
        
        self.effects_header_btn = header_btn
        
        self.effects_content = ctk.CTkFrame(effects_panel, fg_color="#2b2b2b") # Content frame (initially hidden)
        
        self.noise_frame = ctk.CTkFrame(self.effects_content, fg_color="#1f538d") # Noise section frame
        self.noise_frame.pack(fill="x", padx=10, pady=2)
        
        self.noise_open = False # Noise state variables
        self.noise_arrow = "▶"
        
        self.noise_header_btn = ctk.CTkButton(  # Noise header button
            self.noise_frame,
            text=f"{self.noise_arrow} Noise",
            height=35,
            font=("Segoe UI", 14, "bold"),
            command=self.toggle_noise,
            fg_color="#1f538d",
            hover_color="#1f538d"
        )
        self.noise_header_btn.pack(fill="x", padx=3)
        
        self.noise_content = ctk.CTkFrame(self.noise_frame, fg_color="#1f538d") # Noise content frame
        
        # Noise size control
        noise_size_frame = ctk.CTkFrame(self.noise_content, fg_color="#1f538d")
        noise_size_frame.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(noise_size_frame, text="Size:  ", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.noise_size_slider = ctk.CTkSlider(
            noise_size_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            width=150,
            command=self.update_noise_preview,
            button_color="#2b2b2b"
        )
        self.noise_size_slider.set(0)
        self.noise_size_slider.pack(side="left", padx=(10, 0))
        self.noise_size_label = ctk.CTkLabel(noise_size_frame, text="10", font=("Segoe UI", 14, "bold"))
        self.noise_size_label.pack(side="left", padx=(10, 0))
        
        # Noise level control
        noise_level_frame = ctk.CTkFrame(self.noise_content, fg_color="#1f538d")
        noise_level_frame.pack(fill="x", padx=10, pady=(5, 10))
        ctk.CTkLabel(noise_level_frame, text="Level:", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.noise_level_slider = ctk.CTkSlider(
            noise_level_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            width=150,
            command=self.update_noise_preview,
            button_color="#2b2b2b"
        )
        self.noise_level_slider.set(0)
        self.noise_level_slider.pack(side="left", padx=(10, 0))
        self.noise_level_label = ctk.CTkLabel(noise_level_frame, text="50", font=("Segoe UI", 14, "bold"))
        self.noise_level_label.pack(side="left", padx=(10, 0))
        
        apply_grayscale_btn = ctk.CTkButton( # Grayscale button
            self.effects_content, 
            text="Grayscale", 
            height=35,
            font=("Segoe UI", 14, "bold"),
            command=self.apply_grayscale,
            fg_color="#1f538d",
            text_color="white",
            hover_color="#2a63a5"
        )
        apply_grayscale_btn.pack(fill="x", padx=10, pady=2)

        self.halftone_frame = ctk.CTkFrame(self.effects_content, fg_color="#1f538d") # Halftone section frame
        self.halftone_frame.pack(fill="x", padx=10, pady=2)
        
        self.halftone_open = False # Halftone state variables
        self.halftone_arrow = "▶"
        
        self.halftone_header_btn = ctk.CTkButton( # Halftone header button
            self.halftone_frame,
            text=f"{self.halftone_arrow} Halftone",
            height=35,
            font=("Segoe UI", 14, "bold"),
            command=self.toggle_halftone,
            fg_color="#1f538d",
            hover_color="#1f538d"
        )
        self.halftone_header_btn.pack(fill="x", padx=3)
        
        self.halftone_content = ctk.CTkFrame(self.halftone_frame, fg_color="#1f538d") # Halftone content frame
        
        halftone_strength_frame = ctk.CTkFrame(self.halftone_content, fg_color="#1f538d") # Halftone strength control
        halftone_strength_frame.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(halftone_strength_frame, text="Level:", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.halftone_slider = ctk.CTkSlider(
            halftone_strength_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            width=150,
            command=self.update_halftone_preview,
            button_color="#2b2b2b"
        )
        self.halftone_slider.set(0)
        self.halftone_slider.pack(side="left", padx=(10, 0))
        self.halftone_value_label = ctk.CTkLabel(halftone_strength_frame, text="9", font=("Segoe UI", 14, "bold"))
        self.halftone_value_label.pack(side="left", padx=(10, 0))

        self.blurring_frame = ctk.CTkFrame(self.effects_content, fg_color="#1f538d")
        self.blurring_frame.pack(fill="x", padx=10, pady=2)
        
        self.blurring_open = False # Blurring state variables
        self.blurring_arrow = "▶"
        
        self.blurring_header_btn = ctk.CTkButton( # Blurring header button
            self.blurring_frame,
            text=f"{self.blurring_arrow} Blurring",
            height=35,
            font=("Segoe UI", 14, "bold"),
            command=self.toggle_blurring,
            fg_color="#1f538d",
            hover_color="#1f538d"
        )
        self.blurring_header_btn.pack(fill="x", padx=3)
        
        self.blurring_content = ctk.CTkFrame(self.blurring_frame, fg_color="#1f538d") # Blurring header button
        
        blurring_strength_frame = ctk.CTkFrame(self.blurring_content, fg_color="#1f538d") # Blurring content frame
        blurring_strength_frame.pack(fill="x", padx=10, pady=(10, 5)) # Blurring strength control
        ctk.CTkLabel(blurring_strength_frame, text="Level:", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.blurring_slider = ctk.CTkSlider(
            blurring_strength_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            width=150,
            command=self.update_blurring_preview,
            button_color="#2b2b2b"
        )
        self.blurring_slider.set(0)
        self.blurring_slider.pack(side="left", padx=(10, 0))
        self.blurring_label = ctk.CTkLabel(blurring_strength_frame, text="15", font=("Segoe UI", 14, "bold"))
        self.blurring_label.pack(side="left", padx=(10, 0))

        self.effects_apply_btn = ctk.CTkButton( # Apply all effects button
            self.effects_content, 
            height=35, 
            text="Apply Effect", 
            font=("Segoe UI", 14, "bold"),
            fg_color="#1f538d", 
            text_color="white", 
            hover_color="#2a63a5",
            command=self.apply_all_effects # Apply all selected effects
        )
        self.effects_apply_btn.pack(fill="x", padx=10, pady=(2, 10))
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------//

#-------------------------------------------------------- Function to Update Noise ----------------------------------------------------------//
    def update_noise_preview(self, value):
        self.noise_size_label.configure(text=str(int(self.noise_size_slider.get())))
        self.noise_level_label.configure(text=str(int(self.noise_level_slider.get())))
        
        if self.image is not None:
            # Get current image from history
            current_img = self.history[self.history_index].copy()

            noise_size = int(self.noise_size_slider.get())
            noise_level = int(self.noise_level_slider.get()) / 100.0
            
            h, w, c = current_img.shape[:3]
            
            # Convert to float for proper noise addition
            img_float = current_img.astype(np.float32)
            
            # Generate Gaussian noise
            mean = 0
            std_dev = noise_level * 50  # Adjust multiplier for noise strength
            
            if noise_size > 1:
                # For granular control, generate smaller noise and upsample
                small_h = max(1, h // noise_size)
                small_w = max(1, w // noise_size)
                gaussian_noise_small = np.random.normal(mean, std_dev, (small_h, small_w, c))
                gaussian_noise = cv.resize(gaussian_noise_small, (w, h), interpolation=cv.INTER_LINEAR)
            else:
                gaussian_noise = np.random.normal(mean, std_dev, (h, w, c))
            
            # Store the generated noise pattern for later use when applying
            self.current_noise_pattern = gaussian_noise.copy()
            
            # Add noise to image
            noisy_img_float = img_float + gaussian_noise
            
            # Clip to valid range [0, 255] and convert back to uint8
            noisy_img = np.clip(noisy_img_float, 0, 255).astype(np.uint8)
            
            self.preview_image = noisy_img
            self.update_image_display()
#--------------------------------------------------------------------------------------------------------------------------------------------//

#---------------------------------------------------- Function to Apply Grayscale --------------------------------------------------------------------------//
    def apply_grayscale(self): # Convert image to grayscale
        if self.image is not None:
            current_img = self.history[self.history_index].copy() # Get current image from history
            gray = cv.cvtColor(current_img, cv.COLOR_RGB2GRAY) # Convert to grayscale
            result = cv.cvtColor(gray, cv.COLOR_GRAY2RGB) # Convert back to RGB (3 channels)
            self.add_to_history(result) # Add to history
            if self.layers: # Update base layer
                self.layers[0].image = result.copy()
                self.layers[0].original_image = result.copy()
#-----------------------------------------------------------------------------------------------------------------------------------------------------------//

#--------------------------------------------------- Function to Open Blurring Section --------------------------------------------------//
    def update_halftone_preview(self, value):  
        if self.image is not None: # Update halftone preview when slider changes
            self.halftone_value_label.configure(text=str(int(float(value)))) # Update value label
            
            if float(value) == 0:
                self.preview_image = None
                self.update_image_display()
                return
                
            self.history[self.history_index].copy() # Get current image from history

            val = float(value) # Determine halftone pattern based on value
            if val <= 33: # Small dots
                block_size = 2
                pattern = np.array([[1, 3],
                                    [4, 2]])
            elif val <= 66:
                block_size = 4 # Medium dots
                pattern = np.array([[1, 9, 3, 11],
                                    [13, 5, 15, 7],
                                    [4, 12, 2, 10],
                                    [16, 8, 14, 6]])
            else:
                block_size = 8 # Large dots
                pattern = np.array([[0, 48, 12, 60, 3, 51, 15, 63],
                                    [32, 16, 44, 28, 35, 19, 47, 31],
                                    [8, 56, 4, 52, 11, 59, 7, 55],
                                    [40, 24, 36, 20, 43, 27, 39, 23],
                                    [2, 50, 14, 62, 1, 49, 13, 61],
                                    [34, 18, 46, 30, 33, 17, 45, 29],
                                    [10, 58, 6, 54, 9, 57, 5, 53],
                                    [42, 26, 38, 22, 41, 25, 37, 21]])

            gray_img = cv.cvtColor(self.image, cv.COLOR_RGB2GRAY) # Convert to grayscale
            h, w = gray_img.shape

            pattern = (pattern - pattern.min()) / (pattern.max() - pattern.min()) * 255 # Normalize pattern to 0-255

            reps_h = (h // block_size) + 1 # Tile pattern to cover image
            reps_w = (w // block_size) + 1
            pattern_tiled = np.tile(pattern, (reps_h, reps_w))[:h, :w]

            halftoned = np.where(gray_img > pattern_tiled, 255, 0).astype(np.uint8) # Apply halftone thresholding
            
            halftoned_rgb = cv.cvtColor(halftoned, cv.COLOR_GRAY2RGB) # Convert back to RGB
            
            self.preview_image = halftoned_rgb # Store preview and update display
            self.update_image_display()
#----------------------------------------------------------------------------------------------------------------------------------------------//

#------------------------------------ Function to Open Blurring Section -------------------------------------//
    def update_blurring_preview(self, value):
        if self.image is not None: # Update blur preview when slider changes
            self.blurring_label.configure(text=str(int(float(value))))
            
            self.history[self.history_index].copy() # Get current image from history

            blur_strength = int(float(value)) # Calculate kernel size from blur strength
            kernel_size = max(3, blur_strength // 2 * 2 + 1) 
            
            if kernel_size % 2 == 0: # Ensure kernel is odd
                kernel_size += 1
        
            blurred = cv.medianBlur(self.image, kernel_size) # Apply median blur
            
            self.preview_image = blurred # Store preview and update display
            self.update_image_display()
#-------------------------------------------------------------------------------------------------------//

#-------------------------------- Function to Open Effects Section -------------------------------------//
    def toggle_effects(self): # Toggle effects section visibility
        self.effects_open = not self.effects_open
        arrow = "▼" if self.effects_open else "▶"
        self.effects_header_btn.configure(text=f"{arrow} Effects")
        
        if self.effects_open: # Show/hide content
            self.effects_content.pack(fill="x", padx=10, pady=(5, 10))
        else:
            self.effects_content.pack_forget() # Clear preview when hiding
            self.current_noise_pattern = None  # Clear saved noise pattern
            if hasattr(self, 'preview_image') and self.preview_image is not None:
                self.preview_image = None
                self.update_image_display()
#-------------------------------------------------------------------------------------------------------//

#-------------------------------- Function to Open Noise Section ---------------------------------------//
    def toggle_noise(self): # Toggle noise section visibility
        self.noise_open = not self.noise_open
        arrow = "▼" if self.noise_open else "▶"
        self.noise_header_btn.configure(text=f"{arrow} Noise")
        
        if self.noise_open: #  Show/hide content
            self.noise_content.pack(fill="x", pady=(0, 5))
        else:
            self.noise_content.pack_forget()
#-------------------------------------------------------------------------------------------------------//

#----------------------------------- Function to Open Halftone Section -----------------------------------//
    def toggle_halftone(self): # Toggle halftone section visibility
        self.halftone_open = not self.halftone_open
        arrow = "▼" if self.halftone_open else "▶"
        self.halftone_header_btn.configure(text=f"{arrow} Halftone")
        
        if self.halftone_open: # Show/hide content
            self.halftone_content.pack(fill="x", pady=(0, 5))
        else:
            self.halftone_content.pack_forget()
#---------------------------------------------------------------------------------------------------------//

#----------------------------------- Function to Open Blurring Section --------------------------------------//
    def toggle_blurring(self): # Toggle blurring section visibility
        self.blurring_open = not self.blurring_open
        arrow = "▼" if self.blurring_open else "▶"
        self.blurring_header_btn.configure(text=f"{arrow} Blurring")
        
        if self.blurring_open: # Show/hide content
            self.blurring_content.pack(fill="x", pady=(0, 5))
        else:
            self.blurring_content.pack_forget()
#------------------------------------------------------------------------------------------------------------//

#---------------------------------------------- Function to Apply All Effects ------------------------------------------------------//
    def apply_all_effects(self): # Apply all selected effects to the image
        if self.image is None:
            return
        
        result = self.history[self.history_index].copy() # Start with current image
        
        noise_size = int(self.noise_size_slider.get()) # Apply noise if enabled
        noise_level = int(self.noise_level_slider.get())
        
        if noise_size != 10 or noise_level != 50:
            h, w = result.shape[:2]
            result_float = result.astype(np.float32)
            
            # Use the saved noise pattern if it exists
            if self.current_noise_pattern is not None:
                # Make sure dimensions match
                if (self.current_noise_pattern.shape[0] == h and 
                    self.current_noise_pattern.shape[1] == w):
                    gaussian_noise = self.current_noise_pattern
                else:
                    # Regenerate if dimensions don't match
                    mean = 0
                    std_dev = (noise_level / 100.0) * 50
                    if noise_size > 1:
                        small_h = max(1, h // noise_size)
                        small_w = max(1, w // noise_size)
                        gaussian_noise_small = np.random.normal(mean, std_dev, (small_h, small_w, 3))
                        gaussian_noise = cv.resize(gaussian_noise_small, (w, h), interpolation=cv.INTER_LINEAR)
                    else:
                        gaussian_noise = np.random.normal(mean, std_dev, (h, w, 3))
            else:
                # Generate new pattern if none saved
                mean = 0
                std_dev = (noise_level / 100.0) * 50
                if noise_size > 1:
                    small_h = max(1, h // noise_size)
                    small_w = max(1, w // noise_size)
                    gaussian_noise_small = np.random.normal(mean, std_dev, (small_h, small_w, 3))
                    gaussian_noise = cv.resize(gaussian_noise_small, (w, h), interpolation=cv.INTER_LINEAR)
                else:
                    gaussian_noise = np.random.normal(mean, std_dev, (h, w, 3))
            
            # Add Gaussian noise
            result_float = result_float + gaussian_noise
            result = np.clip(result_float, 0, 255).astype(np.uint8)
        
        blur_strength = int(self.blurring_slider.get()) # Apply blur if enabled
        if blur_strength != 0:
            kernel_size = max(3, blur_strength // 2 * 2 + 1)
            if kernel_size % 2 == 0:  
                kernel_size += 1
            result = cv.medianBlur(result, kernel_size)
        
        halftone_strength = int(self.halftone_slider.get()) # Apply halftone if enabled
        if halftone_strength > 0:
            val = float(halftone_strength)
            if val < 33:
                block_size = 2
                pattern = np.array([[1, 3], [4, 2]])
            elif val < 66:
                block_size = 4
                pattern = np.array([[1, 9, 3, 11],
                                    [13, 5, 15, 7],
                                    [4, 12, 2, 10],
                                    [16, 8, 14, 6]])
            else:
                block_size = 8
                pattern = np.array([[0, 48, 12, 60, 3, 51, 15, 63],
                                    [32, 16, 44, 28, 35, 19, 47, 31],
                                    [8, 56, 4, 52, 11, 59, 7, 55],
                                    [40, 24, 36, 20, 43, 27, 39, 23],
                                    [2, 50, 14, 62, 1, 49, 13, 61],
                                    [34, 18, 46, 30, 33, 17, 45, 29],
                                    [10, 58, 6, 54, 9, 57, 5, 53],
                                    [42, 26, 38, 22, 41, 25, 37, 21]])
            
            gray_img = cv.cvtColor(result, cv.COLOR_RGB2GRAY) # Convert to grayscale
            h, w = gray_img.shape
            
            pattern = (pattern - pattern.min()) / (pattern.max() - pattern.min()) * 255 # Normalize and tile pattern
            reps_h = (h // block_size) + 1
            reps_w = (w // block_size) + 1
            pattern_tiled = np.tile(pattern, (reps_h, reps_w))[:h, :w]
            
            halftoned = np.where(gray_img > pattern_tiled, 255, 0).astype(np.uint8) # Apply halftone thresholding
            result = cv.cvtColor(halftoned, cv.COLOR_GRAY2RGB)
        
        self.add_to_history(result)
        
        if self.layers: # Update base layer
            self.layers[0].image = result.copy()
            self.layers[0].original_image = result.copy()
        
        self.noise_size_slider.set(0) # Reset sliders
        self.noise_level_slider.set(0)
        self.blurring_slider.set(0)
        self.halftone_slider.set(0)
        
        self.current_noise_pattern = None  # Clear saved noise pattern
        self.preview_image = None # Clear preview
        self.update_image_display()
#---------------------------------------------------------------------------------------------------------------------------------//








# !           --------------------------------  ADJUST   ---------------------------------------------- 
#-------------------------------------------------------------- Function Create Adjust Section --------------------------------------------------------//
    def create_adjust_section(self, parent): # Create adjustment tools section
        adjust_panel = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        adjust_panel.pack(fill="x", padx=10, pady=5)
        
        self.adjust_open = False
        self.adjust_arrow = "▶"
        
        header_btn = ctk.CTkButton( # Header button
            adjust_panel, 
            text=f"{self.adjust_arrow} Adjust",
            height=40,
            font=("Segoe UI", 16, "bold"),
            command=self.toggle_adjust,
            fg_color="#2b2b2b",
            hover_color="#2b2b2b"
        )
        header_btn.pack(fill="x", pady=(5, 10))
        
        self.adjust_header_btn = header_btn
        
        self.adjust_content = ctk.CTkFrame(adjust_panel, fg_color="#2b2b2b") # Content frame (initially hidden)
        
        self.sharpness_frame = ctk.CTkFrame(self.adjust_content, fg_color="#1f538d") # Sharpness section frame
        self.sharpness_frame.pack(fill="x", padx=10, pady=2)
        
        self.sharpness_open = False
        self.sharpness_arrow = "▶"
        
        self.sharpness_header_btn = ctk.CTkButton(  # Sharpness header button
            self.sharpness_frame,
            text=f"{self.sharpness_arrow} Sharpness",
            height=35,
            font=("Segoe UI", 14, "bold"),
            command=self.toggle_sharpness,
            fg_color="#1f538d",
            hover_color="#1f538d"
        )
        self.sharpness_header_btn.pack(fill="x", padx=3)
        
        self.sharpness_content = ctk.CTkFrame(self.sharpness_frame, fg_color="#1f538d")
        
        sharpness_level_frame = ctk.CTkFrame(self.sharpness_content, fg_color="#1f538d") # Sharpness content frame
        sharpness_level_frame.pack(fill="x", padx=10, pady=(10, 5)) # Sharpness level control
        ctk.CTkLabel(sharpness_level_frame, text="Level:", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.sharpness_slider = ctk.CTkSlider(
            sharpness_level_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            width=150,
            command=self.update_sharpness_preview,
            button_color="#2b2b2b"
        )
        self.sharpness_slider.set(0)
        self.sharpness_slider.pack(side="left", padx=(10, 0))
        self.sharpness_value_label = ctk.CTkLabel(sharpness_level_frame, text="50", font=("Segoe UI", 14, "bold"))
        self.sharpness_value_label.pack(side="left", padx=(10, 0))
        
        self.brightness_frame = ctk.CTkFrame(self.adjust_content, fg_color="#1f538d") # Brightness section frame
        self.brightness_frame.pack(fill="x", padx=10, pady=2)
        
        self.brightness_open = False # Brightness state variables
        self.brightness_arrow = "▶"
        
        self.brightness_header_btn = ctk.CTkButton( # Brightness header button
            self.brightness_frame,
            text=f"{self.brightness_arrow} Brightness",
            height=35,
            font=("Segoe UI", 14, "bold"),
            command=self.toggle_brightness,
            fg_color="#1f538d",
            hover_color="#1f538d"
        )
        self.brightness_header_btn.pack(fill="x", padx=3)
        
        self.brightness_content = ctk.CTkFrame(self.brightness_frame, fg_color="#1f538d")
        
        brightness_level_frame = ctk.CTkFrame(self.brightness_content, fg_color="#1f538d") # Brightness level control
        brightness_level_frame.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(brightness_level_frame, text="Level:", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.brightness_slider = ctk.CTkSlider( 
            brightness_level_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            width=150,
            command=self.update_brightness_preview,
            button_color="#2b2b2b"
        )
        self.brightness_slider.set(0)
        self.brightness_slider.pack(side="left", padx=(10, 0))
        self.brightness_value_label = ctk.CTkLabel(brightness_level_frame, text="0", font=("Segoe UI", 14, "bold"))
        self.brightness_value_label.pack(side="left", padx=(10, 0))
        
        self.darkness_frame = ctk.CTkFrame(self.adjust_content, fg_color="#1f538d")
        self.darkness_frame.pack(fill="x", padx=10, pady=2)
        
        self.darkness_open = False # Darkness state variables
        self.darkness_arrow = "▶"
        
        self.darkness_header_btn = ctk.CTkButton( # Darkness header button
            self.darkness_frame,
            text=f"{self.darkness_arrow} Darkness",
            height=35,
            font=("Segoe UI", 14, "bold"),
            command=self.toggle_darkness,
            fg_color="#1f538d",
            text_color="white",
            hover_color="#1f538d"
        )
        self.darkness_header_btn.pack(fill="x", padx=3)
        
        self.darkness_content = ctk.CTkFrame(self.darkness_frame, fg_color="#1f538d")
        
        darkness_level_frame = ctk.CTkFrame(self.darkness_content, fg_color="#1f538d") # Darkness level control
        darkness_level_frame.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(darkness_level_frame, text="Level:", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.darkness_slider = ctk.CTkSlider(
            darkness_level_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            width=150,
            command=self.update_darkness_preview,
            button_color="#2b2b2b"
        )
        self.darkness_slider.set(100)
        self.darkness_slider.pack(side="left", padx=(10, 0))
        self.darkness_value_label = ctk.CTkLabel(darkness_level_frame, text="0", font=("Segoe UI", 14, "bold"))
        self.darkness_value_label.pack(side="left", padx=(10, 0))
        
        self.vignette_frame = ctk.CTkFrame(self.adjust_content, fg_color="#1f538d") # Vignette section frame
        self.vignette_frame.pack(fill="x", padx=10, pady=2)
        
        self.vignette_open = False # Vignette state variables
        self.vignette_arrow = "▶"
        
        self.vignette_header_btn = ctk.CTkButton( # Vignette header button
            self.vignette_frame,
            text=f"{self.vignette_arrow} Vignette",
            height=35,
            font=("Segoe UI", 14, "bold"),
            command=self.toggle_vignette,
            fg_color="#1f538d",
            text_color="white",
            hover_color="#1f538d"
        )
        self.vignette_header_btn.pack(fill="x", padx=3)
        
        self.vignette_content = ctk.CTkFrame(self.vignette_frame, fg_color="#1f538d") # Vignette content frame
        
        vignette_strength_frame = ctk.CTkFrame(self.vignette_content, fg_color="#1f538d") # Vignette strength control
        vignette_strength_frame.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(vignette_strength_frame, text="Level:", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.vignette_slider = ctk.CTkSlider(
            vignette_strength_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            width=150,
            command=self.update_vignette_preview ,
            button_color="#2b2b2b"
        )
        self.vignette_slider.set(0)
        self.vignette_slider.pack(side="left", padx=(10, 0))
        self.vignette_value_label = ctk.CTkLabel(vignette_strength_frame, text="50", font=("Segoe UI", 14, "bold"))
        self.vignette_value_label.pack(side="left", padx=(10, 0))
        
        denoise_btn = ctk.CTkButton( # Denoise button
            self.adjust_content, 
            text="Denoise", 
            height=35,
            font=("Segoe UI", 14, "bold"),
            fg_color="#1f538d",
            hover_color="#2a63a5",
            text_color="white",
            command=self.apply_denoise
        )
        denoise_btn.pack(fill="x", padx=10, pady=2)

        self.adjust_apply_btn = ctk.CTkButton( # Apply all adjustments button
            self.adjust_content, 
            height=35, 
            text="Apply Adjustments", 
            font=("Segoe UI", 14, "bold"),
            fg_color="#1f538d", 
            text_color="white", 
            hover_color="#2a63a5",
            command=self.apply_all_adjustments
        )
        self.adjust_apply_btn.pack(fill="x", padx=10, pady=(2, 10))
        # Connect sliders to preview functions
        self.sharpness_slider.configure(command=self.update_sharpness_preview)
        self.brightness_slider.configure(command=self.update_brightness_preview)
        self.darkness_slider.configure(command=self.update_darkness_preview)
        self.vignette_slider.configure(command=self.update_vignette_preview)

        self.preview_image = None # Initialize preview variables
        self.is_previewing = False
#----------------------------------------------------------------------------------------------------------------------------------------------//

#------------------------------------ Function  to Update Sharpness Preview ------------------------------//
    def update_sharpness_preview(self, value): # Update sharpness preview
        self.update_sharpness_label(value)
        if self.image is not None:
            self.history[self.history_index].copy()  # Get current image from history

            strength = float(value) / 50.0 # Calculate sharpness strength
            
            laplacian_kernel = np.array([ # Laplacian kernel for edge detection
                [0, 1, 0],
                [1, -4, 1],
                [0, 1, 0]
            ])
            
            laplacian = cv.filter2D(self.image, -1, laplacian_kernel) # Apply Laplacian filter
            
            img_float = self.image.astype(np.float32)
            laplacian_float = laplacian.astype(np.float32)
            
            preview_img = img_float + strength * laplacian_float # Sharpen: original + strength * edges
            
            preview_img = np.clip(preview_img, 0, 255).astype(np.uint8)
            
            self.preview_image = preview_img # Store preview and update display
            self.update_image_display()
#---------------------------------------------------------------------------------------------------------//

#--------------------------------- Function  to Update Brightness Preview ------------------------------//
    def update_brightness_preview(self, value):
        self.update_brightness_label(value)
        if self.image is not None:
            self.history[self.history_index].copy()  # Get current image from history

            brightness_factor = float(value) # Calculate brightness adjustment
            add_val = int(50 * (brightness_factor / 100.0)) 
            preview_img = cv.add(self.image, add_val) # Apply brightness (Using arithmetic cv.add())
            preview_img = np.clip(preview_img, 0, 255)
            
            self.preview_image = preview_img # Store preview and update display
            self.update_image_display()
#-------------------------------------------------------------------------------------------------------//

#------------------------------------------------- Function  to Update Darkness Preview -------------------------------------------//
    def update_darkness_preview(self, value): # Update darkness preview
        self.update_darkness_label(value)
        if self.image is not None:
            self.history[self.history_index].copy() # Get current image from history

            darken_factor = float(value) / 100.0 # Calculate darkness factor (0-1)
            preview_img = cv.multiply(self.image, darken_factor) # Apply darkness (Using arithmetic (cv.multiply()))
            preview_img = np.clip(preview_img, 0, 255).astype(np.uint8)
            
            self.preview_image = preview_img # Store preview and update display
            self.update_image_display()
#---------------------------------------------------------------------------------------------------------------------------------//

#------------------------------------ Function  to Update Vignette Preview ------------------------------//
    def update_vignette_preview(self, value): # Update vignette preview
        self.update_vignette_label(value) # Update label
        
        if self.image is not None and self.vignette_img is not None:
            self.history[self.history_index].copy() # Get current image from history
            
            strength = float(value) / 100.0  # Calculate vignette strength
            
            h, w = self.image.shape[:2] # Get image dimensions
            
            vignette_resized = cv.resize(self.vignette_img, (w, h)) # Resize vignette to match image
            
            img_float = self.image.astype(np.float32)
            vignette_float = vignette_resized.astype(np.float32)
            
            preview_img = cv.addWeighted(img_float, 1 - strength, vignette_float, strength, 0)
            
            preview_img = np.clip(preview_img, 0, 255).astype(np.uint8)
            
            self.preview_image = preview_img # Store preview and update display
            self.update_image_display()
#-------------------------------------------------------------------------------------------------------//

#--------------------------------- Function to Adjust Section Visibility -------------------------------//
    def toggle_adjust(self): # Toggle adjust section visibility
        self.adjust_open = not self.adjust_open
        arrow = "▼" if self.adjust_open else "▶"
        self.adjust_header_btn.configure(text=f"{arrow} Adjust")
        
        if self.adjust_open: # Show/hide content
            self.adjust_content.pack(fill="x", padx=10, pady=(5, 10))
        else:
            self.adjust_content.pack_forget()
#-------------------------------------------------------------------------------------------------------//

#------------------------------- Function to Update Label ----------------------------------------------//
    def update_sharpness_label(self, value): # Update sharpness value label
        self.sharpness_value_label.configure(text=str(int(float(value))))
    
    def update_brightness_label(self, value): # Update brightness value label
        self.brightness_value_label.configure(text=str(int(float(value))))
    
    def update_darkness_label(self, value): # Update darkness value label
        self.darkness_value_label.configure(text=str(int(float(value))))
    
    def update_vignette_label(self, value):  # Update vignette value label
        self.vignette_value_label.configure(text=str(int(float(value))))
#-------------------------------------------------------------------------------------------------------//

#---------------------------------------------------------- Fuction to Apply Denoise to Image --------------------------------------------------------------//
    def apply_denoise(self): # Apply denoising to image
        if self.image is None:
            return
        
        img_median = cv.medianBlur(self.image, 5) # Median blur for noise reduction
        
        img_gaussian = cv.GaussianBlur(img_median, (3, 3), 1) # Gaussian blur for smoothing
        
        blurred = cv.GaussianBlur(img_gaussian, (7, 7), 3) # Additional blur for unsharp masking
        
        A = 2.0 # Unsharp masking parameters
        
        sharpened = cv.addWeighted(img_gaussian, A, blurred, -0.9, 0) # Unsharp masking: original + amount * (original - blurred)
         
        denoised_img = np.clip(sharpened, 0, 255).astype(np.uint8) # Final result
        
        self.add_to_history(denoised_img) # Add to history

        if self.layers: #Update base leyer
            self.layers[0].image = denoised_img.copy()
            self.layers[0].original_image = denoised_img.copy()
#-----------------------------------------------------------------------------------------------------------------------------------------------------------//

#------------------------------------------------ Function to Apply Adjustment ------------------------------------------------------//
    def apply_all_adjustments(self): # Apply all selected adjustments
        if self.image is None:
            return
        
        result = self.history[self.history_index].copy()  # Start with current image
        
        sharpness_val = self.sharpness_slider.get() # Apply sharpness (using laplacian filter)
        if sharpness_val != 50:
            strength = sharpness_val / 50.0  
            
            laplacian_kernel = np.array([ # Laplacian kernel for edge detection
                [0, 1, 0],
                [1, -4, 1],
                [0, 1, 0]
            ])
            
            laplacian = cv.filter2D(result, -1, laplacian_kernel) # Apply Laplacian
            
            img_float = result.astype(np.float32) # Convert to float for arithmetic
            laplacian_float = laplacian.astype(np.float32)
            
            sharpened = img_float + strength * laplacian_float # Sharpen: original + strength * edges
            
            result = np.clip(sharpened, 0, 255).astype(np.uint8)
        
        brightness_val = self.brightness_slider.get()  # Apply brightness (using arithmetic - cv.add())
        if brightness_val != 0:
            add_val = int(50 * (brightness_val / 100.0)) 
            result = cv.add(result, add_val)
            result = np.clip(result, 0, 255) # Ensure valid range

        darkness_val = self.darkness_slider.get() # Apply darkness (using arithmetic - cv.multiply)
        if darkness_val != 0:
            darken_factor = darkness_val / 100.0
            result = cv.multiply(result, darken_factor)
            result = np.clip(result, 0, 255).astype(np.uint8)
        
        vignette_val = self.vignette_slider.get()  # Apply vignette (using arithmetic - addition of another image)
        if vignette_val != 50 and self.vignette_img is not None:
            strength = vignette_val / 100.0
            
            h, w = result.shape[:2] # Get image dimension
            
            vignette_resized = cv.resize(self.vignette_img, (w, h)) # Resize vignette
            
            img_float = result.astype(np.float32)  # Convert to float for blending
            vignette_float = vignette_resized.astype(np.float32)
            
            result = cv.addWeighted(img_float, 1 - strength, vignette_float, strength, 0)
            result = np.clip(result, 0, 255).astype(np.uint8)
        
        self.add_to_history(result) # Save image to history
        
        
        if self.layers: # Update base layer
            self.layers[0].image = result.copy()
            self.layers[0].original_image = result.copy()
        
        self.preview_image = None #Clear preview
        
        self.sharpness_slider.set(0) # Reset slider to default
        self.brightness_slider.set(0)
        self.darkness_slider.set(100)
        self.vignette_slider.set(0)
        
        self.update_image_display()
#---------------------------------------------------------------------------------------------------------------------------------//

#------------------------------- Function to Open Sharpness Dropdown ------------------------------------//
    def toggle_sharpness(self): # Open brightness dropdown section
        self.sharpness_open = not self.sharpness_open
        arrow = "▼" if self.sharpness_open else "▶"
        self.sharpness_header_btn.configure(text=f"{arrow} Sharpness")
        
        if self.sharpness_open: # Show/Hide content
            self.sharpness_content.pack(fill="x", pady=(0, 5))
        else:
            self.sharpness_content.pack_forget()
#-------------------------------------------------------------------------------------------------------//

#------------------------------ Function to Open Brightness Dropdown ------------------------------------//
    def toggle_brightness(self): # Open brightness dropdown section
        self.brightness_open = not self.brightness_open
        arrow = "▼" if self.brightness_open else "▶"
        self.brightness_header_btn.configure(text=f"{arrow} Brightness")
        
        if self.brightness_open: # Show/Hide content
            self.brightness_content.pack(fill="x", pady=(0, 5))
        else:
            self.brightness_content.pack_forget()
#-------------------------------------------------------------------------------------------------------//

#------------------------------ Function to Open Darkness Dropdown --------------------------------------//
    def toggle_darkness(self): # Open darkness dropdown section
        self.darkness_open = not self.darkness_open
        arrow = "▼" if self.darkness_open else "▶"
        self.darkness_header_btn.configure(text=f"{arrow} Darkness")
        
        if self.darkness_open: # Show/Hide content
            self.darkness_content.pack(fill="x", pady=(0, 5))
        else:
            self.darkness_content.pack_forget()
#-------------------------------------------------------------------------------------------------------//

#------------------------------ Function to Open Vignette Dropdown --------------------------------------//
    def toggle_vignette(self):
        self.vignette_open = not self.vignette_open # Open vignette dropdown section
        arrow = "▼" if self.vignette_open else "▶"
        self.vignette_header_btn.configure(text=f"{arrow} Vignette")
        
        if self.vignette_open: # Show/Hide content
            self.vignette_content.pack(fill="x", pady=(0, 5))
        else:
            self.vignette_content.pack_forget()
#-------------------------------------------------------------------------------------------------------//

#--------------------------------- Function to Update Image Display ------------------------------------//
    def update_image_display(self): # Add image to displayed on GUI
        if self.image is None:
            return
    
        if hasattr(self, 'preview_image') and self.preview_image is not None:
            display_img = self.preview_image.copy()
        else:
            display_img = self.image.copy()
        
        img_pil = Image.fromarray(display_img)
        self.original_size = img_pil.size # Store original size
        
        img_pil.thumbnail((800, 600)) # Max display size
        
        self.tk_image = ctk.CTkImage(img_pil, size=img_pil.size)
        self.image_label.configure(image=self.tk_image)
#--------------------------------------------------------------------------------------------------------//

#------------------------------------ Function to Add Image to History ----------------------------------//
    def add_to_history(self, new_image): # Add image to history for redo and undo
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        self.history.append(new_image.copy()) # Add new image and update index
        self.history_index += 1
        self.image = new_image
        self.update_image_display()
#--------------------------------------------------------------------------------------------------------//

#--------------------------------------- Function to Undo Image -----------------------------------------//
    def undo(self): # Undo last operation
        if self.history_index > 0:
            self.history_index -= 1
            self.image = self.history[self.history_index]

            if self.layers: # Update base layer
                self.layers[0].image = self.image.copy()
                self.layers[0].original_image = self.image.copy()
            self.update_image_display()
#-------------------------------------------------------------------------------------------------------//

#--------------------------------------- Function to Redo Image -----------------------------------------//
    def redo(self): # Redo last undone operation
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.image = self.history[self.history_index]

            if self.layers: # Update base layer
                self.layers[0].image = self.image.copy()
                self.layers[0].original_image = self.image.copy()
            self.update_image_display()
#--------------------------------------------------------------------------------------------------------//

#--------------------------------------- Function to Reset Image -----------------------------------------//
    def reset(self):
        if self.history: # Reset image to original state
            self.history_index = 0
            self.image = self.history[0]

            if self.layers: # Update base layers
                self.layers[0].image = self.image.copy()
                self.layers[0].original_image = self.image.copy()

            if len(self.layers) > 1: # Remove overlay layers
                self.layers = [self.layers[0]]
                self.selected_layer_index = 0
                self.editing_layer_index = -1
            self.update_image_display()
#-------------------------------------------------------------------------------------------------------//

#------------------------------------- Function to Save Image ------------------------------------------//
    def save_image(self):
        path = filedialog.asksaveasfilename( # Save to file
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")]
        )
        if path and self.image is not None:
            img_bgr = cv.cvtColor(self.image, cv.COLOR_RGB2BGR) # Convert RGB to BGR for OpenCV
            cv.imwrite(path, img_bgr) # Save image
#-------------------------------------------------------------------------------------------------------//

#--------------------------------------------- Main ----------------------------------------------------//
if __name__ == "__main__":
    app = PhotoEditorApp()
    app.iconbitmap("logo.ico") # Window icon
    app.mainloop() # GUI loop
#-------------------------------------------------------------------------------------------------------//