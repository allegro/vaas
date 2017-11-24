VCL Variables
=============

VCL variables may be used in VclTemplates or VclTemplateBlocks. VaaS variables should be enclosed with curly braces and
prepended with hash sign. VaaS variable keys have to fulfill the definition of a word in regex terms ('^\w+$').

For example:

    #{foo}

An important feature of VaaS VCL variables is that they are associated with a VirtualCluster. They are not associated
directly with VclCluster, VclTemplate nor with VarnishServer.

Defining VCL Variables
----------------------

You can define variables in _home -> cluster -> Vcl variables_ section of the VaaS admin panel.

Using VCL Variables
-------------------

Before using a VCL variable in a VclTemplate or a VclTemplateBlock, you first have to define it. If a variable that has
not been defined is detected in a template when you save it, a validation error is raised by VaaS and the item is not
saved.

Here is an example of how to use a VCL variable in a template:

    sub vcl_recv {
        if (req.http.host == "#{host_variable}") {
            ## <do something> ##
            <SET_BACKEND_director_name/>
        }
     }

Notice the #{host_variable}. It will be substituted with whatever value you define under the "host_variable" key in the
Vcl variables section in VaaS admin panel.

When to use VCL Variables
-------------------------

VCL variables can be useful when you have the same VCL template in different environments (eg. test and production). In
such case you may have both environments available at different DNS domains, eg. test.example.org and prod.example.org.
In such a set up, you could change your test VCL and once it is proved to work, you could release the VCL 1:1 into
production.