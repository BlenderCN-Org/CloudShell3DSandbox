import bpy, numpy
from mathutils import *
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
from math import pi
from random import randint
import os

####
# Parameters
####
# Credentials for CloudShell
QSHost = "https://server.com:82"
QSUn = "username"
QSPw = "password"
QSDom = "Global"
SBID = "901b392d-3587-4e9d-bfaa-437b835145ac"
# Where files are and to be stored
WorkDir = "C:/temp"
ExportFile = WorkDir + "/sandbox.fbx"
ResourceTexturePath = WorkDir + "/resourcerect.png"

#### 
# CloudShell Stuff
####
def authRest(host, un, pw, dom):
    # authentication
    URI = host+"/api/login"
    auth = {"username":un,"password":pw,"domain":dom}
    headers = {"Content-Type":"application/json"}
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    ar = requests.put(URI, data=json.dumps(auth), headers=headers, verify=False)
    token = str(ar.text).replace('"','')
    print(ar.text)
    if ("Login failed for user" in str(token)):
        print ("Your authentication credentials to the server were bad")
        exit(1)
    return token

# Authenticate and log get devices in sandbox
token = authRest(QSHost, QSUn, QSPw, QSDom)
headers = {}
headers["Content-Type"] = "application/json"
headers["Accept"] = "application/json"
headers["Authorization"] = "Basic "+token
SBURI = QSHost+"/api/v1/sandboxes/"+SBID

sbsr = requests.get(SBURI, headers=headers, verify=False)
sbrobj = json.loads(sbsr.text)

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

def wrapTexture():
    # from https://wiki.blender.org/index.php/Dev:Py/Scripts/Cookbook/Code_snippets/Materials_and_textures#Textures
    # Load image file. Change here if the snippet folder is 
    # not located in you home directory.
    realpath = os.path.expanduser(ResourceTexturePath)
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
    
def addText(txt):
    # right now just pick random numbers as a POC
    # later we will spread these out logically and add connections
    x = randint(1,50) # top to b
    y = 0 # depth
    z = randint(10,50) # l to r
    textColor = makeMaterial('TextColor', (0,0,0), (1,1,1), 1)

    # first add the text and place it
    bpy.ops.object.text_add()
    textObject = bpy.context.active_object # the object just addded to the scene becomes the active object of the context
    textObject.data.body = txt
    textObject.data.materials.append(textColor)
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY") # set the origin (center of rotation) of the shape to it's geometric center
    textObject.rotation_euler[0] = pi / 2 #rotation euler is an array-like, [x,y,z], so this is 90 deg x axis rotation in radians!
    textObject.location += Vector((x-2,y-2,z))

    # put a block behind it
    planeObject = wrapTexture()
    planeObject.location += Vector((x,y,z))
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY") # set the origin (center of rotation) of the shape to it's geometric center
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, 0, 1)})
    bpy.ops.object.mode_set(mode='OBJECT')
    planeObject.rotation_euler[0] = pi / 2 #rotation euler is an array-like, [x,y,z], so this is 90 deg x axis rotation in radians!

    # animate to correct location
    textObject.keyframe_insert('rotation_euler',frame = 0) #as opposed to rotation quaternion
    planeObject.keyframe_insert('rotation_euler',frame = 0) #as opposed to rotation quaternion


# iterate over each root resource and add it
for component in sbrobj["components"]:
    if (component["type"] == "Resource"):
        if("/" not in component["name"]):
            print(component["name"])
            addText(component["name"])

# save it out
bpy.context.scene.update() 
bpy.ops.export_scene.fbx(filepath=ExportFile, object_types={'OTHER','MESH','ARMATURE'}, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False) # following recommendations from SketchFab