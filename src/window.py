# window.py
#
# Copyright 2024 Jeffry Samuel Eduarte Rojas
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk, Gdk
import os, threading, uuid, shutil, time, subprocess, re
from colorthief import ColorThief
from zipfile import ZipFile

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

@Gtk.Template(resource_path='/com/jeffser/Garden/window.ui')
class GardenWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'GardenWindow'

    shimeji_container = Gtk.Template.Child()
    shimeji_scroller = Gtk.Template.Child()
    searchbar = Gtk.Template.Child()

    @Gtk.Template.Callback()
    def closing_app(self, user_data):
        if not self.get_hide_on_close():
            for shime_group in list(self.shimeji_container):
                for shime in shime_group.get_child().shime_list:
                    shime.stop()
            self.get_application().quit()

    @Gtk.Template.Callback()
    def search_changed(self, entry):
        for shime_group in list(self.shimeji_container):
            shime_group.set_visible(re.search(entry.get_text(), shime_group.get_child().get_name(), re.IGNORECASE))

    @Gtk.Template.Callback()
    def search_toggle(self, button):
        self.searchbar.set_search_mode(button.get_active())

    def on_file_drop(self, drop_target, value, x, y):
        for file in value.get_files():
            extension=os.path.splitext(file.get_path())[1][1:]
            if extension == 'zip':
                with ZipFile(file.get_path(), 'r') as zf:
                    if os.path.isdir(os.path.join(os.environ['XDG_CACHE_HOME'], 'new_shimeji')):
                        shutil.rmtree(os.path.join(os.environ['XDG_CACHE_HOME'], 'new_shimeji'))
                    zf.extractall(os.path.join(os.environ['XDG_CACHE_HOME'], 'new_shimeji'))

                    shime_name=os.listdir(os.path.join(os.environ['XDG_CACHE_HOME'], 'new_shimeji'))[0]

                    old_dir=os.path.join(os.environ['XDG_CACHE_HOME'], 'new_shimeji', shime_name)
                    new_dir=os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji', shime_name)
                    os.makedirs(new_dir)
                    os.makedirs(os.path.join(new_dir, 'img'))

                    if os.path.isdir(os.path.join(old_dir, 'img', 'Shimeji')):
                        for image in os.listdir(os.path.join(old_dir, 'img', 'Shimeji')):
                            shutil.move(os.path.join(old_dir, 'img', 'Shimeji', image), os.path.join(new_dir, 'img'))
                        shutil.move(os.path.join(old_dir, 'img', 'icon.png'), os.path.join(new_dir, 'img'))

                    custom_conf=False
                    if custom_conf:
                        os.makedirs(os.path.join(new_dir, 'conf'))
                        shutil.copyfile('/app/shimeji/conf/logging.properties', os.path.join(new_dir, 'conf', 'logging.properties'))
                        shutil.copyfile('/app/shimeji/conf/Mascot.xsd', os.path.join(new_dir, 'conf', 'Mascot.xsd'))

                        os.system('sed -f /app/shimeji/conf/conv.sed "{}" > "{}"'.format(os.path.join(old_dir, 'conf', 'actions.xml'), os.path.join(new_dir, 'conf', 'Actions.xml')))
                        os.system('sed -f /app/shimeji/conf/conv.sed "{}" > "{}"'.format(os.path.join(old_dir, 'conf', 'behaviors.xml'), os.path.join(new_dir, 'conf', 'Behavior.xml')))
                    else:
                        shutil.copytree('/app/shimeji/conf', os.path.join(new_dir, 'conf'))

                    shutil.copyfile('/app/shimeji/Shimeji.jar', os.path.join(new_dir, 'Shimeji.jar'))
                    os.symlink('/app/shimeji/lib', os.path.join(new_dir, 'lib'))

                    shutil.rmtree(os.path.join(os.environ['XDG_CACHE_HOME'], 'new_shimeji'))

                    self.add_shimeji_selector(shime_name)


    def add_shimeji_selector(self, shime_name:str):
        shime_sel = shimeji_selector(shime_name, self)
        self.shimeji_container.append(shime_sel)
        shime_sel.get_parent().set_valign(1)
        shime_sel.get_parent().set_focusable(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        drop_target=Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect('drop', self.on_file_drop)
        self.shimeji_scroller.add_controller(drop_target)
        for shime in os.listdir(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji')):
            self.add_shimeji_selector(shime)

