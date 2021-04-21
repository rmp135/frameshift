bl_info = {
    "name": "FrameShift",
    "author": "Ryan Poole",
    "version": (1, 0, 0),
    "blender": (2, 92, 0),
    "description": "Keyframe shifting tools",
    "category": "Animation"
}


import bpy
from bpy.types import Operator, PropertyGroup


class FSProps(PropertyGroup):
    frame_count: bpy.props.IntProperty(name="Frame Count", description="Number of frames to shift by.", default=1, min=1)
    skip_insert: bpy.props.BoolProperty(name='Skip Insert', description="Do not insert keyframes, only move existing ones.", default=False)
    initial_keyframe_only: bpy.props.BoolProperty(name='Start Keyframe Only', description="Only insert a start keyframe Do not insert keyframes, only move existing ones.", default=False)

class FrameShiftPanel(bpy.types.Panel):
    bl_label = "FrameShift"
    bl_idname = "DOPESHEET_PT_frameshift_panel"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        access = context.scene.fs_props
        layout = self.layout
        obj = context.object

        row = layout.row()
        row.prop(access, "frame_count")

        row = layout.row()
        row.prop(access, "skip_insert")

        row = layout.row()
        row.operator("fshift.shift", text="Shift")

class ShiftOp(bpy.types.Operator):
    bl_idname = 'fshift.shift'
    bl_label = 'Insert'
    bl_options = {'INTERNAL'}
    
    def execute(self, context): 
        access = context.scene.fs_props
        objs = bpy.context.selected_objects

        for obj in objs:
            if obj.animation_data == None:
                continue
            fcurves = obj.animation_data.action.fcurves
            for fc in fcurves:
                for key in fc.keyframe_points:
                    if key.co[0] > bpy.context.scene.frame_current:
                        key.co[0] = key.co[0] + access.frame_count
                        fc.update()
            if not access.skip_insert:
                for fc in fcurves:
                    obj.keyframe_insert(data_path=fc.data_path, options={'INSERTKEY_AVAILABLE'})
                    obj.keyframe_insert(data_path=fc.data_path, frame=bpy.context.scene.frame_current+access.frame_count, options={'INSERTKEY_AVAILABLE'})
        return {'FINISHED'}

def register():
    bpy.utils.register_class(ShiftOp)
    bpy.utils.register_class(FrameShiftPanel)
    bpy.utils.register_class(FSProps)

    bpy.types.Scene.fs_props = bpy.props.PointerProperty(type=FSProps)

def unregister():
    bpy.utils.unregister_class(FSProps)
    bpy.utils.unregister_class(FrameShiftPanel)
    bpy.utils.unregister_class(ShiftOp)


if __name__ == "__main__":
    register()
