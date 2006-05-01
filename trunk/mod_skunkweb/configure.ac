dnl -*- m4 -*-
dnl  
dnl  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
dnl  
dnl	 You may distribute under the terms of either the GNU General
dnl	 Public License or the SkunkWeb License, as specified in the
dnl	 README file.
dnl   
dnl Process this file with autoconf to produce a configure script.

AC_INIT(mod_skunkweb.c, 3.4.1)

AC_SUBST(SW_VERSION)
SW_VERSION=3.4.1

AC_PROG_CC
AC_PROG_MAKE_SET
AC_PROG_RANLIB
AC_PROG_INSTALL

dnl deal with weird HP/UX stuff
if test "`uname -s`" = "HP-UX"
then
    INSTALL="/bin/sh $INSTALL"
fi

AC_MSG_CHECKING([--with-apxs given])
AC_ARG_WITH(apxs, 
[  --with-apxs=/path/apxs  Specify path to the apxs program],[
	AC_MSG_RESULT([yes $withval])
	APXS=$withval],[
	AC_MSG_RESULT([no, will look in \$PATH])
	APXS=])

# --with-apxs not supplied, try to find in PATH
if test -z "$APXS"
then
dnl Locate apache axps, needed to compile mod_skunkweb
AC_PATH_PROG(APXS, apxs, "notfound", "$PATH:/usr/local/apache/bin")

if [[ "$APXS" = "notfound" ]]
then
    AC_MSG_ERROR([apxs not found! Make sure Apache is installed])
fi
fi

# Now, check that apache is compiled with shared modules enabled
AC_MSG_CHECKING([apache shared module support])
if $APXS -q CC >/dev/null 2>&1
then
    AC_MSG_RESULT(ok)
else
    AC_MSG_ERROR([Apache does not appear to be compiled with shared module support])
    exit 1
fi

# Check the the apxs contains the absolute library path. Some RPMs for 
# RedHat / Mandrake have broken apxs
AC_MSG_CHECKING([apache modules directory])
if test -d `$APXS -q LIBEXECDIR`
then
    AC_MSG_RESULT([OK])
else
    AC_MSG_ERROR([Apache appears to be misconfigured - apxs reports module directory as `$APXS -q LIBEXECDIR`. Absolute path expected])
    exit 1
fi

# Set the modules dir for substitution
AC_SUBST(APACHE_MODULES_DIR)
APACHE_MODULES_DIR=`$APXS -q LIBEXECDIR`

dnl Check for functions
dnl memmem() is used by mod_skunkweb
AC_CHECK_FUNCS(memmem)

dnl Checks for header files.
AC_HEADER_STDC
AC_CHECK_HEADERS(limits.h unistd.h)

dnl Checks for typedefs, structures, and compiler characteristics.
AC_C_CONST
AC_TYPE_SIZE_T

AC_OUTPUT(Makefile httpd_conf.stub)


