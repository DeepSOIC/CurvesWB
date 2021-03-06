# -*- coding: utf-8 -*-

__title__ = "Constrained Profile"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Creates an editable interpolation curve"

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
import FreeCADGui
import Part
import _utils
import profile_editor
reload(profile_editor)

TOOL_ICON = _utils.iconsPath() + '/icon.svg'
#debug = _utils.debug
#debug = _utils.doNothing

#App::PropertyBool
#App::PropertyBoolList
#App::PropertyFloat
#App::PropertyFloatList
#App::PropertyFloatConstraint
#App::PropertyQuantity
#App::PropertyQuantityConstraint
#App::PropertyAngle
#App::PropertyDistance
#App::PropertyLength
#App::PropertySpeed
#App::PropertyAcceleration
#App::PropertyForce
#App::PropertyPressure
#App::PropertyInteger
#App::PropertyIntegerConstraint
#App::PropertyPercent
#App::PropertyEnumeration
#App::PropertyIntegerList
#App::PropertyIntegerSet
#App::PropertyMap
#App::PropertyString
#App::PropertyUUID
#App::PropertyFont
#App::PropertyStringList
#App::PropertyLink
#App::PropertyLinkSub
#App::PropertyLinkList
#App::PropertyLinkSubList
#App::PropertyMatrix
#App::PropertyVector
#App::PropertyVectorList
#App::PropertyPlacement
#App::PropertyPlacementLink
#App::PropertyColor
#App::PropertyColorList
#App::PropertyMaterial
#App::PropertyPath
#App::PropertyFile
#App::PropertyFileIncluded
#App::PropertyPythonObject
#Part::PropertyPartShape
#Part::PropertyGeometryList
#Part::PropertyShapeHistory
#Part::PropertyFilletEdges
#Sketcher::PropertyConstraintList

def midpoint(e):
    p = e.FirstParameter + 0.5 * (e.LastParameter - e.FirstParameter)
    return(e.valueAt(p))

class GordonProfileFP:
    """Creates an editable interpolation curve"""
    def __init__(self, obj, s, d, t):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSubList", "Support",         "Profile", "Constraint shapes").Support = s
        #obj.addProperty("App::PropertyEnumeration", "Parametrization", "Profile", "Parametrization type").Parametrization=["ChordLength","Centripetal","Uniform"]
        obj.addProperty("App::PropertyFloat",       "Tolerance",       "Profile", "Tolerance").Tolerance = 1e-5
        obj.addProperty("App::PropertyBool",        "Periodic",        "Profile", "Periodic curve").Periodic = False
        obj.addProperty("App::PropertyVectorList",  "Data",            "Profile", "Data list").Data = d
        #obj.addProperty("App::PropertyVectorList",  "Points",          "Profile", "Interpolated points")
        obj.addProperty("App::PropertyIntegerList", "DataType",        "Profile", "Types of interpolated points").DataType = t
        #obj.addProperty("App::PropertyVector",      "InitialTangent",  "Profile", "Initial Tangent")
        #obj.addProperty("App::PropertyVector",      "FinalTangent",    "Profile", "Final Tangent")
        #obj.addProperty("App::PropertyFloatList",   "Parameters",      "Profile", "Parameters of intersection points")
        obj.setEditorMode("Data", 2)
        obj.setEditorMode("DataType", 2)
        #obj.Parametrization = "ChordLength"
        obj.Proxy = self

    def get_shapes(self, fp):
        if hasattr(fp,'Support'):
            sl = list()
            for ob,names in fp.Support:
                for name in names:
                    if   ("Vertex" in name):
                        n = eval(name.lstrip("Vertex"))
                        if len(ob.Shape.Vertexes) >= n:
                            sl.append(ob.Shape.Vertexes[n-1])
                    elif ("Edge" in name):
                        n = eval(name.lstrip("Edge"))
                        if len(ob.Shape.Edges) >= n:
                            sl.append(ob.Shape.Edges[n-1])
                    elif ("Face" in name):
                        n = eval(name.lstrip("Face"))
                        if len(ob.Shape.Faces) >= n:
                            sl.append(ob.Shape.Faces[n-1])
            return(sl)

    def get_points(self, fp):
        shapes = self.get_shapes(fp)
        if   not len(fp.Data) == len(fp.DataType):
            FreeCAD.Console.PrintError("Gordon Profile : Data and DataType mismatch\n")
            return(None)
        else:
            pts = list()
            shape_idx = 0
            for i in range(len(fp.Data)):
                if   fp.DataType[i] == 0: # Free point
                    pts.append(fp.Data[i])
                elif (fp.DataType[i] == 1):
                    if (shape_idx < len(shapes)): # project on shape
                        d,p,i = Part.Vertex(fp.Data[i]).distToShape(shapes[shape_idx])
                        pts.append(p[0][1]) #shapes[shape_idx].valueAt(fp.Data[i].x))
                        shape_idx += 1
                    else:
                        pts.append(fp.Data[i])
                #elif fp.DataType[i] == 2: # datum is parameter on shape
                    #if isinstance(shapes[shape_idx],Part.Vertex):
                        #pts.append(shapes[shape_idx].Point)
                    #elif isinstance(shapes[shape_idx],Part.Edge):
                        #pts.append(shapes[shape_idx].valueAt(fp.Data[i].x))
                    #elif isinstance(shapes[shape_idx],Part.Face):
                        #pts.append(shapes[shape_idx].valueAt(fp.Data[i].x,fp.Data[i].y))
                    #shape_idx += 1
            return(pts)
        return(None)

    def execute(self, obj):
        pts = self.get_points(obj)
        
        if len(pts) < 2:
            FreeCAD.Console.PrintError("Gordon Profile : Not enough points\n")
        else:
            curve = Part.BSplineCurve()
            curve.interpolate(Points=pts, PeriodicFlag=obj.Periodic, Tolerance=obj.Tolerance)
            obj.Shape = curve.toShape()

    def onChanged(self, fp, prop):
        if prop == "Support":
            FreeCAD.Console.PrintMessage("Gordon Profile : Support changed\n")
            old_pts = fp.Data
            new_pts = self.get_points(fp)
            if new_pts:
                diff = [new_pts[i]-old_pts[i] for i in range(len(new_pts))]
                fp.Data = new_pts
                self.execute(fp)
            
            #for i in range(len(fp.Data)):
                
        #elif prop == "Data":
            
        return(True)

    def onDocumentRestored(self, fp):
        fp.setEditorMode("Data", 2)
        fp.setEditorMode("DataType", 2)

