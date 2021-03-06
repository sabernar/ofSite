#!/usr/bin/python

from lxml import etree
from lxml import objectify
import os
import sys
import re
from lxml.html.soupparser import fromstring 

import doxygen_compound

from documentation_class import DocsClass
from markdown_file import getclass,setclass,getfunctionsfile,setfunctionsfile
from documentation_members import DocsMethod, DocsVar
from documentation_function import DocsFunctionsFile, DocsFunction

of_root = "/home/arturo/Desktop/openFrameworks/"
of_documentation = of_root + 'libs/openFrameworksCompiled/project/doxygen/build/xml/'
documentation_root = '/home/arturo/Documents/ofSite/documentation/'
#index = open(documentation_root + "index.html.mako",'w')

print of_documentation

missing_functions = []

currentversion = "0.8.0"


def update_moved_functions(filename):
    xml = objectify.parse(filename)
    doxygen = xml.getroot()
    
    xmlfunctionsfile = doxygen.compounddef

    
    if xmlfunctionsfile.find('sectiondef')!=None:
        if len([ s for s in xmlfunctionsfile.sectiondef if s.get('kind')=='func'])>0:
            file_split = os.path.splitext(xmlfunctionsfile.compoundname.text)
            functionsfile = getfunctionsfile(file_split[0])
            for section in xmlfunctionsfile.sectiondef:
                if section.get('kind')=='func':
                    for xmlfunction in section.memberdef:
                        for function in missing_functions:
                            if function.name == xmlfunction.name.text:
                                argstring = str(xmlfunction.argsstring.text)
                                params = argstring[argstring.find('(')+1:argstring.rfind(')')]
                                returns = xmlfunction.type.ref.text if hasattr(xmlfunction.type,'ref') else xmlfunction.type.text
                                moved_function = functionsfile.function_by_signature(xmlfunction.name.text, returns, params)
                                moved_function.returns = returns
                                moved_function.description = moved_function.description + '\n\n' + function.description
                                print "moved function: " + function.name
                                
            setfunctionsfile(functionsfile)
    
    
            
def serialize_functionsfile(filename):
    xml = objectify.parse(filename)
    doxygen = xml.getroot()
    
    xmlfunctionsfile = doxygen.compounddef

    
    if xmlfunctionsfile.find('sectiondef')!=None:
        if len([ s for s in xmlfunctionsfile.sectiondef if s.get('kind')=='func'])>0:
            #print '\n'
            file_split = os.path.splitext(xmlfunctionsfile.compoundname.text)
            #print file_split[0]
            functionsfile = getfunctionsfile(file_split[0])
            #print 'new: ' + str(functionsfile.new)
            functions_fromxml = []
            for section in xmlfunctionsfile.sectiondef:
                if section.get('kind')=='func':
                    for xmlfunction in section.memberdef:
                        argstring = str(xmlfunction.argsstring.text)
                        params = argstring[argstring.find('(')+1:argstring.rfind(')')]
                        returns = xmlfunction.type.ref.text if hasattr(xmlfunction.type,'ref') else xmlfunction.type.text
                        function = functionsfile.function_by_signature(xmlfunction.name.text, returns, params)
                        #function.description = function.description.replace("~~~~{.brush cpp}","~~~~{.cpp}").replace('</pre>',"~~~~")
                        function.description = function.description.replace('<p>','').replace('</p>','').replace('<code>','').replace('</code>','').replace('<pre>','')
                        function.returns = returns
                        functions_fromxml.append(function.name)
                        
                        #print function.returns + " " + function.name + xmlfunction.argsstring.text + " new: " + str(function.new)
            
            #print "missing functions"
            thisfile_missing_functions = []
            #[f for f in functionsfile.function_list if f not in functions_fromxml.function_list]
            for function in functionsfile.function_list:
                if not function.name in functions_fromxml:
                    #print function.name+"("+function.parameters+")"
                    missing_functions.append(function)
                    thisfile_missing_functions.append(function)
            
            for function in thisfile_missing_functions:
                functionsfile.function_list.remove(function)
                
            deprecated_functions = []
            for function in functionsfile.function_list:
                if function.name.find("OF_DEPRECATED_MSG")!=-1:
                    deprecated_functions.append(function)
            for function in deprecated_functions:
                functionsfile.function_list.remove(function);
                        
            functionsfile.function_list.sort(key=lambda function: function.name)
            setfunctionsfile(functionsfile)
                        
    
