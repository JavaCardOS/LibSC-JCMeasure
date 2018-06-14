# LibSC-JCMeasure

LibSC-JCMeasure is a speed measure tool for Java Card.

## Requirments

Requirments are listed below:

1. Windows 7+
2. Pyhton3.6 (download the install pack at [https://www.python.org/downloads/](https://www.python.org/downloads/) )
3. JDK1.5+ (please add dir of javac.exe to PATH environment variable)
4. JRE1.5+ (please add dir of java.exe to PATH environment variable)
5. scons (use `pip install scons` to install scons)
6. pyDes (use `pip install pyDes` to install pyDes)

## Usage

First, you need to clone this project form Github, the URL is [https://github.com/JavaCardOS/LibSC-JCMeasure.git](https://github.com/JavaCardOS/LibSC-JCMeasure.git).

After you have all requirments installed, execute

```
scons
```

under the project directory. All measure test cases will be built into the `tests` directory.

Execute

```
python jcmeasure.py
```

to start a measure process, and then a report file will be generated in the project directory when process over.

## How to add measure case

Source files of a measure case is structured in a folder in `tests_src`, in this folder there must be a `SConstruct` file to build the measure case, a `test_xxx.json` file to describe the case and any other files needed. An example:

```
test_nop
|   SConstruct
|   test_nop.json
\---src
    \---libsc
        \---jcmeasure
            \---test_nop
                    TestNop.java
```

Please see the measure cases in the `tests_src` for more information.

### SConstruct file

SConstruct file is the build description file for scons. In this file, you need to build your measure case, install the `test_xxx.json` and any other files to the folder `DIST_PATH` in the `ARGUMENTS` dict.

``` python
#coding: utf-8

PKGS = [{
    "name": "libsc.jcmeasure.test_nop",
    "version": "1.0",
    "aid": "11223344550001",
    "applets": [{
        "name": "TestNop",
        "aid": "1122334455000101"
    }]
}]

from jcbuilder import gen_caps, convert_jca
from pathlib import Path

dist_path = ARGUMENTS.get("DIST_PATH", "../../tests")

# generate cap and jca file by java file
caps = gen_caps(PKGS)
jca = str(Path(str(caps[0])).with_suffix(".jca"))
Depends(jca, caps)

def insert_op(target, source, env):
    jca_lines = open(str(source[0])).readlines()
    with open(str(target[0]), "w") as f:
        f.writelines(jca_lines[:127])
        # insert 10 nop after if_scmpge L5;
        f.writelines(["\t\t\t\t\tnop;\n"] * 10)
        f.writelines(jca_lines[127:])
    
new_jca = Command("test_nop.jca", jca, insert_op)

out = convert_jca("test_nop.cap", new_jca)
inst = Install(dist_path, out + Glob("*.json"))
Default(inst)

```

### json file

The `test_xxx.json` file is used to describe the measure test case. A test json file is like below:

``` json
{
    "name": "Ins_nop",
    "description": "Test nop instruction speed.",
    "round": 10,        // how many times the adjust or test action will perform
    "result": "lambda t: 0x1000 / t",   // the python lambda expression to calculate result
    "unit": "INS/S",    // the unit of result
    "setup": [      // setup will be executed before adjust and test
        "Reset",        // action: reset card
        "LoadAndInstall test_nop.cap", // action: load CAP and install applet in the CAP
        "Select 1122334455000101"   // action: select applet instance
    ],
    "teardown": [ // teardown will be executed after adjust and test
        "Reset",
        "Remove 11223344550001" // remove package or applet
    ],
    // adjust is usually an `empty` action for time ajustment
    "adjust": "SendAPDU 8001100000",    // send APDU
    // the action to test what you need to test
    "test": "SendAPDU 8002100000"
}
```

In the test case above, the measure system will send the `adjust` APDU 10 times, and get the minimize elapsed time as `t1`, then send the `test` APDU 10 times, and get the minimize elapsed time as `t2`, so the actual time for the measure test case is `t = t2 - t1`, and then the system will caculate the result by using the `lambda` expression and write it into the report file.
