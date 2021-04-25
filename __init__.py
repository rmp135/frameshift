bl_info = {
    "name": "FrameShift",
    "author": "Ryan Poole",
    "version": (1, 1, 0),
    "blender": (2, 92, 0),
    "description": "Keyframe shifting tools",
    "category": "Animation"
}


import bpy
from math import *
from bpy.types import Operator, PropertyGroup, Panel, Scene, Operator
from bpy.props import IntProperty, BoolProperty, StringProperty, EnumProperty

# Props
class FSProps(PropertyGroup):
    frame_count: IntProperty(name="Frame Count", description="Number of frames to shift by", default=1, min=0)
    repeat_offset: IntProperty(name="Repeat Offset", description="Number of frames to offset the repeat", default=0, min=0)
    repeat_count: IntProperty(name="Repeat Count", description="Number of times to repeat", default=1, min=1)
    keyframe_options: EnumProperty(
        name= "Keyframe Options",
        description= "Where to add keyframes",
        items= [
            ("BOTH", "Start and End", "Add keyframes at the start and end"),
            ("START", "Start Only", "Only add initial keyframe"),
            ("NONE", "None", "Do not add keyframes, only move existing"),
        ]
    )

# Panels
class SharedPanel(Panel):
    def draw(self, context):
        props = context.scene.fs_props
        layout = self.layout

        shift_box = layout.box()
        row = shift_box.row()
        row.label(text="Shift")
        row = shift_box.row()
        row.prop(props, "frame_count")
        row = shift_box.row()
        row.label(text="Insert Keyframes At:")
        row = shift_box.row()
        row.prop(props, "keyframe_options", text="")

        row = shift_box.row()
        row.operator("fshift.shift", text="Shift")

        repeat_box = layout.box()
        row = repeat_box.row()
        row.label(text="Repeat")
        row = repeat_box.row()
        row.prop(props, "repeat_offset")
        row = repeat_box.row()
        row.prop(props, "repeat_count")
        row = repeat_box.row()
        row.operator("fshift.repeat", text="Repeat")

        merge_box = layout.box()
        row = merge_box.row()
        row.label(text="Merge")
        row = merge_box.row()
        row.operator("fshift.merge", text="First").mode="FIRST"
        row.operator("fshift.merge", text="Center").mode="CENTER"
        row.operator("fshift.merge", text="Last").mode="LAST"

        row = merge_box.row()
        row.operator("fshift.merge", text="Cursor").mode="CURSOR"

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
class RepeatOp(bpy.types.Operator):
    bl_idname = "fshift.repeat"
    bl_label = "RepeatOp"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        props = context.scene.fs_props
        for i in range(props.repeat_count):
            selected_keys = []

            # Collect selected frames
            for obj in [o for o in bpy.context.scene.objects if o.animation_data is not None]:
                for fc in obj.animation_data.action.fcurves:
                    for key in fc.keyframe_points:
                        if (key.select_control_point): # is selected
                            selected_keys.append((fc, key))
            if len(selected_keys) == 0:
                ShowMessageBox("No keyframes are selected.", "No selection.", "ERROR")
                return {'FINISHED'}

            # Get frame range
            earliest_frame = min([s[1].co[0] for s in selected_keys])
            last_frame = max([s[1].co[0] for s in selected_keys])

            # Move future frames
            for obj in [o for o in bpy.context.scene.objects if o.animation_data is not None]:
                for fc in obj.animation_data.action.fcurves:
                    for key in reversed(fc.keyframe_points):
                        if key.co[0] >  last_frame:
                            key.co[0] = key.co[0] + last_frame - earliest_frame + props.repeat_offset
                            fc.update()
            
            bpy.ops.action.duplicate_move(
                TRANSFORM_OT_transform={
                    "value":(last_frame - earliest_frame + props.repeat_offset, 0, 0, 0),
                }
            )
        return {'FINISHED'}


class MergeOp(Operator):
    bl_idname = 'fshift.merge'
    bl_label = 'Merge'
    bl_options = {'INTERNAL'}
    mode: StringProperty()

    def execute(self, context):
        selected_keys = []

        for obj in [o for o in bpy.context.selected_objects if o.animation_data is not None and o.animation_data.action is not None]:
            fcurves = obj.animation_data.action.fcurves
            for fc in fcurves:
                for key in fc.keyframe_points:
                    if (key.select_control_point): # is selected
                        selected_keys.append((fc, key))
        if len(selected_keys) == 0:
            ShowMessageBox("No keyframes are selected.", "No selection.", "ERROR")
            return

        active_frame = bpy.context.scene.frame_current
        earliest_frame = min([s[1].co[0] for s in selected_keys])
        last_frame = max([s[1].co[0] for s in selected_keys])
        
        if self.mode == "FIRST":
            active_frame = earliest_frame
        if self.mode == "LAST":
            active_frame = last_frame
        if self.mode == "CENTER":
            active_frame = floor((earliest_frame + last_frame) / 2)
        frame = bpy.context.scene.frame_current
        bpy.context.scene.frame_set(active_frame)
        bpy.ops.transform.transform(
            mode='TIME_SCALE',
            value=(0, 0, 0, 0)
        )
        bpy.context.scene.frame_set(frame)

        return {'FINISHED'}


class ShiftOp(Operator):
    bl_idname = 'fshift.shift'
    bl_label = 'Insert'
    bl_options = {'INTERNAL'}
    
    def execute(self, context): 
        props = context.scene.fs_props
        objs = bpy.context.selected_objects

        for obj in [o for o in objs if o.animation_data is not None]:
            fcurves = obj.animation_data.action.fcurves
            for fc in fcurves:
                for key in reversed(fc.keyframe_points):
                    if key.co[0] > bpy.context.scene.frame_current:
                        key.co[0] = key.co[0] + props.frame_count
                        fc.update()
            if not props.keyframe_options == "NONE":
                for fc in fcurves:
                    obj.keyframe_insert(data_path=fc.data_path, options={'INSERTKEY_AVAILABLE'})
                    if props.keyframe_options == "BOTH":
                        obj.keyframe_insert(data_path=fc.data_path, frame=bpy.context.scene.frame_current+props.frame_count, options={'INSERTKEY_AVAILABLE'})
        return {'FINISHED'}

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


classes = [
    FSProps,
    ShiftOp,
    RepeatOp,
    MergeOp,
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
