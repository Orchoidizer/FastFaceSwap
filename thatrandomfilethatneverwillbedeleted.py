from tkinter import ttk, Tk
from PIL import Image, ImageTk
import tkinter as tk
class AutoScroll(object):
    '''Configure the scrollbars for a widget.'''
    def __init__(self, master):
        try:
            vsb = ttk.Scrollbar(master, orient='vertical', command=self.yview)
        except:
            pass
        hsb = ttk.Scrollbar(master, orient='horizontal', command=self.xview)
        try:
            self.configure(yscrollcommand=self._autoscroll(vsb))
        except:
            pass
        self.configure(xscrollcommand=self._autoscroll(hsb))
        self.grid(column=0, row=0, sticky='nsew')
        try:
            vsb.grid(column=1, row=0, sticky='ns')
        except:
            pass
        hsb.grid(column=0, row=1, sticky='ew')
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)

    @staticmethod
    def _autoscroll(sbar):
        '''Hide and show scrollbar as needed.'''
        def wrapped(first, last):
            first, last = float(first), float(last)
            if first <= 0 and last >= 1:
                sbar.grid_remove()
            else:
                sbar.grid()
            sbar.set(first, last)
        return wrapped

class ScrolledListBox(AutoScroll, tk.Canvas):
    def __init__(self, master, **kw):
        tk.Canvas.__init__(self, master, **kw)
        AutoScroll.__init__(self, master)
        self.image_cache = {}
        self.original_images = {}
        self.data_list = []
        self.bind('<Configure>', self._update_layout)
        self.bind("<MouseWheel>", self.scroll)
        self.min_canvas_width = 220  
        self.spacing = 10  

    def _update_layout(self, event):
        canvas_width = self.winfo_width()
        if canvas_width < self.min_canvas_width:
            return

        self.delete('all')
        total_height = 0
        half_canvas_width = canvas_width // 2

        for i, data in enumerate(self.data_list):
            text, image = data

            if i not in self.original_images:
                self.original_images[i] = image.copy()

            aspect_ratio = image.width / image.height
            max_width = max(1, half_canvas_width - 30)
            max_height = max_width / aspect_ratio
            image = image.resize((int(max_width), int(max_height)))
            image_tk = ImageTk.PhotoImage(image)

            y_offset = total_height + (i * self.spacing)
            total_height += max_height + self.spacing

            # Create a bounding rectangle around the entire item (image + text combo)
            bounding_rect = self.create_rectangle(0, y_offset, canvas_width, y_offset + max_height + self.spacing, fill='', outline='')
            
            
            # This ensures the bounding rectangle is always at the top layer
            self.tag_lower(bounding_rect)
            
            # Bind the clickable rectangle to the click event

            text_id = self.create_text(half_canvas_width // 2, y_offset + max_height // 2, anchor='center', text=text)
            image_id = self.create_image(half_canvas_width + (half_canvas_width // 2), y_offset + max_height // 2, anchor='center', image=image_tk)
            # Create the clickable rectangle
            clickable_rect = self.create_rectangle(0, y_offset, canvas_width, y_offset + max_height + self.spacing, fill='', outline='')
            self.tag_bind(clickable_rect, '<Button-1>', lambda event, idx=i: self._on_item_click(event, idx))

            self.image_cache[i] = (text_id, image_id, image_tk, bounding_rect, clickable_rect)

        self.config(scrollregion=self.bbox("all"))



    def _on_item_click(self, event, idx):
        if hasattr(self, 'highlighted_rect'):
            self.itemconfig(self.highlighted_rect, fill='')  # Clear the previous highlight by setting its fill to empty
        
        # Highlight the bounding rectangle associated with the clicked item
        self.highlighted_rect = self.image_cache[idx][3]
        self.itemconfig(self.highlighted_rect, fill='blue')

        self.selected_index = idx  # Store the actual data index
        print(idx)  # print the index of the clicked item

    def reset_images(self):
        for i, image in self.original_images.items():
            self.data_list[i][1] = image
        self._update_layout(None)

    def insert_data(self, data_list):
        self.data_list = data_list
        self.original_images.clear()
        self._update_layout(None)

    def add_item(self, text, image):
        """Add a new item (text and image) to the list and update the display."""
        self.data_list.append([text, image])
        self._update_layout(None)
    def scroll(self, event):
        self.yview_scroll(-1*(event.delta//120), "units")

    def delete_by_id(self, idx):
        """Delete an item by its index."""
        if idx < 0 or idx >= len(self.data_list):
            raise ValueError("Index out of range.")
        
        # Remove the item from data_list
        del self.data_list[idx]
        
        # Remove the item from original_images, image_cache, and the canvas
        if idx in self.original_images:
            del self.original_images[idx]
        if idx in self.image_cache:
            text_id, image_id, image_tk, bounding_rect, clickable_rect = self.image_cache[idx]
            self.delete(text_id)
            self.delete(image_id)
            self.delete(bounding_rect)
            self.delete(clickable_rect)
            del self.image_cache[idx]
        
        # Adjust the keys in original_images and image_cache
        keys_original = sorted(list(self.original_images.keys()))
        keys_cache = sorted(list(self.image_cache.keys()))
        
        for key in keys_original:
            if key > idx:
                self.original_images[key-1] = self.original_images[key]
                del self.original_images[key]
        
        for key in keys_cache:
            if key > idx:
                self.image_cache[key-1] = self.image_cache[key]
                del self.image_cache[key]
        
        # Redraw the items
        self._update_layout(None)

    def delete_all(self):
        """Delete all items from the list and update the display."""
        self.data_list.clear()  # Clear the data list
        self.original_images.clear()  # Clear the original images dictionary
        self.image_cache.clear()  # Clear the image cache dictionary
        self.delete('all')  # Remove all canvas items
    def delete_selected(self):
        if hasattr(self, 'selected_index'):
            self.delete_by_id(self.selected_index)
            delattr(self, 'selected_index')

    def get_selected_id(self):
        """Retrieve the ID of the currently selected item."""
        if hasattr(self, 'selected_index'):
            return self.selected_index
        else:
            return None  # No item is currently selected