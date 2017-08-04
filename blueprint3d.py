import bpy, bmesh
import numpy, math
from mathutils import *
from math import pi
from random import randint
import os
import xml.dom.minidom

####
# Parameters
####
# Where files are and to be stored
WorkDir = "C:/temp"
ExportFile = WorkDir + "/blueprint.fbx"
SourceFile = WorkDir + "/SampleBlueprintExport.xml"
ResourceTexturePath = WorkDir + "/resourcerect.png"
ServiceTexturePath = WorkDir + "/servicerect.png"

####
# Blender stuff
####
def makeMaterial(name, diffuse, specular, alpha):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT' 
    mat.diffuse_intensity = 1.0 
    mat.specular_color = specular
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.5
    mat.alpha = alpha
    mat.ambient = 1
    return mat

def wrapTexture(textpath):
    # from https://wiki.blender.org/index.php/Dev:Py/Scripts/Cookbook/Code_snippets/Materials_and_textures#Textures
    # Load image file. Change here if the snippet folder is 
    # not located in you home directory.
    realpath = os.path.expanduser(textpath)
    try:
        img = bpy.data.images.load(realpath)
    except:
        raise NameError("Cannot load image %s" % realpath)
 
    # Create image texture from image
    cTex = bpy.data.textures.new('ColorTex', type = 'IMAGE')
    cTex.image = img
 
 
    # Create material
    mat = bpy.data.materials.new('TexMat')
 
    # Add texture slot for color texture
    mtex = mat.texture_slots.add()
    mtex.texture = cTex
    mtex.texture_coords = 'UV'
    mtex.use_map_color_diffuse = True 
    mtex.use_map_color_emission = True 
    mtex.emission_color_factor = 0.5
    mtex.use_map_density = True 
    mtex.mapping = 'FLAT' 
 
    # Create new cube and give it UVs
    bpy.ops.mesh.primitive_plane_add()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')
 
    # Add material to current object
    ob = bpy.context.object
    ob.dimensions.x = 10
    me = ob.data
    me.materials.append(mat)
 
    return ob
    
def addResource(txt, x, y, z, textpath):
    # store it
    coord = {}
    coord["x"] = int(x)
    coord["y"] = int(y)
    coord["z"] = int(z)
    objList[txt.replace(" ","")] = coord

    # first add the text and place it
    # from https://medium.com/@colten_jackson/hello-hololens-creating-holographic-animations-with-python-blender-44d8ba237a2b
    bpy.ops.object.text_add()
    textObject = bpy.context.active_object # the object just addded to the scene becomes the active object of the context
    textObject.data.body = txt
    textObject.data.materials.append(textColor)
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY") # set the origin (center of rotation) of the shape to it's geometric center
    textObject.rotation_euler[0] = pi / 2 #rotation euler is an array-like, [x,y,z], so this is 90 deg x axis rotation in radians!
    textObject.location += Vector((x-2,y-2,z))

    # put a block behind it
    planeObject = wrapTexture(textpath)
    planeObject.location += Vector((x,y,z))
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY") # set the origin (center of rotation) of the shape to it's geometric center
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, 0, 1)})
    bpy.ops.object.mode_set(mode='OBJECT')
    planeObject.rotation_euler[0] = pi / 2 #rotation euler is an array-like, [x,y,z], so this is 90 deg x axis rotation in radians!

    # animate to correct location
    textObject.keyframe_insert('rotation_euler',frame = 0) #as opposed to rotation quaternion
    planeObject.keyframe_insert('rotation_euler',frame = 0) #as opposed to rotation quaternion

def drawLine(r1, r2):
    # from https://blender.stackexchange.com/questions/5898/how-can-i-create-a-cylinder-linking-two-points-with-python
    r = .1
    dx = r2["x"] - r1["x"]
    dy = r2["y"] - r1["y"]
    dz = r2["z"] - r1["z"]
    dist = math.sqrt(dx**2 + dy**2 + dz**2)

    bpy.ops.mesh.primitive_cylinder_add(
        radius = r, 
        depth = dist,
        location = (dx/2 + r1["x"], dy/2 + r1["y"], dz/2 + r1["z"])   
    ) 
    lineObject = bpy.context.active_object
    lineObject.data.materials.append(lineColor)

    phi = math.atan2(dy, dx) 
    theta = math.acos(dz/dist) 

    bpy.context.object.rotation_euler[1] = theta 
    bpy.context.object.rotation_euler[2] = phi 

####
# main program
####
# clear out existing crap on canvas
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete(use_global=False)
bpy.ops.object.select_by_type(type='FONT')
bpy.ops.object.delete(use_global=False)

# store where we put stuff
objList = {}
# global colors
textColor = makeMaterial('TextColor', (0,0,0), (1,1,1), 1) # black
lineColor = makeMaterial('LineColor', (0,1,0), (1,1,1), 1) # green

dom = xml.dom.minidom.parse(SourceFile)

# iterate over each root resource and add it to canvas
rlist = dom.getElementsByTagName('Resource')
for node in rlist:
    name = node.getAttribute("Name")
    x = node.getAttribute("PositionX")
    y = node.getAttribute("PositionY")
    if((x!="") and (y!="")):
        addResource(name,int(float(x)/20)+10,0,int(float(y)/20), ResourceTexturePath)

# iterate over each service resource and add it to canvas
slist = dom.getElementsByTagName('Service')
for node in slist:
    name = node.getAttribute("Alias")
    x = node.getAttribute("PositionX")
    y = node.getAttribute("PositionY")
    if((x!="") and (y!="")):
        addResource(name,int(float(x)/20)+10,0,int(float(y)/20), ServiceTexturePath)

# iterate over each routea nd add it to canvas
routelist = dom.getElementsByTagName('Route')
for node in routelist:
    source = node.getAttribute("Source")
    print(source)
    if ("/" in source):
        source = source.split("/")[0]
    target = node.getAttribute("Target")
    if ("/" in target):
        target = target.split("/")[0]
    print(source + " " + target)
    drawLine(objList[source.replace(" ","")],objList[target.replace(" ","")])
    
# iterate over each connector add it to canvas
conList = dom.getElementsByTagName('Connector')
for node in conList:
    source = node.getAttribute("Source")
    print(source)
    if ("/" in source):
        source = source.split("/")[0]
    target = node.getAttribute("Target")
    if ("/" in target):
        target = target.split("/")[0]
    print(source + " " + target)
    drawLine(objList[source.replace(" ","")],objList[target.replace(" ","")])

# save it out
bpy.context.scene.update() 
bpy.ops.export_scene.fbx(filepath=ExportFile, object_types={'OTHER','MESH','ARMATURE'}, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False) # following recommendations from SketchFab