from setuptools_scm import get_version
import os
import re
import shutil
import subprocess

PWD = os.path.realpath(os.path.dirname(__file__))
UAL = os.path.dirname(PWD)

def join_path(path1="", path2=""):
    return os.path.normpath(os.path.join(path1, path2))


DD_GIT_DESCRIBE = get_version()


def saxon_version(verb=False) -> int:
    cmd = ["java", "net.sf.saxon.Transform", "-t"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=False)
        line = out.stderr.split("\n")[0]
        version = re.search(r"Saxon.* +(\d+)\.(\d+)", line)
        if verb:
            print("Got Saxon version:", version.group(1), version.group(2))
        major = int(version.group(1)) * 100
        minor = int(version.group(2))
        version = major + minor
    except Exception as e:
        if verb:
            print(f"Error: can't get Saxon version. {e}")
        version = 0
    return version


def generate_dd_data_dictionary(extra_opts=""):
    print("generating dd_data_dictionary.xml")
    dd_data_dictionary_generation_command = (
        "java"
        + " net.sf.saxon.Transform"
        + extra_opts
        + " -t -warnings:fatal -s:"
        + "dd_data_dictionary.xml.xsd"
        + " -xsl:"
        + "dd_data_dictionary.xml.xsl"
        + " -o:"
        + "dd_data_dictionary.xml"
        + " DD_GIT_DESCRIBE="
        + DD_GIT_DESCRIBE
    )
    proc = subprocess.Popen(
        dd_data_dictionary_generation_command.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # env=env,
        universal_newlines=True,
    )
    (stdout, stderr) = proc.communicate()

    if proc.returncode != 0:
        assert False, stderr
    else:
        try:
            if not os.path.islink(join_path(PWD, "IDSDef.xml")):
                os.symlink(
                    "dd_data_dictionary.xml",
                    "IDSDef.xml",
                )
        except Exception as _:  # noqa: F841
            shutil.copy("dd_data_dictionary.xml", "IDSDef.xml")


def generate_html_documentation(extra_opts=""):
    print("generating html_documentation.html")
    html_documentation_generation_command = (
        "java"
        + " net.sf.saxon.Transform"
        + extra_opts
        + " -t -warnings:fatal -s:"
        + "dd_data_dictionary.xml"
        + " -xsl:"
        + "dd_data_dictionary_html_documentation.xsl"
        + " -o:"
        + "html_documentation.html"
        + " DD_GIT_DESCRIBE="
        + DD_GIT_DESCRIBE
    )
    proc = subprocess.Popen(
        html_documentation_generation_command.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # env=env,
        universal_newlines=True,
    )
    (stdout, stderr) = proc.communicate()

    if proc.returncode != 0:
        assert False, stderr

    shutil.copy(
        "schemas/utilities/coordinate_identifier.xml",
        "html_documentation/utilities/coordinate_identifier.xml",
    )


def generate_ids_cocos_transformations_symbolic_table(extra_opts=""):
    print("generating html_documentation/cocos/ids_cocos_transformations_symbolic_table.csv")
    ids_cocos_transformations_symbolic_table_generation_command = (
        "java"
        + " net.sf.saxon.Transform"
        + extra_opts
        + " -t -warnings:fatal -s:"
        + "dd_data_dictionary.xml"
        + " -xsl:"
        + "ids_cocos_transformations_symbolic_table.csv.xsl"
        + " -o:"
        + "html_documentation/cocos/ids_cocos_transformations_symbolic_table.csv"
        + " DD_GIT_DESCRIBE="
        + DD_GIT_DESCRIBE
    )
    proc = subprocess.Popen(
        ids_cocos_transformations_symbolic_table_generation_command.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # env=env,
        universal_newlines=True,
    )
    (stdout, stderr) = proc.communicate()

    if proc.returncode != 0:
        assert False, stderr


def generate_idsnames():
    print("generating IDSNames.txt")
    idsnames_command = (
        "java"
        + " net.sf.saxon.Transform"
        + " -t -warnings:fatal -s:"
        + "dd_data_dictionary.xml"
        + " -xsl:"
        + "IDSNames.txt.xsl"
        + " -o:"
        + "IDSNames.txt"
    )
    proc = subprocess.Popen(
        idsnames_command.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    (stdout, stderr) = proc.communicate()

    if proc.returncode != 0:
        assert False, stderr

def generate_dd_data_dictionary_validation(extra_opts=""):
    print("dd_data_dictionary_validation.txt")

    dd_data_dictionary_validation_generation_command = (
        "java"
        + " net.sf.saxon.Transform"
        + extra_opts
        + " -t -warnings:fatal -s:"
        + "dd_data_dictionary.xml"
        + " -xsl:"
        + "dd_data_dictionary_validation.txt.xsl"
        + " -o:"
        + "dd_data_dictionary_validation.txt"
    )
    proc = subprocess.Popen(
        dd_data_dictionary_validation_generation_command.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    (stdout, stderr) = proc.communicate()

    if proc.returncode != 0:
        assert False, stderr


if __name__ == "__main__":

    generate_dd_data_dictionary()
    generate_html_documentation()
    generate_ids_cocos_transformations_symbolic_table()
    generate_idsnames()
    generate_dd_data_dictionary_validation()