def parse_doxigen_para_element(e):
    if type(e.value) == doxygen_compound.docRefTextType:
        if type(e.value.content_) == list:
            ret = ""
            for l in e.value.content_:
                ret = ret + parse_doxigen_para_element(l)
            return ret
        else:
            return e.value.content_
            
            
    elif type(e.value) == doxygen_compound.docURLLink:
        if type(e.value.content_) == list:
            ret = ""
            for l in e.value.content_:
                ret = ret + "[" + l.value + "](" + l.value + ")"
            return ret
        else:
            return + "[" + e.value.content_ + "](" + e.value.content_ + ")"
            
            
    elif type(e.value) == doxygen_compound.docSimpleSectType:
        ret = "***" + e.value.kind + ":*** \n\t"
        for pc in e.value.get_para():
            ret = ret + serialize_doxygen_paragraph(pc)
        return ret
        
    elif type(e.value) == doxygen_compound.refTextType:
        if type(e.value.content_) == list:
            ret = ""
            for l in e.value.content_:
                ret = ret + parse_doxigen_para_element(l)
            return ret
        else:
            return e.value.content_
    
    elif type(e.value) == doxygen_compound.docMarkupType:
        if type(e.value.content_) == list:
            ret = ""
            for l in e.value.content_:
                ret = ret + parse_doxigen_para_element(l)
            return ret
        else:
            return e.value.content_
            
    else:        
        return  e.value

def serialize_doxygen_paragraph(p):
    ret = ""
    for c in p.content_:
        next_element = parse_doxigen_para_element(c)
        ret = ret + next_element
            
    ret = ret + "\n\n"
    return ret

