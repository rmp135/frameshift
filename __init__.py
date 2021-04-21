bl_info = {
    "name": "FrameShift",
    "author": "Ryan Poole",
    "version": (1, 0, 0),
    "blender": (2, 92, 0),
    "description": "Keyframe shifting tools",
    "category": "Animation"
}


import bpy
from bpy.types import Operator, PropertyGroup, Panel, Scene

# Props
class FSProps(PropertyGroup):
    frame_count: bpy.props.IntProperty(name="Frame Count", description="Number of frames to shift by", default=1, min=0)
    skip_insert: bpy.props.BoolProperty(name='Skip Insert', description="Do not insert keyframes, only move existing ones", default=False)
    initial_keyframe_only: bpy.props.BoolProperty(name='Initial Keyframe Only', description="Only insert the initial keyframe", default=False)

# Panels
class SharedPanel(Panel):
    def draw(self, context):
        props = context.scene.fs_props
        layout = self.layout

        row = layout.row()
        row.prop(props, "frame_count")

        row = layout.row()
        row.prop(props, "skip_insert")

        if not props.skip_insert:
            row = layout.row()
            row.prop(props, "initial_keyframe_only")
            row.enabled = not props.skip_insert

        row = layout.row()
        row.operator("fshift.shift", text="Shift")

class FrameShiftDopeSheetPanel(SharedPanel):
    bl_label = "FrameShift"
    bl_idname = "DOPESHEET_PT_frameshift_panel"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'


class FrameShiftFCurvesPanel(SharedPanel):
    bl_label = "FrameShift"
    bl_idname = "GRAPH_PT_frameshift_panel"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'

# Operators
class ShiftOp(bpy.types.Operator):
    bl_idname = 'fshift.shift'
    bl_label = 'Insert'
    bl_options = {'INTERNAL'}
    
    def execute(self, context): 
        props = context.scene.fs_props
        objs = bpy.context.selected_objects

        for obj in objs:
            if obj.animation_data == None:
                continue
            fcurves = obj.animation_data.action.fcurves
            for fc in fcurves:
                for key in fc.keyframe_points:
                    if key.co[0] > bpy.context.scene.frame_current:
                        key.co[0] = key.co[0] + props.frame_count
                        fc.update()
            if not props.skip_insert:
                for fc in fcurves:
                    obj.keyframe_insert(data_path=fc.data_path, options={'INSERTKEY_AVAILABLE'})
                    if not props.initial_keyframe_only:
                        obj.keyframe_insert(data_path=fc.data_path, frame=bpy.context.scene.frame_current+props.frame_count, options={'INSERTKEY_AVAILABLE'})
        return {'FINISHED'}

classes = [
    FSProps,
    ShiftOp,
    FrameShiftDopeSheetPanel,
    FrameShiftFCurvesPanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.fs_props = bpy.props.PointerProperty(type=FSProps)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
