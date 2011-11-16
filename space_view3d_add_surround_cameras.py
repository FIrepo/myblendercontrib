# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    'name': "Surround Projection Tools",
    'author': "Cole Ingraham",
    'location': "View3D > Tool Shelf > Surround Projection panel",
    'description': "Setup cameras and create rendering scenes for n-screen surround projection.",
    'wiki_url': "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/3D_interaction/Surround_Projection_Tools",
    'version': (0,1,1),
    'blender': (2, 6, 0),
    'api': 41769,
    'category': '3D View'
}

import bpy
from bpy.props import IntProperty
from bpy.props import BoolProperty
from math import pi
import re

# property for how many screens to add
bpy.types.WindowManager.num_surround_screens = IntProperty(
    name="Number of screens",
    description="How many screens to add",
    default=4,
    min=3)

# safeguard for removing previous cameras/scenes
bpy.types.WindowManager.previous_num_surround_screens = IntProperty(
    name="Previous number of screens",
    description="used for removing cameras/scenes",
    default=-1)

# used to enable/disable make/remove scenes and cameras
bpy.types.WindowManager.surround_screens_init = BoolProperty(
    name="SurroundScenesInit",
    default=False)

# GUI panel
class AddSurroundCamerasPanel(bpy.types.Panel):
   bl_space_type = 'VIEW_3D'
   bl_region_type = 'TOOLS'
   bl_label = "Surround Projection"
   
   def draw(self, context):
      layout = self.layout
      col = layout.column(align=True)
      
      row = col.row()
      row.prop(context.window_manager, "num_surround_screens")
      row = col.row()
      row.operator('objects.add_surround_cameras', icon='CAMERA_DATA')
      row = col.row()
      row.operator('scene.add_linked_scenes_for_surround_cameras', icon='SCENE_DATA')
      
      col = layout.column(align=True)
      row = col.row()
      row.operator('objects.remove_surround_cameras', icon='X')
      row = col.row()
      row.operator('objects.remove_linked_scenes_for_surround_cameras', icon='X')
	

# operator for adding cameras
class AddSurroundCamerasOperator(bpy.types.Operator):
   bl_idname = 'objects.add_surround_cameras'
   bl_label = "Add Cameras"
   bl_description = "Add n cameras"
   bl_options = {'REGISTER', 'UNDO'}
   
   @classmethod
   def poll(cls, context):
      return context.window_manager.previous_num_surround_screens is -1
   
   def execute(self, context):
      
      numScreens = context.window_manager.num_surround_screens
      
      # add an empty for the camera origin if not already present
      originExists = False
      for object in bpy.data.objects:
         if object.name == "CameraOrigin":
            bpy.ops.object.select_name(name="CameraOrigin")
            origin = bpy.context.active_object
            originExists = True
            break
      
      if not originExists:
         bpy.ops.object.add()
         origin = bpy.context.active_object
         origin.name = "CameraOrigin"
         origin.location = bpy.context.scene.cursor_location
      
      for i in range(0,numScreens):
         
         # add a new camer
         bpy.ops.object.camera_add()
            
         # get the current camera
         cam = bpy.context.active_object
         
         # name the camera
         cameraName = "Camera" + str(i)
         cam.name = cameraName
         cam.data.name = cameraName
         
         # position camera
         cam.location = 0,0,0
         cam.rotation_euler = (pi/2), 0, ((-2*pi)/numScreens) * i
         
         # set the field of view angle
         cam.data.angle = (2*pi)/numScreens
            
         # make the parent of the camera the origin
         cam.parent = origin
     
      bpy.ops.object.select_name(name="CameraOrigin")
      context.window_manager.previous_num_surround_screens = numScreens
      return {'FINISHED'}


# operator for creating new linked scenes for each camera
class AddSurroundScenesOperator(bpy.types.Operator):
   bl_idname = 'scene.add_linked_scenes_for_surround_cameras'
   bl_label = "Make Scenes"
   bl_description = "Creates new scenes with linked object data for each camera"
   bl_options = {'REGISTER', 'UNDO'}
   
   @classmethod
   def poll(cls, context):
      if context.window_manager.previous_num_surround_screens is not -1 and context.window_manager.surround_screens_init is False:
         return True
      return False
   
   def execute(self, context):
      numScreens = context.window_manager.previous_num_surround_screens
      sceneName = bpy.context.scene.name
      renderpath = bpy.context.scene.render.filepath
      
      for i in range(0, numScreens):
         
         thisScene = sceneName + "-Camera" + str(i)
         
         bpy.ops.scene.new(type='LINK_OBJECTS')
         bpy.context.scene.name = thisScene
         
         bpy.context.scene.camera = bpy.data.objects["Camera" + str(i)]
         
         bpy.context.scene.render.filepath = renderpath + thisScene

      bpy.context.screen.scene = bpy.data.scenes[sceneName]
      context.window_manager.surround_screens_init = True
      return {'FINISHED'}


# operator for removing the surround scenes
class RemoveSurroundScenesOperator(bpy.types.Operator):
   bl_idname = 'objects.remove_linked_scenes_for_surround_cameras'
   bl_label = "Remove Scenes"
   bl_description = "Removes all surround scenes"
   bl_options = {'REGISTER', 'UNDO'}
   
   @classmethod
   def poll(cls, context):
      return context.window_manager.surround_screens_init is True
   
   def execute(self, context):
      numScreens = context.window_manager.previous_num_surround_screens

      for scene in list(bpy.data.scenes):
         if re.search("-Camera",scene.name):
            bpy.data.scenes.remove(scene)
      
      context.window_manager.surround_screens_init = False
      return {'FINISHED'}


# operator for removing the surround cameras/scenes
class RemoveSurroundCamerasOperator(bpy.types.Operator):
   bl_idname = 'objects.remove_surround_cameras'
   bl_label = "Remove Cameras"
   bl_description = "Removes all surround cameras"
   bl_options = {'REGISTER', 'UNDO'}
   
   @classmethod
   def poll(cls, context):
      if context.window_manager.previous_num_surround_screens is not -1 and context.window_manager.surround_screens_init is False:
         return True
      return False
   
   def execute(self, context):
      numScreens = context.window_manager.previous_num_surround_screens
      
      for object in bpy.data.objects:
         if object.type == 'CAMERA':
            bpy.ops.object.select_name(name=object.name)
            bpy.ops.object.delete()
      
      context.window_manager.previous_num_surround_screens = -1
      return {'FINISHED'}



def register():
    bpy.utils.register_module(__name__)
    
    pass
    
def unregister():
    bpy.utils.unregister_module(__name__)
    
    pass
    
if __name__ == "__main__":
    register()