def serialize_class(filename):
    xml = objectify.parse(filename)
    doxygen = xml.getroot()
    
    clazz = doxygen_compound.parse(filename).compounddef #doxygen.compounddef
        
    print "class " + clazz.compoundname
    documentation_class = getclass(clazz.compoundname)
    
    
    #f = open('documentation/' + classname + ".html.mako",'w')
    
    #index.write("[" + classname + "](" + classname + ".html)\n\n")
    
    #f.write( '<%inherit file="_templates/documentation.mako" />\n' )
    #f.write( '___' + classname + "___\n" )
    
    inheritsfrom = []
    #if clazz.find('derivedcompoundref')!=None:
    inheritsfrom = clazz.derivedcompoundref

    documentation_class.detailed_inline_description = ""
   
    #clazz_for_description = doxygen_compound.parse(filename).compounddef 
    for p in clazz.briefdescription.get_para():
        documentation_class.detailed_inline_description = documentation_class.detailed_inline_description + serialize_doxygen_paragraph(p)
    documentation_class.detailed_inline_description = documentation_class.detailed_inline_description + "\n\n\n"
        
    for p in clazz.detaileddescription.get_para():
        documentation_class.detailed_inline_description = documentation_class.detailed_inline_description + serialize_doxygen_paragraph(p)

    #if clazz.find('sectiondef')!=None:
    for section in clazz.sectiondef:
        for member in section.memberdef:
            #if section.get("kind") == public TODO: access, virtual, pure virtual
            if member.kind == 'enum':
                pass
            else:
                #f.write( "$$code(lang=c++)\n" )
                if member.kind == 'variable':
                    var = documentation_class.var_by_name(member.name)
                    if not var:
                        var = DocsVar(0)
                        var.name = member.name
                        var.access = member.prot
                        var.version_started = currentversion
                        var.version_deprecated = ""
                        var.constant = member.mutable=="no"
                        var.static = member.static
                        var.clazz = documentation_class.name
                        #member.type.ref.text if hasattr(member.type,'ref') else member.type.text
                        var.type = ""
                        try:
                            for e in member.type_.content_:
                                if type(e.value) == doxygen_compound.refTextType:
                                    var.type = var.type +  e.value.valueOf_
                                else:
                                    var.type = var.type + e.value + " "
                        except:
                            pass
                    #f.write( str(member.type.text) + " " + str(member.name.text) + "\n" )
                if member.kind == 'function' and member.name.find("OF_DEPRECATED_MSG")==-1:
                    argstring = str(member.argsstring)
                    params = argstring[argstring.find('(')+1:argstring.rfind(')')]
                    
                    returns = ""
                    try:
                        for e in member.type_.content_:
                            if type(e.value) == doxygen_compound.refTextType:
                                returns = returns +  e.value.valueOf_
                            else:
                                returns = returns + e.value
                    except:
                        pass
                        
                    returns = ("" if returns is None else returns)
                    method = documentation_class.function_by_signature(member.name, returns, params)
                    method.static = member.static
                    method.clazz = documentation_class.name
                    method.access = member.prot
                    method.returns = returns
                    #method.description = method.description.replace("~~~~{.brush: cpp}","~~~~{.cpp}").replace('</pre>',"~~~~")
                    method.description = method.description.replace('<p>','').replace('</p>','').replace('<code>','').replace('</code>','').replace('<pre>','')
                    if method.new:
                        print "new method " + method.name + " in " + method.clazz
                        method.version_started = currentversion
                        
                    method.inlined_description = ""
                    for p in member.briefdescription.get_para():
                        method.inlined_description = method.inlined_description + serialize_doxygen_paragraph(p)
                        
                    method.inlined_description = method.inlined_description + "\n\n"
                    for p in member.detaileddescription.get_para():
                        method.inlined_description = method.inlined_description + serialize_doxygen_paragraph(p)
                        
                    #f.write( str(member.type.text) + " " + str(member.name.text) + str(member.argsstring.text) + "\n" )
                """if member.name.text.find("OF_DEPRECATED_MSG")!=-1:
                    print "found deprecated function " + member.name.text
                    print "argstring = " + str(member.argsstring.text)
                    print "params = " + member.argsstring.text[member.argsstring.text.find('(')+1:member.argsstring.text.rfind(')')]
                    returns = member.type.ref.text if hasattr(member.type,'ref') else member.type.text
                    print "returns = " + ("" if returns is None else returns)"""
                #f.write( "$$/code\n\n\n\n" )
    
    #f.close()
    deprecated_methods = []
    for method in documentation_class.function_list:
        if method.name.find("OF_DEPRECATED_MSG")!=-1:
            deprecated_methods.append(method)
    for method in deprecated_methods:
        documentation_class.function_list.remove(method);
        
    documentation_class.function_list.sort(key=lambda function: function.name)
    documentation_class.var_list.sort(key=lambda variable: variable.name)
    setclass(documentation_class)

#serialize_class ("/home/arturo/Desktop/openFrameworks/libs/openFrameworksCompiled/project/doxygen/build/xml/classof_log.xml")
#quit()

#index.write( '<%inherit file="_templates/documentation.mako" />\n' )
dir_count=0
file_count=0
for root, dirs, files in os.walk("/home/arturo/Desktop/openFrameworks/libs/openFrameworksCompiled/project/doxygen/build/xml"):
    dir_count+=1
    for name in files:       
        file_count+=1
        filename = os.path.join(root, name)
        if name.find('class')==0:
            serialize_class(filename)
        elif name.find('of_')==0 and name.find('8h.xml')!=-1:
            serialize_functionsfile(filename)

for root, dirs, files in os.walk("/home/arturo/Desktop/openFrameworks/libs/openFrameworksCompiled/project/doxygen/build/xml"):
    dir_count+=1
    for name in files:       
        file_count+=1
        filename = os.path.join(root, name)
        if name.find('of_')==0 and name.find('8h.xml')!=-1:
            update_moved_functions(filename)

print ""+str(dir_count)+" dirs/"+str(file_count)+" files"

