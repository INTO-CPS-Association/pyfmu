import datetime
from typing import Dict

from lxml import etree as ET

from pyfmu.fmi2.types import (
    IsFmi2Slave,
    Fmi2DataType_T,
    Fmi2Causality_T,
    Fmi2Variability_T,
)
from pyfmu.fmi2 import Fmi2Causality


_type_to_fmi2: Dict[Fmi2DataType_T, str] = {
    "real": "Real",
    "integer": "Integer",
    "boolean": "Boolean",
    "string": "String",
}

_causality_to_fmi2: Dict[Fmi2Causality_T, str] = {
    "calculatedParameter": "calculatedParameter",
    "independent": "independent",
    "input": "input",
    "local": "local",
    "output": "output",
    "parameter": "parameter",
}

_variability_to_fmi2: Dict[Fmi2Variability_T, str] = {
    "discrete": "discrete",
    "constant": "constant",
    "continuous": "continuous",
    "fixed": "fixed",
    "tunable": "tunable",
}


def extract_model_description_v2(fmu_instance: IsFmi2Slave) -> str:

    # 2.2.1 p.29) Structure

    data_time_obj = datetime.datetime.now()
    date_str_xsd = datetime.datetime.strftime(data_time_obj, "%Y-%m-%dT%H:%M:%SZ")

    fmd = ET.Element("fmiModelDescription")
    fmd.set("fmiVersion", "2.0")
    fmd.set("modelName", fmu_instance.model_name)
    fmd.set("guid", fmu_instance.guid)
    fmd.set("author", fmu_instance.author)
    fmd.set("generationDateAndTime", date_str_xsd)
    fmd.set("variableNamingConvention", "structured")
    fmd.set("generationTool", "pyfmu")

    #
    cs = ET.SubElement(fmd, "CoSimulation")
    cs.set("modelIdentifier", "pyfmu")
    cs.set("needsExecutionTool", "true")

    # 2.2.4 p.42) Log categories:
    # cs = ET.SubElement(fmd, "LogCategories")
    # for ac in fmu_instance.log_categories:
    #     c = ET.SubElement(cs, "Category")
    #     c.set("name", ac)

    # 2.2.7 p.47) ModelVariables
    mvs = ET.SubElement(fmd, "ModelVariables")

    variable_index = 0

    for var in fmu_instance.variables:

        value_reference = str(var.value_reference)
        variability = _variability_to_fmi2[var.variability]
        causality = _causality_to_fmi2[var.causality]
        data_type = _type_to_fmi2[var.data_type]

        idx_comment = ET.Comment(f'Index of variable = "{variable_index + 1}"')
        mvs.append(idx_comment)
        sv = ET.SubElement(mvs, "ScalarVariable")
        sv.set("name", var.name)
        sv.set("valueReference", value_reference)
        sv.set("variability", variability)
        sv.set("causality", causality)

        if var.description:
            sv.set("description", var.description)

        if var.initial:
            i = var.initial
            sv.set("initial", i)

        val = ET.SubElement(sv, data_type)

        if var.start is not None:
            s = str(var.start).lower()
            val.set("start", s)

        variable_index += 1
    ms = ET.SubElement(fmd, "ModelStructure")

    # 2.2.8) For each output we must declare 'Outputs' and 'InitialUnknowns'
    outputs = [
        (idx + 1, o)
        for idx, o in enumerate(fmu_instance.variables)
        if o.causality == Fmi2Causality.output
    ]

    if outputs:
        os = ET.SubElement(ms, "Outputs")
        for idx, o in outputs:
            ET.SubElement(os, "Unknown", {"index": str(idx), "dependencies": ""})

        os = ET.SubElement(ms, "InitialUnknowns")
        for idx, o in outputs:
            ET.SubElement(os, "Unknown", {"index": str(idx), "dependencies": ""})

    try:
        # FMI requires encoding to be encoded as UTF-8 and contain a header:
        #
        # See 2.2 p.28
        md = ET.tostring(
            fmd, pretty_print=True, encoding="UTF-8", xml_declaration=True
        ).decode("UTF-8")
    except Exception as e:
        raise RuntimeError(
            f"Failed to parse model description. Write resulted in error: {e}"
        ) from e

    return md
