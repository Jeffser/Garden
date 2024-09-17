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
import os, shutil, re
from zipfile import ZipFile
from .custom_widgets import shimeji_widget

@Gtk.Template(resource_path='/com/jeffser/Garden/window.ui')
class GardenWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'GardenWindow'

    shimeji_container = Gtk.Template.Child()
    shimeji_scroller = Gtk.Template.Child()
    searchbar = Gtk.Template.Child()
    window_stack = Gtk.Template.Child()

    @Gtk.Template.Callback()
    def closing_app(self, user_data):
        if not self.get_hide_on_close():
            for shime_group in list(self.shimeji_container):
                for shime in shime_group.get_child().shime_list:
                    shime.stop()
            self.get_application().quit()

    @Gtk.Template.Callback()
    def search_changed(self, entry):
        results=0
        for shime_group in list(self.shimeji_container):
            if re.search(entry.get_text(), shime_group.get_child().get_name(), re.IGNORECASE):
                shime_group.set_visible(True)
                results+=1
        if results==0 and entry.get_text():
            self.window_stack.set_visible_child_name('no_results')
        elif len(list(self.shimeji_container)) == 0:
            self.window_stack.set_visible_child_name('empty')
        else:
            self.window_stack.set_visible_child_name('normal')


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
                    else:
                        for file in os.listdir(os.path.join(old_dir, 'img')):
                            shutil.move(os.path.join(old_dir, 'img', file), os.path.join(new_dir, 'img'))

                    if not os.path.isfile(os.path.join(new_dir, 'img', 'icon.png')):
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
                    self.window_stack.set_visible_child_name('normal')


    def add_shimeji_selector(self, shime_name:str):
        try:
            if not os.path.isfile(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji', shime_name, 'Shimeji.jar')):
                raise FileNotFoundError
            shime_sel = shimeji_widget.shimeji_selector(shime_name, self)
        except Exception as e:
            print(e)
            return
        self.shimeji_container.append(shime_sel)
        shime_sel.get_parent().set_valign(1)
        shime_sel.get_parent().set_focusable(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        shimeji_widget.window=self
        if not os.path.isdir(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji')):
            os.makedirs(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji'))
        drop_target=Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect('drop', self.on_file_drop)
        self.window_stack.add_controller(drop_target)
        for shime in os.listdir(os.path.join(os.environ['XDG_DATA_HOME'], 'shimeji')):
            self.add_shimeji_selector(shime)
        if len(list(self.shimeji_container)) == 0:
            self.window_stack.set_visible_child_name('empty')

