from typing import Union, Set
from pathlib import Path
from glob import glob
from os.path import sep

import bpy
from bpy.props import CollectionProperty, FloatProperty, StringProperty, BoolProperty
from bpy.types import Operator, Context, Property, OperatorFileListElement, TOPBAR_MT_file_import
from bpy_extras.io_utils import ImportHelper
from io_import_pskx.blend.psw import ActorXWorld
from io_import_pskx.blend import nodes
from io_import_pskx.utils import log_info


def find_root_from_path(path: str):
    current_path = Path(path).parent.absolute()
    while True:
        root_files = glob(str(current_path) + sep + "*.root")
        if len(root_files) == 1:
            log_info('ACTORX', "Found root path %s" % str(current_path))
            if os.path.exists(f"{str(current_path)}/Content"):
                log_info('ACTORX', "Root is modern layout")
                return str(current_path) + '/Content'
            return str(current_path)
        if current_path.parent == current_path:
            return None
        current_path = current_path.parent


class op_import_psw(Operator, ImportHelper):
    bl_idname = 'import_scene.psw'
    bl_label = 'Import ActorX PSW'
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default='*.psw', options={'HIDDEN'})

    files: CollectionProperty(
            name='File Path',
            type=OperatorFileListElement,
    )

    resize_by: FloatProperty(
            name='Scale',
            description='Resize By',
            default=0.01,
            min=0.01,
            soft_max=10.0
    )

    adjust_intensity: FloatProperty(
            name='Light Power',
            description='Adjust Point Light Intensity By',
            default=0.05,
            min=0.0,
            soft_max=10.0
    )

    adjust_area_intensity: FloatProperty(
            name='Area Light Power',
            description='Adjust Area Light Intensity By',
            default=0.01,
            min=0.0,
            soft_max=10.0
    )

    adjust_spot_intensity: FloatProperty(
            name='Spot Light Power',
            description='Adjust Spot Light Intensity By',
            default=0.0025,
            min=0.0,
            soft_max=10.0
    )

    adjust_sun_intensity: FloatProperty(
            name='Sun Light Power',
            description='Adjust Directional Light Intensity By',
            default=0.001,
            min=0.0,
            soft_max=10.0
    )

    skip_offcenter: BoolProperty(
            name='Skip Invalid Tiles',
            description='Skips landscapes that are offset',
            default=True
    )

    base_game_dir: StringProperty(
            name='Asset Directory',
            description='If empty will try to walk directories to find it',
            default='',
            subtype='DIR_PATH'
    )

    def draw(self, context: Context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = True

        layout.prop(self, 'resize_by')
        layout.prop(self, 'adjust_intensity')
        layout.prop(self, 'adjust_area_intensity')
        layout.prop(self, 'adjust_spot_intensity')
        layout.prop(self, 'adjust_sun_intensity')
        layout.prop(self, 'skip_offcenter')
        layout.prop(self, 'base_game_dir')

    def execute(self, context: Context) -> Union[Set[str], Set[int]]:
        if len(self.base_game_dir) == 0:
            self.base_game_dir = find_root_from_path(self.filepath) or ''
            if len(self.base_game_dir) == 0:
                self.report({'ERROR'}, 'Did not select a game directory')
                return {'CANCELLED'}

        nodes.register()

        import os

        settings: dict[str, Property] = self.as_keywords()

        if self.files:
            dirname = os.path.dirname(self.filepath)
            ret = {'CANCELLED'}
            for file in self.files:
                path = os.path.join(dirname, file.name)
                if ActorXWorld(path, settings).execute(context) == {'FINISHED'}:
                    ret = {'FINISHED'}
            return ret
        else:
            return ActorXWorld(self.filepath, settings).execute(context)
