/*
    Copyright (C) 2003, Andrew T. Csillag <drew_csillag@yahoo.com>
	 You may distribute under the terms of either the GNU General
	 Public License or the SkunkWeb License, as specified in the
	 README file.
*/
#include <unistd.h>
#include <stdio.h>
#include <errno.h>
int main(int argc, char **argv)
{
    char** buf;
    int i;

    /*for (i=0; i<argc; i++) puts(argv[i]);*/

    buf = alloca((argc+3)* sizeof(char*));
    buf[0]="/home/drew/local/bin/python";
    buf[1]="/home/drew/swinst//bin/swpython.py";
    for (i=1;i<argc;i++) buf[i+1] = argv[i];
    buf[i+2]=0;
    i = execv(buf[0], buf);
    printf("ERROR! rc is %d %s\n", i, strerror(errno));
}
