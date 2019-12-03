from jinja2 import Template
from os.path import join

import datetime

def extract_model_description_from(working_dir : str, fmu_instance: object) -> str:
    
    builder_template_path = join(working_dir, "resources", "templates","modelDescription.xml.j2")


    data_time_obj = datetime.datetime.now()
    date_str_xsd = datetime.datetime.strftime(data_time_obj, '%Y-%m-%dT%H:%M:%SZ')

    values = {
        "fmi_version" : 2,
        "guid" : "",
        "model_name" : fmu_instance.modelName,
        "author" : fmu_instance.author,
        "generation_time" : date_str_xsd,
    }

    with open(builder_template_path) as f:
        s = f.read()
        t = Template(s)
        r = t.render(values)


    return r