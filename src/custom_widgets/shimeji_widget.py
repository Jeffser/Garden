
from gi.repository import Adw, Gtk, Gdk
from colorthief import ColorThief
import os, shutil, uuid, subprocess, threading

window=None

class shimeji:
    def __init__(self, shime_name:str):
        self.instance_id = str(uuid.uuid4())
        self.shime_name = shime_name

    def work(self):
        cmd = 'java -classpath Shimeji.jar -Xmx1000m com.group_finity.mascot.Main -Djava.util.logging.config.file=./conf/logging.properties'
        env = os.environ.copy()
        env['DISPLAY'] = ':0'
        working_directory = os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji', self.shime_name)

        process = subprocess.Popen(cmd, shell=True, cwd=working_directory, env=env)

        while not self.stop_event.is_set():
            if process.poll() is not None:
                break
            self.stop_event.wait(1)
        if process.poll() is None:
            process.terminate()
            process.wait()

    def start(self):
        self.stop_event = threading.Event()
        self.instance = threading.Thread(target=self.work)
        self.instance.start()

    def stop(self):
        self.stop_event.set()
        self.instance.join()

class shimeji_selector(Gtk.Box):
    __gtype_name__ = 'GardenShimejiSelector'

    def __init__(self, shime_name:str, window:Gtk.Window):
        self.window=window
        super().__init__(
            css_classes=["card", "shimeji_card"],
            name=shime_name,
            valign=1,
            orientation=1,
            spacing=10,
            tooltip_text=shime_name
        )
        self.main_color=ColorThief(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji', self.get_name(), 'img', 'shime1.png')).get_color(quality=5)
        self.main_color='rgb({},{},{})'.format(self.main_color[0], self.main_color[1], self.main_color[2])
        style_context=self.get_style_context()
        css_provider=Gtk.CssProvider()
        css_provider.load_from_data(f".shimeji_card {{\nbackground-color: mix({self.main_color}, @theme_bg_color, .8);\n}}".encode())
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self.shime_list=[]

        self.title_stack = Gtk.Stack(
            transition_type=1
        )
        self.append(self.title_stack)

        label_container=Gtk.Box(
            orientation=0,
            spacing=10
        )

        self.label=Gtk.Label(
            label=shime_name,
            ellipsize=3,
            can_focus=True,
            focus_on_click=True,
            halign=1,
            hexpand=True
        )
        gesture=Gtk.GestureClick.new()
        gesture.connect('pressed', lambda gesture, n_press, x, y: self.edit_title() if n_press==2 else None)
        self.label.add_controller(gesture)
        label_container.append(self.label)

        delete_button=Gtk.Button(
            icon_name='user-trash-symbolic',
            css_classes=['flat', 'circular']
        )
        delete_button.connect('clicked', self.ask_delete)
        label_container.append(delete_button)
        self.title_stack.add_named(label_container, 'title')

        title_entry=Gtk.Entry()
        title_entry.connect('activate', self.save_name)
        self.title_stack.add_named(title_entry, 'edit')

        self.image_stack = Gtk.Stack()
        self.append(self.image_stack)

        image=Gtk.Image.new_from_file(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji', self.get_name(), 'img', 'shime1.png'))
        image.set_size_request(100, 100)
        image2=Gtk.Image.new_from_file(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji', self.get_name(), 'img', 'shime1.png'))
        image2.set_size_request(100, 100)
        self.image_stack.add_named(image, '1')
        self.image_stack.add_named(image2, '2')

        spin_button=Gtk.SpinButton.new_with_range(0,10,1)
        spin_button.set_digits(0)
        spin_button.set_snap_to_ticks(True)
        spin_button.set_css_classes(["flat"])
        spin_button.connect('value-changed', self.value_changed)
        self.append(spin_button)

    def delete(self):
        for shime in self.shime_list:
            shime.stop()
        shutil.rmtree(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji', self.get_name()))
        self.get_parent().get_parent().remove(self)
        if len(list(window.shimeji_container)) == 0:
            window.window_stack.set_visible_child_name('empty')

    def ask_delete(self, button):
        dialog=Adw.AlertDialog(
            heading="Delete Shimeji",
            body="Are you sure you want to delete '{}'?".format(self.get_name()),
            close_response="cancel"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("delete")
        dialog.choose(
            parent=self.window,
            cancellable=None,
            callback=lambda dialog, task: self.delete() if dialog.choose_finish(task) == 'delete' else None
        )

    def save_name(self, entry):
        new_name=entry.get_buffer().get_text().replace('/', '')
        if new_name:
            if new_name != self.get_name():
                compare_list=os.listdir(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji'))
                if new_name in compare_list:
                    for i in range(len(compare_list)):
                        if "{} {}".format(new_name, i+1) not in compare_list:
                            new_name = "{} {}".format(new_name, i+1)
                            break
                os.rename(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji', self.get_name()), os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji', new_name))
                self.set_name(new_name)
                self.label.set_label(new_name)
                self.set_tooltip_text(new_name)
            self.title_stack.set_visible_child_name('title')

    def edit_title(self):
        self.title_stack.set_visible_child_name('edit')
        buffer = self.title_stack.get_visible_child().get_buffer()
        buffer.delete_text(0, -1)
        buffer.insert_text(0, self.get_name(), len(self.get_name()))
        self.title_stack.get_visible_child().grab_focus()

    def value_changed(self, spin_button):
        while spin_button.get_value() != len(self.shime_list):
            if spin_button.get_value() > len(self.shime_list):
                self.image_stack.set_transition_type(4)
                new_shime = shimeji(self.get_name())
                new_shime.start()
                self.shime_list.append(new_shime)
            elif spin_button.get_value() < len(self.shime_list):
                self.image_stack.set_transition_type(5)
                self.shime_list.pop(-1).stop()

            self.image_stack.set_visible_child_name('1' if self.image_stack.get_visible_child_name() == '2' else '2')
