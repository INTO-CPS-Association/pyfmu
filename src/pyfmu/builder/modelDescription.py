from os.path import join
from xml.dom import minidom
from xml.etree.ElementTree import ElementTree
import datetime
import io
import uuid
import xml.etree.ElementTree as ET

from jinja2 import Template

from pyfmu.fmi2 import Fmi2Causality


def extract_model_description_v2(fmu_instance) -> str:
    
    data_time_obj = datetime.datetime.now()
    date_str_xsd = datetime.datetime.strftime(data_time_obj, '%Y-%m-%dT%H:%M:%SZ')

    uid = str(uuid.uuid4())

    fmd = ET.Element("fmiModelDescription")
    fmd.set("fmiVersion","2.0")
    fmd.set("modelName",fmu_instance.modelName)
    fmd.set("guid",uid)
    fmd.set('author',fmu_instance.author)
    fmd.set('generationDateAndTime', date_str_xsd)
    fmd.set('variableNamingConvention', 'structured')
    fmd.set("generationTool", 'pyfmu')

    cs = ET.SubElement(fmd,'CoSimulation')
    cs.set("modelIdentifier", 'pyfmu')
    cs.set('needsExecutionTool','true')
    
    

    mvs = ET.SubElement(fmd,'ModelVariables')
    
    variable_index = 0

    for var in fmu_instance.vars:

        vref = str(var.value_reference)
        v = var.variability.value
        c = var.causality.value
        t = var.data_type.value

        idx_comment = ET.Comment(f'Index of variable = "{variable_index + 1}"')
        mvs.append(idx_comment)
        sv = ET.SubElement(mvs, "ScalarVariable")
        sv.set("name",var.name)
        sv.set("valueReference",vref)
        sv.set("variability", v)
        sv.set("causality", c)

        if(var.description):
            sv.set("description",var.description)
        

        if(var.initial):
            i = var.initial.value
            sv.set('initial', i)
        
        
        val = ET.SubElement(sv, t)

        if(var.start is not None):
            s = str(var.start)
            val.set("start", s)
        
        variable_index += 1


    ms = ET.SubElement(fmd,'ModelStructure')
    
    

    # 2.2.8) For each output we must declare 'Outputs' and 'InitialUnknowns'
    outputs = [(idx+1,o) for idx,o in enumerate(fmu_instance.vars) if o.causality.name == Fmi2Causality.output.name]

    if(outputs):
        os = ET.SubElement(ms,'Outputs')
        for idx,o in outputs:
            ET.SubElement(os,'Unknown',{'index' : str(idx), 'dependencies' : ''})

        os = ET.SubElement(ms, 'InitialUnknowns')
        for idx,o in outputs:
            ET.SubElement(os,'Unknown',{'index' : str(idx), 'dependencies' : ''})
    

    try:
        stream = io.StringIO()
        ElementTree(fmd).write(stream, encoding="unicode", short_empty_elements=True,xml_declaration=True)
    except Exception as e:
        raise RuntimeError("Failed to parse model description. ") from e
   
    # Format XML
    md_not_formatted =  stream.getvalue()
    md_formatted = minidom.parseString(md_not_formatted).toprettyxml(indent='   ')


    return md_formatted
    