class GordonProfileVP:
    def __init__(self,vobj):
        vobj.Proxy = self
        
    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object
        self.active = False

    def start_edit(self):
        pts = list()
        #shapes = self.Object.Proxy.get_shapes(self.Object)
        shape_idx = 0
        for i in range(len(self.Object.Data)):
            p = self.Object.Data[i]
            t = self.Object.DataType[i]
            if t == 0:
                pts.append(profile_editor.MarkerOnShape([p]))
            elif t == 1:
                pts.append(profile_editor.MarkerOnShape([p],self.Object.Support[shape_idx]))
                shape_idx += 1
        self.ip = profile_editor.InterpoCurveEditor(pts, self.Object)

    def apply_edit(self):
        if not isinstance(self.ip,profile_editor.InterpoCurveEditor):
            return(False)
        pts = list()
        typ = list()
        original_links = self.Object.Support
        new_links = list()
        for p in self.ip.points:
            if isinstance(p,profile_editor.MarkerOnShape):
                pt = p.points[0]
                pts.append(FreeCAD.Vector(pt[0],pt[1],pt[2]))
                if p.shape:
                    if p.sublink in original_links:
                        new_links.append(p.sublink)
                        typ.append(1)
                    else:
                        typ.append(0)
                else:
                    typ.append(0)
        self.Object.Data = pts
        self.Object.DataType = typ
        self.Object.Support = new_links
        return(True)

    def doubleClicked(self,vobj):
        if not hasattr(self,'active'):
            self.active = False
        if not self.active:
            self.active = True
            self.start_edit()
        else:
            if self.apply_edit():
                self.active = False
                self.ip.quit()
        return(True)

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

class GordonProfileCommand:
    """Creates a editable interpolation curve"""
    def makeFeature(self, sub, pts, typ):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Gordon Profile")
        GordonProfileFP(fp,sub,pts,typ)
        GordonProfileVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        try:
            ordered = FreeCADGui.activeWorkbench().Selection
            if ordered:
                s = ordered
        except AttributeError:
            pass

        sub = list()
        pts = list()
        typ = list()
        for obj in s:
            if obj.HasSubObjects:
                #FreeCAD.Console.PrintMessage("object has subobjects %s\n"%str(obj.SubElementNames))
                for n in obj.SubElementNames:
                    sub.append((obj.Object,[n]))
                for p in obj.PickedPoints:
                    pts.append(p)
                    
        if len(pts) == 0:
            pts = [FreeCAD.Vector(0,0,0),FreeCAD.Vector(1,0,0)]
            typ = [0,0]
        else:
            typ = [1]*len(pts)
        self.makeFeature(sub,pts,typ)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('gordon_profile', GordonProfileCommand())
